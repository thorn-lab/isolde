# @Author: Tristan Croll
# @Date:   18-Apr-2018
# @Email:  tic20@cam.ac.uk
# @Last modified by:   Tristan Croll
# @Last modified time: 18-Apr-2018
# @License: Creative Commons BY-NC-SA 3.0, https://creativecommons.org/licenses/by-nc-sa/3.0/.
# @Copyright: Copyright 2017-2018 Tristan Croll



import numpy
import copy
from collections import defaultdict

from chimerax.core.triggerset import TriggerSet
from chimerax.atomic import AtomicStructure, concatenate
from chimerax.core.geometry import Place, Places
from chimerax.core.geometry import find_close_points, find_close_points_sets
from chimerax.surface import zone
from chimerax.surface.shapes import sphere_geometry

from chimerax.core.models import Model, Drawing
from chimerax.std_commands import camera, cofr, cartoon
from chimerax.core.commands import atomspec
from chimerax.map.data import Array_Grid_Data
from chimerax.map import Volume, volumecommand

from .mousemodes import initialize_map_contour_mouse_modes
from .main import atom_list_from_sel
from . import clipper
from .clipper_mtz import ReflectionDataContainer

DEFAULT_BOND_RADIUS = 0.2


def move_model(session, model, new_parent):
    '''
    Temporary method until something similar is added to the ChimeraX
    core. Picks up a model from the ChimeraX model tree and transplants
    it (with all its children intact) as the child of a different model.
    '''
    model._auto_style = False
    mlist = model.all_models()
    model_id = model.id
    if new_parent in mlist:
        raise RuntimeError('Target model cannot be one of the models being moved!')
    for m in mlist:
        m.removed_from_session(session)
        mid = m.id
        if mid is not None:
            del session.models._models[mid]
            m.id = None
    session.triggers.activate_trigger('remove models', mlist)
    if len(model_id) == 1:
        parent = session.models.drawing
    else:
        parent = session.models._models[model_id[:-1]]
    parent.remove_drawing(model, delete=False)
    parent._next_unused_id = None
    new_parent.add([model])

def symmetry_from_model_metadata(model):
    if 'CRYST1' in model.metadata.keys():
        return symmetry_from_model_metadata_pdb(model)
    elif 'cell' in model.metadata.keys():
        return symmetry_from_model_metadata_mmcif(model)
    raise TypeError('Model does not appear to have symmetry information!')

def symmetry_from_model_metadata_mmcif(model):
    metadata = model.metadata
    try:
        cell_headers = metadata['cell']
        cell_data = metadata['cell data']
        cell_dict = dict((key, data) for (key, data) in zip(cell_headers, cell_data))
        abc = [cell_dict['length_a'], cell_dict['length_b'], cell_dict['length_c']]
        angles = [cell_dict['angle_alpha'], cell_dict['angle_beta'], cell_dict['angle_gamma']]
    except:
        raise TypeError('No cell information available!')

    try:
        spgr_headers = metadata['symmetry']
        spgr_data = metadata['symmetry data']
    except:
        raise TypeError('No space group headers in metadata!')

    sprg_dict = dict((key, data) for (key, data) in zip(spgr_headers, spgr_data))
    spgr_str = spgr_dict['int_tables_number']
    if spgr_str == '?':
        spgr_str = spgr_dict['space_group_name_h-m']
    if spgr_str == '?':
        spgr_str = spgr_dict['space_group_name_hall']
    if spgr_str == '?':
        raise TypeError('No space group information available!')


    # TODO: ChimeraX does not currently keep refinement metadata (including resolution)
    res = 3.0

    cell_descr = clipper.Cell_descr(*abc, *angles)
    cell = clipper.Cell(cell_descr)
    spgr_descr = clipper.Spgr_descr(spgr_str)
    spacegroup = clipper.Spacegroup(spgr_descr)
    resolution = clipper.Resolution(res)
    grid_sampling = clipper.Grid_sampling(spacegroup, cell, resolution)
    return cell, spacegroup, grid_sampling


