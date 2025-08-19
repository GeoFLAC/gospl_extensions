#!/usr/bin/env python3
"""
Advanced Enhanced Model example showing elevation tracking and updating.

IMPORTANT: This example requires the 'gospl' conda environment to be activated:
    conda activate gospl

This example demonstrates:
1. Using EnhancedModel for granular time control
2. Tracking elevation changes at velocity sampling points
3. Updating velocity coordinates based on evolving topography
4. Comparing elevation changes before and after each time step
5. Advanced coupling between tectonics and topographic evolution
"""

import numpy as np
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from gospl.model import Model
    from gospl_tectonics_ext import DataDrivenTectonics
    from gospl_model_ext import EnhancedModel
    print("Successfully imported goSPL, DataDrivenTectonics, and EnhancedModel")
except ImportError as e:
    print(f"Import error: {e}")
    print("This example requires goSPL to be installed and importable.")
    print("Please ensure you have:")
    print("1. Activated the gospl conda environment: conda activate gospl")
    print("2. Installed goSPL in that environment")
    sys.exit(1)


def create_velocity_field(t, domain_center=(5.0, 5.0), amplitude=0.1):
    """
    Create a time-dependent rotational velocity field.

    Args:
        t: Time value
        domain_center: Center of rotation
        amplitude: Velocity amplitude

    Returns:
        dict with 'coords' and 'vel' arrays
    """
    # Create a grid of velocity sampling points
    x = np.linspace(1, 9, 8)  # Avoid domain edges for better interpolation
    y = np.linspace(1, 9, 8)
    X, Y = np.meshgrid(x, y)

    coords = np.column_stack([X.flatten(), Y.flatten(), np.zeros(X.size)])

    # Create rotational velocity field that changes with time
    cx, cy = domain_center
    dx = coords[:, 0] - cx
    dy = coords[:, 1] - cy

    # Time-dependent rotation with varying amplitude
    omega = 0.1 * (1.0 + 0.5 * np.sin(t * 0.1))  # Angular velocity varies with time
    vx = -dy * omega * amplitude
    vy = dx * omega * amplitude
    vz = 0.01 * np.sin(coords[:, 0] + t * 0.05) * amplitude

    vel = np.column_stack([vx, vy, vz])

    return {
        "coords": coords,
        "vel": vel
    }


def analyze_elevation_changes(z_before, z_after, step_info=""):
    """
    Analyze and report elevation changes.
    
    Args:
        z_before: Elevation values before the step
        z_after: Elevation values after the step
        step_info: Additional information about the step
    """
    elevation_change = z_after - z_before
    
    print(f"  Elevation Analysis{step_info}:")
    print(f"    Before - Min: {np.min(z_before):.6f}, Max: {np.max(z_before):.6f}, Mean: {np.mean(z_before):.6f}")
    print(f"    After  - Min: {np.min(z_after):.6f}, Max: {np.max(z_after):.6f}, Mean: {np.mean(z_after):.6f}")
    print(f"    Change - Min: {np.min(elevation_change):.6f}, Max: {np.max(elevation_change):.6f}, Mean: {np.mean(elevation_change):.6f}")
    print(f"    RMS change: {np.sqrt(np.mean(elevation_change**2)):.6f}")
    
    # Find points with significant changes
    significant_threshold = np.std(elevation_change) * 2
    significant_changes = np.abs(elevation_change) > significant_threshold
    if np.any(significant_changes):
        n_significant = np.sum(significant_changes)
        print(f"    Points with significant change (>{significant_threshold:.6f}): {n_significant}/{len(elevation_change)}")


