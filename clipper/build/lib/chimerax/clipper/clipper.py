from .lib import clipper_python_core as clipper_core
import numpy

'''
 To make things a little more user-friendly than the raw SWIG wrapper,
 all the major Clipper classes are sub-classed here with some extra
 documentation, useful Python methods, @property decorators, etc.
 This requires overcoming one small problem: when Clipper itself creates 
 and returns objects, they're returned as the base class rather than
 the sub-class. So, we have to over-ride the __new__ method for each
 base class to make sure they're instead instantiated as the derived
 class with all the bells and whistles. Therefore, each class definition 
 is preceded by a function (e.g. __newAtom__) that makes this mapping.
'''


#### Message logging
_clipper_messages = clipper_core.ClipperMessageStream()

def log_clipper(func):
    '''
    Acts as a decorator to direct Clipper messages to the Python console.
    Any messages coming from Clipper are accumulated in _clipper_messages.
    For any core Clipper function which has the potential to generate a
    warning message, simply add the @log_clipper decorator to the Python
    method. Override this function if you want the messages to go somewhere
    else (e.g. to a log file).
    '''
    def func_wrapper(*args, **kwargs):
        _clipper_messages.clear()
        func(*args, **kwargs)
        message_string = _clipper_messages.read_and_clear()
        if message_string:
            print("CLIPPER WARNING:")
            print(message_string)
    return func_wrapper
    

def __newAtom__(cls, *args, **kwargs):
    if cls == clipper_core.clipper.Atom:
        return object.__new__(Atom)
    return object.__new__(cls)        
clipper_core.Atom.__new__ = staticmethod(__newAtom__)

