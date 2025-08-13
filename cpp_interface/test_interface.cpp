#include "gospl_extensions.h"
#include <iostream>
#include <vector>

/**
 * Simple test program for the gospl_extensions C++ interface.
 * This tests basic functionality without requiring a full goSPL configuration.
 */

int main() {
    std::cout << "Testing gospl_extensions C++ interface" << std::endl;
    std::cout << std::string(40, '=') << std::endl;
    
    // Test 1: Initialize the interface
    std::cout << "\n1. Testing initialization..." << std::endl;
    if (initialize_gospl_extensions() != 0) {
        std::cerr << "❌ Failed to initialize gospl_extensions" << std::endl;
        return 1;
    }
    std::cout << "✅ Initialization successful" << std::endl;
    
    // Test 2: Test velocity field generation
    std::cout << "\n2. Testing velocity field generation..." << std::endl;
    const int num_points = 100;
    std::vector<double> coords(num_points * 3);
    std::vector<double> velocities(num_points * 3);
    
    int points_generated = create_velocity_field(0.0, 5.0, 5.0, 0.1, 
                                               coords.data(), velocities.data());
    
    if (points_generated == num_points) {
        std::cout << "✅ Velocity field generation successful (" 
                  << points_generated << " points)" << std::endl;
        
        // Print some sample points
        std::cout << "   Sample points:" << std::endl;
        for (int i = 0; i < 3; i++) {
            std::cout << "   Point " << i << ": coord=(" 
                      << coords[i*3] << ", " << coords[i*3+1] << ", " << coords[i*3+2]
                      << ") vel=(" << velocities[i*3] << ", " << velocities[i*3+1] 
                      << ", " << velocities[i*3+2] << ")" << std::endl;
        }
    } else {
        std::cerr << "❌ Velocity field generation failed" << std::endl;
    }
    
    // Test 3: Test model creation (this will likely fail without proper config)
    std::cout << "\n3. Testing model creation (expected to fail without config)..." << std::endl;
    ModelHandle handle = create_enhanced_model("nonexistent_config.yml");
    
    if (handle >= 0) {
        std::cout << "✅ Model created successfully (handle: " << handle << ")" << std::endl;
        
        // Test getting current time and dt
        double current_time = get_current_time(handle);
        double dt = get_time_step(handle);
        
        std::cout << "   Current time: " << current_time << std::endl;
        std::cout << "   Time step: " << dt << std::endl;
        
        // Clean up
        if (destroy_model(handle) == 0) {
            std::cout << "✅ Model destroyed successfully" << std::endl;
        } else {
            std::cerr << "❌ Failed to destroy model" << std::endl;
        }
    } else {
        std::cout << "⚠️  Model creation failed (expected without valid config)" << std::endl;
    }
    
    // Test 4: Cleanup
    std::cout << "\n4. Testing cleanup..." << std::endl;
    finalize_gospl_extensions();
    std::cout << "✅ Cleanup completed" << std::endl;
    
    std::cout << "\n🎉 Basic interface testing completed!" << std::endl;
    std::cout << "\nTo test with actual goSPL simulation:" << std::endl;
    std::cout << "1. Ensure you have a valid goSPL config file (e.g., input-escarpment.yml)" << std::endl;
    std::cout << "2. Activate the gospl conda environment" << std::endl;
    std::cout << "3. Run: ./enhanced_model_driver path/to/config.yml" << std::endl;
    
    return 0;
}
