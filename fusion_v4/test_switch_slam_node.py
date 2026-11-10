"""Plumbing test of switch_slam_node without ROS: stub rospy/message types, drive the callbacks with a fake A-LOAM mapping
that keeps laserMapping's T_w_odom bookkeeping, check log rows, published guesses and the modes (run: python3 test_switch_slam_node.py)."""
import os, sys, types, tempfile
import numpy as np

# ---- stubs
class Msg:  # generic attribute bag
    def __init__(self, **k): self.__dict__.update(k)
def odom_msg(t, R, p):
    import fusion_core as fc
    q = fc.R_to_quat(R)
    m = Msg(header=Msg(stamp=Stamp(t)), pose=Msg(pose=Msg(position=Msg(x=p[0], y=p[1], z=p[2]),
            orientation=Msg(x=q[0], y=q[1], z=q[2], w=q[3]))))
    return m
class Stamp:
    def __init__(self, t): self.t = t
    def to_sec(self): return self.t
class Odometry(Msg):
    def __init__(self):
        self.header = Msg(stamp=None, frame_id=""); self.pose = Msg(pose=Msg(position=Msg(x=0, y=0, z=0), orientation=Msg(x=0, y=0, z=0, w=1)))
class Pub:
    def __init__(self): self.sent = []
    def publish(self, m): self.sent.append(m)
rospy = types.ModuleType("rospy"); rospy.loginfo = lambda *a, **k: None; rospy.Publisher = lambda *a, **k: Pub()
nav = types.ModuleType("nav_msgs"); nav.msg = types.ModuleType("nav_msgs.msg"); nav.msg.Odometry = Odometry
std = types.ModuleType("std_msgs"); std.msg = types.ModuleType("std_msgs.msg"); std.msg.Float64MultiArray = Msg
for n, m in [("rospy", rospy), ("nav_msgs", nav), ("nav_msgs.msg", nav.msg), ("std_msgs", std), ("std_msgs.msg", std.msg)]:
    sys.modules[n] = m
os.chdir(tempfile.mkdtemp())
os.environ["RUN_TAG"] = "TEST"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fusion_core as fc, switch_slam_core as sw
import switch_slam_node as node

R_IL, t_IL = node.R_IL, node.t_IL
def H_from_rad(Hr): D = np.diag([2.0, 2, 2, 1, 1, 1]); return D @ Hr @ D
H_ISO = H_from_rad(np.diag([400.0] * 6)); H_DEG = H_from_rad(np.diag([400.0, 400, 400, 1.0, 400, 400]))
pub_msgs = node.pub[0] = Pub()

def T(k): return k * 0.1
def truth(k):
    t = T(k); return fc.so3_exp([0, 0, 0.05 * np.sin(t)]), np.array([t, 0.1 * np.sin(t), 0.0])
def vins_msg(t, RI, pI): return odom_msg(t, RI, pI)

# fake mapping (laserMapping bookkeeping)
Two = (np.eye(3), np.zeros(3))
rng = np.random.default_rng(0)
vx = 0.0
n = 260
for k in range(1, n + 1):
    t = 100.0 + T(k); RL, pL = truth(k)
    deg = k > 120
    # VINS (after 30 scans): exact except 0.5 % along x
    if k > 30:
        vx += 0.1 * 1.005
        RI = RL @ R_IL.T; pI = np.array([vx, pL[1], 0.0]) - RI @ t_IL
        node.vins_cb(vins_msg(t, RI, pI))
    node.hess_cb(Msg(data=list((H_DEG if deg else H_ISO).ravel()) + [1.0, 100.0]))
    odo = (RL, pL + (np.array([rng.normal() * 0.05, 0, 0]) if deg else 0))
    node.laser_odom_cb(odom_msg(t, *odo))
    P = pub_msgs.sent[-1]; Pp = (fc.quat_to_R([P.pose.pose.orientation.x, P.pose.pose.orientation.y, P.pose.pose.orientation.z, P.pose.pose.orientation.w]),
                                 np.array([P.pose.pose.position.x, P.pose.pose.position.y, P.pose.pose.position.z]))
    g = sw.pose_mul(Two, Pp)
    aft_p = np.array([g[1][0] + rng.normal() * 0.03 if deg else pL[0], pL[1], 0.0])
    aft = (RL, aft_p)
    node.aft_cb(odom_msg(t, *aft))
    Two = sw.pose_mul(aft, sw.pose_inv(Pp))

node.log.flush()
import pandas as pd
L = pd.read_csv("switching_log_v2_TEST.csv")
print(len(L), "rows; modes", L["mode"].value_counts().to_dict(), "cases", L["sw_case"].value_counts().to_dict())
assert len(L) == n
assert L["mode"].iloc[0] == "SW_INIT"
assert (L["mode"].iloc[:30] == "SW_INIT").sum() == 1 and (L["mode"].iloc[1:30] == "SW_LIDAR").all()        # no VINS yet -> LiDAR
assert (L["sw_vo_fail"].iloc[1:30] == 1).all() and (L["sw_vo_fail"].iloc[32:] == 0).all()
d = L.iloc[125:]
assert (d["sw_case"] == 3).all() and set(d["mode"].unique()) <= {"SW_VO", "SW_INTERP"}
ex = L["fused_x"].values[-1] - (100 + T(n) - 100)                 # final x vs truth x = T(n)
print("final x error %.3f m (VINS scale error alone would give %.3f)" % (L["fused_x"].values[-1] - T(n), 0.005 * (n - 30) * 0.1))
assert abs(L["fused_x"].values[-1] - T(n)) < 0.2
assert (L["sw_race"] == 0).all()
print("node plumbing test passed")

# additional-T lookup: exact stamp, else the newest earlier scan within the lag limit, else none
node.t_buf.clear()
Ta, Tb = np.eye(3) / 3, np.diag([0.1, 0.45, 0.45])
node.t_buf.append((10.0, Ta)); node.t_buf.append((10.1, Tb))
assert node.t_at(10.1)[1] == 0.0 and np.allclose(node.t_at(10.1)[0], Tb)
r = node.t_at(10.2); assert r is not None and abs(r[1] - 0.1) < 1e-9 and np.allclose(r[0], Tb), "newest earlier tensor, 0.1 s old"
assert node.t_at(10.1 + node.T_LAG_MAX + 0.01) is None, "too old: none"
print("additional-T lag lookup test passed")
