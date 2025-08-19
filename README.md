# gospl_extensions

1. `gospl_tectonics_ext` - Data-driven tectonics extension
2. `gospl_model_ext` - Enhanced model with granular time control
3. `cpp_interface` - C++ interface to goSPL extensions

## Prerequisites

**Important**: All extensions require the `gospl` conda environment to be activated:

```bash
conda activate gospl
```

The extensions depend on goSPL and its Fortran extensions, which are typically installed via conda.

### Additional Requirements for C++ Interface

For the `cpp_interface`, you'll also need C++ build tools:

```bash
# On Ubuntu/Debian:
sudo apt install build-essential python3-dev python3-numpy

# On CentOS/RHEL:
sudo yum install gcc-c++ python3-devel python3-numpy
```

## gospl_tectonics_ext: Data-driven tectonics for goSPL

This out-of-tree extension adds a way to drive horizontal and vertical tectonic velocities from an external dataset (positions + 3-component velocities) whose sampling points don’t coincide with the model mesh. Velocities are interpolated to mesh nodes via k-nearest-neighbor inverse-distance weighting and then applied using goSPL’s existing advection machinery.

- Core goSPL code remains untouched.
- Import path: `from gospl_tectonics_ext import DataDrivenTectonics`.

### Install or make importable

Option A — Add to PYTHONPATH (quickest):
- Ensure `path/to/gospl_extensions` is on PYTHONPATH so Python can find `gospl_tectonics_ext`.

Option B — Editable install (recommended):
- Use the provided `pyproject.toml` and run an editable install.

### Usage

```python
from gospl.model import Model
from gospl_tectonics_ext import DataDrivenTectonics

m = Model("input-escarpment.yml", verbose=True)

# Bind the methods to this instance without modifying Model inheritance
m.apply_velocity_data = DataDrivenTectonics.apply_velocity_data.__get__(m, type(m))
m.interpolate_elevation_to_points = DataDrivenTectonics.interpolate_elevation_to_points.__get__(m, type(m))

veldata = {
    "coords": coords_np_array,  # shape (N, 3)
    "vel":    vel_np_array,     # shape (N, 3)
}

# Interpolate and apply external velocities
m.apply_velocity_data(veldata, timer=None, k=3, power=1.0)

# Interpolate current elevation field to external points
external_points = np.array([[x1, y1, z1], [x2, y2, z2], ...])  # shape (N, 3)
elevations = m.interpolate_elevation_to_points(external_points, k=3, power=1.0)
```

Behavior by advection scheme:
- advscheme == 0 (semi-Lagrangian): builds interpolation to advected positions and schedules plate advection at `tNow + timer`.
- advscheme > 0 (finite-volume IIOE/upwind): computes face velocities and advects immediately.

### Methods

**`apply_velocity_data(veldata, timer=None, k=3, power=1.0)`**
- Interpolates external velocity data to mesh nodes and applies it using goSPL's advection machinery
- `veldata`: dict or object with 'coords' (N,3) and 'vel' (N,3) arrays
- `timer`: time interval for semi-Lagrangian scheme (defaults to model dt)
- `k`: number of nearest neighbors for interpolation
- `power`: inverse distance weighting power

**`interpolate_elevation_to_points(src_pts, k=3, power=1.0)`**
- Interpolates current elevation field (`hGlobal`) to external points
- `src_pts`: target coordinates array of shape (N,3)
- Returns: numpy array of interpolated elevations (N,)
- Useful for data extraction, analysis, or coupling with other models

Notes:
- Requires goSPL to be importable and its Fortran extensions available (`gospl._fortran.getfacevelocity`).
- Handles coincident nodes robustly; respects flat vs spherical mode.
- MPI safe: interpolation built on global coordinates; locals are sliced to `locIDs`.

### Files
- `gospl_tectonics_ext/data_driven_tectonics.py`: the extension implementation.
- `gospl_tectonics_ext/__init__.py`: re-exports `DataDrivenTectonics`.

### Testing

The extension includes a comprehensive test suite to ensure reliability:

```bash
# Run tests using pytest (recommended)
pytest tests/

# Or use the built-in test runner (no pytest required)
python run_tests.py
```

Test coverage includes:
- Input validation and error handling
- Interpolation accuracy with different parameters (both velocity and elevation)
- Both advection schemes (semi-Lagrangian and finite-volume)
- Edge cases (coincident nodes, empty data, etc.)
- Elevation interpolation with various k and power values
- Mock testing that doesn't require goSPL installation

### Examples

Several example scripts demonstrate different use cases:

#### DataDrivenTectonics Basic Example
```bash
cd examples
python data_driven_tectonics_basic.py
```
Shows basic usage with synthetic velocity data and elevation interpolation.

#### DataDrivenTectonics Advanced Example
```bash
cd examples
python data_driven_tectonics_advanced.py
```
Demonstrates:
- Loading velocity data from CSV files
- Time-dependent velocity fields
- Comparing interpolation parameters
- Elevation field interpolation and sampling
- Monitoring velocity field effects

#### Sample Data
- `examples/velocity_data.csv`: Sample velocity data for testing
- `examples/input-escarpment.yml`: Working goSPL configuration file

### Packaging (optional)
A `pyproject.toml` is included for proper Python packaging. To install in editable mode:

```bash
pip install -e path/to/gospl_extensions
```

