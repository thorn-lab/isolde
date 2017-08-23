import numpy
import simtk
import os

from simtk import unit, openmm
from simtk.openmm import app
from simtk.openmm.openmm import CustomBondForce, CustomExternalForce, \
                                CustomCompoundBondForce, CustomTorsionForce, \
                                NonbondedForce
from simtk.openmm.openmm import Continuous1DFunction, Continuous3DFunction 
from simtk.openmm.app.internal import customgbforces   
from chimerax.core.atomic import concatenate
from .custom_forces import LinearInterpMapForce, TopOutBondForce, \
                           TopOutRestraintForce, FlatBottomTorsionRestraintForce, \
                           GBSAForce, AmberCMAPForce

from ..threading.shared_array import TypedMPArray, SharedNumpyArray

from ..constants import defaults
OPENMM_LENGTH_UNIT = defaults.OPENMM_LENGTH_UNIT
OPENMM_FORCE_UNIT = defaults.OPENMM_FORCE_UNIT
OPENMM_SPRING_UNIT = defaults.OPENMM_SPRING_UNIT
OPENMM_RADIAL_SPRING_UNIT = defaults.OPENMM_RADIAL_SPRING_UNIT
OPENMM_ENERGY_UNIT = defaults.OPENMM_ENERGY_UNIT
OPENMM_ANGLE_UNIT = defaults.OPENMM_ANGLE_UNIT


amber14 = ['amberff14SB.xml','tip3p_standard.xml',
            'tip3p_HFE_multivalent.xml', 'tip3p_IOD_multivalent.xml']

cwd = os.path.dirname(os.path.abspath(__file__))
class available_forcefields():
    '''Main force field files'''
    main_files = (
        [os.path.join(cwd,'amberff',f) for f in amber14],
        ['amber99sbildn.xml',],
        ['amber99sbnmr.xml',],
        ['amber10.xml',],
        ['charmm36.xml',],
        )
    
    main_file_descriptions = (
        'AMBER14 withi improved backbone & sidechain torsions',
        'AMBER99 with improved backbone & sidechain torsions',
        'AMBER99 with modifications to fit NMR data',
        'AMBER10',
        'CHARMM36',
        )
    
    # Implicit solvent force field files. The main file and the implicit
    # solvent file must match.
    implicit_solvent_files = [
        None,
        'amber99_obc.xml',
        'amber99_obc.xml',
        'amber10_obc.xml',
        None
        ]
    
    # Explicit water models
    explicit_water_files = [
        None,
        'tip3pfb.xml',
        'tip4pfb.xml',
        'tip3p.xml',
        ]
    
    explicit_water_descriptions = [
        None,
        'TIP3P-FB (DOI: 10.1021/jz500737m)',
        'TIP4P-FB (DOI: 10.1021/jz500737m)',
        'Original TIP3P water (not recommended)',
        ]

def get_available_platforms():
        from simtk.openmm import Platform
        platform_names = []
        for i in range(Platform.getNumPlatforms()):
            p = Platform.getPlatform(i)
            name = p.getName()
            platform_names.append(name)
        return platform_names


        
class GenericMapObject:
    def __init__(self, c3dfunc, per_atom_coupling, coupling_k):
        '''
        A minimal class to hold a Continuous3DFunction and its parameters.
        '''
        self._potential_function = c3dfunc
        self._per_atom_coupling = per_atom_coupling
        self._k = coupling_k
        
    def get_potential_function(self):
        return self._potential_function
    
    def get_per_atom_coupling_params(self):
        return self._k
    
    def per_atom_coupling(self):
        return hasattr(self._k, '__len__') or hasattr(self._k, '__iter__')





