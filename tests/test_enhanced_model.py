"""
Tests for the Enhanced Model extension.

This test suite validates the EnhancedModel class functionality without requiring 
a full goSPL installation by using mock objects.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import time

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that we can import the EnhancedModel class."""
    # Mock goSPL before importing our module
    with patch.dict('sys.modules', {'gospl': Mock(), 'gospl.model': Mock()}):
        from gospl_model_ext import EnhancedModel
        assert EnhancedModel is not None

class MockModel:
    """Mock Model class to simulate goSPL Model behavior."""
    
    def __init__(self, *args, **kwargs):
        self.tNow = 0.0
        self.tEnd = 100000.0
        self.dt = 1000.0
        self.run_calls = []
        
    def runProcesses(self, *args, **kwargs):
        """Mock runProcesses method."""
        # Simulate time advancement
        old_time = self.tNow
        self.tNow += self.dt
        self.run_calls.append({
            'method': 'runProcesses',
            'old_time': old_time,
            'new_time': self.tNow,
            'args': args,
            'kwargs': kwargs
        })

@pytest.fixture
def mock_gospl():
    """Create mock goSPL environment."""
    mock_gospl = Mock()
    mock_model = Mock()
    mock_model.Model = MockModel
    mock_gospl.model = mock_model
    
    with patch.dict('sys.modules', {
        'gospl': mock_gospl,
        'gospl.model': mock_model
    }):
        yield mock_gospl

def test_enhanced_model_creation(mock_gospl):
    """Test that EnhancedModel can be created."""
    from gospl_model_ext import EnhancedModel
    
    # Create an enhanced model
    model = EnhancedModel("test_config.yml")
    
    # Check that it has the base Model attributes
    assert hasattr(model, 'tNow')
    assert hasattr(model, 'tEnd') 
    assert hasattr(model, 'dt')
    assert hasattr(model, 'runProcesses')
    
    # Check that it has our new methods
    assert hasattr(model, 'runProcessesForDt')
    assert hasattr(model, 'runProcessesForSteps')
    assert hasattr(model, 'runProcessesUntilTime')

def test_run_processes_for_dt(mock_gospl):
    """Test runProcessesForDt method."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    initial_time = model.tNow
    
    # Run for specific dt
    dt = 2000.0
    model.runProcessesForDt(dt=dt)
    
    # Check that time advanced by dt
    assert model.tNow == initial_time + dt
    assert len(model.run_calls) == 1
    assert model.run_calls[0]['method'] == 'runProcesses'

def test_run_processes_for_dt_default(mock_gospl):
    """Test runProcessesForDt with default dt."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    model.dt = 1500.0  # Set default dt
    initial_time = model.tNow
    
    # Run with default dt
    model.runProcessesForDt()
    
    # Check that time advanced by model's dt
    assert model.tNow == initial_time + 1500.0

def test_run_processes_for_steps(mock_gospl):
    """Test runProcessesForSteps method."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    initial_time = model.tNow
    
    # Run for 5 steps with specific dt
    num_steps = 5
    dt = 800.0
    model.runProcessesForSteps(num_steps=num_steps, dt=dt)
    
    # Check that we ran 5 times
    assert len(model.run_calls) == num_steps
    
    # Check that time advanced by num_steps * dt
    expected_time = initial_time + (num_steps * dt)
    assert model.tNow == expected_time

def test_run_processes_for_steps_default_dt(mock_gospl):
    """Test runProcessesForSteps with default dt."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    model.dt = 1200.0
    initial_time = model.tNow
    
    # Run for 3 steps with default dt
    num_steps = 3
    model.runProcessesForSteps(num_steps=num_steps)
    
    # Check that time advanced correctly
    expected_time = initial_time + (num_steps * 1200.0)
    assert model.tNow == expected_time
    assert len(model.run_calls) == num_steps

def test_run_processes_until_time(mock_gospl):
    """Test runProcessesUntilTime method."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    model.tNow = 0.0
    
    # Run until target time
    target_time = 5500.0
    dt = 1000.0
    model.runProcessesUntilTime(target_time=target_time, dt=dt)
    
    # Should run 6 times: 0->1000, 1000->2000, ..., 5000->6000
    # Final time should be >= target_time
    assert model.tNow >= target_time
    assert len(model.run_calls) == 6  # ceil(5500/1000) = 6

def test_run_processes_until_time_exact(mock_gospl):
    """Test runProcessesUntilTime with exact multiple."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    model.tNow = 0.0
    
    # Run until exact multiple of dt
    target_time = 4000.0
    dt = 1000.0
    model.runProcessesUntilTime(target_time=target_time, dt=dt)
    
    # Should run exactly 4 times
    assert model.tNow == target_time
    assert len(model.run_calls) == 4

