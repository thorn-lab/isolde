# @Author: Tristan Croll <tic20>
# @Date:   26-Apr-2018
# @Email:  tic20@cam.ac.uk
# @Last modified by:   tic20
# @Last modified time: 17-Dec-2019
# @License: Free for non-commercial use (see license.pdf)
# @Copyright:2016-2019 Tristan Croll



import numpy
from numpy import uint8, int32, uint32, float64, float32, uintp, byte, bool as npy_bool, integer, empty, array
from chimerax.atomic import molc
# from chimerax.atomic.molc import CFunctions, string, cptr, pyobject, \
#     set_c_pointer, pointer, size_t

CFunctions = molc.CFunctions
string = molc.string
cptr = molc.cptr
pyobject = molc.pyobject
set_c_pointer = molc.set_c_pointer
pointer = molc.pointer
size_t = molc.size_t

from chimerax.atomic import molarray as ma
Collection = ma.Collection
from . import molobject
from .molobject import c_function, c_array_function, cvec_property, delayed_class_init
#from .molobject import object_map
from .molobject import (
    ChiralCenter, ProperDihedral, Rotamer, Rama, PositionRestraint,
    TuggableAtom, MDFFAtom, DistanceRestraint, AdaptiveDistanceRestraint,
    ChiralRestraint, ProperDihedralRestraint, AdaptiveDihedralRestraint,
    RotamerRestraint
)

from .molobject import (
    get_chiral_mgr, get_proper_dihedral_mgr, get_ramachandran_mgr,
    get_rotamer_mgr
)

import ctypes

from chimerax.atomic import Atom, Atoms, Residue, Residues

from chimerax.atomic import ctypes_support as convert
# from chimerax.atomic.molarray import _atoms, _atoms_or_nones, \
#         _bonds, _non_null_atoms, _pseudobond_groups, _pseudobonds, \
#         _elements, _residues, _non_null_residues, _chains, \
#         _non_null_chains, _atomic_structures, structure_datas, \
#         _atoms_pair, _pseudobond_group_map

def _chiral_centers(p):
    return ChiralCenters(p)
def _proper_dihedrals(p):
    return ProperDihedrals(p)
def _rotamers(p):
    return Rotamers(p)
def _proper_dihedrals_or_nones(p):
    return [ProperDihedral.c_ptr_to_py_inst(ptr) if ptr else None for ptr in p]
def _distance_restraints(p):
    return DistanceRestraints(p)
def _adaptive_distance_restraints(p):
    return AdaptiveDistanceRestraints(p)
def _non_null_proper_dihedrals(p):
    return ProperDihedrals(p[p!=0])
def _atoms_pair(p):
    return (Atoms(p[:,0].copy()), Atoms(p[:,1].copy()))
def _atoms_four_tuple(p):
    return tuple((Atoms(p[:,i].copy()) for i in range(4)))
def _chiral_restraints(p):
    return ChiralRestraints(p)
def _proper_dihedral_restraints(p):
    return ProperDihedralRestraints(p)
def _adaptive_dihedral_restraints(p):
    return AdaptiveDihedralRestraints(p)
def _rotamer_restraints(p):
    return RotamerRestraints(p)

class _Dihedrals(Collection):
    '''
    Base class for ProperDihedrals and Improper_Dihedrals. Do not
    instantiate directly.
    '''
    SESSION_SAVE=False
    def __init__(self, c_pointers, single_class, array_class):
        super().__init__(c_pointers, single_class, array_class)

    @property
    def _natoms(self):
        return 4