def symmetry_from_model_metadata_pdb(model):
    '''
    Generate Cell, Spacegroup and a default Grid_Sampling from the PDB
    CRYST1 card.
    '''
    cryst1 = model.metadata['CRYST1'][0].split()
    abc = [float(a) for a in cryst1[1:4]]
    angles = [float(c) for c in cryst1[4:7]]
    symstr = ' '.join(cryst1[7:])

    remarks = model.metadata['REMARK']
    i = 0

    '''
    Get the resolution. We need this to define a Grid_sampling
    for the unit cell (needed even in the absence of a map since
    atomic symmetry lookups are done with integerised symops for
    performance). We want to be as forgiving as possible at this
    stage - we'll use the official resolution if we find it, and
    set a default resolution if we don't. This will be overridden
    by the value from any mtz file that's loaded later.
    '''
    try:
        while 'REMARK   2' not in remarks[i]:
            i += 1
        # The first 'REMARK   2' line is blank by convention, and
        # resolution is on the second line
        i += 1
        line = remarks[i].split()
        res = line[3]
    except:
        res = 3.0

    # '''
    # The spacegroup identifier tends to be the most unreliable part
    # of the CRYST1 card, so it's considered safer to let Clipper
    # infer it from the list of symmetry operators at remark 290. This
    # typically looks something like the following:
    #
    # REMARK 290      SYMOP   SYMMETRY
    # REMARK 290     NNNMMM   OPERATOR
    # REMARK 290       1555   X,Y,Z
    # REMARK 290       2555   -X,-Y,Z+1/2
    # REMARK 290       3555   -Y+1/2,X+1/2,Z+1/4
    # REMARK 290       4555   Y+1/2,-X+1/2,Z+3/4
    # REMARK 290       5555   -X+1/2,Y+1/2,-Z+1/4
    # REMARK 290       6555   X+1/2,-Y+1/2,-Z+3/4
    # REMARK 290       7555   Y,X,-Z
    # REMARK 290       8555   -Y,-X,-Z+1/2
    #
    # Clipper is able to initialise a Spacegroup object from a
    # string containing a semicolon-delimited list of the symop
    # descriptors in the SYMMETRY OPERATOR column, so we need to
    # parse those out.
    # '''
    # # Find the start of the REMARK 290 section
    # while 'REMARK 290' not in remarks[i]:
    #     i += 1
    # while 'NNNMMM' not in remarks[i]:
    #     i += 1
    # i+=1
    # symstr = ''
    # thisline = remarks[i]
    # while 'X' in thisline and 'Y' in thisline and 'Z' in thisline:
    #     if len(symstr):
    #         symstr += ';'
    #     splitline = thisline.split()
    #     symstr += splitline[3]
    #     i+=1
    #     thisline = remarks[i]


    cell_descr = clipper.Cell_descr(*abc, *angles)
    cell = clipper.Cell(cell_descr)
    spgr_descr = clipper.Spgr_descr(symstr)
    spacegroup = clipper.Spacegroup(spgr_descr)
    resolution = clipper.Resolution(float(res))
    grid_sampling = clipper.Grid_sampling(spacegroup, cell, resolution)
    return cell, spacegroup, grid_sampling



def set_to_default_cartoon(session, model = None):
    '''
    Adjust the ribbon representation to provide information without
    getting in the way.
    '''
    try:
        if model is None:
            atoms = None
        else:
            arg = atomspec.AtomSpecArg('thearg')
            atoms = arg.parse('#' + model.id_string(), session)[0]
        cartoon.cartoon(session, atoms = atoms, suppress_backbone_display=False)
        cartoon.cartoon_style(session, atoms = atoms, width=0.4, thickness=0.1, arrows_helix=True, arrow_scale = 2)
        cartoon.cartoon_tether(session, structures=atoms, opacity=0)
    except:
        return

