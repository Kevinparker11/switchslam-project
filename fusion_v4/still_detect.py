"""IMU standstill detector for the F25 standstill hold (FusionCore zupt).

Still = over the last `window` s the IMU is quiet: mean |gyro| below g_thr (rad/s) AND the standard deviation of |accel| below
a_thr (m/s^2).  An IMU alone cannot tell standing from a smooth constant-speed run, so FusionCore additionally requires that the
LiDAR path is a wander (net displacement well below path length) before it holds the pose.  The thresholds are NOT set here: they
are read off the recorded IMU of the sequences with imu_still_scan.py (stationary windows against moving windows from ground
truth).  numpy only."""
from collections import deque

import numpy as np


class StillDetector:
    def __init__(self, window=1.0, g_thr=0.02, a_thr=0.1, min_n=20, maxlen=4000):
        self.window, self.g_thr, self.a_thr, self.min_n = float(window), float(g_thr), float(a_thr), int(min_n)
        self.buf = deque(maxlen=maxlen)           # (t, |gyro|, |accel|)

    def add(self, t, gyro, acc):
        if self.buf and t <= self.buf[-1][0]:
            return
        self.buf.append((float(t), float(np.linalg.norm(gyro)), float(np.linalg.norm(acc))))

    def stats(self, t):
        """(mean |gyro|, std |accel|, n) over (t - window, t]; (nan, nan, n) if the window is not covered"""
        s = [b for b in self.buf if t - self.window < b[0] <= t]
        if len(s) < self.min_n or s[-1][0] - s[0][0] < 0.8 * self.window or t - s[-1][0] > 0.25 * self.window:
            return float("nan"), float("nan"), len(s)
        return float(np.mean([x[1] for x in s])), float(np.std([x[2] for x in s])), len(s)

    def still(self, t):
        g, a, n = self.stats(t)
        return bool(np.isfinite(g) and g < self.g_thr and a < self.a_thr)