class ChiralCenters(_Dihedrals):


    def __init__(self, c_pointers = None):
        super().__init__(c_pointers, ChiralCenter, ChiralCenters)

    def delete(self):
        err_string = 'Dihedrals are not in charge of their own creation '\
            +'and deletion. Instead, use '\
            +'session.chiral_mgr.delete_chirals(chirals).'
        raise RuntimeError(err_string)

    atoms = cvec_property('chiral_atoms', cptr, '_natoms', astype=_atoms_four_tuple, read_only=True,
        doc = '''
        Returns a four-tuple of :class:`Atoms` objects. For each dihedral,
        its constituent atoms are in the matching position in the four
        :class:`Atoms` collections. Read only.
        ''')
    angles = cvec_property('chiral_angle', float64, read_only=True,
        doc='Returns the angle in radians for each dihedral. Read only.')
    residues = cvec_property('chiral_residue', cptr, astype=convert.residues, read_only=True,
        doc='Returns a :class:`Residues` giving the parent residue of each dihedral. Read only')

    expected_angles = cvec_property('chiral_center_expected_angle', float64, read_only=True,
        doc='The equilibrium angle of each chiral dihedral in its correct isomeric state. Read only.')
    deviations = cvec_property('chiral_center_deviation', float64, read_only=True,
        doc='The difference between each current dihedral angle and its :attr:`expected_angle`. Read only.')
    chiral_atoms = cvec_property('chiral_center_chiral_atom', cptr, astype=convert.atoms, read_only=True,
        doc='The chiral atoms. Read only.')

    def take_snapshot(self, session, flags):
        data = {
            'atoms':    self.chiral_atoms,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        cm = get_chiral_mgr(session)
        return cm.get_chirals(data['atoms'])


class ProperDihedrals(_Dihedrals):

    def __init__(self, c_pointers = None):
        super().__init__(c_pointers, ProperDihedral, ProperDihedrals)

    def delete(self):
        err_string = 'Dihedrals are not in charge of their own creation '\
            +'and deletion. Instead, use '\
            +'session.proper_dihedrals_mgr.delete_dihedrals(dihedrals).'
        raise RuntimeError(err_string)

    @property
    def natoms(self):
        return 4
    #TODO: remove this hack once ChimeraX c_array_property bug is fixed
    atoms = cvec_property('proper_dihedral_atoms', cptr, '_natoms', astype=_atoms_four_tuple, read_only=True,
        doc = '''
        Returns a four-tuple of :class:`Atoms` objects. For each dihedral,
        its constituent atoms are in the matching position in the four
        :class:`Atoms` collections. Read only.
        ''')
    angles = cvec_property('proper_dihedral_angle', float64, read_only=True,
        doc='Returns the angle in radians for each dihedral. Read only.')
    names = cvec_property('proper_dihedral_name', string, read_only=True)
    residues = cvec_property('proper_dihedral_residue', cptr, astype=convert.residues, read_only=True,
        doc='Returns a :class:`Residues` giving the parent residue of each dihedral. Read only')

    axial_bonds = cvec_property('proper_dihedral_axial_bond', cptr, astype=convert.bonds, read_only=True,
        doc='Returns a :class:`Bonds` giving the axial bond for each dihedral. Read-only')

    def take_snapshot(self, session, flags):
        data = {
            'residues': self.residues,
            'names':    list(self.names),
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        pdm = get_proper_dihedral_mgr(session)
        return ProperDihedrals([pdm.get_dihedral(r, name) for r, name in zip(
            data['residues'], data['names']
        )])

class Ramas(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, Rama, Ramas)

    @property
    def omega_dihedrals(self):
        '''
        Returns a :class:`ProperDihedrals` instance pointing to the omega
        (peptide bond) dihedral for each residue. Note that some residues
        will not have omega dihedrals, so the output array may be shorter
        than the :class:`Ramas` instance.
        '''
        f = c_function('rama_omega',
            args = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p),
            ret = ctypes.c_size_t)
        n = len(self)
        ret = numpy.empty(n, cptr)
        found = f(self._c_pointers, n, pointer(ret))
        return _proper_dihedrals(ret[:found])

    @property
    def phi_dihedrals(self):
        '''
        Returns a :class:`ProperDihedrals` instance pointing to the phi
        dihedral for each residue. Note that some residues will not have phi
        dihedrals, so the output array may be shorter  than the :class:`Ramas`
        instance.
        '''
        f = c_function('rama_phi',
            args = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p),
            ret = ctypes.c_size_t)
        n = len(self)
        ret = numpy.empty(n, cptr)
        found = f(self._c_pointers, n, pointer(ret))
        return _proper_dihedrals(ret[:found])

    @property
    def psi_dihedrals(self):
        '''
        Returns a :class:`ProperDihedrals` instance pointing to the psi
        dihedral for each residue. Note that some residues will not have psi
        dihedrals, so the output array may be shorter than the :class:`Ramas`
        instance.
        '''
        f = c_function('rama_psi',
            args = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p),
            ret = ctypes.c_size_t)
        n = len(self)
        ret = numpy.empty(n, cptr)
        found = f(self._c_pointers, n, pointer(ret))
        return _proper_dihedrals(ret[:found])

    residues = cvec_property('rama_residue', cptr, astype=convert.residues, read_only = True,
            doc = 'Returns a :class:`chimerax.Residues` instance giving the residue to which each Rama belongs. Read only.')
    ca_atoms = cvec_property('rama_ca_atom', cptr, astype=convert.atoms, read_only = True,
            doc = 'Returns a :class:`chimerax.Atoms` instance giving the alpha carbon of each amino acid residue. Read only.')
    valids = cvec_property('rama_is_valid', npy_bool, read_only = True,
            doc = 'True for each residue that has all three of omega, phi and psi. Read only.')
    visibles = cvec_property('rama_visible', npy_bool, read_only = True,
            doc = 'True for each residue whose alpha carbon is visible. Read only.')
    visibles_ignoring_ribbon = cvec_property('rama_only_hidden_by_ribbon', npy_bool, read_only=True,
            doc = 'True if the only thing hiding the alpha carbon is the ribbon display. Read only.')
    scores = cvec_property('rama_score', float64, read_only = True,
            doc = 'The score of each residue on the MolProbity Ramachandran contours. Read only.')
    phipsis = cvec_property('rama_phipsi', float64, 2, read_only = True,
            doc = 'The phi and psi angles for each residue in radians. Read only.')
    angles = cvec_property('rama_omegaphipsi', float64, 3, read_only = True,
            doc = 'The omega, phi and psi angles for each residue in radians. Read only.')
    cases = cvec_property('rama_case', uint8, read_only=True,
            doc = '''Values representing the Ramachandran case for these residues,
                matching the case definitions in :class:`RamaMgr.RamaCase`. Read only.''')

    def take_snapshot(self, session, flags):
        data = {
            'residues': self.residues,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        rmgr = get_ramachandran_mgr(session)
        return rmgr.get_ramas(data['residues'])

class Rotamers(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, Rotamer, Rotamers)

    residues = cvec_property('rotamer_residue', cptr, astype=convert.residues, read_only=True,
                doc=':py:class:`chimerax.Residue` this rotamer belongs to. Read only.')
    scores = cvec_property('rotamer_score', float64, read_only=True,
                doc='P-value for the current conformation of this rotamer. Read only.')
    ca_cb_bonds = cvec_property('rotamer_ca_cb_bond', cptr, astype=convert.bonds, read_only=True,
                doc='The "stem" :py:class:`chimerax.Bond` of this rotamer. Read only.')
    visibles = cvec_property('rotamer_visible', npy_bool, read_only=True,
                doc='True for each rotamer whose CA-CB bond is visible')

    def take_snapshot(self, session, flags):
        data = {
            'residues': self.residues,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        rmgr = get_rotamer_mgr(session)
        return rmgr.get_rotamers(data['residues'])

class PositionRestraints(Collection):
    def __init__(self, c_pointers=None, single_type = None, poly_type = None):
        if single_type is None:
            single_type = PositionRestraint
        if poly_type is None:
            poly_type = PositionRestraints
        super().__init__(c_pointers, single_type, poly_type)

    @property
    def _bond_cylinder_transforms(self):
        '''Transforms mapping a unit cylinder onto the restraint bonds. Read only.'''
        f = c_function('position_restraint_bond_transform',
            args = (ctypes.c_void_p, ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_float)))
        n = len(self)
        transforms = empty((n,4,4), float32)
        f(self._c_pointers, n, pointer(transforms))
        return transforms

    def clear_sim_indices(self):
        '''
        Run at the end of a simulation to reset :attr:`sim_indices` to -1.
        '''
        f = c_function('position_restraint_clear_sim_index',
            args = (ctypes.c_void_p, ctypes.c_size_t))
        f(self._c_pointers, len(self))

    atoms = cvec_property('position_restraint_atom', cptr, astype=convert.atoms, read_only=True,
        doc = 'Returns the restrained :py:class:`chimerax.Atoms`. Read-only.')
    targets = cvec_property('position_restraint_target', float64, 3,
        doc = 'Target (x,y,z) positions in Angstroms. Can be written.')
    target_vectors = cvec_property('position_restraint_target_vector', float64, 3, read_only=True,
        doc = 'Returns the vectors ("bonds") connecting each atom to its target. Read only.')
    spring_constants = cvec_property('position_restraint_k', float64,
        doc = 'Restraint spring constants in :math:`kJ mol^{-1} nm^{-2}`. Can be written')
    enableds = cvec_property('position_restraint_enabled', npy_bool,
        doc = 'Enable/disable position restraints with a Numpy boolean array.')
    visibles = cvec_property('position_restraint_visible', npy_bool, read_only=True,
        doc = 'Returns a boolean mask giving the currently visible restraints. Read only.')
    sim_indices = cvec_property('position_restraint_sim_index', int32,
        doc = '''
        Index of each restraint in the associated force object in a running
        simulation. Restraints tha are not part of a simulation have indices of
        -1. Can be set, but only if you know what you are doing.
        ''')

    def take_snapshot(self, session, flags):
        prms = [r.mgr for r in self]
        data = {
            'restraint mgrs': prms,
            'atoms':          self.atoms,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        prs = PositionRestraints([prm.get_restraint(atom) for prm, atom in zip(
            data['restraint mgrs'], data['atoms']
        )])


class TuggableAtoms(PositionRestraints):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, single_type=TuggableAtom, poly_type = TuggableAtoms)

    def take_snapshot(self, session, flags):
        tams = [t.mgr for t in self]
        data = {
            'restraint mgrs': tams,
            'atoms':          self.atoms,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        tas = TuggableAtoms([tam.get_tuggable(atom) for tam, atom in zip(
            data['restraint mgrs'], data['atoms']
        )])


class MDFFAtoms(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, MDFFAtom, MDFFAtoms)

    def clear_sim_indices(self):
        '''
        Run at the end of a simulation to reset :attr:`sim_indices` to -1.
        '''
        f = c_function('mdff_atom_clear_sim_index',
            args=(ctypes.c_void_p, ctypes.c_size_t))
        f(self._c_pointers, len(self))

    enableds = cvec_property('mdff_atom_enabled', npy_bool,
        doc='Enable/disable MDFF tugging on each atom or get the current states.')
    atoms = cvec_property('mdff_atom_atom', cptr, astype=convert.atoms, read_only=True,
        doc='Returns the :py:class:`chimerax.Atom`. Read only.')
    coupling_constants = cvec_property('mdff_atom_coupling_constant', float64,
        doc='''
        Per-atom MDFF coupling constants. These are multiplied by the global
        coupling constant for the map when calculating the MDFF potentials.
        Can be set.
        ''')
    sim_indices = cvec_property('mdff_atom_sim_index', int32,
        doc='''
        Index of each atom in the relevant MDFF Force in a running simulation.
        Atoms which are not currently in a simulation have indices equal to -1.
        Can be set, but only if you know what you are doing.
         ''')

    def take_snapshot(self, session, flags):
        mgrs = [a.mgr for a in self]
        data = {
            'restraint mgrs':   mgrs,
            'atoms':            atoms,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        return MDFFAtoms([mgr.get_mdff_atom(a) for mgr, a in zip(
            data['restraint mgrs'], data['atoms']
        )])



class DistanceRestraints(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, DistanceRestraint, DistanceRestraints)

    @property
    def _bond_cylinder_transforms(self):
        '''Transforms mapping a unit cylinder onto the restraint bonds. Read only.'''
        from chimerax.core.geometry import Places
        f = c_function('distance_restraint_bond_transform',
            args = (ctypes.c_void_p, ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_float)))
        n = len(self)
        transforms = empty((n,4,4), float32)
        f(self._c_pointers, n, pointer(transforms))
        return Places(opengl_array=transforms)

    @property
    def _target_transforms(self):
        from chimerax.core.geometry import Places
        f = c_function('distance_restraint_target_transform',
            args=(ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_float)))
        n = len(self)
        transforms=empty((n,4,4), float32)
        f(self._c_pointers, n, pointer(transforms))
        return Places(opengl_array=transforms)

    def clear_sim_indices(self):
        '''
        Run at the end of a simulation to reset sim indices to -1
        '''
        f = c_function('distance_restraint_clear_sim_index',
            args = (ctypes.c_void_p, ctypes.c_size_t))
        f(self._c_pointers, len(self))

    enableds =cvec_property('distance_restraint_enabled', npy_bool,
            doc = 'Enable/disable these restraints or get their current states.')
    visibles = cvec_property('distance_restraint_visible', npy_bool, read_only = True,
            doc = 'Each restraint will be visible if it is enabled and both atoms are visible.')
    atoms = cvec_property('distance_restraint_atoms', cptr, 2, astype=_atoms_pair, read_only=True,
            doc = 'Returns a 2-tuple of :class:`Atoms` containing the restrained atoms. Read only.' )
    targets = cvec_property('distance_restraint_target', float64,
            doc = 'Target distances in Angstroms')
    spring_constants = cvec_property('distance_restraint_k', float64,
            doc = 'Restraint spring constants in :math:`kJ mol^{-1} nm^{-2}`')
    distances = cvec_property('distance_restraint_distance', float64, read_only=True,
            doc = 'Current distances between restrained atoms in Angstroms. Read only.')
    sim_indices = cvec_property('distance_restraint_sim_index', int32,
        doc='''
        Index of each restraint in the relevant MDFF Force in a running
        simulation. Restraints which are not currently in a simulation have
        indices equal to -1. Can be set, but only if you know what you are
        doing.
         ''')

    def take_snapshot(self, session, flags):
        data = {
        'restraint mgrs': [r.mgr for r in self],
        'atoms':    self.atoms
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        rmgrs = data['restraint mgrs']
        atoms1, atoms2 = data['atoms']
        return DistanceRestraints([
            drm.get_restraint(a1, a2) for drm, a1, a2 in zip(rmgrs, atoms1, atoms2)
        ])

class AdaptiveDistanceRestraints(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, AdaptiveDistanceRestraint,
            AdaptiveDistanceRestraints)

    @property
    def _bond_transforms(self):
        '''
        Transforms mapping a tripartite bond onto the restraint vectors. Read only.
        '''
        from chimerax.core.geometry import Places
        f = c_function('adaptive_distance_restraint_bond_transforms',
            args= (ctypes.c_void_p, ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
            )
        )
        n = len(self)
        tf_ends = empty((n*2,4,4), float32)
        tf_m = empty((n,4,4), float32)
        f(self._c_pointers, n, pointer(tf_ends), pointer(tf_m))
        return tuple(Places(opengl_array=tf) for tf in (tf_ends, tf_m))

    def clear_sim_indices(self):
        '''
        Run at the end of a simulation to reset sim indices to -1
        '''
        f = c_function('distance_restraint_clear_sim_index',
            args = (ctypes.c_void_p, ctypes.c_size_t))
        f(self._c_pointers, len(self))


    enableds =cvec_property('adaptive_distance_restraint_enabled', npy_bool,
            doc = 'Enable/disable these restraints or get their current states.')
    visibles = cvec_property('adaptive_distance_restraint_visible', npy_bool, read_only = True,
            doc = 'Each restraint will be visible if it is enabled and both atoms are visible.')
    atoms = cvec_property('adaptive_distance_restraint_atoms', cptr, 2, astype=_atoms_pair, read_only=True,
            doc = 'Returns a 2-tuple of :class:`Atoms` containing the restrained atoms. Read only.' )
    targets = cvec_property('adaptive_distance_restraint_target', float64,
            doc = 'Target distances in Angstroms')
    tolerances = cvec_property('adaptive_distance_restraint_tolerance', float64,
            doc = 'Half-widths of potential well flat bottoms in Angstroms')
    kappas = cvec_property('adaptive_distance_restraint_kappa', float64,
            doc = 'Parameter setting depth of energy well, in kJ/mol')
    cs = cvec_property('adaptive_distance_restraint_c', float64,
            doc = 'Parameter setting width of quadratic portion of energy well, in Angstroms')
    effective_spring_constants = cvec_property('adaptive_distance_restraint_effective_k', float64,
            doc = (r'Effective harmonic spring constants when '
                   r':attr:`distance` < :attr:`c`, in :math:`kJ mol^{-1} nm^{-2}`. '
                   r'The effective spring constant is :math:`k=\kappa/c^2`. '
                   r'Setting this parameter adjusts :math:`\kappa` for the '
                   r'current :attr:`c`.'))
    alphas = cvec_property('adaptive_distance_restraint_alpha', float64,
            doc = 'Parameter setting rate of energy growth/flattening outside well')
    distances = cvec_property('adaptive_distance_restraint_distance', float64, read_only=True,
            doc = 'Current distances between restrained atoms in Angstroms. Read only.')
    applied_forces = cvec_property('adaptive_distance_restraint_force_magnitude', float64, read_only=True,
            doc = 'Total force currently being applied to each restraint. Read only.')
    sim_indices = cvec_property('adaptive_distance_restraint_sim_index', int32,
        doc='''
        Index of each restraint in the relevant MDFF Force in a running
        simulation. Restraints which are not currently in a simulation have
        indices equal to -1. Can be set, but only if you know what you are
        doing.
         ''')
    colors = cvec_property('adaptive_distance_restraint_color', uint8, 4, read_only=True,
            doc = 'Color of each restraint. Automatically set based on ratio of current distance to target. Read only.')

    def take_snapshot(self, session, flags):
        data = {
        'restraint mgrs': [r.mgr for r in self],
        'atoms':    self.atoms
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        rmgrs = data['restraint mgrs']
        atoms1, atoms2 = data['atoms']
        return DistanceRestraints([
            drm.get_restraint(a1, a2) for drm, a1, a2 in zip(rmgrs, atoms1, atoms2)
        ])

class ChiralRestraints(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, ChiralRestraint, ChiralRestraints)

    def clear_sim_indices(self):
        f = c_function('chiral_restraint_clear_sim_index',
            args = (ctypes.c_void_p, ctypes.c_size_t))
        f(self._c_pointers, len(self))

    @property
    def atoms(self):
        return self.dihedrals.atoms

    @property
    def chiral_atoms(self):
        return self.dihedrals.chiral_atoms

    def restrict_to_sel(self, atoms):
        '''
        Returns a new :py:class:`ChiralRestraints` containing only the
        restraints for which every atom is in the given selection.
        '''
        f = c_function('chiral_restraint_all_atoms_in_sel',
            args=(ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t),
            ret=ctypes.py_object
            )
        return _chiral_restraints(f(self._c_pointers, len(self), atoms._c_pointers, len(atoms)))

    targets = cvec_property('chiral_restraint_target', float64, read_only = True,
        doc = 'Target angles for each restraint in radians. Read only.')
    dihedrals = cvec_property('chiral_restraint_chiral_center', cptr, astype=_chiral_centers, read_only=True,
        doc = 'Returns the restrained :py:class:`ChiralCenters`. Read only.')
    offsets = cvec_property('chiral_restraint_offset', float64, read_only = True,
        doc = 'Differences between current and target angles in radians. Read only.')
    cutoffs = cvec_property('chiral_restraint_cutoff', float64,
        doc = 'Cutoff angle offsets below which no restraint will be applied. Can be set.')
    enableds = cvec_property('chiral_restraint_enabled', npy_bool,
        doc = 'Enable/disable each restraint or get their current states.')
    spring_constants = cvec_property('chiral_restraint_k', float64,
        doc = 'Get/set the spring constants for each restraint in :math:`kJ mol^{-1} rad^{-2}`')
    sim_indices = cvec_property('chiral_restraint_sim_index', int32,
        doc='''
        Index of each restraint in the relevant Force in a running simulation.
        Returns -1 for restraints not currently in a simulation. Can be
        set, but only if you know what you are doing.
        ''')

    def take_snapshot(self, session, flags):
        data = {
            'restraint mgrs':   [r.mgr for r in self],
            'dihedrals':        self.dihedrals,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        return ChiralRestraints([
            mgr.get_restraint(dihedral) for mgr, dihedral in zip(
                data['restraint mgrs'], data['dihedrals']
            )
        ])


class _ProperDihedralRestraints_Base(Collection):
    _C_FUNCTION_PREFIX=None
    _ARRAY_GETTER=None

    def __init__(self, c_pointers=None, singular_py_class=None,
            array_py_class=None):
        super().__init__(c_pointers, singular_py_class, array_py_class)

    @classmethod
    def _c_function_prefix(cls):
        return cls._C_FUNCTION_PREFIX

    def _annotation_transforms(self):
        n = len(self)
        f = c_function(self._C_FUNCTION_PREFIX+'_annotation_transform',
            args = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p))
        tf1 = numpy.empty((n,4,4), float32)
        tf2 = numpy.empty((n,4,4), float32)
        f(self._c_pointers, n, pointer(tf1), pointer(tf2))
        from chimerax.core.geometry import Places
        return (Places(opengl_array=tf1), Places(opengl_array=tf2))

    def clear_sim_indices(self):
        f = c_function(self._C_FUNCTION_PREFIX+'_clear_sim_index',
            args = (ctypes.c_void_p, ctypes.c_size_t))
        f(self._c_pointers, len(self))

    @property
    def atoms(self):
        return self.dihedrals.atoms

    def restrict_to_sel(self, atoms):
        '''
        Returns a new :py:class:`ProperDihedralRestraints` containing only the
        restraints for which every atom is in the given selection.
        '''
        f = c_function(self._C_FUNCTION_PREFIX+'_all_atoms_in_sel',
            args=(ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t),
            ret=ctypes.py_object
            )
        return self._ARRAY_GETTER(f(self._c_pointers, len(self), atoms._c_pointers, len(atoms)))

    @classmethod
    def _init_methods(cls):

        cls.targets = cvec_property(cls._C_FUNCTION_PREFIX+'_target', float64,
            doc = 'Target angles for each restraint in radians. Can be written.')
        cls.dihedrals = cvec_property(cls._C_FUNCTION_PREFIX+'_dihedral', cptr, astype=_proper_dihedrals, read_only=True,
            doc = 'The restrained :py:class:`{ProperDihedrals}`. Read only.')
        cls.offsets = cvec_property(cls._C_FUNCTION_PREFIX+'_offset', float64, read_only = True,
            doc = 'Difference between current and target angles in radians. Read only.')
        cls.enableds = cvec_property(cls._C_FUNCTION_PREFIX+'_enabled', npy_bool,
            doc = 'Enable/disable each restraint or get their current states.')
        cls.displays = cvec_property(cls._C_FUNCTION_PREFIX+'_display', npy_bool,
            doc = 'Set whether you want each restraint to be displayed when active.')
        cls.visibles = cvec_property(cls._C_FUNCTION_PREFIX+'_visible', npy_bool, read_only=True,
            doc = 'Is each restraint currently visible? Read-only.')
        cls.spring_constants = cvec_property(cls._C_FUNCTION_PREFIX+'_k', float64,
            doc = 'Get/set the spring constant for each restraint in :math:`kJ mol^{-1} rad^{-2}`')
        cls.annotation_colors = cvec_property(cls._C_FUNCTION_PREFIX+'_annotation_color', uint8, 4, read_only=True,
            doc = 'Get the annotation color for each restraint according to the current colormap. Read only.')
        cls.sim_indices = cvec_property(cls._C_FUNCTION_PREFIX+'_sim_index', int32,
            doc='''
            Index of each restraint in the relevant Force in a running
            simulation. Restraints which are not currently in a simulation have
            indices equal to -1. Can be set, but only if you know what you are
            doing.
             ''')

    def take_snapshot(self, session, flags):
        data = {
            'restraint mgrs':   [r.mgr for r in self],
            'dihedrals':        self.dihedrals,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        return ProperDihedralRestraints([
            mgr.get_restraint(dihedral) for mgr, dihedral in zip(
                data['restraint mgrs'], data['dihedrals']
            )
        ])


@delayed_class_init
class ProperDihedralRestraints(_ProperDihedralRestraints_Base):
    _C_FUNCTION_PREFIX='proper_dihedral_restraint'

    @classmethod
    def _ARRAY_GETTER(cls, p):
        return _proper_dihedral_restraints(p)

    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, ProperDihedralRestraint, ProperDihedralRestraints)


    cutoffs = cvec_property('proper_dihedral_restraint_cutoff', float64,
        doc = 'Cutoff angle offsets below which no restraint will be applied. Can be set.')

@delayed_class_init
class AdaptiveDihedralRestraints(_ProperDihedralRestraints_Base):
    _C_FUNCTION_PREFIX='adaptive_dihedral_restraint'

    @classmethod
    def _ARRAY_GETTER(cls, p):
        return _adaptive_dihedral_restraints(p)

    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, AdaptiveDihedralRestraint, AdaptiveDihedralRestraints)


    kappas = cvec_property('adaptive_dihedral_restraint_kappa', float64,
        doc = (r'Sets the width of the region within which the dihedral will be '
            r'restrained. For values of kappa greater than about 1, the effective '
            r'standard deviation is approximately equal to '
            r':math:`\sqrt{\frac{1}{\kappa}}`. As kappa approaches zero the '
            r'shape of the energy profile approaches a standard cosine. Values '
            r'of kappa below zero are not allowed.'))

class RotamerRestraints(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, RotamerRestraint, RotamerRestraints)

    def set_spring_constant(self, k):
        '''
        Sets the spring constants for all chi dihedrals in all rotamers to k.
        Write-only. To retrieve the current spring constants, use
        :attr:`Rotamer.chi_restraints.spring_constants` (note: this is only
        possible for one rotamer at a time).
        '''
        f = c_function('set_rotamer_restraint_spring_constant',
            args=(ctypes.c_void_p, ctypes.c_size_t, ctypes.c_double))
        f(self._c_pointers, len(self), k)


    rotamers = cvec_property('rotamer_restraint_rotamer', cptr, astype=_rotamers, read_only=True,
        doc = ':py:class:`Rotamers` to be restrained. Read only.')
    residues = cvec_property('rotamer_restraint_residue', cptr, astype=convert.residues, read_only=True,
        doc = ':py:class:`chimerax.Residues` to be restrained. Read only.')
    enableds = cvec_property('rotamer_restraint_enabled', npy_bool,
        doc = '''
        Enable/disable chi dihedral restraints. Returns False for any rotamer
        where at least one chi restraint is disabled.
        ''')
    target_index = cvec_property('rotamer_restraint_target_index', int32,
        doc = '''
        Get/set the index of the rotamer target definition giving target angles
        and cutoffs. If no restraint is currently applied, returns the last
        restraint that was applied to this rotamer. If no restraint has ever
        been applied, returns -1.
        ''')

    def take_snapshot(self, session, flags):
        data = {
            'restraint mgrs': [r.mgr for r in self],
            'rotamers':       self.rotamers,
        }
        return data

    @staticmethod
    def restore_snapshot(session, data):
        return RotamerRestraints([
            mgr.get_restraint(rotamer) for mgr, rotamer in zip(
            data['restraint mgrs'], data['rotamers'])
        ])
