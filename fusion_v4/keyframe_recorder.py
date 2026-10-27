#!/usr/bin/env python3
"""keyframe_recorder: saves A-LOAM's registered scans as body-frame keyframes for the offline back end
(loop closure + pose graph, backend_graph.py).  Runs next to fusion_node_v2 during one bag replay and
does not publish anything, so it cannot change the run.

Keyframe rule: every KF_DIST m (default 1.0) or KF_ROT rad (default 0.2) of A-LOAM scan-to-map motion.
Each keyframe stores: scan time, A-LOAM pose (x y z qx qy qz qw), and the full-resolution scan from
/velodyne_cloud_registered moved back into the LiDAR body frame with that same pose, voxel-downsampled
(KF_VOXEL m, default 0.25), range-limited (KF_RMIN..KF_RMAX m), capped at KF_MAXPTS points and stored as
int16 centimetres.
Output: keyframes_<RUN_TAG>.npz in the working directory, rewritten every 25 keyframes and on shutdown.
"""
import os
import threading
from collections import deque

import numpy as np
import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2

E = os.environ.get
RUN_TAG = E("RUN_TAG", "kf")
KF_DIST = float(E("KF_DIST", "1.0"))
KF_ROT = float(E("KF_ROT", "0.2"))
KF_VOXEL = float(E("KF_VOXEL", "0.25"))
KF_RMIN, KF_RMAX = float(E("KF_RMIN", "1.0")), float(E("KF_RMAX", "60.0"))
KF_MAXPTS = int(E("KF_MAXPTS", "10000"))
OUT = "keyframes_%s.npz" % RUN_TAG
SCALE = 0.01                       # metres per int16 unit

lock = threading.Lock()
clouds = deque(maxlen=30)          # (stamp, msg) of recent registered scans
pending = {}                       # stamp -> (R, p) of keyframes whose scan has not arrived yet
kf_t, kf_pose, kf_pts = [], [], []
last = [None]


def quat_to_R(x, y, z, w):
    n = np.sqrt(x * x + y * y + z * z + w * w)
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def xyz(msg):
    off = {f.name: f.offset for f in msg.fields}
    dt = np.dtype({"names": ["x", "y", "z"], "formats": ["<f4"] * 3,
                   "offsets": [off["x"], off["y"], off["z"]], "itemsize": msg.point_step})
    a = np.frombuffer(msg.data, dtype=dt, count=msg.width * msg.height)
    P = np.stack([a["x"], a["y"], a["z"]], 1).astype(np.float64)
    return P[np.isfinite(P).all(1)]


def voxel_down(P, v):
    k = np.floor(P / v).astype(np.int64) + (1 << 20)
    key = (k[:, 0] << 42) | (k[:, 1] << 21) | k[:, 2]
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    out = np.zeros((len(cnt), 3))
    np.add.at(out, inv.ravel(), P)
    return out / cnt[:, None]


def add_keyframe(stamp, R, p, msg):
    Pw = xyz(msg)
    Pb = (Pw - p) @ R                                  # world (camera_init) -> LiDAR body
    r = np.linalg.norm(Pb, axis=1)
    Pb = Pb[(r > KF_RMIN) & (r < KF_RMAX)]
    Pb = voxel_down(Pb, KF_VOXEL)
    if len(Pb) > KF_MAXPTS:
        Pb = Pb[np.random.default_rng(len(kf_t)).choice(len(Pb), KF_MAXPTS, replace=False)]
    q = rot_to_quat(R)
    kf_t.append(stamp)
    kf_pose.append(np.r_[p, q])
    kf_pts.append(np.clip(np.round(Pb / SCALE), -32767, 32767).astype(np.int16))
    if len(kf_t) % 25 == 0:
        save()


def rot_to_quat(R):
    tr = np.trace(R)
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        w, x, y, z = 0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        w, x, y, z = (R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        w, x, y, z = (R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        w, x, y, z = (R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s
    return np.array([x, y, z, w])


def save():
    if not kf_t:
        return
    n = np.array([len(a) for a in kf_pts], np.int32)
    tmp = OUT + ".tmp.npz"
    np.savez_compressed(tmp, t=np.array(kf_t), pose=np.array(kf_pose), n=n, pts=np.vstack(kf_pts),
                        scale=SCALE, voxel=KF_VOXEL, kf_dist=KF_DIST, kf_rot=KF_ROT)
    os.replace(tmp, OUT)


def cloud_cb(msg):
    st = msg.header.stamp.to_sec()
    with lock:
        if st in pending:
            R, p = pending.pop(st)
            add_keyframe(st, R, p, msg)
        else:
            clouds.append((st, msg))


def aft_cb(msg):
    st = msg.header.stamp.to_sec()
    o, q = msg.pose.pose.position, msg.pose.pose.orientation
    R, p = quat_to_R(q.x, q.y, q.z, q.w), np.array([o.x, o.y, o.z])
    with lock:
        if last[0] is not None:
            R0, p0 = last[0]
            dR = R0.T @ R
            ang = np.arccos(np.clip((np.trace(dR) - 1) / 2, -1, 1))
            if np.linalg.norm(p - p0) < KF_DIST and ang < KF_ROT:
                return
        last[0] = (R, p)
        for s, m in clouds:
            if s == st:
                add_keyframe(st, R, p, m)
                return
        pending[st] = (R, p)
        for s in [s for s in pending if s < st - 2.0]:      # scan never arrived
            pending.pop(s)


def main():
    rospy.init_node("keyframe_recorder", anonymous=True)
    rospy.Subscriber("/velodyne_cloud_registered", PointCloud2, cloud_cb, queue_size=20, buff_size=2 ** 24)
    rospy.Subscriber("/aft_mapped_to_init", Odometry, aft_cb, queue_size=50)
    rospy.on_shutdown(lambda: (save(), print("keyframe_recorder saved %d keyframes to %s" % (len(kf_t), OUT))))
    print("keyframe_recorder listening (KF_DIST=%g KF_ROT=%g KF_VOXEL=%g) -> %s" % (KF_DIST, KF_ROT, KF_VOXEL, OUT))
    rospy.spin()


if __name__ == "__main__":
    main()
