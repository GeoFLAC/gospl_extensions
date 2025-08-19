#!/usr/bin/env python3
"""
Test runner script for gospl_extensions.

This script can be used to run tests without requiring pytest to be installed
in the system. It provides a simple way to validate the functionality of
DataDrivenTectonics.
"""

import sys
import os
import traceback

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def run_basic_tests():
    """Run basic functionality tests without pytest."""
    print("Running basic functionality tests...")
    print("=" * 50)
    
    # Test 1: Import test
    try:
        from gospl_tectonics_ext import DataDrivenTectonics
        print("✓ Import test passed")
    except ImportError as e:
        print(f"✗ Import test failed: {e}")
        return False
    
    # Test 2: Basic instantiation test
    try:
        # Mock the parent class for testing
        import numpy as np
        from unittest.mock import Mock
        
        # Create a mock version for testing
        class MockTectonics:
            def __init__(self):
                self.mCoords = np.array([[0, 0, 0], [1, 1, 0]])
                self.locIDs = np.array([0, 1])
                self.dt = 1.0
                self.advscheme = 0
                self.tNow = 0.0
                self.plateStep = False
                self.plateTimer = 0.0
                self.lpoints = 2
                self.flatModel = True
            
            def _readAdvectionData(self, v_interp, timer):
                pass
        
        # Temporarily replace the parent class
        original_bases = DataDrivenTectonics.__bases__
        DataDrivenTectonics.__bases__ = (MockTectonics,)
        
        tectonics = DataDrivenTectonics()
        
        # Restore original bases
        DataDrivenTectonics.__bases__ = original_bases
        
        print("✓ Instantiation test passed")
    except Exception as e:
        print(f"✗ Instantiation test failed: {e}")
        return False
    
    # Test 3: Method existence test
    try:
        if hasattr(DataDrivenTectonics, 'apply_velocity_data'):
            print("✓ Method existence test passed")
        else:
            print("✗ Method existence test failed: apply_velocity_data method not found")
            return False
    except Exception as e:
        print(f"✗ Method existence test failed: {e}")
        return False
    
    print("\nAll basic tests passed! ✓")
    return True


def run_example_validation():
    """Validate that example scripts are syntactically correct."""
    print("\nValidating example scripts...")
    print("=" * 50)
    
    examples_dir = os.path.join(os.path.dirname(__file__), 'examples')
    if not os.path.exists(examples_dir):
        print("✗ Examples directory not found")
        return False
    
    example_files = [
        'data_driven_tectonics_basic.py',
        'data_driven_tectonics_advanced.py',
        'enhanced_model_basic.py',
        'enhanced_model_advanced.py'
    ]
    
    for example_file in example_files:
        file_path = os.path.join(examples_dir, example_file)
        if os.path.exists(file_path):
            try:
                # Try to compile the file (syntax check)
                with open(file_path, 'r') as f:
                    code = f.read()
                compile(code, file_path, 'exec')
                print(f"✓ {example_file} syntax is valid")
            except SyntaxError as e:
                print(f"✗ {example_file} has syntax error: {e}")
                return False
            except Exception as e:
                print(f"✗ Error validating {example_file}: {e}")
                return False
        else:
            print(f"✗ Example file {example_file} not found")
            return False
    
    print("✓ All example scripts are syntactically valid")
    return True


def check_environment():
    """Check if the gospl conda environment is activated."""
    print("Checking environment...")
    print("=" * 50)
    
    # Check if we're in a conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', None)
    if conda_env is None:
        print("⚠️  No conda environment detected")
        print("Please activate the gospl conda environment: conda activate gospl")
        return False
    
    print(f"✓ Conda environment active: {conda_env}")
    
    if conda_env != 'gospl':
        print(f"⚠️  Current environment '{conda_env}' is not 'gospl'")
        print("Please activate the gospl conda environment: conda activate gospl")
        print("(This may still work if goSPL is installed in the current environment)")
        return True  # Don't fail completely, just warn
    
    print("✓ gospl conda environment is active")
    return True


def check_dependencies():
    """Check if required dependencies are available."""
    print("\nChecking dependencies...")
    print("=" * 50)
    
    required_deps = ['numpy', 'scipy']
    optional_deps = ['pytest', 'pandas']
    
    missing_required = []
    missing_optional = []
    
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"✓ {dep} is available")
        except ImportError:
            print(f"✗ {dep} is missing (required)")
            missing_required.append(dep)
    
    for dep in optional_deps:
        try:
            __import__(dep)
            print(f"✓ {dep} is available")
        except ImportError:
            print(f"- {dep} is missing (optional)")
            missing_optional.append(dep)
    
    if missing_required:
        print(f"\n⚠️  Missing required dependencies: {', '.join(missing_required)}")
        print("Please install them with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n💡 Missing optional dependencies: {', '.join(missing_optional)}")
        print("Install them for additional features: pip install " + " ".join(missing_optional))
    
    return True


def main():
    """Main test runner function."""
    print("gospl_extensions Test Runner")
    print("=" * 60)
    
    all_passed = True
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed")
        all_passed = False
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        all_passed = False
    
    # Run basic tests
    if not run_basic_tests():
        print("\n❌ Basic tests failed")
        all_passed = False
    
    # Validate examples
    if not run_example_validation():
        print("\n❌ Example validation failed")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! The extension appears to be working correctly.")
        print("\nNext steps:")
        print("1. Ensure the gospl conda environment is activated: conda activate gospl")
        print("2. Install goSPL if you haven't already")
        print("3. Try running the examples in the 'examples/' directory")
        print("4. Run 'pytest tests/' if pytest is installed for comprehensive testing")
    else:
        print("❌ Some tests failed. Please check the output above for details.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
