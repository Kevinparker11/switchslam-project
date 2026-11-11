"""LiDAR-IMU propagation for the SWF variant of the Switch-SLAM replica (loosely coupled error-state Kalman filter, numpy only).

Why: in the paper the LiDAR initial guess of Algorithm 1 is a LiDAR-IMU propagation (IMU preintegration).  The A-LOAM stack has none: the
guess is A-LOAM's scan-to-scan odometry (difference D1 in docs/protocols/SwitchSLAM_Exact_Replica.md).  The gyro-only SWI variant did
not help on Long Corridor.  This module gives the missing piece in the simplest standard form:

  state    R, p (IMU frame in the pose-chain frame), v (chain frame), gyro bias bg, accelerometer bias ba
  gravity  g, a fixed vector in the chain frame, estimated once from a quiet IMU window (mean specific force) at the first quiet scan
  predict  between two scans: bias-corrected gyro and accelerometer, midpoint integration (the increment handed to Algorithm 1)
  update   after every finished scan with the final pose of the node (position and orientation), 15-state error-state EKF, so v, bg, ba
           are corrected by the LiDAR and the IMU only has to carry the motion over one scan period (about 0.1 s) or a few dropped scans

Not in it: deskewing (A-LOAM does its own constant-velocity deskew), IMU-rate output, any tuning.  The noise values are the project's own
VINS-Mono IMU parameters (acc_n 0.08, gyr_n 0.004, acc_w 4e-5, gyr_w 2e-6, g 9.81007) and a fixed pose noise (0.1 m, 0.01 rad), all set
before the first run and not changed afterwards.  If the IMU samples do not cover a scan, increment() returns None and the replica falls
back to A-LOAM's own increment for that scan.

Conventions: x_imu = R_IL x_laser + t_IL (as everywhere in fusion_v4); the chain pose is the LiDAR pose (R_L, p_L) in the chain frame,
so R_I = R_L R_IL^T and p_I = p_L - R_I t_IL.
"""
from collections import deque

import numpy as np

import fusion_core as fc

I3 = np.eye(3)


