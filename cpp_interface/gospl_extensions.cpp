#include "gospl_extensions.h"
#include <Python.h>
#include <iostream>
#include <cstring>
#include <cmath>

// Include numpy headers
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>

static PyObject* gospl_module = nullptr;
static PyObject* create_model_func = nullptr;
static PyObject* destroy_model_func = nullptr;
static PyObject* run_dt_func = nullptr;
static PyObject* run_steps_func = nullptr;
static PyObject* run_until_func = nullptr;
static PyObject* apply_vel_func = nullptr;
static PyObject* interpolate_elev_func = nullptr;
static PyObject* get_time_func = nullptr;
static PyObject* get_dt_func = nullptr;

int initialize_gospl_extensions() {
    // Initialize Python interpreter
    if (!Py_IsInitialized()) {
        Py_Initialize();
        if (!Py_IsInitialized()) {
            std::cerr << "Failed to initialize Python interpreter" << std::endl;
            return -1;
        }
    }
    
    // Initialize numpy
    import_array1(-1);
    
    // Import sys module and add cpp_interface to path
    PyRun_SimpleString("import sys");
    PyRun_SimpleString("import os");
    PyRun_SimpleString("sys.path.insert(0, os.getcwd())");
    PyRun_SimpleString("sys.path.insert(0, '..')");
    PyRun_SimpleString("sys.path.insert(0, '.')");
    
    // Import our Python module
    gospl_module = PyImport_ImportModule("gospl_python_interface");
    if (!gospl_module) {
        PyErr_Print();
        std::cerr << "Failed to import gospl_python_interface module" << std::endl;
        return -1;
    }
    
    // Get function references
    create_model_func = PyObject_GetAttrString(gospl_module, "create_enhanced_model");
    destroy_model_func = PyObject_GetAttrString(gospl_module, "destroy_model");
    run_dt_func = PyObject_GetAttrString(gospl_module, "run_processes_for_dt");
    run_steps_func = PyObject_GetAttrString(gospl_module, "run_processes_for_steps");
    run_until_func = PyObject_GetAttrString(gospl_module, "run_processes_until_time");
    apply_vel_func = PyObject_GetAttrString(gospl_module, "apply_velocity_data");
    interpolate_elev_func = PyObject_GetAttrString(gospl_module, "interpolate_elevation_to_points");
    get_time_func = PyObject_GetAttrString(gospl_module, "get_current_time");
    get_dt_func = PyObject_GetAttrString(gospl_module, "get_time_step");
    
    if (!create_model_func || !destroy_model_func || !run_dt_func || 
        !run_steps_func || !run_until_func || !apply_vel_func ||
        !interpolate_elev_func || !get_time_func || !get_dt_func) {
        PyErr_Print();
        std::cerr << "Failed to get function references from Python module" << std::endl;
        return -1;
    }
    
    std::cout << "gospl_extensions C++ interface initialized successfully" << std::endl;
    return 0;
}

void finalize_gospl_extensions() {
    // Clean up Python references
    Py_XDECREF(create_model_func);
    Py_XDECREF(destroy_model_func);
    Py_XDECREF(run_dt_func);
    Py_XDECREF(run_steps_func);
    Py_XDECREF(run_until_func);
    Py_XDECREF(apply_vel_func);
    Py_XDECREF(interpolate_elev_func);
    Py_XDECREF(get_time_func);
    Py_XDECREF(get_dt_func);
    Py_XDECREF(gospl_module);
    
    // Finalize Python interpreter
    if (Py_IsInitialized()) {
        Py_Finalize();
    }
}

ModelHandle create_enhanced_model(const char* config_path) {
    if (!create_model_func) return -1;
    
    PyObject* args = PyTuple_New(1);
    PyTuple_SetItem(args, 0, PyUnicode_FromString(config_path));
    
    PyObject* result = PyObject_CallObject(create_model_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1;
    }
    
    ModelHandle handle = PyLong_AsLong(result);
    Py_DECREF(result);
    
    return handle;
}

