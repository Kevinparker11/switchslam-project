"""SWF (LiDAR-IMU propagation): gravity initialisation, increment accuracy with biases and noise, dropped scans, coverage fallback, core use,
node plumbing without ROS.  Run: python3 test_imu_prop.py"""
import os, sys, types, tempfile
import numpy as np
os.environ["IMU_PROP"] = "1"; os.environ["RUN_TAG"] = "TESTF"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fusion_core as fc, imu_prop as ip, switch_slam_core as sw

rng = np.random.default_rng(1)
G_TRUE = fc.so3_exp([0.3, -0.2, 0.1]) @ np.array([0.0, 0.0, -9.81007])       # chain frame is tilted against gravity
R_IL = fc.so3_exp([0.02, -0.01, 1.5])                                       # IMU rotated about 86 deg in yaw against the LiDAR
t_IL = np.array([0.08, 0.03, 0.03])
BG, BA = np.array([0.01, -0.005, 0.008]), np.array([0.05, -0.03, 0.04])
FS = 400.0
T_MOVE = 2.0


def truth(t):
    """IMU-frame pose, velocity and world acceleration at time t (static until T_MOVE, then constant acceleration and a turn)"""
    s = max(0.0, t - T_MOVE)
    p = np.array([0.4 * s * s, 0.2 * s * s, 0.05 * s * s]) + np.array([1.0, 2.0, 3.0])
    v = np.array([0.8 * s, 0.4 * s, 0.1 * s]); a = np.array([0.8, 0.4, 0.1]) if t >= T_MOVE else np.zeros(3)
    w_body = np.array([0.0, 0.0, 0.25]) if t >= T_MOVE else np.zeros(3)
    ang = 0.25 * s
    R = fc.so3_exp([0.2, 0.1, 0.4]) @ fc.so3_exp([0, 0, ang])
    return R, p, v, a, w_body


def imu_sample(t, noise=True):
    R, p, v, a, w = truth(t)
    f = R.T @ (a - G_TRUE)
    g = w + BG + (rng.normal(0, 0.003, 3) if noise else 0)
    f = f + BA + (rng.normal(0, 0.05, 3) if noise else 0)
    return g, f


def lidar_pose(t, noise=0.0):
    R, p, _, _, _ = truth(t)
    RL = R @ R_IL
    pL = p + R @ t_IL
    if noise:
        RL = RL @ fc.so3_exp(rng.normal(0, noise / 5, 3)); pL = pL + rng.normal(0, noise, 3)
    return RL, pL


def feed(f, t0, t1):
    for t in np.arange(t0, t1, 1.0 / FS):
        g, a = imu_sample(t); f.add(t, g, a)


# ---- 1 gravity and gyro bias from the quiet start
f = ip.ImuPropagator(R_IL, t_IL)
feed(f, 0.0, 1.6)
assert not f.try_init(0.5, *lidar_pose(0.5)), "window shorter than init_win must not initialise"
assert f.try_init(1.5, *lidar_pose(1.5))
assert np.linalg.norm(f.g - G_TRUE) < 0.12, (f.g, G_TRUE)                    # accelerometer bias of norm 0.07 m/s^2 tilts the gravity direction by up to 0.4 deg
assert np.linalg.norm(f.bg - BG) < 0.004, f.bg

# ---- 2 moving: after a few updates the increment is accurate (rotation and translation, LiDAR frame), also over dropped scans
f = ip.ImuPropagator(R_IL, t_IL)
feed(f, 0.0, 8.0)
assert f.try_init(1.5, *lidar_pose(1.5))
t = 1.5; errs_p, errs_r, errs_p3 = [], [], []
while t < 7.0:
    tn = round(t + 0.1, 4)
    inc = f.increment(tn)
    R0, p0 = lidar_pose(t); R1, p1 = lidar_pose(tn)
    dR_true, dp_true = fc.rel_body(R0, p0, R1, p1)
    if t > 4.0:
        errs_p.append(np.linalg.norm(inc[1] - dp_true)); errs_r.append(np.degrees(np.linalg.norm(fc.so3_log(inc[0].T @ dR_true))))
        inc3 = f.increment(round(t + 0.3, 4)); R3, p3 = lidar_pose(round(t + 0.3, 4)); _, dp3 = fc.rel_body(R0, p0, R3, p3)
        errs_p3.append(np.linalg.norm(inc3[1] - dp3))
    d = f.update(tn, *lidar_pose(tn, noise=0.02))
    assert d["covered"]
    t = tn
