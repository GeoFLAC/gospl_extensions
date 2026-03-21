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

    def run_one_step(self, dt):
        """
        Run goSPL processes for one time step of duration dt.
        
        This method implements the core goSPL processes for a single time step,
        following the same pattern as the original runProcesses() method:
        - Updates paleo elevation tracking
        - Gets tectonics (this sets up solver state)
        - Computes flow accumulation
        - Performs land surface evolution (erosion, transport, deposition)
        - Applies hillslope processes
        - Records stratigraphy and applies flexure
        - Updates forces (tectonic, sea-level, climatic conditions)
        
        :param dt: time step duration
        """
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")
            
        # Check for reasonable dt values to catch numerical issues early
        if dt > 1e10 or dt != dt:  # dt != dt checks for NaN
            raise ValueError(f"dt value appears to be corrupted: {dt}")
            
        # Store original dt to restore later
        original_dt = self.dt
        
        # Validate original dt is reasonable
        if original_dt <= 0 or original_dt > 1e10 or original_dt != original_dt:
            raise ValueError(f"Model dt appears to be corrupted before step: {original_dt}")
            
        # Only temporarily modify dt if necessary
        dt_was_modified = False
        if dt != original_dt:
            self.dt = dt
            dt_was_modified = True
        
        try:
            # 1. Update paleo elevation (needed for proper tracking)
            if hasattr(self, 'updatePaleoZ'):
                self.updatePaleoZ()
                
            # 2. Get tectonics (this is crucial - sets up solver state)
            if hasattr(self, 'getTectonics'):
                self.getTectonics()
            
            # 3. Only proceed with surface processes if not in fast mode
            if not getattr(self, 'fast', False):
                # 4. Compute flow accumulation
                if hasattr(self, 'flowAccumulation'):
                    self.flowAccumulation()
                
                # 5. Perform land surface evolution (erosion and deposition)
                if hasattr(self, 'erodepSPL'):
                    self.erodepSPL()
                
                # 6. Handle sedimentation if not disabled
                if not getattr(self, 'nodep', False):
                    # Second flow accumulation for downstream sediment deposition
                    if hasattr(self, 'flowAccumulation'):
                        self.flowAccumulation()
                    
                    # Sediment deposition inland
                    if hasattr(self, 'sedChange'):
                        self.sedChange()
                    
                    # Marine deposition if enabled
                    if getattr(self, 'seaDepo', False) and hasattr(self, 'seaChange'):
                        self.seaChange()
                
                # 7. Apply hillslope processes (diffusion) - this was causing the PETSc error
                if hasattr(self, 'getHillslope'):
                    self.getHillslope()
            
            # 8. Handle stratigraphy if it's time
            # Check if we need to handle stratigraphy based on current time
            current_save_strat = getattr(self, 'saveStrat', float('inf'))
            if self.tNow >= current_save_strat:
                # Update stratStep and saveStrat as in original runProcesses
                if hasattr(self, 'stratStep'):
                    self.stratStep += 1
                if hasattr(self, 'strat'):
                    self.saveStrat += self.strat
                    
                if hasattr(self, 'getCompaction'):
                    self.getCompaction()
            
            # 9. Apply flexural isostasy if enabled
            if getattr(self, 'flexOn', False) and hasattr(self, 'applyFlexure'):
                self.applyFlexure()
            
            # 10. Update forces (tectonic, sea-level & climatic conditions)
            # Only apply forces if we haven't reached the end time
            if hasattr(self, 'applyForces') and (self.tNow + dt) < self.tEnd:
                self.applyForces()
            
            # 11. Update model time
            self.tNow += dt
            
            # 12. Validate model state after step
            if self.tNow != self.tNow or self.dt != self.dt:  # Check for NaN
                raise ValueError(f"Model state corrupted after step: tNow={self.tNow}, dt={self.dt}")
            
        finally:
            # Restore original dt only if we modified it
            if dt_was_modified:
                self.dt = original_dt

    def runProcessesForDt(self, dt=None, verbose=False, skip_tectonics=False):
        """
        Run goSPL processes for a specific time step dt instead of the full simulation.
        
        This method is similar to runProcesses but runs for only one time step of 
        duration dt, allowing for more granular control over the simulation.
        
        :param dt: time step duration. If None, uses self.dt
        :param verbose: print progress information
        :param skip_tectonics: if True, skip all tectonics-related operations
        :return: elapsed time for the step
        """
        
        if dt is not None and dt <= 0:
            raise ValueError("dt must be positive")
            
        if dt is None:
            dt = self.dt
            
        if verbose:
            print(f"Running processes for dt={dt} from t={self.tNow}")
            if skip_tectonics:
                print("  (skipping tectonics operations)")
        
        # Store originals to restore after the coupling interval
        original_dt   = self.dt
        original_tEnd = self.tEnd

        # If skipping tectonics, we need to temporarily disable tectonics methods
        tectonics_methods_backup = {}
        if skip_tectonics:
            # Backup and disable tectonics-related methods
            tectonics_method_names = [
                'getTectonics', 'applyTectonics', 'updatePaleoZ', 'applyForces',
                '_getTectonics', '_applyTectonics', '_updatePaleoZ', '_applyForces'
            ]

            for method_name in tectonics_method_names:
                if hasattr(self, method_name):
                    tectonics_methods_backup[method_name] = getattr(self, method_name)
                    # Replace with a no-op function
                    setattr(self, method_name, lambda *args, **kwargs: None)

        try:
            # Use the coupling interval as GoSPL's timestep so runProcesses()
            # takes exactly one step of length dt (one GoSPL step per coupling event).
            self.dt   = dt
            self.tEnd = self.tNow + dt

            # Record start time
            tstep = process_time()

            self.runProcesses()

            # Calculate elapsed time
            elapsed_time = process_time() - tstep

            if verbose:
                print(f"  Completed step in {elapsed_time:.3f} seconds, new t={self.tNow}")

            return elapsed_time

        finally:
            # Restore dt and tEnd; tNow is intentionally left advanced
            self.dt   = original_dt
            self.tEnd = original_tEnd

            # Restore tectonics methods if they were disabled
            if skip_tectonics:
                for method_name, original_method in tectonics_methods_backup.items():
                    setattr(self, method_name, original_method)

    def runProcessesForSteps(self, num_steps, dt=None, verbose=False, skip_tectonics=False):
        """
        Run processes for a specified number of time steps.
        
        :param num_steps: number of time steps to run
        :param dt: time step duration (uses self.dt if None)
        :param verbose: whether to print progress information
        :param skip_tectonics: if True, skip all tectonics-related operations
        
        :return: list of elapsed times for each step
        """
        if num_steps <= 0:
            raise ValueError("num_steps must be positive")
            
        if dt is None:
            dt = self.dt
        
        elapsed_times = []
        
        if verbose:
            print(f"Running {num_steps} steps with dt={dt}")
            if skip_tectonics:
                print("  (skipping tectonics operations)")
        
        for step in range(num_steps):
            step_start_time = self.tNow
            elapsed = self.runProcessesForDt(dt, verbose=verbose, skip_tectonics=skip_tectonics)
            elapsed_times.append(elapsed)
            
            if verbose:
                print(f"Step {step+1}/{num_steps}: t={step_start_time:.1f} -> {self.tNow:.1f}")
        
        return elapsed_times

    def runProcessesUntilTime(self, target_time, dt=None, verbose=False, skip_tectonics=False):
        """
        Run processes until a specific target time is reached.
        
        :param target_time: target simulation time to reach
        :param dt: time step duration (uses self.dt if None)  
        :param verbose: whether to print progress information
        :param skip_tectonics: if True, skip all tectonics-related operations
        
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
            if skip_tectonics:
                print("  (skipping tectonics operations)")
        
        while self.tNow < target_time:
            # Adjust dt for final step if necessary
            remaining_time = target_time - self.tNow
            step_dt = min(dt, remaining_time)
            
            step_start_time = self.tNow
            elapsed = self.runProcessesForDt(step_dt, verbose=verbose, skip_tectonics=skip_tectonics)
            elapsed_times.append(elapsed)
            
            step += 1
            if verbose:
                print(f"Step {step}: t={step_start_time:.1f} -> {self.tNow:.1f}")
        
        return elapsed_times

    def interpolate_elevation_to_points(self, src_pts, k=3, power=1.0):
        """
        Interpolate model elevation field to external points using inverse distance weighting.
        
        This method interpolates the current elevation field (self.hGlobal) to arbitrary 
        external points using k-nearest neighbor inverse distance weighting.
        
        :param src_pts: array of shape (N, 3) containing target coordinates [x, y, z]
        :param k: number of nearest neighbors for interpolation (default: 3)
        :param power: inverse distance power exponent (default: 1.0)
        :return: array of shape (N,) containing interpolated elevation values
        """
        # Import scipy.spatial here to avoid requiring it at module level
        try:
            from scipy import spatial
        except ImportError:
            raise ImportError("scipy is required for elevation interpolation")
        
        src_pts = np.asarray(src_pts, dtype=np.float64)
        if src_pts.ndim != 2 or src_pts.shape[1] != 3:
            raise ValueError("src_pts must be of shape (N, 3)")
        
        npts = src_pts.shape[0]
        if npts == 0:
            raise ValueError("src_pts contains no points")
        
        # Get global elevation values as numpy array
        h_values = self.hGlobal.getArray()
        
        # Limit k to available mesh nodes
        k = max(1, min(int(k), self.mCoords.shape[0]))
        
        # Build KDTree from mesh coordinates for efficient nearest neighbor search
        tree = spatial.cKDTree(self.mCoords, leafsize=10)
        distances, idx = tree.query(src_pts, k=k)
        
        # Handle single neighbor case
        if k == 1:
            distances = distances[:, None]
            idx = idx[:, None]
        
        # Inverse distance weighting
        eps = 1.0e-20
        if power == 1.0:
            weights = 1.0 / np.maximum(distances, eps)
        else:
            weights = 1.0 / np.maximum(distances, eps) ** power
        
        # Get elevation values at neighbor nodes
        neigh_elev = h_values[idx]  # (N, k)
        wsum = np.sum(weights, axis=1)  # (N,)
        h_interp = np.sum(weights * neigh_elev, axis=1) / np.maximum(wsum, eps)
        
        # Handle points that coincide exactly with mesh nodes
        onIDs = np.where(distances[:, 0] < eps)[0]
        if onIDs.size > 0:
            h_interp[onIDs] = h_values[idx[onIDs, 0]]
        
        return h_interp

    def apply_elevation_data(self, elevdata, k=3, power=1.0):
        """
        Apply external elevation data to the model's global elevation field.
        
        This method takes elevation data at arbitrary external points and interpolates
        it onto the model mesh nodes, then updates the global elevation field (self.hGlobal).
        This is useful for coupling with external models or applying elevation changes
        from other sources.
        
        Example usage:
            # Create elevation data at specific coordinates
            coords = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 0.0], [2.0, 2.0, 0.0]])
            elevs = np.array([100.0, 150.0, 200.0])
            
            elevdata = {"coords": coords, "elev": elevs}
            model.apply_elevation_data(elevdata, k=3, power=1.0)
            
            # Later, get elevations at other points
            query_coords = np.array([[0.5, 0.5, 0.0], [1.5, 1.5, 0.0]])
            interpolated_elevs = model.get_elevation_at_points(query_coords)
        
        :param elevdata: object or dict with fields/keys 'coords' (N,3) and 'elev' (N,) or 'elevations' (N,)
        :param k: number of nearest neighbors for IDW interpolation (default: 3)
        :param power: inverse distance power exponent (default: 1.0)
        """
        # Import scipy.spatial here to avoid requiring it at module level
        try:
            from scipy import spatial
        except ImportError:
            raise ImportError("scipy is required for elevation interpolation")
        
        # Extract coordinates and elevations from input data
        if isinstance(elevdata, dict):
            src_pts = elevdata.get("coords", None)
            src_elev = elevdata.get("elev", elevdata.get("elevations", None))
        else:
            src_pts = getattr(elevdata, "coords", None)
            src_elev = getattr(elevdata, "elev", getattr(elevdata, "elevations", None))

        if src_pts is None or src_elev is None:
            raise ValueError("elevdata must contain 'coords' and 'elev' (or 'elevations') arrays")

        src_pts = np.asarray(src_pts, dtype=np.float64)
        src_elev = np.asarray(src_elev, dtype=np.float64)
        
        if src_pts.ndim != 2 or src_pts.shape[1] != 3:
            raise ValueError("coords must be of shape (N, 3)")
        if src_elev.ndim != 1:
            raise ValueError("elev must be of shape (N,)")
        if src_pts.shape[0] != src_elev.shape[0]:
            raise ValueError("coords and elev must have the same number of rows")

        nsrc = src_pts.shape[0]
        if nsrc == 0:
            raise ValueError("elevdata contains no samples")
        k = max(1, min(int(k), nsrc))

        # Interpolate elevation data to ALL mesh nodes (global arrays)
        tree = spatial.cKDTree(src_pts, leafsize=10)
        distances, idx = tree.query(self.mCoords, k=k)

        if k == 1:
            distances = distances[:, None]
            idx = idx[:, None]

        # Inverse distance weighting
        eps = 1.0e-20
        if power == 1.0:
            weights = 1.0 / np.maximum(distances, eps)
        else:
            weights = 1.0 / np.maximum(distances, eps) ** power

        neigh_elev = src_elev[idx]  # (M, k)
        wsum = np.sum(weights, axis=1)  # (M,)
        elev_interp = np.sum(weights * neigh_elev, axis=1) / np.maximum(wsum, eps)

        # Handle points that coincide exactly with mesh nodes
        onIDs = np.where(distances[:, 0] < eps)[0]
        if onIDs.size > 0:
            elev_interp[onIDs] = src_elev[idx[onIDs, 0]]

        # Update the global elevation field
        # Get the current elevation array and update it
        h_array = self.hGlobal.getArray()
        h_array[:] = elev_interp[:]
        
        
        # Also update local elevation arrays if they exist
        if hasattr(self, 'hLocal') and hasattr(self, 'locIDs'):
            # Update local elevation array with interpolated values at local node IDs
            h_local_array = self.hLocal.getArray()
            h_local_array[:] = elev_interp[self.locIDs]

        return

    def get_elevation_at_points(self, src_pts, k=3, power=1.0):
        """
        Convenience method that combines getting current elevations and interpolating them.
        
        This is just an alias for interpolate_elevation_to_points to maintain consistency
        with the apply_elevation_data naming pattern.
        
        :param src_pts: array of shape (N, 3) containing target coordinates [x, y, z]
        :param k: number of nearest neighbors for interpolation (default: 3)
        :param power: inverse distance power exponent (default: 1.0)
        :return: array of shape (N,) containing interpolated elevation values
        """
        return self.interpolate_elevation_to_points(src_pts, k=k, power=power)

    # ------------------------------------------------------------------
    # Redesigned coupling API (v2)
    # ------------------------------------------------------------------

    def _get_mesh_tree(self):
        """Return a cached cKDTree of GoSPL mesh coordinates (built once)."""
        if not hasattr(self, '_mesh_kdtree') or self._mesh_kdtree is None:
            from scipy.spatial import cKDTree
            self._mesh_kdtree = cKDTree(self.mCoords, leafsize=10)
        return self._mesh_kdtree

    def set_surface_velocity(self, src_pts, vx_yr, vy_yr, vz_yr, k=3, power=1.0):
        """
        Interpolate all three DES surface velocity components (m/yr) onto the GoSPL
        mesh and store for the next run_and_get_erosion() call.

        - vz_yr is stored as _upsub_override (vertical uplift/subsidence)
        - vx_yr, vy_yr are stored as _vx_override, _vy_override and applied as
          semi-Lagrangian horizontal advection of hGlobal before GoSPL runs.

        :param src_pts: (N, 3) DES surface node coordinates
        :param vx_yr:   (N,)  x-velocity at each DES node in m/yr
        :param vy_yr:   (N,)  y-velocity at each DES node in m/yr
        :param vz_yr:   (N,)  z-velocity (uplift) at each DES node in m/yr
        :param k:       number of IDW neighbours (default 3)
        :param power:   IDW power exponent (default 1.0)
        """
        from scipy.spatial import cKDTree
        src_pts = np.asarray(src_pts, dtype=np.float64)
        vx_yr   = np.asarray(vx_yr,   dtype=np.float64)
        vy_yr   = np.asarray(vy_yr,   dtype=np.float64)
        vz_yr   = np.asarray(vz_yr,   dtype=np.float64)
        k = max(1, min(int(k), src_pts.shape[0]))
        src_tree = cKDTree(src_pts, leafsize=10)
        dists, idxs = src_tree.query(self.mCoords, k=k)
        if k == 1:
            dists = dists[:, None]
            idxs  = idxs[:, None]
        eps = 1.0e-20
        weights = 1.0 / np.maximum(dists, eps) ** power
        onIDs = np.where(dists[:, 0] < eps)[0]
        if onIDs.size > 0:
            weights[onIDs] = 0.0
            weights[onIDs, 0] = 1.0
        weights /= weights.sum(axis=1, keepdims=True)
        self._upsub_override = (weights * vz_yr[idxs]).sum(axis=1)
        self._vx_override    = (weights * vx_yr[idxs]).sum(axis=1)
        self._vy_override    = (weights * vy_yr[idxs]).sum(axis=1)

    def set_uplift_rate(self, src_pts, vz_yr, k=3, power=1.0):
        """
        Interpolate DES vertical velocities (m/yr) onto GoSPL mesh nodes and store
        as self._upsub_override.  Consumed by the next run_and_get_erosion() call
        (which runs GoSPL with skip_tectonics=True so the config-file tectonic
        archive does not overwrite the override).

        :param src_pts: (N, 3) DES surface node coordinates
        :param vz_yr:   (N,)  vertical velocity at each DES node in m/yr
        :param k:       number of IDW neighbours (default 3)
        :param power:   IDW power exponent (default 1.0)
        """
        from scipy.spatial import cKDTree
        src_pts = np.asarray(src_pts, dtype=np.float64)
        vz_yr   = np.asarray(vz_yr,   dtype=np.float64)
        k = max(1, min(int(k), src_pts.shape[0]))
        src_tree = cKDTree(src_pts, leafsize=10)
        dists, idxs = src_tree.query(self.mCoords, k=k)
        if k == 1:
            dists = dists[:, None]
            idxs  = idxs[:, None]
        eps = 1.0e-20
        weights = 1.0 / np.maximum(dists, eps) ** power
        onIDs = np.where(dists[:, 0] < eps)[0]
        if onIDs.size > 0:
            weights[onIDs] = 0.0
            weights[onIDs, 0] = 1.0
        weights /= weights.sum(axis=1, keepdims=True)
        self._upsub_override = (weights * vz_yr[idxs]).sum(axis=1)  # (M,) m/yr, full mesh

    def run_and_get_erosion(self, dt, query_pts, k=3, power=1.0):
        """
        Run GoSPL for *dt* years and return net erosion (metres) at *query_pts*.

        Steps when set_surface_velocity() was called:
          1. Horizontal advection via GoSPL's native _varAdvector (FV scheme):
             sets self.hdisp, calls getfacevelocity, then _varAdvector.
             Falls back to IDW semi-Lagrangian only when advscheme == 0.
          2. Set self.upsub from _upsub_override for GoSPL's native applyTectonics.
          3. Null self.tecdata so getTectonics() returns early (no config overwrite),
             but applyTectonics() still runs and applies the vertical uplift.
          4. Snapshot hGlobal, run GoSPL (skip_tectonics=False), diff on native mesh.
          5. One IDW pass: interpolate delta_h to query_pts.

        When no velocity override is set, GoSPL runs normally with its config-file
        tectonics (skip_tectonics=False).

        :param dt:         coupling interval in years
        :param query_pts:  (N, 3) coordinates at which to return erosion
        :param k:          IDW neighbours (default 3)
        :param power:      IDW power exponent (default 1.0)
        :return:           (N,) array of net erosion in metres (negative = erosion)
        """
        eps = 1.0e-20
        has_vel   = hasattr(self, '_upsub_override') and self._upsub_override is not None
        has_horiz = has_vel and (hasattr(self, '_vx_override') and self._vx_override is not None)

        # --- Horizontal advection ---
        if has_horiz:
            if self.advscheme > 0:
                # Use GoSPL's native FV advector (no extra IDW pass on mesh).
                from gospl._fortran import getfacevelocity
                nodeVel = np.zeros((self.lpoints, 3), dtype=np.float64)
                nodeVel[:, 0] = self._vx_override[self.locIDs]
                nodeVel[:, 1] = self._vy_override[self.locIDs]
                self.hdisp = nodeVel
                getfacevelocity(self.lpoints, nodeVel)
                old_dt = self.dt
                self.dt = dt          # _varAdvector uses self.dt for the time step
                self._varAdvector()
                self.dt = old_dt
                self.hdisp = None
            else:
                # advscheme == 0 (plate semi-Lagrangian): fall back to IDW remap.
                displaced = self.mCoords.copy()
                displaced[:, 0] -= self._vx_override * dt
                displaced[:, 1] -= self._vy_override * dt
                mesh_tree = self._get_mesh_tree()
                k_adv = max(1, min(int(k), self.mCoords.shape[0]))
                adv_dists, adv_idxs = mesh_tree.query(displaced, k=k_adv)
                if k_adv == 1:
                    adv_dists = adv_dists[:, None]
                    adv_idxs  = adv_idxs[:, None]
                adv_w = 1.0 / np.maximum(adv_dists, eps) ** power
                on = np.where(adv_dists[:, 0] < eps)[0]
                if on.size > 0:
                    adv_w[on] = 0.0
                    adv_w[on, 0] = 1.0
                adv_w /= adv_w.sum(axis=1, keepdims=True)
                h = self.hGlobal.getArray()
                h[:] = (adv_w * h[adv_idxs]).sum(axis=1)
                if hasattr(self, 'hLocal') and hasattr(self, 'locIDs'):
                    self.hLocal.getArray()[:] = h[self.locIDs]
            self._vx_override = None
            self._vy_override = None

        # --- Vertical uplift: set self.upsub for GoSPL's native applyTectonics ---
        old_upsub   = getattr(self, 'upsub', None)
        old_tecdata = self.tecdata
        if has_vel:
            self.upsub   = self._upsub_override[self.locIDs]
            # Null tecdata so getTectonics() returns immediately without loading
            # the config-file archive, while applyTectonics() still runs normally.
            self.tecdata = None

        # Snapshot, run, diff on native mesh
        h_before = self.hGlobal.getArray().copy()
        self.runProcessesForDt(dt, verbose=False, skip_tectonics=False)
        h_after  = self.hGlobal.getArray()
        delta_h  = h_after - h_before

        # Strip tectonic uplift so only erosion+diffusion is returned to DES.
        # GoSPL applied upsub*dt to hGlobal internally (via applyTectonics), and
        # DES already has the same displacement from its own mechanical solver —
        # returning the full delta_h would double-count the tectonic uplift.
        # hGlobal.getArray() uses PETSc's internal ordering (indexed by glbIDs),
        # while _upsub_override uses mCoords ordering — use glbIDs to align them.
        if has_vel:
            delta_h = delta_h - self._upsub_override[self.glbIDs] * dt

        # Restore state
        if has_vel:
            self.tecdata        = old_tecdata
            self.upsub          = old_upsub
            self._upsub_override = None

        # Single IDW pass: native-mesh delta_h → query_pts
        query_pts = np.asarray(query_pts, dtype=np.float64)
        tree = self._get_mesh_tree()
        k_q = max(1, min(int(k), self.mCoords.shape[0]))
        dists, idxs = tree.query(query_pts, k=k_q)
        if k_q == 1:
            dists = dists[:, None]
            idxs  = idxs[:, None]
        weights = 1.0 / np.maximum(dists, eps) ** power
        onIDs = np.where(dists[:, 0] < eps)[0]
        if onIDs.size > 0:
            weights[onIDs] = 0.0
            weights[onIDs, 0] = 1.0
        weights /= weights.sum(axis=1, keepdims=True)
        # delta_h is in PETSc global ordering; idxs indexes mCoords.
        # Remap through glbIDs so delta_h[glbIDs[idxs]] gives the correct
        # elevation change for the mCoords node referenced by each idxs entry.
        delta_h_mcoords = delta_h[self.glbIDs]  # mCoords-ordered delta_h
        return (weights * delta_h_mcoords[idxs]).sum(axis=1)  # (N,)

    def apply_drift_correction(self, src_pts, des_elevation, alpha=0.1, k=3, power=1.0):
        """
        Blend hGlobal gently toward the DES elevation without a full reset.

        h_new[i] = h[i] + alpha * (h_des_on_mesh[i] - h[i])

        alpha=1.0 is equivalent to a full reset; alpha≈0.2 is a gentle nudge
        that preserves GoSPL's drainage network (flow accumulation, chi, etc.).

        :param src_pts:       (N, 3) DES surface node coordinates
        :param des_elevation: (N,)  DES elevation at each surface node (metres)
        :param alpha:         blending strength in [0, 1] (default 0.1)
        :param k:             IDW neighbours (default 3)
        :param power:         IDW power exponent (default 1.0)
        """
        from scipy.spatial import cKDTree
        src_pts       = np.asarray(src_pts,       dtype=np.float64)
        des_elevation = np.asarray(des_elevation, dtype=np.float64)
        k = max(1, min(int(k), src_pts.shape[0]))
        src_tree = cKDTree(src_pts, leafsize=10)
        dists, idxs = src_tree.query(self.mCoords, k=k)
        if k == 1:
            dists = dists[:, None]
            idxs  = idxs[:, None]
        eps = 1.0e-20
        weights = 1.0 / np.maximum(dists, eps) ** power
        onIDs = np.where(dists[:, 0] < eps)[0]
        if onIDs.size > 0:
            weights[onIDs] = 0.0
            weights[onIDs, 0] = 1.0
        weights /= weights.sum(axis=1, keepdims=True)
        h_des_on_mesh = (weights * des_elevation[idxs]).sum(axis=1)

        h_array = self.hGlobal.getArray()
        h_array[:] += alpha * (h_des_on_mesh - h_array)
        if hasattr(self, 'hLocal') and self.hLocal is not None:
            h_local = self.hLocal.getArray()
            h_local[:] = h_array[self.locIDs]
