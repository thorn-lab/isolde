import numpy
from .main import atom_list_from_sel
from . import clipper
from .lib import clipper_python_core as clipper_core
from .clipper_mtz import Clipper_MTZ
from .data_tree import db_levels, DataTree
from collections import defaultdict
from chimerax.core.atomic import AtomicStructure
from chimerax.core.geometry import Place, Places
from chimerax.core.geometry import find_close_points, find_close_points_sets
from chimerax.core.surface import zone
from chimerax.core.models import Model, Drawing
from chimerax.core.commands import camera, cofr
from chimerax.core.map.data import Array_Grid_Data
from chimerax.core.map import Volume, volumecommand    

class Xtal_Project:
  '''
  The master object for handling a crystallographic data set within
  ChimeraX. Contains a Clipper_MTZ object holding all reciprocal-space
  data for one or more crystals, any maps generated for each crystal,
  and all ChimeraX-specific functions for working with them.
  '''
  def __init__(self, session, name):
    self.session = session
    if not hasattr(session, 'Clipper_DB') or session.Clipper_DB is None:
      session.Clipper_DB = DataTree()
    #if not hasattr(session.Clipper_DB, 'experiments'):
    #  from types import SimpleNamespace
    #  session.Clipper_DB.experiments = SimpleNamespace()
    #if hasattr(session.Clipper_DB.experiments, name):
    #  raise TypeError('The Clipper database already has a project of that name!')
    db = self.master_db = session.Clipper_DB
    # Store all the data safely in the database
    self.data = db['Experiment'][name] = Clipper_MTZ(parent=db['Experiment'])
    # Add a more user-friendly handle to retrieve this project from the db
    #setattr(session.Clipper_DB.experiments, name, self)
    
  def load_data(self, filename):
    return self.data.load_hkl_data(filename)
  
  def add_maps(self, crystal_name):
    maps = self.data[crystal_name]['maps'] = \
          Map_set(self.session, self.data[crystal_name]['dataset'])
    for key in self.data[crystal_name]['dataset']['F_Phi'].keys():
      maps.generate_map_from_f_phi(key)
    return maps
    
  

DEFAULT_SOLID_MAP_COLOR = [0,1.0,1.0,0.6] # Transparent cyan
DEFAULT_MESH_MAP_COLOR = [0,1.0,1.0,1.0] # Solid cyan
DEFAULT_DIFF_MAP_COLORS = [[1.0,0,0,1.0],[0,1.0,0,1.0]] #Solid red and yellow


