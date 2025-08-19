#include "gospl_extensions.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <iomanip>

/**
 * Enhanced Model C++ Driver
 * 
 * This C++ driver corresponds to enhanced_model_basic.py and demonstrates:
 * 1. Using EnhancedModel for granular time control
 * 2. Running processes for specific dt intervals
 * 3. Combining with DataDrivenTectonics for controlled simulations
 * 4. Monitoring simulation progress step by step
 * 
 * This code interfaces with goSPL extensions through Python C API bindings.
 */

class EnhancedModelDriver {
public:
    ModelHandle model_handle;
    bool initialized;
    
    EnhancedModelDriver() : model_handle(-1), initialized(false) {}
    
    ~EnhancedModelDriver() {
        cleanup();
    }
    
    bool initialize(const std::string& config_path) {
        std::cout << "Enhanced Model C++ Driver: Granular Time Control" << std::endl;
        std::cout << std::string(55, '=') << std::endl;
        
        // Initialize gospl extensions
        if (initialize_gospl_extensions() != 0) {
            std::cerr << "Failed to initialize gospl extensions" << std::endl;
            return false;
        }
        
        // Create enhanced model
        std::cout << "Initializing EnhancedModel with " << config_path << std::endl;
        model_handle = create_enhanced_model(config_path.c_str());
        
        if (model_handle < 0) {
            std::cerr << "Failed to create enhanced model" << std::endl;
            return false;
        }
        
        double current_time = get_current_time(model_handle);
        double dt = get_time_step(model_handle);
        
        std::cout << "Model initialized at t=" << current_time 
                  << ", dt=" << dt << std::endl;
        
        initialized = true;
        return true;
    }
    
    void cleanup() {
        if (model_handle >= 0) {
            destroy_model(model_handle);
            model_handle = -1;
        }
        
        if (initialized) {
            finalize_gospl_extensions();
            initialized = false;
        }
    }
    
    void demonstrate_enhanced_model_methods() {
        if (!initialized) return;
        
        std::cout << "\nDemonstrating EnhancedModel methods:" << std::endl;
        std::cout << std::string(50, '=') << std::endl;
        
        double initial_time = get_current_time(model_handle);
        
        // Method 1: Run for specific number of steps
        std::cout << "\n1. Running 3 steps with dt=0.5" << std::endl;
        int steps_completed = run_processes_for_steps(model_handle, 3, 0.5, 1);
        if (steps_completed > 0) {
            std::cout << "   Completed " << steps_completed << " steps" << std::endl;
        } else {
            std::cerr << "   Error running steps" << std::endl;
        }
        
        // Method 2: Run until specific time
        double current_time = get_current_time(model_handle);
        double target_time = current_time + 2.0;
        std::cout << "\n2. Running until t=" << target_time << std::endl;
        int steps_until = run_processes_until_time(model_handle, target_time, 0.75, 1);
        if (steps_until > 0) {
            std::cout << "   Completed " << steps_until << " steps to reach target" << std::endl;
        } else {
            std::cerr << "   Error running until time" << std::endl;
        }
        
        double final_time = get_current_time(model_handle);
        double total_time = final_time - initial_time;
        std::cout << "\n✓ Enhanced model methods demo completed! Total time advanced: " 
                  << std::fixed << std::setprecision(2) << total_time << std::endl;
    }
    
