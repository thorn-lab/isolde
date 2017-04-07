import numpy
from .main import atom_list_from_sel
from . import clipper
from .lib import clipper_python_core as clipper_core
from .clipper_mtz import Clipper_MTZ
from .data_tree import db_levels, DataTree
from collections import defaultdict
from chimerax.core.atomic import AtomicStructure, concatenate
from chimerax.core.geometry import Place, Places
from chimerax.core.geometry import find_close_points, find_close_points_sets
from chimerax.core.surface import zone
from chimerax.core.models import Model, Drawing
from chimerax.core.commands import camera, cofr
from chimerax.core.map.data import Array_Grid_Data
from chimerax.core.map import Volume, volumecommand

def move_model(session, model, new_parent):
    '''
    Temporary method until something similar is added to the ChimeraX
    core. Picks up a model from the ChimeraX model tree and transplants
    it (with all its children intact) as the child of a different model.
    '''

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
    '''
    Generate Cell, Spacegroup and a default Grid_Sampling from the PDB
    CRYST1 card (or mmCIF equivalent metadata once it's available in
    ChimeraX).
    '''
    if 'CRYST1' in model.metadata.keys():
        cryst1 = model.metadata['CRYST1'][0].split()
        abc = cryst1[1:4]
        angles = cryst1[4:7]

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

        '''
        The spacegroup identifier tends to be the most unreliable part
        of the CRYST1 card, so it's considered safer to let Clipper
        infer it from the list of symmetry operators at remark 290. This
        typically looks something like the following:

        REMARK 290      SYMOP   SYMMETRY
        REMARK 290     NNNMMM   OPERATOR
        REMARK 290       1555   X,Y,Z
        REMARK 290       2555   -X,-Y,Z+1/2
        REMARK 290       3555   -Y+1/2,X+1/2,Z+1/4
        REMARK 290       4555   Y+1/2,-X+1/2,Z+3/4
        REMARK 290       5555   -X+1/2,Y+1/2,-Z+1/4
        REMARK 290       6555   X+1/2,-Y+1/2,-Z+3/4
        REMARK 290       7555   Y,X,-Z
        REMARK 290       8555   -Y,-X,-Z+1/2

        Clipper is able to initialise a Spacegroup object from a
        string containing a semicolon-delimited list of the symop
        descriptors in the SYMMETRY OPERATOR column, so we need to
        parse those out.
        '''
        # Find the start of the REMARK 290 section
        while remarks[i][0:10] != 'REMARK 290':
            i += 1
        while 'NNNMMM' not in remarks[i]:
            i += 1
        i+=1
        symstr = ''
        thisline = remarks[i]
        while 'X' in thisline and 'Y' in thisline and 'Z' in thisline:
            if len(symstr):
                symstr += ';'
            splitline = thisline.split()
            symstr += splitline[3]
            i+=1
            thisline = remarks[i]




    # TODO: add equivalent lookup for mmCIF metadata once available

    cell_descr = clipper.Cell_descr(*abc, *angles)
    cell = clipper.Cell(cell_descr)
    spgr_descr = clipper.Spgr_descr(symstr)
    spacegroup = clipper.Spacegroup(spgr_descr)
    resolution = clipper.Resolution(res)
    grid_sampling = clipper.Grid_sampling(spacegroup, cell, resolution)
    return cell, spacegroup, grid_sampling





