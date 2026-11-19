#!/usr/bin/env python3
"""Offline tests of the stock LIO-SAM helpers (no ROS, no bags): python3 test_stock_liosam.py  (from fusion_v4/stock_liosam/)"""
import os
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lio_inputs as li
import make_params as mp

BASE = """lio_sam:
  # Topics
  pointCloudTopic: "points_raw"               # Point cloud data
  imuTopic: "imu_raw"                         # IMU data
  odomTopic: "odometry/imu"
  sensor: velodyne
  N_SCAN: 16
  extrinsicTrans: [0.0, 0.0, 0.0]
  extrinsicRot: [-1, 0, 0,
                  0, 1, 0,
                  0, 0, -1]
  extrinsicRPY: [0, -1, 0,
                 1, 0, 0,
                 0, 0, 1]
  # extrinsicRot: [1, 0, 0,
  #                 0, 1, 0,
  #                 0, 0, 1]
  imuGravity: 9.80511
  loopClosureEnableFlag: true
  loopClosureFrequency: 1.0                     # Hz
"""


def Rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


class Params(unittest.TestCase):
    def test_convention_and_untouched_keys(self):
        R, t = Rz(np.pi / 2), np.array([1.0, 2.0, 3.0])
        text, ch = mp.make(BASE, R, t, "/pts", "/imu")
        d = yaml.safe_load(text)["lio_sam"]
        np.testing.assert_allclose(np.array(d["extrinsicRot"]).reshape(3, 3), R.T, atol=1e-8)
        np.testing.assert_allclose(np.array(d["extrinsicRPY"]).reshape(3, 3), R.T, atol=1e-8)
        np.testing.assert_allclose(d["extrinsicTrans"], -R.T @ t, atol=1e-8)
        self.assertEqual((d["pointCloudTopic"], d["imuTopic"], d["loopClosureEnableFlag"]), ("/pts", "/imu", False))
        old = yaml.safe_load(BASE)["lio_sam"]
        for k in old:
            if k not in ("pointCloudTopic", "imuTopic", "extrinsicTrans", "extrinsicRot", "extrinsicRPY", "loopClosureEnableFlag"):
                self.assertEqual(d[k], old[k], k)
        self.assertEqual(len(ch), 6)
        self.assertIn("# extrinsicRot: [1, 0, 0,", text)          # the commented upstream alternative is left alone
        self.assertIn("# Hz", text)                                # trailing comments of untouched keys survive

    def test_imu_point_roundtrip(self):
        # a point at the IMU origin, seen from the lidar, must sit at extTrans in lidar coordinates
        R, t = Rz(0.3), np.array([0.08, 0.03, 0.03])          # p_imu = R p_lidar + t
        rot, rpy, tr = mp.liosam_extrinsics(R, t)
        p_lidar_of_imu_origin = R.T @ (np.zeros(3) - t)
        np.testing.assert_allclose(tr, p_lidar_of_imu_origin, atol=1e-12)

    def test_missing_key_is_an_error(self):
        with self.assertRaises(ValueError):
            mp.make(BASE.replace("imuTopic", "imuTopicX"), np.eye(3), np.zeros(3), "/p", "/i")

    def test_real_upstream_file_if_present(self):
        p = os.environ.get("LIOSAM_PARAMS")
        if p and os.path.exists(p):
            text, ch = mp.make(open(p).read(), np.eye(3), np.zeros(3), "/p", "/i")
            yaml.safe_load(text)
            self.assertEqual(len(ch), 6)