class Atom(clipper_core.Atom):
    '''
    A minimalist atom object containing only the properties required for
    electron density calculations
    '''
    # The complete list of scatterers found in clipper/core/atomsf.cpp.
    # Clipper itself doesn't check incoming atom names for legality, but
    # it's easy to do so here in Python. Used by setter methods in Atom and 
    # Atom_list objects.
    ATOM_NAMES = set(
         ['H',  'He', 'Li', 'Be', 'B',  'C',  'N',  'O',  'F',
          'Ne', 'Na', 'Mg', 'Al', 'Si', 'P',  'S',  'Cl', 'Ar',
          'K',  'Ca', 'Sc', 'Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co',
          'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr',
          'Rb', 'Sr', 'Y',  'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh',
          'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I',  'Xe',
          'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu',
          'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf',
          'Ta', 'W',  'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl',
          'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
          'Pa', 'U',  'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 
          'H1-',  'Li1+', 'Be2+', 'Cval', 'O1-',  'O2-',  'F1-',
          'Na1+', 'Mg2+', 'Al3+', 'Siva', 'Si4+', 'Cl1-', 'K1+',
          'Ca2+', 'Sc3+', 'Ti2+', 'Ti3+', 'Ti4+', 'V2+',  'V3+',
          'V5+',  'Cr2+', 'Cr3+', 'Mn2+', 'Mn3+', 'Mn4+', 'Fe2+',
          'Fe3+', 'Co2+', 'Co3+', 'Ni2+', 'Ni3+', 'Cu1+', 'Cu2+',
          'Zn2+', 'Ga3+', 'Ge4+', 'Br1-', 'Rb1+', 'Sr2+', 'Y3+',
          'Zr4+', 'Nb3+', 'Nb5+', 'Mo3+', 'Mo5+', 'Mo6+', 'Ru3+',
          'Ru4+', 'Rh3+', 'Rh4+', 'Pd2+', 'Pd4+', 'Ag1+', 'Ag2+',
          'Cd2+', 'In3+', 'Sn2+', 'Sn4+', 'Sb3+', 'Sb5+', 'I1-',
          'Cs1+', 'Ba2+', 'La3+', 'Ce3+', 'Ce4+', 'Pr3+', 'Pr4+',
          'Nd3+', 'Pm3+', 'Sm3+', 'Eu2+', 'Eu3+', 'Gd3+', 'Tb3+',
          'Dy3+', 'Ho3+', 'Er3+', 'Tm3+', 'Yb2+', 'Yb3+', 'Lu3+',
          'Hf4+', 'Ta5+', 'W6+',  'Os4+', 'Ir3+', 'Ir4+', 'Pt2+',
          'Pt4+', 'Au1+', 'Au3+', 'Hg1+', 'Hg2+', 'Tl1+', 'Tl3+',
          'Pb2+', 'Pb4+', 'Bi3+', 'Bi5+', 'Ra2+', 'Ac3+', 'Th4+',
          'U3+',  'U4+',  'U6+',  'Np3+', 'Np4+', 'Np6+', 'Pu3+',
          'Pu4+', 'Pu6+'])  
                        
    def __init__(self, element, coord, occ, u_iso, u_aniso):
        '''
        __init__(self, element, coord, occ, u_iso, u_aniso) -> Atom
        
        Create a new Clipper Atom with the given properties
        Args:
            element (string): 
                The standard abbreviated element (or elemental ion) 
                name. All valid names are listed in Atom.ATOM_NAMES.
            coord ([float*3] or Clipper.Coord_orth object): 
                (x,y,z) coordinates of the atom in Angstroms. 
            occ (float):
                The fractional occupancy of the atom
            u_iso (float):
                Isotropic B-factor
            u_aniso ([float * 6]):
                Anisotropic B-factor matrix as a 6-member array:
                [u00, u11, u22, u01, u02, u12].
        '''
        clipper_core.Atom.__init__(self)
        self.element = element
        self.coord = coord
        self.occupancy = occ
        self.u_iso = u_iso
        self.u_aniso = u_aniso
    
    
    @property
    def element(self):
        '''
        The standard abbreviated element (or elemental ion) name. All valid
        names are listed in Atom.ATOM_NAMES.
        '''
        return super(Atom, self).element()
    
    @element.setter
    def element(self, element_name):
        # Check common atom names first to improve performance
        if element_name not in ('H', 'C', 'N', 'O', 'S'):
            if element_name not in self.ATOM_NAMES:
                raise TypeError('Unrecognised element!')
        super(Atom, self).set_element(element_name)
    
    @property
    def coord(self):
        '''
        (x,y,z) coordinates of the atom in Angstroms. Can be set from
        a Python list, numpy array, or a Clipper Coord_orth object.
        '''
        return self.coord_orth.xyz
    
    @coord.setter
    def coord(self, coord):
        if isinstance(coord, Coord_orth):
            self.set_coord_orth(coord)
        else:
            self.set_coord_orth(clipper_core.Coord_orth(*coord))

    @property
    def coord_orth(self):
        '''
        Clipper Coord_orth object associated with this atom. Will return
        a coord_orth object, but can be set with a simple list of 3 
        (x,y,z) coordinates.
        '''
        return super(Atom, self).coord_orth()
    
    @coord_orth.setter
    def coord_orth(self, coord):
        self.coord = coord
        
    @property
    def occupancy(self):
        '''Fractional occupancy of this atom'''
        return super(Atom, self).occupancy()
    
    @occupancy.setter
    def occupancy(self, occ):
        self.set_occupancy(occ)
    
    @property
    def u_iso(self):
        '''Isotropic b-factor in square Angstroms.'''
        return super(Atom, self).u_iso()
    
    @u_iso.setter
    def u_iso(self, u_iso):
        self.set_u_iso(u_iso)
    
    @property
    def b_factor(self):
        '''Isotropic b-factor in square Angstroms.'''
        return self.u_iso
    
    @b_factor.setter
    def b_factor(self, b_factor):
        self.u_iso = b_factor
    
    @property
    def u_aniso_orth(self):
        '''
        Anisotropic B-factor matrix as a 6-member array:
        [u00, u11, u22, u01, u02, u12].
        For purely isotropic values, set this to None
        '''
        return super(Atom, self).u_aniso_orth().get_vals()
    
    @property
    def _u_aniso_orth(self):
        '''Get the Clipper::U_aniso_orth object'''
        return super(Atom, self).u_aniso_orth()
    
    @u_aniso_orth.setter
    def u_aniso_orth(self, u_aniso):
        if u_aniso is None:
            from math import nan
            self.set_u_aniso_orth(clipper_core.U_aniso_orth(*([nan]*6)))
        else:
            self.set_u_aniso_orth(clipper_core.U_aniso_orth(*u_aniso))
    
    @property
    def is_null(self):
        '''Check to see if this atom has been initialised'''
        return super(Atom, self).is_null()


def __newAtom_list__(cls, *args, **kwargs):
    if cls == clipper_core.Atom_list:
        return object.__new__(Atom_list)
    return object.__new__(cls)        
