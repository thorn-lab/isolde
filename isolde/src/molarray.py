
from numpy import uint8, int32, uint32, float64, float32, uintp, byte, bool as npy_bool, integer, empty, array
from chimerax.core.atomic.molc import string, cptr, pyobject, set_cvec_pointer, pointer, size_t
from chimerax.core.atomic.molarray import Collection
from . import molobject
from .molobject import c_function, c_array_function, cvec_property
#from .molobject import object_map
from .molobject import Proper_Dihedral, Rotamer, Distance_Restraint
import ctypes

from chimerax.core.atomic import Atom, Atoms, Residue, Residues

from chimerax.core.atomic.molarray import _atoms, _atoms_or_nones, \
        _bonds, _non_null_atoms, _pseudobond_groups, _pseudobonds, \
        _elements, _residues, _non_null_residues, _chains, \
        _non_null_chains, _atomic_structures, structure_datas, \
        _atoms_pair, _pseudobond_group_map

def _proper_dihedrals(p):
    return Proper_Dihedrals(p)
def _rotamers(p):
    return Rotamers(p)
def _proper_dihedrals_or_nones(p):
    return [Proper_Dihedral.c_ptr_to_py_inst(ptr) if ptr else None for ptr in p]
def _distance_restraints(p):
    return Distance_Restraints(p)
def _non_null_proper_dihedrals(p):
    return Proper_Dihedrals(p[p!=0])
def _atoms_four_tuple(p):
    return tuple((Atoms(p[:,i].copy()) for i in range(4)))



class _Dihedrals(Collection):
    '''
    Base class for Proper_Dihedrals and Improper_Dihedrals. Do not
    instantiate directly.
    '''

    def __init__(self, c_pointers, single_class, array_class):
        super().__init__(c_pointers, single_class, array_class)

    atoms = cvec_property('dihedral_atoms', cptr, 4, astype=_atoms_four_tuple, read_only=True,
        doc = '''
        Returns a four-tuple of :class:`Atoms` objects. For each dihedral,
        its constituent atoms are in the matching position in the four
        :class:`Atoms` collections. Read only.
        ''')
    angles = cvec_property('dihedral_angle', float32, read_only=True,
        doc='Returns the angle in radians for each dihedral. Read only.')
    names = cvec_property('dihedral_name', string, read_only=True)


class Proper_Dihedrals(_Dihedrals):

    def __init__(self, c_pointers = None):
        super().__init__(c_pointers, Proper_Dihedral, Proper_Dihedrals)

    def delete(self):
        err_string = 'Dihedrals are not in charge of their own creation '\
            +'and deletion. Instead, use '\
            +'session.proper_dihedrals_mgr.delete_dihedrals(dihedrals).'
        raise RuntimeError(err_string)

    residues = cvec_property('proper_dihedral_residue', cptr, astype=_residues, read_only=True,
        doc='Returns a :class:`Residues` giving the parent residue of each dihedral. Read only')
    axial_bonds = cvec_property('proper_dihedral_axial_bond', cptr, astype=_bonds, read_only=True,
        doc='Returns a :class:`Bonds` giving the axial bond for each dihedral. Read-only')

class Ramas(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, Rotamer, Rotamers)

    residues = cvec_property('rama_residue', cptr, astype=_residues, read_only = True,
            doc = 'The residue to which each Rama belongs. Read only.')
    ca_atoms = cvec_property('rama_ca_atom', cptr, astype=_atoms, read_only = True,
            doc = 'The alpha carbon of each amino acid residue. Read only.')
    valids = cvec_property('rama_is_valid', npy_bool, read_only = True,
            doc = 'True for each residue that has all three of omega, phi and psi. Read only.')
    scores = cvec_property('rama_score', float64, read_only = True,
            doc = 'The score of each residue on the MolProbity Ramachandran contours. Read only.')
    phipsis = cvec_property('rama_phipsi', float64, 2, read_only = True,
            doc = 'The phi and psi angles for each residue in radians. Read only.')
    angles = cvec_property('rama_omegaphipsi', float64, 3, read_only = True,
            doc = 'The omega, phi and psi angles for each residue in radians. Read only.')


class Rotamers(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, Rotamer, Rotamers)

    residues = cvec_property('rotamer_residue', cptr, astype=_residues, read_only=True,
                doc='Residue this rotamer belongs to. Read only.')
    scores = cvec_property('rotamer_score', float32, read_only=True,
                doc='P-value for the current conformation of this rotamer. Read only.')
    ca_cb_bonds = cvec_property('rotamer_ca_cb_bond', cptr, astype=_bonds, read_only=True,
                doc='The "stem" bond of this rotamer. Read only.')

class Distance_Restraints(Collection):
    def __init__(self, c_pointers=None):
        super().__init__(c_pointers, Distance_Restraint, Distance_Restraints)

    enabled =cvec_property('distance_restraint_enabled', npy_bool,
            doc = 'Enable/disable these restraints or get their current states.')
    atoms = cvec_property('distance_restraint_atoms', cptr, 2, astype=_atoms_pair, read_only=True,
            doc = 'Returns a 2-tuple of :class:`Atoms` containing the restrained atoms. Read only.' )
    targets = cvec_property('distance_restraint_target', float64,
            doc = 'Target distances in Angstroms')
    spring_constants = cvec_property('distance_restraint_k', float64,
            doc = 'Restraint spring constants in kJ mol-1 Angstrom-2')
    distances = cvec_property('distance_restraint_distance', float64, read_only=True,
            doc = 'Current distances between restrained atoms in Angstroms. Read only.')
    pseudobonds = cvec_property('distance_restraint_pbond', cptr, astype=_pseudobonds, read_only=True,
            doc = 'Pseudobond visualisations of the restraints. Read only.')
