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
  DETECT       sw (default: Switch-SLAM's own rule, the replica) | ours: Switch-SLAM's rule plus our R, T and additional-T channels
               | ours_only: our channels only, with our own thresholds (kappa 15.7 for R, c_T 0.03 information weight for T), no
               Switch-SLAM thresholds at all (switch_slam_detect.py; the switching structure is unchanged)
  DET_CT, DET_KR, DET_TT_RULE   ours_only: c_T (0.03), kappa threshold of R (15.7), tensor rule (min)
  DET_CH       with DETECT=ours: R,T,TT (default; R rotation Schur, T translation Schur, TT additional T = T combined with the
               orientation tensor of /laser_cloud_surf_last).  Subsets for ablations, e.g. R,T
  VINS_JUMP_POS, VINS_JUMP_ROT_DEG   VINS-Mono failure limits per scan (default 5 m, 50 deg = VINS-Mono's own, as in the paper)
  VIO_CHECK    1: VINS-Mono also counts as failed while F24's scale-consistency gate is closed (fusion_core.VioConsistency, slow
               ref VIO_CHECK_REF over the segment, fast ref VIO_CHECK_FAST_REF over VIO_CHECK_FAST s, VIO_CHECK_START trusted at start)
  EQ15_MODE    mean (default, printed Eq. 15) | split (F34: flagged directions from VINS-Mono, the others from the LiDAR; our detector only)
  SAH          1 (F34): structure-anchored heading, F24's module and settings (KF_DIST, KF_ROT, SAH_RMIN/RMAX/VOXEL/MAXPTS/MAX_STEP)
  ROT_SRC      lidar (default) | vins (F33: rotation of the output = VINS-Mono's on every scan where it is trusted, translation unchanged)
  T_KNN, T_SUB the orientation-tensor recipe (12, 400), same as fusion_node_v2
  RUN_TAG      log name suffix
  EXTRINSIC_YAML  same format as fusion_node_v2 (default SubT-MRS Multi Floor laser_to_imu)
"""
import csv
import os
import queue
import threading
from collections import OrderedDict, deque

import numpy as np
import rospy
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray

import fusion_core as fc
import switch_slam_core as sw
import switch_slam_detect as sd
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
DETECT = E("DETECT", "sw")
DET_CH = sd.parse_channels(E("DET_CH", "R,T,TT"))
assert DETECT in ("sw", "ours", "ours_only"), DETECT
DET_CT, DET_KR, DET_TT_RULE = float(E("DET_CT", "0.03")), float(E("DET_KR", "15.7")), E("DET_TT_RULE", "min")
T_KNN, T_SUB = int(E("T_KNN", "12")), int(E("T_SUB", "400"))
VINS_JUMP_POS, VINS_JUMP_ROT_DEG = float(E("VINS_JUMP_POS", "5.0")), float(E("VINS_JUMP_ROT_DEG", "50.0"))
VIO_CHECK = E("VIO_CHECK", "0") == "1"
VIO_CHECK_REF, VIO_CHECK_NMIN = float(E("VIO_CHECK_REF", "0.157")), int(E("VIO_CHECK_NMIN", "200"))
VIO_CHECK_FAST, VIO_CHECK_FAST_REF = float(E("VIO_CHECK_FAST", "5")), float(E("VIO_CHECK_FAST_REF", "0.277"))
VIO_CHECK_FAST_NMIN = int(E("VIO_CHECK_FAST_NMIN", "25"))
VIO_CHECK_START = E("VIO_CHECK_START", "1") == "1"
EQ15_MODE = E("EQ15_MODE", "mean")        # F34: split = flagged directions from VINS-Mono, the others from the LiDAR
assert EQ15_MODE in ("mean", "split"), EQ15_MODE
SAH = E("SAH", "0") == "1"                # F34: structure-anchored heading, the same module and settings as F24 (structure_heading.py)
KF_DIST, KF_ROT = float(E("KF_DIST", "1.0")), float(E("KF_ROT", "0.2"))
SAH_RMIN, SAH_RMAX = float(E("SAH_RMIN", "1.0")), float(E("SAH_RMAX", "60.0"))
SAH_VOXEL, SAH_MAXPTS = float(E("SAH_VOXEL", "0.25")), int(E("SAH_MAXPTS", "6000"))
SAH_MAX_STEP = np.radians(float(E("SAH_MAX_STEP", "0.25")))
SAH_SYNC = E("SAH_SYNC", "0") == "1"
ROT_SRC = E("ROT_SRC", "lidar")           # F33: vins = rotation of the output from VINS-Mono whenever trusted
assert ROT_SRC in ("lidar", "vins"), ROT_SRC
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
core = sw.SwitchSlamCore(R_IL, t_IL, n_buf=N_BUF, lt=lt, eq15_w=EQ15_W, hess_frame=HESS_FRAME,
                         vins_jump_pos=VINS_JUMP_POS, vins_jump_rot=np.radians(VINS_JUMP_ROT_DEG), rot_src=ROT_SRC, eq15_mode=EQ15_MODE,
                         detector=(sd.OurDetector(DET_CH, lt) if DETECT == "ours" else
                                   sd.OwnDetector(DET_CH, DET_CT, 1.0, DET_KR, DET_TT_RULE) if DETECT == "ours_only" else None))
vio_check = None
if VIO_CHECK:
    _c = [fc.VioConsistency(ref=VIO_CHECK_REF, stat="scale", rule="gate", avg=None, n_min=VIO_CHECK_NMIN, start_trusted=VIO_CHECK_START)]
    if VIO_CHECK_FAST > 0:
        _c.append(fc.VioConsistency(ref=VIO_CHECK_FAST_REF, stat="scale", rule="gate", avg=VIO_CHECK_FAST, n_min=VIO_CHECK_FAST_NMIN,
                                    start_trusted=VIO_CHECK_START))
    vio_check = fc.VioChecks(_c)
USE_TT = DETECT in ("ours", "ours_only") and "TT" in DET_CH
E3 = np.array([0.0, 0.0, 1.0])
if SAH:
    import structure_heading as shd
    sah = shd.make_sah()
sah_state = dict(last_kf=None, pending={}, clouds=deque(maxlen=30), todo=0.0, applied=0.0, decided=0.0, n_kf=0, Rprev=None, dropped=0)
sah_q = queue.Queue(maxsize=2)
t_buf = deque(maxlen=40)                   # (scan stamp, T 3x3) from /laser_cloud_surf_last, additional-T channel
t_rng = np.random.default_rng(0)
t_stats = dict(have=0, miss=0)
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
           ["sw_case", "sw_status", "sw_vo_fail", "sw_lam1", "sw_lam2", "sw_lam3", "sw_w", "sw_degen", "sw_race", "sw_gyro", "sw_gyro_deg"] +
           (["det_sw", "det_R", "det_T", "det_TT", "det_T_missing", "det_nrem"] if DETECT != "sw" else []) +
           (["vio_gamma"] if VIO_CHECK else []) + (["sw_rotv"] if ROT_SRC == "vins" else []))


def odom_to_pose(msg):
    p, q = msg.pose.pose.position, msg.pose.pose.orientation
    return fc.quat_to_R([q.x, q.y, q.z, q.w]), np.array([p.x, p.y, p.z])


def cloud_xyz(msg):
    off = {f.name: f.offset for f in msg.fields}
    dt = np.dtype({"names": ["x", "y", "z"], "formats": ["<f4"] * 3,
                   "offsets": [off["x"], off["y"], off["z"]], "itemsize": msg.point_step})
    a = np.frombuffer(msg.data, dtype=dt, count=msg.width * msg.height)
    P = np.stack([a["x"], a["y"], a["z"]], 1).astype(np.float64)
    return P[np.isfinite(P).all(1)]


def surf_cb(msg):
    """additional T: orientation tensor of this scan's planar points, stored under the scan's time stamp"""
    try:
        res = fc.orientation_tensor(cloud_xyz(msg), T_KNN, T_SUB, t_rng)
    except Exception as ex:                                     # never let T break the node
        rospy.logwarn("T failed: %s", ex)
        return
    if res is None:
        return
    with lock:
        t_buf.append((msg.header.stamp.to_sec(), res[0]))


T_LAG_MAX = float(E("T_LAG_MAX", "0.25"))      # s: the tensor of the newest scan not later than t is used when the exact one has not arrived yet


def t_at(t):
    """T of the scan with time stamp t if it is already there, else the tensor of the newest earlier scan within T_LAG_MAX seconds
    (A-LOAM publishes /laser_cloud_surf_last just after the odometry message of the same scan, so at the odometry callback the exact
    tensor is never there yet: the first F30 run found 0 of 3455).  The scene's orientation tensor changes little in one scan.
    Returns (T, lag in s) or None."""
    for st, T in reversed(t_buf):
        if abs(st - t) < 1e-3:
            return T, 0.0
        if st < t - 1e-3:
            return (T, t - st) if t - st <= T_LAG_MAX else None
    return None


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


def voxel_down(P, v):
    k = np.floor(P / v).astype(np.int64) + (1 << 20)
    key = (k[:, 0] << 42) | (k[:, 1] << 21) | k[:, 2]
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    out = np.zeros((len(cnt), 3))
    np.add.at(out, inv.ravel(), P)
    return out / cnt[:, None]


def sah_process(job):
    """as fusion_node_v2.sah_process: the registered cloud of a keyframe scan in the LiDAR frame -> planar normals -> heading measurement
    about the VINS-Mono vertical; the correction is queued and applied gradually (SAH_MAX_STEP per scan)"""
    t, Ra, pa, Rf, u, applied_snap, msg = job
    try:
        Pb = (cloud_xyz(msg) - pa) @ Ra
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


def sah_on_step(t, Ra, pa, v, fused, R):
    """called under the lock after core.finish (F24's sah_on_step with 'mode == FUSED' = VINS-Mono trusted on this scan): turn bookkeeping,
    gradual application of the decided corrections to the final rotation chain, keyframe selection.  Returns (R, corr_now, job)."""
    corr_now, job = 0.0, None
    u = None
    if v is not None:
        u = core.Rf @ (R_IL.T @ (v[0].T @ E3))
        u = u / np.linalg.norm(u)
    if v is not None:
        if sah_state["Rprev"] is not None:
            sah.add_turn(float(fc.so3_log(core.Rf @ sah_state["Rprev"].T) @ u))
        if fused and sah_state["todo"] != 0.0:
            corr_now = float(np.clip(sah_state["todo"], -SAH_MAX_STEP, SAH_MAX_STEP))
            core.Rf = fc.so3_exp(-corr_now * u) @ core.Rf
            sah_state["todo"] -= corr_now
            sah_state["applied"] += corr_now
            R = core.Rf
    if not fused and sah_state["todo"] != 0.0:
        sah_state["decided"] -= sah_state["todo"]               # VINS-Mono distrusted: drop stale corrections
        sah_state["todo"] = 0.0
    sah_state["Rprev"] = core.Rf.copy()
    lk = sah_state["last_kf"]
    is_kf = lk is None or np.linalg.norm(pa - lk[1]) >= KF_DIST or \
        np.arccos(np.clip((np.trace(lk[0].T @ Ra) - 1) / 2, -1, 1)) >= KF_ROT
    if is_kf:
        sah_state["last_kf"] = (Ra, pa)
        if fused and u is not None:
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
            T_hit = t_at(t) if USE_TT else None
            T_scan = T_hit[0] if T_hit is not None else None
            if USE_TT:
                t_stats["have" if T_scan is not None else "miss"] += 1
                if T_hit is not None and T_hit[1] > 0.0:
                    t_stats["lag"] = t_stats.get("lag", 0) + 1
            trusted = vio_check is None or vio_check.gamma() > 0.5
            dec = core.decide(O, vins_at(t), H, gyro_dR=dR_L, t=t, T=T_scan, vo_trusted=trusted)
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
    job, corr_now = None, 0.0
    with lock:
        v = vins_at(t)
        if vio_check is not None:                            # F24's scale-consistency gate, fed with A-LOAM's pose and the VINS pose
            if v is not None:
                vio_check.update(t, (Ra, pa), (np.asarray(v[0], float), np.asarray(v[1], float)), R_IL, t_IL)
            else:
                vio_check.reset()
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
            if SAH:
                try:
                    R, corr_now, job = sah_on_step(t, Ra, pa, v, not info["vo_fail"], R)
                except Exception as ex:                         # never let SAH break the estimator
                    rospy.logwarn("SAH step failed at %.2f: %s", t, ex)
        cost, mres = latest_H[1], latest_H[2]
    if job is not None:
        sah_submit(job)
    vq = fc.R_to_quat(v[0]) if v is not None else [np.nan] * 4
    vp = v[1] if v is not None else [np.nan] * 3
    Hrow = list(Hfull.ravel()) if Hfull is not None else [np.nan] * 36
    lb = info["lam_bar"]
    w.writerow([t, "SW_" + info["kind"], *p, *fc.R_to_quat(R), *pa, *fc.R_to_quat(Ra), *vp, *vq,
                info["case"], np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, info["dtl"], info["dtv"],
                HESS_TOPIC, cost, mres] + Hrow + [np.degrees(corr_now), np.degrees(sah_state["applied"]), (sah.stats["acc"] if SAH else 0)] +
               [info["case"], info["status"], int(info["vo_fail"]), lb[0], lb[1], lb[2], info["w"], int(info["degen"]), int(race), int(info["gyro"]), info["gyro_deg"]] +
               ([int(ch["SW"]), int(ch["R"]), int(ch["T"]), int(ch["TT"]), int(ch["T_missing"]), info["nrem"]] if DETECT != "sw" and (ch := info.get("chan")) is not None else
                ([0, 0, 0, 0, 0, -1] if DETECT != "sw" else [])) +
               ([vio_check.gamma()] if vio_check is not None else []) + ([int(info.get("rot_vins", False))] if ROT_SRC == "vins" else []))
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
    if USE_TT:
        from sensor_msgs.msg import PointCloud2
        rospy.Subscriber("/laser_cloud_surf_last", PointCloud2, surf_cb, queue_size=20, buff_size=2 ** 24)
    if SAH:
        from sensor_msgs.msg import PointCloud2
        rospy.Subscriber("/velodyne_cloud_registered", PointCloud2, sah_cloud_cb, queue_size=20, buff_size=2 ** 24)
        if not SAH_SYNC:
            threading.Thread(target=sah_worker, daemon=True).start()
        print("SAH=1 KF_DIST=%g KF_ROT=%g SAH_RMIN=%g SAH_RMAX=%g SAH_VOXEL=%g SAH_MAXPTS=%d SAH_MAX_STEP=%.2f deg"
              % (KF_DIST, KF_ROT, SAH_RMIN, SAH_RMAX, SAH_VOXEL, SAH_MAXPTS, np.degrees(SAH_MAX_STEP)))
    if GYRO:
        from sensor_msgs.msg import Imu
        for tp in IMU_TOPICS:
            rospy.Subscriber(tp, Imu, imu_cb, queue_size=1000)
    print("FUSION_MODE=switch_slam HESS_TOPIC=%s HESS_FRAME=%s N_BUF=%d LT_MODE=%s LT=%s EQ15_W=%g GYRO=%d RUN_TAG=%s"
          % (HESS_TOPIC, HESS_FRAME, N_BUF, LT_MODE, np.round(lt, 3).tolist(), EQ15_W, int(GYRO), RUN_TAG))
    print("DETECT=%s DET_CH=%s T_KNN=%d T_SUB=%d" % (DETECT, ",".join(DET_CH), T_KNN, T_SUB))
    print("ROT_SRC=%s EQ15_MODE=%s SAH=%d" % (ROT_SRC, EQ15_MODE, int(SAH)))
    print("VINS_JUMP_POS=%g VINS_JUMP_ROT_DEG=%g VIO_CHECK=%d VIO_CHECK_REF=%g VIO_CHECK_FAST=%g VIO_CHECK_FAST_REF=%g VIO_CHECK_START=%d"
          % (VINS_JUMP_POS, VINS_JUMP_ROT_DEG, int(VIO_CHECK), VIO_CHECK_REF, VIO_CHECK_FAST, VIO_CHECK_FAST_REF, int(VIO_CHECK_START)))
    print("switch_slam_node listening...")
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    finally:
        log.close()
        if USE_TT:
            print("additional T: tensor found for %d scans (%d of them the previous scan's, up to %.2f s old), missing for %d (plain Schur T used there)" % (t_stats["have"], t_stats.get("lag", 0), T_LAG_MAX, t_stats["miss"]))
        if SAH:
            print("SAH keyframes %d dropped %d applied %.2f deg stats %s" % (sah_state["n_kf"], sah_state["dropped"], np.degrees(sah_state["applied"]), sah.stats))
        print("Saved", log_path, "rows", stats["rows"], "race (earlier scan unfinished at publish)", stats["race"], "no decision", stats["no_dec"])
