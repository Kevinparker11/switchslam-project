#!/usr/bin/env python3
"""fusion_node_v2: VIO-primary, degeneracy-gated, information-weighted LiDAR correction.

Replaces the switching node.  Same feedback loop as before: A-LOAM's laserMapping reads our
/switch_fused_pose as its odometry (launch remap), we read its scan-to-map output /aft_mapped_to_init.

Per mapped scan k (all in the LiDAR body frame, so world frames never mix):
  dT_lidar = relative scan-to-map motion k-1 -> k
  dT_vio   = VINS-Mono IMU motion k-1 -> k (interpolated to the scan times), moved to the LiDAR frame
  WARMUP   (no VINS yet, or < T_WARM s since VINS (re)started): use dT_lidar
  VO_FAIL  (VINS missing / jump / re-initialised): use dT_lidar, warm-up restarts when VINS returns
  FUSED    : gate = kappa(S_RR) <= KAPPA_TH (fixed, or Otsu online);  W = (c S + I)^-1 c S per Schur block
             dt = W_t dt_lidar + (I - W_t) dt_vio ;  dphi likewise with W_R (C_R = 0 -> VINS rotation)
Environment (all optional):
  FUSION_MODE   fused | vins | lidar          (vins: C_T=C_R=0;  lidar: always dT_lidar)
  C_T, C_R      LiDAR information scale for translation / rotation   (default 1e-3 / 0)
  KAPPA_MODE    fixed | otsu ;  KAPPA_TH (default 15.7)
  T_WARM        seconds of LiDAR-only after VINS (re)starts (default 20)
  HESS_TOPIC    /laser_hessian (default, scan-to-scan, body frame) or /mapping_hessian (scan-to-map, world frame)
  PREDICT_WITH_VINS  1 (default): initial guess for mapping = fused pose moved by VINS motion; 0: last fused pose
  JUMP_MAX      m per scan for a VINS/LiDAR step to be accepted (default 1.0)
  RUN_TAG       log name suffix
Extrinsic: SubT-MRS Multi Floor 'laser_to_imu' (override with EXTRINSIC_YAML=path to the same format).
"""
import os
import csv
import threading
from collections import deque

import numpy as np
import rospy
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray

import fusion_core as fc

E = os.environ.get
MODE = E("FUSION_MODE", "fused")
C_T = float(E("C_T", "1e-3"))
C_R = float(E("C_R", "0"))
if MODE == "vins":
    C_T = C_R = 0.0
KAPPA_MODE = E("KAPPA_MODE", "fixed")
KAPPA_TH = float(E("KAPPA_TH", "15.7"))
T_WARM = float(E("T_WARM", "20"))
HESS_TOPIC = E("HESS_TOPIC", "/laser_hessian")
HESS_FRAME = "world" if "mapping" in HESS_TOPIC else "body"
PREDICT_WITH_VINS = E("PREDICT_WITH_VINS", "1") == "1"
JUMP_MAX = float(E("JUMP_MAX", "1.0"))
RUN_TAG = E("RUN_TAG", "fusion_v2")
VINS_GAP = 1.0            # s without VINS -> treated as lost (warm-up restarts)

# SubT-MRS Hawkins Multi Floor laser_to_imu (x_imu = R x_laser + t)
T_LI = np.array([[0.999945562, 0.009074807, 0.005149763, 0.080],
                 [-0.009060897, 0.999955255, -0.002718066, 0.029],
                 [-0.005174199, 0.002671256, 0.999983046, 0.030],
                 [0, 0, 0, 1.0]])
if E("EXTRINSIC_YAML"):
    import yaml
    with open(E("EXTRINSIC_YAML")) as f:
        T_LI = np.array(yaml.safe_load(f.read().replace("%YAML 1.2", ""))["laser_to_imu"]["data"]).reshape(4, 4)
U, _, Vt = np.linalg.svd(T_LI[:3, :3])
R_IL, t_IL = U @ Vt, T_LI[:3, 3].copy()

lock = threading.Lock()
gate = fc.KappaGate(kth=KAPPA_TH, mode=KAPPA_MODE)
core = fc.FusionCore(R_IL, t_IL, c_t=C_T, c_R=C_R, gate=gate, t_warm=T_WARM, hess_frame=HESS_FRAME,
                     jump_max=JUMP_MAX)
if MODE == "lidar":
    core.t_warm = 1e12                     # every step is WARMUP = LiDAR only

vins_buf = deque(maxlen=400)               # (t, R, p) IMU poses in the VINS world
latest_H = [None, None, None]              # H, cost, m
pub = [None]

log_path = "switching_log_v2_%s.csv" % RUN_TAG
log = open(log_path, "w", newline="")
w = csv.writer(log)
HCOLS = ["Hl_%d%d" % (i, j) for i in range(6) for j in range(6)]
w.writerow(["time", "mode", "fused_x", "fused_y", "fused_z", "fused_qx", "fused_qy", "fused_qz", "fused_qw",
            "aft_x", "aft_y", "aft_z", "aft_qx", "aft_qy", "aft_qz", "aft_qw",
            "v_px", "v_py", "v_pz", "v_qx", "v_qy", "v_qz", "v_qw",
            "gate", "kappa_R", "kappa_t", "kth", "wt0", "wt1", "wt2", "wR0", "wR1", "wR2", "dta", "dtv",
            "hess_src", "cost", "m_res"] + HCOLS)
