from simtk import unit, openmm
from math import pi
import ctypes

'''
Constants are a slightly difficult problem here, in that ChimeraX works
in Angstroms while OpenMM works in 
'''

_defaults = {
    ###
    # Units
    ###
    'OPENMM_LENGTH_UNIT':         unit.nanometer,
    'OPENMM_FORCE_UNIT':          unit.kilojoule_per_mole/unit.nanometer,
    'OPENMM_SPRING_UNIT':         unit.kilojoule_per_mole/unit.nanometer**2,
    'OPENMM_RADIAL_SPRING_UNIT':  unit.kilojoule_per_mole/unit.radians**2,
    'OPENMM_ENERGY_UNIT':         unit.kilojoule_per_mole,
    'OPENMM_ANGLE_UNIT':          unit.radians,
    'OPENMM_TIME_UNIT':           unit.picoseconds,

    ###
    # Simulation parameters
    ###
    'OPENMM_INTEGRATOR_TYPE':     openmm.VariableLangevinIntegrator,
    'OPENMM_NONBONDED_CUTOFF':    1.0, #* unit.nanometers,
    'OPENMM_FRICTION':            5.0, #/ unit.picoseconds,
    'OPENMM_VAR_INTEGRATOR_TOL':  1e-4,
    'OPENMM_CONSTRAINT_TOL':      1e-4,
    'OPENMM_FIXED_INTEGRATOR_TS': 0.001, #* unit.picoseconds,
    'SIM_STEPS_PER_GUI_UPDATE':   50,
    'MIN_STEPS_PER_GUI_UPDATE':   100,
    'SIM_STARTUP_ROUNDS':         10,
    'MAX_UNSTABLE_ROUNDS':        20,
    'ROUNDS_PER_RAMA_UPDATE':     5,
    'ROUNDS_PER_MAP_REMASK':      20,
    'FIX_SOFT_SHELL_BACKBONE':    False,
    'TEMPERATURE':                100.0, # * unit.kelvin,
    
    ###
    # Force constants
    ###
    'MAX_RESTRAINT_FORCE':                  25000.0, # * unit.kilojoule_per_mole/unit.nanometer,
    'HAPTIC_SPRING_CONSTANT':                2500.0, # * unit.kilojoule_per_mole/unit.nanometer**2,
    'MOUSE_TUG_SPRING_CONSTANT':            10000.0, # * unit.kilojoule_per_mole/unit.nanometer**2,
    'MAX_TUG_FORCE':                        10000.0, # * unit.kilojoule_per_mole/unit.nanometer,
    'DISTANCE_RESTRAINT_SPRING_CONSTANT':    5000.0, # * unit.kilojoule_per_mole/unit.nanometer**2,
    'POSITION_RESTRAINT_SPRING_CONSTANT':    2000.0, # * unit.kilojoule_per_mole/unit.nanometer**2,
    'PEPTIDE_SPRING_CONSTANT':                500.0, # * unit.kilojoule_per_mole/unit.radians**2,  
    'PHI_PSI_SPRING_CONSTANT':                250.0, # * unit.kilojoule_per_mole/unit.radians**2, 
    'ROTAMER_SPRING_CONSTANT':               1000.0, # * unit.kilojoule_per_mole/unit.radians**2,
    'STANDARD_MAP_K':                           5.0, # * unit.kilojoule_per_mole/unit.nanometer**2,
    'DIFFERENCE_MAP_K':                         1.0, # * unit.kilojoule_per_mole/unit.nanometer**2,
    
    ###
    # Safety limits
    ###
    'MAX_ALLOWABLE_FORCE':        4.0e4, # * unit.kilojoule_per_mole/unit.nanometer,
    'MAX_ATOM_MOVEMENT_PER_STEP':   0.5, # * unit.nanometer,
    
    ###
    # Geometric parameters
    ###
    'DIHEDRAL_RESTRAINT_CUTOFF':    pi/6,  # * unit.radians, # 30 degrees  
    'ROTAMER_RESTRAINT_CUTOFF':     pi/12, # * unit.radians, # 15 degrees
    'CIS_PEPTIDE_BOND_CUTOFF':      pi/6,  # * unit.radians, # 30 degrees
    
    ###
    # Constants specific to ChimeraX - lengths in Angstroms beyond this point!
    ###
    
    'SELECTION_SEQUENCE_PADDING':   3,      # residues
    'SOFT_SHELL_CUTOFF':            5,      # Angstroms
    'HARD_SHELL_CUTOFF':            8,      # Angstroms
    
    'STANDARD_MAP_MASK_RADIUS':   4.0, # Angstroms  
    'DIFFERENCE_MAP_MASK_RADIUS': 8.0, # Angstroms

    
    
    ###
    # Types for shared variables
    ###
    'FLOAT_TYPE' :                  ctypes.c_float,
}

class _Defaults:
    pass

def _fset_factory():
    def fset(self, value):
        raise TypeError("Can't change value of a constant!")
    return fset

def _fget_factory(val):
    def fget(self):
        return val
    return fget

for (name, val) in _defaults.items():
    setattr(_Defaults, name, property(_fget_factory(val), _fset_factory()))

defaults = _Defaults()

        
    