def run_controlled_simulation(model, duration=10.0, dt=1.0):
    """
    Run a controlled simulation with elevation tracking and coordinate updating.

    Args:
        model: EnhancedModel instance
        duration: Total simulation duration
        dt: Time step size
    """
    print(f"\nRunning controlled simulation with elevation tracking")
    print(f"Duration: {duration} time units, dt: {dt}")
    print("=" * 70)

    start_time = model.tNow
    target_time = start_time + duration
    step = 0

    # Initialize velocity field
    veldata = create_velocity_field(start_time)
    
    # Get initial elevations at velocity sampling points
    initial_elevations = model.interpolate_elevation_to_points(
        veldata['coords'], k=5, power=1.0
    )
    print(f"Initial elevation stats:")
    print(f"  Min: {np.min(initial_elevations):.6f}")
    print(f"  Max: {np.max(initial_elevations):.6f}")
    print(f"  Mean: {np.mean(initial_elevations):.6f}")
    
    # Store elevation history
    elevation_history = [initial_elevations.copy()]
    time_history = [start_time]

    # Apply time-dependent velocities and run step by step
    while model.tNow < target_time:
        current_time = model.tNow
        remaining_time = target_time - current_time
        step_dt = min(dt, remaining_time)

        print(f"\nStep {step + 1}: t={current_time:.2f} -> {current_time + step_dt:.2f}")

        # Store elevation before this step
        z_before = veldata['coords'][:, 2].copy()
        
        # Generate time-dependent velocity field (keeping x,y coordinates, updating z)
        new_veldata = create_velocity_field(current_time)
        veldata['vel'] = new_veldata['vel']  # Update velocities
        # Keep existing coordinates (including updated z from previous step)
        
        print(f"  Generated velocity field for t={current_time:.2f}")

        # Apply velocities using DataDrivenTectonics
        model.apply_velocity_data(veldata, timer=step_dt, k=3, power=1.0)
        print(f"  Applied velocity data with timer={step_dt}")

        # Run processes for this specific time step
        elapsed = model.runProcessesForDt(step_dt, verbose=True)
        print(f"  Completed step in {elapsed:.2f}s")

        # NOW: Interpolate current elevation field to velocity sampling points
        current_elevations = model.interpolate_elevation_to_points(
            veldata['coords'], k=5, power=1.0
        )
        
        # Update z coordinates of velocity sampling points with new elevations
        veldata['coords'][:, 2] = current_elevations
        z_after = current_elevations.copy()
        
        # Analyze elevation changes
        analyze_elevation_changes(z_before, z_after, f" (Step {step + 1})")
        
        # Store elevation history
        elevation_history.append(current_elevations.copy())
        time_history.append(model.tNow)

        # Monitor velocity properties
        if hasattr(model, 'hdisp'):
            max_vel = np.max(np.linalg.norm(model.hdisp, axis=1))
            mean_vel = np.mean(np.linalg.norm(model.hdisp, axis=1))
            print(f"  Velocity stats - Max: {max_vel:.6f}, Mean: {mean_vel:.6f}")

        step += 1

    # Final analysis
    print(f"\n" + "="*70)
    print("FINAL ELEVATION ANALYSIS")
    print("="*70)
    
    final_elevations = elevation_history[-1]
    total_change = final_elevations - elevation_history[0]
    
    print(f"Total simulation time: {model.tNow - start_time:.2f} time units")
    print(f"Number of steps: {step}")
    
    analyze_elevation_changes(elevation_history[0], final_elevations, " (Total)")
    
    # Analyze elevation evolution over time
    print(f"\nElevation Evolution Summary:")
    for i, (t, elevs) in enumerate(zip(time_history, elevation_history)):
        mean_elev = np.mean(elevs)
        if i == 0:
            print(f"  t={t:.2f}: Mean elevation = {mean_elev:.6f} (initial)")
        else:
            change_from_prev = np.mean(elevs - elevation_history[i-1])
            print(f"  t={t:.2f}: Mean elevation = {mean_elev:.6f} (Δ={change_from_prev:+.6f})")
    
    print(f"\n✓ Simulation completed! Ran for {model.tNow - start_time:.2f} time units in {step} steps")


def demonstrate_elevation_interpolation(model):
    """
    Demonstrate elevation interpolation capabilities.
    
    Args:
        model: EnhancedModel instance
    """
    print("\nDemonstrating elevation interpolation:")
    print("=" * 50)
    
    # Create test points across the domain
    x_test = np.linspace(0, 10, 11)
    y_test = np.linspace(0, 10, 11)
    X_test, Y_test = np.meshgrid(x_test, y_test)
    test_points = np.column_stack([X_test.flatten(), Y_test.flatten(), np.zeros(X_test.size)])
    
    print(f"Interpolating elevation at {len(test_points)} test points")
    
    # Test different interpolation parameters
    for k in [1, 3, 5]:
        elevations = model.interpolate_elevation_to_points(test_points, k=k, power=1.0)
        print(f"  k={k}: Min={np.min(elevations):.6f}, Max={np.max(elevations):.6f}, Mean={np.mean(elevations):.6f}")
    
    for power in [0.5, 1.0, 2.0]:
        elevations = model.interpolate_elevation_to_points(test_points, k=3, power=power)
        print(f"  power={power}: Min={np.min(elevations):.6f}, Max={np.max(elevations):.6f}, Mean={np.mean(elevations):.6f}")


def main():
    """Main advanced enhanced model example function."""
    print("Advanced EnhancedModel Example: Elevation Tracking & Updating")
    print("=" * 65)

    input_file = "input-escarpment.yml"

    try:
        # Initialize enhanced model
        print(f"Initializing EnhancedModel with {input_file}")
        model = EnhancedModel(input_file, verbose=True)

        # Bind DataDrivenTectonics methods to the enhanced model
        print("Binding DataDrivenTectonics methods to EnhancedModel")
        model.apply_velocity_data = DataDrivenTectonics.apply_velocity_data.__get__(
            model, type(model)
        )
        model.interpolate_elevation_to_points = DataDrivenTectonics.interpolate_elevation_to_points.__get__(
            model, type(model)
        )

        print(f"Model initialized at t={model.tNow}, dt={model.dt}")

        # Demonstrate elevation interpolation
        demonstrate_elevation_interpolation(model)

        # Run controlled simulation with elevation tracking
        run_controlled_simulation(model, duration=5.0, dt=1.0)

        print(f"\n🎉 All demonstrations completed successfully!")
        print(f"Final simulation time: t={model.tNow}")

    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_file}'")
        print("Please ensure the input file exists in the examples directory.")
        return
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("Make sure goSPL is properly installed and the input file is valid.")
        return


if __name__ == "__main__":
    main()