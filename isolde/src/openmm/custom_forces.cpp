/**
 * @Author: Tristan Croll <tic20>
 * @Date:   18-Apr-2018
 * @Email:  tic20@cam.ac.uk
 * @Last modified by:   tic20
 * @Last modified time: 26-Apr-2018
 * @License: Free for non-commercial use (see license.pdf)
 * @Copyright:2016-2019 Tristan Croll
 */



#ifdef _WIN32
# define EXPORT __declspec(dllexport)
#else
# define EXPORT __attribute__((__visibility__("default")))
#endif

#include "../molc.h"
#include <vector>
#include <OpenMM.h>

extern "C"
{

EXPORT void
cmaptorsionforce_add_torsions(void *force, size_t n, int *map_indices, int *d1_indices, int *d2_indices, int *force_indices)
{
    OpenMM::CMAPTorsionForce *f = static_cast<OpenMM::CMAPTorsionForce *>(force);
    try {
        int *d1 = d1_indices, *d2 = d2_indices;
        for (size_t i=0; i<n; ++i) {
            *(force_indices++) = f->addTorsion(*(map_indices++), d1[0], d1[1], d1[2], d1[3], d2[0], d2[1], d2[2], d2[3]);
            d1 += 4; d2 += 4;
        }
    } catch (...) {
        molc_error();
    }
}


EXPORT void
customcompoundbondforce_add_bonds(void *force, size_t n, int *p_indices, double *params, int *f_indices)
{
    OpenMM::CustomCompoundBondForce *f = static_cast<OpenMM::CustomCompoundBondForce *>(force);
    try {
        int n_params = f->getNumPerBondParameters();
        std::vector<double> param_vec(n_params);
        int n_particles = f->getNumParticlesPerBond();
        std::vector<int> particles(n_particles);
        for (size_t i=0; i<n; ++i) {
            for (int j=0; j<n_params; ++j)
                param_vec[j] = *params++;
            for (int j=0; j<n_particles; ++j)
                particles[j] = *(p_indices++);
            *(f_indices++) = f->addBond(particles, param_vec);
        }
    } catch (...) {
        molc_error();
    }
}

EXPORT void
customcompoundbondforce_update_bond_parameters(void *force, size_t n, int *indices, double *params)
{
    OpenMM::CustomCompoundBondForce *f = static_cast<OpenMM::CustomCompoundBondForce *>(force);
    try {
        int n_params = f->getNumPerBondParameters();
        std::vector<double> param_vec(n_params);
        int n_particles = f->getNumParticlesPerBond();
        std::vector<int> particles(n_particles);
        for (size_t i=0; i<n; ++i) {
            int index = *(indices++);
            f->getBondParameters(index, particles, param_vec);
            for (int j=0; j<n_params; ++j) {
                param_vec[j] = *params++;
            }
            f->setBondParameters(index, particles, param_vec);
        }
    } catch (...) {
        molc_error();
    }
}

EXPORT void
custombondforce_add_bonds(void *force, size_t n, int *p_indices, double *params, int *f_indices)
{
    OpenMM::CustomBondForce *f = static_cast<OpenMM::CustomBondForce *>(force);
    try {
        int n_params = f->getNumPerBondParameters();
        std::vector<double> param_vec(n_params);
        int p1, p2;
        for (size_t i=0; i<n; ++i) {
            for (int j=0; j<n_params; ++j)
                param_vec[j] = *params++;
            p1 = *(p_indices++);
            p2 = *(p_indices++);
            *(f_indices++) = f->addBond(p1, p2, param_vec);
        }
    } catch (...) {
        molc_error();
    }
}

EXPORT void
custombondforce_update_bond_parameters(void *force, size_t n, int *indices, double *params)
{
    OpenMM::CustomBondForce *f = static_cast<OpenMM::CustomBondForce *>(force);
    try {
        int n_params = f->getNumPerBondParameters();
        std::vector<double> param_vec(n_params);
        int particle1, particle2;
        for (size_t i=0; i<n; ++i) {
            int index = *(indices++);
            f->getBondParameters(index, particle1, particle2, param_vec);
            for (int j=0; j<n_params; ++j) {
                param_vec[j] = *params++;
            }
            f->setBondParameters(index, particle1, particle2, param_vec);
        }
    } catch (...) {
        molc_error();
    }
}


EXPORT void
customexternalforce_add_particles(void *force, size_t n, int *particle_indices, double *params, int *force_indices)
{
    OpenMM::CustomExternalForce *f = static_cast<OpenMM::CustomExternalForce *>(force);
    try {
        int n_params = f->getNumPerParticleParameters();
        std::vector<double> param_vec(n_params);
        for (size_t i=0; i<n; ++i) {
            for (int j=0; j<n_params; ++j)
                param_vec[j] = *params++;
            *(force_indices++) = f->addParticle(*(particle_indices++), param_vec);
        }
    } catch (...) {
        molc_error();
    }
}

EXPORT void
customexternalforce_update_particle_parameters(void *force, size_t n, int *indices, double *params)
{
    OpenMM::CustomExternalForce *f = static_cast<OpenMM::CustomExternalForce *>(force);
    try {
        int n_params = f->getNumPerParticleParameters();
        std::vector<double> param_vec(n_params);
        int particle;
        for (size_t i=0; i<n; ++i) {
            int index = *(indices++);
            f->getParticleParameters(index, particle, param_vec);
            for (int j=0; j<n_params; ++j) {
                param_vec[j] = *params++;
            }
            f->setParticleParameters(index, particle, param_vec);
        }
    } catch (...) {
        molc_error();
    }
}

EXPORT void
customtorsionforce_add_torsions(void *force, size_t n, int *particle_indices, double *params, int *force_indices)
{
    OpenMM::CustomTorsionForce *f = static_cast<OpenMM::CustomTorsionForce *>(force);
    try {
        int n_params = f->getNumPerTorsionParameters();
        std::vector<double> param_vec(n_params);
        std::vector<int> p(4);
        for (size_t i=0; i<n; ++i) {
            for (int j=0; j<n_params; ++j) {
                param_vec[j] = *params++;
            }
            for (size_t j=0; j<4; ++j) {
                p[j] = *(particle_indices++);
            }
            *(force_indices++) = f->addTorsion(p[0], p[1], p[2], p[3], param_vec);
        }
    } catch (...) {
        molc_error();
    }
}

EXPORT void
customtorsionforce_update_torsion_parameters(void *force, size_t n, int *indices, double *params)
{
    OpenMM::CustomTorsionForce *f = static_cast<OpenMM::CustomTorsionForce *>(force);
    try {
        int n_params = f->getNumPerTorsionParameters();
        std::vector<double> param_vec(n_params);
        int p1, p2, p3, p4;
        for (size_t i=0; i<n; ++i) {
            int index = *(indices++);
            f->getTorsionParameters(index, p1, p2, p3, p4, param_vec);
            for (int j=0; j<n_params; ++j) {
                param_vec[j] = *params++;
            }
            f->setTorsionParameters(index, p1, p2, p3, p4, param_vec);
        }
    } catch (...) {
        molc_error();
    }
}

EXPORT void
customgbforce_add_particles(void *force, size_t n, double* params)
{
    OpenMM::CustomGBForce *f = static_cast<OpenMM::CustomGBForce *>(force);
    try
    {
        int n_params = f->getNumPerParticleParameters();
        std::vector<double> param_vec(n_params);
        for (size_t i=0; i<n; ++i) {
            for (int j=0; j<n_params; ++j) {
                param_vec[j] = *params++;
            }
            f->addParticle(param_vec);
        }
    } catch (...) {
        molc_error();
    }
}


} // extern "C"
