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
  SAH           1: structure-anchored heading (structure_heading.py): at every keyframe (KF_DIST m / KF_ROT rad of
                scan-to-map motion, as keyframe_recorder) the registered scan's vertical-wall directions correct the
                fused heading; corrections are applied gradually (SAH_MAX_STEP deg per scan). Off by default.
  SAH_RMIN, SAH_RMAX, SAH_VOXEL, SAH_MAXPTS   scan preprocessing (defaults 1.0 m, 60 m, 0.25 m, 6000 points)
  SAH_SYNC      1: process keyframes inside the callback (tests); default 0: worker thread
  VIO_CHECK     1: VINS-LiDAR scale-consistency gate (fusion_core.VioConsistency, stat 'scale', segment mean, rule 'gate'):
                the VINS prior is used (gamma = 1) only while the RMS log ratio of VINS to LiDAR displacement over 10 s
                windows of the current VINS segment is <= VIO_CHECK_REF (0.156 = largest value on Multi Floor with
                >= VIO_CHECK_NMIN = 200 windows); otherwise gamma = 0 and the LiDAR carries the step. Off by default.
  VIO_SCALE_T   > 0: VINS translation increments are rescaled by the LiDAR/VINS path-length ratio over the last
                VIO_SCALE_T s of the VINS segment before fusion (0 = off, default).
