#!/usr/bin/env python3
"""
Simple test script for EnhancedModel without external dependencies.
"""

import sys
import os
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_model():
    """Test EnhancedModel with mocked goSPL"""
    
    print("=== Testing EnhancedModel ===")
    
    # Create a mock Model class
    class MockModel:
        def __init__(self, *args, **kwargs):
            self.tNow = 0.0
            self.tEnd = 100000.0
            self.dt = 1000.0
            self.run_count = 0
            
        def runProcesses(self):
            """Mock runProcesses method"""
            self.tNow += self.dt
            self.run_count += 1
            print(f"  Mock runProcesses called (tNow={self.tNow}, count={self.run_count})")
    
    # Mock the entire gospl module tree
    mock_gospl = Mock()
    mock_model_module = Mock()
    mock_model_module.Model = MockModel
    mock_gospl.model = mock_model_module
    
    # Patch sys.modules before importing our code
    with patch.dict('sys.modules', {
        'gospl': mock_gospl,
        'gospl.model': mock_model_module
    }):
        # Now import our module
        try:
            from gospl_model_ext import EnhancedModel
            print("✓ EnhancedModel imported successfully")
            
            # Test instantiation
            model = EnhancedModel("test_config.yml")
            print("✓ EnhancedModel instantiated")
            
            # Test that it has our methods
            assert hasattr(model, 'runProcessesForDt'), "Missing runProcessesForDt method"
            assert hasattr(model, 'runProcessesForSteps'), "Missing runProcessesForSteps method" 
            assert hasattr(model, 'runProcessesUntilTime'), "Missing runProcessesUntilTime method"
            print("✓ All required methods present")
            
            # Test runProcessesForDt
            initial_time = model.tNow
            model.runProcessesForDt(dt=2000.0)
            assert model.tNow == initial_time + 2000.0, f"Time not advanced correctly: {model.tNow} != {initial_time + 2000.0}"
            print("✓ runProcessesForDt works correctly")
            
            # Test runProcessesForSteps
            initial_time = model.tNow
            model.runProcessesForSteps(num_steps=3, dt=500.0)
            expected_time = initial_time + (3 * 500.0)
            assert model.tNow == expected_time, f"Time not advanced correctly: {model.tNow} != {expected_time}"
            print("✓ runProcessesForSteps works correctly")
            
            # Test runProcessesUntilTime
            model.tNow = 0.0  # Reset
            model.runProcessesUntilTime(target_time=3500.0, dt=1000.0)
            assert model.tNow >= 3500.0, f"Did not reach target time: {model.tNow} < 3500.0"
            print("✓ runProcessesUntilTime works correctly")
            
            print("\n🎉 All tests passed!")
            return True
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_enhanced_model()
    sys.exit(0 if success else 1)