class CrystalStructure(Model):
    '''
    Master container class for a crystal structure, designed to act as the
    head node of a Model tree with the following general format:

    CrystalStructure
      |
      -- master model (AtomicStructure)
      |
      -- symmetry copies (SymModels)
      |    |
      |    -- AtomicStructure
      |    |
      |    -- AtomicStructure
      |    |
      |    -- ...
      |
      -- reciprocal space data (ReflectionDataContainer)
      |    |
      |    -- Free Flags (ReflectionData_FreeFlags)
      |    |
      |    -- Experimental (ReflectionData_Node)
      |    |    |
      |    |    -- F/SigF (ReflectionData_Exp)
      |    |    |
      |    |    -- ...
      |    |
      |    -- Calculated (ReflectionData_Calc)
      |         |
      |         -- 2mFo-DFc (ReflectionData_Calc)
      |         |
      |         -- ...
      |
      |
      -- real-space maps (XMapSet)
           |
           -- 2mFo-Fc (Volume)
           |
           -- ...
    '''

    def __init__(self, session, model, mtzfile = None, show_nonpolar_H = False):
        '''
        Create a new crystal structure object from an atomic model and
        (optionally) a set of reciprocal-space data.
        Args:
            session:
                The ChimeraX session.
            model:
                A loaded AtomicStructure model. NOTE: this will be moved from
                its existing place in the session.models tree to become a
                child of this one.
            mtzdata:
                An MTZ_Data object containing experimental and/or calculated
                amplitudes and phases
            show_nonpolar_H:
                Do you want non-polar hydrogens to be visible in all default
                visualisations?
        '''
        name = 'Crystal (' + model.name +')'
        Model.__init__(self, name, session)
        self.session.models.add([self])
        move_model(self.session, model, self)
        self.master_model = model
        if mtzfile is not None:
            from .clipper_mtz_new import ReflectionDataContainer
            self.mtzdata = ReflectionDataContainer(self.session, mtzfile)
            self.add([self.mtzdata])
            self.cell = mtzdata.cell
            self.sg = mtzdata.spacegroup
            self.grid = mtzdata.grid_sampling
            self.hklinfo = mtzdata.hklinfo
        else:
            self.cell, self.sg, self.grid = symmetry_from_model_metadata(model)

        self._voxel_size = self.cell.dim / self.grid.dim

        self.show_nonpolar_H = show_nonpolar_H

        ref = model.bounds().center()

        # Convert the atoms to a format recognised by Clipper
        self._clipper_atoms = atom_list_from_sel(model.atoms)
        # A C++ object holding the symmetry operations required to pack one
        # unit cell relative to the current atomic model, along with fast
        # functions returning the symops necessary to pack a given box in
        # xyz space.
        self.unit_cell = clipper.Unit_Cell(ref,
                    self._clipper_atoms, cell, spacegroup, grid_sampling)


        # Container for managing all the symmetry copies
        self._sym_model_container = None
        # Do we want to find and show atoms in the search radius at each iteration?
        self.sym_show_atoms = True
        # Do we want to show symmetry equivalent molecules live as we move
        # around?
        self._show_symmetry = False
        # Do we want to always have the reference model shown?
        self.sym_always_shows_reference_model = True
        # Trigger handler for live display of symmetry
        self._sym_handler = None
        # Centroid of the search space for symmetry equivalents
        self._sym_box_center = None
        # Half-width of the box in which we want to search
        self._sym_box_radius = None
        # Grid dimensions of the box
        self._sym_box_dimensions = None
        # Is the box already initialised?
        self._sym_box_initialized = False
        # Last grid coordinate for the cofr at which the symmetry was updated
        self._sym_last_cofr_grid = None
        # Factor defining the frequency of steps in the symmetry search
        # (larger number = more steps)
        self._sym_search_frequency = 2

    @property
    def is_live(self):
        return self._sym_handler is not None

    @property
    def sym_box_radius(self):
        return self._sym_box_radius

    @sym_box_radius.setter
    def sym_box_radius(self, radius):
        self._change_sym_box_radius(radius)

    @property
    def sym_model_container(self):
        if self._sym_model_container is None:
            self._sym_model_container = SymModels(self.session, self)
        return self._sym_model_container

    def items(self):
        return ((clipper.RTop_frac.identity(), self.master_model), *self.sym_model_container.items())

    def add_model_to_self(self, model):
        '''
        Transplant a model from
        '''

    def sym_select_within(self, coords, radius):
        '''
        Given an array of (x,y,z) coordinates, return a list of Atoms lists
        (one per symmetry equivalent molecule) covering all atoms within
        radius of any input coordinate.
        Args:
          coords:
            An (n * [x,y,z)) array of coordinates
          radius:
            Search radius in Angstroms
        '''
        c = numpy.empty((len(coords), 3), numpy.float32)
        c[:] = coords
        master_atoms = self.master_model.atoms
        master_coords = master_atoms.coords.astype(numpy.float32)
        grid_minmax = clipper.Util.get_minmax_grid(coords, self.cell, self.grid)
        pad = calculate_grid_padding(radius, self.grid, self.cell)
        grid_minmax += numpy.array((-pad, pad))
        min_xyz = clipper.Coord_grid(grid_minmax[0]).coord_frac(self.grid).coord_orth(self.cell).xyz
        dim = grid_minmax[1] - grid_minmax[0]
        symops = self.unit_cell.all_symops_in_box(min_xyz, dim)
        symmats = symops.all_matrices_orth(self.cell, format = '3x4')
        target = [(c, Place().matrix.astype(numpy.float32))]
        search_list = []
        model_list = []
        for i, s in enumerate(symops):
            search_list.append((master_coords, symmats[i].astype(numpy.float32)))
            model_list.append(self.sym_model_container[s])
        i1, i2 = find_close_points_sets(search_list, target, radius)

        found = []
        for i, c in enumerate(i1):
            if len(c):
                found.append(model_list[i].atoms[c])
        return found

    def initialize_symmetry_display(self, radius = 20):
        '''
        Continually update the display to show all symmetry equivalents of
        the atomic model which enter a box of the given size, centred on the
        centre of rotation.

        Args:
          radius (float):
            The search volume is actually the smallest parallelepiped defined
            by the same angles as the unit cell, which will contain a sphere
            of the given radius.
        '''
        if self._sym_box_initialized:
            raise RuntimeError('''
              The symmetry box is already intialised for this structure. If you
              want to reset it, run sym_box_reset().
              ''')
        camera.camera(self.session, 'ortho')
        cofr.cofr(self.session, 'centerOfView')
        self.sym_always_shows_reference_model = True
        self._sym_box_radius = radius
        uc = self.unit_cell
        v = self.session.view
        c = self.cell
        g = self.grid
        self._sym_box_center = v.center_of_rotation
        self._sym_last_cofr_grid = clipper.Coord_orth(self._sym_box_center).coord_frac(c).coord_grid(g)
        box_corner_grid, box_corner_xyz = _find_box_corner(self._sym_box_center, c, g, radius)
        self._sym_box_dimensions = (numpy.ceil(radius / self._voxel_size * 2)).astype(int)
        self._update_sym_box(force_update = True)
        self._sym_box_go_live()
        self._sym_box_initialized = True

    def stop_symmetry_display(self):
        self._sym_box_go_static()
        for key, m in self.sym_model_container.items():
            m.display = False

    def _change_sym_box_radius(self, radius):
        dim = (numpy.ceil(radius / self._voxel_size * 2)).astype(int)
        self._sym_box_dimensions = dim
        self._sym_box_radius = radius

    def _update_sym_box(self, *_, force_update = False):
        v = self.session.view
        uc = self.unit_cell
        cofr = v.center_of_rotation
        cofr_grid = clipper.Coord_orth(cofr).coord_frac(self.cell).coord_grid(self.grid)
        if not force_update:
            if cofr_grid == self._sym_last_cofr_grid:
                return
        self._sym_last_cofr_grid = cofr_grid
        self._sym_box_center = cofr
        box_corner_grid, box_corner_xyz = _find_box_corner(
                  self._sym_box_center, self.cell,
                  self.grid, self._sym_box_radius)
        symops = uc.all_symops_in_box(box_corner_xyz,
                  self._sym_box_dimensions.astype(numpy.int32), self.sym_always_shows_reference_model,
                  sample_frequency = self._sym_search_frequency)
        l1 = []
        search_entry = [(numpy.array([cofr], numpy.float32), Place().matrix.astype(numpy.float32))]
        coords = self.master_model.atoms.coords.astype(numpy.float32)
        display_mask = numpy.array([False]*len(coords))
        if not self.show_nonpolar_H:
            h_mask = self.master_model.atoms.idatm_types != 'HC'
        for s in symops:
            this_model = self.sym_model_container[s]
            this_set = (coords, s.rtop_orth(self.cell).mat34.astype(numpy.float32))
            l1.append(this_set)
        i1, i2 = find_close_points_sets(l1, search_entry, self.sym_box_radius)
        for i, indices in enumerate(i1):
            this_model = self.sym_model_container[symops[i]]
            if len(indices):
                display_mask[:] = False
                a = this_model.atoms
                display_mask[a.indices(a[indices].residues.atoms)] = True
                if not self.show_nonpolar_H:
                    display_mask = numpy.logical_and(display_mask, h_mask)
                a.displays = display_mask
                #if this_model is not self.master_model:
                    #a.residues.ribbon_displays = display_mask
                this_model.display = True
            else:
                if this_model is not self.master_model:
                    this_model.display = False
        for s, m in self.sym_model_container.items():
            if s not in symops:
                m.display = False

    def show_large_scale_symmetry(self, box_width = 200):
        '''
        Show the model symmetry over a large volume by tiling the current
        representation of the master model
        '''
        box_center = self.master_model.bounds().center()
        uc = self.unit_cell
        dim = (numpy.ceil(box_width / self._voxel_size)).astype(int)
        box_corner_grid, box_corner_xyz = _find_box_corner(
                  box_center, self.cell,
                  self.grid, box_width/2)
        symops = uc.all_symops_in_box(box_corner_xyz, dim, True)
        num_symops = len(symops)
        sym_matrices = symops.all_matrices_orth(self.cell, format = '3x4')
        self.master_model.positions = Places(place_array=sym_matrices)

    def hide_large_scale_symmetry(self):
        self.master_model.position = Place()



    def _sym_box_go_live(self):
        if self._sym_handler is None:
            self._sym_handler = self.session.triggers.add_handler('new frame', self._update_sym_box)

    def _sym_box_go_static(self):
        if self._sym_handler is not None:
            self.session.triggers.remove_handler(self._sym_handler)
            self._sym_handler = None

