# @Author: Tristan Croll <tic20>
# @Date:   18-Apr-2018
# @Email:  tic20@cam.ac.uk
# @Last modified by:   tic20
# @Last modified time: 26-Apr-2018
# @License: Free for non-commercial use (see license.pdf)
# @Copyright: 2017-2018 Tristan Croll



from math import pi, radians

'''
Constants are a slightly difficult problem here, in that ChimeraX works
in Angstroms while OpenMM works in nanometres
'''

def _constant_property_factory(key):
    def fget(self):
        return self._constants[key]

    def fset(self, val):
        raise TypeError("Can't change value of a constant!")

    return property(fget, fset)

def _constant_properties(cls):
    for key in cls._constants.keys():
        setattr(cls, key, _constant_property_factory(key))
    return cls


@_constant_properties
class _SS_Helix:
    _constants = {
        'CA_TO_CA_PLUS_TWO_DISTANCE':        5.43,
        'O_TO_N_PLUS_FOUR_DISTANCE':         3.05,
        'PHI_ANGLE':                         radians(-64.0),
        'PSI_ANGLE':                         radians(-41.0),
        'CUTOFF_ANGLE':                      radians(10.0),
    }

@_constant_properties
class _SS_Beta_Parallel:
    _constants = {
        'CA_TO_CA_PLUS_TWO_DISTANCE':        6.81,
        'O_TO_N_PLUS_FOUR_DISTANCE':         11.4,
        'PHI_ANGLE':                         radians(-119.0),
        'PSI_ANGLE':                         radians(113.0),
        'CUTOFF_ANGLE':                      radians(10.0),
    }

@_constant_properties
class _SS_Beta_Antiparallel:
    _constants = {
        'CA_TO_CA_PLUS_TWO_DISTANCE':        6.81,
        'O_TO_N_PLUS_FOUR_DISTANCE':         11.4,
        'PHI_ANGLE':                         radians(-139.0),
        'PSI_ANGLE':                         radians(135.0),
        'CUTOFF_ANGLE':                      radians(10.0),
    }

ss_restraints = {
    'Helix':                _SS_Helix(),
    'Parallel Beta':        _SS_Beta_Parallel(),
    'Antiparallel Beta':    _SS_Beta_Antiparallel(),
}
