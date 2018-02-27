import numpy
import sys, os, glob
import ctypes

from . import clipper

from chimerax.core.atomic import molc

from chimerax.core.atomic.molc import CFunctions, string, cptr, pyobject, \
    set_c_pointer, pointer, size_t

from chimerax.core.atomic.molobject import _atoms, \
                _atom_pair, _atom_or_none, _bonds, _chain, _element, \
                _pseudobonds, _residue, _residues, _rings, _non_null_residues, \
                _residue_or_none, _residues_or_nones, _residues_or_nones, \
                _chains, _atomic_structure, _pseudobond_group, \
                _pseudobond_group_map


dpath = os.path.dirname(os.path.abspath(__file__))
libfile = glob.glob(os.path.join(dpath, '_symmetry.cpython*'))[0]

_c_functions = CFunctions(os.path.splitext(libfile)[0])

_symmetry = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), libfile))
c_property = _c_functions.c_property
cvec_property = _c_functions.cvec_property
c_function = _c_functions.c_function
c_array_function = _c_functions.c_array_function


# _sym_transforms = _symmetry.atom_and_bond_sym_transforms
# _sym_transforms.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_double),
#     ctypes.c_size_t, ctypes.POINTER(ctypes.c_double), ctypes.c_double)
# _sym_transforms.restype = ctypes.py_object

_sym_transforms = c_function('atom_and_bond_sym_transforms',
    args=(ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_double),
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_double), ctypes.c_double),
    ret = ctypes.py_object)
def sym_transforms_in_sphere(atoms, transforms, center, cutoff):
    natoms = len(atoms);
    tf = numpy.empty(transforms.shape, numpy.double)
    tf[:] = transforms
    c = numpy.empty(3, numpy.double)
    c[:] = center
    n_tf = len(transforms);
    result = _sym_transforms(atoms._c_pointers, natoms, transforms.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        n_tf, c.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), cutoff)
    from chimerax.core.atomic.molarray import _atoms, _bonds
    from chimerax.core.geometry import Places
    natoms = len(result[0])
    atom_coords = result[1].reshape((natoms,3))
    nbonds = len(result[3])
    bond_positions = Places(opengl_array=result[4].reshape((nbonds*2,4,4)))
    return (_atoms(result[0]), atom_coords, result[2], _bonds(result[3]), bond_positions, result[5])

def bond_half_colors(bonds):
    f = c_function('bond_half_colors',
        args=(ctypes.c_void_p, ctypes.c_size_t),
        ret=ctypes.py_object)
    return f(bonds._c_pointers, len(bonds))

from chimerax.core.models import Model, Drawing

class XtalSymmetryHandler(Model):
    '''
    Handles crystallographic symmetry for an atomic model.
    '''
    def __init__(self, model, mtzfile=None, calculate_maps=True, map_oversampling=1.5,
        live_map_scrolling=True, map_scrolling_radius=12, live_atomic_symmetry=True,
        atomic_symmetry_radius=15):
        name = 'Crystal'
        session = self.session = model.session
        super().__init__(name, session)

        self._box_center = session.view.center_of_rotation
        self._box_center_grid = None
        self._atomic_sym_radius = atomic_symmetry_radius

        self.mtzdata=None

        if mtzfile is not None:
            from .clipper_mtz import ReflectionDataContainer
            mtzdata = self.mtzdata = ReflectionDataContainer(self.session, mtzfile, shannon_rate = map_oversampling)
            self.add([mtzdata])
            self.cell = mtzdata.cell
            self.spacegroup = mtzdata.spacegroup
            self.grid = mtzdata.grid_sampling
            self.hklinfo = mtzdata.hklinfo
        else:
            from .crystal import symmetry_from_model_metadata
            self.cell, self.spacegroup, self.grid = symmetry_from_model_metadata(model)

        cell = self.cell
        spacegroup = self.spacegroup
        grid = self.grid

        self._voxel_size = cell.dim/grid.dim

        ref = model.bounds().center()

        from .main import atom_list_from_sel
        ca = self._clipper_atoms = atom_list_from_sel(model.atoms)

        uc = self._unit_cell = clipper.Unit_Cell(ref, ca, cell, spacegroup, grid)

        from chimerax.core.triggerset import TriggerSet
        trig = self.triggers = TriggerSet()

        trigger_names = (
            'map box changed',  # Changed shape of box for map viewing
            'map box moved',    # Changed location of box for map viewing
            'atom box changed', # Changed shape or centre of box for showing symmetry atoms
        )
        for t in trigger_names:
            trig.add_trigger(t)

        self._atomic_symmetry_model = AtomicSymmetryModel(model, self, uc,
            radius = atomic_symmetry_radius, live = live_atomic_symmetry)

        self._update_trigger = session.triggers.add_handler('new frame',
            self.update)

        model.add([self])

    @property
    def atomic_sym_radius(self):
        return self._atomic_sym_radius

    @atomic_sym_radius.setter
    def atomic_sym_radius(self, radius):
        self._atomic_sym_radius = radius
        self.triggers.activate_trigger('atom box changed', (self._box_center, radius))

    @property
    def unit_cell(self):
        return self._unit_cell

    def update(self, *_):
        v = self.session.view
        cofr = self._box_center = v.center_of_rotation
        cofr_grid = clipper.Coord_orth(cofr).coord_frac(self.cell).coord_grid(self.grid)
        if self._box_center_grid is not None:
            if (cofr_grid == self._box_center_grid):
                return
        self._box_center_grid = cofr_grid
        self.triggers.activate_trigger('map box moved', (cofr, cofr_grid))
        self.triggers.activate_trigger('atom box changed', (cofr, self._atomic_sym_radius))

    @property
    def atom_sym(self):
        return self._atomic_symmetry_model