class Map_set:
  '''
  Each crystal dataset will usually have multiple maps associated with it.
  We need an object to organise these, to control their display, and to
  re-calculate them as necessary.  
  '''
  
  def __init__(self, session, dataset):
    '''
    Parameters:
      session: the current ChimeraX session
      dataset: a node from the Clipper_MTZ tree corresponding to one
               crystallographic dataset
    '''
    self.session = session
    if not isinstance(dataset, DataTree) or dataset.level != db_levels.DATASET:
      raise TypeError('dataset should be the fourth level of a Clipper_MTZ tree!')
    self._data = dataset
    # The Clipper HKL_info object holding the (h,k,l) arrays and cell/symmetry information
    hkl = self.hklinfo = dataset.find_ancestor(db_levels.CRYSTAL_SET)['hkl']
    sg = self.spacegroup = hkl.spacegroup
    cell = self.cell = hkl.cell
    res = self.resolution = hkl.resolution
    grid = self.grid = clipper.Grid_sampling(sg, cell, res)
    
    self.voxel_size = cell.dim / grid.dim
    self._voxel_size_frac = 1 / grid.dim
    
    
    # List of Xmap objects generated and handled by this object
    self.maps = []
    
    # Atomic model associated with this object
    self._atomic_model = None
    # Unit cell definition for fast symmetry operations
    self._unit_cell = None
    # Object wrapping the atomic model with functions to handle periodicity
    self._periodic_model = None
    
    #############
    # Variables involved in handling live redrawing of maps in a box
    # centred on the cofr
    #############
    
    # FIXME: The model box and its parameters should really be handled
    # at a higher level - we really just want one box per session, into
    # which we can pour multiple maps from different crystals as necessary
    
    self._master_box_model = Model('Xmap display', self.session)
    
    self._standard_contour = numpy.array([1.5])
    self._standard_difference_map_contours = numpy.array([-3.0, 3.0])
    # Default "radius" (actually half-width of the rhombohedron) of
    # the box in which the maps will be drawn.
    self._box_radius = None
    # Box dimensions in grid points (depends on resolution)
    self._box_dimensions = None
    # Centre point of the box (will typically be set to the centre of
    # rotation).
    self._box_center = None
    # Last grid coordinate of the box centre. We only need to update the
    # map if the new centre changes
    self._last_cofr_grid = None
    # ChimeraX Volume objects to draw the map into
    self._volumes = []
    # Array_Grid_Data objects held by the Volume objects
    self._array_grid_data = []
    # The actual numpy arrays to send the map data to
    self._volume_data = []
    # session.triggers handler for live box update
    self._box_handler = None
    # Is the box already initialised?
    self._box_initialized = False    
    
    ################
    # Variables involved in handling other useful annotations
    ################
    
    # Model object to hold Drawings defining the special positions
    self._special_positions_model = None
    
    self._crosshairs = None
    
    self._show_crosshairs = True

  @property
  def periodic_model(self):
    if self.atomic_model is None:
      raise RuntimeError('You must assign an atomic model first!')
    if self._periodic_model is None:
      self.periodic_model = self.atomic_model
    return self._periodic_model
    
  @periodic_model.setter
  def periodic_model(self, model):
    if isinstance(model, AtomicStructure):
      self._periodic_model = AtomicCrystalStructure(self.session, model, self.cell, self.spacegroup, self.grid)
      self.atomic_model = model
    elif isinstance(model, AtomicCrystalStructure):
      self._periodic_model = model
    
    
  @property
  def atomic_model(self):
    '''
    The atomic model representing one asymmetric unit of the crystal
    structure.
    '''
    return self._atomic_model
  
  @atomic_model.setter
  def atomic_model(self, model):
    if isinstance(model, AtomicStructure):
      self._atomic_model = model
    else:
      raise TypeError('Model must be an atomic structure!')
  
  @property
  def clipper_atoms(self):
    '''
    Clipper Atom_list object describing the atomic model
    '''
    return self.periodic_model._clipper_atoms
  
  
  @property
  def unit_cell(self):
    if self._unit_cell is None:
      ref = self._atomic_model.bounds().center()
      self._unit_cell = clipper.Unit_Cell(ref, self.clipper_atoms, 
                                self.cell, self.spacegroup, self.grid)
    return self._unit_cell
  
  @property
  def show_symmetry(self):
    return self._show_symmetry
  
  @show_symmetry.setter
  def show_symmetry(self, flag):
    if flag:
      if not all([self.cell, self.spacegroup, self.grid]):
        raise RuntimeError('You need to define symmetry information first!')
    self._show_symmetry = flag
  
  
  @property
  def show_crosshairs(self):
    return self._show_crosshairs
  
  @show_crosshairs.setter
  def show_crosshairs(self, state):
    if state:
      if self._crosshairs is None or self._crosshairs.deleted:
        if self._box_handler:
          self._crosshairs = draw_crosshairs()
          self._master_box_model.add([self._crosshairs])
        else:
          print('Please initialise map drawing first!')
          return
    self._show_crosshairs = state
    self._crosshairs.visible = state
  
  def generate_map_from_f_phi(self, data_key):
    name = data_key
    data = self._data['F_Phi'][data_key]
    xmap = clipper.Xmap(self.spacegroup, self.cell, self.grid, name = data_key, hkldata = data)
    #xmap.fft_from(data)
    # FIXME: Ugly fudge for now to find difference maps
    if '2' not in data_key:
      xmap.is_difference_map = True
    self.maps.append(xmap)
  

  ################
  # Live-updating map box
  ################
  
  def initialize_box_display(self, radius = 15, pad = 2):
    '''
    Generate a Volume big enough to hold a sphere of the given radius,
    plus an optional padding of pad voxels on each side. The session
    view will be changed to use an orthographic camera, with the centre
    of rotation updating to always remain at the centre of the screen.
    The volume will automatically track the centre of rotation and 
    update its position and contents to reflect the local density.
    '''
    if self.maps is None or not len(self.maps):
      raise RuntimeError('You must generate at least one map first!')
    if self._box_initialized:
      raise RuntimeError(''' 
          The live map box is already initialised for this crystal.
          If you want to reset it, run box_reset().
          ''')
    camera.camera(self.session, 'ortho')
    cofr.cofr(self.session, 'centerOfView')
    self._box_pad = pad
    self._box_radius = radius
    v = self.session.view
    c = self.cell
    g = self.grid
    self._box_center = v.center_of_rotation
    self._last_cofr_grid = clipper.Coord_orth(self._box_center).coord_frac(c).coord_grid(g)
    if self.show_crosshairs:
      self._crosshairs = draw_crosshairs(self._box_center)
      self._master_box_model.add([self._crosshairs])

    box_corner_grid, box_corner_xyz = _find_box_corner(self._box_center, c, g, radius, pad)
    self._box_dimensions = (numpy.ceil(radius / self.voxel_size * 2)+pad*2).astype(int)[::-1]
    for m in self.maps:
      data = numpy.empty(self._box_dimensions, numpy.double)
      self._volume_data.append(data)
      grid_data = Array_Grid_Data(data, origin = box_corner_xyz,
          step = self.voxel_size, cell_angles = c.angles_deg)
      self._array_grid_data.append(grid_data)
      volume = Volume(grid_data, self.session)
      volume.name = m.name
      self._volumes.append(volume)
      self._fill_volume_data(m, data, box_corner_grid)
      volume.initialize_thresholds()
      self._master_box_model.add([volume])
      if not m.is_difference_map:
        contour_val = [self._standard_contour * m.sigma]
        colorset = [DEFAULT_SOLID_MAP_COLOR]
      else:
        contour_val = self._standard_difference_map_contours * m.sigma
        colorset = DEFAULT_DIFF_MAP_COLORS
        volume.set_representation('mesh')
      volume.set_parameters(**{'cap_faces': False,
                               'surface_levels': contour_val,
                               'show_outline_box': False,
                               'surface_colors': colorset})
      volume.update_surface()
      volume.show()
    self.session.models.add([self._master_box_model])
    self.update_box(force_update = True)
    self._box_go_live()
    self._box_initialized = True

  def change_box_radius(self, radius, pad=1):
    self._box_go_static()
    v = self.session.view
    cofr = v.center_of_rotation
    self._box_radius = radius
    dim = (numpy.ceil(radius / self.voxel_size * 2)+pad*2).astype(int)[::-1]
    box_corner_grid, box_corner_xyz = _find_box_corner(cofr, self.cell, self.grid, radius, pad)
    for i, volume in enumerate(self._volumes):
      data = numpy.empty(dim, numpy.double)
      self._volume_data[i] = data    
      darray = Array_Grid_Data(data, origin = box_corner_xyz,
        step = self.voxel_size, cell_angles = self.cell.angles_deg)
      self._array_grid_data[i] = darray
      volume.replace_data(darray)
      volume.new_region((0,0,0), darray.size)
    self._box_pad = pad
    self._box_dimensions = dim
    self.update_box(force_update=True)
    self._box_go_live()
    
    
    
  def update_box(self, *_, force_update = False):
    v = self.session.view
    cofr = v.center_of_rotation
    cofr_eps = self.session.main_view.pixel_size(cofr)
    # We need to redraw the crosshairs if the cofr moves by a pixel...
    if not force_update:
      if numpy.all(abs(self._box_center - cofr) < cofr_eps):
        return
    if self.show_crosshairs:
      self._crosshairs.position = Place(origin=cofr)
    # ... and redraw the box if it moves by a grid point
    self._box_center = cofr
    cofr_grid = clipper.Coord_orth(cofr).coord_frac(self.cell).coord_grid(self.grid)
    if not force_update:
      if cofr_grid == self._last_cofr_grid:
        return
    self._last_cofr_grid = cofr_grid      
    box_corner_grid, box_corner_xyz = _find_box_corner(cofr, self.cell, self.grid, self._box_radius, self._box_pad)
    for i, volume in enumerate(self._volumes):
      # If the user has closed this map, pop it from our list.
      #if volume not in self._master_box_model.all_models():
        #self._volumes[i] = None
        #self._array_grid_data[i] = None
        #self._volume_data[i] = None
        #continue
      if volume is None or not volume.display:
        continue
      self._array_grid_data[i].set_origin( box_corner_xyz )#box_corner_xyz)
      self._fill_volume_data(self.maps[i], self._volume_data[i], box_corner_grid)

      volume.update_surface()
    surface_zones(self._volumes, [cofr], self._box_radius)
    
  def change_contour(self, volume, contour_vals):
    volume.set_parameters(**{'surface_levels': contour_vals})
    self.update_box(force_update = True)
    

  def _fill_volume_data(self, xmap, target, start_grid_coor):
    #shape = (numpy.array(target.shape)[::-1] - 1)
    #end_grid_coor = start_grid_coor + clipper.Coord_grid(shape)
    xmap.export_section_numpy(target, start_grid_coor, 'C', 'zyx')

        
  def _box_go_live(self):
    if self._box_handler is None:
      self._box_handler = self.session.triggers.add_handler('new frame', self.update_box)
  
  def _box_go_static(self):
    if self._box_handler is not None:
      self.session.triggers.remove_handler(self._box_handler)
      self._box_handler = None

  ########
  # Other utility functions
  ########
    
  def draw_unit_cell_maps(self, nu = 1, nv = 1, nw = 1):
    '''
    Create a Volume covering the whole unit cell for each currently loaded
    map, and optionally tile it by a number of unit cells in each direction
    '''
    if self.maps is None or not len(self.maps):
      raise RuntimeError('You must generate at least one map first!')
    uc = self.unit_cell    
    c = self.cell
    g = self.grid
    asu_model = Model('Unit Cell Maps', self.session)
    
    box_min_grid = self.unit_cell.min()
    box_min_xyz = box_min_grid.coord_frac(g).coord_orth(c).xyz
    box_max_grid = self.unit_cell.max()+clipper.Coord_grid([2,2,2])
    box_dim = (box_max_grid-box_min_grid).uvw[::-1]
    for m in self.maps:
      data = numpy.empty(box_dim, numpy.double)
      self._fill_volume_data(m, data, box_min_grid)
      grid_data = Array_Grid_Data(data, origin=box_min_xyz, step = self.voxel_size, cell_angles = c.angles_deg)
      volume = Volume(grid_data, self.session)
      volume.name = m.name
      asu_model.add([volume])
      volume.initialize_thresholds()
      if not m.is_difference_map:
        contour_val = [self._standard_contour * m.sigma]
        colorset = {'surface_colors': [DEFAULT_SOLID_MAP_COLOR]}
      else:
        contour_val = self._standard_difference_map_contours * m.sigma
        colorset = {'surface_colors': DEFAULT_DIFF_MAP_COLORS}
        volume.set_representation('mesh')
      volume.set_parameters(**{'cap_faces': False, 
                               'show_outline_box': False,
                               'surface_levels': contour_val,
                               **colorset})
      #volume.set_parameters(**{'surface_levels': contour_val})
      #volume.set_parameters(**colorset)
      volume.update_surface()
      volume.show()
    places = []
    grid_dim = g.dim
    for i in range(nu):
      for j in range(nv):
        for k in range(nw):
          thisgrid = clipper.Coord_grid(numpy.array([i, j, k])*grid_dim)
          thisorigin = thisgrid.coord_frac(g).coord_orth(c).xyz
          places.append(Place(origin = thisorigin))
    asu_model.positions = Places(places)
    self.session.models.add([asu_model])

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
  


