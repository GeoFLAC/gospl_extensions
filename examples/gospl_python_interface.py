"""
Python C API wrapper for gospl_extensions to be used from C++.

This module provides C-compatible functions that can be called from C++ code
to interface with the EnhancedModel and DataDrivenTectonics extensions.
"""

import ctypes
import numpy as np
import sys
import os
from ctypes import c_double, c_int, c_char_p, c_void_p, POINTER, Structure

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from gospl_model_ext import EnhancedModel
    from gospl_tectonics_ext import DataDrivenTectonics
    print("Successfully imported gospl extensions for C++ interface")
except ImportError as e:
    print(f"Failed to import gospl extensions: {e}")
    sys.exit(1)


# Global storage for model instances (indexed by handle)
_models = {}
_next_handle = 1


class VelocityData(Structure):
    """C structure for velocity data"""
    _fields_ = [
        ('coords', POINTER(c_double)),
        ('velocities', POINTER(c_double)),
        ('num_points', c_int),
    ]


def create_enhanced_model(config_path: str) -> int:
    """
    Create an EnhancedModel instance and return a handle to it.
    
    Args:
        config_path: Path to goSPL configuration file
        
    Returns:
        Handle (integer) to the model instance
    """
    global _models, _next_handle
    
    try:
        # Create enhanced model
        model = EnhancedModel(config_path.decode() if isinstance(config_path, bytes) else config_path)
        
        # Bind DataDrivenTectonics methods
        model.apply_velocity_data = DataDrivenTectonics.apply_velocity_data.__get__(
            model, type(model)
        )
        model.interpolate_elevation_to_points = DataDrivenTectonics.interpolate_elevation_to_points.__get__(
            model, type(model)
        )
        
        # Store model and return handle
        handle = _next_handle
        _models[handle] = model
        _next_handle += 1
        
        return handle
        
    except Exception as e:
        print(f"Error creating enhanced model: {e}")
        return -1


def destroy_model(handle: int) -> int:
    """
    Destroy a model instance.
    
    Args:
        handle: Model handle
        
    Returns:
        0 on success, -1 on error
    """
    global _models
    
    try:
        if handle in _models:
            # Clean up model if needed
            model = _models[handle]
            if hasattr(model, 'destroy'):
                model.destroy()
            del _models[handle]
            return 0
        else:
            return -1
    except Exception:
        return -1


def run_processes_for_dt(handle: int, dt: float, verbose: bool = False) -> float:
    """
    Run processes for a specific time step.
    
    Args:
        handle: Model handle
        dt: Time step size
        verbose: Print progress information
        
    Returns:
        Elapsed time, or -1.0 on error
    """
    global _models
    
    try:
        if handle not in _models:
            return -1.0
            
        model = _models[handle]
        elapsed = model.runProcessesForDt(dt, verbose)
        return elapsed
        
    except Exception as e:
        print(f"Error in run_processes_for_dt: {e}")
        return -1.0


def run_processes_for_steps(handle: int, num_steps: int, dt: float, verbose: bool = False) -> int:
    """
    Run processes for a specified number of steps.
    
    Args:
        handle: Model handle
        num_steps: Number of steps to run
        dt: Time step size
        verbose: Print progress information
        
    Returns:
        Number of steps completed, or -1 on error
    """
    global _models
    
    try:
        if handle not in _models:
            return -1
            
        model = _models[handle]
        elapsed_times = model.runProcessesForSteps(num_steps, dt, verbose)
        return len(elapsed_times)
        
    except Exception as e:
        print(f"Error in run_processes_for_steps: {e}")
        return -1


def run_processes_until_time(handle: int, target_time: float, dt: float, verbose: bool = False) -> int:
    """
    Run processes until target time is reached.
    
    Args:
        handle: Model handle
        target_time: Target simulation time
        dt: Time step size
        verbose: Print progress information
        
    Returns:
        Number of steps completed, or -1 on error
    """
    global _models
    
    try:
        if handle not in _models:
            return -1
            
        model = _models[handle]
        elapsed_times = model.runProcessesUntilTime(target_time, dt, verbose)
        return len(elapsed_times)
        
    except Exception as e:
        print(f"Error in run_processes_until_time: {e}")
        return -1


