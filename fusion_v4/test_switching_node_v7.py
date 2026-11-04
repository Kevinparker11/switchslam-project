"""The ported generation-1 node (switching_node_v7.py) must make exactly the decisions of the original
(../switchslam_v1/multifloor/switching_node_multifloor.py).  Both files are loaded with stubbed ROS, fed the same synthetic
messages (normal, transition and fully-degenerate stretches, a VINS jump, a feature drop) and the fused poses, modes and the
published odometry are compared.  Also checks the log schema the scorer needs.  Run: python3 test_switching_node_v7.py"""
import importlib.util, os, sys, tempfile, types
import numpy as np

class Msg:
    def __init__(self, **k): self.__dict__.update(k)
class Stamp:
    def __init__(self, t): self.t = t
    def to_sec(self): return self.t
class Odometry(Msg):
    def __init__(self):
        self.header = Msg(stamp=None, frame_id=""); self.pose = Msg(pose=Msg(position=Msg(x=0, y=0, z=0), orientation=Msg(x=0, y=0, z=0, w=1)))
class Pub:
    def __init__(self): self.sent = []
    def publish(self, m): self.sent.append(m)
def mod(name, **attrs):
    m = types.ModuleType(name); m.__dict__.update(attrs); sys.modules[name] = m; return m
mod("rospy", loginfo=lambda *a, **k: None, Publisher=lambda *a, **k: Pub(), Subscriber=lambda *a, **k: None, init_node=lambda *a, **k: None,
    spin=lambda: None, Timer=lambda *a, **k: None, Duration=lambda s: s)
mod("message_filters", Subscriber=lambda *a, **k: None, ApproximateTimeSynchronizer=lambda *a, **k: Msg(registerCallback=lambda f: None))
mod("std_msgs"); mod("std_msgs.msg", Float64MultiArray=Msg)
mod("nav_msgs"); mod("nav_msgs.msg", Odometry=Odometry)
mod("sensor_msgs"); mod("sensor_msgs.msg", PointCloud=Msg)

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["RUN_TAG"] = "TESTV7"
def load(name, path):
    d = tempfile.mkdtemp(); os.chdir(d)
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    m.fused_pub[0] = Pub(); return m, d
orig, d0 = load("orig", os.path.join(HERE, "..", "switchslam_v1", "multifloor", "switching_node_multifloor.py"))
port, d1 = load("port", os.path.join(HERE, "switching_node_v7.py"))

def quat(rv):
    a = np.linalg.norm(rv)
    return [0, 0, 0, 1.0] if a < 1e-12 else list(np.r_[np.array(rv) / a * np.sin(a / 2), np.cos(a / 2)])
def odom(t, p, rv):
    q = quat(rv); return Msg(header=Msg(stamp=Stamp(t)), pose=Msg(pose=Msg(position=Msg(x=p[0], y=p[1], z=p[2]), orientation=Msg(x=q[0], y=q[1], z=q[2], w=q[3]))))
def hmsg(diag, extra=()): return Msg(data=list(np.diag(diag).ravel()) + list(extra))
H_OK, H_DEG = [400.0] * 6, [400.0, 400, 400, 1.0, 400, 400]        # eigenvalues sorted ascending: one tiny -> degenerate

rng = np.random.default_rng(1)
n = 300
for k in range(1, n + 1):
    t = 50.0 + 0.1 * k
    lp = np.array([0.1 * k + rng.normal() * 0.01, 0.02 * np.sin(0.1 * k), 0.0]); lrv = [0, 0, 0.01 * k]
    vp = lp * 1.02 + rng.normal(size=3) * 0.01; vrv = [0, 0, 0.01 * k + 0.002]
    if k == 200: vp = vp + np.array([4.0, 0, 0])                    # VINS jump -> VO failure
    deg = 60 <= k < 140 or 220 <= k < 232                           # a long degenerate stretch and a short one
    feat = 8 if 250 <= k < 255 else 120                             # feature drop -> VO failure
    hm = hmsg(H_DEG if deg else H_OK, extra=(5.0, 100.0) if k % 2 else ())    # with and without the cost/residual tail
    vm = hmsg([50.0] * 6)
    for m in (orig, port):
        m.feat_cb(Msg(points=[0] * feat)); m.aft_cb(odom(t, lp + 0.01, lrv))
        m.fast_odom_cb(odom(t, lp, lrv))
        if m is orig: m.sync_cb(Msg(data=hm.data[:36]), vm, odom(t, lp, lrv), odom(t, vp, vrv))   # the original cannot take the 38-entry message
        else: m.sync_cb(hm, vm, odom(t, lp, lrv), odom(t, vp, vrv))

for m in (orig, port): m.log.flush()
import pandas as pd
A = pd.read_csv(os.path.join(d0, "switching_log_multifloor.csv")); B = pd.read_csv(os.path.join(d1, "switching_log_v2_TESTV7.csv"))
print(len(A), "rows;", B["mode"].value_counts().to_dict())
assert len(A) == len(B) == n - 1
assert (A["mode"] == B["mode"]).all()
cols = ["fused_x", "fused_y", "fused_z", "fused_qx", "fused_qy", "fused_qz", "fused_qw"]
assert np.array_equal(A[cols].values, B[cols].values), "fused poses differ"
assert set(B["mode"]) >= {"LIDAR_ONLY", "TRANSITION", "TIGHTLY_COUPLED", "LIDAR_ONLY_SAFE"}, set(B["mode"])
pa = np.array([[o.pose.pose.position.x, o.pose.pose.position.y, o.pose.pose.position.z, o.pose.pose.orientation.w] for o in orig.fused_pub[0].sent])
pb = np.array([[o.pose.pose.position.x, o.pose.pose.position.y, o.pose.pose.position.z, o.pose.pose.orientation.w] for o in port.fused_pub[0].sent])
assert np.array_equal(pa, pb), "published odometry differs"
need = ["time", "mode", "fused_x", "aft_x", "aft_qw", "v_px", "v_qw", "hess_src", "Hl_00", "Hl_55", "feat_count"]
assert all(c in B for c in need) and abs(B["time"].iloc[0] - 50.2) < 1e-9
assert B["Hl_00"].notna().all()
print("ported v7 node = original rule on", n - 1, "rows (modes, fused poses, published odometry identical); log schema ok")
