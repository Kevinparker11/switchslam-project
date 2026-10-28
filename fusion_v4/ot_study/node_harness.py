"""Drive the real fusion_node_v2 callbacks offline (rospy and messages stubbed) with a logged run and its keyframe
scans, to check the live SAH integration against the offline replay.
usage: SAH=1 python3 node_harness.py LOG.csv KEYFRAMES.npz OUTDIR [cloud_first|aft_first]"""
import os, sys, types, time
sys.path.insert(0, os.environ.get("FUSION_DIR", "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/clean4/fusion_v4"))
if os.environ.get("HIDE_SCIPY"):
    sys.modules["scipy"] = None; sys.modules["scipy.spatial"] = None
import numpy as np
import pandas as pd

# ---------------- stubs ----------------
class _Stamp:
    def __init__(self, t): self.t = t
    def to_sec(self): return self.t
class _Hdr:
    def __init__(self, t): self.stamp = _Stamp(t); self.frame_id = ""
class _P: pass
class Odometry:
    def __init__(self, t=0.0, R=None, p=None):
        self.header = _Hdr(t); self.child_frame_id = ""
        self.pose = _P(); self.pose.pose = _P(); self.pose.pose.position = _P(); self.pose.pose.orientation = _P()
        if p is not None:
            import fusion_core as fc
            q = fc.R_to_quat(R)
            pp, oo = self.pose.pose.position, self.pose.pose.orientation
            pp.x, pp.y, pp.z = p
            oo.x, oo.y, oo.z, oo.w = q
class Float64MultiArray:
    def __init__(self, data=()): self.data = list(data)
class _Field:
    def __init__(self, n, o): self.name, self.offset = n, o
class PointCloud2:
    def __init__(self, t, P):
        self.header = _Hdr(t)
        a = np.zeros(len(P), dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("intensity", "<f4")])
        a["x"], a["y"], a["z"] = P[:, 0], P[:, 1], P[:, 2]
        self.fields = [_Field("x", 0), _Field("y", 4), _Field("z", 8), _Field("intensity", 12)]
        self.point_step, self.width, self.height, self.data = 16, len(P), 1, a.tobytes()

rospy = types.ModuleType("rospy")
rospy.loginfo = lambda *a, **k: None
rospy.logwarn = lambda *a, **k: print("WARN", a[0] % a[1:] if len(a) > 1 else a[0])
rospy.is_shutdown = lambda: False
class _Pub:
    def __init__(self, *a, **k): pass
    def publish(self, m): pass
rospy.Publisher = _Pub
rospy.Subscriber = lambda *a, **k: None
rospy.init_node = lambda *a, **k: None
rospy.spin = lambda: None
sys.modules["rospy"] = rospy
for mod, names in (("nav_msgs.msg", {"Odometry": Odometry}), ("std_msgs.msg", {"Float64MultiArray": Float64MultiArray}),
                   ("sensor_msgs.msg", {"PointCloud2": PointCloud2})):
    pkg = mod.split(".")[0]
    sys.modules.setdefault(pkg, types.ModuleType(pkg))
    m = types.ModuleType(mod); [setattr(m, k, v) for k, v in names.items()]; sys.modules[mod] = m

# ---------------- drive ----------------
logp, kfp, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
order = sys.argv[4] if len(sys.argv) > 4 else "aft_first"
os.makedirs(outdir, exist_ok=True); os.chdir(outdir)
os.environ.setdefault("RUN_TAG", "harness")
import fusion_core as fc
import fusion_node_v2 as node
import threading
if node.SAH and not node.SAH_SYNC:
    threading.Thread(target=node.sah_worker, daemon=True).start()

L = pd.read_csv(logp); L = L[pd.to_numeric(L["time"], errors="coerce").notna()].reset_index(drop=True)
z = np.load(kfp); kt = z["t"]; n = z["n"]; off = np.r_[0, np.cumsum(n)]; pts = z["pts"].astype(float) * float(z["scale"])
kfi = {round(float(t), 3): i for i, t in enumerate(kt)}
Hc = ["Hl_%d%d" % (i, j) for i in range(6) for j in range(6)]
# optional injected solver fault (stage 3 of the OT study): FAULT=1 -> three 20 s windows at 25/50/75 % of the log
FAULT = os.environ.get("FAULT", "0") == "1"
FV, FW = float(os.environ.get("FAULT_V", "0.2")), float(os.environ.get("FAULT_W", "20"))
_tt = L["time"].astype(float).values
F_START = [_tt[0] + f * (_tt[-1] - _tt[0]) for f in (0.25, 0.5, 0.75)] if FAULT else []
f_dir = {}; f_off = np.zeros(3)
def fault_apply(t, Ra, pa, H, dt_prev):
    """returns (pa', H') for the faulted solver"""
    global f_off
    for s0 in F_START:
        if s0 <= t < s0 + FW:
            if s0 not in f_dir:
                if np.isfinite(H).all():
                    S_tt = fc.schur_blocks(H.reshape(6, 6), "body")[1]
                    v = np.linalg.eigh(S_tt)[1][:, 0]
                else:
                    v = np.array([1.0, 0, 0])
                f_dir[s0] = Ra @ v
            f_off = f_off + FV * dt_prev * f_dir[s0]
            if np.isfinite(H).all():
                Hm = H.reshape(6, 6).copy(); Hm[3:, 3:] = np.trace(Hm[3:, 3:]) / 3.0 * np.eye(3)
                H = Hm.ravel()
            break
    return pa + f_off, H
t_prevrow = None
t0 = time.time()
for k in range(len(L)):
    r = L.iloc[k]; t = float(r["time"])
    if np.isfinite(r["v_px"]):
        node.vins_cb(Odometry(t, fc.quat_to_R(r[["v_qx", "v_qy", "v_qz", "v_qw"]].values.astype(float)), r[["v_px", "v_py", "v_pz"]].values.astype(float)))
    H = r[Hc].values.astype(float)
    Ra = fc.quat_to_R(r[["aft_qx", "aft_qy", "aft_qz", "aft_qw"]].values.astype(float)); pa = r[["aft_x", "aft_y", "aft_z"]].values.astype(float)
    if FAULT:
        pa, H = fault_apply(t, Ra, pa, H, 0.0 if t_prevrow is None else t - t_prevrow)
    t_prevrow = t
    if np.isfinite(H).all():
        node.hess_cb(Float64MultiArray(list(H) + [r["cost"] if "cost" in r else np.nan, np.nan]))
    i = kfi.get(round(t, 3))
    cloud = PointCloud2(t, pts[off[i]:off[i + 1]] @ Ra.T + pa) if i is not None else None
    if cloud is not None and order == "cloud_first":
        node.sah_cloud_cb(cloud) if getattr(node, "KF_CLOUDS", node.SAH) else None
    node.aft_cb(Odometry(t, Ra, pa))
    if cloud is not None and order == "aft_first":
        node.sah_cloud_cb(cloud) if getattr(node, "KF_CLOUDS", node.SAH) else None
    if cloud is not None and getattr(node, "KF_CLOUDS", node.SAH) and not node.SAH_SYNC:
        time.sleep(0.15)          # real time between keyframes is >= 0.3 s; let the worker keep up mostly
node.log.close()
print("rows %d, %.0f s; SAH: %s" % (len(L), time.time() - t0, (node.sah.stats, node.sah_state["n_kf"], node.sah_state["dropped"], np.degrees(node.sah_state["applied"])) if node.SAH else "off"))
