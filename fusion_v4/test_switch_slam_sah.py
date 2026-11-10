"""F34 plumbing test without ROS: the heading anchor (SAH) in switch_slam_node corrects a slowly drifting VINS-Mono yaw (F33 rotation source) against a
room with vertical walls, and does nothing harmful without drift.  Runs the node twice in subprocesses (SAH=0 and SAH=1) and compares the final
heading error.   run: python3 test_switch_slam_sah.py"""
import os, subprocess, sys, json

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
import fusion_core as fc, switch_slam_core as sw
import switch_slam_node as node
def odom_msg(t, R, p):
    q = fc.R_to_quat(R)
    return Msg(header=Msg(stamp=Stamp(t)), pose=Msg(pose=Msg(position=Msg(x=p[0], y=p[1], z=p[2]), orientation=Msg(x=q[0], y=q[1], z=q[2], w=q[3]))))
def cloud_msg(t, P):
    a = P.astype("<f4").tobytes()
    return Msg(header=Msg(stamp=Stamp(t)), fields=[Msg(name="x", offset=0), Msg(name="y", offset=4), Msg(name="z", offset=8)], point_step=12, width=len(P), height=1, data=a)
R_IL, t_IL = node.R_IL, node.t_IL
rng = np.random.default_rng(1)
def room(n=9000):                                         # vertical walls of a 50 x 16 m room (z in [0, 3]), sampled; both wall directions present
    w = []
    for _ in range(n):
        z = rng.uniform(0, 3); s = rng.uniform()
        if s < 0.35: w.append([rng.uniform(-10, 40), 8.0 + rng.normal() * 0.01, z])
        elif s < 0.7: w.append([rng.uniform(-10, 40), -8.0 + rng.normal() * 0.01, z])
        elif s < 0.85: w.append([40.0 + rng.normal() * 0.01, rng.uniform(-8, 8), z])
        else: w.append([-10.0 + rng.normal() * 0.01, rng.uniform(-8, 8), z])
    return np.array(w)
ROOM = room()
DRIFT = float(os.environ["DRIFT_DEG_PER_SCAN"]); N = 1200
H_ISO = np.diag([2.0, 2, 2, 1, 1, 1]) @ np.diag([400.0] * 6) @ np.diag([2.0, 2, 2, 1, 1, 1])
node.pub[0] = Pub(); pub_msgs = node.pub[0]
Two = (np.eye(3), np.zeros(3))
for k in range(1, N + 1):
    t = 100.0 + 0.1 * k; RL = np.eye(3); pL = np.array([0.1 * k * 0.8, 0.0, 0.0])
    Rdr = fc.so3_exp([0, 0, np.radians(DRIFT) * k])        # VINS-Mono yaw drift against the world structure
    RI = Rdr @ RL @ R_IL.T; pI = pL - RI @ t_IL
    node.vins_cb(odom_msg(t, RI, pI))
    node.hess_cb(Msg(data=list(H_ISO.ravel()) + [1.0, 100.0]))
    node.laser_odom_cb(odom_msg(t, RL, pL))
    P = pub_msgs.sent[-1]
    Pp = (fc.quat_to_R([P.pose.pose.orientation.x, P.pose.pose.orientation.y, P.pose.pose.orientation.z, P.pose.pose.orientation.w]),
          np.array([P.pose.pose.position.x, P.pose.pose.position.y, P.pose.pose.position.z]))
    g = sw.pose_mul(Two, Pp)
    aft = (RL, pL)                                         # A-LOAM is right (the room's structure fixes it)
    if node.SAH:
        sub = ROOM[rng.choice(len(ROOM), 5000, replace=False)]
        node.sah_cloud_cb(cloud_msg(t, sub))
    node.aft_cb(odom_msg(t, *aft))
    Two = sw.pose_mul(aft, sw.pose_inv(Pp))
node.log.flush()
import pandas as pd
L = pd.read_csv("switching_log_v2_TEST.csv")
q = L[["fused_qx", "fused_qy", "fused_qz", "fused_qw"]].values[-1]
R = fc.quat_to_R(q); yaw = float(np.degrees(np.arctan2(R[1, 0], R[0, 0])))
import json
print("RESULT " + json.dumps(dict(logsah=float(L["sah_total_deg"].iloc[-1]), yaw=yaw, n_kf=node.sah_state["n_kf"], applied=float(np.degrees(node.sah_state["applied"])), acc=(node.sah.stats["acc"] if node.SAH else 0), stats=(node.sah.stats if node.SAH else {}))))
'''

def run(sah, drift):
    env = dict(os.environ, SAH=str(sah), SAH_SYNC="1", ROT_SRC="vins", DRIFT_DEG_PER_SCAN=str(drift), HERE=os.path.dirname(os.path.abspath(__file__)))
    code = "HERE=%r\n" % env["HERE"] + CHILD
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    out = [l for l in r.stdout.splitlines() if l.startswith("RESULT ")]
    assert out, (r.stdout[-2000:], r.stderr[-2000:])
    warns = [l for l in r.stdout.splitlines() if l.startswith("WARN")]
    return json.loads(out[0][7:]), warns

if __name__ == "__main__":
    base, _ = run(0, 0.004)
    sah, warns = run(1, 0.004)
    none, warns0 = run(1, 0.0)
    print("drift 0.004 deg/scan = 0.04 deg/s, inside SAH's physical rate bound (4.8 deg over 120 s): final yaw error without SAH %.2f deg, with SAH %.2f deg (applied %.2f, accepted %d of %d keyframes)"
          % (base["yaw"], sah["yaw"], sah["applied"], sah["acc"], sah["n_kf"]))
    print("no drift, SAH on: final yaw %.3f deg" % none["yaw"])
    assert not warns and not warns0, (warns, warns0)
    assert sah["n_kf"] >= 80 and sah["acc"] >= 40
    assert abs(sah["logsah"] - sah["applied"]) < 1e-6 and abs(sah["applied"]) > 1.0, sah     # the log column carries the applied correction (it was left at 0 in the first F34 run)
    assert abs(base["yaw"]) > 4.0, base
    assert abs(sah["yaw"]) < 0.6 * abs(base["yaw"]), (base, sah)       # corrects most of the drift
    assert abs(none["yaw"]) < 0.5, none                                 # no drift: no harm
    print("SAH node plumbing test passed")