int destroy_model(ModelHandle handle) {
    if (!destroy_model_func) return -1;
    
    PyObject* args = PyTuple_New(1);
    PyTuple_SetItem(args, 0, PyLong_FromLong(handle));
    
    PyObject* result = PyObject_CallObject(destroy_model_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1;
    }
    
    int ret = PyLong_AsLong(result);
    Py_DECREF(result);
    
    return ret;
}

double run_processes_for_dt(ModelHandle handle, double dt, int verbose) {
    if (!run_dt_func) return -1.0;
    
    PyObject* args = PyTuple_New(3);
    PyTuple_SetItem(args, 0, PyLong_FromLong(handle));
    PyTuple_SetItem(args, 1, PyFloat_FromDouble(dt));
    PyTuple_SetItem(args, 2, PyBool_FromLong(verbose));
    
    PyObject* result = PyObject_CallObject(run_dt_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1.0;
    }
    
    double elapsed = PyFloat_AsDouble(result);
    Py_DECREF(result);
    
    return elapsed;
}

int run_processes_for_steps(ModelHandle handle, int num_steps, double dt, int verbose) {
    if (!run_steps_func) return -1;
    
    PyObject* args = PyTuple_New(4);
    PyTuple_SetItem(args, 0, PyLong_FromLong(handle));
    PyTuple_SetItem(args, 1, PyLong_FromLong(num_steps));
    PyTuple_SetItem(args, 2, PyFloat_FromDouble(dt));
    PyTuple_SetItem(args, 3, PyBool_FromLong(verbose));
    
    PyObject* result = PyObject_CallObject(run_steps_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1;
    }
    
    int steps = PyLong_AsLong(result);
    Py_DECREF(result);
    
    return steps;
}

int run_processes_until_time(ModelHandle handle, double target_time, double dt, int verbose) {
    if (!run_until_func) return -1;
    
    PyObject* args = PyTuple_New(4);
    PyTuple_SetItem(args, 0, PyLong_FromLong(handle));
    PyTuple_SetItem(args, 1, PyFloat_FromDouble(target_time));
    PyTuple_SetItem(args, 2, PyFloat_FromDouble(dt));
    PyTuple_SetItem(args, 3, PyBool_FromLong(verbose));
    
    PyObject* result = PyObject_CallObject(run_until_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1;
    }
    
    int steps = PyLong_AsLong(result);
    Py_DECREF(result);
    
    return steps;
}

int apply_velocity_data(ModelHandle handle, const double* coords, const double* velocities,
                       int num_points, double timer, int k, double power) {
    if (!apply_vel_func) return -1;
    
    // Create numpy arrays from C arrays
    npy_intp coord_dims[2] = {num_points, 3};
    npy_intp vel_dims[2] = {num_points, 3};
    
    PyObject* coord_array = PyArray_SimpleNewFromData(2, coord_dims, NPY_DOUBLE, (void*)coords);
    PyObject* vel_array = PyArray_SimpleNewFromData(2, vel_dims, NPY_DOUBLE, (void*)velocities);
    
    if (!coord_array || !vel_array) {
        PyErr_Print();
        Py_XDECREF(coord_array);
        Py_XDECREF(vel_array);
        return -1;
    }
    
    PyObject* args = PyTuple_New(7);
    PyTuple_SetItem(args, 0, PyLong_FromLong(handle));
    PyTuple_SetItem(args, 1, coord_array);
    PyTuple_SetItem(args, 2, vel_array);
    PyTuple_SetItem(args, 3, PyLong_FromLong(num_points));
    PyTuple_SetItem(args, 4, PyFloat_FromDouble(timer));
    PyTuple_SetItem(args, 5, PyLong_FromLong(k));
    PyTuple_SetItem(args, 6, PyFloat_FromDouble(power));
    
    PyObject* result = PyObject_CallObject(apply_vel_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1;
    }
    
    int ret = PyLong_AsLong(result);
    Py_DECREF(result);
    
    return ret;
}