class SymModels(defaultdict):
    '''
    Handles creation, destruction and organisation of symmetry copies
    of an atomic model. Uses the Clipper RTop_frac object for the given
    symop as the dict key. If the key is not found, automatically creates
    a copy of the master model, sets colours, applies the Place transform
    for the symop, and adds the model to the session.
    NOTE: the coordinates in each symmetry model are identical to
    those of the master model - the transform is only applied to the
    *visualisation* of the model, not the coordinates themselves.
    '''
    def __init__(self, session, parent):
        '''
        Just create an empty dict.
        Args:
          session:
            The ChimeraX session.
          parent:
            The AtomicCrystalStructure describing the master model and symmetry
        '''
        self.session = session
        self.parent = parent
        self.master = parent.master_model

        # Add a sub-model to the master to act as a container for the
        # symmetry copies
        self._sym_container = None

    @property
    def sym_container(self):
        if self._sym_container is None or self._sym_container.deleted:
            self._sym_container = Model('symmetry equivalents', self.session)
            self.parent.add([self._sym_container])
            self.clear()
        return self._sym_container

    def __missing__(self, key):
        if type(key) is not clipper.RTop_frac:
            raise TypeError('Key must be a clipper.RTop_frac!')
        thisplace = Place(matrix=key.rtop_orth(self.parent.cell).mat34)
        if not thisplace.is_identity():
            thismodel = self.master.copy(name=key.format_as_symop)
            atoms = thismodel.atoms
            #thismodel.position = thisplace
            atoms.coords = thisplace.moved(atoms.coords)
            atom_colors = atoms.colors
            atom_colors[:,0:3] = (self.master.atoms.colors[:,0:3].astype(float)*0.6).astype(numpy.uint8)
            atoms.colors = atom_colors
            ribbon_colors = thismodel.residues.ribbon_colors
            ribbon_colors[:,0:3] = (self.master.residues.ribbon_colors[:,0:3].astype(float)*0.6).astype(numpy.uint8)
            thismodel.residues.ribbon_colors = ribbon_colors
            self.sym_container.add([thismodel])
            set_to_default_cartoon(self.session, thismodel)
            self[key] = thismodel
            thismodel.display = False
            return thismodel
        return self.master

    def __getitem__(self, key):
        s = self.sym_container
        m = super(SymModels, self).__getitem__(key)
        return m


