#!/usr/bin/env python3
"""Offline tests of diag_inputs_window.py: python3 stock_liosam/test_diag_inputs_window.py (from fusion_v4/)."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diag_inputs_window as dw  # noqa: E402


def imu(n=3000, hz=100.0):
    t = 500.0 + np.arange(n) / hz
    gyro = np.zeros((n, 3))
    acc = np.tile([0.0, 0.0, 9.81], (n, 1))
    quat = np.tile([0.0, 0.0, 0.0, 1.0], (n, 1))
    return t, gyro, acc, quat


class Windows(unittest.TestCase):
    def test_quiet_imu_has_clean_windows(self):
        t, g, a, q = imu()
        rows = dw.imu_windows(t, g, a, q, 500.0, window=5.0, span=30.0)
        self.assertEqual(len(rows), 6)
        for r in rows:
            self.assertAlmostEqual(r[1], 500, delta=2)
            self.assertAlmostEqual(r[2], 10.0, delta=0.5)
            self.assertAlmostEqual(r[4], 9.81, delta=1e-6)
            self.assertAlmostEqual(r[6], 0.0, delta=1e-6)

    def test_gap_spike_and_orientation_jump_are_seen_in_their_window(self):
        t, g, a, q = imu()
        keep = ~((t > 512.0) & (t < 513.5))          # 1.5 s without IMU in window 10..15
        t, g, a, q = t[keep], g[keep], a[keep], q[keep]
        g[np.searchsorted(t, 521.0), 0] = 30.0        # gyro spike in window 20..25
        a[np.searchsorted(t, 526.0), 2] = 60.0        # acc spike in window 25..30
        q[np.searchsorted(t, 517.0):, :] = [0.0, 0.0, np.sin(0.5), np.cos(0.5)]   # 1 rad = 57.3 deg yaw jump in window 15..20
        rows = {r[0]: r for r in dw.imu_windows(t, g, a, q, 500.0, 5.0, 30.0)}
        self.assertGreater(rows[10.0][2], 1400.0)
        self.assertLess(rows[0.0][2], 20.0)
        self.assertAlmostEqual(rows[20.0][3], 30.0, delta=1e-6)
        self.assertAlmostEqual(rows[25.0][5], 60.0, delta=1e-6)
        self.assertAlmostEqual(rows[15.0][6], 57.3, delta=0.2)
        self.assertLess(rows[0.0][6], 1e-6)

    def test_lidar_counts_and_sizes(self):
        t = 500.0 + np.arange(300) * 0.1
        size = np.full(300, 75)
        size[(t > 512.0) & (t < 513.0)] = 20
        rows = dw.lidar_windows(t, size, 500.0, 5.0, 30.0)
        self.assertTrue(all(r[1] == 50 for r in rows))
        self.assertEqual(rows[2][2], 20)
        self.assertEqual(rows[0][2], 75)

    def test_spike_samples_are_listed_in_time_order(self):
        t, g, a, q = imu()
        a[1500, 2] = 120.0
        a[1501, 2] = 80.0
        a[900, 0] = 50.0
        rows, total = dw.spike_samples(t, a, g, 500.0, 40.0)
        self.assertEqual(total, 3)
        self.assertEqual([round(r[0], 3) for r in rows], [9.0, 15.0, 15.01])
        self.assertAlmostEqual(rows[1][1], 120.0, delta=0.01)
        self.assertEqual(len(dw.spike_samples(t, a, g, 500.0, 40.0, limit=2)[0]), 2)
        self.assertEqual(dw.spike_samples(t, a, g, 500.0, 200.0)[1], 0)

    def test_empty_window_is_reported_not_dropped(self):
        t, g, a, q = imu(n=500)                      # 5 s of IMU, windows to 30 s
        rows = dw.imu_windows(t, g, a, q, 500.0, 5.0, 30.0)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[-1][1], 0)

    def test_gt_speed_stop_and_turn(self):
        t = np.arange(0.0, 60.0, 0.1) + 1000.0
        sp = np.where(t < 1020.0, 2.0, np.where(t < 1030.0, 0.0, 1.0))       # 2 m/s, stopped 10 s, then 1 m/s
        yaw = np.where(t < 1040.0, 0.0, 0.1 * (t - 1040.0))                  # turns at 0.1 rad/s after 40 s
        dt = np.r_[0.0, np.diff(t)]
        x = np.cumsum(sp * np.cos(yaw) * dt)
        y = np.cumsum(sp * np.sin(yaw) * dt)
        rows = dw.gt_windows(t, np.stack([x, y, np.zeros_like(t)], 1), 5.0, 55.0)
        self.assertAlmostEqual(rows[0][1], 2.0, delta=0.05)
        self.assertAlmostEqual(rows[5][1], 0.0, delta=0.05)                  # 25..30 s stopped
        self.assertAlmostEqual(rows[7][1], 1.0, delta=0.05)
        self.assertLess(rows[0][3], 1.0)
        self.assertAlmostEqual(rows[9][3], 0.1 * 180 / np.pi * 4.0, delta=3.0)   # window 45..50: 4 chord-to-chord changes of 5.7 deg


if __name__ == "__main__":
    unittest.main()
