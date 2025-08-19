# gospl_extensions C++ Interface

This directory provides a C++ interface to the goSPL extensions (EnhancedModel and DataDrivenTectonics) through Python C API bindings.

## Overview

The C++ interface allows external C++ simulation codes to:
- Create and manage EnhancedModel instances
- Run goSPL simulations with granular time control
- Apply time-dependent velocity data using DataDrivenTectonics
- Monitor simulation progress and control execution

## Files

### Core Interface
- `gospl_extensions.h` - C++ header defining the interface
- `gospl_extensions.cpp` - C++ implementation using Python C API
- `gospl_python_interface.py` - Python bridge module

### Driver and Examples
- `enhanced_model_driver.cpp` - Basic C++ driver (equivalent to enhanced_model_basic.py)
- `enhanced_model_advanced_driver.cpp` - Advanced C++ driver with elevation tracking (equivalent to enhanced_model_advanced.py)
- `test_interface.cpp` - Simple test program for the interface

### Build System
- `Makefile` - Build system for compiling shared library and executables
- `CMakeLists.txt` - CMake build configuration (alternative)

## Prerequisites

1. **goSPL Environment**: Activate the gospl conda environment
   ```bash
   conda activate gospl
   ```

2. **Build Tools**: Ensure you have a C++ compiler and Python development headers
   ```bash
   # On Ubuntu/Debian:
   sudo apt install build-essential python3-dev python3-numpy
   
   # On CentOS/RHEL:
   sudo yum install gcc-c++ python3-devel python3-numpy
   ```

3. **goSPL Extensions**: Ensure the parent gospl_extensions package is working
   ```bash
   cd ..
   python -c "from gospl_model_ext import EnhancedModel; print('✅ Extensions working')"
   ```

## Building

### Option 1: Using Makefile (Recommended)

```bash
# Build everything (shared library + executables)
make

# Run basic interface tests
make test

# Run with actual goSPL simulation (requires config file)
make test-gospl

# Run advanced simulation with elevation tracking
make test-gospl-advanced

# Clean build artifacts
make clean

# Show build configuration
make debug-info
```

### Option 2: Using CMake

```bash
mkdir build
cd build
cmake ..
make
```

### Manual Build

```bash
# Get Python configuration
PYTHON_INCLUDE=$(python3 -c "import sys; print(f'-I{sys.prefix}/include/python{sys.version_info.major}.{sys.version_info.minor}')")
NUMPY_INCLUDE=$(python3 -c "import numpy; print(f'-I{numpy.get_include()}')")
PYTHON_LIBS=$(python3-config --ldflags)

# Build shared library
g++ -std=c++14 -Wall -fPIC -O3 $PYTHON_INCLUDE $NUMPY_INCLUDE -shared -o libgospl_extensions.so gospl_extensions.cpp $PYTHON_LIBS

# Build driver
g++ -std=c++14 -Wall -O3 $PYTHON_INCLUDE $NUMPY_INCLUDE -o enhanced_model_driver enhanced_model_driver.cpp -L. -lgospl_extensions $PYTHON_LIBS
```

## Usage

### 1. Basic Interface Test

```bash
# Test the interface without goSPL simulation
./test_interface
```

This tests:
- Python interpreter initialization
- Function loading
- Velocity field generation
- Basic error handling

### 2. Full goSPL Simulation

```bash
# Ensure you have a goSPL config file
ls ../examples/input-escarpment.yml

# Run the full C++ driver
export LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH
./enhanced_model_driver ../examples/input-escarpment.yml
```

This runs the complete C++ equivalent of `enhanced_model_basic.py`:
- Creates EnhancedModel instance
- Demonstrates all three new methods (`runProcessesForDt`, `runProcessesForSteps`, `runProcessesUntilTime`)
- Runs controlled simulation with time-dependent tectonics
- Shows real landscape evolution physics

### Advanced Driver with Elevation Tracking

```bash
# Build and run advanced driver
make advanced-driver
export LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH
./enhanced_model_advanced_driver ../examples/input-escarpment.yml
```

