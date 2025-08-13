import numpy as np
from time import process_time

# Import from gospl package
from gospl.model import Model

# Additional imports for extended functionality
try:
    from gospl.mesher.tectonics import Tectonics as _Tectonics
    from gospl.mesher.writeMesh import WriteMesh as _WriteMesh
    GOSPL_AVAILABLE = True
except ImportError:
    # Mock these for testing
    _Tectonics = None
    _WriteMesh = None
    GOSPL_AVAILABLE = False


class EnhancedModel(Model):
    """
    Extends Model with a method to run processes for a specific time step dt,
    similar to how DataDrivenTectonics extends Tectonics.
    """

    def runProcessesForDt(self, dt=None, verbose=False):
        """
        Run goSPL processes for a specific time step dt instead of the full simulation.
        
        This method is similar to runProcesses but runs for only one time step of 
        duration dt, allowing for more granular control over the simulation.
        
        :param dt: time step duration. If None, uses self.dt
        :param verbose: print progress information
        :return: elapsed time for the step
        """
        
        if dt is not None and dt <= 0:
            raise ValueError("dt must be positive")
            
        if dt is None:
            dt = self.dt
            
        if verbose:
            print(f"Running processes for dt={dt} from t={self.tNow}")
        
        # Store original dt and tEnd
        original_dt = self.dt
        original_tEnd = self.tEnd
        
        try:
            # Set up for single time step
            self.dt = dt
            target_time = self.tNow + dt
            self.tEnd = target_time
            
            # Record start time
            tstep = process_time()
            
            # Use goSPL's built-in run_one_step method if available
            if hasattr(self, 'run_one_step'):
                self.run_one_step(dt)
            else:
                # Fallback to calling runProcesses for one step
                # This will run until self.tEnd (which we set to tNow + dt)
                self.runProcesses()
            
            # Calculate elapsed time
            elapsed_time = process_time() - tstep
            
            if verbose:
                print(f"  Completed step in {elapsed_time:.3f} seconds, new t={self.tNow}")
                
            return elapsed_time
            
        finally:
            # Restore original values
            self.dt = original_dt
            self.tEnd = original_tEnd

    def runProcessesForSteps(self, num_steps, dt=None, verbose=False):
        """
        Run processes for a specified number of time steps.
        
        :param num_steps: number of time steps to run
        :param dt: time step duration (uses self.dt if None)
        :param verbose: whether to print progress information
        
        :return: list of elapsed times for each step
        """
        if num_steps <= 0:
            raise ValueError("num_steps must be positive")
            
        if dt is None:
            dt = self.dt
        
        elapsed_times = []
        
        if verbose:
            print(f"Running {num_steps} steps with dt={dt}")
        
        for step in range(num_steps):
            step_start_time = self.tNow
            elapsed = self.runProcessesForDt(dt, verbose=verbose)
            elapsed_times.append(elapsed)
            
            if verbose:
                print(f"Step {step+1}/{num_steps}: t={step_start_time:.1f} -> {self.tNow:.1f}")
        
        return elapsed_times

    def runProcessesUntilTime(self, target_time, dt=None, verbose=False):
        """
        Run processes until a specific target time is reached.
        
        :param target_time: target simulation time to reach
        :param dt: time step duration (uses self.dt if None)  
        :param verbose: whether to print progress information
        
        :return: list of elapsed times for each step
        """
        if target_time < 0:
            raise ValueError("target_time must be non-negative")
            
        if dt is None:
            dt = self.dt
        
        if target_time <= self.tNow:
            if verbose:
                print(f"Target time {target_time} is not greater than current time {self.tNow}")
            return []
        
        elapsed_times = []
        step = 0
        
        if verbose:
            print(f"Running from t={self.tNow} to t={target_time} with dt={dt}")
        
        while self.tNow < target_time:
            # Adjust dt for final step if necessary
            remaining_time = target_time - self.tNow
            step_dt = min(dt, remaining_time)
            
            step_start_time = self.tNow
            elapsed = self.runProcessesForDt(step_dt, verbose=verbose)
            elapsed_times.append(elapsed)
            
            step += 1
            if verbose:
                print(f"Step {step}: t={step_start_time:.1f} -> {self.tNow:.1f}")
        
        return elapsed_times
