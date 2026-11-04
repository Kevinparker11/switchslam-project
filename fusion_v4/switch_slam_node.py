#!/usr/bin/env python3
"""switch_slam_node: Switch-SLAM's switching node (Lee et al., RA-L 2024) in place of fusion_node_v2.

Same wiring as fusion_node_v2 (A-LOAM's laserMapping reads /switch_fused_pose as its odometry, this node reads
/aft_mapped_to_init), so the A-LOAM build, the VINS-Mono configuration, the extrinsics, the replay rates, the keyframe recorder and
the scoring are identical to the F-configs and only the fusion rule differs.  The rule is switch_slam_core.SwitchSlamCore
(Algorithm 1 and Eqs. 11-16).  No warm-up, no weights, no SAH, no orientation tensor, no guards: none of them is in the paper.

Environment (all optional):
  HESS_TOPIC   /laser_hessian (default: scan-to-scan Hessian of the patched laserOdometry, body frame, available with every scan)
               or /mapping_hessian (scan-to-map Hessian of the patched laserMapping, the quantity the paper uses; needs
               fusion_v3/patch_mapping_hessian.py applied to A-LOAM)
  N_BUF        length of the status queue Q_s (default 5; the paper does not give it)
  LT_MODE      published (default, [0.12, 0.27, 0.48] as printed) | formula (Eq. 12 evaluated: [0.116, 0.271, 0.471])
  EQ15_W       weight of the LiDAR step in Eq. 15 (default 0.5 = the literal reading, mean of the two steps)
  GYRO         1 = SWI variant: rotation of the LiDAR increment from the integrated gyro (IMU_TOPICS, default /imu/data,/cmu_sp1/imu/data)
  RUN_TAG      log name suffix
  EXTRINSIC_YAML  same format as fusion_node_v2 (default SubT-MRS Multi Floor laser_to_imu)
"""
import csv
import os
import threading
from collections import OrderedDict, deque

import numpy as np
import rospy
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray

import fusion_core as fc
import switch_slam_core as sw
import gyro_prior as gp

E = os.environ.get
HESS_TOPIC = E("HESS_TOPIC", "/laser_hessian")
HESS_FRAME = "world" if "mapping" in HESS_TOPIC else "body"
N_BUF = int(E("N_BUF", "5"))
LT_MODE = E("LT_MODE", "published")
EQ15_W = float(E("EQ15_W", "0.5"))
RUN_TAG = E("RUN_TAG", "SW")
GYRO = E("GYRO", "0") == "1"                  # SWI: rotation of the LiDAR increment from the integrated gyro (docs section 12)
IMU_TOPICS = E("IMU_TOPICS", "/imu/data,/cmu_sp1/imu/data").split(",")
VINS_GAP = 1.0                      # s without a VINS-Mono pose -> S_vo = fail

T_LI = np.array([[0.999945562, 0.009074807, 0.005149763, 0.080],
                 [-0.009060897, 0.999955255, -0.002718066, 0.029],
                 [-0.005174199, 0.002671256, 0.999983046, 0.030],
                 [0, 0, 0, 1.0]])
if E("EXTRINSIC_YAML"):
    import yaml
    with open(E("EXTRINSIC_YAML")) as f:
        T_LI = np.array(yaml.safe_load(f.read().replace("%YAML 1.2", ""))["laser_to_imu"]["data"]).reshape(4, 4)
U_, _, Vt_ = np.linalg.svd(T_LI[:3, :3])
R_IL, t_IL = U_ @ Vt_, T_LI[:3, 3].copy()

lt = sw.LT_PUBLISHED if LT_MODE == "published" else sw.thresholds_from_formula()
core = sw.SwitchSlamCore(R_IL, t_IL, n_buf=N_BUF, lt=lt, eq15_w=EQ15_W, hess_frame=HESS_FRAME)
lock = threading.Lock()
gyro_buf = gp.GyroBuffer()
vins_buf = deque(maxlen=400)
odoms, pubs, decs = OrderedDict(), OrderedDict(), OrderedDict()
latest_H = [None, np.nan, np.nan]
pub = [None]
stats = dict(rows=0, race=0, no_dec=0)

log_path = "switching_log_v2_%s.csv" % RUN_TAG
log = open(log_path, "w", newline="")
w = csv.writer(log)
HCOLS = ["Hl_%d%d" % (i, j) for i in range(6) for j in range(6)]
w.writerow(["time", "mode", "fused_x", "fused_y", "fused_z", "fused_qx", "fused_qy", "fused_qz", "fused_qw",
            "aft_x", "aft_y", "aft_z", "aft_qx", "aft_qy", "aft_qz", "aft_qw",
            "v_px", "v_py", "v_pz", "v_qx", "v_qy", "v_qz", "v_qw",
            "gate", "kappa_R", "kappa_t", "kth", "wt0", "wt1", "wt2", "wR0", "wR1", "wR2", "dta", "dtv",
            "hess_src", "cost", "m_res"] + HCOLS + ["sah_corr_deg", "sah_total_deg", "sah_acc"] +
           ["sw_case", "sw_status", "sw_vo_fail", "sw_lam1", "sw_lam2", "sw_lam3", "sw_w", "sw_degen", "sw_race", "sw_gyro", "sw_gyro_deg"])


def odom_to_pose(msg):
    p, q = msg.pose.pose.position, msg.pose.pose.orientation
    return fc.quat_to_R([q.x, q.y, q.z, q.w]), np.array([p.x, p.y, p.z])