class AtomicSymmetryModel(Model):
    '''
    Finds and draws local symmetry atoms for an atomic structure
    '''
    def __init__(self, atomic_structure, parent, unit_cell, radius = 15,
        include_master = False, dim_colors_to = 0.7, live = True):
        self._live = False
        self.structure = atomic_structure
        session = self.session = atomic_structure.session
        self.unit_cell = unit_cell
        self.cell = parent.cell
        self.spacegroup =parent.spacegroup
        self.grid = parent.grid
        self.session = atomic_structure.session
        self._include_identity = include_master
        self._color_dim_factor = dim_colors_to
        super().__init__('Atomic symmetry', session)
        parent.add([self])
        self._model_changes_handler = atomic_structure.triggers.add_handler(
                                        'changes', self._model_changed_cb)
        self._box_changed_handler = None
        self._center = session.view.center_of_rotation
        self._radius = radius
        self._box_dim = numpy.array([radius*2, radius*2, radius*2], numpy.double)
        ad = self._atoms_drawing = SymAtomsDrawing('Symmetry atoms')
        self.add_drawing(ad)
        from chimerax.core.atomic.structure import PickedBonds
        bd = self._bonds_drawing = SymBondsDrawing('Symmetry bonds', PickedSymBond, PickedBonds)
        self.add_drawing(bd)
        self.live = live

    @property
    def live(self):
        return self._live

    @live.setter
    def live(self, flag):
        if flag and not self._live:
            self._box_changed_handler = self.parent.triggers.add_handler('atom box changed',
                self._box_changed_cb)
            self._update_box(self._center, self._radius)
            self.update_graphics()
        elif not flag and self._live:
            self.parent.triggers.remove_handler(self._box_changed_cb)
        self._live = flag

    @property
    def _level_of_detail(self):
        from chimerax.core.atomic.structure import structure_graphics_updater
        gu = structure_graphics_updater(self.session)
        return gu.level_of_detail


    def _box_changed_cb(self, trigger_name, box_params):
        if not self.visible:
            return
        center, radius = box_params
        self._center = center
        self._radius = radius
        self._update_box(center, radius)
        self.update_graphics()

    def _update_box(self, center, radius):
        from .crystal import find_box_corner
        self._center = center
        self._radius = radius
        box_corner_grid, box_corner_xyz = find_box_corner(center, self.cell, self.grid, radius)
        dim = self._box_dim
        dim[:] = radius*2
        grid_dim = (dim / self.parent._voxel_size).astype(numpy.int32)
        symops = self._current_symops = self.unit_cell.all_symops_in_box(box_corner_xyz, grid_dim, True)
        # Identity symop will always be the first in the list
        if self._include_identity:
            first_symop = 0
        else:
            first_symop = 1
        tfs = symops.all_matrices_orth(self.cell, format='3x4')[first_symop:]
        self._current_atoms, self._current_atom_coords, self._current_atom_syms, \
            self._current_bonds, self._current_bond_tfs, self._current_bond_syms = \
                sym_transforms_in_sphere(self.structure.atoms, tfs, center, radius)

    def _model_changed_cb(self, trigger_name, changes):
        if not self.visible:
            return
        changes = changes[1]
        update_needed = False
        if len(changes.created_atoms()):
            update_needed = True
        if changes.num_deleted_atoms() > 0:
            update_needed = True
        reasons = changes.atom_reasons()
        if 'coord changed' in reasons:
            update_needed = True
        if 'display changed' in reasons or 'hide changed' in reasons:
            update_needed = True
        if 'color_changed' in reasons:
            update_needed = True
        if (update_needed):
            self._update_box(self._center, self._radius)
            self.update_graphics()

    def update_graphics(self):
        ad = self._atoms_drawing
        bd = self._bonds_drawing

        lod = self._level_of_detail
        lod.set_atom_sphere_geometry(ad)
        lod.set_bond_cylinder_geometry(bd)

        ca = ad.visible_atoms = self._current_atoms
        na = len(ca)
        if na > 0:
            ad.display = True
            xyzr = numpy.empty((na, 4), numpy.float32)
            xyzr[:,:3] = self._current_atom_coords
            xyzr[:,3] = self.structure._atom_display_radii(ca)
            from chimerax.core.geometry import Places
            ad.positions = Places(shift_and_scale = xyzr)
            colors = ca.colors.astype(numpy.float32)
            if self._include_identity:
                colors[self._current_atom_syms!=0,:3] *= self._color_dim_factor
            else:
                colors[:,:3] *= self._color_dim_factor
            ad.colors = colors.astype(numpy.uint8)
        else:
            ad.display = False

        bonds = bd.visible_bonds = self._current_bonds
        nb = len(bonds)
        if nb > 0:
            bd.display = True
            bd.positions = self._current_bond_tfs
            colors = bonds.half_colors.astype(numpy.float32)
            if self._include_identity:
                mask = numpy.concatenate([self._current_bond_syms!=0]*2)
                colors[mask, :3] *= self._color_dim_factor
            else:
                colors[:,:3] *= self._color_dim_factor
            bd.colors = colors.astype(numpy.uint8)
        else:
            bd.display = False