int interpolate_elevation_to_points(ModelHandle handle, const double* coords, int num_points,
                                   double* elevations, int k, double power) {
    if (!interpolate_elev_func) return -1;
    
    // Create numpy array from C array
    npy_intp coord_dims[2] = {num_points, 3};
    PyObject* coord_array = PyArray_SimpleNewFromData(2, coord_dims, NPY_DOUBLE, (void*)coords);
    
    if (!coord_array) {
        PyErr_Print();
        return -1;
    }
    
    PyObject* args = PyTuple_New(4);
    PyTuple_SetItem(args, 0, PyLong_FromLong(handle));
    PyTuple_SetItem(args, 1, coord_array);
    PyTuple_SetItem(args, 2, PyLong_FromLong(k));
    PyTuple_SetItem(args, 3, PyFloat_FromDouble(power));
    
    PyObject* result = PyObject_CallObject(interpolate_elev_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1;
    }
    
    // Extract elevation values from numpy array result
    if (PyArray_Check(result)) {
        PyArrayObject* elev_array = (PyArrayObject*)result;
        double* elev_data = (double*)PyArray_DATA(elev_array);
        
        // Copy elevation data to output array
        for (int i = 0; i < num_points; i++) {
            elevations[i] = elev_data[i];
        }
        
        Py_DECREF(result);
        return 0;
    } else {
        Py_DECREF(result);
        return -1;
    }
}

double get_current_time(ModelHandle handle) {
    if (!get_time_func) return -1.0;
    
    PyObject* args = PyTuple_New(1);
    PyTuple_SetItem(args, 0, PyLong_FromLong(handle));
    
    PyObject* result = PyObject_CallObject(get_time_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1.0;
    }
    
    double time = PyFloat_AsDouble(result);
    Py_DECREF(result);
    
    return time;
}

double get_time_step(ModelHandle handle) {
    if (!get_dt_func) return -1.0;
    
    PyObject* args = PyTuple_New(1);
    PyTuple_SetItem(args, 0, PyLong_FromLong(handle));
    
    PyObject* result = PyObject_CallObject(get_dt_func, args);
    Py_DECREF(args);
    
    if (!result) {
        PyErr_Print();
        return -1.0;
    }
    
    double dt = PyFloat_AsDouble(result);
    Py_DECREF(result);
    
    return dt;
}

int create_velocity_field(double t, double center_x, double center_y, double amplitude,
                         double* coords, double* velocities) {
    // Generate a 10x10 grid of velocity points (100 points total)
    const int grid_size = 10;
    const int num_points = grid_size * grid_size;
    
    for (int i = 0; i < grid_size; i++) {
        for (int j = 0; j < grid_size; j++) {
            int idx = i * grid_size + j;
            
            // Coordinates (10x10 grid from 0 to 10)
            double x = i * 10.0 / (grid_size - 1);
            double y = j * 10.0 / (grid_size - 1);
            double z = 0.0;
            
            coords[idx * 3 + 0] = x;
            coords[idx * 3 + 1] = y;
            coords[idx * 3 + 2] = z;
            
            // Create rotational velocity field that changes with time
            double dx = x - center_x;
            double dy = y - center_y;
            
            // Time-dependent rotation
            double omega = 0.1 * std::sin(t * 0.1);  // Angular velocity varies with time
            double vx = -dy * omega * amplitude;
            double vy = dx * omega * amplitude;
            double vz = 0.01 * std::sin(x + t * 0.05) * amplitude;
            
            velocities[idx * 3 + 0] = vx;
            velocities[idx * 3 + 1] = vy;
            velocities[idx * 3 + 2] = vz;
        }
    }
    
    return num_points;
}