This will also install required dependencies (numpy, scipy) and make the extension importable from anywhere.

#### Development Installation
For development with testing dependencies:

```bash
pip install -e "path/to/gospl_extensions[dev]"
```

After this, `from gospl_tectonics_ext import DataDrivenTectonics` will work from anywhere.

## gospl_model_ext: Enhanced Model with Granular Time Control

This extension provides an `EnhancedModel` class that extends the goSPL `Model` class with additional methods for granular time control.

### Features

- **runProcessesForDt**: Run processes for a specific time step 'dt'
- **runProcessesForSteps**: Run processes for a specified number of time steps  
- **runProcessesUntilTime**: Run processes until a target time is reached

### Usage

```python
from gospl_model_ext import EnhancedModel

# Create enhanced model
model = EnhancedModel("config.yml")

# Run for specific dt
model.runProcessesForDt(dt=1000.0)

# Run for multiple steps with specific dt
model.runProcessesForSteps(num_steps=10, dt=1000.0)

# Run until target time is reached
model.runProcessesUntilTime(target_time=50000.0, dt=1000.0)
```

### Files
- `gospl_model_ext/enhanced_model.py`: the extension implementation.
- `gospl_model_ext/__init__.py`: re-exports `EnhancedModel`.

### Examples

#### EnhancedModel Basic Example
```bash
cd examples
python enhanced_model_basic.py
```
Shows controlled time-stepping with the EnhancedModel class, including demonstrations of all three new methods.

#### EnhancedModel Advanced Example
```bash
cd examples
python enhanced_model_advanced.py
```
Demonstrates:
- Elevation tracking at velocity sampling points
- Updating velocity coordinates based on evolving topography
- Analyzing elevation changes before and after each time step
- Advanced coupling between tectonics and topographic evolution

## cpp_interface: C++ Interface to goSPL Extensions

This directory provides a C++ interface to the goSPL extensions through Python C API bindings, allowing external C++ simulation codes to use the EnhancedModel and DataDrivenTectonics functionality.

### Features

- **C++ API**: Full C++ interface to EnhancedModel and DataDrivenTectonics
- **Time Control**: Run goSPL simulations with granular time control from C++
- **Velocity Data**: Apply time-dependent velocity fields from C++ code
- **Integration Ready**: Easy integration with existing C++ simulation frameworks

### Quick Start

```bash
# Build the interface
cd cpp_interface
make

# Run basic tests
make test

# Run with goSPL simulation
make test-gospl
```

### Basic Usage

```cpp
#include "gospl_extensions.h"

// Initialize and create model
initialize_gospl_extensions();
ModelHandle model = create_enhanced_model("config.yml");

// Run simulation with time control
double elapsed = run_processes_for_dt(model, 1000.0, 1);

// Apply velocity data
apply_velocity_data(model, coords, velocities, num_points, 1.0, 3, 1.0);

// Cleanup
destroy_model(model);
finalize_gospl_extensions();
```

For detailed documentation, API reference, build instructions, and examples, see [`cpp_interface/README.md`](cpp_interface/README.md).

## Project Structure

```
gospl_extensions/
├── README.md
├── pyproject.toml                    # Python packaging configuration
├── run_tests.py                      # Standalone test runner
├── gospl_tectonics_ext/
│   ├── __init__.py
│   └── data_driven_tectonics.py      # Main implementation
├── gospl_model_ext/
│   ├── __init__.py
│   └── enhanced_model.py             # Enhanced Model implementation
├── cpp_interface/
│   ├── README.md                     # Detailed C++ interface documentation
│   ├── gospl_extensions.h            # C++ header file
│   ├── gospl_extensions.cpp          # C++ implementation
│   ├── gospl_python_interface.py     # Python bridge module
│   ├── enhanced_model_driver.cpp     # C++ driver example
│   ├── test_interface.cpp            # Basic interface tests
│   ├── Makefile                      # Build system
│   └── CMakeLists.txt                # CMake configuration
├── tests/
│   ├── __init__.py
│   ├── test_data_driven_tectonics.py # Comprehensive test suite
│   └── test_enhanced_model.py        # Enhanced Model tests
└── examples/
    ├── __init__.py
    ├── data_driven_tectonics_basic.py    # DataDrivenTectonics basic usage
    ├── data_driven_tectonics_advanced.py # DataDrivenTectonics advanced features
    ├── enhanced_model_basic.py           # EnhancedModel basic usage
    ├── enhanced_model_advanced.py        # EnhancedModel with elevation tracking
    ├── velocity_data.csv             # Sample velocity data
    └── input-escarpment.yml          # Working goSPL config
```

## Dependencies

### Required Python Packages
- `numpy`: Numerical computations
- `scipy`: Spatial indexing and interpolation

### Optional Python Packages
- `pytest`: For running the full test suite
- `pandas`: For CSV data loading in examples
- `matplotlib`: For visualization in examples

## Contributing

To contribute to this extension:

1. Clone the repository
2. Install in development mode: `pip install -e ".[dev]"`
3. Run tests: `pytest tests/` or `python run_tests.py`
4. Make your changes and ensure tests pass
5. Add tests for new functionality

## Acknowledgments

This extension was developed with assistance from GitHub Copilot, an AI-powered coding assistant. The comprehensive test suite, documentation, examples, and project structure were collaboratively created to ensure robustness and usability.
