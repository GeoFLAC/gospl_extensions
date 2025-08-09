#!/usr/bin/env python3
"""
Basic example of using DataDrivenTectonics with synthetic data.

IMPORTANT: This example requires the 'gospl' conda environment to be activated:
    conda activate gospl

This example shows how to:
1. Create a simple goSPL model
2. Generate synthetic velocity data
3. Apply external velocities using DataDrivenTectonics
"""

import numpy as np
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


def create_synthetic_velocity_data(n_points=100, domain_size=10.0):
    """
    Create synthetic velocity data for testing.
    
    Args:
        n_points: Number of velocity sampling points
        domain_size: Size of the square domain
    
    Returns:
        dict with 'coords' and 'vel' arrays
    """
    # Create random sampling points
    coords = np.random.uniform(0, domain_size, size=(n_points, 3))
    coords[:, 2] = 0.0  # Keep z=0 for 2D case
    
    # Create synthetic velocity field (simple rotation + vertical motion)
    center_x, center_y = domain_size / 2, domain_size / 2
    dx = coords[:, 0] - center_x
    dy = coords[:, 1] - center_y
    
    # Rotational velocity field
    vx = -dy * 0.1  # Angular velocity
    vy = dx * 0.1
    vz = np.sin(coords[:, 0] / domain_size * np.pi) * 0.05  # Vertical oscillation
    
    vel = np.column_stack([vx, vy, vz])
    
    return {
        "coords": coords,
        "vel": vel
    }


def main():
    """Main example function."""
    print("DataDrivenTectonics Basic Example")
    print("=" * 40)
    
    # Note: This example uses a real goSPL input file from the escarpment retreat example
    input_file = "input-escarpment.yml"  # Real goSPL input file with mesh data
    
    try:
        # Initialize goSPL model
        print(f"Initializing goSPL model with {input_file}")
        model = Model(input_file, verbose=True)
        
        # Bind the DataDrivenTectonics method to the model instance
        print("Binding DataDrivenTectonics method to model")
        model.apply_velocity_data = DataDrivenTectonics.apply_velocity_data.__get__(
            model, type(model)
        )
        
        # Create synthetic velocity data
        print("Creating synthetic velocity data...")
        veldata = create_synthetic_velocity_data(n_points=50, domain_size=10.0)
        print(f"Created {veldata['coords'].shape[0]} velocity samples")
        
        # Apply the external velocities
        print("Applying external velocity data to model...")
        model.apply_velocity_data(
            veldata, 
            timer=None,    # Use model's default time step
            k=3,           # Use 3 nearest neighbors
            power=1.0      # Linear inverse distance weighting
        )
        
        print("Successfully applied external velocities!")
        print(f"Model now has interpolated velocities at mesh nodes")
        
        # You can now run your goSPL simulation as usual
        # model.runProcesses()  # Run one time step
        
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
