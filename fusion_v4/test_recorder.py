#!/usr/bin/env python3
"""Tests keyframe_recorder.py without ROS (stubbed messages): PointCloud2 parsing, keyframe rule,
world->body conversion, the npz format, and the round trip into backend_graph.load_keyframes."""
import os
import sys
import tempfile
import types

import numpy as np

# --- stub the ROS modules the recorder imports
for name in ["rospy", "nav_msgs", "nav_msgs.msg", "sensor_msgs", "sensor_msgs.msg"]:
    sys.modules[name] = types.ModuleType(name)
sys.modules["nav_msgs.msg"].Odometry = object
sys.modules["sensor_msgs.msg"].PointCloud2 = object
work = tempfile.mkdtemp()
os.chdir(work)
os.environ["RUN_TAG"] = "TEST"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keyframe_recorder as kr          # noqa: E402
import backend_graph as bg              # noqa: E402
import fusion_core as fc                # noqa: E402


class Stamp:
    def __init__(self, t):
        self.t = t

    def to_sec(self):
        return self.t


class Field:
    def __init__(self, name, offset):
        self.name, self.offset = name, offset


def cloud_msg(t, Pw):
    """PCL PointXYZI layout: x y z (pad) intensity ..., point_step 32"""
    n = len(Pw)
    buf = np.zeros((n, 8), np.float32)
    buf[:, :3] = Pw
    buf[:, 4] = 7.0
    m = types.SimpleNamespace(header=types.SimpleNamespace(stamp=Stamp(t)), width=n, height=1, point_step=32,
                              fields=[Field("x", 0), Field("y", 4), Field("z", 8), Field("intensity", 16)],
                              data=buf.tobytes())
    return m


def odom_msg(t, R, p):
    q = fc.R_to_quat(R)
    return types.SimpleNamespace(header=types.SimpleNamespace(stamp=Stamp(t)),
                                 pose=types.SimpleNamespace(pose=types.SimpleNamespace(
                                     position=types.SimpleNamespace(x=p[0], y=p[1], z=p[2]),
                                     orientation=types.SimpleNamespace(x=q[0], y=q[1], z=q[2], w=q[3]))))


rng = np.random.default_rng(0)
body_scan = rng.uniform(-20, 20, (5000, 3))
body_scan = body_scan[np.linalg.norm(body_scan, axis=1) > 2]
truth = {}
for k in range(60):                        # 0.1 m per scan along x, yawing slowly; 6 m in total
    t = 1000.0 + 0.1 * k
    R = fc.so3_exp([0, 0, 0.01 * k])
    p = np.array([0.1 * k, 0.02 * k, 0.0])
    Pw = body_scan @ R.T + p
    if k % 2 == 0:                          # cloud before pose (as laserMapping publishes)
        kr.cloud_cb(cloud_msg(t, Pw))
        kr.aft_cb(odom_msg(t, R, p))
    else:                                   # pose before cloud
        kr.aft_cb(odom_msg(t, R, p))
        kr.cloud_cb(cloud_msg(t, Pw))
    truth[t] = (R, p)
kr.save()
assert os.path.exists("keyframes_TEST.npz")
K = bg.load_keyframes("keyframes_TEST.npz")
print("keyframes:", len(K["t"]), "at t =", np.round(K["t"] - 1000.0, 1))
assert 5 <= len(K["t"]) <= 7, K["t"]
d = np.diff([truth[t][1][0] for t in K["t"]])
assert np.all(d >= 0.99), d
# each keyframe cloud must be the body-frame scan (voxelised), independent of the pose
ref = kr.voxel_down(body_scan[(np.linalg.norm(body_scan, axis=1) > kr.KF_RMIN)], kr.KF_VOXEL)
from scipy.spatial import cKDTree    # noqa: E402
tree = cKDTree(ref)
for k in range(len(K["t"])):
    dist, _ = tree.query(K["clouds"][k])
    assert np.percentile(dist, 95) < 0.15, (k, np.percentile(dist, 95))
    Rk = K["T_aft"][k][:3, :3]
    assert np.allclose(Rk, truth[K["t"][k]][0], atol=1e-6)
print("size per keyframe: %.1f kB" % (os.path.getsize("keyframes_TEST.npz") / len(K["t"]) / 1024))
print("ALL RECORDER TESTS PASSED")