def set_to_default_cartoon(session, model = None):
        # Adjust the ribbon representation to provide information without
        # getting in the way
    from chimerax.core.commands import cartoon, atomspec
    if model is None:
        atoms = None
    else:
        arg = atomspec.AtomSpecArg('thearg')
        atoms = arg.parse('#' + model.id_string(), session)[0]
    cartoon.cartoon(session, atoms = atoms, suppress_backbone_display=False)
    cartoon.cartoon_style(session, atoms = atoms, width=0.4, thickness=0.1, arrows_helix=True, arrow_scale = 2)

def read_mtz(session, filename, experiment_name,
              atomic_model = None,
              auto_generate_maps = True,
              live_map_display = True):
    '''
    Read in an MTZ file and add its contents to the session.Clipper_DB
    database. Optionally, register an atomic model with the data to allow
    live display of symmetry equivalents, and/or automatically generate
    maps for any map data found in the file.
    Args:
      session:
        The ChimeraX session
      filename (string):
        The mtz file itself
      experiment_name (string):
        Name of the Xtal_Project to which this data will be added. If the
        name does not match an existing Xtal_Project, a new one will be
        created.
      atomic_model:
        A currently loaded ChimeraX AtomicStructure
      auto_generate_maps (bool):
        If true, a Map_Set object will be created containing one Xmap for
        each set of (F, Phi) data found in the MTZ file.
      live_map_display (bool):
        Only has an effect if auto_generated_maps is True. Maps will be
        displayed, with live updating within a sphere of 15 Angstroms radius
        around the centre of rotation.
    '''
    if not hasattr(session, 'Clipper_DB') or \
          experiment_name not in session.Clipper_DB['Experiment'].keys():
        project = Xtal_Project(session, experiment_name)
        xmapset = None
    else:
        project = session.Clipper_DB['Experiment'][experiment_name]
    # Bring in all the data from the MTZ file and add the corresponding
    # Clipper objects to the database
    crystal_name = project.load_data(filename)
    if auto_generate_maps:
        data_key = project.data.find_first_map_data(crystal_name)
        print(data_key)
        if data_key is not None:
            xmapset = project.add_maps(crystal_name, data_key)
            if atomic_model is not None:
        # Move the model to sit beneath a head Model object to act as a
        # container for symmetry models, annotations etc.
                from chimerax.core.models import Model
                m = Model(atomic_model.name, session)
                session.models.remove([atomic_model])
                m.add([atomic_model])
                session.models.add([m])
                xmapset.atomic_model = atomic_model
            if live_map_display:
                xmapset.initialize_box_display()
                if atomic_model:
                    xmapset.periodic_model.initialize_symmetry_display()

    return project, xmapset