def apply_velocity_data(handle: int, coords, velocities, 
                       num_points: int, timer: float, k: int = 3, power: float = 1.0) -> int:
    """
    Apply velocity data to the model.
    
    Args:
        handle: Model handle
        coords: Coordinates array (num_points * 3)
        velocities: Velocities array (num_points * 3)  
        num_points: Number of data points
        timer: Time for velocity application
        k: Number of nearest neighbors
        power: Inverse distance weighting power
        
    Returns:
        0 on success, -1 on error
    """
    global _models
    
    try:
        if handle not in _models:
            return -1
            
        model = _models[handle]
        
        # Convert to numpy arrays if not already
        coords_array = np.array(coords).reshape(num_points, 3)
        vel_array = np.array(velocities).reshape(num_points, 3)
        
        # Create velocity data dictionary
        veldata = {
            "coords": coords_array,
            "vel": vel_array
        }
        
        # Apply velocity data
        model.apply_velocity_data(veldata, timer=timer, k=k, power=power)
        return 0
        
    except Exception as e:
        print(f"Error in apply_velocity_data: {e}")
        return -1


def get_current_time(handle: int) -> float:
    """
    Get current simulation time.
    
    Args:
        handle: Model handle
        
    Returns:
        Current time, or -1.0 on error
    """
    global _models
    
    try:
        if handle not in _models:
            return -1.0
            
        model = _models[handle]
        return model.tNow
        
    except Exception:
        return -1.0


def get_time_step(handle: int) -> float:
    """
    Get model time step.
    
    Args:
        handle: Model handle
        
    Returns:
        Time step, or -1.0 on error
    """
    global _models
    
    try:
        if handle not in _models:
            return -1.0
            
        model = _models[handle]
        return model.dt
        
    except Exception:
        return -1.0


def interpolate_elevation_to_points(handle: int, coords, k: int = 3, power: float = 1.0):
    """
    Interpolate elevation field to external points.
    
    Args:
        handle: Model handle
        coords: Coordinates array (num_points * 3)
        k: Number of nearest neighbors
        power: Inverse distance weighting power
        
    Returns:
        Numpy array of interpolated elevations, or None on error
    """
    global _models
    
    try:
        if handle not in _models:
            return None
            
        model = _models[handle]
        
        # Convert to numpy array if not already
        coords_array = np.array(coords)
        if coords_array.ndim == 1:
            # Assume it's flattened, reshape to (N, 3)
            num_points = len(coords_array) // 3
            coords_array = coords_array.reshape(num_points, 3)
        
        # Interpolate elevations
        elevations = model.interpolate_elevation_to_points(coords_array, k=k, power=power)
        return elevations
        
    except Exception as e:
        print(f"Error in interpolate_elevation_to_points: {e}")
        return None


# C-compatible function exports using ctypes
def export_c_functions():
    """Export functions with C-compatible signatures"""
    
    # Function signatures for C compatibility
    create_enhanced_model.argtypes = [c_char_p]
    create_enhanced_model.restype = c_int
    
    destroy_model.argtypes = [c_int]
    destroy_model.restype = c_int
    
    run_processes_for_dt.argtypes = [c_int, c_double, c_int]
    run_processes_for_dt.restype = c_double
    
    run_processes_for_steps.argtypes = [c_int, c_int, c_double, c_int]
    run_processes_for_steps.restype = c_int
    
    run_processes_until_time.argtypes = [c_int, c_double, c_double, c_int]
    run_processes_until_time.restype = c_int
    
    apply_velocity_data.argtypes = [c_int, POINTER(c_double), POINTER(c_double), 
                                   c_int, c_double, c_int, c_double]
    apply_velocity_data.restype = c_int
    
    interpolate_elevation_to_points.argtypes = [c_int, POINTER(c_double), c_int, c_double]
    interpolate_elevation_to_points.restype = POINTER(c_double)
    
    get_current_time.argtypes = [c_int]
    get_current_time.restype = c_double
    
    get_time_step.argtypes = [c_int]
    get_time_step.restype = c_double


if __name__ == "__main__":
    export_c_functions()
    print("gospl_extensions C API interface ready")
