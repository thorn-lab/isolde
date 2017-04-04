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
    CRYST1 card
    '''
    if 'CRYST1' in model.metadata.keys():
        cryst1 = model.metadata['CRYST1'][0].split()
        abc = cryst1[1:4]
        angles = cryst1[4:7]
        
        # Safest to infer the spacegroup from the list of symmetry 
        # operators at REMARK 290
        
        remarks = model.metadata['REMARK']
        i = 0
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
        return abc, angles, symstr
            
        
    
        
    # TODO: add equivalent lookup for mmCIF metadata once available
    
    cell_descr = clipper.Cell_descr(*abc, *angles)
    cell = clipper.Cell(cell_descr)
    
        



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
    -- reciprocal space data (MTZData)
    |    |
    |    -- clippper.HKL_info
    |    |
    |    -- clipper.HKL_data_Flag
    |    |
    |    -- clipper.HKL_data_F_Phi
    |    |
    |    -- ...
    |
    -- real-space maps (XMapSet)
         |
         -- 2mFo-Fc (Volume)
         |
         -- ...
  '''
  
  def __init__(self, session, model, mtzdata = None, show_nonpolar_H = False):
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
    name = 'Crystal(' + model.name +')'
    Model.__init__(self, name, session)
    self.session.models.add([self])
    move_model(self.session, model, self)
    self.master_model = model
    if mtzdata is not None:
        self.cell = mtzdata.cell
        self.sg = mtzdata.spacegroup
        self.grid = mtzdata.grid_sampling
        self._voxel_size = cell.dim / grid_sampling.dim
    else:
        # Need to generate the above from the PDB header
        pass
    
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
    #i1, i2 = find_close_points(this_model.atoms.coords, [cofr], self.sym_box_radius)
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