class ImuPropagator:
    def __init__(self, R_IL, t_IL, g_norm=9.81007, acc_n=0.08, gyr_n=0.004, acc_w=4e-5, gyr_w=2e-6,
                 sig_p=0.1, sig_th=0.01, init_win=1.0, quiet_g=0.6, quiet_acc_std=0.6, quiet_gyro=0.15, quiet_speed=0.1, max_gap=0.05, maxlen=8000):
        self.R_IL, self.t_IL = np.asarray(R_IL, float), np.asarray(t_IL, float)
        self.g_norm = float(g_norm)
        self.acc_n, self.gyr_n, self.acc_w, self.gyr_w = acc_n, gyr_n, acc_w, gyr_w
        self.sig_p, self.sig_th = sig_p, sig_th
        self.init_win, self.quiet_g, self.quiet_acc_std, self.quiet_gyro, self.max_gap = init_win, quiet_g, quiet_acc_std, quiet_gyro, max_gap
        self.quiet_speed = quiet_speed                   # m/s: mean speed of the LiDAR poses over the window (a slow steady push passes the IMU tests)
        self._ph = deque(maxlen=64)                      # (t, p_L) of the scans offered to try_init
        self.buf = deque(maxlen=maxlen)                  # (t, gx, gy, gz, ax, ay, az), IMU frame, increasing t
        self.ready = False
        self.t = None                                    # stamp of the state (last update)
        self.R = I3.copy(); self.p = np.zeros(3); self.v = np.zeros(3)
        self.bg = np.zeros(3); self.ba = np.zeros(3)
        self.g = np.zeros(3)                             # gravity vector (points down) in the chain frame
        self.P = np.eye(15) * 1e-2
        self.stats = dict(init_tries=0, no_cover=0, updates=0)

    # ------------------------------------------------------------------ input
    def add(self, t, gyro, acc):
        if self.buf and t <= self.buf[-1][0]:
            return
        self.buf.append((float(t), *map(float, gyro), *map(float, acc)))

    def _covers(self, t0, t1):
        b = self.buf
        return len(b) >= 2 and t1 > t0 and b[0][0] <= t0 + self.max_gap and b[-1][0] >= t1 - self.max_gap

    def _segments(self, t0, t1):
        """list of (dt, gyro, acc) with the mean of the two bounding samples on each piece of [t0, t1]; before the first sample the
        first one is held, after the last the last one"""
        b = list(self.buf)
        out = []
        for i in range(len(b)):
            ta = b[i][0]
            tb = b[i + 1][0] if i + 1 < len(b) else max(t1, ta)
            lo, hi = max(ta, t0), min(tb, t1)
            if i == 0 and ta > t0:
                lo = t0
            if hi > lo:
                nxt = b[i + 1] if i + 1 < len(b) else b[i]
                g = 0.5 * (np.array(b[i][1:4]) + np.array(nxt[1:4]))
                a = 0.5 * (np.array(b[i][4:7]) + np.array(nxt[4:7]))
                out.append((hi - lo, g, a))
        return out

    # ------------------------------------------------------------------ initialisation (gravity)
    def try_init(self, t, R_L, p_L):
        """called at every finished scan with its final LiDAR pose until it succeeds; succeeds when the last init_win seconds look quiet: IMU (mean specific force
        near g, small spread, small gyro) and poses (mean speed below quiet_speed).
        Returns True once the filter is running."""
        if self.ready:
            return True
        self.stats["init_tries"] += 1
        self._ph.append((float(t), np.asarray(p_L, float).copy()))
        while self._ph and self._ph[0][0] < t - self.init_win:
            self._ph.popleft()
        if len(self._ph) < 2 or self._ph[-1][0] - self._ph[0][0] < 0.8 * self.init_win:
            return False                                 # the poses must span most of the window to show that the sensor stood still
        if np.linalg.norm(self._ph[-1][1] - self._ph[0][1]) / (self._ph[-1][0] - self._ph[0][0]) > self.quiet_speed:
            return False
        win = [s for s in self.buf if t - self.init_win <= s[0] <= t]
        if len(win) < 20 or win[-1][0] - win[0][0] < 0.8 * self.init_win:
            return False
        G = np.array([s[1:4] for s in win]); A = np.array([s[4:7] for s in win])
        f = A.mean(0)
        if abs(np.linalg.norm(f) - self.g_norm) > self.quiet_g or np.linalg.norm(A.std(0)) > self.quiet_acc_std \
                or np.linalg.norm(G.mean(0)) > self.quiet_gyro:
            return False
        R_I = np.asarray(R_L, float) @ self.R_IL.T
        self.g = -self.g_norm * (R_I @ f) / np.linalg.norm(f)     # at rest R f = -g
        self.bg = G.mean(0)                                          # at rest the gyro reads its bias (earth rate neglected)
        self.ba = np.zeros(3)
        self._set_pose(R_L, p_L)
        self.v = np.zeros(3)
        self.t = float(t)
        self.P = np.diag([1e-4] * 3 + [1e-2] * 3 + [1e-2] * 3 + [1e-4] * 3 + [1e-2] * 3)
        self.ready = True
        return True

    def _set_pose(self, R_L, p_L):
        self.R = np.asarray(R_L, float) @ self.R_IL.T
        self.p = np.asarray(p_L, float) - self.R @ self.t_IL

    # ------------------------------------------------------------------ prediction
    @staticmethod
    def _step(R, p, v, bg, ba, g, dt, w, a):
        """one midpoint step of the nominal state"""
        wc, ac = w - bg, a - ba
        aw = R @ ac + g
        p = p + v * dt + 0.5 * aw * dt * dt
        v = v + aw * dt
        R = R @ fc.so3_exp(wc * dt)
        return R, p, v

    def increment(self, t):
        """IMU-propagated LiDAR-frame increment (dR, dp) from the state stamp to t, or None (not ready / IMU does not cover)"""
        if not self.ready or self.t is None or t <= self.t:
            return None
        if not self._covers(self.t, t):
            self.stats["no_cover"] += 1
            return None
        R, p, v = self.R.copy(), self.p.copy(), self.v.copy()
        for dt, w, a in self._segments(self.t, t):
            R, p, v = self._step(R, p, v, self.bg, self.ba, self.g, dt, w, a)
        dR_I, dp_I = fc.rel_body(self.R, self.p, R, p)
        return fc.imu_to_lidar_increment(dR_I, dp_I, self.R_IL, self.t_IL)

    # ------------------------------------------------------------------ update
    def update(self, t, R_L, p_L):
        """propagate the state (and covariance) to t, then correct it with the final LiDAR pose of the scan.  Returns diagnostics,
        or None if not ready / the IMU does not cover [state stamp, t] (then the state is re-seeded on the pose, velocity kept)."""
        if not self.ready:
            return None
        if t <= self.t:
            return None
        R_m = np.asarray(R_L, float) @ self.R_IL.T
        p_m = np.asarray(p_L, float) - R_m @ self.t_IL
        if not self._covers(self.t, t):
            self.stats["no_cover"] += 1
            self.R, self.p, self.t = R_m, p_m, float(t)       # no IMU between the two stamps: take the pose, keep v, bg, ba
            return dict(innov_th=np.nan, innov_p=np.nan, covered=False)
        for dt, w, a in self._segments(self.t, t):
            F = np.eye(15)
            wc, ac = w - self.bg, a - self.ba
            F[0:3, 0:3] = fc.so3_exp(-wc * dt)
            F[0:3, 9:12] = -I3 * dt
            F[3:6, 6:9] = I3 * dt
            F[6:9, 0:3] = -self.R @ fc.skew(ac) * dt
            F[6:9, 12:15] = -self.R * dt
            Q = np.zeros((15, 15))
            Q[0:3, 0:3] = I3 * self.gyr_n ** 2 * dt
            Q[6:9, 6:9] = I3 * self.acc_n ** 2 * dt
            Q[9:12, 9:12] = I3 * self.gyr_w ** 2 * dt
            Q[12:15, 12:15] = I3 * self.acc_w ** 2 * dt
            self.P = F @ self.P @ F.T + Q
            self.R, self.p, self.v = self._step(self.R, self.p, self.v, self.bg, self.ba, self.g, dt, w, a)
        r = np.concatenate([fc.so3_log(self.R.T @ R_m), p_m - self.p])
        H = np.zeros((6, 15)); H[0:3, 0:3] = I3; H[3:6, 3:6] = I3
        Rn = np.diag([self.sig_th ** 2] * 3 + [self.sig_p ** 2] * 3)
        S = H @ self.P @ H.T + Rn
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ r
        self.R = self.R @ fc.so3_exp(dx[0:3])
        U, _, Vt = np.linalg.svd(self.R); self.R = U @ Vt
        self.p = self.p + dx[3:6]
        self.v = self.v + dx[6:9]
        self.bg = self.bg + dx[9:12]
        self.ba = self.ba + dx[12:15]
        IKH = np.eye(15) - K @ H
        self.P = IKH @ self.P @ IKH.T + K @ Rn @ K.T            # Joseph form
        self.P = 0.5 * (self.P + self.P.T)
        self.t = float(t)
        self.stats["updates"] += 1
        return dict(innov_th=float(np.linalg.norm(r[:3])), innov_p=float(np.linalg.norm(r[3:])), covered=True)