class Surface_Zone:
    '''
    Add this as a property to a Volume object to provide it with the 
    necessary information to update its triangle mask after re-contouring.
    '''
    def __init__(self, distance, atoms = None, coords = None):
        '''
        Args:
          distance (float in Angstroms):
            distance from points to which the map will be masked
          atoms:
            Atoms to mask to (coordinates will be updated upon re-masking)
          coords:
            (x,y,z) coordinates to mask to (will not be updated upon 
            re-masking).
          
          Set both atoms and coords to None to disable automatic re-masking.
        '''
        self.update(distance, atoms, coords)
    
    def update(self, distance, atoms=None, coords = None):
        self.distance = distance
        self.atoms = atoms
        self.coords = coords
    
    @property
    def all_coords(self):
        if self.atoms is not None:
            if self.coords is not None:
                return numpy.concatenate(self.atoms.coords self.coords)
            return self.atoms.coords
        return self.coords

def surface_zones(models, points, distance):
    '''
    Essentially a copy of chimerax.core.surface.zone.surface_zone, but uses
    find_close_points_sets to eke a little extra performance
    '''
    vlist = []
    dlist = []
    ident_matrix = Place().matrix.astype(numpy.float32)
    search_entry = [(numpy.array(points, numpy.float32), Place().matrix.astype(numpy.float32))]
    for m in models:
        for d in m.child_drawings():
            if not d.display:
                continue
            dlist.append(d)
            vlist.append((d.vertices.astype(numpy.float32), ident_matrix))
  
    i1, i2 = find_close_points_sets(vlist, search_entry, distance)
  
    for vp, i, d in zip(vlist, i1, dlist):
        v = vp[0]
        nv = len(v)
        from numpy import zeros, bool, put, logical_and
        mask = zeros((nv,), bool)
        put(mask, i, 1)
        t = d.triangles
        if t is None:
            return
        tmask = logical_and(mask[t[:,0]], mask[t[:,1]])
        logical_and(tmask, mask[t[:,2]], tmask)
        d.triangle_mask = tmask