class XmapSet(Model):
    '''
    Handles creation, deletion, recalculation and visualisation of
    crystallographic maps based on the current model and a set of observed
    reflection data (FOBS, SIGFOBS).
    '''

    STANDARD_LOW_CONTOUR = numpy.array([1.5])
    STANDARD_HIGH_CONTOUR = numpy.array([2.0])
    STANDARD_DIFFERENCE_MAP_CONTOURS = numpy.array([-3.0, 3.0])

    DEFAULT_MESH_MAP_COLOR = [0,1.0,1.0,1.0] # Solid cyan
    DEFAULT_SOLID_MAP_COLOR = [0,1.0,1.0,0.4] # Transparent cyan
    DEFAULT_DIFF_MAP_COLORS = [[1.0,0,0,1.0],[0,1.0,0,1.0]] #Solid red and green


    def __init__(self, session, crystal, fsigf, atoms, bsharp_vals=[],
                 exclude_free_reflections=True, fill_with_fcalc=True,
                 display_radius = 12):
        '''
        Prepare the C++ Xtal_mgr object and create a set of crystallographic
        maps. The standard 2mFo-DFc and mFo-DFc maps will always be created,
        while any number of maps with different sharpening/smoothing can be
        created by providing a list of b-factors in bsharp_vals.
        Args:
            session:
                The ChimeraX session
            crystal:
                The parent XtalSymmetryHandler object
            fsigf:
                A Clipper HKL_data_F_sigF_float object containing the observed
                amplitudes and standard deviations.
            atoms:
                A ChimeraX `Atoms` object encompassing the atoms to be used to
                calculate the maps. Unless deliberately generating omit
                maps, this should contain all atoms in the model.
            bsharp_vals:
                For each value in this list, a 2mFo-DFc map will be generated
                with the given B_sharp value. A negative B_sharp yields a
                sharpened map, while a positive B_sharp gives smoothing. As a
                rough rule of thumb, a value of B_sharp=-100 tends to be
                reasonable for a 3.8 Angstrom map, and -50 for 3 Angstroms.
                For maps with resolutions better than ~2 Angstroms, it may be
                useful in some circumstances to apply smoothing. This can
                sometimes bring out weaker, low-resolution features hidden by
                high-resolution noise in standard maps.
            exclude_free_reflections:
                If True, observed amplitudes corresponding to the free set will
                not be used in generating the maps. The values used in their
                place will depend on the value of `fill_with_fcalc`. If the maps
                are to be used solely for viewing it is safe to include the
                free set, but inclusion when actively fitting a model will
                render your Rfree statistic meaningless.
            fill_with_fcalc:
                If `exclude_free_reflections` is False this argument will be
                ignored. Otherwise, if `fill_with_fcalc` is True then the
                excluded amplitudes will be replaced by sigmaa-weighted F(calc).
                If False, the excluded amplitudes will be set to zero.
            display_radius:
                The radius (in Angstroms) of the display sphere used in
                live scrolling mode.
        '''
        Model.__init__(self, 'Real-space maps', session)
        self.crystal = crystal
        from chimerax.core.triggerset import TriggerSet
        trig = self.triggers = TriggerSet()

        trigger_names = (
            'map box changed',  # Changed shape of box for map viewing
            'map box moved',    # Just changed the centre of the box
        )
        for t in trigger_names:
            trig.add_trigger(t)
        #############
        # Variables involved in handling live redrawing of maps in a box
        # centred on the cofr
        #############

        # Handler for live box update
        self._box_update_handler = None
        # Is the box already initialised?
        self._box_initialized = False
        # Object storing the parameters required for masking (used after
        # adjusting contours)
        self._surface_zone = Surface_Zone(display_radius, None, None)
        # Is the map box moving with the centre of rotation?
        self._live_scrolling = False
        # Radius of the sphere in which the map will be displayed when
        # in live-scrolling mode
        self.display_radius = display_radius
        # Actual box dimensions in (u,v,w) grid coordinates
        self._box_dimensions = None
        # Centre of the box (used when tracking the centre of rotation)
        self._box_center = None
        # Last grid coordinate of the box centre. We only need to update
        # the map if the new centre maps to a different integer grid point
        self._box_center_grid = None
        # Minimum corner of the box in (x,y,z) coordinates. This must
        # correspond to the grid coordinate in self._box_corner_grid
        self._box_corner_xyz = None
        # Minimum corner of the box in grid coordinates
        self._box_corner_grid = None


        self.live_scrolling = True

        self._box_initialized = True

        # The master C++ manager for handling all map operations
        from .clipper_python.ext import Xtal_mgr
        xm = self._xtal_mgr = Xtal_mgr(crystal.hkl_info,
            crystal.mtzdata.free_flags.data, crystal.grid, fsigf.data)

        from . import atom_list_from_sel
        xm.generate_fcalc(atom_list_from_sel(atoms))
        xm.generate_base_map_coeffs()
        xm.add_xmap('2mFo-DFc', xm.base_2fofc, 0, is_difference_map=False,
            exclude_free_reflections=True, fill_with_fcalc=True)
        xm.add_xmap('mFo-DFc', xm.base_fofc, 0, is_difference_map=True,
            exclude_free_reflections=True)

        for b in bsharp_vals:
            if b == 0:
                continue
            elif b < 0:
                name_str = "2mFo-DFc_sharp_{:.0f}".format(-b)
            else:
                name_str = "2mFo-DFc_smooth_{:.0f}".format(b)
            xm.add_xmap(name_str, xm.base_2fofc, b, is_difference_map=False,
                exclude_free_reflections=True, fill_with_fcalc=True)

        self.display=False
        # Apply the surface mask
        self.session.triggers.add_handler('frame drawn', self._rezone_once_cb)
        # self._reapply_zone()

    def _rezone_once_cb(self, *_):
        self.display = True
        from chimerax.core.triggerset import DEREGISTER
        return DEREGISTER

    @property
    def hklinfo(self):
        return self.crystal.hklinfo

    @property
    def spacegroup(self):
        return self.crystal.spacegroup

    @property
    def cell(self):
        return self.crystal.cell

    @property
    def res(self):
        return self.hklinfo.resolution

    @property
    def grid(self):
        return self.crystal.grid

    @property
    def voxel_size(self):
        return self.cell.dim / self.grid.dim

    @property
    def voxel_size_frac(self):
        return 1/ self.grid.dim

    @property
    def unit_cell(self):
        return self.crystal.unit_cell

    @property
    def display_radius(self):
        return self._display_radius

    @display_radius.setter
    def display_radius(self, radius):
        '''Set the radius (in Angstroms) of the live map display sphere.'''
        self._display_radius = radius
        v = self.session.view
        cofr = self._box_center = v.center_of_rotation
        self._box_center_grid = clipper.Coord_orth(cofr).coord_frac(self.cell).coord_grid(self.grid)
        dim = self._box_dimensions = \
            2 * calculate_grid_padding(radius, self.grid, self.cell)
        self._box_corner_grid, self._box_corner_xyz = _find_box_corner(
            cofr, self.cell, self.grid, radius)
        self.triggers.activate_trigger('map box changed',
            (self._box_corner_xyz, self._box_corner_grid, dim))
        self._surface_zone.update(radius, coords = numpy.array([cofr]))
        self._reapply_zone()

    @property
    def live_scrolling(self):
        '''Turn live map scrolling on and off.'''
        return self._live_scrolling

    @live_scrolling.setter
    def live_scrolling(self, switch):
        if switch:
            self.position = Place()
            if not self._live_scrolling:
                '''
                Set the box dimensions to match the stored radius.
                '''
                self.display_radius = self._display_radius
            self._start_live_scrolling()
        else:
            self._stop_live_scrolling()

    @property
    def display(self):
        return super().display

    @display.setter
    def display(self, switch):
        if switch:
            if self.live_scrolling:
                self._start_live_scrolling()
        Model.display.fset(self, switch)

    def _start_live_scrolling(self):
        if self._box_update_handler is None:
            self._box_update_handler = self.crystal.triggers.add_handler(
                'box center moved', self.update_box)
        if self._box_center is not None:
            self.update_box(None, (self._box_center, self._box_center_grid), force=True)
        self.positions = Places()
        self._live_scrolling = True

    def _stop_live_scrolling(self):
        if self._box_update_handler is not None:
            self.crystal.triggers.remove_handler(self._box_update_handler)
            self._box_update_handler = None
        self._live_scrolling = False

    def __getitem__(self, name_or_index):
        '''Get one of the child maps by name or index.'''
        if type(name_or_index) == str:
            for m in self.child_models():
                if m.name == name_or_index:
                    return m
            raise KeyError('No map with that name!')
        else:
            return self.child_models()[name_or_index]


    def set_box_limits(self, minmax):
        '''
        Set the map box to fill a volume encompassed by the provided minimum
        and maximum grid coordinates. Automatically turns off live scrolling.
        '''
        self.live_scrolling = False
        cmin = clipper.Coord_grid(minmax[0])
        cmin_xyz = cmin.coord_frac(self.grid).coord_orth(self.cell).xyz
        dim = (minmax[1]-minmax[0])
        self.triggers.activate_trigger('map box changed',
            (cmin_xyz, cmin, dim))

    def cover_unit_cells(self, nuvw = [1,1,1], offset = [0,0,0]):
        '''
        Expand the map(s) to cover multiple unit cells. In order to
        maintain reasonable performance, this method cheats a little by
        filling just one unit cell and then tiling it using the graphics
        engine. This leaves some minor artefacts at the cell edges, but
        is a worthwhile tradeoff.
        Automatically turns off live scrolling.
        Args:
            nuvw (array of 3 positive integers):
                Number of unit cells to show in each direction.
            offset (array of 3 integers):
                Shifts the starting corner of the displayed volume by
                this number of unit cells in each direction.
        '''
        self.live_scrolling = False
        uc = self.unit_cell
        box_min_grid = uc.min.uvw
        # Add a little padding to the max to create a slight overlap between copies
        box_max_grid = (uc.max+clipper.Coord_grid([2,2,2])).uvw
        minmax = [box_min_grid, box_max_grid]
        self.set_box_limits(minmax)
        self._surface_zone.update(None, None)
        # Tile by the desired number of cells
        places = []
        grid_dim = self.grid.dim
        nu, nv, nw = nuvw
        ou, ov, ow = offset
        for i in range(ou, nu+ou):
            for j in range(ov, nv+ov):
                for k in range(ow, nw+ow):
                    thisgrid = clipper.Coord_grid(numpy.array([i,j,k])*grid_dim)
                    thisorigin = thisgrid.coord_frac(self.grid).coord_orth(self.cell).xyz
                    places.append(Place(origin = thisorigin))
        self.positions = Places(places)



    def add_nxmap_handler(self, volume):
        from .real_space_map import NXmapHandler
        m = NXmapHandler(self.session, self, volume)
        self.add([m])


    def add_xmap_handler(self, dataset, is_difference_map = None,
                color = None, style = None, contour = None):
        '''
        Add a new XmapHandler based on the given reflections and phases.
        Args:
            dataset:
                a ReflectionData_Calc object.
            is_difference_map:
                Decides whether this map is to be treated as a difference
                map (with positive and negative contours) or a standard
                map with positive contours only. Leave as None to allow
                this to be determined automatically from the dataset,
                or set it to True or False to force an explicit choice.
            color:
                an array of [r, g, b, alpha] as integers in the range 0-255
                for a positive density map, or
                [[r,g,b,alpha],[r,g,b,alpha]] representing the colours of
                the positive and negative contours respectively if the
                map is a difference map
            style:
                one of 'mesh' or 'surface'
            contour:
                The value(s) (in sigma units) at which to contour the map
                on initial loading. For a standard map this should be a
                single value; for a difference map it should be
                [negative contour, positive contour]
        '''
        data = dataset.data
        new_xmap = Xmap(self.spacegroup, self.cell, self.grid, name = dataset.name, hkldata = data)
        if is_difference_map is None:
            is_difference_map = dataset.is_difference_map
        new_xmap.is_difference_map = is_difference_map
        if is_difference_map and color is not None and len(color) != 2:
            err_string = '''
            ERROR: For a difference map you need to define colours for
            both positive and negative contours, as:
            [[r,g,b,a],[r,g,b,a]] in order [positive, negative].
            '''
            raise TypeError(err_string)
        new_handler = XmapHandler(self.session, self, dataset.name, new_xmap,
            self._box_corner_xyz, self._box_corner_grid, self._box_dimensions)
        if style is None:
            style = 'mesh'
        if color is None:
            if is_difference_map:
                color = self.DEFAULT_DIFF_MAP_COLORS
            elif style == 'mesh':
                color = [self.DEFAULT_MESH_MAP_COLOR]
            else:
                color = [self.DEFAULT_SOLID_MAP_COLOR]
        if contour is None:
            if is_difference_map:
                contour = self.STANDARD_DIFFERENCE_MAP_CONTOURS
            else:
                contour = self.STANDARD_LOW_CONTOUR
        elif not hasattr(contour, '__len__'):
                contour = numpy.array([contour])
        else:
            contour = numpy.array(contour)
        contour = contour * new_xmap.sigma
        self.add([new_handler])
        new_handler.set_representation(style)
        new_handler.set_parameters(**{'cap_faces': False,
                                  'surface_levels': contour,
                                  'show_outline_box': False,
                                  'surface_colors': color,
                                  'square_mesh': True})
        # new_handler.update_surface()
        new_handler.show()

    def update_box(self, trigger_name, new_center, force=True):
        '''Update the map box to surround the current centre of rotation.'''
        center, center_grid = new_center
        self._box_center = center
        self._box_center_grid = center_grid
        if not self.visible and not force:
            # Just store the box parameters for when we're re-displayed
            return
        if self.live_scrolling:
            box_corner_grid, box_corner_xyz = _find_box_corner(center, self.cell, self.grid, self.display_radius)
            self.triggers.activate_trigger('map box moved', (box_corner_xyz, box_corner_grid, self._box_dimensions))
            self._surface_zone.update(self.display_radius, coords = numpy.array([center]))
            self._reapply_zone()

    def _reapply_zone(self):
        '''
        Reapply any surface zone applied to the volume after changing box
        position.
        '''
        coords = self._surface_zone.all_coords
        radius = self._surface_zone.distance
        if coords is not None:
            surface_zones(self, coords, radius)

    def delete(self):
        self.live_scrolling = False
        super(XmapSet, self).delete()


