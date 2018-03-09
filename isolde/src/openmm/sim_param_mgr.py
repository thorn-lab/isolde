# Copyright 2017 Tristan Croll
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.



import numpy
import os, sys
import multiprocessing as mp
import ctypes
from math import pi, radians, degrees, cos
from warnings import warn
from time import time, sleep
from simtk import unit
from simtk.unit import Quantity, Unit
from chimerax.core.atomic import concatenate, Bonds

from ..checkpoint import CheckPoint
from ..threading.shared_array import TypedMPArray, SharedNumpyArray
from . import sim_thread
from .sim_thread import SimComms, SimThread, ChangeTracker
from ..constants import defaults, sim_outcomes, control
from ..param_mgr import Param_Mgr, autodoc, param_properties

OPENMM_LENGTH_UNIT = defaults.OPENMM_LENGTH_UNIT
OPENMM_FORCE_UNIT = defaults.OPENMM_FORCE_UNIT
OPENMM_SPRING_UNIT = defaults.OPENMM_SPRING_UNIT
OPENMM_RADIAL_SPRING_UNIT = defaults.OPENMM_RADIAL_SPRING_UNIT
OPENMM_ENERGY_UNIT = defaults.OPENMM_ENERGY_UNIT
OPENMM_ANGLE_UNIT = defaults.OPENMM_ANGLE_UNIT
OPENMM_TIME_UNIT = defaults.OPENMM_TIME_UNIT
OPENMM_DIPOLE_UNIT = defaults.OPENMM_DIPOLE_UNIT
OPENMM_TEMPERATURE_UNIT = defaults.OPENMM_TEMPERATURE_UNIT
CHIMERAX_LENGTH_UNIT        = defaults.CHIMERAX_LENGTH_UNIT
CHIMERAX_FORCE_UNIT         = defaults.CHIMERAX_FORCE_UNIT
CHIMERAX_SPRING_UNIT        = defaults.CHIMERAX_SPRING_UNIT

SIM_MODE_MIN                = control.SIM_MODE_MIN
SIM_MODE_EQUIL              = control.SIM_MODE_EQUIL
SIM_MODE_UNSTABLE           = control.SIM_MODE_UNSTABLE

CARBON_MASS = defaults.CARBON_MASS
CARBON_ATOMIC_NUMBER = defaults.CARBON_ATOMIC_NUMBER

def error_cb(e):
    print(e.__traceback__)
    print(e)

FLOAT_TYPE = defaults.FLOAT_TYPE

_amber14 = ['amberff14SB.xml','tip3p_standard.xml',
            'tip3p_HFE_multivalent.xml', 'tip3p_IOD_multivalent.xml']

cwd = os.path.dirname(os.path.abspath(__file__))
amber14 = [os.path.join(cwd,'amberff',f) for f in _amber14]