This runs the complete C++ equivalent of `enhanced_model_advanced.py`:
- Creates EnhancedModel with elevation interpolation capabilities
- Tracks elevation changes at velocity sampling points
- Updates velocity coordinates based on evolving topography
- Provides detailed before/after elevation analysis
- Demonstrates sophisticated coupling between tectonics and topography

### 3. Integration in Your Code

```cpp
#include "gospl_extensions.h"

int main() {
    // Initialize
    if (initialize_gospl_extensions() != 0) {
        return 1;
    }
    
    // Create model
    ModelHandle model = create_enhanced_model("config.yml");
    if (model < 0) {
        finalize_gospl_extensions();
        return 1;
    }
    
    // Run simulation
    double elapsed = run_processes_for_dt(model, 1.0, 1);  // dt=1.0, verbose=true
    
    // Apply velocity data
    double coords[300], velocities[300];  // 100 points * 3 components
    create_velocity_field(0.0, 5.0, 5.0, 0.1, coords, velocities);
    apply_velocity_data(model, coords, velocities, 100, 1.0, 3, 1.0);
    
    // Cleanup
    destroy_model(model);
    finalize_gospl_extensions();
    return 0;
}
```

## API Reference

### Initialization
- `int initialize_gospl_extensions()` - Initialize Python and load extensions
- `void finalize_gospl_extensions()` - Clean up Python interpreter

### Model Management  
- `ModelHandle create_enhanced_model(const char* config_path)` - Create model instance
- `int destroy_model(ModelHandle handle)` - Destroy model instance

### Time Control
- `double run_processes_for_dt(ModelHandle, double dt, int verbose)` - Run for specific dt
- `int run_processes_for_steps(ModelHandle, int num_steps, double dt, int verbose)` - Run multiple steps
- `int run_processes_until_time(ModelHandle, double target_time, double dt, int verbose)` - Run until time

### Velocity Data
- `int apply_velocity_data(ModelHandle, const double* coords, const double* velocities, int num_points, double timer, int k, double power)` - Apply external velocities
- `int interpolate_elevation_to_points(ModelHandle, const double* coords, int num_points, double* elevations, int k, double power)` - Interpolate elevation field to external points
- `int create_velocity_field(double t, double center_x, double center_y, double amplitude, double* coords, double* velocities)` - Generate test velocity field

### Utilities
- `double get_current_time(ModelHandle)` - Get current simulation time
- `double get_time_step(ModelHandle)` - Get model time step

## Troubleshooting

### Build Issues

1. **Python headers not found**:
   ```bash
   # Install development headers
   sudo apt install python3-dev
   
   # Or check Python installation
   python3-config --includes
   ```

2. **NumPy headers not found**:
   ```bash
   # Check NumPy installation
   python3 -c "import numpy; print(numpy.get_include())"
   ```

3. **Library linking errors**:
   ```bash
   # Set library path
   export LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH
   
   # Or install system-wide
   sudo make install
   ```

### Runtime Issues

1. **Python import errors**:
   ```bash
   # Ensure gospl environment is activated
   conda activate gospl
   
   # Check extensions work
   python3 -c "from gospl_model_ext import EnhancedModel"
   ```

2. **Config file errors**:
   ```bash
   # Use absolute path to config file
   ./enhanced_model_driver /full/path/to/input-escarpment.yml
   ```

3. **Memory or stability issues**:
   - Make sure to call `destroy_model()` for each created model
   - Call `finalize_gospl_extensions()` at program exit
   - Check for Python exceptions in console output

## Performance

The C++ interface adds minimal overhead:
- Function calls go through Python C API (microsecond latency)
- Actual simulation runs at full goSPL speed
- Memory is managed by Python/NumPy (efficient)
- No data copying for large arrays (numpy views)

For high-performance applications:
- Batch multiple time steps when possible
- Minimize create/destroy model cycles
- Use larger time steps (dt) when appropriate
- Consider keeping the interface initialized for the application lifetime

## Examples

See `enhanced_model_driver.cpp` for a complete example that demonstrates:
- Model initialization and cleanup
- All three time-stepping methods
- Time-dependent velocity field application
- Error handling and progress monitoring
- Integration with DataDrivenTectonics

The C++ driver produces equivalent results to `enhanced_model_basic.py` but can be integrated into larger C++ simulation frameworks.
