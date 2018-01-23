
#ifndef isolde_Dihedral
#define isolde_Dihedral

#include <vector>
#define _USE_MATH_DEFINES
#include <cmath>
#include <atomstruct/destruct.h>
#include <atomstruct/AtomicStructure.h>
#include <atomstruct/Atom.h>
#include <atomstruct/Bond.h>
#include <atomstruct/Coord.h>
#include <atomstruct/Residue.h>
#include <pyinstance/PythonInstance.declare.h>

#include "../geometry/geometry.h"

using namespace atomstruct;


namespace isolde 
{

template <class DType> class Dihedral_Mgr;

//! Define a dihedral by four atoms.
/*!  
 * Atoms must be provided in order, such that the central pair defines
 * the dihedral axis. For the generic base class, the atoms needn't be
 * bonded to each other, but the same atom must not appear more than
 * once.
 * 
 * MUST BE ALLOCATED ON THE HEAP (i.e. via Dihedral* d = new Dihedral(...))
 * to work with ChimeraX's automatic clean-up system.
 * If you want the dihedral to be automatically deleted when any of its
 * atoms are deleted (HIGHLY recommended!) then it should be added to a
 * suitable Dihedral_Mgr after creation. 
 */ 
class Dihedral: public pyinstance::PythonInstance<Dihedral>
{

public:
    typedef Atom* Atoms[4];
    typedef Coord Coords[4];
    typedef Bond* Bonds[3];
    
private:
    
    
    const double NAN_NOT_SET = std::nan("Not set");
    const double TWO_PI = 2.0*M_PI;

    Atoms _atoms;
    Coords _coords;
    Bonds _bonds;
    const char* err_msg_dup_atom() const
        {return "All atoms must be unique!";}
    const char* err_msg_multi_struct() const
        {return "All atoms must be in the same structure!";}
    const char* err_msg_no_residue() const
        {return "This dihedral has not been attached to a residue!";}
    std::string _name=""; // Name of the dihedral (e.g. phi, psi, omega, ...)
    // Most dihedrals belong to specific residues by convention, but 
    // we want to leave this optional for this base case.
    Residue* _residue = nullptr; 
    double _target_angle = NAN_NOT_SET;
    double _spring_constant = 0;
    
public:
    Dihedral() {} // null constructor
    Dihedral(Atom* a1, Atom* a2, Atom* a3, Atom* a4);
    Dihedral(Atom* a1, Atom* a2, Atom* a3, Atom* a4, Residue* owner, std::string name);
    ~Dihedral() { auto du = DestructionUser(this); }
    const Atoms& atoms() const {return _atoms;}
    Structure* structure() const {return atoms()[0]->structure();}
    double angle() const; // return the current dihedral angle in radians
    const std::string& name() const { return _name; }
    void set_name(const std::string& name) { _name = name; }
    Residue* residue() const;
    void set_residue(Residue* residue) { _residue = residue; }
    virtual const Bonds& bonds() const { 
        throw std::invalid_argument("Base class Dihedral does not support bonds!");
    }
    virtual Bond* axial_bond() const {
        throw std::invalid_argument("Axial bond is only defined for a Proper_Dihedral!");
    }    
    
    const Coords &coords() const;
    const double &target() const {return _target_angle;} // getter
    //! Set the target angle, automatically wrapping to (-pi,pi)
    void set_target(const double &val) { _target_angle = remainder(val, TWO_PI); } // setter
    const double &spring_constant() const { return _spring_constant; } // getter
    void set_spring_constant (const double &val) {_spring_constant = val; } // setter
    
    

}; // class Dihedral


//! Define a proper dihedral
/*!
 * Atoms must be provided in order and must all be bonded in strict 
 * order atom1--atom2--atom3--atom4. 
 */ 
class Proper_Dihedral: public Dihedral 
{

public:
    typedef Bond* Bonds[3];
    Proper_Dihedral() {} // null constructor
    Proper_Dihedral(Atom* a1, Atom* a2, Atom* a3, Atom* a4, Residue* owner, std::string name);
    const Bonds& bonds() const { return _bonds; }
    Bond* axial_bond() const { return bonds()[1]; }

private:
    Bonds _bonds;
    const char* err_msg_not_bonded() const
        {return "Atoms must be bonded a1--a2--a3--a4";}

}; // class Proper_Dihedral

} // namespace isolde

#endif // isolde_Dihedral
