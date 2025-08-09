import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the gospl dependencies since they may not be available during testing
sys.modules['gospl'] = Mock()
sys.modules['gospl.mesher'] = Mock()
sys.modules['gospl.mesher.tectonics'] = Mock()
sys.modules['gospl._fortran'] = Mock()

# Create mock Tectonics class
class MockTectonics:
    def __init__(self):
        self.mCoords = None
        self.locIDs = None
        self.hdisp = None
        self.upsub = None
        self.advscheme = 0
        self.dt = 1.0
        self.plateStep = False
        self.plateTimer = 0.0
        self.tNow = 0.0
        self.lpoints = 0
        self.flatModel = True

    def _readAdvectionData(self, v_interp, timer):
        pass
    
    def _varAdvector(self):
        pass

# Patch the import
sys.modules['gospl.mesher.tectonics'].Tectonics = MockTectonics

from gospl_tectonics_ext import DataDrivenTectonics


class TestDataDrivenTectonics:
    """Test suite for DataDrivenTectonics class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.tectonics = DataDrivenTectonics()
        
        # Create sample mesh coordinates (10 points in 3D)
        self.tectonics.mCoords = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.5, 0.5, 0.0],
            [2.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [2.0, 2.0, 0.0],
            [1.5, 1.5, 0.0],
            [0.25, 0.75, 0.0]
        ])
        
        # Local IDs (subset of mesh nodes)
        self.tectonics.locIDs = np.array([0, 1, 2, 3, 4])
        self.tectonics.lpoints = len(self.tectonics.locIDs)
        
        # Sample velocity data
        self.sample_coords = np.array([
            [0.1, 0.1, 0.0],
            [1.1, 0.1, 0.0],
            [0.1, 1.1, 0.0],
            [1.1, 1.1, 0.0]
        ])
        
        self.sample_vel = np.array([
            [0.1, 0.0, 0.05],
            [0.0, 0.1, 0.0],
            [-0.1, 0.0, -0.05],
            [0.0, -0.1, 0.0]
        ])

    def test_init(self):
        """Test that DataDrivenTectonics initializes properly."""
        tectonics = DataDrivenTectonics()
        assert isinstance(tectonics, DataDrivenTectonics)

    def test_apply_velocity_data_dict_input(self):
        """Test apply_velocity_data with dictionary input."""
        veldata = {
            "coords": self.sample_coords,
            "vel": self.sample_vel
        }
        
        # Mock the required methods
        self.tectonics._readAdvectionData = Mock()
        
        # Call the method
        self.tectonics.apply_velocity_data(veldata, k=2)
        
        # Check that interpolated data was stored
        assert self.tectonics.hdisp is not None
        assert self.tectonics.upsub is not None
        assert self.tectonics.hdisp.shape == (5, 3)  # 5 local points, 3 components
        assert self.tectonics.upsub.shape == (5,)    # 5 local points, z-component

    def test_apply_velocity_data_object_input(self):
        """Test apply_velocity_data with object input."""
        class VelData:
            def __init__(self, coords, vel):
                self.coords = coords
                self.vel = vel
        
        veldata = VelData(self.sample_coords, self.sample_vel)
        
        # Mock the required methods
        self.tectonics._readAdvectionData = Mock()
        
        # Call the method
        self.tectonics.apply_velocity_data(veldata, k=3)
        
        # Check that data was processed
        assert self.tectonics.hdisp is not None
        assert self.tectonics.upsub is not None

    def test_invalid_input_no_coords(self):
        """Test error handling for missing coordinates."""
        veldata = {"vel": self.sample_vel}
        
        with pytest.raises(ValueError, match="must contain 'coords' and 'vel'"):
            self.tectonics.apply_velocity_data(veldata)

    def test_invalid_input_no_vel(self):
        """Test error handling for missing velocities."""
        veldata = {"coords": self.sample_coords}
        
        with pytest.raises(ValueError, match="must contain 'coords' and 'vel'"):
            self.tectonics.apply_velocity_data(veldata)

    def test_invalid_coords_shape(self):
        """Test error handling for invalid coordinate shape."""
        veldata = {
            "coords": np.array([[1, 2]]),  # Wrong shape
            "vel": self.sample_vel
        }
        
        with pytest.raises(ValueError, match="coords must be of shape \\(N, 3\\)"):
            self.tectonics.apply_velocity_data(veldata)

    def test_invalid_vel_shape(self):
        """Test error handling for invalid velocity shape."""
        veldata = {
            "coords": self.sample_coords,
            "vel": np.array([[1, 2]])  # Wrong shape
        }
        
        with pytest.raises(ValueError, match="vel must be of shape \\(N, 3\\)"):
            self.tectonics.apply_velocity_data(veldata)

    def test_mismatched_sizes(self):
        """Test error handling for mismatched array sizes."""
        veldata = {
            "coords": self.sample_coords,
            "vel": np.array([[1, 2, 3]])  # Different number of rows
        }
        
        with pytest.raises(ValueError, match="must have the same number of rows"):
            self.tectonics.apply_velocity_data(veldata)

    def test_empty_data(self):
        """Test error handling for empty data."""
        veldata = {
            "coords": np.empty((0, 3)),
            "vel": np.empty((0, 3))
        }
        
        with pytest.raises(ValueError, match="contains no samples"):
            self.tectonics.apply_velocity_data(veldata)

    def test_k_parameter_bounds(self):
        """Test that k parameter is properly bounded."""
        veldata = {
            "coords": self.sample_coords,
            "vel": self.sample_vel
        }
        
        # Mock the required methods
        self.tectonics._readAdvectionData = Mock()
        
        # Test k too large (should be clamped to data size)
        self.tectonics.apply_velocity_data(veldata, k=100)
        assert self.tectonics.hdisp is not None
        
        # Test k = 0 (should be clamped to 1)
        self.tectonics.apply_velocity_data(veldata, k=0)
        assert self.tectonics.hdisp is not None

    def test_advscheme_zero(self):
        """Test semi-Lagrangian advection scheme (advscheme == 0)."""
        self.tectonics.advscheme = 0
        self.tectonics.dt = 2.0
        self.tectonics.tNow = 10.0
        self.tectonics._readAdvectionData = Mock()
        
        veldata = {
            "coords": self.sample_coords,
            "vel": self.sample_vel
        }
        
        self.tectonics.apply_velocity_data(veldata)
        
        # Check that plate advection is scheduled
        assert self.tectonics.plateStep == True
        assert self.tectonics.plateTimer == 12.0  # tNow + dt

    def test_advscheme_nonzero(self):
        """Test finite-volume advection scheme (advscheme > 0)."""
        self.tectonics.advscheme = 1
        self.tectonics._varAdvector = Mock()
        
        # Mock the getfacevelocity function
        with patch('gospl_tectonics_ext.data_driven_tectonics.getfacevelocity') as mock_getface:
            veldata = {
                "coords": self.sample_coords,
                "vel": self.sample_vel
            }
            
            self.tectonics.apply_velocity_data(veldata)
            
            # Check that face velocity computation was called
            mock_getface.assert_called_once()
            self.tectonics._varAdvector.assert_called_once()

    def test_custom_timer(self):
        """Test custom timer parameter."""
        self.tectonics.advscheme = 0
        self.tectonics.tNow = 5.0
        self.tectonics._readAdvectionData = Mock()
        
        veldata = {
            "coords": self.sample_coords,
            "vel": self.sample_vel
        }
        
        custom_timer = 3.0
        self.tectonics.apply_velocity_data(veldata, timer=custom_timer)
        
        # Check that custom timer was used
        assert self.tectonics.plateTimer == 8.0  # tNow + custom_timer

    def test_coincident_nodes(self):
        """Test handling of coincident nodes (distance < eps)."""
        # Create velocity data where one point coincides exactly with mesh node
        coincident_coords = np.copy(self.sample_coords)
        coincident_coords[0] = self.tectonics.mCoords[0]  # Exact match
        
        veldata = {
            "coords": coincident_coords,
            "vel": self.sample_vel
        }
        
        self.tectonics._readAdvectionData = Mock()
        
        self.tectonics.apply_velocity_data(veldata)
        
        # Should handle coincident nodes without error
        assert self.tectonics.hdisp is not None
        assert self.tectonics.upsub is not None

    def test_power_parameter(self):
        """Test different power values for inverse distance weighting."""
        veldata = {
            "coords": self.sample_coords,
            "vel": self.sample_vel
        }
        
        self.tectonics._readAdvectionData = Mock()
        
        # Test power = 2.0
        self.tectonics.apply_velocity_data(veldata, power=2.0)
        hdisp_p2 = self.tectonics.hdisp.copy()
        
        # Test power = 0.5
        self.tectonics.apply_velocity_data(veldata, power=0.5)
        hdisp_p05 = self.tectonics.hdisp.copy()
        
        # Results should be different with different power values
        assert not np.allclose(hdisp_p2, hdisp_p05)

    def test_single_neighbor(self):
        """Test interpolation with k=1 (single nearest neighbor)."""
        veldata = {
            "coords": self.sample_coords,
            "vel": self.sample_vel
        }
        
        self.tectonics._readAdvectionData = Mock()
        
        self.tectonics.apply_velocity_data(veldata, k=1)
        
        # Should work with single neighbor
        assert self.tectonics.hdisp is not None
        assert self.tectonics.upsub is not None
        assert self.tectonics.hdisp.shape == (5, 3)

    def test_spherical_model(self):
        """Test with spherical model (flatModel = False)."""
        self.tectonics.flatModel = False
        self.tectonics.advscheme = 1
        self.tectonics._varAdvector = Mock()
        
        with patch('gospl_tectonics_ext.data_driven_tectonics.getfacevelocity') as mock_getface:
            veldata = {
                "coords": self.sample_coords,
                "vel": self.sample_vel
            }
            
            self.tectonics.apply_velocity_data(veldata)
            
            # Should call getfacevelocity and _varAdvector
            mock_getface.assert_called_once()
            self.tectonics._varAdvector.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
