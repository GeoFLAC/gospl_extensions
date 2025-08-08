# gospl_tectonics_ext: Data-driven tectonics for goSPL

This out-of-tree extension adds a way to drive horizontal and vertical tectonic velocities from an external dataset (positions + 3-component velocities) whose sampling points don’t coincide with the model mesh. Velocities are interpolated to mesh nodes via k-nearest-neighbor inverse-distance weighting and then applied using goSPL’s existing advection machinery.

- Core goSPL code remains untouched.
- Import path: `from gospl_tectonics_ext import DataDrivenTectonics`.

## Install or make importable

Option A — Add to PYTHONPATH (quickest):
- Ensure `/home/eunseo/opt` is on PYTHONPATH so Python can find `gospl_tectonics_ext`.

Option B — Editable install (recommended):
- Use the provided `pyproject.toml` and run an editable install.

## Usage

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

## Files
- `gospl_tectonics_ext/data_driven_tectonics.py`: the extension implementation.
- `gospl_tectonics_ext/__init__.py`: re-exports `DataDrivenTectonics`.

## Packaging (optional)
A minimal `pyproject.toml` is included. To install in editable mode:

```bash
pip install -e /home/eunseo/opt/gospl_tectonics_ext
```

After this, `from gospl_tectonics_ext import DataDrivenTectonics` will work from anywhere.
