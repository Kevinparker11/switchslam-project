"""F35 plumbing test without ROS: fusion_node_v2 with the F35 settings (GUESS_MODE=ours, orientation tensor from keyframes, SAH) runs through
the callbacks on a synthetic room, publishes a guess for every scan, logs the guess kinds, and the keyframe tensor reaches the guess detector.
run: python3 test_fusion_node_ours.py"""
import os, subprocess, sys

CHILD = r'''
import os, sys, types, tempfile
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
rospy = types.ModuleType("rospy"); rospy.loginfo = lambda *a, **k: None; rospy.logwarn = lambda *a, **k: print("WARN", *a); rospy.Publisher = lambda *a, **k: Pub()
rospy.is_shutdown = lambda: False
nav = types.ModuleType("nav_msgs"); nav.msg = types.ModuleType("nav_msgs.msg"); nav.msg.Odometry = Odometry
std = types.ModuleType("std_msgs"); std.msg = types.ModuleType("std_msgs.msg"); std.msg.Float64MultiArray = Msg
for n, m in [("rospy", rospy), ("nav_msgs", nav), ("nav_msgs.msg", nav.msg), ("std_msgs", std), ("std_msgs.msg", std.msg)]:
    sys.modules[n] = m
os.chdir(tempfile.mkdtemp()); os.environ["RUN_TAG"] = "TEST"
sys.path.insert(0, HERE)
import fusion_core as fc
import fusion_node_v2 as node
def odom_msg(t, R, p):
    q = fc.R_to_quat(R)
    return Msg(header=Msg(stamp=Stamp(t)), pose=Msg(pose=Msg(position=Msg(x=p[0], y=p[1], z=p[2]), orientation=Msg(x=q[0], y=q[1], z=q[2], w=q[3]))))
def cloud_msg(t, P):
    return Msg(header=Msg(stamp=Stamp(t)), fields=[Msg(name="x", offset=0), Msg(name="y", offset=4), Msg(name="z", offset=8)], point_step=12, width=len(P), height=1, data=P.astype("<f4").tobytes())
R_IL, t_IL = node.R_IL, node.t_IL
rng = np.random.default_rng(1)
w = []
for _ in range(9000):
    z = rng.uniform(0, 3); s = rng.uniform()
    if s < 0.35: w.append([rng.uniform(-10, 60), 8.0, z])
    elif s < 0.7: w.append([rng.uniform(-10, 60), -8.0, z])
    elif s < 0.85: w.append([60.0, rng.uniform(-8, 8), z])
    else: w.append([-10.0, rng.uniform(-8, 8), z])
ROOM = np.array(w)
D6 = np.diag([2.0, 2, 2, 1, 1, 1])
H_ISO = D6 @ np.diag([400.0] * 6) @ D6
if os.environ.get("HDEG") == "1":
    H_ISO = D6 @ np.diag([400.0, 400, 400, 1.0, 400, 400]) @ D6      # translation x has almost no information
node.pub[0] = Pub(); pub_msgs = node.pub[0]
N = 700
for k in range(1, N + 1):
    t = 100.0 + 0.1 * k; RL = np.eye(3); pL = np.array([0.08 * k, 0.0, 0.0])
    RI = RL @ R_IL.T; pI = pL - RI @ t_IL
    node.vins_cb(odom_msg(t, RI, pI))
    node.hess_cb(Msg(data=list(H_ISO.ravel()) + [1.0, 100.0]))
    node.laser_odom_cb(odom_msg(t, RL, pL))
    node.sah_cloud_cb(cloud_msg(t, ROOM[rng.choice(len(ROOM), 5000, replace=False)]))
    node.aft_cb(odom_msg(t, RL, pL))
node.log.flush()
import pandas as pd
L = pd.read_csv("switching_log_v2_TEST.csv")
print("RESULT", len(L), len(pub_msgs.sent), L["guess_kind"].value_counts().to_dict(), node.ot_state["n_kf"], node.sah_state["n_kf"], round(float(L["fused_x"].iloc[-1]), 3))
'''

def run(extra):
    env = dict(os.environ, SAH_SYNC="1", FUSION_MODE="fused", C_T="3e-2", KAPPA_TH="1e9", SAH="1", ROT_CHECK="1", OT_SRC="geom", OT_MODE="gmax",
               VIO_CHECK="1", VIO_CHECK_FAST="5", LIDAR_GUARD_T="2", LIDAR_GUARD_EX="4.325", VIO_CHECK_REF="0.157", VIO_CHECK_FAST_REF="0.277",
               VIO_CHECK_START="1", HANDOVER="anchor", PREDICT_GUARD="1", T_WARM="5", **extra)
    code = "HERE=%r\n" % os.path.dirname(os.path.abspath(__file__)) + CHILD
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    out = [l for l in r.stdout.splitlines() if l.startswith("RESULT")]
    assert out, (r.stdout[-1500:], r.stderr[-2500:])
    warns = [l for l in r.stdout.splitlines() if l.startswith("WARN")]
    return out[0], warns

if __name__ == "__main__":
    for mode in ("status", "ours"):
        out, warns = run(dict(GUESS_MODE=mode, DET_CH="R,T,TT"))
        print(mode, out, warns[:2])
        assert not warns
        n_rows, n_pub = int(out.split()[1]), int(out.split()[2])
        assert n_rows >= 690 and n_pub >= 690
    out, warns = run(dict(GUESS_MODE="ours", DET_CH="R,T,TT", HDEG="1"))
    print("ours, weak translation x:", out, warns[:2])
    assert not warns and "'VO'" in out, out                                  # our T channel flags the scans, the guess becomes VINS-Mono's step
    print("F35 node plumbing test passed")