def calculate_grid_padding(radius, grid, cell):
    '''
    Calculate the number of grid steps needed on each crystallographic axis
    in order to capture at least radius angstroms in x, y and z.
    '''
    corner_mask = numpy.array([[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,0,0],[1,1,1]])
    corners = (corner_mask * radius).astype(float)
    grid_upper = numpy.zeros([8,3], numpy.int)
    grid_lower = numpy.zeros([8,3], numpy.int)
    for i, c in enumerate(corners):
        co = clipper.Coord_orth(c)
        cm = co.coord_frac(cell).coord_map(grid).uvw
        grid_upper[i,:] = numpy.ceil(cm).astype(int)
        grid_lower[i,:] = numpy.floor(cm).astype(int)
    return grid_upper.max(axis=0) - grid_lower.min(axis=0)

def find_box_corner(center, cell, grid, radius=20):
    return _find_box_corner(center, cell, grid, radius)

def _find_box_corner(center, cell, grid, radius = 20):
    '''
    Find the bottom corner (i.e. the origin) of a rhombohedral box
    big enough to hold a sphere of the desired radius.
    '''
    radii_frac = clipper.Coord_frac(radius/cell.dim)
    center_frac = clipper.Coord_orth(center).coord_frac(cell)
    bottom_corner_grid = center_frac.coord_grid(grid) \
                - clipper.Coord_grid(calculate_grid_padding(radius, grid, cell))
    bottom_corner_orth = bottom_corner_grid.coord_frac(grid).coord_orth(cell)
    return bottom_corner_grid, bottom_corner_orth.xyz