clipper_core.Atom_list.__new__ = staticmethod(__newAtom_list__)

class Atom_list(clipper_core.Atom_list):
    '''
    Generate a Clipper Atom_list object from lists or numpy arrays of data.
    '''
    def __init__(self, elements, coords, occupancies, u_isos, u_anisos):
        '''
        __init__(self, elements, coords, occupancies, u_isos, u_anisos)
            -> Atom_list
            
        Arguments:
            elements:    standard elemental abbreviations (e.g. "C", "Na1+" etc.)
                         See clipper.Atom.ATOM_NAMES for a full list of legal atom names
            coords:      (x,y,z) coordinates in Angstroms as an N x 3 array
            occupancies: fractional occupancies (one value per atom)
            u_isos:      isotropic B-factors (one value per atom)
            u_anisos:    the six unique entries in the anisotropic B-factor matrix
                         (u00, u11, u22, u01, u02, u12) as an N x 3 array
        '''
        clipper_core.Atom_list.__init__(self)
        self.extend_by(len(elements))
        self.elements = elements
        self.coord_orth = coords
        self.occupancies = occupancies
        self.u_isos = u_isos
        self.u_anisos = u_anisos
    
    @property
    def elements(self):
        '''Ordered list of all element names'''
        return super(Atom_list, self)._get_elements()
    
    @elements.setter
    def elements(self, elements):
        # Quick check to see if all element names are legal
        if not set(elements).issubset(Atom.ATOM_NAMES):
            bad_atoms = []
            for el in set(elements):
                if el not in Atom.ATOM_NAMES:
                    bad_atoms.append(el)
            bad_atoms = set(bad_atoms)
            errstring = '''
                The following atom names are not recognised by Clipper:
                {}
                '''.format(bad_atoms)
            raise TypeError(errstring)
        super(Atom_list, self)._set_elements(elements)
            
    def _set_coord_orth(self, coords):
        n = len(self)
        array_in = numpy.empty((n, 3), numpy.double)
        array_in[:] = coords
        super(Atom_list, self)._set_coord_orth(array_in)
    
    def _get_coord_orth(self):
        '''Orthographic (x,y,z) coordinates of all atoms'''
        n = len(self)
        coords = numpy.empty((n,3,), numpy.double)
        super(Atom_list, self)._get_coord_orth(coords)
        return coords
    
    coord_orth = property(_get_coord_orth, _set_coord_orth)
    
    def _set_occupancies(self, occ):
        n = len(self)
        array_in = numpy.empty(n, numpy.double)
        array_in[:] = occ
        super(Atom_list, self)._set_occupancies(array_in)
        
    def _get_occupancies(self):
        '''Fractional occupancies of all atoms'''
        n = len(self)
        occ = numpy.empty(n, numpy.double)
        super(Atom_list, self)._get_occupancies(occ)
        return occ
    
    occupancies = property(_get_occupancies, _set_occupancies)
    
    def _set_u_isos(self, u_isos):
        n = len(self)
        array_in = numpy.empty(n, numpy.double)
        array_in[:] = u_isos
        super(Atom_list, self)._set_u_isos(array_in)
    
    def _get_u_isos(self):
        '''Isotropic B-factors of all atoms'''
        n = len(self)
        uiso = numpy.empty(n, numpy.double)
        super(Atom_list, self)._get_u_isos(uiso)
        return uiso
    
    u_isos = property(_get_u_isos, _set_u_isos)
    
    def _set_u_anisos(self, u_anisos):
        n = len(self)
        array_in = numpy.empty((n,6), numpy.double)
        array_in[:] = u_anisos
        super(Atom_list, self)._set_u_anisos(array_in)
    
    def _get_u_anisos(self):
        '''
        Anisotropic B-factor matrices for all atoms as an nx6 array, in the
        format: n*[u00, u11, u22, u01, u02, u12]. For purely isotropic
        atoms, set all elements in their row to math.nan or numpy.nan.
        '''
        n = len(self)
        uaniso = numpy.empty((n,6), numpy.double)
        super(Atom_list, self)._get_u_anisos(uaniso)
        return uaniso
    
    u_anisos = property(_get_u_anisos, _set_u_anisos)

def __newCoord_orth__(cls, *args, **kwargs):
    if cls == clipper_core.Coord_orth:
        return object.__new__(Coord_orth)
    return object.__new__(cls)        
