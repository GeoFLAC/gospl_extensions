#!/usr/bin/env python3
"""
Enhanced Model example showing time-stepping control with EnhancedModel.

IMPORTANT: This example requires the 'gospl' conda environment to be activated:
    conda activate gospl

This example demonstrates:
1. Using EnhancedModel for granular time control
2. Running processes for specific dt intervals
3. Combining with DataDrivenTectonics for controlled simulations
4. Monitoring simulation progress step by step
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
    x = np.linspace(0, 10, 10)
    y = np.linspace(0, 10, 10)
    X, Y = np.meshgrid(x, y)
    
    coords = np.column_stack([X.flatten(), Y.flatten(), np.zeros(X.size)])
    
    # Create rotational velocity field that changes with time
    cx, cy = domain_center
    dx = coords[:, 0] - cx
    dy = coords[:, 1] - cy
    
    # Time-dependent rotation
    omega = 0.1 * np.sin(t * 0.1)  # Angular velocity varies with time
    vx = -dy * omega * amplitude
    vy = dx * omega * amplitude
    vz = 0.01 * np.sin(coords[:, 0] + t * 0.05) * amplitude
    
    vel = np.column_stack([vx, vy, vz])
    
    return {
        "coords": coords,
        "vel": vel
    }


def run_controlled_simulation(model, duration=10.0, dt=1.0):
    """
    Run a controlled simulation with time-dependent tectonics and granular time control.
    
    Args:
        model: EnhancedModel instance
        duration: Total simulation duration
        dt: Time step size
    """
    print(f"\nRunning controlled simulation for {duration} time units with dt={dt}")
    print("=" * 60)
    
    start_time = model.tNow
    target_time = start_time + duration
    step = 0
    
    # Apply time-dependent velocities and run step by step
    while model.tNow < target_time:
        current_time = model.tNow
        remaining_time = target_time - current_time
        step_dt = min(dt, remaining_time)
        
        print(f"\nStep {step + 1}: t={current_time:.2f} -> {current_time + step_dt:.2f}")
        
        # Generate time-dependent velocity field
        veldata = create_velocity_field(current_time)
        print(f"  Generated velocity field for t={current_time:.2f}")
        
        # Apply velocities using DataDrivenTectonics
        model.apply_velocity_data(veldata, timer=step_dt, k=3, power=1.0)
        print(f"  Applied velocity data with timer={step_dt}")
        
        # Run processes for this specific time step
        elapsed = model.runProcessesForDt(step_dt, verbose=True)
        print(f"  Completed step in {elapsed:.2f}s")
        
        # Monitor some properties
        if hasattr(model, 'hdisp'):
            max_vel = np.max(np.linalg.norm(model.hdisp, axis=1))
            mean_vel = np.mean(np.linalg.norm(model.hdisp, axis=1))
            print(f"  Velocity stats - Max: {max_vel:.6f}, Mean: {mean_vel:.6f}")
        
        step += 1
    
    total_time = model.tNow - start_time
    print(f"\n✓ Simulation completed! Ran for {total_time:.2f} time units in {step} steps")


def demonstrate_enhanced_model_methods(model):
    """
    Demonstrate different methods available in EnhancedModel.
    
    Args:
        model: EnhancedModel instance
    """
    print("\nDemonstrating EnhancedModel methods:")
    print("=" * 50)
    
    initial_time = model.tNow
    
    # Method 1: Run for specific number of steps
    print(f"\n1. Running 3 steps with dt=0.5")
    elapsed_times = model.runProcessesForSteps(num_steps=3, dt=0.5, verbose=True)
    print(f"   Step durations: {[f'{t:.2f}s' for t in elapsed_times]}")
    
    # Method 2: Run until specific time
    target_time = model.tNow + 2.0
    print(f"\n2. Running until t={target_time}")
    elapsed_times = model.runProcessesUntilTime(target_time, dt=0.75, verbose=True)
    print(f"   Step durations: {[f'{t:.2f}s' for t in elapsed_times]}")
    
    total_time = model.tNow - initial_time
    print(f"\n✓ Enhanced model methods demo completed! Total time advanced: {total_time:.2f}")


def main():
    """Main enhanced model example function."""
    print("EnhancedModel Example: Granular Time Control")
    print("=" * 55)
    
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
        
        print(f"Model initialized at t={model.tNow}, dt={model.dt}")
        
        # Demonstrate enhanced model methods
        demonstrate_enhanced_model_methods(model)
        
        # Run controlled simulation with time-dependent tectonics
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
