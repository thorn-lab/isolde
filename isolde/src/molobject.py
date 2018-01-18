
import os, sys, glob
import numpy
import ctypes
from chimerax.core.state import State
from chimerax.core.atomic import molc
from chimerax.core.atomic.molc import CFunctions, string, cptr, pyobject, \
    set_c_pointer, pointer, size_t
# object map lookups
from chimerax.core.atomic.molobject import _atoms, \
                _atom_pair, _atom_or_none, _bonds, _chain, _element, \
                _pseudobonds, _residue, _residues, _rings, _non_null_residues, \
                _residue_or_none, _residues_or_nones, _residues_or_nones, \
                _chains, _atomic_structure, _pseudobond_group, \
                _pseudobond_group_map

from numpy import uint8, int32, uint32, float64, float32, byte, bool as npy_bool

libdir = os.path.dirname(os.path.abspath(__file__))
libfile = glob.glob(os.path.join(libdir, 'molc.cpython*'))[0]

_c_functions = CFunctions(os.path.splitext(libfile)[0])
c_property = _c_functions.c_property
cvec_property = _c_functions.cvec_property
c_function = _c_functions.c_function
c_array_function = _c_functions.c_array_function



def _proper_dihedrals(p):
    from .molarray import Proper_Dihedrals
    return Proper_Dihedrals(p)
def _proper_dihedral_or_none(p):
    return Proper_Dihedral.c_ptr_to_py_inst(p) if p else None

class _Dihedral_Mgr:
    '''Base class. Do not instantiate directly.'''
    def __init__(self, model, c_pointer=None):
        cname = type(self).__name__.lower()
        if c_pointer is None:
            new_func = cname + '_new'
            c_pointer = c_function(new_func, ret=ctypes.c_void_p)()
        set_c_pointer(self, c_pointer)
        f = c_function('set_'+cname+'_py_instance', args=(ctypes.c_void_p, ctypes.py_object))
        f(self._c_pointer, self)
        self.atomic_model = model
        

    @property
    def cpp_pointer(self):
        '''Value that can be passed to C++ layer to be used as pointer (Python int)'''
        return self._c_pointer.value

    @property
    def deleted(self):
        '''Has the C++ side been deleted?'''
        return not hasattr(self, '_c_pointer')

class Proper_Dihedral_Mgr(_Dihedral_Mgr):
    
    def __init__(self, model, c_pointer=None):
        super().__init__(model, c_pointer=c_pointer)
    
    def add_dihedrals(self, dihedrals):
        f = c_function('proper_dihedral_mgr_add_dihedral', 
            args = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t),
            )
        f(self.cpp_pointer, dihedrals._c_pointers, len(dihedrals))
    
    def find_dihedrals(self):
        import json
        with open(os.path.join(libdir, 'dictionaries', 'named_dihedrals.json'), 'r') as f:
            dihedral_dict = json.load(f)
        amino_acid_resnames = [a.upper() for a in dihedral_dict['aminoacids']]
        r = self.atomic_model.residues
        aa_residues = r[numpy.in1d(r.names, amino_acid_resnames)]
        f = c_function('proper_dihedral_mgr_new_dihedral', args=(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)))
        for key, data in dihedral_dict['all_protein'].items():
            atom_names = numpy.array(data[0], string);
            externals = numpy.array(data[1], numpy.int32);
            k = ctypes.py_object()
            k.value = key
            print(aa_residues._c_pointers)
            f(self._c_pointer, aa_residues._c_pointers, len(aa_residues), ctypes.byref(k), pointer(atom_names), pointer(externals))
        return aa_residues    
        
    
    def get_dihedrals(self, residues, name):
        f = c_function('proper_dihedral_mgr_get_dihedrals', args=(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p), ret=ctypes.c_size_t)
        n = len(residues)
        names = numpy.empty(n, string)
        names[:] = name
        ptrs  = numpy.empty(n, cptr)
        num_found = f(self._c_pointer, residues._c_pointers, pointer(names), n, pointer(ptrs))
        print("Found {} dihedrals".format(num_found))
        return _proper_dihedrals(ptrs[0:num_found])
    
    @property
    def num_dihedrals(self):
        f = c_function('proper_dihedral_mgr_num_dihedrals', args=(ctypes.c_void_p,), ret=ctypes.c_size_t)
        return f(self._c_pointer)
    

class Proper_Dihedral(State):
    def __init__(self, c_pointer):
        set_c_pointer(self, c_pointer)
    
    @property
    def cpp_pointer(self):
        '''Value that can be passed to C++ layer to be used as pointer (Python int)'''
        return self._c_pointer.value

    @property
    def deleted(self):
        '''Has the C++ side been deleted?'''
        return not hasattr(self, '_c_pointer')
    
    def __str__(self):
        return self.name
    
    def reset_state(self):
        pass
    
    name = c_property('proper_dihedral_name', string, read_only = True, doc = 'Name of this dihedral. Read only.')
    angle = c_property('proper_dihedral_angle', float32, read_only=True, doc = 'Angle in radians. Read only.')

# tell the C++ layer about class objects whose Python objects can be instantiated directly
# from C++ with just a pointer, and put functions in those classes for getting the instance
# from the pointer (needed by Collections)
for class_obj in [Proper_Dihedral, ]:
    cname = class_obj.__name__.lower()
    func_name = 'set_' + cname + '_pyclass'
    f = c_function(func_name, args = (ctypes.py_object,))
    f(class_obj)
    
    func_name = cname + 'py_inst'
    class_obj.c_ptr_to_py_inst = lambda ptr, fname=func_name: c_function(fname, 
        args = (ctypes.c_void_p,), ret = ctypes.py_object)(ctypes.c_void_p(int(ptr)))
    func_name = cname + '_existing_py_inst'
    class_obj.c_ptr_to_existing_py_inst = lambda ptr, fname=func_name: c_function(fname,
        args = (ctypes.c_void_p,), ret = ctypes.py_object)(ctypes.c_void_p(int(ptr)))
    
Proper_Dihedral_Mgr.c_ptr_to_py_inst = lambda ptr: c_function('proper_dihedral_mgr_py_inst',
    args = (ctypes.c_void_p,), ret = ctypes.py_object)(ctypes.c_void_p(int(ptr)))
Proper_Dihedral_Mgr.c_ptr_to_existing_py_inst = lambda ptr: c_function("proper_dihedral_mgr_existing_py_inst",
    args = (ctypes.c_void_p,), ret = ctypes.py_object)(ctypes.c_void_p(int(ptr)))