clipper_core.Coord_orth.__new__ = staticmethod(__newCoord_orth__)

class Coord_orth(clipper_core.Coord_orth):
    '''Coordinates in orthographic (x,y,z) space.'''
    def __init__(self, xyz):
        '''
        __init__(self, xyz) -> Coord_orth
        
        Args:
            xyz ([float * 3]): (x, z, z) coordinates in Angstroms
        '''
        if isinstance(xyz, numpy.ndarray):
            # Because SWIG does not correctly typemap numpy.float32
            xyz = xyz.astype(float)
        clipper_core.Coord_orth.__init__(self, *xyz)
    '''
    @property
    def x(self):
        return super(Coord_orth, self).x()
    
    @property
    def y(self):
        return super(Coord_orth, self).y()
        
    @property
    def z(self):
        return super(Coord_orth, self).z()

    @property
    def xyz(self):
        return super(Coord_orth, self).xyz()
    '''
    @property
    def xyz(self):
        return super(Coord_orth, self)._get_xyz()
    
    def __add__(self, other):
        if isinstance(other, Coord_orth):
            return super(Coord_orth, self).__add__(other)
        return self + Coord_orth(other)
    
    
def __newCoord_grid__(cls, *args, **kwargs):
    if cls == clipper_core.Coord_grid:
        return object.__new__(Coord_grid)
    return object.__new__(cls)        
clipper_core.Coord_grid.__new__ = staticmethod(__newCoord_grid__)
        
class Coord_grid(clipper_core.Coord_grid):
    '''Integer grid coordinates in crystal space.'''
    def __init__(self, uvw):
        '''
        __init__(self, uvw) -> Coord_grid
        
        Args:
            uvw ([int * 3]): (u, v, w) grid coordinates
        '''
        # Not sure why, but wrapped C functions fail when fed expansions
        # of numpy int32 arrays, so we need to convert these to lists first
        if isinstance(uvw, numpy.ndarray):
            uvw = uvw.tolist()
        clipper_core.Coord_grid.__init__(self, *uvw)
    
    '''
    @property
    def u(self):
        return super(Coord_grid, self).u()
    
    @property
    def v(self):
        return super(Coord_grid, self).v()
    
    @property
    def w(self):
        return super(Coord_grid, self).w()
    
    @property
    def uvw(self):
        return super(Coord_grid, self).uvw()
    '''
    
    @property
    def uvw(self):
        return super(Coord_grid, self)._get_uvw()

    def __add__(self, other):
        if isinstance(other, Coord_grid):
            return super(Coord_grid, self).__add__(other)
        return self + Coord_grid(other)
    

def __newCoord_map__(cls, *args, **kwargs):
    if cls == clipper_core.Coord_map:
        return object.__new__(Coord_map)
    return object.__new__(cls)        
clipper_core.Coord_map.__new__ = staticmethod(__newCoord_map__)
    
class Coord_map(clipper_core.Coord_map):
    '''Like Coord_grid, but allowing non-integer values.'''
    def __init__(self, uvw):
        '''
        __init__(self, uvw) -> Coord_map
        
        Args:
            uvw ([float * 3]): (u, v, w) grid coordinates
        '''
        if isinstance(uvw, numpy.ndarray):
            # Because SWIG does not correctly typemap numpy.float32
            uvw = uvw.astype(float)
        clipper_core.Coord_map.__init__(self, *uvw)
    
    @property
    def u(self):
        return super(Coord_map, self).u()
    
    @property
    def v(self):
        return super(Coord_map, self).v()
    
    @property
    def w(self):
        return super(Coord_map, self).w()
    
    @property
    def uvw(self):
        return super(Coord_map, self).uvw()

def __newCoord_frac__(cls, *args, **kwargs):
    if cls == clipper_core.Coord_frac:
        return object.__new__(Coord_frac)
    return object.__new__(cls)        
clipper_core.Coord_frac.__new__ = staticmethod(__newCoord_frac__)