def test_run_processes_until_time_already_past(mock_gospl):
    """Test runProcessesUntilTime when already past target."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    model.tNow = 5000.0
    
    # Try to run until earlier time
    target_time = 3000.0
    dt = 1000.0
    model.runProcessesUntilTime(target_time=target_time, dt=dt)
    
    # Should not run any steps
    assert len(model.run_calls) == 0
    assert model.tNow == 5000.0

def test_run_processes_until_time_default_dt(mock_gospl):
    """Test runProcessesUntilTime with default dt."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    model.tNow = 0.0
    model.dt = 750.0
    
    # Run until target time with default dt
    target_time = 2000.0
    model.runProcessesUntilTime(target_time=target_time)
    
    # Should run 3 times: 0->750, 750->1500, 1500->2250
    assert model.tNow >= target_time
    assert len(model.run_calls) == 3

def test_error_handling_invalid_dt(mock_gospl):
    """Test error handling for invalid dt values."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    
    # Test negative dt
    with pytest.raises(ValueError, match="dt must be positive"):
        model.runProcessesForDt(dt=-1000.0)
    
    # Test zero dt
    with pytest.raises(ValueError, match="dt must be positive"):
        model.runProcessesForDt(dt=0.0)

def test_error_handling_invalid_steps(mock_gospl):
    """Test error handling for invalid number of steps."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    
    # Test negative steps
    with pytest.raises(ValueError, match="num_steps must be positive"):
        model.runProcessesForSteps(num_steps=-1)
    
    # Test zero steps
    with pytest.raises(ValueError, match="num_steps must be positive"):
        model.runProcessesForSteps(num_steps=0)

def test_error_handling_invalid_target_time(mock_gospl):
    """Test error handling for invalid target time."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    
    # Test negative target time
    with pytest.raises(ValueError, match="target_time must be non-negative"):
        model.runProcessesUntilTime(target_time=-1000.0)

def test_dt_override_preserves_original(mock_gospl):
    """Test that overriding dt preserves the original value."""
    from gospl_model_ext import EnhancedModel
    
    model = EnhancedModel("test_config.yml")
    original_dt = model.dt
    
    # Run with different dt
    custom_dt = 500.0
    model.runProcessesForDt(dt=custom_dt)
    
    # Original dt should be preserved
    assert model.dt == original_dt

def test_timing_consistency(mock_gospl):
    """Test that timing is consistent across different methods."""
    from gospl_model_ext import EnhancedModel
    
    # Test with multiple models to compare approaches
    model1 = EnhancedModel("test_config.yml")
    model2 = EnhancedModel("test_config.yml")
    model3 = EnhancedModel("test_config.yml")
    
    dt = 1000.0
    
    # Method 1: Single large step
    model1.runProcessesForDt(dt=dt * 5)
    
    # Method 2: Multiple small steps
    model2.runProcessesForSteps(num_steps=5, dt=dt)
    
    # Method 3: Run until time
    model3.runProcessesUntilTime(target_time=5000.0, dt=dt)
    
    # All should result in same final time
    assert model1.tNow == 5000.0
    assert model2.tNow == 5000.0
    assert model3.tNow == 5000.0

if __name__ == "__main__":
    # Run tests if called directly
    import subprocess
    import sys
    
    try:
        # Try to run with pytest if available
        subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to running tests manually
        print("Running tests manually...")
        
        # Create mock environment
        with patch.dict('sys.modules', {'gospl': Mock(), 'gospl.model': Mock()}):
            test_functions = [
                test_imports,
                test_enhanced_model_creation,
                test_run_processes_for_dt,
                test_run_processes_for_dt_default,
                test_run_processes_for_steps,
                test_run_processes_for_steps_default_dt,
                test_run_processes_until_time,
                test_run_processes_until_time_exact,
                test_run_processes_until_time_already_past,
                test_run_processes_until_time_default_dt,
                test_error_handling_invalid_dt,
                test_error_handling_invalid_steps,
                test_error_handling_invalid_target_time,
                test_dt_override_preserves_original,
                test_timing_consistency
            ]
            
            passed = 0
            failed = 0
            
            for test_func in test_functions:
                try:
                    if 'mock_gospl' in test_func.__code__.co_varnames:
                        # Call with mock fixture
                        test_func(Mock())
                    else:
                        # Call without arguments
                        test_func()
                    print(f"✓ {test_func.__name__}")
                    passed += 1
                except Exception as e:
                    print(f"✗ {test_func.__name__}: {e}")
                    failed += 1
            
            print(f"\nResults: {passed} passed, {failed} failed")