def vins_at(t):
    """IMU pose interpolated at time t, or None if VINS-Mono is absent/stale (S_vo = fail)"""
    if not vins_buf or t - vins_buf[-1][0] > VINS_GAP:
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


def imu_cb(msg):
    a = msg.angular_velocity
    with lock:
        gyro_buf.add(msg.header.stamp.to_sec(), a.x, a.y, a.z)


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


def prune(d, t, keep=8.0):
    for k in [k for k in d if k < t - keep]:
        d.pop(k)


def laser_odom_cb(msg):
    """one A-LOAM scan-to-scan odometry per scan: Algorithm 1 lines 1-8, then publish the initial guess for the mapping"""
    t = msg.header.stamp.to_sec()
    O = odom_to_pose(msg)
    with lock:
        odoms[t] = O
        if not core.initialised():
            P = O                                            # before the first mapped scan: pass A-LOAM's odometry through
        else:
            H = None if latest_H[0] is None else latest_H[0].copy()
            dR_L = None
            if GYRO and core.prev_t is not None:
                dR_I = gyro_buf.rotation(core.prev_t, t)
                dR_L = None if dR_I is None else gp.to_lidar(dR_I, R_IL)
            dec = core.decide(O, vins_at(t), H, gyro_dR=dR_L, t=t)
            dec["H"] = H
            dec["race"] = len(decs) > 0                      # an earlier scan is still being mapped: its T_w_odom is not in yet
            P = core.pose_to_publish(dec["guess"])
            decs[t] = dec
        pubs[t] = P
        prune(odoms, t); prune(pubs, t); prune(decs, t)
    publish(msg.header.stamp, P[0], P[1])


def aft_cb(msg):
    """A-LOAM's scan-to-map solution: Eqs. 14-16 (remap), then Algorithm 1 line 10"""
    t = msg.header.stamp.to_sec()
    Ra, pa = odom_to_pose(msg)
    with lock:
        v = vins_at(t)
        Hfull = latest_H[0]
        if not core.initialised():
            O = odoms.get(t, (Ra, pa))
            core.init((Ra, pa), O, v, pubs.get(t, O), t=t)
            R, p, info = core.Rf, core.pf, dict(case=0, kind="INIT", status="", vo_fail=v is None, degen=False,
                                               lam_bar=np.full(3, np.nan), w=np.nan, dtl=np.nan, dtv=np.nan, gyro=False, gyro_deg=np.nan)
            race = False
        else:
            dec = decs.pop(t, None)
            if dec is None:                                  # decision pruned or never made: skip this scan
                stats["no_dec"] += 1
                return
            P = pubs.get(t)
            if P is None:
                stats["no_dec"] += 1
                return
            Hfin = dec["H"] if HESS_FRAME == "body" else Hfull
            race = dec["race"]
            R, p, info = core.finish((Ra, pa), Hfin, dec, P)
        cost, mres = latest_H[1], latest_H[2]
    vq = fc.R_to_quat(v[0]) if v is not None else [np.nan] * 4
    vp = v[1] if v is not None else [np.nan] * 3
    Hrow = list(Hfull.ravel()) if Hfull is not None else [np.nan] * 36
    lb = info["lam_bar"]
    w.writerow([t, "SW_" + info["kind"], *p, *fc.R_to_quat(R), *pa, *fc.R_to_quat(Ra), *vp, *vq,
                info["case"], np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, info["dtl"], info["dtv"],
                HESS_TOPIC, cost, mres] + Hrow + [0.0, 0.0, 0] +
               [info["case"], info["status"], int(info["vo_fail"]), lb[0], lb[1], lb[2], info["w"], int(info["degen"]), int(race), int(info["gyro"]), info["gyro_deg"]])
    stats["rows"] += 1
    stats["race"] += int(race)
    if stats["rows"] % 50 == 0:
        log.flush()
        rospy.loginfo("[%d] %s case=%s status=%s lam=(%.2f %.2f %.2f) race=%d p=(%.2f %.2f %.2f)", stats["rows"], info["kind"],
                      info["case"], info["status"], lb[0], lb[1], lb[2], stats["race"], *p)


def main():
    rospy.init_node("switch_slam_node", anonymous=True)
    pub[0] = rospy.Publisher("/switch_fused_pose", Odometry, queue_size=50)
    rospy.Subscriber("/vins_estimator/odometry", Odometry, vins_cb, queue_size=200)
    rospy.Subscriber(HESS_TOPIC, Float64MultiArray, hess_cb, queue_size=50)
    rospy.Subscriber("/laser_odom_to_init", Odometry, laser_odom_cb, queue_size=50)
    rospy.Subscriber("/aft_mapped_to_init", Odometry, aft_cb, queue_size=50)
    if GYRO:
        from sensor_msgs.msg import Imu
        for tp in IMU_TOPICS:
            rospy.Subscriber(tp, Imu, imu_cb, queue_size=1000)
    print("FUSION_MODE=switch_slam HESS_TOPIC=%s HESS_FRAME=%s N_BUF=%d LT_MODE=%s LT=%s EQ15_W=%g GYRO=%d RUN_TAG=%s"
          % (HESS_TOPIC, HESS_FRAME, N_BUF, LT_MODE, np.round(lt, 3).tolist(), EQ15_W, int(GYRO), RUN_TAG))
    print("switch_slam_node listening...")
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    finally:
        log.close()
        print("Saved", log_path, "rows", stats["rows"], "race (earlier scan unfinished at publish)", stats["race"], "no decision", stats["no_dec"])