class Clouds(unittest.TestCase):
    F = [("x", 0, 7, 1), ("y", 4, 7, 1), ("z", 8, 7, 1), ("intensity", 12, 7, 1), ("ring", 16, 4, 1), ("time", 20, 7, 1)]

    def make(self, time, nan_rows=()):
        dt = li.cloud_dtype(self.F, 24)
        a = np.zeros(len(time), dtype=dt)
        a["x"], a["y"], a["z"] = np.arange(len(time)), 2.0 * np.arange(len(time)), 0.5
        a["ring"], a["time"] = np.arange(len(time)) % 16, time
        for r in nan_rows:
            a["x"][r] = np.nan
        return a

    def test_report_negative_time_and_nan(self):
        a = self.make(np.linspace(-0.1, 0.0, 10), nan_rows=[3])
        r = li.cloud_report(self.F, 24, a.tobytes(), False)
        self.assertEqual((r["ring"], r["time"], r["nan_points"], r["is_dense"]), ("ok", "negative", 1, False))

    def test_report_ok(self):
        a = self.make(np.linspace(0.0, 0.1, 10))
        r = li.cloud_report(self.F, 24, a.tobytes(), True)
        self.assertEqual((r["time"], r["nan_points"]), ("ok", 0))

    def test_adapt_drops_nan_and_shifts_time_only(self):
        a = self.make(np.linspace(-0.1, 0.0, 10), nan_rows=[3, 7])
        data, n, tmin = li.adapt_cloud(self.F, 24, a.tobytes(), True)
        b = li.cloud_to_array(self.F, 24, data)
        self.assertEqual(n, 8)
        self.assertAlmostEqual(tmin, -0.1, places=6)
        self.assertAlmostEqual(float(b["time"].min()), 0.0, places=6)
        keep = np.isfinite(a["x"])
        np.testing.assert_array_equal(b["x"], a["x"][keep])        # coordinates are not touched
        np.testing.assert_array_equal(b["y"], a["y"][keep])
        np.testing.assert_array_equal(b["ring"], a["ring"][keep])

    def test_adapt_leaves_positive_time_alone(self):
        a = self.make(np.linspace(0.0, 0.1, 10))
        data, n, tmin = li.adapt_cloud(self.F, 24, a.tobytes(), True)
        self.assertEqual((n, tmin), (10, 0.0))
        np.testing.assert_array_equal(li.cloud_to_array(self.F, 24, data)["time"], a["time"])


class Imu(unittest.TestCase):
    def quats(self, n, tilt=0.0):
        yaw = np.linspace(0, 1, n)
        q = np.zeros((n, 4))
        # rotation about x by tilt, then yaw about z (z-y-x order is not needed; any valid attitude works)
        for i, y in enumerate(yaw):
            cz, sz, cx, sx = np.cos(y / 2), np.sin(y / 2), np.cos(tilt / 2), np.sin(tilt / 2)
            q[i] = [cz * sx, sz * sx, sz * cx, cz * cx]       # q = qz * qx  (x, y, z, w)
        return q

    def acc_for(self, q):
        R = li._quat_to_R(q)
        return np.einsum("nji,j->ni", R, np.array([0, 0, 9.8]))   # R^T g: what the accelerometer reads in the body frame

    def test_ok_and_gravity(self):
        q = self.quats(400, tilt=0.5)
        r = li.orientation_verdict(q, np.zeros(400), self.acc_for(q))
        self.assertEqual(r["status"], "ok")
        self.assertLess(r["gravity_err_deg"], 0.5)

    def test_missing_zero_quaternion(self):
        self.assertEqual(li.orientation_verdict(np.zeros((50, 4)), np.zeros(50), np.zeros((50, 3)))["status"], "missing")

    def test_missing_flagged_by_covariance(self):
        q = self.quats(50)
        self.assertEqual(li.orientation_verdict(q, -np.ones(50), self.acc_for(q))["status"], "missing")

    def test_constant_identity(self):
        q = np.tile([0, 0, 0, 1.0], (50, 1))
        self.assertEqual(li.orientation_verdict(q, np.zeros(50), np.tile([0, 0, 9.8], (50, 1)))["status"], "constant")

    def test_wrong_convention_is_visible(self):
        q = self.quats(100, tilt=0.5)
        r = li.orientation_verdict(q, np.zeros(100), np.tile([0, 0, 9.8], (100, 1)))   # accelerometer ignores the tilt
        self.assertGreater(r["gravity_err_deg"], 20)


class Scorer(unittest.TestCase):
    def test_rigid_offset_gives_zero_error(self):
        t = np.arange(0, 60, 0.1)
        p = np.stack([5 * np.cos(t / 6), 5 * np.sin(t / 6), 0.05 * t], 1)
        q = np.tile([0, 0, 0, 1.0], (len(t), 1))
        with tempfile.TemporaryDirectory() as d:
            gt, est = os.path.join(d, "gt.txt"), os.path.join(d, "est.tum")
            np.savetxt(gt, np.column_stack([t + 1000, p, q]), fmt="%.6f")
            p2 = p @ Rz(0.7).T + np.array([3.0, -2.0, 1.0])
            np.savetxt(est, np.column_stack([t + 1000, p2, q]), fmt="%.6f")
            out = subprocess.run([sys.executable, os.path.join(HERE, "score_tum.py"), "--gt", gt, "--est", est],
                                 capture_output=True, text=True, cwd=os.path.join(HERE, ".."))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("RMSE =   0.00 m", out.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