class XmapSet(Model):
    '''
    Each crystal will typically have multiple maps associated with it -
    the standard 2mFo-DFc and mFo-DFc maps, for a start, but also
    potentially sharpened/smoothed versions of these, anomalous difference
    maps, omit maps, etc. etc. etc.

    XmapSet is designed as a class to contain and organise these, control
    their display and recalculation, etc.
    '''
    
    STANDARD_LOW_CONTOUR = numpy.array([1.5])
    STANDARD_HIGH_CONTOUR = numpy.array([2.0])
    STANDARD_DIFFERENCE_MAP_CONTOURS = numpy.array([-3.0, 3.0])
    
    DEFAULT_MESH_MAP_COLOR = [0,1.0,1.0,1.0] # Solid cyan
    DEFAULT_SOLID_MAP_COLOR = [0,1.0,1.0,0.4] # Transparent cyan
    DEFAULT_DIFF_MAP_COLORS = [[1.0,0,0,1.0],[0,1.0,0,1.0]] #Solid red and green

    
    def __init__(self, session, datasets, 
                 live_scrolling = True, display_radius = 10,
                 atom_selection = None, padding = 3):
        '''
        Args:
            session:
                The ChimeraX session
            datasets:
                An iterable of ReflectionData_Calc objects
            live_scrolling:
                If True, the maps will be initialised in live scrolling
                mode, displaying a sphere of density centred on the 
                centre of rotation. This option takes precedence over
                atom_selection. 
            display_radius:
                The radius (in Angstroms) of the display sphere used in
                live scrolling mode.
            atom_selection:
                If live_scrolling is False, this argument must provide a
                selection of atoms around which the maps will be masked.
            padding:
                The radius (in Angstroms) of the mask surrounding each
                atom in atom_selection.
        '''
        if not live_scrolling and not atom_selection:
            raise TypeError('''
            If live_scrolling is False, you must provide a set of atoms
            to mask the maps to!
            ''')
        Model.__init__(self, 'Real-space maps', session)
        
        #############
        # Variables involved in handling live redrawing of maps in a box
        # centred on the cofr
        #############

        # Radius of the sphere in which the map will be displayed when
        # in live-scrolling mode
        self.display_radius = display_radius
        # Actual box dimensions in (u,v,w) grid coordinates
        self._box_dimensions = None
        # Centre of the box (used when tracking the centre of rotation)
        self._box_center = None
        # Last grid coordinate of the box centre. We only need to update
        # the map if the new centre maps to a different integer grid point
        self._last_box_centre_grid = None
        # Minimum corner of the box in (x,y,z) coordinates. This must
        # correspond to the grid coordinate in self._box_corner_grid
        self._box_corner_xyz = None
        # Minimum corner of the box in grid coordinates
        self._box_corner_grid = None
        # ChimeraX session.triggers handler for live box update
        self._box_update_handler = None
        # Is the box already initialised?
        self._box_initialized = False
        # Object storing the parameters required for masking (used after
        # adjusting contours)
        self._surface_zone = Surface_Zone(display_radius, None, None)
        
        
        if live_scrolling:
            # Get the initial box parameters based on cofr and radius
            v = self.session.view
            cofr = v.center_of_rotation
            self._box_dimensions = \
                2 * calculate_grid_padding(display_radius, self.grid, self.cell)
            self._box_corner_grid, self._box_corner_xyz = \
                _find_box_corner(cofr, self.cell, self.grid, display_radius)
            self._surface_zone.update(self, display_radius, coords = [cofr])
            
        else:
            # Get the initial box parameters based on atom_selection and padding
            self._box_corner_grid, self._box_corner_xyz, self._box_dimensions = \
                _get_bounding_box(atom_selection.coords, padding, self.grid, self.cell)
            self._surface_zone.update(self, padding, atoms = atom_selection)
        
        for dataset in datasets:
            self.add_map(dataset)
        
        # Apply the surface mask
        self._reapply_zone()

        if live_scrolling:
            self.start_live_scrolling()
        
    def add_map(self, dataset, is_difference_map = None, 
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
        new_xmap = clipper.Xmap(self.spacegroup, self.cell, self.grid, name = dataset.name, hkldata = data)
        if is_difference_map = None:
            is_difference_map = data.is_difference_map
        new_map.is_difference_map = is_difference_map
        if is_difference_map and color is not None and len(color) != 2:
            err_string = '''
            ERROR: For a difference map you need to define colours for 
            both positive and negative contours, as:
            [[r,g,b,a],[r,g,b,a]] in order [positive, negative].
            '''
            raise TypeError(err_string)
        new_handler = XmapHandler(self.session, dataset.name, new_xmap, 
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
        else:
            if not hasattr(contour, '__len__'):
                contour = [contour]
        new_handler.set_representation(style)
        new_handler.set_parameters(**{'cap_faces': False,
                                  'surface_levels': contour,
                                  'show_outline_box': False,
                                  'surface_colors': color,
                                  'square_mesh': True})
        
        self.add([new_handler])
        
        
    
    @property
    def hklinfo(self):
        return self.parent.hklinfo
        
    @property
    def spacegroup(self):
        return self.parent.spacegroup
    
    @property
    def cell(self):
        return self.parent.cell
    
    @property
    def res(self):
        return self.hklinfo.resolution
    
    @property
    def grid(self):
        return self.parent.grid
    
    @property
    def voxel_size(self):
        return self.cell.dim / self.grid.dim
    
    @property
    def voxel_size_frac(self):
        return 1/ self.grid.dim
    
    @property
    def unit_cell(self):
        return self.parent.unit_cell
    
    @property
    def display_radius(self):
        return self._display_radius
    
    @display_radius.setter
    def display_radius(self, radius):
        self._display_radius = radius
        self.stop_live_update()
        v = self.session.view
        cofr = v.center_of_rotation
        dim = self._box_dimensions = 
            2 * calculate_grid_padding(radius, self.grid, self.cell)
        box_corner_grid, box_corner_xyz = _find_box_corner(cofr, self.cell, self.grid, radius)
        triggers.activate_trigger('map box changed', (box_corner_xyz, box_corner_grid, dim))
        self.start_live_update()
    
    
    def update_box(self, *_, force_update = False):
        '''Update the map box to surround the current centre of rotation.'''
        v = self.session.view
        cofr = v.center_of_rotation
        self._box_center = cofr
        cofr_grid = clipper.Coord_orth(cofr).coord_frac(self.cell).coord_grid(self.grid)
        if not force_update:
            if cofr_grid == self._last_cofr_grid:
                return
        self._last_cofr_grid = cofr_grid      
        box_corner_grid, box_corner_xyz = _find_box_corner(cofr, self.cell, self.grid, self.display_radius)
        triggers.activate_trigger('map box moved', (box_corner_xyz, box_corner_grid, self._box_dimensions))
        self._surface_zone.update(self.display_radius, coordlist = numpy.array([cofr]))
        self._reapply_zone()
     
    def _reapply_zone(self):
        '''
        Reapply any surface zone applied to the volume after changing 
        position or contour level.
        '''
        coords = self._surface_zone.all_coords
        radius = self._surface_zone.distance
        if coords is not None:
            surface_zones([self], coords, radius)
        

    def start_live_scrolling(self):
        if self._box_handler is None:
            self._box_handler = self.session.triggers.add_handler('new frame', self.update_box)
  
    def stop_live_scrolling(self):
        if self._box_handler is not None:
            self.session.triggers.remove_handler(self._box_handler)
            self._box_handler = None

    def delete(self):
        self.stop_live_scrolling()
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


class XmapHandler(Volume):
    '''
    An XmapHandler is in effect a resizable window into a periodic 
    crystallographic map. The actual map data (a clipper Xmap object) is
    held within, and filled into the XmapWindow.data array as needed.
    Methods are included for both live updating (e.g. tracking and filling
    a box centred on the centre of rotation) and static display of a 
    given region.
    '''
    def __init__(self, session, name, xmap, origin, grid_origin, dim):
        '''
        Args:
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
        # Volume data is stored in zyx order, so we need to reverse the dimensions
        darray = self._generate_and_fill_data_array(origin, grid_origin, dim)
        Volume.__init__(self, darray, session)
        
        self.is_difference_map = xmap.is_difference_map
        self.name = name
        self.initialize_thresholds()
        self._box_shape_changed_cb_handler = triggers.add_handler(
            'map box changed', self._box_changed_cb)
        self._box_moved_cb_handler = triggers.add_handler(
            'map box moved', self._box_moved_cb)
        
        
        # If the box shape changes while the volume is hidden, the change
        # will not be applied until it's shown again.
        self._needs_update = True
        self.show()
        
    
    def show(self):
        if self._needs_update:
            self._swap_volume_data(self.box_params, force_update = True)
            self._needs_update = False
        else:
            # Just set the origin and fill the box with the data for 
            # the current location
            origin, grid_origin, ignore = self.box_params
            self._fill_volume_data(self.data.array, origin, grid_origin)
        super(XmapHandler, self).show()

    @property
    def hklinfo(self):
        return self.parent.hklinfo
        
    @property
    def spacegroup(self):
        return self.parent.spacegroup
    
    @property
    def cell(self):
        return self.parent.cell
    
    @property
    def res(self):
        return self.hklinfo.resolution
    
    @property
    def grid(self):
        return self.parent.grid
    
    @property
    def voxel_size(self):
        return self.cell.dim / self.grid.dim
    
    @property
    def voxel_size_frac(self):
        return 1/ self.grid.dim
    
    @property
    def unit_cell(self):
        return self.parent.unit_cell


    def _box_changed_cb(self, params):
        self.box_params = params
        if not self.display:
            self._needs_update = True
            # No sense in wasting cycles on this if the volume is hidden.
            # We'll just store the params and apply them when we show the
            # volume.
            # NOTE: this means we need to over-ride show() to ensure 
            # it's updated before re-displaying.
            return
        self._swap_volume_data(params)
        self.data.values_changed()
    
    def _box_moved_cb(self, params):
        if not self.display:
            self.box_params = params
            return
        self._fill_volume_data(self.data.array, params[0], params[1])
        self.data.values_changed()
    
    def delete(self):
        if self._box_shape_changed_cb_handler is not None:
            triggers.remove_handler(self._box_shape_changed_cb_handler)
            self._box_shape_changed_cb_handler = None
        if self._box_moved_cb_handler is not None:
            triggers.remove_handler(self._box_moved_cb_handler)
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
        darray, dim = self._generate_and_fill_data_array(new_origin, new_grid_origin, new_dim)
        self._box_dimensions = dim
        self.replace_data(darray)
        self.new_region((0,0,0), darray.size)
    
    def _generate_and_fill_data_array(self, origin, grid_origin, dim):
        dim = dim[::-1]
        data = numpy.empty(dim, numpy.double)
        self._fill_volume_dta(data, grid_origin)
        darray = Array_Grid_Data(data, origin = origin,
            step = self.voxel_size, cell_angles = self.cell.angles_deg)
        return darray
    
        
    def _fill_volume_data(self, target, origin_xyz, start_grid_coor):
        #shape = (numpy.array(target.shape)[::-1] - 1)
        #end_grid_coor = start_grid_coor + clipper.Coord_grid(shape)
        self.data.set_origin(origin_xyz)
        xmap = self.xmap
        xmap.export_section_numpy(start_grid_coor, target = target,  order = 'C', rot = 'zyx')