class SimHandler():
    
    def __init__(self):
        # Forcefield used in this simulation
        self._forcefield = None
        # Overall simulation topology
        self._topology = None
        # Atoms in simulation topology
        self._atoms = None
        
        self.all_forces = []
        
        # Dict holding each custom external force object, its global and its
        # per-particle parameters. Format:
        # {'name': [object, 
        #           {'global_name': value}, 
        #           [per_particle_names],
        #           [per_particle_default_values],
        #           {index_in_topology: index_in_force}
        # } 
        self._custom_external_forces = {}
        
        # List of IsoldeMap objects registered with this simulation
        self._maps = []
        # CustomExternalForce handling haptic interactions
        self._tugging_force = None
        # Dict for mapping atom indices in the topology to indices in the tugging force
        self._tug_force_lookup = {}
        
    
    def update_restraints_in_context(self, context):
        self.update_distance_restraints_in_context(context)
        self.update_position_restraints_in_context(context)
        self.update_dihedral_restraints_in_context(context)
        for m in self._maps:
            pf = m.get_potential_function()
            pf.update_context_if_needed(context)
            
    
    ####
    # Positional Restraints
    ####
    
        ##
        # Before simulation starts
        ##
    
    def initialize_position_restraints_force(self, max_force):
        '''Just create the force object.'''
        rf = self._position_restraints_force = TopOutRestraintForce(max_force)
        self.all_forces.append(rf)
        return rf
    
    
    def add_position_restraints(self, force_index_map, atom_indices, ks, targets):
        rf = self._position_restraints_force
        for i, (index, k, target) in enumerate(zip(atom_indices, ks, targets)):
            force_index_map[i] = rf.addParticle(index, (k, target))
    
        ##
        # During simulation
        ##
    
    def update_position_restraint(self, force_index, k = None, target = None):
        rf = self._position_restraints_force
        rf.update_target(force_index, k, target)
    
    def release_position_restraint(self, force_index):
        self._position_restraints_force.release_restraint(force_index)
        
    def update_position_restraints_in_context(self, context):
        rf = self._position_restraints_force
        if rf.update_needed:
            rf.updateParametersInContext(context)
        rf.update_needed = False

        ##
        # Cleanup on simulation termination
        ##

    def disconnect_position_restraints_from_sim(self, restraints):
        for r in restraints:
            r.sim_force_index = -1
            r.sim_handler = None
    
    ####
    # Distance Restraints
    ####
    
        ##
        # Before simulation starts
        ##
        
    def initialize_distance_restraints_force(self, max_force):
        tf = self._distance_restraints_force = TopOutBondForce(max_force*10)
        self.all_forces.append(tf)
        return tf
    
    def add_distance_restraints(self, restraints, sim_construct):
        for r in restraints:
            self.add_distance_restraint(r, sim_construct)
    
    def add_distance_restraint(self, restraint, sim_construct):
        r = restraint
        atoms = r.atoms
        indices = sim_construct.indices(atoms)
        tf = self._distance_restraints_force
        r.sim_handler = self
        r.sim_force_index = tf.addBond(*indices.tolist(), (r.spring_constant*100, r.target_distance/10))
        
        ##
        # During simulation
        ##

    def change_distance_restraint_parameters(self, restraint):
        tf = self._distance_restraints_force
        indices = self._chimerax_atoms.indices(restraint.atoms).tolist()
        tf.setBondParameters(restraint._sim_force_index, *indices, 
            (restraint.spring_constant*100, restraint.target_distance/10))
        tf.update_needed = True
        
    def update_distance_restraints_in_context(self, context):
        tf = self._distance_restraints_force
        if tf.update_needed:
            tf.updateParametersInContext(context)
        tf.update_needed = False
    
        ##
        # Cleanup on simulation termination
        ##
    
    def disconnect_distance_restraints_from_sim(self, restraints):
        for r in restraints:
            r.sim_force_index = -1
            r.sim_handler = None
    
    
    ####
    # AMBER CMAP corrections
    ####
        
        ##
        # Before simulation starts
        ##
    
    def initialize_amber_cmap_force(self):
        cf = self._amber_cmap_force = AmberCMAPForce()
        self.all_forces.append(cf)
    
    def add_amber_cmap_torsions(self, phi_array, psi_array, sim_construct):
        cf = self._amber_cmap_force
        sc = sim_construct
        phi_has_psi = phi_array.residues.indices(psi_array.residues)
        psi_has_phi = psi_array.residues.indices(phi_array.residues)
        good_phi = phi_array[phi_has_psi[phi_has_psi != -1]]
        good_psi = psi_array[psi_has_phi[psi_has_phi != -1]]
        phi_resnames = good_phi.residues.names
        psi_resnames = good_psi.residues.names
        n = len(good_psi)
        phi_indices = sc.indices(good_phi.atoms).reshape((n,4))
        psi_indices = sc.indices(good_psi.atoms).reshape((n,4))
        
        for pname, fname, pi, fi in zip(phi_resnames, psi_resnames, 
                                        phi_indices, psi_indices):
            assert(pname == fname)
            cf.addTorsion(pname, pi, fi)
        
    
    
    ####
    # Dihedral restraints
    ####
    
        ##
        # Before simulation starts
        ##
    
    def initialize_dihedral_restraint_force(self, default_cutoff):
        
        df = self._dihedral_restraint_force = FlatBottomTorsionRestraintForce()
        self.default_torsion_cutoff = default_cutoff
        self.all_forces.append(df)
    
    def initialize_dihedral_restraint(self, indices, cutoff = None):
        #top = self._topology
        c = (cutoff or self.default_torsion_cutoff)
        force = self._dihedral_restraint_force
        index_in_force = force.addTorsion(*indices.tolist(), [0, 0, cos(c)])
        return index_in_force

        ##
        # During simulation
        ##
    
    def update_dihedral_restraints_in_context(self, context):
        rf = self._dihedral_restraint_force
        if rf.update_needed:
            rf.updateParametersInContext(context)
        rf.update_needed = False
    
    def set_dihedral_restraints(self, dihedrals, target, k, degrees = False, cutoffs = None):
        c = (cutoffs or [self.default_torsion_cutoff]*len(dihedrals))
        variable_t = hasattr(target, '__iter__')
        variable_k = hasattr(k, '__iter__')
        variable_c = hasattr(c, '__iter__')
        for i, d in enumerate(dihedrals):
            if variable_t:
                t = target[i]
            else:
                t = target
            if degrees:
                t = radians(t)
            if variable_k:
                thisk = k[i]
            else:
                thisk = k
            if variable_c:
                thisc = c[i]
            else:
                thisc = c
            
            self.update_dihedral_restraint(d.sim_index, target=t, k=thisk, cutoff=thisc)    
            
    def update_dihedral_restraint(self, sim_index, target = None, 
                            k = None, cutoff = None, degrees = False):
        if target is not None and degrees:
            target = radians(target)
        self._dihedral_restraint_force.update_target(sim_index, target=target, k=k, cutoff=cutoff)
        
    def register_custom_external_force(self, name, force, global_params, 
                                        per_particle_params, 
                                        per_particle_default_vals):
        self._custom_external_forces[name] = [force, global_params, per_particle_params, per_particle_default_vals, {}]
    
    def get_custom_external_force_by_name(self, name):
        return self._custom_external_forces[name]
    
    def get_all_custom_external_forces(self):
        return self._custom_external_forces
    
    def set_custom_external_force_particle_params(self, name, index, params):
        fparams = self._custom_external_forces[name]
        force = fparams[0]
        index_lookup = fparams[4]
        index_in_force = index_lookup[index]
        force.setParticleParameters(index_in_force, index, params)
       
    def register_map(self, map_object):
        self._maps.append(map_object)

    #TODO: Define the tugging force as a subclass in custom_forces.py
    def initialize_tugging_force(self):
        from simtk import openmm as mm
        potential_equation = '0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)'
        per_particle_parameters = ['k','x0','y0','z0']
        per_particle_defaults = [0,0,0,0]
        global_parameters = None
        global_defaults = None
        f = self._tugging_force = mm.CustomExternalForce(potential_equation)
        if global_parameters is not None:
            for p, v in zip(global_parameters, g_vals):
                f.addGlobalParameter(g, v)
        if per_particle_parameters is not None:
            for p in per_particle_parameters:
                f.addPerParticleParameter(p)
        self.register_custom_external_force('tug', f, global_parameters,
                per_particle_parameters, per_particle_defaults)
        
        self.all_forces.append(f)
        return f
    
    def couple_atoms_to_tugging_force(self, indices, force_map):
        force = self._tugging_force
        for i, index in enumerate(indices):
            force_map[i] = force.addParticle(i, (0,))
    
    def create_openmm_topology(self, atom_names, element_names,
                            residue_names, residue_numbers, chain_ids, 
                            bonded_atom_indices):
        '''
        Generate a simulation topology from generic Python and numpy 
        objects describing the simulation construct.
        @param atom_names:
            The names of the atoms (CA, CB etc.) in PDB standard nomenclature
        @param element_names:
            The PDB-standard element symbols for the atoms
        @param residue_names:
            Three-letter PDB-standard residue names, one per atom
        @param residue_numbers:
            The number of the residue each atom belongs to, one per atom
        @param chain_ids:
            The chain ID of each atom
        @param bonded_atom_indices:
            A tuple of two numpy arrays, where element i of each array
            provides the index of one of the two atoms involved in bond i
        '''
        
        anames   = atom_names
        n = len(aname)
        enames   = element_names
        rnames   = residue_names
        rnums    = residue_numbers
        cids    = chain_ids
        bond_is  = bonded_atom_indices
        
        from simtk.openmm.app import Topology, Element
        top = self.topology = Topology()
        cmap = {}
        rmap = {}
        atoms = self._atoms = {}
        rcount = 0
        for i, (aname, ename, rname, rnum, cid) in enumerate(
                zip(anames, enames, rnames, rnums, cids)):
            if not cid in cmap:
                cmap[cid] = top.addChain()   # OpenMM chains have no name
            rid = (rname, rnum, cid)
            if not rid in rmap:
                res = rmap[rid] = top.addResidue(rname, cmap[cid])
                template = residue_templates[rcount]
                

            element = Element.getBySymbol(ename)
            atoms[i] = top.addAtom(aname, element,rmap[rid])

        for i1, i2 in zip(*bond_is):
            top.addBond(atoms[i1],  atoms[i2])

        return top


    def create_openmm_system(self, topology, forcefield, templates, force_implicit = True):
        sys = self.system = create_openmm_system(topology, forcefield, templates, force_implicit)
        return sys    
    
    
    def set_fixed_atoms(self, fixed_indices):
        '''
        Fix the desired atoms rigidly in space for the duration of the
        simulation.
        @param fixed_indices:
            An array of atom indices to fix
        '''
        sys = self.system
        for index in fixed_indices:
            sys.setParticleMass(index, 0)
            
    def register_all_forces_with_system(self):
        sys = self.system
        forces = self.all_forces
        for f in forces:
            sys.addForce(f)
    
    def set_integrator(self, name, temperature, friction, tolerance, timestep):
        self.integrator = integrator(name, temperature, friction, tolerance, timestep)
    
    def openmm_topology_and_external_forces(self, sim_construct,
                                        sim_bonds, fixed_flags,
                                        tug_hydrogens = False,
                                        hydrogens_feel_maps = False):        
        '''
        Prepares the openmm topology and binds atoms to existing force fields.
        Since looping over all atoms can take a long time, it's best to do
        topology generation and force binding as a single concerted loop as
        much as we can. This should be possible for all external-type forces
        (tugging and map forces). Forces involving two or more atoms (e.g.
        H-bond or dihedral restraints) will have to be handled in separate
        loops.
        Args:
            sim_construct:
                The atoms to be simulated
            sim_bonds:
                The set of all bonds between simulated atoms
            fixed_flags:
                A boolean array indicating which atoms will be fixed. No
                need to add these to any custom forces.
            tug_hydrogens:
                Do we want to be able to interactively pull on hydrogens?
            hydrogens_feel_maps:
                Do we want the hydrogens to be pulled into the maps?
        '''
        # When we allow missing external bonds, some residues become ambiguous.
        # In particular, a cysteine with a bare sulphur might be part of a 
        # disulphide bond but have the connecting residue missing, or may be
        # a deprotonated (negatively-charged) Cys. In such cases, we need to 
        # explicitly tell OpenMM which templates to use.
        templates = {}
        a = self._chimerax_atoms = sim_construct
        n = len(a)
        r = a.residues
        aname = a.names
        ename = a.element_names
        rname = r.names
        rnum = r.numbers
        cids = r.chain_ids
        from simtk.openmm.app import Topology, Element
        from simtk import unit
        top = self._simulation_topology = Topology()
        cmap = {}
        rmap = {}
        atoms = self._atoms = {}
        for i in range(n):
            cid = cids[i]
            if not cid in cmap:
                cmap[cid] = top.addChain()   # OpenMM chains have no name
            rid = (rname[i], rnum[i], cid)
            if not rid in rmap:
                res = rmap[rid] = top.addResidue(rname[i], cmap[cid])
                if rname[i] == 'CYS':
                    ctype = cys_type(r[i])
                    if ctype != 'CYS':
                        templates[res] = ctype

            element = Element.getBySymbol(ename[i])
            atoms[i] = top.addAtom(aname[i], element,rmap[rid])

            if not fixed_flags[i]:
                # Register atoms with forces
                if ename[i] is not 'H' or (ename[i] is 'H' and tug_hydrogens):
                    # All CustomExternalForces
                    for key, ff in self._custom_external_forces.items():
                        f = ff[0]
                        per_particle_param_vals = ff[3]
                        index_map = ff[4]
                        index_map[i] = f.addParticle(i, per_particle_param_vals)
            
                if ename[i] is not 'H' or (ename[i] is 'H' and hydrogens_feel_maps):
                    # All map forces
                    for m in self._maps:
                        self.couple_atom_to_map(i, m)

        
        a1, a2 = sim_bonds.atoms
        for i1, i2 in zip(a.indices(a1), a.indices(a2)):
            if -1 not in [i1, i2]:
                top.addBond(atoms[i1],  atoms[i2])

        pos = a.coords # in Angstrom (convert to nm for OpenMM)
        return top, pos, templates

    def couple_atoms_to_map(self, indices, ks, force, force_map):
        for i, (index, k) in enumerate(zip(indices, ks)):
            force_map[i] = force.addBond(index, (k,))
    
    def couple_atom_to_map(self, index, map_object):
        '''
        Adds an atom to a map-derived potential field.
        The argument per_atom_coupling must be either a single value, 
        or an array with one value per atom
        '''
        m = map_object
        map_field = m.get_potential_function()
        k = m.get_per_atom_coupling_params()
        if m.per_atom_coupling():
            k = k[index]
        map_field.addBond([index],[k])


    def map_to_force_field(self, imap, atoms, 
                            pad, normalize = True):
        '''
        Takes an IsoldeMap object, masks down the map to cover the atoms
        with the desired padding, and converts it into a LinearInterpMapForce
        object. 
        '''
        vd, r = imap.crop_to_selection(atoms, pad, normalize)
        tf = r.xyz_to_ijk_transform.matrix
        f = self._map_to_force_field(vd, r, tf, imap.get_coupling_constant())
        imap.set_potential_function(f)
    
    def _map_to_force_field(self, volume_data, xyz_to_ijk_transform,
                            coupling_constant):
        vd = volume_data
        tf = xyz_to_ijk_transform
        f = LinearInterpMapForce(vd, tf, units='angstroms')
        f.set_global_k(coupling_constant)
        self.all_forces.append(f)
        return f
    
    
    def continuous3D_from_volume(self, vol_data):
        '''
        Takes a volumetric map and uses it to generate an OpenMM 
        Continuous3DFunction. Returns the function.
        '''
        import numpy as np
        vol_dimensions = vol_data.shape[::-1]
        mincoor = np.array([0,0,0], np.double)
        maxcoor = (np.array(vol_dimensions, np.double) - 1) / 10
        # Continuous3DFunction expects the minimum and maximum coordinates as
        # arguments xmin, xmax, ymin, ...
        minmax = [val for pair in zip(mincoor, maxcoor) for val in pair]
        vol_data_1d = np.ravel(vol_data, order = 'C')
        from simtk.openmm.openmm import Continuous3DFunction    
        return Continuous3DFunction(*vol_dimensions, vol_data_1d, *minmax)
    
    def continuous3D_from_maps(self, master_map_list, keys, atoms, pad, normalize):
        '''
        Combine multiple maps into a single Continuous3DFunction by 
        summing their data with applied weights. 
        '''
        from . import volumetric
        combined_map = None
        for key in keys:
            m = master_map_list[key]
            vd, r = m.crop_to_selection(atoms, pad, normalize)
            weighted_map = vd*m.get_coupling_constant()
            if combined_map is None:
                combined_map = weighted_map
            else:
                combined_map += weighted_map
        c3d = self.continuous3D_from_volume(combined_map)
        f = self.map_potential_force_field(c3d, 1.0, r)
        ret = GenericMapObject(f, False, 1.0)
        return ret
        

    def map_potential_force_field(self, c3d_func, global_k, region):
        '''
        Takes a Continuous3DFunction and returns a CustomCompoundBondForce 
        based on it.
        Args:
            c3d_func:
                A Continuous3DFunction
            global_k:
                An overall global spring constant coupling atoms to the 
                map. This can be further adjusted per atom using 
                the "individual_k" parameter defined in the 
                CustomCompoundBondForce energy function.
            xyz_to_ijk_transform:
                The affine transformation matrix mapping (x,y,z) coordinates
                back to (i,j,k) in the c3d_func array
        '''
        xyz_to_ijk_transform = region.xyz_to_ijk_transform
        from simtk.openmm import CustomCompoundBondForce
        f = CustomCompoundBondForce(1,'')
        f.addTabulatedFunction(name = 'map_potential', function = c3d_func)
        f.addGlobalParameter(name = 'global_k', defaultValue = global_k)
        f.addPerBondParameter(name = 'individual_k')
        tf = xyz_to_ijk_transform.matrix
        tf[:,3] /= 10 # OpenMM in nm, ChimeraX in Angstroms
        i_str = 'x1* {} + y1 * {} + z1 * {} + {}'.format(
            tf[0][0], tf[0][1], tf[0][2], tf[0][3])
        j_str = 'x1* {} + y1 * {} + z1 * {} + {}'.format(
            tf[1][0], tf[1][1], tf[1][2], tf[1][3])
        k_str = 'x1* {} + y1 * {} + z1 * {} + {}'.format(
            tf[2][0], tf[2][1], tf[2][2], tf[2][3])
        
        f.setEnergyFunction('-global_k * individual_k * map_potential({},{},{})'.format(
        i_str, j_str, k_str))
        return f

    
    def update_force_in_context(self, force_name, context):
        force = self._custom_external_forces[force_name][0]
        force.updateParametersInContext(context)


