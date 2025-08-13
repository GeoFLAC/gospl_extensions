/**
 * Simple Debug Test for C++ Interface
 */
#include <iostream>
#include <Python.h>

int main() {
    std::cout << "Python Debug Test" << std::endl;
    std::cout << "=================" << std::endl;
    
    // Initialize Python interpreter
    if (!Py_IsInitialized()) {
        Py_Initialize();
        if (!Py_IsInitialized()) {
            std::cerr << "Failed to initialize Python interpreter" << std::endl;
            return 1;
        }
    }
    std::cout << "✅ Python interpreter initialized" << std::endl;
    
    // Add current directory to path
    PyRun_SimpleString("import sys");
    PyRun_SimpleString("import os");
    PyRun_SimpleString("print('Current working directory:', os.getcwd())");
    PyRun_SimpleString("sys.path.insert(0, os.getcwd())");
    PyRun_SimpleString("print('Python path:')");
    PyRun_SimpleString("for p in sys.path[:5]: print('  ', p)");
    
    // Try to import the module
    std::cout << "Attempting to import gospl_python_interface..." << std::endl;
    PyObject* module = PyImport_ImportModule("gospl_python_interface");
    if (!module) {
        std::cout << "❌ Module import failed" << std::endl;
        PyErr_Print();
    } else {
        std::cout << "✅ Module import successful!" << std::endl;
        Py_DECREF(module);
    }
    
    Py_Finalize();
    return 0;
}
