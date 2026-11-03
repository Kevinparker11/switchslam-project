#!/usr/bin/env python3
"""Publish a ground-truth trajectory as a latched nav_msgs/Path on /gt_path in frame camera_init, for RViz.
usage: gt_path.py GT_FILE      (TUM text 't x y z qx qy qz qw', or the SubT-MRS csv)
The first ground-truth pose is moved to the origin (A-LOAM's camera_init also starts at its first scan), so the trail is
only approximately aligned: the offline ATE uses a best-fit Umeyama alignment over the whole run, which a live view cannot."""
import sys
import csv
import numpy as np

def q2R(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def R2q(R):
    t = np.trace(R)
    if t > 0:
        s = 2 * np.sqrt(t + 1); w = s / 4; x = (R[2, 1]-R[1, 2]) / s; y = (R[0, 2]-R[2, 0]) / s; z = (R[1, 0]-R[0, 1]) / s
    else:
        i = int(np.argmax(np.diag(R))); j, k = (i+1) % 3, (i+2) % 3
        s = 2 * np.sqrt(R[i, i]-R[j, j]-R[k, k]+1); v = np.zeros(4); v[i] = s/4; v[3] = (R[k, j]-R[j, k]) / s
        v[j] = (R[j, i]+R[i, j]) / s; v[k] = (R[k, i]+R[i, k]) / s; x, y, z, w = v
    q = np.array([x, y, z, w]); return q if w >= 0 else -q

def rebase(p, q):
    """express poses (p n x3, q n x4 xyzw) in the frame of the first pose"""
    R0 = q2R(q[0]); P = (p - p[0]) @ R0
    Q = np.array([R2q(R0.T @ q2R(x)) for x in q])
    return P, Q

def load(path):
    with open(path) as f: head = f.readline()
    if "p_w_b_x" in head:
        rows = list(csv.DictReader(open(path)))
        p = np.array([[float(r["p_w_b_x"]), float(r["p_w_b_y"]), float(r["p_w_b_z"])] for r in rows])
        q = np.array([[float(r["q_w_b_x"]), float(r["q_w_b_y"]), float(r["q_w_b_z"]), float(r["q_w_b_w"])] for r in rows])
    else:
        g = np.loadtxt(path, comments="#"); p, q = g[:, 1:4].astype(float), g[:, 4:8].astype(float)
    return p, q

if __name__ == "__main__":
    import rospy
    from nav_msgs.msg import Path
    from geometry_msgs.msg import PoseStamped
    p, q = load(sys.argv[1]); P, Q = rebase(p, q)
    rospy.init_node("gt_path")
    pub = rospy.Publisher("/gt_path", Path, queue_size=1, latch=True)
    m = Path(); m.header.frame_id = "camera_init"; m.header.stamp = rospy.Time.now()
    for a, b in zip(P[::5], Q[::5]):
        s = PoseStamped(); s.header = m.header
        s.pose.position.x, s.pose.position.y, s.pose.position.z = a
        s.pose.orientation.x, s.pose.orientation.y, s.pose.orientation.z, s.pose.orientation.w = b
        m.poses.append(s)
    pub.publish(m); print("gt_path: %d poses published" % len(m.poses), flush=True); rospy.spin()
