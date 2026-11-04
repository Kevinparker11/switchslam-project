"""SWI (gyro prior): integration, frame conversion, core use, node plumbing without ROS.  Run: python3 test_gyro_prior.py"""
import os, sys, types, tempfile
import numpy as np
os.environ["GYRO"] = "1"; os.environ["RUN_TAG"] = "TESTG"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fusion_core as fc, gyro_prior as gp, switch_slam_core as sw

# 1 constant rate, irregular sampling, interval inside the sample span
g = gp.GyroBuffer(); w = np.array([0.1, -0.2, 0.5]); rng = np.random.default_rng(0); t = 10.0
while t < 11.0: g.add(t, *w); t += rng.uniform(0.002, 0.008)
R = g.rotation(10.2, 10.7); E = fc.so3_exp(w * 0.5)
assert np.linalg.norm(fc.so3_log(R.T @ E)) < 1e-9, "constant-rate integration"
# 2 ends not covered -> None
assert g.rotation(9.0, 10.5) is None and g.rotation(10.5, 12.0) is None and gp.GyroBuffer().rotation(0, 1) is None
# 3 varying rate: yaw rate = 0.3*t, exact angle 0.15*(t1^2-t0^2); zero-order hold error small at 400 Hz
g = gp.GyroBuffer()
for t in np.arange(0.0, 2.0, 0.0025): g.add(t, 0, 0, 0.3 * t)
ang = fc.so3_log(g.rotation(0.5, 1.5))[2]; assert abs(ang - 0.15 * (1.5 ** 2 - 0.5 ** 2)) < 2e-3, ang
# 4 frame: IMU rotated 90 deg about z relative to the LiDAR; rotation about the LiDAR x axis shows up about the IMU's y axis
R_IL = fc.so3_exp([0, 0, np.pi / 2]); dR_L = fc.so3_exp([0.1, 0, 0]); dR_I = R_IL @ dR_L @ R_IL.T
assert np.linalg.norm(gp.to_lidar(dR_I, R_IL) - dR_L) < 1e-12
# 5 core: gyro replaces the rotation of the LiDAR increment, keeps translation, logs the difference; no gyro = unchanged
core = sw.SwitchSlamCore(n_buf=5, lt=sw.LT_PUBLISHED, hess_frame="body")
I = np.eye(3); o0 = (I, np.zeros(3)); o1 = (fc.so3_exp([0, 0, 0.02]), np.array([0.3, 0.0, 0.0]))
core.init((I, np.zeros(3)), o0, None, o0, t=1.0)
H_OK = np.diag([2.0, 2, 2, 1, 1, 1]) @ np.diag([400.0] * 6) @ np.diag([2.0, 2, 2, 1, 1, 1])
d0 = core.decide(o1, None, H_OK); dg = core.decide(o1, None, H_OK, gyro_dR=fc.so3_exp([0, 0, 0.05]), t=1.1)
assert not d0["gyro"] and np.isnan(d0["gyro_deg"]) and dg["gyro"]
assert abs(dg["gyro_deg"] - np.degrees(0.03)) < 1e-9
assert np.linalg.norm(fc.so3_log(dg["guess"][0]) - [0, 0, 0.05]) < 1e-12 and np.allclose(dg["guess"][1], [0.3, 0, 0])
assert np.linalg.norm(fc.so3_log(d0["guess"][0]) - [0, 0, 0.02]) < 1e-12, "plain replica unchanged"
core.finish((dg["guess"][0], dg["guess"][1]), H_OK, dg, o1); assert core.prev_t == 1.1

# 6 node: stubbed ROS, constant yaw rate IMU, matching LiDAR odometry
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
def mod(n, **a): m = types.ModuleType(n); m.__dict__.update(a); sys.modules[n] = m
mod("rospy", loginfo=lambda *a, **k: None, Publisher=lambda *a, **k: Pub()); mod("nav_msgs"); mod("nav_msgs.msg", Odometry=Odometry)
mod("std_msgs"); mod("std_msgs.msg", Float64MultiArray=Msg)
os.chdir(tempfile.mkdtemp())
import switch_slam_node as node
assert node.GYRO
node.pub[0] = Pub()
def odom(t, R, p):
    q = fc.R_to_quat(R); return Msg(header=Msg(stamp=Stamp(t)), pose=Msg(pose=Msg(position=Msg(x=p[0], y=p[1], z=p[2]), orientation=Msg(x=q[0], y=q[1], z=q[2], w=q[3]))))
wz = 0.4                                            # rad/s about the LiDAR z axis (IMU z = LiDAR z up to R_IL, taken from the node)
w_I = node.R_IL @ np.array([0, 0, wz])
for i in range(3000): node.imu_cb(Msg(header=Msg(stamp=Stamp(100.0 + 0.0025 * i)), angular_velocity=Msg(x=w_I[0], y=w_I[1], z=w_I[2])))
H = list((np.diag([2.0, 2, 2, 1, 1, 1]) @ np.diag([400.0] * 6) @ np.diag([2.0, 2, 2, 1, 1, 1])).ravel())
for k in range(1, 40):
    t = 100.0 + 0.1 * k; R = fc.so3_exp([0, 0, wz * 0.1 * k]); p = np.array([0.1 * k, 0, 0])
    node.hess_cb(Msg(data=H + [1.0, 100.0])); node.laser_odom_cb(odom(t, R, p)); node.aft_cb(odom(t, R, p))
node.log.flush()
import pandas as pd
L = pd.read_csv("switching_log_v2_TESTG.csv")
assert len(L) == 39 and (L["sw_gyro"].iloc[1:] == 1).all() and L["sw_gyro"].iloc[0] == 0
assert L["sw_gyro_deg"].iloc[1:].abs().max() < 0.05, L["sw_gyro_deg"].iloc[1:].abs().max()      # gyro and odometry agree to 0.05 deg
print("gyro prior tests passed (rotation agreement in node test: max %.4f deg)" % L["sw_gyro_deg"].iloc[1:].abs().max())