def define_forcefield (forcefield_list):
    from simtk.openmm.app import ForceField
    ff = self_forcefield = ForceField(*[f for f in forcefield_list if f is not None])
    return ff


def initialize_implicit_solvent(system, top):
    '''Add a Generalised Born Implicit Solvent (GBIS) formulation.'''
    # Somewhat annoyingly, OpenMM doesn't store atomic charges in a 
    # nice accessible format. So, we have to pull it back out of the
    # NonbondedForce term.
    for f in system.getForces():
        if isinstance(f, NonbondedForce):
            break
    charges = []
    for i in range(f.getNumParticles()):
        charges.append(f.getParticleParameters(i)[0])
    gbforce = GBSAForce()
    params = GBSAForce.getStandardParameters(top)
    print('charge length: {}, param length: {}, natoms: {}, top_n: {}'.format(
        len(charges), len(params), f.getNumParticles(), top.getNumAtoms()))
    i = 0
    for charge, param in zip(charges, params):
        gbforce.addParticle([charge, *param])
        i+= 1
    print(i)
    gbforce.finalize()
    print('GB Force num particles: '.format(gbforce.getNumParticles()))
    system.addForce(gbforce)


    
def create_openmm_system(top, ff, templatedict, force_implicit=False):
    from simtk.openmm import app
    from simtk import openmm as mm
    from simtk import unit

    params = {
        'nonbondedMethod':      app.CutoffNonPeriodic,
        'nonbondedCutoff':      defaults.OPENMM_NONBONDED_CUTOFF,
        'constraints':          app.HBonds,
        'rigidWater':           True,
        'removeCMMotion':       False,
        'residueTemplates':     templatedict,
        'ignoreExternalBonds':  True,
        }
    
        
    try:
        #~ system = ff.createSystem(top,
                                #~ nonbondedMethod = app.CutoffNonPeriodic,
                                #~ nonbondedCutoff = 1.0*unit.nanometers,
                                #~ constraints = app.HBonds,
                                #~ rigidWater = True,
                                #~ removeCMMotion = False,
                                #~ residueTemplates = templatedict,
                                #~ ignoreExternalBonds = True)
        system = ff.createSystem(top, **params)
        if force_implicit:
            print('Setting up implicit solvent...')
            initialize_implicit_solvent(system, top)
    except ValueError as e:
        raise Exception('Missing atoms or parameterisation needed by force field.\n' +
                              'All heavy atoms and hydrogens with standard names are required.\n' +
                              str(e))
    return system


def integrator(i_type, temperature, friction, tolerance, timestep):
    from simtk import openmm as mm
    if i_type == 'variable':
        integrator = mm.VariableLangevinIntegrator(temperature, friction, tolerance)
    elif i_type == 'fixed':
        integrator = mm.LangevinIntegrator(temperature, friction, timestep)
    return integrator
    
def platform(name):
    from simtk.openmm import Platform
    return Platform.getPlatformByName(name)


def create_sim(topology, system, integrator, platform):
    from simtk.openmm.app import Simulation
    return Simulation(topology, system, integrator, platform)

