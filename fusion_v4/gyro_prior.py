"""Gyro-integrated rotation increment between two scan stamps, for the SWI variant of the Switch-SLAM replica.

Why: the paper propagates the LiDAR pose with the IMU (Algorithm 1, "LiDAR propagation"); the A-LOAM stack has only the scan-to-scan
odometry (difference D1 in docs/protocols/SwitchSLAM_Exact_Replica.md).  SWI replaces the ROTATION of the LiDAR increment by the
integrated gyro; the translation stays A-LOAM's.  No bias estimation, no accelerometer, no preintegration of position: gyro only,
over one scan period (about 0.1 s), where a bias of 0.005 rad/s adds 0.0005 rad.  numpy only."""
from collections import deque

import numpy as np

import fusion_core as fc


class GyroBuffer:
    def __init__(self, maxlen=6000, max_gap=0.05):
        self.buf = deque(maxlen=maxlen)           # (t, wx, wy, wz) in the IMU frame, increasing t
        self.max_gap = float(max_gap)             # s: allowed distance between the interval ends and the nearest sample

    def add(self, t, wx, wy, wz):
        if self.buf and t <= self.buf[-1][0]:
            return
        self.buf.append((float(t), float(wx), float(wy), float(wz)))

    def rotation(self, t0, t1):
        """IMU-frame rotation from t0 to t1 (R_I(t0)^T R_I(t1)) by zero-order-hold integration, or None if the samples do not cover
        [t0, t1] (first sample later than t0 + max_gap, last sample earlier than t1 - max_gap, or fewer than 2 samples)."""
        if t1 <= t0 or len(self.buf) < 2:
            return None
        b = self.buf
        if b[0][0] > t0 + self.max_gap or b[-1][0] < t1 - self.max_gap:
            return None
        R = np.eye(3)
        for i in range(len(b)):
            ta = b[i][0]
            tb = b[i + 1][0] if i + 1 < len(b) else max(t1, ta)
            lo, hi = max(ta, t0), min(tb, t1)
            if i == 0 and ta > t0:
                lo = t0                           # before the first sample: hold its rate
            if hi > lo:
                R = R @ fc.so3_exp(np.array(b[i][1:4]) * (hi - lo))
        return R


def to_lidar(dR_I, R_IL):
    """rotation increment of the LiDAR frame from the IMU frame one (x_imu = R_IL x_laser + t): R_IL^T dR_I R_IL"""
    return np.asarray(R_IL).T @ dR_I @ np.asarray(R_IL)
