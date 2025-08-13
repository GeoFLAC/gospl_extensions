# gospl_extensions

1. `gospl_tectonics_ext` - Data-driven tectonics extension
2. `gospl_model_ext` - Enhanced model with granular time control

## gospl_tectonics_ext: Data-driven tectonics for goSPL

This out-of-tree extension adds a way to drive horizontal and vertical tectonic velocities from an external dataset (positions + 3-component velocities) whose sampling points don’t coincide with the model mesh. Velocities are interpolated to mesh nodes via k-nearest-neighbor inverse-distance weighting and then applied using goSPL’s existing advection machinery.

- Core goSPL code remains untouched.
- Import path: `from gospl_tectonics_ext import DataDrivenTectonics`.

### Prerequisites

**Important**: This extension requires the `gospl` conda environment to be activated:

```bash
conda activate gospl
```

The extension depends on goSPL and its Fortran extensions, which are typically installed via conda.

### Install or make importable

Option A — Add to PYTHONPATH (quickest):
- Activate the gospl conda environment: `conda activate gospl`
- Ensure `path/to/gospl_extensions` is on PYTHONPATH so Python can find `gospl_tectonics_ext`.

Option B — Editable install (recommended):
- Activate the gospl conda environment: `conda activate gospl`
- Use the provided `pyproject.toml` and run an editable install.

### Usage

```python
from gospl.model import Model
from gospl_tectonics_ext import DataDrivenTectonics

m = Model("input.yml", verbose=True)

# Bind the method to this instance without modifying Model inheritance
m.apply_velocity_data = DataDrivenTectonics.apply_velocity_data.__get__(m, type(m))

veldata = {
    "coords": coords_np_array,  # shape (N, 3)
    "vel":    vel_np_array,     # shape (N, 3)
}

# Interpolate and apply external velocities
m.apply_velocity_data(veldata, timer=None, k=3, power=1.0)
```

Behavior by advection scheme:
- advscheme == 0 (semi-Lagrangian): builds interpolation to advected positions and schedules plate advection at `tNow + timer`.
- advscheme > 0 (finite-volume IIOE/upwind): computes face velocities and advects immediately.

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
# Activate the gospl conda environment first
conda activate gospl

# Run tests using pytest (recommended)
pytest tests/

# Or use the built-in test runner (no pytest required)
python run_tests.py
```

Test coverage includes:
- Input validation and error handling
- Interpolation accuracy with different parameters
- Both advection schemes (semi-Lagrangian and finite-volume)
- Edge cases (coincident nodes, empty data, etc.)
- Mock testing that doesn't require goSPL installation

### Examples

Several example scripts demonstrate different use cases:

#### Basic Example
```bash
# Activate the gospl conda environment
conda activate gospl

cd examples
python basic_example.py
```
Shows basic usage with synthetic velocity data.

#### Advanced Example
```bash
# Activate the gospl conda environment
conda activate gospl

cd examples
python advanced_example.py
```
Demonstrates:
- Loading velocity data from CSV files
- Time-dependent velocity fields
- Comparing interpolation parameters
- Monitoring velocity field effects

#### Sample Data
- `examples/velocity_data.csv`: Sample velocity data for testing
- `examples/input.yml`: Template goSPL configuration file

### Packaging (optional)
A `pyproject.toml` is included for proper Python packaging. To install in editable mode:

```bash
# Activate the gospl conda environment first
conda activate gospl

pip install -e path/to/gospl_extensions
```

This will also install required dependencies (numpy, scipy) and make the extension importable from anywhere.

#### Development Installation
For development with testing dependencies:

```bash
# Activate the gospl conda environment first
conda activate gospl

pip install -e "path/to/gospl_extensions[dev]"
```

After this, `from gospl_tectonics_ext import DataDrivenTectonics` will work from anywhere.

## gospl_model_ext: Enhanced Model with Granular Time Control

This extension provides an `EnhancedModel` class that extends the goSPL `Model` class with additional methods for granular time control.

### Prerequisites

**Important**: This extension requires the `gospl` conda environment to be activated:

```bash
conda activate gospl
```

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

```bash
# Activate the gospl conda environment
conda activate gospl

cd examples
python enhanced_model_example.py
```

Shows controlled time-stepping with the EnhancedModel class, including demonstrations of all three new methods.

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
├── tests/
│   ├── __init__.py
│   ├── test_data_driven_tectonics.py # Comprehensive test suite
│   └── test_enhanced_model.py        # Enhanced Model tests
└── examples/
    ├── __init__.py
    ├── basic_example.py              # Basic usage example
    ├── advanced_example.py           # Advanced features example
    ├── enhanced_model_example.py     # Enhanced Model example
    ├── velocity_data.csv             # Sample velocity data
    └── input.yml                     # Template goSPL config
```

## Dependencies

### Environment Requirements
- **Conda environment**: Must activate the `gospl` conda environment before using this extension
- **goSPL**: The main landscape evolution model with Fortran extensions

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
2. Activate the gospl conda environment: `conda activate gospl`
3. Install in development mode: `pip install -e ".[dev]"`
4. Run tests: `pytest tests/` or `python run_tests.py`
5. Make your changes and ensure tests pass
6. Add tests for new functionality

## Acknowledgments

This extension was developed with assistance from GitHub Copilot, an AI-powered coding assistant. The comprehensive test suite, documentation, examples, and project structure were collaboratively created to ensure robustness and usability.