from chimerax.core.atomic.structure import AtomsDrawing
class SymAtomsDrawing(AtomsDrawing):
    def first_intercept(self, mxyz1, mxyz2, exclude=None):
        if not self.display or self.visible_atoms is None or (exclude and exclude(self)):
            return None
        xyzr = self.positions.shift_and_scale_array()
        coords, radii = xyzr[:,:3], xyzr[:,3]

        from chimerax.core.geometry import closest_sphere_intercept
        fmin, anum = closest_sphere_intercept(coords, radii, mxyz1, mxyz2)
        if fmin is None:
            return None
        atom = self.visible_atoms[anum]
        atom_syms = self.parent._current_atom_syms
        sym = self.parent._current_symops[int(atom_syms[anum])]
        return PickedSymAtom(atom, fmin, sym)

    def planes_pick(self, planes, exclude=None):
        return []

    def bounds(self, positions=True):
        if not positions:
            return self._geometry_bounds()
        cpb = self._cached_position_bounds
        if cpb is not None:
            return cpb
        xyzr = self.positions.shift_and_scale_array()
        coords, radii = xyzr[:, :3], xyzr[:,3]
        from chimerax.core.geometry import sphere_bounds
        b = sphere_bounds(coords, radii)
        self._cached_position_bounds = b

    def update_selection(self):
        pass

from chimerax.core.graphics import Pick
#from chimerax.core.atomic.structure import PickedAtom

class PickedSymAtom(Pick):
    def __init__(self, atom, distance, sym):
        super().__init__(distance)
        self.atom = atom
        self.sym = sym

    def description(self):
        return '({}) {}'.format(self.sym, self.atom)

    def select(self, mode = 'add'):
        pass

from chimerax.core.atomic.structure import BondsDrawing
class SymBondsDrawing(BondsDrawing):
    def first_intercept(self, mxyz1, mxyz2, exclude=None):
        return None #too-hard basket for now.

        if not self.display or (exclude and exclude(self)):
            return None
        from chimerax.core.atomic.structure import _bond_intercept
        b, f = _bond_intercept(bonds, mxyz1, mxyz2)

    def planes_pick(self, mxyz1, mxyz2, exclude=None):
        return []

    def bounds(self, positions=True):
        #TODO: properly calculate bounds
        return self._geometry_bounds()

    def select(self, mode = 'add'):
        pass

    def update_selection(self):
        pass

#from chimerax.core.atomic.structure import PickedBond
class PickedSymBond(Pick):
    def __init__(self, bond, distance, sym):
        super().__init__(distance)
        self.bond = bond
        self.sym = sym
    def description(self):
        return '({}) {}'.format(self.sym, self.bond)
