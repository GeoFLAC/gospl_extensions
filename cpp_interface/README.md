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

# Install locally for external C++ project integration
make install-local

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

#### Local Installation for External Projects

The `install-local` target creates a standard library structure for integration with external C++ projects like DynEarthSol:

```bash
make install-local
```

This creates:
- `../lib/libgospl_extensions.so` - Shared library for linking
- `../include/gospl_extensions.h` - Header file for inclusion

The external project's build system can then use standard linking:
```makefile
CXXFLAGS += -I./gospl_extensions/include
LDFLAGS += -L./gospl_extensions/lib -lgospl_extensions
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
    if (initialize_gospl_extensions() != 0) return 1;

    ModelHandle model = create_enhanced_model("config.yml");
    if (model < 0) { finalize_gospl_extensions(); return 1; }

    const int N = 100;  // number of DES surface nodes
    double coords[N * 3];    // surface node coordinates
    double elevations[N];    // surface node elevations (metres)
    // ... fill coords and elevations from DES ...

    // Seed GoSPL elevation from DES surface (once at init; repeat after remeshing)
    apply_elevation_data(model, coords, elevations, N, 3, 1.0);

    // Coupling loop
    double dt_yr = 1000.0;
    for (int step = 0; step < num_steps; ++step) {
        double vx_yr[N], vy_yr[N], vz_yr[N];
        // ... compute time-averaged DES surface velocities (m/yr) ...

        // Send all three velocity components to GoSPL
        set_surface_velocity(model, coords, vx_yr, vy_yr, vz_yr, N, 3, 1.0);

        // Run GoSPL; erosion[i] = delta_h (erosion+diffusion only, uplift excluded)
        double erosion[N];
        run_and_get_erosion(model, dt_yr, coords, N, erosion, 3, 1.0);

        // Add erosion[i] to DES surface node z-coordinates
        for (int i = 0; i < N; ++i) coords[i*3 + 2] += erosion[i];
    }

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
- `double run_processes_for_dt(ModelHandle, double dt, int verbose, int skip_tectonics)` - Run for specific dt
- `int run_processes_for_steps(ModelHandle, int num_steps, double dt, int verbose, int skip_tectonics)` - Run multiple steps
- `int run_processes_until_time(ModelHandle, double target_time, double dt, int verbose, int skip_tectonics)` - Run until time

### DES Coupling API
- `int apply_elevation_data(ModelHandle, const double* coords, const double* elevations, int num_points, int k, double power)` - Seed GoSPL elevation from DES surface (called once at init and after remeshing)
- `int set_surface_velocity(ModelHandle, const double* coords, const double* vx_yr, const double* vy_yr, const double* vz_yr, int num_points, int k, double power)` - IDW-interpolate all three DES surface velocity components onto GoSPL mesh; stored for the next `run_and_get_erosion` call
- `int set_uplift_rate(ModelHandle, const double* coords, const double* vz_yr, int num_points, int k, double power)` - IDW-interpolate vertical velocity only (vz in m/yr) onto GoSPL mesh
- `int run_and_get_erosion(ModelHandle, double dt, const double* coords, int num_points, double* erosion, int k, double power)` - Run GoSPL for dt years; return net erosion (m) at query points (uplift excluded)
- `int apply_drift_correction(ModelHandle, const double* coords, const double* des_elev, int num_points, double alpha, int k, double power)` - Blend GoSPL elevation toward DES elevation with strength alpha [0,1]
- `int interpolate_elevation_to_points(ModelHandle, const double* coords, int num_points, double* elevations, int k, double power)` - Query current GoSPL elevation at arbitrary coordinates

### Utilities
- `double get_current_time(ModelHandle)` - Get current simulation time
- `double get_time_step(ModelHandle)` - Get model time step
- `int apply_velocity_data(ModelHandle, const double* coords, const double* velocities, int num_points, double timer, int k, double power)` - Apply DataDrivenTectonics velocity field
- `int create_velocity_field(double t, double center_x, double center_y, double amplitude, double* coords, double* velocities)` - Generate test velocity field

## DynEarthSol Integration

The C++ interface is specifically designed to integrate with DynEarthSol, a finite element geodynamic modeling code. This allows for two-way coupling between geodynamic processes (DynEarthSol) and landscape evolution processes (GoSPL).

### Integration Overview

1. **DynEarthSol** handles:
   - Tectonic deformation and stress evolution
   - Temperature and fluid flow
   - Rock rheology and material properties
   - Mesh adaptation and remeshing

2. **GoSPL** handles:
   - Surface erosion and sedimentation
   - Hillslope diffusion
   - River incision and transport
   - Marine processes

3. **Coupling mechanism**:
   - DynEarthSol provides surface velocities to GoSPL
   - GoSPL evolves surface topography over each timestep
   - Updated elevations are returned to DynEarthSol
   - Process repeats for each simulation timestep

### Integration Steps

1. **Clone gospl_extensions in DynEarthSol directory:**
   ```bash
   cd /path/to/DynEarthSol
   git clone https://github.com/GeoFLAC/gospl_extensions.git
   ```

2. **Build gospl_extensions for local integration:**
   ```bash
   conda activate gospl  # Activate gospl environment
   cd gospl_extensions/cpp_interface
   make install-local
   cd ../..
   ```

3. **Configure DynEarthSol build:**
   ```makefile
   # In DynEarthSol Makefile, set:
   use_gospl = 1
   ```

4. **Build DynEarthSol:**
   ```bash
   conda deactivate  # Use system compiler for DynEarthSol
   make
   ```

5. **Configure simulation:**
   ```cfg
   # In DynEarthSol config file:
   surface_process_option = 11
   surface_process_gospl_config_file = ./gospl_config.yml
   ```

### Directory Structure After Integration

```
DynEarthSol/
├── Makefile                          # use_gospl = 1
├── gospl_extensions/                 # Cloned repository
│   ├── lib/
│   │   └── libgospl_extensions.so    # Built by make install-local
│   ├── include/
│   │   └── gospl_extensions.h        # Built by make install-local
│   └── cpp_interface/
│       ├── Makefile                  # Contains install-local target
│       └── ...
├── gospl_driver/                     # DynEarthSol GoSPL integration code
│   ├── gospl-driver.hpp
│   ├── gospl-driver.cxx
│   └── examples/
│       └── gospl_config_example.yml
└── dynearthsol3d                     # Built executable with GoSPL support
```

### Usage in DynEarthSol

When properly configured, DynEarthSol follows the ASPECT–FastScape coupling scheme:
1. Initialize GoSPL at startup using the specified config file
2. At the first coupling event, seed GoSPL's elevation from DES surface nodes via `apply_elevation_data`; GoSPL owns the topography from this point on (and after each remesh)
3. At each coupling event, compute time-averaged DES surface velocities (Δcoord/Δt over the coupling interval) and send them to GoSPL via `set_surface_velocity`
4. Call `run_and_get_erosion` to advance GoSPL; it returns delta_h (erosion + diffusion only, uplift excluded because DES already moved the nodes via its Lagrangian solver)
5. Add delta_h to DES surface node z-coordinates

The integration is seamless and controlled by the `surface_process_option = 11` setting.

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
