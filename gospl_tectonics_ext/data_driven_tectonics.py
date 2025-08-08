import numpy as np
from scipy import spatial

# Import from gospl package (available when running inside gospl or when installed)
from gospl.mesher.tectonics import Tectonics
from gospl._fortran import getfacevelocity


class DataDrivenTectonics(Tectonics):
    """
    Extends Tectonics with a method to ingest externally provided velocity data
    (positions + 3-component velocities) whose sampling points do not coincide
    with the model mesh nodes. Velocities are interpolated onto the model nodes
    using inverse-distance weighting (k-NN), then applied like getTectonics.
    """

    def apply_velocity_data(self, veldata, timer=None, k=3, power=1.0):
        """
        Apply an external velocity field after interpolating it to the model nodes.

        :arg veldata: object or dict with fields/keys 'coords' (N,3) and 'vel' (N,3)
        :arg timer: time interval used for advscheme==0 semi-Lagrangian setup; defaults to self.dt
        :arg k: number of nearest neighbors for IDW interpolation (default: 3)
        :arg power: inverse distance power exponent (default: 1.0)
        """
        if isinstance(veldata, dict):
            src_pts = veldata.get("coords", None)
            src_vel = veldata.get("vel", None)
        else:
            src_pts = getattr(veldata, "coords", None)
            src_vel = getattr(veldata, "vel", None)

        if src_pts is None or src_vel is None:
            raise ValueError("veldata must contain 'coords' and 'vel' arrays")

        src_pts = np.asarray(src_pts, dtype=np.float64)
        src_vel = np.asarray(src_vel, dtype=np.float64)
        if src_pts.ndim != 2 or src_pts.shape[1] != 3:
            raise ValueError("coords must be of shape (N, 3)")
        if src_vel.ndim != 2 or src_vel.shape[1] != 3:
            raise ValueError("vel must be of shape (N, 3)")
        if src_pts.shape[0] != src_vel.shape[0]:
            raise ValueError("coords and vel must have the same number of rows")

        nsrc = src_pts.shape[0]
        if nsrc == 0:
            raise ValueError("veldata contains no samples")
        k = max(1, min(int(k), nsrc))

        # Interpolate the 3D velocity field at ALL mesh nodes (global arrays)
        tree = spatial.cKDTree(src_pts, leafsize=10)
        distances, idx = tree.query(self.mCoords, k=k)

        if k == 1:
            distances = distances[:, None]
            idx = idx[:, None]

        eps = 1.0e-20
        if power == 1.0:
            weights = 1.0 / np.maximum(distances, eps)
        else:
            weights = 1.0 / np.maximum(distances, eps) ** power

        neigh_vel = src_vel[idx]  # (M, k, 3)
        ws = weights[..., None]   # (M, k, 1)
        wsum = np.sum(weights, axis=1, keepdims=True)  # (M, 1)
        v_interp = np.sum(ws * neigh_vel, axis=1) / np.maximum(wsum, eps)

        onIDs = np.where(distances[:, 0] < eps)[0]
        if onIDs.size > 0:
            v_interp[onIDs] = src_vel[idx[onIDs, 0]]

        # Store local arrays
        self.hdisp = v_interp[self.locIDs, :].copy()
        self.upsub = v_interp[self.locIDs, 2].copy()  # vertical component

        # Route based on advection scheme
        if self.advscheme == 0:
            if timer is None:
                timer = self.dt
            self._readAdvectionData(v_interp, timer)
            self.plateStep = True
            self.plateTimer = self.tNow + timer
        else:
            nodeVel = np.zeros((self.lpoints, 3))
            if self.flatModel:
                nodeVel[:, :2] = self.hdisp[:, :2]
            else:
                nodeVel = self.hdisp.copy()
            getfacevelocity(self.lpoints, nodeVel)
            self._varAdvector()

        return
