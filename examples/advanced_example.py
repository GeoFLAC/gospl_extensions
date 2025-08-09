#!/usr/bin/env python3
"""
Advanced example showing time-dependent tectonics with DataDrivenTectonics.

IMPORTANT: This example requires the 'gospl' conda environment to be activated:
    conda activate gospl

This example demonstrates:
1. Loading velocity data from files (CSV format)
2. Time-dependent velocity fields
3. Different interpolation parameters
4. Monitoring the effects of applied velocities
"""

import numpy as np
import pandas as pd
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from gospl.model import Model
    from gospl_tectonics_ext import DataDrivenTectonics
    print("Successfully imported goSPL and DataDrivenTectonics")
except ImportError as e:
    print(f"Import error: {e}")
    print("This example requires goSPL to be installed and importable.")
    print("Please ensure you have:")
    print("1. Activated the gospl conda environment: conda activate gospl")
    print("2. Installed goSPL in that environment")
    sys.exit(1)


def load_velocity_data_from_csv(filename):
    """
    Load velocity data from a CSV file.
    
    Expected CSV format:
    x,y,z,vx,vy,vz
    0.0,0.0,0.0,0.1,0.0,0.05
    1.0,0.0,0.0,0.0,0.1,0.0
    ...
    
    Args:
        filename: Path to CSV file
    
    Returns:
        dict with 'coords' and 'vel' arrays
    """
    try:
        data = pd.read_csv(filename)
        
        # Extract coordinates and velocities
        coords = data[['x', 'y', 'z']].values
        vel = data[['vx', 'vy', 'vz']].values
        
        print(f"Loaded {len(coords)} velocity samples from {filename}")
        return {
            "coords": coords,
            "vel": vel
        }
    except Exception as e:
        print(f"Error loading velocity data from {filename}: {e}")
        return None


def create_time_dependent_velocity_field(t, n_points=100, domain_size=10.0):
    """
    Create a time-dependent synthetic velocity field.
    
    Args:
        t: Time value
        n_points: Number of velocity sampling points
        domain_size: Size of the square domain
    
    Returns:
        dict with 'coords' and 'vel' arrays
    """
    # Create fixed sampling points (same locations for each time)
    np.random.seed(42)  # For reproducible results
    coords = np.random.uniform(0, domain_size, size=(n_points, 3))
    coords[:, 2] = 0.0
    
    # Time-dependent velocity field
    center_x, center_y = domain_size / 2, domain_size / 2
    dx = coords[:, 0] - center_x
    dy = coords[:, 1] - center_y
    
    # Rotating velocity field with time-dependent amplitude
    amplitude = 0.1 * (1.0 + 0.5 * np.sin(t * 0.1))
    vx = -dy * amplitude
    vy = dx * amplitude
    
    # Time-dependent vertical motion
    vz = np.sin(coords[:, 0] / domain_size * np.pi + t * 0.05) * 0.02
    
    vel = np.column_stack([vx, vy, vz])
    
    return {
        "coords": coords,
        "vel": vel
    }


def compare_interpolation_methods(model, veldata):
    """
    Compare different interpolation parameters and their effects.
    
    Args:
        model: goSPL model instance
        veldata: Velocity data dictionary
    """
    print("\nComparing interpolation methods:")
    print("-" * 40)
    
    # Test different k values (number of neighbors)
    k_values = [1, 3, 5, 10]
    for k in k_values:
        print(f"Testing k={k} neighbors...")
        model.apply_velocity_data(veldata, k=k, power=1.0)
        
        # You could analyze the resulting velocity field here
        max_vel = np.max(np.linalg.norm(model.hdisp, axis=1))
        print(f"  Max interpolated velocity magnitude: {max_vel:.6f}")
    
    # Test different power values
    power_values = [0.5, 1.0, 2.0]
    for power in power_values:
        print(f"Testing power={power}...")
        model.apply_velocity_data(veldata, k=3, power=power)
        
        max_vel = np.max(np.linalg.norm(model.hdisp, axis=1))
        print(f"  Max interpolated velocity magnitude: {max_vel:.6f}")


def run_time_dependent_simulation(model, duration=10.0, dt=1.0):
    """
    Run a time-dependent simulation with evolving velocity fields.
    
    Args:
        model: goSPL model instance
        duration: Total simulation time
        dt: Time step
    """
    print(f"\nRunning time-dependent simulation for {duration} time units")
    print("-" * 50)
    
    current_time = 0.0
    step = 0
    
    while current_time < duration:
        print(f"Step {step}, Time: {current_time:.1f}")
        
        # Generate time-dependent velocity field
        veldata = create_time_dependent_velocity_field(
            current_time, n_points=75, domain_size=10.0
        )
        
        # Apply velocities to model
        model.apply_velocity_data(veldata, timer=dt, k=3, power=1.0)
        
        # Run one step of the model
        # In a real simulation, you would call:
        # model.runProcesses()
        
        # Monitor some properties
        if hasattr(model, 'hdisp'):
            max_vel = np.max(np.linalg.norm(model.hdisp, axis=1))
            mean_vel = np.mean(np.linalg.norm(model.hdisp, axis=1))
            print(f"  Velocity stats - Max: {max_vel:.6f}, Mean: {mean_vel:.6f}")
        
        current_time += dt
        step += 1
    
    print("Simulation completed!")


def main():
    """Main advanced example function."""
    print("DataDrivenTectonics Advanced Example")
    print("=" * 45)
    
    input_file = "input-escarpment.yml"  # Real goSPL input file with mesh data
    
    try:
        # Initialize goSPL model
        print(f"Initializing goSPL model with {input_file}")
        model = Model(input_file, verbose=True)
        
        # Bind the DataDrivenTectonics method
        model.apply_velocity_data = DataDrivenTectonics.apply_velocity_data.__get__(
            model, type(model)
        )
        
        # Example 1: Load velocity data from CSV (if available)
        csv_file = "velocity_data.csv"
        if os.path.exists(csv_file):
            print(f"\nExample 1: Loading velocity data from {csv_file}")
            veldata = load_velocity_data_from_csv(csv_file)
            if veldata:
                model.apply_velocity_data(veldata, k=3, power=1.0)
                print("Successfully applied CSV velocity data")
        else:
            print(f"\nNote: {csv_file} not found, skipping CSV example")
        
        # Example 2: Compare interpolation methods
        print("\nExample 2: Comparing interpolation methods")
        synthetic_data = create_time_dependent_velocity_field(0.0, n_points=50)
        compare_interpolation_methods(model, synthetic_data)
        
        # Example 3: Time-dependent simulation
        print("\nExample 3: Time-dependent velocity simulation")
        run_time_dependent_simulation(model, duration=5.0, dt=1.0)
        
    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_file}'")
        print("Please create a goSPL input file or modify the path in this script.")
        return
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure goSPL is properly installed and the input file is valid.")
        return


if __name__ == "__main__":
    main()