def _get_bounding_box(coords, padding, grid, cell):
    '''
    Find the minimum and maximum grid coordinates of a box which will
    encompass the given (x,y,z) coordinates plus padding (in Angstroms).
    '''
    grid_pad = calculate_grid_padding(padding, grid, cell)
    box_bounds_grid = clipper.Util.get_minmax_grid(coords, cell, grid)\
                        + numpy.array((-grid_pad, grid_pad))
    box_origin_grid = box_bounds_grid[0]
    box_origin_xyz = clipper.Coord_grid(box_origin_grid).coord_frac(grid).coord_orth(cell)
    dim = box_bounds_grid[1] - box_bounds_grid[0]
    return [box_origin_grid, box_origin_xyz, dim]

from .clipper_python import Xmap_float
class Xmap(Xmap_float):
    def __init__(self, spacegroup, cell, grid_sampling,
                 name = None, hkldata = None, is_difference_map = None):
        super().__init__(spacegroup, cell, grid_sampling)
        self.name = name
        self.is_difference_map = is_difference_map
        if hkldata is not None:
            self.fft_from(hkldata)
        from .clipper_python import Map_stats
        self._stats = Map_stats(self)

    @property
    def stats(self):
        if self._stats is None:
            from .clipper_python import Map_stats
            self._stats = Map_stats(self)
        return self._stats

    @property
    def mean(self):
        return self.stats.mean

    @property
    def std_dev(self):
        return self.stats.std_dev

    @property
    def sigma(self):
        return self.stats.std_dev

    @property
    def min(self):
        return self.stats.min

    @property
    def max(self):
        return self.stats.max

    @property
    def range(self):
        return self.stats.range