def _find_box_corner(center, cell, grid, radius = 20, pad = 1):
  '''
  Find the bottom corner (i.e. the origin) of a rhombohedral box
  big enough to hold a sphere of the desired radius, and padded by
  pad voxels in each dimension.
  '''
  radii_frac = clipper.Coord_frac(radius/cell.dim)
  center_frac = clipper.Coord_orth(center).coord_frac(cell)
  bottom_corner_grid = (center_frac - radii_frac).coord_grid(grid) -\
            clipper.Coord_grid([pad,pad,pad])
  bottom_corner_orth = bottom_corner_grid.coord_frac(grid).coord_orth(cell)
  return bottom_corner_grid, bottom_corner_orth.xyz

class AtomicCrystalStructure:
  '''
  Extends an AtomicStructure with methods for finding and drawing symmetry
  equivalents in a crystallographic context.
  '''
  def __init__(self, session, model, cell, spacegroup, grid_sampling):
    '''
    Args:
      session:
        The ChimeraX session
      model:
        An AtomicStructure instance
      cell:
        A clipper.Cell() object
      spacegroup:
        A clipper.Spacegroup() object
      grid_sampling:
        A clipper.Grid_Sampling() object
    '''
    self.session = session
    self.master_model = model
    self.cell = cell
    self.sg = spacegroup
    self.grid = grid_sampling
    
    self._voxel_size = cell.dim / grid_sampling.dim
    
    ref = model.bounds().center()
    
    # Convert the atoms to a format recognised by Clipper
    self._clipper_atoms = atom_list_from_sel(model.atoms)
    # A C++ object holding the symmetry operations required to pack one
    # unit cell relative to the current atomic model, along with fast
    # functions returning the symops necessary to pack a given box in
    # xyz space.
    self.unit_cell = clipper.Unit_Cell(ref, self._clipper_atoms, cell, spacegroup, grid_sampling)
    

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
    box_corner_grid, box_corner_xyz = _find_box_corner(self._sym_box_center, c, g, radius, 0)
    self._sym_box_dimensions = (numpy.ceil(radius / self._voxel_size * 2)).astype(int)
    self._update_sym_box(force_update = True)
    self._sym_box_go_live()
    self._sym_box_initialized = True
  
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
              self.grid, self._sym_box_radius, 0)
    symops = uc.all_symops_in_box(box_corner_xyz, 
              self._sym_box_dimensions, self.sym_always_shows_reference_model, 
              sample_frequency = self._sym_search_frequency)
    l1 = []
    search_entry = [(numpy.array([cofr], numpy.float32), Place().matrix.astype(numpy.float32))]
    coords = self.master_model.atoms.coords.astype(numpy.float32)
    display_mask = numpy.array([False]*len(coords))
    for s in symops:
      this_model = self.sym_model_container[s]
      this_set = (coords, this_model.position.matrix.astype(numpy.float32))
      l1.append(this_set)
    i1, i2 = find_close_points_sets(l1, search_entry, self.sym_box_radius)
    #i1, i2 = find_close_points(this_model.atoms.coords, [cofr], self.sym_box_radius)
    for i, indices in enumerate(i1):
      this_model = self.sym_model_container[symops[i]]
      if len(indices):
        display_mask[:] = False
        a = this_model.atoms
        display_mask[a.indices(a[indices].residues.atoms)] = True
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
              self.grid, box_width/2, 0)
    symops = uc.all_symops_in_box(box_corner_xyz, dim, True)
    num_symops = len(symops)
    sym_matrices = symops.all_matrices34_orth(self.cell)
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
    self._sym_container = Model('symmetry equivalents', self.session)
    self.master.add([self._sym_container])

  def __missing__(self, key):
    if type(key) is not clipper.RTop_frac:
      raise TypeError('Key must be a clipper.RTop_frac!')
    thisplace = Place(matrix=key.rtop_orth(self.parent.cell).mat34)
    if not thisplace.is_identity():
      thismodel = self.master.copy(name=key.format)
      atoms = thismodel.atoms
      thismodel.position = thisplace
      #coords = atoms.coords
      #thisplace.move(coords)
      #atoms.coords = coords
      atom_colors = atoms.colors
      atom_colors[:,0:3] = (self.master.atoms.colors[:,0:3].astype(float)*0.6).astype(numpy.uint8)
      atoms.colors = atom_colors
      ribbon_colors = thismodel.residues.ribbon_colors
      ribbon_colors[:,0:3] = (self.master.residues.ribbon_colors[:,0:3].astype(float)*0.6).astype(numpy.uint8)
      thismodel.residues.ribbon_colors = ribbon_colors
      self._sym_container.add([thismodel])
      self[key] = thismodel
      return thismodel
    return self.master
      



  