class Coord_frac(clipper_core.Coord_frac):
    '''
    Fractional coordinates along unit cell axes (a,b,c), scaled to the 
    range 0..1 on each axis.
    '''
    def __init__(self, uvw):
        '''
        __init__(self, uvw) -> Coord_frac
        
        Args:
            uvw ([float * 3]): (u, v, w) fractional coordinates
        '''
        if isinstance(uvw, numpy.ndarray):
            # Because SWIG does not correctly typemap numpy.float32
            uvw = uvw.astype(float)
        clipper_core.Coord_frac.__init__(self, *uvw)
    '''
    @property
    def u(self):
        return super(Coord_frac, self).u()
    
    @property
    def v(self):
        return super(Coord_frac, self).v()
    
    @property
    def w(self):
        return super(Coord_frac, self).w()
    
    @property
    def uvw(self):
        return super(Coord_frac, self).uvw()
    '''
    
    @property
    def uvw(self):
        return super(Coord_frac, self)._get_uvw()
    
    def __add__(self, other):
        if isinstance(other, Coord_frac):
            return super(Coord_frac, self).__add__(other)
        return self + Coord_frac(other)

def __newCCP4MTZfile__(cls, *args, **kwargs):
    if cls == clipper_core.CCP4MTZfile:
        return object.__new__(CCP4MTZfile)
    return object.__new__(cls)        
clipper_core.CCP4MTZfile.__new__ = staticmethod(__newCCP4MTZfile__)

class CCP4MTZfile(clipper_core.CCP4MTZfile):
    '''
    MTZ import/export parent class for clipper objects.
    
    This is the import/export class which can be linked to an mtz
    file and used to transfer data into or out of a Clipper data structure.
    
    Note that to access the MTZ file efficiently, data reads and writes
    are deferred until the file is closed.

    MTZ column specification:

    Note that the specification of the MTZ column names is quite
    versatile. The MTZ crystal and dataset must be specified, although
    the wildcard '*' may replace a complete name. Several MTZ columns
    will correspond to a single datalist. This may be handled in two
    ways:
    
    - A simple name. The corresponding MTZ columns will be named
    after the datalist name, a dot, the datalist type, a dot, and a
    type name for the indivudal column,
    i.e. /crystal/dataset/datalist.listtype.coltype This is the
    default Clipper naming convention for MTZ data.
    
    - A comma separated list of MTZ column names enclosed in square
    brackets.  This allows MTZ data from legacy applications to be
    accessed.
    
    Thus, for example, an MTZPATH of
    
        native/CuKa/fsigfdata
    
    expands to MTZ column names of
    
        fsigfdata.F_sigF.F
        fsigfdata.F_sigF.sigF
    
    with a crystal called "native" and a dataset called "CuKa". An MTZPATH of
    
        native/CuKa/[FP,SIGFP]
    
    expands to MTZ column names of
    
        FP
        SIGFP
    
    with a crystal called "native" and a dataset called "CuKa".

   Import/export types:

    For an HKL_data object to be imported or exported, an MTZ_iotype
    for that datatype must exist in the MTZ_iotypes_registry. MTZ_iotypes 
    are defined for all the built-in datatypes. If you need to store a 
    user defined type in an MTZ file, then register that type with the 
    MTZ_iotypes_registry. 

    EXAMPLE: Loading essential crystal information and 
    2Fo-Fc amplitudes/phases from an mtz file
    
    fphidata =  HKL_data_F_phi_double()    
    myhkl = hklinfo()
    mtzin = CCP4MTZfile()
    mtzin.open_read(filename)
    mtzin.import_hkl_info(myhkl)
    mtzin.import_hkl_data(fphidata, '/crystal/dataset/[2FOFCWT, PH2FOFCWT]')
    mtzin.close_read()
    '''
    
    def __init__(self):
        '''
        __init__(self) -> CCP4MTZfile
        
        Create an empty CCP4MTZfile object. Call open_read(filename) to
        begin reading a MTZ file.
        '''
        clipper_core.CCP4MTZfile.__init__(self)
    
    @log_clipper
    def open_read(self, filename):
        '''Open an MTZ file for reading'''
        return super(CCP4MTZfile, self).open_read(filename)
        
    @log_clipper
    def import_hkl_data(self, cdata, mtzpath):
        '''
        Mark a set of data for import. NOTE: the data will not actually
        be imported until the close_read() method has been called.
        
        Args:
            cdata:   a Clipper.HKL_data_... object matched to the data types
                     in the mtzpath (e.g. HKL_data_F_phi for amplitudes and
                     phases).
            mtzpath: a string giving the path to the target columns within
                     the MTZ file. Available columns can be listed using
                     column_labels(). To import data spanning multiple
                     columns, use e.g.
                        "/crystal/dataset/[2FOFCWT, PH2FOFCWT]"
        '''
        return super(CCP4MTZfile, self).import_hkl_data(cdata, mtzpath)

    @property
    def ccp4_spacegroup_number(self):
        return super(CCP4MTZfile, self).ccp4_spacegroup_number()
    
    @property
    def cell(self):
        '''Object describing the unit cell dimensions'''
        return super(CCP4MTZfile, self).cell()
    
    @property
    def column_labels(self):
        '''List of available columns in the MTZ file'''
        return super(CCP4MTZfile, self).column_labels()
    
    @property
    def column_paths(self):
        '''List of available columns in the MTZ file'''
        return super(CCP4MTZfile, self).column_paths()
        
    @property
    def high_res_limit(self):
        return super(CCP4MTZfile, self).high_res_limit()
    
    @property
    def history(self):
        return super(CCP4MTZfile, self).history()
            
    @property
    def hkl_sampling(self):
        return super(CCP4MTZfile, self).hkl_sampling()

    @property
    def low_res_limit(self):
        return super(CCP4MTZfile, self).low_res_limit()

    @property
    def resolution(self):
        return super(CCP4MTZfile, self).resolution()
    
    @property
    def sort_order(self):
        return super(CCP4MTZfile, self).sort_order()

    @property
    def spacegroup(self):
        '''Object defining the symmetry operations for this spacegroup'''
        return super(CCP4MTZfile, self).spacegroup()
    
    @property
    def spacegroup_confidence(self):
        return super(CCP4MTZfile, self).spacegroup_confidence()
    
    @spacegroup_confidence.setter
    def spacegroup_confidence(self, confidence):
        super(CCP4MTZfile, self).set_spacegroup_confidence(confidence)
        
    @property
    def title(self):
        return super(CCP4MTZfile, self).title()
    
    @title.setter
    def title(self, title):
        super(CCP4MTZfile, self).set_title(title)
    
    