assert max(errs_p) < 0.008 and np.mean(errs_p) < 0.004, (max(errs_p), np.mean(errs_p))      # 100 ms step 0.08 m per 0.1 s: under 10 %
assert max(errs_r) < 0.4, max(errs_r)
assert max(errs_p3) < 0.03, max(errs_p3)                                       # three scans without update
assert np.linalg.norm(f.bg - BG) < 0.006 and np.linalg.norm(f.ba - BA) < 0.1, (f.bg, f.ba)
R_t, _, v_t, _, _ = truth(7.0); assert np.linalg.norm(f.v - v_t) < 0.1, (f.v, v_t)

# ---- 3 the IMU keeps the translation where a scan-to-scan odometer slides: a pose update that does NOT move (LiDAR stuck along x) still
#      gives an IMU increment of the true size at the next scan
f = ip.ImuPropagator(R_IL, t_IL); feed(f, 0.0, 8.0); f.try_init(1.5, *lidar_pose(1.5))
t = 1.5
while t < 5.0:
    tn = round(t + 0.1, 4); f.update(tn, *lidar_pose(tn, noise=0.02)); t = tn
inc = f.increment(round(t + 0.1, 4)); R0, p0 = lidar_pose(t); R1, p1 = lidar_pose(round(t + 0.1, 4)); _, dp_true = fc.rel_body(R0, p0, R1, p1)
assert np.linalg.norm(inc[1]) > 0.5 * np.linalg.norm(dp_true) and np.linalg.norm(inc[1] - dp_true) < 0.01

# ---- 4 coverage: no IMU for a scan -> None, update re-seeds the pose and keeps v
f = ip.ImuPropagator(R_IL, t_IL); feed(f, 0.0, 3.0); f.try_init(1.5, *lidar_pose(1.5))
assert f.increment(1.6) is not None
assert f.increment(3.4) is None, "IMU ends at 3.0: a scan at 3.4 is not covered"
v_before = f.v.copy(); d = f.update(5.0, *lidar_pose(5.0)); assert d["covered"] is False and np.allclose(f.v, v_before) and f.t == 5.0
assert f.increment(5.0) is None and f.increment(4.0) is None                 # not later than the state
assert not ip.ImuPropagator(R_IL, t_IL).try_init(1.0, np.eye(3), np.zeros(3)), "no samples"
# moving start: not quiet -> not initialised
f = ip.ImuPropagator(R_IL, t_IL)
for t in np.arange(0.0, 6.0, 1 / FS): g, a = imu_sample(t); f.add(t, g, a)
assert not f.try_init(5.0, *lidar_pose(5.0)), "a window with 0.8 m/s^2 acceleration and a turn is not quiet"