Extrinsic: SubT-MRS Multi Floor 'laser_to_imu' (override with EXTRINSIC_YAML=path to the same format).
"""
import os
import csv
import queue
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
WEIGHT_MODE = E("WEIGHT_MODE", "schur")   # ablation: schur diag iso const proj switch_ss switch_kR lidar vins
W_ALPHA = float(E("W_ALPHA", "0.7"))
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
SAH = E("SAH", "0") == "1"
KF_DIST, KF_ROT = float(E("KF_DIST", "1.0")), float(E("KF_ROT", "0.2"))
SAH_RMIN, SAH_RMAX = float(E("SAH_RMIN", "1.0")), float(E("SAH_RMAX", "60.0"))
SAH_VOXEL, SAH_MAXPTS = float(E("SAH_VOXEL", "0.25")), int(E("SAH_MAXPTS", "6000"))
SAH_MAX_STEP = np.radians(float(E("SAH_MAX_STEP", "0.25")))
SAH_SYNC = E("SAH_SYNC", "0") == "1"
VIO_CHECK = E("VIO_CHECK", "0") == "1"
VIO_CHECK_REF = float(E("VIO_CHECK_REF", "0.156"))
VIO_CHECK_NMIN = int(E("VIO_CHECK_NMIN", "200"))
VIO_SCALE_T = float(E("VIO_SCALE_T", "0"))
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
vio_check = fc.VioConsistency(ref=VIO_CHECK_REF, stat="scale", rule="gate", avg=None, n_min=VIO_CHECK_NMIN) if VIO_CHECK else None
core = fc.FusionCore(R_IL, t_IL, c_t=C_T, c_R=C_R, gate=gate, t_warm=T_WARM, hess_frame=HESS_FRAME,
                     jump_max=JUMP_MAX, w_mode=WEIGHT_MODE, alpha=W_ALPHA, vio_adapt=vio_check, vio_scale_T=VIO_SCALE_T)
if MODE == "lidar":
    core.t_warm = 1e12                     # every step is WARMUP = LiDAR only

vins_buf = deque(maxlen=400)               # (t, R, p) IMU poses in the VINS world
E3 = np.array([0.0, 0.0, 1.0])
if SAH:
    import structure_heading as shd
    sah = shd.make_sah()
sah_state = dict(last_kf=None, pending={}, clouds=deque(maxlen=30), todo=0.0, applied=0.0, decided=0.0, n_kf=0, Rprev=None,
                 busy=False, dropped=0)
sah_q = queue.Queue(maxsize=2)
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
            "hess_src", "cost", "m_res"] + HCOLS + ["sah_corr_deg", "sah_total_deg", "sah_acc", "vio_gamma", "s_vio"])
cnt = [0]


def cloud_xyz(msg):
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


def sah_process(job):
    """job = (t, Ra, pa, Rf, u, applied_at_snapshot, cloud msg).
    The heading measurement must refer to the heading the estimator WILL have once every correction decided so far
    is applied (corrections are applied gradually), so the snapshot rotation is moved by the outstanding amount."""
    t, Ra, pa, Rf, u, applied_snap, msg = job
    try:
        Pb = (cloud_xyz(msg) - pa) @ Ra                         # registered (map) cloud -> LiDAR body frame
        r = np.linalg.norm(Pb, axis=1)
        Pb = Pb[(r > SAH_RMIN) & (r < SAH_RMAX)]
        nb = plan = None
        if len(Pb) >= 50:
            Pb = voxel_down(Pb, SAH_VOXEL)
            if len(Pb) > SAH_MAXPTS:
                Pb = Pb[np.random.default_rng(int(t * 1e3) % (2 ** 31)).choice(len(Pb), SAH_MAXPTS, replace=False)]
            nb, plan = shd.planar_normals(Pb)
    except Exception as ex:                                     # never let SAH break the estimator
        rospy.logwarn("SAH preprocessing failed at %.2f: %s", t, ex)
        return
    with lock:
        sah_state["n_kf"] += 1
        if nb is None:
            return
        try:
            outstanding = sah_state["decided"] - applied_snap
            Rf_eff = fc.so3_exp(-outstanding * u) @ Rf
            L = shd.level_rotation(u)
            h, npts = shd.direction_hist(nb @ (L @ Rf_eff).T, plan)
            c = float(sah.update(t, h, npts))
        except Exception as ex:
            rospy.logwarn("SAH update failed at %.2f: %s", t, ex)
            c = 0.0
        if np.isfinite(c) and c != 0.0:
            sah_state["todo"] += c
            sah_state["decided"] += c


def sah_worker():
    while not rospy.is_shutdown():
        try:
            job = sah_q.get(timeout=0.5)
        except queue.Empty:
            continue
        sah_process(job)


def sah_submit(job):
    if SAH_SYNC:
        sah_process(job)
        return
    try:
        sah_q.put_nowait(job)
    except queue.Full:
        sah_state["dropped"] += 1                               # worker busy: skip this keyframe


def sah_cloud_cb(msg):
    st = msg.header.stamp.to_sec()
    job = None
    with lock:
        if st in sah_state["pending"]:
            job = (st,) + sah_state["pending"].pop(st) + (msg,)
        else:
            sah_state["clouds"].append((st, msg))
    if job is not None:
        sah_submit(job)


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


def sah_on_step(t, Ra, pa, v, info, R):
    """called under the lock after core.step: turn bookkeeping, gradual application of decided corrections,
    keyframe selection (same rule as keyframe_recorder, on every mapped scan). Returns (R, corr_now, job)."""
    corr_now, job = 0.0, None
    u = None
    if v is not None:
        u = core.Rf @ (R_IL.T @ (v[0].T @ E3))
        u = u / np.linalg.norm(u)
        if sah_state["Rprev"] is not None:
            sah.add_turn(float(fc.so3_log(core.Rf @ sah_state["Rprev"].T) @ u))
        if info["mode"] == "FUSED" and sah_state["todo"] != 0.0:
            corr_now = float(np.clip(sah_state["todo"], -SAH_MAX_STEP, SAH_MAX_STEP))
            core.Rf = fc.so3_exp(-corr_now * u) @ core.Rf
            sah_state["todo"] -= corr_now
            sah_state["applied"] += corr_now
            R = core.Rf
    if info["mode"] != "FUSED" and sah_state["todo"] != 0.0:
        sah_state["decided"] -= sah_state["todo"]               # VIO (re)starting: drop stale corrections
        sah_state["todo"] = 0.0
    sah_state["Rprev"] = core.Rf.copy()
    lk = sah_state["last_kf"]
    is_kf = lk is None or np.linalg.norm(pa - lk[1]) >= KF_DIST or \
        np.arccos(np.clip((np.trace(lk[0].T @ Ra) - 1) / 2, -1, 1)) >= KF_ROT
    if is_kf:
        sah_state["last_kf"] = (Ra, pa)
        if info["mode"] == "FUSED" and u is not None:
            snap = (Ra.copy(), pa.copy(), core.Rf.copy(), u.copy(), sah_state["applied"])
            for st_, m_ in sah_state["clouds"]:
                if st_ == t:
                    job = (t,) + snap + (m_,)
                    break
            else:
                sah_state["pending"][t] = snap
        for s_ in [s_ for s_ in sah_state["pending"] if s_ < t - 2.0]:
            sah_state["pending"].pop(s_)
    return R, corr_now, job


def aft_cb(msg):
    t = msg.header.stamp.to_sec()
    Ra, pa = odom_to_pose(msg)
    job = None
    corr_now = 0.0
    with lock:
        v = vins_at(t)
        H = latest_H[0]
        R, p, info = core.step(t, (Ra, pa), v, H)
        cost, mres = latest_H[1], latest_H[2]
        if SAH:
            try:
                R, corr_now, job = sah_on_step(t, Ra, pa, v, info, R)
            except Exception as ex:                             # never let SAH break the estimator
                rospy.logwarn("SAH step failed at %.2f: %s", t, ex)
    if job is not None:
        sah_submit(job)
    vq = fc.R_to_quat(v[0]) if v is not None else [np.nan] * 4
    vp = v[1] if v is not None else [np.nan] * 3
    Hrow = list(H.ravel()) if H is not None else [np.nan] * 36
    w.writerow([t, info["mode"], *p, *fc.R_to_quat(R), *pa, *fc.R_to_quat(Ra), *vp, *vq,
                info["gate"], info["kappa_R"], info["kappa_t"], info["kth"], *info["wt"], *info["wR"],
                info["dta"], info["dtv"], HESS_TOPIC, cost, mres] + Hrow +
               [np.degrees(corr_now), np.degrees(sah_state["applied"]), (sah.stats["acc"] if SAH else 0),
                info.get("gamma", 1.0), info.get("s_vio", 1.0)])
    cnt[0] += 1
    if cnt[0] % 50 == 0:
        log.flush()
        rospy.loginfo("[%d] %s gate=%s kR=%.1f kth=%.1f p=(%.2f %.2f %.2f)", cnt[0], info["mode"], info["gate"],
                      info["kappa_R"] if np.isfinite(info["kappa_R"]) else -1, info["kth"] if np.isfinite(info["kth"]) else -1, *p)
        if SAH and cnt[0] % 500 == 0:
            rospy.loginfo("SAH keyframes %d dropped %d applied %.2f deg stats %s", sah_state["n_kf"], sah_state["dropped"],
                          np.degrees(sah_state["applied"]), sah.stats)


def main():
    rospy.init_node("fusion_node_v2", anonymous=True)
    pub[0] = rospy.Publisher("/switch_fused_pose", Odometry, queue_size=50)
    rospy.Subscriber("/vins_estimator/odometry", Odometry, vins_cb, queue_size=200)
    rospy.Subscriber(HESS_TOPIC, Float64MultiArray, hess_cb, queue_size=50)
    rospy.Subscriber("/laser_odom_to_init", Odometry, laser_odom_cb, queue_size=50)
    rospy.Subscriber("/aft_mapped_to_init", Odometry, aft_cb, queue_size=50)
    if SAH:
        from sensor_msgs.msg import PointCloud2
        rospy.Subscriber("/velodyne_cloud_registered", PointCloud2, sah_cloud_cb, queue_size=20, buff_size=2 ** 24)
        if not SAH_SYNC:
            threading.Thread(target=sah_worker, daemon=True).start()
        print("SAH=1 KF_DIST=%g KF_ROT=%g SAH_RMIN=%g SAH_RMAX=%g SAH_VOXEL=%g SAH_MAXPTS=%d SAH_MAX_STEP=%.2f deg"
              % (KF_DIST, KF_ROT, SAH_RMIN, SAH_RMAX, SAH_VOXEL, SAH_MAXPTS, np.degrees(SAH_MAX_STEP)))
    print("VIO_CHECK=%d VIO_CHECK_REF=%g VIO_CHECK_NMIN=%d VIO_SCALE_T=%g" % (VIO_CHECK, VIO_CHECK_REF, VIO_CHECK_NMIN, VIO_SCALE_T))
    print("FUSION_MODE=%s C_T=%g C_R=%g KAPPA_MODE=%s KAPPA_TH=%g T_WARM=%g HESS_TOPIC=%s PREDICT_WITH_VINS=%d RUN_TAG=%s WEIGHT_MODE=%s W_ALPHA=%g"
          % (MODE, C_T, C_R, KAPPA_MODE, KAPPA_TH, T_WARM, HESS_TOPIC, PREDICT_WITH_VINS, RUN_TAG, WEIGHT_MODE, W_ALPHA))
    print("fusion_node_v2 listening...")
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    finally:
        log.close()
        print("Saved", log_path)
        if SAH:
            print("SAH keyframes %d dropped %d applied %.2f deg stats %s" % (sah_state["n_kf"], sah_state["dropped"],
                  np.degrees(sah_state["applied"]), sah.stats))