def __newCIFfile__(cls, *args, **kwargs):
    if cls == clipper_core.CIFfile:
        return object.__new__(CIFfile)
    return object.__new__(cls)        
clipper_core.CIFfile.__new__ = staticmethod(__newCIFfile__)
        
class CIFfile(clipper_core.CIFfile):
    '''
    CIF import/export parent class for clipper objects.
      
    This is the import class which can be linked to an cif data
    file and be used to transfer data into a Clipper
    data structure. 
    It is currently a read-only class.
    '''
    
    def __init__(self):
        '''
        __init__(self) -> CIFfile
        
        Create an empty CIFfile object. Call open_read to begin reading
        a .cif structure factor file.
        '''
        clipper_core.CIFfile.__init__(self)
    
    @log_clipper
    def open_read(self, filename):
        return super(CIFfile, self).open_read(filename)
    
    @log_clipper
    def resolution(self, cell):
        return super(CIFfile, self).resolution(cell)



def __newHKL_info__(cls, *args, **kwargs):
    if cls == clipper_core.HKL_info:
        return object.__new__(HKL_info)
    return object.__new__(cls)        
clipper_core.HKL_info.__new__ = staticmethod(__newHKL_info__)

class HKL_info(clipper_core.HKL_info):
    def __init__(self):
        '''
        __init__(self) -> HKL_info
        
        Create an empty HKL_info object to store the vital statistics
        (h,k,l coordinates, cell parameters, spacegroup etc.) of a set 
        of crystal data. It can be filled by passing it as an argument
        to (CCP4MTZfile or CIFfile).import_hkl_info() after loading a
        structure factor file.
        '''
        clipper_core.HKL_info.__init__(self)
    
    @property
    def cell(self):
        return super(HKL_info, self).cell()
    
    @property
    def spacegroup(self):
        return super(HKL_info, self).spacegroup()
        
    @property
    def resolution(self):
        return super(HKL_info, self).resolution()
    
        
def __newHKL_data_Flag__(cls, *args, **kwargs):
    if cls == clipper_core.HKL_data_Flag:
        return object.__new__(HKL_data_Flag)
    return object.__new__(cls)        
clipper_core.HKL_data_Flag.__new__ = staticmethod(__newHKL_data_Flag__)

class HKL_data_Flag(clipper_core.HKL_data_Flag):
    def __init__(self):
        '''
        __init__(self) -> HKL_data_Flag
        
        Create an empty object to store an array of integer flags 
        (e.g. for holding of R-free flags). Fill it by passing it to
        (CCP4MTZfile or CIFfile).import_hkl_data together with the
        address of a suitable array.
        '''
        clipper_core.HKL_data_Flag.__init__(self)