# ---- 5 core: imu_dT replaces the whole LiDAR increment, differences logged, no imu = unchanged
core = sw.SwitchSlamCore(n_buf=5, lt=sw.LT_PUBLISHED, hess_frame="body")
I = np.eye(3); o0 = (I, np.zeros(3)); o1 = (fc.so3_exp([0, 0, 0.02]), np.array([0.3, 0.0, 0.0]))
core.init((I, np.zeros(3)), o0, None, o0, t=1.0)
H_OK = np.diag([2.0, 2, 2, 1, 1, 1]) @ np.diag([400.0] * 6) @ np.diag([2.0, 2, 2, 1, 1, 1])
d0 = core.decide(o1, None, H_OK)
dT = (fc.so3_exp([0, 0, 0.05]), np.array([0.5, 0.1, 0.0]))
d1 = core.decide(o1, None, H_OK, t=1.1, imu_dT=dT)
assert not d0["imu"] and d1["imu"] and not d1["gyro"]
assert abs(d1["imu_rdeg"] - np.degrees(0.03)) < 1e-9 and abs(d1["imu_tdiff"] - np.linalg.norm([0.2, 0.1, 0.0])) < 1e-12
assert np.allclose(d1["guess"][1], [0.5, 0.1, 0.0]) and np.linalg.norm(fc.so3_log(d1["guess"][0]) - [0, 0, 0.05]) < 1e-12
assert np.allclose(d0["guess"][1], [0.3, 0, 0]), "plain replica unchanged"
# a degenerate scan with a trusted VINS step still goes to the VINS guess; the IMU replaces only the LiDAR side
H_DEG = np.diag([100.0, 100, 100, 1, 100, 100])
v0 = (I, np.zeros(3)); v1 = (I, np.array([0.1, 0.0, 0.0]))
core2 = sw.SwitchSlamCore(n_buf=5, lt=sw.LT_PUBLISHED, hess_frame="body"); core2.init((I, np.zeros(3)), o0, v0, o0, t=1.0)
dd = core2.decide(o1, v1, H_DEG, t=1.1, imu_dT=dT)
assert dd["kind"] in ("VO", "INTERP", "LIDAR")

# ---- 6 node plumbing, stubbed ROS: IMU data with the real trajectory, LiDAR poses = truth; the IMU increment agrees with the truth
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
assert node.IMU_PROP and not node.GYRO
node.pub[0] = Pub()
node.imu = ip.ImuPropagator(node.R_IL, node.t_IL)           # the node's own extrinsic
R_IL, t_IL = node.R_IL, node.t_IL
def odom(t, R, p):
    q = fc.R_to_quat(R); return Msg(header=Msg(stamp=Stamp(t)), pose=Msg(pose=Msg(position=Msg(x=p[0], y=p[1], z=p[2]), orientation=Msg(x=q[0], y=q[1], z=q[2], w=q[3]))))
for t in np.arange(0.0, 8.0, 1 / FS):
    g, a = imu_sample(t); node.imu_cb(Msg(header=Msg(stamp=Stamp(t)), angular_velocity=Msg(x=g[0], y=g[1], z=g[2]), linear_acceleration=Msg(x=a[0], y=a[1], z=a[2])))
H = list(H_OK.ravel())
n = 0
for k in range(15, 71):
    t = round(0.1 * k, 4); RL, pL = lidar_pose(t)
    node.hess_cb(Msg(data=H + [1.0, 100.0])); node.laser_odom_cb(odom(t, RL, pL)); node.aft_cb(odom(t, RL, pL)); n += 1
node.log.flush()
import pandas as pd
L = pd.read_csv("switching_log_v2_TESTF.csv")
assert len(L) == n and "sw_imu" in L.columns
assert L["sw_imu"].iloc[0] == 0 and L["sw_imu"].iloc[1] == 1, "first scan = initialisation (quiet window found, filter starts); the next scan already uses the IMU"
used = L[L["sw_imu"] == 1]
assert len(used) > 40, len(used)
late = L[L["time"] > 4.0]
assert (late["sw_imu_rdeg"].abs() < 0.5).all() and (late["sw_imu_tdiff"].abs() < 0.01).all(), (late["sw_imu_rdeg"].abs().max(), late["sw_imu_tdiff"].abs().max())
print("IMU propagation tests passed (node: IMU used in %d of %d scans, max |IMU - truth| after 4 s: %.2f deg, %.4f m)"
      % (len(used), len(L), late["sw_imu_rdeg"].abs().max(), late["sw_imu_tdiff"].abs().max()))