def draw_crosshairs(origin):
  from chimerax.core.surface.shapes import cylinder_geometry
  d = Drawing('axis')
  axes = Drawing('axes')
  d.vertices, d.normals, d.triangles = cylinder_geometry(radius = 0.05, height = 0.5)
  p = []
  p.append(Place(axes = [[0,0,1],[0,1,0],[-1,0,0]]))
  p.append(Place(axes = [[1,0,0],[0,0,-1],[0,1,0]]))
  p.append(Place())
  c = [[255,0,0,255],[0,255,0,255],[0,0,255,255]] # red = x, green = y, blue = z
  d.positions = Places(p)
  d.colors = c
  axes.add_drawing(d)
  axes.position = Place(origin=origin)
  return axes

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
  if not hasattr(session, 'Clipper_DB') or not hasattr(session.Clipper_DB.Experiment, experiment_name):
    project = Xtal_Project(session, experiment_name)
    xmapset = None
  else:
    project = getattr(session.Clipper_DB.experiments, experiment_name)
  # Bring in all the data from the MTZ file and add the corresponding
  # Clipper objects to the database
  crystal_name = project.load_data(filename)
  if auto_generate_maps:
    if project.data.has_map_data(crystal_name):
      xmapset = project.add_maps(crystal_name)
      if atomic_model is not None:
        xmapset.atomic_model = atomic_model
      if live_map_display:
        xmapset.initialize_box_display()
        if atomic_model:
          xmapset.periodic_model.initialize_symmetry_display()
  return project, xmapset
  
  
  






  
