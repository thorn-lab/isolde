#ifndef molc_py_interface
#define molc_py_interface

#ifndef M_PI
// not defined on Windows
# define M_PI 3.14159265358979323846
#endif

#ifdef _WIN32
# define EXPORT __declspec(dllexport)
#else
# define EXPORT __attribute__((__visibility__("default")))
#endif

#include <Python.h>

// Argument delcaration types:
//
// numpy array arguments are sized, so use uint8_t for numpy's uint8,
// float32_t for numpys float32_t, etc.  The integer _t types are from
// <stdint.h>.  Special case is for numpy/C/C++ booleans which are
// processed in all cases as bytes:
//      1 == numpy.bool_().nbytes in Python
//      1 == sizeof (bool) in C++ and in C from <stdbool.h>
//      25 == sizeof (bool [25]) in C++ and C
//
// Other arguments are their normal C types and are specified with the
// appropriate ctypes annotations on the Python side.
//
// There should be very few 'int' specifications.  Any int-array should
// have a specific size, eg., int32_t, for its elements.
//
typedef uint8_t npy_bool;
typedef float float32_t;
typedef double float64_t;
typedef void *pyobject_t;

inline PyObject* unicode_from_string(const char *data, size_t size)
{
    return PyUnicode_DecodeUTF8(data, size, "replace");
}

inline PyObject* unicode_from_string(const std::string& str)
{
    return PyUnicode_DecodeUTF8(str.data(), str.size(), "replace");
}

inline PyObject* unicode_from_character(char c)
{
    char buffer[2];
    buffer[0] = c;
    buffer[1] = '\0';
    return unicode_from_string(buffer, 1);
}

static void
molc_error()
{
    // generic exception handler
    if (PyErr_Occurred())
        return;   // nothing to do, already set
    try {
        throw;    // rethrow exception to look at it
    } catch (std::bad_alloc&) {
        PyErr_SetString(PyExc_MemoryError, "not enough memory");
    } catch (std::invalid_argument& e) {
        PyErr_SetString(PyExc_TypeError, e.what());
    } catch (std::length_error& e) {
        PyErr_SetString(PyExc_MemoryError, e.what());
    } catch (std::out_of_range& e) {
        PyErr_SetString(PyExc_IndexError, e.what());
    } catch (std::overflow_error& e) {
        PyErr_SetString(PyExc_OverflowError, e.what());
    } catch (std::range_error& e) {
        PyErr_SetString(PyExc_IndexError, e.what());
    } catch (std::underflow_error& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
    } catch (std::logic_error& e) {
        PyErr_SetString(PyExc_ValueError, e.what());
    } catch (std::ios_base::failure& e) {
        PyErr_SetString(PyExc_IOError, e.what());
    } catch (std::runtime_error& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
    } catch (std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "unknown C++ exception");
    }
}

// wrap an arbitrary function
template <typename F, typename... Args> auto
error_wrap(const F& func, Args... args) -> decltype(func(args...))
{
    try {
        return func(args...);
    } catch (...) {
        molc_error();
        return decltype(func(args...))();
    }
}

// wrap a member function
template <typename R, typename T, typename... Args> R
error_wrap(T* inst, R (T::*pm)(Args...), Args... args)
{
    try {
        return (inst->*pm)(args...);
    } catch (...) {
        molc_error();
        return R();
    }
}

// wrap a constant member function
template <typename R, typename T, typename... Args> R
error_wrap(T* inst, R (T::*pm)(Args...) const, Args... args)
{
    try {
        return (inst->*pm)(args...);
    } catch (...) {
        molc_error();
        return R();
    }
}

// wrap getting array elements via const member function
template <typename T, typename Elem, typename Elem2 = Elem> void
error_wrap_array_get(T** instances, size_t n, Elem (T::*pm)() const, Elem2* args)
{
    try {
        for (size_t i = 0; i < n; ++i)
            args[i] = (instances[i]->*pm)();
    } catch (...) {
        molc_error();
    }
}

// wrap setting array elements via member function
template <typename T, typename Elem, typename Elem2 = Elem> void
error_wrap_array_set(T** instances, size_t n, void (T::*pm)(Elem), Elem2* args)
{
    try {
        for (size_t i = 0; i < n; ++i)
            (instances[i]->*pm)(args[i]);
    } catch (...) {
        molc_error();
    }
}

#endif // molc_py_interface