def __newHKL_data_F_sigF__(cls, *args, **kwargs):
    if cls == clipper_core.HKL_data_F_sigF_double:
        return object.__new__(HKL_data_F_sigF)
    return object.__new__(cls)        
clipper_core.HKL_data_F_sigF_double.__new__ = staticmethod(__newHKL_data_F_sigF__)

class HKL_data_F_sigF (clipper_core.HKL_data_F_sigF_double):
    def __init__(self):
        '''
        __init__(self) -> HKL_data_F_sigF
        
        Create an empty object to store an array of amplitudes and
        their associated sigmas. Fill it by passing it to
        (CCP4MTZfile or CIFfile).import_hkl_data together with the
        addresses of a suitable pair of arrays.
        '''
        clipper_core.HKL_data_F_sigF_double.__init__(self)


def __newHKL_data_F_phi__(cls, *args, **kwargs):
    if cls == clipper_core.HKL_data_F_phi_double:
        return object.__new__(HKL_data_F_phi)
    return object.__new__(cls)        
clipper_core.HKL_data_F_phi_double.__new__ = staticmethod(__newHKL_data_F_phi__)

class HKL_data_F_phi (clipper_core.HKL_data_F_phi_double):
    def __init__(self):
        '''
        __init__(self) -> HKL_data_F_phi
        
        Create an empty object to store an array of amplitudes and their
        associated phases (observed or calculated). Fill it by passing it 
        to (CCP4MTZfile or CIFfile).import_hkl_data together with the
        addresses of a suitable pair of arrays.
        '''
        clipper_core.HKL_data_F_phi_double.__init__(self)


def __newHKL_data_I_sigI__(cls, *args, **kwargs):
    if cls == clipper_core.HKL_data_I_sigI_double:
        return object.__new__(HKL_data_I_sigI)
    return object.__new__(cls)        
clipper_core.HKL_data_I_sigI_double.__new__ = staticmethod(__newHKL_data_F_phi__)

class HKL_data_I_sigI(clipper_core.HKL_data_I_sigI_double):
    def __init__(self):
        '''
        __init__(self) -> HKL_data_I_sigI
        
        Create an empty object to store an array of intensities and
        their associated sigmas. Fill it by passing it to
        (CCP4MTZfile or CIFfile).import_hkl_data together with the
        addresses of a suitable pair of arrays.
        '''
        clipper_core.HKL_data_I_sigI_double.__init__(self)


def __newGrid_sampling__(cls, *args, **kwargs):
    if cls == clipper_core.Grid_sampling:
        return object.__new__(Grid_sampling)
    return object.__new__(cls)        
clipper_core.Grid_sampling.__new__ = staticmethod(__newGrid_sampling__)

class Grid_sampling(clipper_core.Grid_sampling):
    '''
    Object defining the grid used to sample points in a 3D map.
    '''
    def __init__(self, spacegroup, cell, resolution, rate = 1.5):
        '''
        __init__(self, spacegroup, cell, resolution, rate = 1.5) -> Grid_sampling
        
        Args:
            spacegroup (clipper.Spacegroup)
            cell (clipper.Cell)
            resolution (clipper.Resolution)
            rate: the over-sampling rate defining the spacing of grid
                  points. Leave this as the default unless you know what
                  you're doing.
        
        The first three arguments can be readily obtained from an HKL_info
        object: HKL_info.spacegroup, HKL_info.cell, HKL_info.resolution.
            
        '''
        clipper_core.Grid_sampling.__init__(self, spacegroup, cell, resolution, rate)
    
    @property
    def dim(self):
        return super(Grid_sampling, self).dim()

def __newCell__(cls, *args, **kwargs):
    if cls == clipper_core.Cell:
        return object.__new__(Cell)
    return object.__new__(cls)        
clipper_core.Cell.__new__ = staticmethod(__newCell__)