@param_properties
@autodoc
class SimParams(Param_Mgr):
    '''
    Container for all the parameters needed to initialise a simulation
    '''
    _default_params = {
        'restraint_max_force':                  (defaults.MAX_RESTRAINT_FORCE, OPENMM_FORCE_UNIT),
        'distance_restraint_spring_constant':   (defaults.DISTANCE_RESTRAINT_SPRING_CONSTANT, OPENMM_SPRING_UNIT),
        'position_restraint_spring_constant':   (defaults.POSITION_RESTRAINT_SPRING_CONSTANT, OPENMM_SPRING_UNIT),
        'haptic_spring_constant':               (defaults.HAPTIC_SPRING_CONSTANT, OPENMM_SPRING_UNIT),
        'mouse_tug_spring_constant':            (defaults.MOUSE_TUG_SPRING_CONSTANT, OPENMM_SPRING_UNIT),
        'tug_max_force':                        (defaults.MAX_TUG_FORCE, OPENMM_FORCE_UNIT),
        'dihedral_restraint_cutoff_angle':      (defaults.DIHEDRAL_RESTRAINT_CUTOFF, OPENMM_ANGLE_UNIT),
        'rotamer_restraint_cutoff_angle':       (defaults.ROTAMER_RESTRAINT_CUTOFF, OPENMM_ANGLE_UNIT),
        'rotamer_spring_constant':              (defaults.ROTAMER_SPRING_CONSTANT, OPENMM_RADIAL_SPRING_UNIT),
        'peptide_bond_spring_constant':         (defaults.PEPTIDE_SPRING_CONSTANT, OPENMM_RADIAL_SPRING_UNIT),
        'phi_psi_spring_constant':              (defaults.PHI_PSI_SPRING_CONSTANT, OPENMM_RADIAL_SPRING_UNIT),
        'cis_peptide_bond_cutoff_angle':        (defaults.CIS_PEPTIDE_BOND_CUTOFF, OPENMM_ANGLE_UNIT),
        'max_atom_movement_per_step':           (defaults.MAX_ATOM_MOVEMENT_PER_STEP, OPENMM_LENGTH_UNIT),
        'max_allowable_force':                  (defaults.MAX_ALLOWABLE_FORCE, OPENMM_FORCE_UNIT),
        'max_stable_force':                     (defaults.MAX_STABLE_FORCE, OPENMM_FORCE_UNIT),
        'friction_coefficient':                 (defaults.OPENMM_FRICTION, 1/OPENMM_TIME_UNIT),
        'temperature':                          (defaults.TEMPERATURE, OPENMM_TEMPERATURE_UNIT),

        'nonbonded_cutoff_method':              (defaults.OPENMM_NONBONDED_METHOD, None),
        'nonbonded_cutoff_distance':            (defaults.OPENMM_NONBONDED_CUTOFF, OPENMM_LENGTH_UNIT),

        'vacuum_dielectric_correction':         (defaults.VACUUM_DIELECTRIC_CORR, OPENMM_DIPOLE_UNIT),

        'use_gbsa':                             (defaults.USE_GBSA, None),
        'gbsa_cutoff_method':                   (defaults.GBSA_NONBONDED_METHOD, None),
        'gbsa_solvent_dielectric':              (defaults.GBSA_SOLVENT_DIELECTRIC, OPENMM_DIPOLE_UNIT),
        'gbsa_solute_dielectric':               (defaults.GBSA_SOLUTE_DIELECTRIC, OPENMM_DIPOLE_UNIT),
        'gbsa_sa_method':                       (defaults.GBSA_SA_METHOD, None),
        'gbsa_cutoff':                          (defaults.GBSA_CUTOFF, OPENMM_LENGTH_UNIT),
        'gbsa_kappa':                           (defaults.GBSA_KAPPA, 1/OPENMM_LENGTH_UNIT),

        'rigid_bonds':                          (defaults.RIGID_BONDS, None),
        'rigid_water':                          (defaults.RIGID_WATER, None),
        'remove_c_of_m_motion':                 (defaults.REMOVE_C_OF_M_MOTION, None),

        'platform':                             (defaults.OPENMM_PLATFORM, None),
        'forcefield':                           ('amber14', None),
        'integrator':                           (defaults.OPENMM_INTEGRATOR_TYPE, None),
        'variable_integrator_tolerance':        (defaults.OPENMM_VAR_INTEGRATOR_TOL, None),
        'fixed_integrator_timestep':            (defaults.OPENMM_FIXED_INTEGRATOR_TS, None),
        'constraint_tolerance':                 (defaults.OPENMM_CONSTRAINT_TOL, None),
        'sim_steps_per_gui_update':             (defaults.SIM_STEPS_PER_GUI_UPDATE, None),
        'minimization_steps_per_gui_update':    (defaults.MIN_STEPS_PER_GUI_UPDATE, None),
        'simulation_startup_rounds':            (defaults.SIM_STARTUP_ROUNDS, None),
        'maximum_unstable_rounds':              (defaults.MAX_UNSTABLE_ROUNDS, None),
        'minimization_convergence_tol':         (defaults.MIN_CONVERGENCE_FORCE_TOL, OPENMM_FORCE_UNIT),
        'tug_hydrogens':                        (False, None),
        'hydrogens_feel_maps':                  (defaults.HYDROGENS_FEEL_MAPS, None),
        'target_loop_period':                   (defaults.TARGET_LOOP_PERIOD, None),

    }