cnt = [0]


def odom_to_pose(msg):
    p, q = msg.pose.pose.position, msg.pose.pose.orientation
    return fc.quat_to_R([q.x, q.y, q.z, q.w]), np.array([p.x, p.y, p.z])


def vins_at(t):
    """IMU pose interpolated at time t, or None if VINS is absent/stale"""
    if not vins_buf:
        return None
    if t - vins_buf[-1][0] > VINS_GAP:
        return None
    if t >= vins_buf[-1][0]:
        return vins_buf[-1][1], vins_buf[-1][2]
    for i in range(len(vins_buf) - 1, 0, -1):
        t0, R0, p0 = vins_buf[i - 1]
        t1, R1, p1 = vins_buf[i]
        if t0 <= t <= t1:
            if t1 - t0 > VINS_GAP:
                return None
            return fc.interp_pose(t, t0, R0, p0, t1, R1, p1)
    return None


def vins_cb(msg):
    R, p = odom_to_pose(msg)
    with lock:
        vins_buf.append((msg.header.stamp.to_sec(), R, p))


def hess_cb(msg):
    d = np.array(msg.data, float)
    with lock:
        latest_H[0] = d[:36].reshape(6, 6)
        latest_H[1] = d[36] if len(d) > 36 else np.nan
        latest_H[2] = d[37] if len(d) > 37 else np.nan


def publish(stamp, R, p):
    q = fc.R_to_quat(R)
    om = Odometry()
    om.header.stamp = stamp
    om.header.frame_id = "camera_init"
    om.child_frame_id = "/laser_odom"
    om.pose.pose.position.x, om.pose.pose.position.y, om.pose.pose.position.z = p
    om.pose.pose.orientation.x, om.pose.pose.orientation.y, om.pose.pose.orientation.z, om.pose.pose.orientation.w = q
    pub[0].publish(om)


def laser_odom_cb(msg):
    """A-LOAM scan-to-scan odometry arrives once per scan: publish the initial guess for mapping
    with the same stamp (laserMapping matches odometry and cloud by stamp)."""
    t = msg.header.stamp.to_sec()
    with lock:
        if not core.initialised():
            R, p = odom_to_pose(msg)            # before the first mapped scan: pass A-LOAM odometry through
        else:
            pred = core.predict(vins_at(t) if PREDICT_WITH_VINS else None)
            R, p = pred
    publish(msg.header.stamp, R, p)


def aft_cb(msg):
    t = msg.header.stamp.to_sec()
    Ra, pa = odom_to_pose(msg)
    with lock:
        v = vins_at(t)
        H = latest_H[0]
        R, p, info = core.step(t, (Ra, pa), v, H)
        cost, mres = latest_H[1], latest_H[2]
    vq = fc.R_to_quat(v[0]) if v is not None else [np.nan] * 4
    vp = v[1] if v is not None else [np.nan] * 3
    Hrow = list(H.ravel()) if H is not None else [np.nan] * 36
    w.writerow([t, info["mode"], *p, *fc.R_to_quat(R), *pa, *fc.R_to_quat(Ra), *vp, *vq,
                info["gate"], info["kappa_R"], info["kappa_t"], info["kth"], *info["wt"], *info["wR"],
                info["dta"], info["dtv"], HESS_TOPIC, cost, mres] + Hrow)
    cnt[0] += 1
    if cnt[0] % 50 == 0:
        log.flush()
        rospy.loginfo("[%d] %s gate=%s kR=%.1f kth=%.1f p=(%.2f %.2f %.2f)", cnt[0], info["mode"], info["gate"],
                      info["kappa_R"] if np.isfinite(info["kappa_R"]) else -1, info["kth"] if np.isfinite(info["kth"]) else -1, *p)


def main():
    rospy.init_node("fusion_node_v2", anonymous=True)
    pub[0] = rospy.Publisher("/switch_fused_pose", Odometry, queue_size=50)
    rospy.Subscriber("/vins_estimator/odometry", Odometry, vins_cb, queue_size=200)
    rospy.Subscriber(HESS_TOPIC, Float64MultiArray, hess_cb, queue_size=50)
    rospy.Subscriber("/laser_odom_to_init", Odometry, laser_odom_cb, queue_size=50)
    rospy.Subscriber("/aft_mapped_to_init", Odometry, aft_cb, queue_size=50)
    print("FUSION_MODE=%s C_T=%g C_R=%g KAPPA_MODE=%s KAPPA_TH=%g T_WARM=%g HESS_TOPIC=%s PREDICT_WITH_VINS=%d RUN_TAG=%s"
          % (MODE, C_T, C_R, KAPPA_MODE, KAPPA_TH, T_WARM, HESS_TOPIC, PREDICT_WITH_VINS, RUN_TAG))
    print("fusion_node_v2 listening...")
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    finally:
        log.close()
        print("Saved", log_path)
