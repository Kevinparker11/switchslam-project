#!/usr/bin/env python3
"""
degen_logger.py  -  LiDAR-only degeneracy logger (ROS1 Noetic, python3).

Runs next to the patched A-LOAM (which publishes the 6x6 scan-to-scan Hessian on
/laser_hessian, ordered [rotation(3), translation(3)]). For every Hessian it logs:
  * the full 6x6 H                         -> Schur channel is computed offline
  * the orientation tensor T of the normals of the SAME scan's planar points
    (/laser_cloud_surf_last, published by laserOdometry right after the Hessian)
  * timing: how long T took, so real-time cost is measured on the real run

No VINS, no switching, no ground truth: this is the detector-only log.
T is computed exactly as in the switching node (k=12 PCA normals, 400-point cap),
but with a fixed random seed so repeated runs differ only because A-LOAM differs.

Usage (inside switchslam_gpu_v2):
  python3 -u degen_logger.py _out:=/root/degen_floor01_run1.csv
Optional params: _knn:=12 _subsample:=400 _seed:=0 _surf_topic:=/laser_cloud_surf_last
"""
import csv, time, sys
import numpy as np
import rospy
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2
try:
    from scipy.spatial import cKDTree
except ImportError:
    sys.exit("scipy missing: pip3 install scipy")


def orientation_tensor(pts, k, subsample, rng):
    """T = (1/N) sum n n^T over local-PCA normals of a subsample of the points."""
    if len(pts) < k + 1:
        return None
    tree = cKDTree(pts)
    m = min(len(pts), subsample)
    idx = rng.choice(len(pts), m, replace=False)
    _, nn = tree.query(pts[idx], k=k)                    # (m, k)
    nb = pts[nn]                                         # (m, k, 3)
    nb = nb - nb.mean(axis=1, keepdims=True)
    cov = np.einsum("mki,mkj->mij", nb, nb) / (k - 1)    # (m, 3, 3)
    w, v = np.linalg.eigh(cov)
    n = v[:, :, 0]                                       # smallest-eigenvalue eigenvector = normal
    T = n.T @ n / len(n)
    return T, len(n)


class Logger:
    def __init__(self):
        self.out = rospy.get_param("~out", "/root/degen_log.csv")
        self.k = int(rospy.get_param("~knn", 12))
        self.sub = int(rospy.get_param("~subsample", 400))
        self.rng = np.random.default_rng(int(rospy.get_param("~seed", 0)))
        self.pending = None          # (receipt_time, H) waiting for its scan's planar cloud
        self.n_rows = 0
        self.n_h_dropped = 0
        self.f = open(self.out, "w", newline="")
        self.w = csv.writer(self.f)
        hdr = ["t_scan", "t_hess_recv", "n_surf", "n_normals",
               "T_l1", "T_l2", "T_l3",
               "T_v1x", "T_v1y", "T_v1z",          # eigenvector of the smallest eigenvalue (weak axis, LiDAR frame)
               "B_stat", "T_ms"]
        hdr += [f"H_{i}{j}" for i in range(6) for j in range(6)]
        self.w.writerow(hdr)
        rospy.Subscriber("/laser_hessian", Float64MultiArray, self.on_h, queue_size=50)
        rospy.Subscriber(rospy.get_param("~surf_topic", "/laser_cloud_surf_last"),
                         PointCloud2, self.on_surf, queue_size=50)
        rospy.loginfo("degen_logger -> %s (knn=%d, subsample=%d)", self.out, self.k, self.sub)

    def on_h(self, msg):
        if len(msg.data) != 36:
            rospy.logwarn_throttle(5, "laser_hessian has %d values, expected 36", len(msg.data))
            return
        if self.pending is not None:
            # A-LOAM's laserOdometry solves twice per scan (opti_counter loop), so each scan
            # publishes two Hessians; the later one (final solve) overwrites the earlier.
            self.n_h_dropped += 1
        self.pending = (rospy.get_time(), np.array(msg.data))

    def on_surf(self, msg):
        if self.pending is None:
            return
        t_recv, H = self.pending
        self.pending = None
        pts = np.array(list(pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)),
                       dtype=np.float64)
        t0 = time.perf_counter()
        res = orientation_tensor(pts, self.k, self.sub, self.rng)
        ms = (time.perf_counter() - t0) * 1e3
        if res is None:
            return
        T, n = res
        lam, vec = np.linalg.eigh(T)
        B = 7.5 * n * float(np.sum((lam - 1.0 / 3.0) ** 2))   # Bingham uniformity statistic (15N/2) sum (l-1/3)^2
        row = [f"{msg.header.stamp.to_sec():.6f}", f"{t_recv:.6f}", len(pts), n,
               *[f"{x:.6g}" for x in lam], *[f"{x:.6g}" for x in vec[:, 0]],
               f"{B:.6g}", f"{ms:.3f}"]
        row += [f"{x:.9g}" for x in H]
        self.w.writerow(row)
        self.n_rows += 1
        if self.n_rows % 50 == 0:
            self.f.flush()
            rospy.loginfo("rows=%d  T_l1=%.3f  T_ms=%.1f  superseded_H=%d",
                          self.n_rows, lam[0], ms, self.n_h_dropped)

    def close(self):
        self.f.flush(); self.f.close()
        print(f"saved {self.n_rows} rows to {self.out}; superseded Hessians (expected ~1 per scan): {self.n_h_dropped}")


if __name__ == "__main__":
    rospy.init_node("degen_logger")
    L = Logger()
    rospy.on_shutdown(L.close)
    rospy.spin()
