import pickle
import numpy

from simtk.openmm.app import *
from simtk.openmm import *
from simtk.unit import *
from sys import stdout

from os import environ, path
environ['OPENMM_PLUGIN_DIR'] = '/home/tic20/apps/chimerax/lib/plugins'

def continuous3D_from_volume(vol_data, origin, step):
    '''
    Takes a volumetric map and uses it to generate an OpenMM 
    Continuous3DFunction. Returns the function.
    '''
    mincoor = numpy.array(origin)
    print('Mincoor: {}'.format(mincoor))
    step = numpy.array(step)
    print('Step: {}'.format(step))
    vol_dimensions = numpy.array(vol_data.shape)
    maxcoor = mincoor + vol_dimensions*step  
    #Map data is in Angstroms. Need to convert (x,y,z) positions to nanometres
    mincoor = mincoor/10
    maxcoor = maxcoor/10
    # Continuous3DFunction expects the minimum and maximum coordinates as
    # arguments xmin, xmax, ymin, ...
    minmax = [val for pair in zip(mincoor, maxcoor) for val in pair]
    vol_data_1d = numpy.ravel(vol_data, order = 'C').astype(numpy.double)
    print('Max: {}, min: {}, nans: {}, infs: {}'.format(
        vol_data_1d.max(), vol_data_1d.min(), 
        numpy.argwhere(numpy.isnan(vol_data_1d)),
        numpy.argwhere(numpy.isinf(vol_data_1d))))
    from simtk.openmm.openmm import Continuous3DFunction    
    return Continuous3DFunction(*(vol_dimensions.tolist()), vol_data_1d, *minmax)


def map_potential_force_field(c3d_func, global_k):
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
    '''
    from simtk.openmm import CustomCompoundBondForce
    f = CustomCompoundBondForce(1,'')
    f.addTabulatedFunction(name = 'map_potential', function = c3d_func)
    f.addGlobalParameter(name = 'global_k', defaultValue = global_k)
    f.addPerBondParameter(name = 'individual_k')
    f.setEnergyFunction('-global_k * individual_k * map_potential(x1,y1,z1)')
    return f


infile = open('volume_matrix.pickle', 'r+b')
data_origin_and_step, data = pickle.load(infile)
infile.close()

global_k = 10.0
individual_k = 1.0

c3d_func = continuous3D_from_volume(data, *data_origin_and_step)
map_potential = map_potential_force_field(c3d_func, global_k)



pdb = PDBFile('1pmx_A.pdb')
forcefield = ForceField('amber99sb.xml', 'tip3p.xml')
top = pdb.topology
    
system = forcefield.createSystem(top, nonbondedMethod=CutoffNonPeriodic,
                        nonbondedCutoff=1*nanometer, constraints=HBonds,
                        removeCMMotion = False)

fixed_residue_cutoff = -1
for i, a in enumerate(top.atoms()):
    if a.residue.index > fixed_residue_cutoff:
        if a.element.symbol != 'H':
            map_potential.addBond([i],[individual_k])
    else:
        system.setParticleMass(i,0)

system.addForce(map_potential)
for i, f in enumerate(system.getForces()):
    f.setForceGroup(i)

platform = Platform.getPlatformByName('OpenCL')
integrator = LangevinIntegrator(300*kelvin, 1/picosecond, 0.002*picoseconds)
simulation = Simulation(pdb.topology, system, integrator, platform)
simulation.context.setPositions(pdb.positions)
for i, f in enumerate(system.getForces()):
    print(f, simulation.context.getState(getEnergy=True, groups = {i}).getPotentialEnergy())

