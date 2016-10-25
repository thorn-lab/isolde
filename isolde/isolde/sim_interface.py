
class available_forcefields():
    # Main force field files
    main_files = [
        'amber99sbildn.xml',
        'amber99sbnmr.xml',
        'amber10.xml'
        ]
    
    main_file_descriptions = [
        'AMBER99 with improved backbone & sidechain torsions',
        'AMBER99 with modifications to fit NMR data',
        'AMBER10'
        ]
    
    # Implicit solvent force field files. The main file and the implicit
    # solvent file must match.
    implicit_solvent_files = [
        'amber99_obc.xml',
        'amber99_obc.xml',
        'amber10_obc.xml'
        ]
    
    # Explicit water models
    explicit_water_files = [
        'tip3pfb.xml',
        'tip4pfb.xml',
        'tip3p.xml'
        ]
    
    explicit_water_descriptions = [
        'TIP3P-FB (DOI: 10.1021/jz500737m)',
        'TIP4P-FB (DOI: 10.1021/jz500737m)',
        'Original TIP3P water (not recommended)'
        ]

def get_available_platforms():
    from simtk.openmm import Platform
    platform_names = []
    for i in range(Platform.getNumPlatforms()):
        p = Platform.getPlatform(i)
        name = p.getName()
        platform_names.append(name)
    return platform_names

    
def openmm_topology_and_coordinates(sim_construct,
                                    sim_bonds,
                                    fix_shell_backbones = False,
                                    logging = False,
                                    log = None):        
    a = sim_construct
    n = len(a)
    r = a.residues
    aname = a.names
    ename = a.element_names
    rname = r.names
    rnum = r.numbers
    cids = r.chain_ids
    from simtk.openmm.app import Topology, Element
    from simtk import unit
    top = Topology()
    cmap = {}
    rmap = {}
    atoms = {}
    for i in range(n):
        cid = cids[i]
        if not cid in cmap:
            cmap[cid] = top.addChain()   # OpenMM chains have no name
        rid = (rname[i], rnum[i], cid)
        if not rid in rmap:
            rmap[rid] = top.addResidue(rname[i], cmap[cid])
        element = Element.getBySymbol(ename[i])
        atoms[i] = top.addAtom(aname[i], element,rmap[rid])
    
    
    a1, a2 = sim_bonds.atoms
    for i1, i2 in zip(a1.indices(a), a2.indices(a)):
        #if logging and log is not None:
            #for num, i in enumerate([i1, i2]):
                #info_str = 'Atom ' + str(num) + ': Chain ' + a[i].chain_id + \
                             #' Resid ' + str(a[i].residue.number) + ' Resname ' + a[i].residue.name + ' Name ' + a[i].name
                #log(info_str)

        if -1 not in [i1, i2]:
            top.addBond(atoms[i1],  atoms[i2])
    
    from simtk.openmm import Vec3
    pos = a.coords # in Angstrom (convert to nm for OpenMM)
    return top, pos


# Takes a volumetric map and uses it to generate an OpenMM Continuous3DFunction.
# Returns the function.
def continuous3D_from_volume(volume):
    import numpy as np
    vol_data = volume.data
    mincoor = np.array(vol_data.origin)
    maxcoor = mincoor + volume.data_origin_and_step()[1]*(np.array(vol_data.size)-1)
    #Map data is in Angstroms. Need to convert (x,y,z) positions to nanometres
    mincoor = mincoor/10
    maxcoor = maxcoor/10
    # Continuous3DFunction expects the minimum and maximum coordinates as
    # arguments xmin, xmax, ymin, ...
    minmax = [val for pair in zip(mincoor, maxcoor) for val in pair]
    vol_data_1d = np.ravel(vol_data.matrix(), order = 'C')
    vol_dimensions = (vol_data.size)
    from simtk.openmm.openmm import Continuous3DFunction    
    return Continuous3DFunction(*vol_dimensions, vol_data_1d, *minmax)
    
# Takes a Continuous3DFunction and returns a CustomCompoundBondForce based on it
def map_potential_force_field(c3d_func):
    from simtk.openmm import CustomCompoundBondForce
    f = CustomCompoundBondForce(1,'')
    f.addTabulatedFunction(name = 'map_potential', function = c3d_func)
    f.addGlobalParameter(name = 'global_k', defaultValue = 1.0)
    f.addPerBondParameter(name = 'individual_k')
    f.setEnergyFunction('-global_k * individual_k * map_potential(x1,y1,z1)')
    return f

# Take the atoms in a topology, and add them to a map-derived potential field.
# per_atom_coupling must be either a single value, or an array with one value
# per atom
def couple_atoms_to_map(top, map_field, global_coupling_constant, \
                        hydrogens = False, per_atom_coupling = 1.0):
    if not isinstance(per_atom_coupling, list):
        global_coupling = True
        k = per_atom_coupling
    else:
        global_coupling = False
    # Find the global coupling constant parameter in the Force and set its new value
    for i in range(map_field.getNumGlobalParameters()):
        if map_field.getGlobalParameterName(i) == 'global_k':
            map_field.setGlobalParameterDefaultValue(i, global_coupling_constant)
            break
    
    for a in top.atoms():
        i = a.index
        if not hydrogens:
            if a.element.name == 'hydrogen':
                continue
        if not global_coupling:
            k = per_atom_coupling[i]
        map_field.addBond([i],[k])
            
            




def define_forcefield (forcefield_list):
    from simtk.openmm.app import ForceField
    return ForceField(*forcefield_list)
    
def create_openmm_system(top, ff):
    from simtk.openmm import app
    from simtk import openmm as mm
    from simtk import unit
    
    try:
        system = ff.createSystem(top,
                                nonbondedMethod = app.CutoffNonPeriodic,
                                nonbondedCutoff = 1.0*unit.nanometers,
                                constraints = app.HBonds,
                                rigidWater = True,
                                removeCMMotion = False,
                                ignoreMissingExternalBonds = True)
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
    

    