'''

                  
  def draw_unit_cell_and_special_positions(self, model, offset = None):
    from chimerax.core.models import Model, Drawing
    from chimerax.core.geometry import Place, Places
    from chimerax.core.surface.shapes import sphere_geometry
    import copy
    
    ref = model.bounds().center().astype(float)
    frac_coords = Coord_orth(ref).coord_frac(self.cell()).uvw
    if offset is None:
      offset = numpy.array([0,0,0],int)
    corners_frac = numpy.array([[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1]],numpy.double) + offset
    corners = []
    for c in corners_frac:
      cf = Coord_frac(c).coord_orth(self.cell())
      corners.append(cf.xyz)
    m = self.special_positions_model
    
    if m is None or m.deleted:
      m = self.special_positions_model = Model('Special Positions',self.session)
      spc = numpy.array(self.special_positions_unit_cell_xyz(offset))
      coords = spc[:,0:3]
      multiplicity = spc[:,3].astype(int)
      sphere = numpy.array(sphere_geometry(80))
      sphere[0]*=0.5
      scale_2fold = numpy.identity(3)
      scale_3fold = numpy.identity(3)* 1.5
      scale_4fold = numpy.identity(3)* 2
      scale_6fold = numpy.identity(3)* 3
      rgba_2fold = numpy.array([255,255,255,255],numpy.int32)
      rgba_3fold = numpy.array([0,255,255,255],numpy.int32)
      rgba_4fold = numpy.array([255,255,0,255],numpy.int32)
      rgba_6fold = numpy.array([255,0,0,255],numpy.int32)
      rgba_corner = numpy.array([255,0,255,255],numpy.int32)
      positions = []
      colors = []
      d = Drawing('points')
      d.vertices, d.normals, d.triangles = sphere
      
      for coord, mult in zip(coords, multiplicity):
        if mult == 2:
          positions.append(Place(axes=scale_2fold, origin=coord))
          colors.append(rgba_2fold)
        elif mult == 3:
          positions.append(Place(axes=scale_3fold, origin=coord))
          colors.append(rgba_3fold)
        elif mult == 4:
          positions.append(Place(axes=scale_4fold, origin=coord))
          colors.append(rgba_4fold)
        elif mult == 6:
          positions.append(Place(axes=scale_6fold, origin=coord))
          colors.append(rgba_6fold)
      for c in corners:
        positions.append(Place(axes=scale_6fold, origin=c))
        colors.append(rgba_corner)
        
      d.positions = Places(positions)
      d.colors = numpy.array(colors)
      m.add_drawing(d)
      self.session.models.add([m])
  
'''    