class XmapHandler(Volume):
    '''
    An XmapHandler is in effect a resizable window into a periodic
    crystallographic map. The actual map data (a clipper Xmap object) is
    held within, and filled into the XmapWindow.data array as needed.
    Methods are included for both live updating (e.g. tracking and filling
    a box centred on the centre of rotation) and static display of a
    given region.
    '''
    def __init__(self, session, manager, name, xmap, origin, grid_origin, dim):
        '''
        Args:
            sesssion:
                The ChimeraX session
            crystal:
                The CrystalStructure object this belongs to
            name:
                A descriptive name for this map
            xmap:
                A clipper.Xmap
            origin:
                The (x,y,z) coordinates of the bottom left corner of the
                volume.
            grid_origin:
                The (u,v,w) integer grid coordinates corresponding to
                origin.
            dim:
                The shape of the box in (u,v,w) grid coordinates.
        '''
        self.box_params = (origin, grid_origin, dim)
        self.xmap = xmap
        self.manager = manager
        darray = self._generate_and_fill_data_array(origin, grid_origin, dim)
        Volume.__init__(self, darray, session)

        self.is_difference_map = xmap.is_difference_map
        self.name = name
        self.initialize_thresholds()

        # If the box shape changes while the volume is hidden, the change
        # will not be applied until it's shown again.
        self._needs_update = True
        self.show()
        self._box_shape_changed_cb_handler = self.manager.triggers.add_handler(
            'map box changed', self._box_changed_cb)
        self._box_moved_cb_handler = self.manager.triggers.add_handler(
            'map box moved', self._box_moved_cb)



    def show(self, *args, **kwargs):
        if self._needs_update:
            self._swap_volume_data(self.box_params, force_update = True)
            self._needs_update = False
        else:
            # Just set the origin and fill the box with the data for
            # the current location
            origin, grid_origin, ignore = self.box_params
            self._fill_volume_data(self._data_fill_target, grid_origin)
        super(XmapHandler, self).show(*args, **kwargs)

    @property
    def hklinfo(self):
        return self.manager.hklinfo

    @property
    def spacegroup(self):
        return self.manager.spacegroup

    @property
    def cell(self):
        return self.manager.cell

    @property
    def res(self):
        return self.hklinfo.resolution

    @property
    def grid(self):
        return self.manager.grid

    @property
    def voxel_size(self):
        return self.cell.dim / self.grid.dim

    @property
    def voxel_size_frac(self):
        return 1/ self.grid.dim

    @property
    def unit_cell(self):
        return self.manager.unit_cell

    @property
    def _surface_zone(self):
        return self.manager._surface_zone

    def mean_sd_rms(self):
        '''
        Overrides the standard Volume method to give the overall values
        from the Clipper object.
        '''
        x = self.xmap
        # RMS is not currently calculated by Clipper, so we'll just return
        # the sigma twice.
        return (x.mean, x.sigma, x.sigma)


    def _box_changed_cb(self, name, params):
        self.box_params = params
        self._needs_update = True
        if not self.display:
            # No sense in wasting cycles on this if the volume is hidden.
            # We'll just store the params and apply them when we show the
            # volume.
            # NOTE: this means we need to over-ride show() to ensure
            # it's updated before re-displaying.
            return
        self._swap_volume_data(params)
        self.data.values_changed()
        self.show()

    def _box_moved_cb(self, name, params):
        self.box_params = params
        if not self.display:
            return
        self.data.set_origin(params[0])
        self._fill_volume_data(self._data_fill_target, params[1])
        self.data.values_changed()

    def delete(self):
        bh = self._box_shape_changed_cb_handler
        if bh is not None:
            self.manager.triggers.remove_handler(bh)
            self._box_shape_changed_cb_handler = None
        bm = self._box_moved_cb_handler
        if bm is not None:
            self.manager.triggers.remove_handler(bm)
            self._box_moved_cb_handler = None
        super(XmapHandler, self).delete()




    def _swap_volume_data(self, params, force_update = False):
        '''
        Replace this Volume's data array with one of a new shape/size
        Args:
            params:
                A tuple of (new_origin, new_grid_origin, new_dim)
        '''
        if not self._needs_update and not force_update:
            # Just store the parameters
            self.box_params = params
            return
        new_origin, new_grid_origin, new_dim = params
        darray = self._generate_and_fill_data_array(new_origin, new_grid_origin, new_dim)
        self._box_dimensions = new_dim
        self.replace_data(darray)
        self.new_region(ijk_min=(0,0,0), ijk_max=darray.size, ijk_step=(1,1,1), adjust_step=False)

    def _generate_and_fill_data_array(self, origin, grid_origin, dim):
        data = self._data_fill_target = numpy.empty(dim, numpy.double)
        self._fill_volume_data(data, grid_origin)
        order = numpy.array([2,1,0], int)
        darray = Array_Grid_Data(data.transpose(), origin = origin,
            step = self.voxel_size, cell_angles = self.cell.angles_deg)
        return darray


    def _fill_volume_data(self, target, start_grid_coor):
        #shape = (numpy.array(target.shape)[::-1] - 1)
        #end_grid_coor = start_grid_coor + clipper.Coord_grid(shape)
        #self.data.set_origin(origin_xyz)
        from .clipper_python import Coord_grid
        xmap = self.xmap
        xmap.export_section_numpy(Coord_grid(start_grid_coor), target)

    # def update_drawings(self):
    #     super().update_drawings()
    #     if hasattr(self, '_surface_zone'):
    #         sz = self._surface_zone
    #         coords = sz.all_coords
    #         distance = sz.distance
    #         if coords is not None:
    #             from chimerax.surface.zone import surface_zone
    #             surface_zone(self, coords, distance)