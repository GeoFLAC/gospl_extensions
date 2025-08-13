#ifndef GOSPL_EXTENSIONS_H
#define GOSPL_EXTENSIONS_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * gospl_extensions C++ Interface Header
 * 
 * This header provides a C++ interface to the goSPL extensions (EnhancedModel 
 * and DataDrivenTectonics) through a Python C API bridge.
 * 
 * The interface allows C++ code to:
 * - Create and manage EnhancedModel instances
 * - Run simulations with granular time control
 * - Apply time-dependent velocity data
 * - Monitor simulation progress
 */

// Handle type for model instances
typedef int ModelHandle;

// Structure for velocity data
struct VelocityData {
    double* coords;      // Array of coordinates (num_points * 3)
    double* velocities;  // Array of velocities (num_points * 3) 
    int num_points;      // Number of data points
};

/**
 * Initialize the Python interpreter and load gospl extensions.
 * Must be called before any other functions.
 * 
 * @return 0 on success, -1 on error
 */
int initialize_gospl_extensions();

/**
 * Finalize the Python interpreter.
 * Should be called at program exit.
 */
void finalize_gospl_extensions();

/**
 * Create an EnhancedModel instance.
 * 
 * @param config_path Path to goSPL configuration file
 * @return Model handle (>= 0) on success, -1 on error
 */
ModelHandle create_enhanced_model(const char* config_path);

/**
 * Destroy a model instance and free resources.
 * 
 * @param handle Model handle
 * @return 0 on success, -1 on error
 */
int destroy_model(ModelHandle handle);

/**
 * Run processes for a specific time step.
 * 
 * @param handle Model handle
 * @param dt Time step size
 * @param verbose Print progress information (0=false, 1=true)
 * @return Elapsed time on success, -1.0 on error
 */
double run_processes_for_dt(ModelHandle handle, double dt, int verbose);

/**
 * Run processes for a specified number of steps.
 * 
 * @param handle Model handle
 * @param num_steps Number of steps to run
 * @param dt Time step size
 * @param verbose Print progress information (0=false, 1=true)
 * @return Number of steps completed on success, -1 on error
 */
int run_processes_for_steps(ModelHandle handle, int num_steps, double dt, int verbose);

/**
 * Run processes until target time is reached.
 * 
 * @param handle Model handle
 * @param target_time Target simulation time
 * @param dt Time step size
 * @param verbose Print progress information (0=false, 1=true)
 * @return Number of steps completed on success, -1 on error
 */
int run_processes_until_time(ModelHandle handle, double target_time, double dt, int verbose);

/**
 * Apply velocity data to the model.
 * 
 * @param handle Model handle
 * @param coords Pointer to coordinates array (num_points * 3)
 * @param velocities Pointer to velocities array (num_points * 3)
 * @param num_points Number of data points
 * @param timer Time for velocity application
 * @param k Number of nearest neighbors for interpolation
 * @param power Inverse distance weighting power
 * @return 0 on success, -1 on error
 */
int apply_velocity_data(ModelHandle handle, const double* coords, const double* velocities,
                       int num_points, double timer, int k, double power);

/**
 * Get current simulation time.
 * 
 * @param handle Model handle
 * @return Current time on success, -1.0 on error
 */
double get_current_time(ModelHandle handle);

/**
 * Get model time step.
 * 
 * @param handle Model handle
 * @return Time step on success, -1.0 on error
 */
double get_time_step(ModelHandle handle);

/**
 * Create a rotational velocity field for testing.
 * This is a utility function that generates synthetic velocity data.
 * 
 * @param t Current time
 * @param center_x X coordinate of rotation center
 * @param center_y Y coordinate of rotation center
 * @param amplitude Velocity amplitude
 * @param coords Output coordinates array (must be pre-allocated for 100*3 doubles)
 * @param velocities Output velocities array (must be pre-allocated for 100*3 doubles)
 * @return Number of points generated (100), or -1 on error
 */
int create_velocity_field(double t, double center_x, double center_y, double amplitude,
                         double* coords, double* velocities);

#ifdef __cplusplus
}
#endif

#endif // GOSPL_EXTENSIONS_H
