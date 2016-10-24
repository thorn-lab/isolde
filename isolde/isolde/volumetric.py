# Generic class to hold the details of maps to be used in the simulation
class IsoldeMap(object):
    
    def __init__(self, session, name, source_map, cutoff, coupling_constant):
        self.session = session # Handle for current ChimeraX session
        self._name = name     # User-specified name (e.g. '2mFo-DFc')
        self._source_map = source_map # A model currently loaded into ChimeraX
        self._mask_cutoff = cutoff # in Angstroms 
        self._coupling_constant = coupling_constant # How hard map pulls on atoms
        # TODO: Add the ability to define specific sub-selections of atoms
        # to be associated with a particular map (e.g. anomalous scatterers with
        # an anomalous difference map; omitted fragments with the mFo-DFc density
        # in an omit map, etc.)
        self._source_map_res = source_map.region_origin_and_step(source_map.region)[1]
        # TODO: This currently ignores the skewness of the map (in most cases
        # probably not a huge deal). Still, it should be re-calculated to give
        # the effective resolution along the model (x,y,z) axes
    # Masks a given volumetric map to within the given cutoff (in 
    # Angstroms) of a selection. Optionally inverts the density values 
    # (useful for MD where high density becomes low potential), 
    # and/or normalises such that standard deviation = 1.
    # Returns the newly-created volume and its minimum/maximum coordinates
    
    def change_map_parameters(self, source_map, cutoff, coupling_constant):
        self._source_map = source_map
        self._mask_cutoff = cutoff
        self._coupling_constant = coupling_constant
    
    def set_source_map(self, source_map):
        self._source_map = source_map
    
    def set_mask_cutoff(self, cutoff):
        self._mask_cutoff = cutoff
    
    def set_coupling_constant(self, coupling_constant):
        self._coupling_constant = coupling_constant
    
    def get_map_parameters(self):
        return self._name, self._source_map, self._mask_cutoff, self._coupling_constant
                
    def get_name(self):
        return self._name
    
    def get_source_map(self):
        return self._source_map
    
    def get_mask_cutoff(self):
        return self._mask_cutoff
    
    def get_coupling_constant(self):
        return self._coupling_constant
    
    # Mask a given map down to a selection and interpolate it onto an orthogonal
    # grid of the specified resolution. Resolution must be either a single
    # number or an (x,y,z) numpy array. If resolution is not specified, 
    # the resolution of the source map will be used. Optionally, the map 
    # may also be inverted or normalised such that its standard deviation = 1.
    def mask_volume_to_selection(self, selection, resolution = None, invert = False, normalize = False):
        big_map = self._source_map
        cutoff = self._mask_cutoff
        sel = selection
        import numpy as np
        # Get minimum and maximum coordinates of selected atoms, and pad
        maxcoor = (sel.coords.max(0)  + cutoff)
        mincoor = (sel.coords.min(0)  - cutoff)
        # ChimeraX wants the volume array to be in zyx order, so we need to reverse
        vol_size = maxcoor[::-1] - mincoor[::-1]
        # Round to an integral number of steps at the desired resolution
        res = resolution
        sizek, sizej, sizei = np.ceil(vol_size/res).astype(int)
        vol_array = np.zeros([sizek, sizej, sizei])
        
        from chimerax.core.map.data import Array_Grid_Data
        from chimerax.core.map import Volume
        
        mask_array = Array_Grid_Data(vol_array, origin = mincoor, step = res*np.ones(3))
        vol = Volume(mask_array, self.session)
        vol_coords = vol.grid_points(vol.model_transform())
        
        from chimerax.core.geometry import find_close_points
        map_points, ignore = find_close_points(vol_coords, sel.coords, cutoff)
        mask_1d = np.zeros(len(vol_coords))
        mask_1d[map_points] = 1
        vol_array = np.reshape(mask_1d, (sizek, sizej, sizei))
        if normalize:
            std = big_map.data.full_matrix().std()
            cropped_map = big_map.interpolate_on_grid(vol) / std
        else:
            cropped_map = big_map.interpolate_on_grid(vol)
        if invert:
            masked_map = -cropped_map[0] * vol_array
        else:
            masked_map = cropped_map[0] * vol_array
        masked_array = Array_Grid_Data(masked_map, origin = mincoor, step = res*np.ones(3))
        vol = Volume(masked_array, self.session)
        return vol, mincoor, maxcoor