class Cell(clipper_core.Cell):
    '''
    Define a crystallographic unit cell using the lengths of the three
    sides a, b, c (in Angstroms) and the three angles alpha, beta, gamma
    (in degrees). 
    '''
    def __init__(self, abc, angles):
        '''
        __init__(self, abc, angles) -> Cell
        
        Args:
            abc ([float*3]): cell dimensions in Angstroms
            angles ([float*3]): alpha, beta and gamma angles in degrees
        '''
        cell_descr = clipper_core.Cell_descr(*abc, *angles)
        clipper_core.Cell.__init__(self, cell_descr)
    
    @property
    def dim(self):
        '''Returns the (a,b,c) lengths of the cell axes in Angstroms'''
        return super(Cell, self).dim()
    
    @property
    def angles(self):
        '''Returns the cell angles (alpha, beta, gamma) in radians'''
        return super(Cell, self).angles()
    
    @property
    def angles_deg(self):
        '''Returns the cell angles (alpha, beta, gamma) in degrees'''
        return super(Cell, self).angles_deg()
    
    @property
    def recip_dim(self):
        '''Returns the reciprocal cell lengths (a*, b*, c*) in inverse Angstroms'''
        return super(Cell, self).recip_dim()
    
    @property    
    def recip_angles(self):
        '''Returns the reciprocal cell angles (alpha*, beta*, gamma*) in radians'''
        return super(Cell, self).recip_angles()
    
    @property
    def recip_angles_deg(self):
        '''Returns the reciprocal cell angles (alpha*, beta*, gamma*) in degrees'''
        return super(Cell, self).recip_angles_deg()


def __newXmap_double__(cls, *args, **kwargs):
    if cls == clipper_core.Xmap_double:
        return object.__new__(Xmap)
    return object.__new__(cls)        
clipper_core.Xmap_double.__new__ = staticmethod(__newXmap_double__)
    
class Xmap(clipper_core.Xmap_double):
    '''
    A Clipper crystallographic map generated from reciprocal space data.
    '''
    def __init__(self, spacegroup, cell, grid_sam, name = None):
        '''
        __init__(self, spacegroup, cell, grid_sam) -> Xmap
        
        Generate an empty map container. This can be filled with data
        using the fft_from(fphi) method where fphi is a clipper.F_phi
        object.
        
        Args:
            spacegroup (clipper.Spacegroup)
            cell (clipper.Cell)
            grid_sam (clipper.Grid_sampling)
            name (string): 
                Optionally, you can give the map a unique name for later
                identification
        '''
        clipper_core.Xmap_double.__init__(self, spacegroup, cell, grid_sam)
        
        # Some extra useful variables that aren't directly available from
        # the Clipper API
        self.name = name
        
        # Get the (nu, nv, nw) grid sampling as a numpy array
        self.grid_samples = self.grid.dim
        
        # Set this flag to True if you want this to be treated as a difference
        # map (i.e. visualisation at +/- 3 sigma, different handling in
        # simulations).
        self.is_difference_map = False
        
        ###
        # Basic stats. Can only be set after the map has been filled with an
        # FFT. Returned as a tuple in the below order by self.stats()
        ###
        self._max = None
        self._min = None
        self._mean = None
        self._sigma = None
        self._skewness = None
        self._kurtosis = None
       
    def recalculate_stats(self):
        '''
        Force recalculation of map statistics (max, min, mean, sigma, 
        skewness and kurtosis).
        '''
        self._min, self._max, self._mean, \
            self._sigma, self._skewness, self._kurtosis = self.stats()  
    
    @property
    def cell(self):
        return super(Xmap, self).cell()
    
    @property
    def grid(self):
        return self.grid_sampling()
    
    @property
    def spacegroup(self):
        return super(Xmap, self).spacegroup()
    
    @property
    def max(self):
        if self._max is None:
            self.recalculate_stats()
        return self._max

    @property
    def min(self):
        if self._min is None:
            self.recalculate_stats()
        return self._min

    @property
    def mean(self):
        if self._mean is None:
            self.recalculate_stats()
        return self._mean
    
    @property
    def sigma(self):
        if self._sigma is None:
            self.recalculate_stats()
        return self._sigma
    
    @property
    def skewness(self):
        if self._skewness is None:
            self.recalculate_stats()
        return self._skewness

    @property
    def kurtosis(self):
        if self._max is None:
            self.recalculate_stats()
        return self._kurtosis
    
                
@log_clipper
def test_log_warn():
    clipper_core.warn_test()

@log_clipper
def test_log_except():
    clipper_core.except_test()

@log_clipper    
def test_log_no_warn():
    pass
                
            
            
        
        
         
                
        
        
    
    
                