    void run_controlled_simulation(double duration = 5.0, double dt = 1.0) {
        if (!initialized) return;
        
        std::cout << "\nRunning controlled simulation for " << duration 
                  << " time units with dt=" << dt << std::endl;
        std::cout << std::string(60, '=') << std::endl;
        
        double start_time = get_current_time(model_handle);
        double target_time = start_time + duration;
        int step = 0;
        
        // Pre-allocate arrays for velocity data (100 points from 10x10 grid)
        const int num_points = 100;
        std::vector<double> coords(num_points * 3);
        std::vector<double> velocities(num_points * 3);
        
        // Apply time-dependent velocities and run step by step
        double current_time = start_time;
        while (current_time < target_time) {
            double remaining_time = target_time - current_time;
            double step_dt = std::min(dt, remaining_time);
            
            std::cout << "\nStep " << (step + 1) << ": t=" 
                      << std::fixed << std::setprecision(2) << current_time 
                      << " -> " << (current_time + step_dt) << std::endl;
            
            // Generate time-dependent velocity field
            int points_generated = create_velocity_field(current_time, 5.0, 5.0, 0.1,
                                                       coords.data(), velocities.data());
            
            if (points_generated > 0) {
                std::cout << "  Generated velocity field for t=" 
                          << std::fixed << std::setprecision(2) << current_time 
                          << " (" << points_generated << " points)" << std::endl;
                
                // Apply velocities using DataDrivenTectonics
                int apply_result = apply_velocity_data(model_handle, 
                                                     coords.data(), velocities.data(),
                                                     points_generated, step_dt, 3, 1.0);
                
                if (apply_result == 0) {
                    std::cout << "  Applied velocity data with timer=" << step_dt << std::endl;
                } else {
                    std::cerr << "  Error applying velocity data" << std::endl;
                }
            }
            
            // Run processes for this specific time step
            double elapsed = run_processes_for_dt(model_handle, step_dt, 1);
            if (elapsed >= 0) {
                std::cout << "  Completed step in " 
                          << std::fixed << std::setprecision(2) << elapsed << "s" << std::endl;
            } else {
                std::cerr << "  Error running processes" << std::endl;
                break;
            }
            
            // Update current time and increment step
            current_time = get_current_time(model_handle);
            step++;
        }
        
        double final_time = get_current_time(model_handle);
        double total_time = final_time - start_time;
        std::cout << "\n✓ Simulation completed! Ran for " 
                  << std::fixed << std::setprecision(2) << total_time 
                  << " time units in " << step << " steps" << std::endl;
    }
};

int main(int argc, char* argv[]) {
    // Default input file
    std::string input_file = "../examples/input-escarpment.yml";
    
    // Parse command line arguments
    if (argc > 1) {
        input_file = argv[1];
    }
    
    try {
        EnhancedModelDriver driver;
        
        // Initialize the driver
        if (!driver.initialize(input_file)) {
            std::cerr << "Failed to initialize Enhanced Model driver" << std::endl;
            return 1;
        }
        
        // Demonstrate enhanced model methods
        driver.demonstrate_enhanced_model_methods();
        
        // Run controlled simulation with time-dependent tectonics
        driver.run_controlled_simulation(5.0, 1.0);
        
        std::cout << "\n🎉 All demonstrations completed successfully!" << std::endl;
        
        // Get final simulation time
        double final_time = get_current_time(driver.model_handle);
        if (final_time >= 0) {
            std::cout << "Final simulation time: t=" 
                      << std::fixed << std::setprecision(1) << final_time << std::endl;
        }
        
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "Unknown error occurred" << std::endl;
        return 1;
    }
}

// Additional utility functions that could be useful for C++ drivers

/**
 * Print velocity statistics
 */
void print_velocity_stats(const std::vector<double>& velocities, int num_points) {
    if (velocities.size() < static_cast<size_t>(num_points * 3)) return;
    
    double max_vel = 0.0;
    double sum_vel = 0.0;
    
    for (int i = 0; i < num_points; i++) {
        double vx = velocities[i * 3 + 0];
        double vy = velocities[i * 3 + 1];
        double vz = velocities[i * 3 + 2];
        
        double vel_mag = std::sqrt(vx*vx + vy*vy + vz*vz);
        max_vel = std::max(max_vel, vel_mag);
        sum_vel += vel_mag;
    }
    
    double mean_vel = sum_vel / num_points;
    
    std::cout << "  Velocity stats - Max: " 
              << std::fixed << std::setprecision(6) << max_vel
              << ", Mean: " << mean_vel << std::endl;
}

/**
 * Timer utility class
 */
class Timer {
private:
    std::chrono::high_resolution_clock::time_point start_time;
    
public:
    Timer() : start_time(std::chrono::high_resolution_clock::now()) {}
    
    double elapsed() const {
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
            end_time - start_time);
        return duration.count() / 1000000.0;  // Convert to seconds
    }
    
    void reset() {
        start_time = std::chrono::high_resolution_clock::now();
    }
};
