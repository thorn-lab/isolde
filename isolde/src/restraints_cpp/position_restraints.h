#ifndef ISOLDE_POSITION_RESTRAINTS
#define ISOLDE_POSITION_RESTRAINTS

#include "../constants.h"
#include "../geometry/geometry.h"
#include "changetracker.h"
#include <atomstruct/destruct.h>
#include <atomstruct/string_types.h>
#include <atomstruct/Atom.h>
#include <atomstruct/Coord.h>
#include <atomstruct/Pseudobond.h>
#include <atomstruct/Residue.h>
#include <pyinstance/PythonInstance.declare.h>

using namespace atomstruct;

namespace isolde
{
class Position_Restraint_Mgr;

class Position_Restraint: public pyinstance::PythonInstance<Position_Restraint>
{
public:
    Position_Restraint() {}
    ~Position_Restraint() { auto du=DestructionUser(this); }
    Position_Restraint(Atom* atom, const Coord& target, Position_Restraint_Mgr *mgr)
        : _atom(atom), _mgr(mgr)
    {
        set_target(target[0], target[1], target[2]);
    }

    void set_target(const Real &x, const Real &y, const Real &z)
    {
        _target[0]=x; _target[1]=y; _target[2]=z;
    }
    void set_target(Real *target)
    {
        for (size_t i=0; i<3; ++i)
            _target[i] = *(target++);
    }
    const Coord& get_target() const { return _target; }
    void get_target(double *target) const {
        for (size_t i=0; i<3; ++i)
            *target++ = _target[i];
    }
    void set_k(double k);
    double get_k() const { return _spring_constant; }
    void set_enabled(bool flag) { _enabled = flag; }
    bool enabled() const { return _enabled; }
    bool visible() const { return _atom->visible() && _enabled; }
    void target_vector(double *vector) const;
    Atom *atom() const { return _atom; }
    double radius() const;
    //! Provide a 4x4 OpenGL array transforming a primitive unit bond onto this restraint
    void bond_cylinder_transform(float *rot44) const;
    Change_Tracker* change_tracker() const;

private:
    Atom* _atom;
    Coord _target;
    Position_Restraint_Mgr* _mgr;
    double _spring_constant = 0.0;
    bool _enabled = false;


}; //class Position_Restraint

class Position_Restraint_Mgr
    : public DestructionObserver, public pyinstance::PythonInstance<Position_Restraint_Mgr>
{
public:
    Position_Restraint_Mgr() {}
    ~Position_Restraint_Mgr();
    Position_Restraint_Mgr(Structure *atomic_model, Change_Tracker *change_tracker)
        : _atomic_model(atomic_model), _change_tracker(change_tracker)
    {
        change_tracker->register_mgr(std::type_index(typeid(this)), _py_name, _managed_class_py_name);
    }

    Structure* structure() const { return _atomic_model; }
    Position_Restraint* get_restraint(Atom *atom, bool create);
    size_t num_restraints() const { return _atom_to_restraint.size(); }
    std::vector<Position_Restraint *> visible_restraints() const;
    Change_Tracker* change_tracker() const { return _change_tracker; }


    void delete_restraints(const std::set<Position_Restraint *>& to_delete);
    virtual void destructors_done(const std::set<void *>& destroyed);

private:
    Structure* _atomic_model;
    Change_Tracker* _change_tracker;
    std::unordered_map<Atom*, Position_Restraint*> _atom_to_restraint;
    Position_Restraint* _new_restraint(Atom *atom);
    Position_Restraint* _new_restraint(Atom *atom, const Coord& target);
    const char* error_different_mol() const {
        return "This atom is in the wrong structure!";
    }
    const char* error_hydrogen() const {
        return "Restraints on hydrogen atoms are not allowed!";
    }
    void _delete_restraints(const std::set<Position_Restraint *>& to_delete);
    const std::string _py_name = "Position_Restraint_Mgr";
    const std::string _managed_class_py_name = "Position_Restraints";

}; //class Position_Restraint_Mgr

} //namespace isolde
#endif //ISOLDE_POSITION_RESTRAINTS
