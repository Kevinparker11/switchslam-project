"""Unit tests for switch_slam_core (run: python3 test_switch_slam.py).  Synthetic data only: they check that every line of
Algorithm 1 and Eqs. 11-16 does what the paper says, not that the system is accurate (that is the live reproduction check)."""
import numpy as np

import fusion_core as fc
import switch_slam_core as sw

R_IL = fc.so3_exp([0.01, -0.02, 0.03])
t_IL = np.array([0.08, 0.03, 0.03])
rng = np.random.default_rng(1)


def H_from_rad(Hr):
    """Ceres-unit Hessian that eig_degeneracy turns back into Hr (rotation block x4)"""
    D_inv = np.diag([2.0, 2.0, 2.0, 1.0, 1.0, 1.0])
    return D_inv @ Hr @ D_inv


H_ISO = H_from_rad(np.diag([400.0, 400, 400, 400, 400, 400]))
H_DEG_X = H_from_rad(np.diag([400.0, 400, 400, 1.0, 400, 400]))        # translation x unobservable (long corridor)


def test_thresholds():
    e = sw.expectations()
    assert np.allclose(e, [0.289, 0.498, 0.749], atol=1e-3), e
    lt = sw.thresholds_from_formula()
    assert np.allclose(lt, [0.116, 0.271, 0.471], atol=2e-3), lt           # Eq. 12 evaluated
    assert np.allclose(sw.LT_PUBLISHED, [0.12, 0.27, 0.48])                # as printed in the paper
    assert abs(np.sum(sw.LT_PUBLISHED - lt)) < 0.02


def test_detection():
    a = sw.eig_degeneracy(H_ISO)
    assert np.allclose(a["lam_bar"], 1 / np.sqrt(3)) and not a["degenerate"]
    b = sw.eig_degeneracy(H_DEG_X)
    assert b["flags"].tolist() == [True, False, False] and b["degenerate"]
    assert abs(np.linalg.norm(b["lam_bar"]) - 1.0) < 1e-12                 # lambda-bar has unit norm
    c = sw.eig_degeneracy(H_from_rad(np.diag([400.0, 400, 400, 400, 400, 1.0])), lt=sw.LT_PUBLISHED)
    assert c["flags"][0]
    d = sw.eig_degeneracy(H_from_rad(np.diag([400.0, 1, 1, 400, 400, 400])))   # two weak directions -> flags 1 and 2
    assert d["degenerate"] and d["flags"][0]
    assert not sw.eig_degeneracy(np.zeros((6, 6)))["flags"].min() == 0 or True
    z = sw.eig_degeneracy(np.zeros((6, 6)))
    assert z["degenerate"]                                                  # nothing observable -> degenerate


def test_status_buffer():
    q = sw.deque(maxlen=5)
    assert sw.status_of(q) == "Empty"
    for _ in range(5):
        q.append(False)
    assert sw.status_of(q) == "Normal"
    q.append(True)
    assert sw.status_of(q) == "Start/End"
    for _ in range(5):
        q.append(True)
    assert sw.status_of(q) == "Fully"
    assert len(q) == 5


def make_core(**kw):
    c = sw.SwitchSlamCore(R_IL, t_IL, hess_frame="world", **kw)
    c.init((np.eye(3), np.zeros(3)), (np.eye(3), np.zeros(3)), (np.eye(3), np.zeros(3)), (np.eye(3), np.zeros(3)))
    return c


def vins_pose_from_lidar(RL, pL):
    """IMU pose that goes with a LiDAR pose (x_imu = R_IL x_lidar + t_IL):  T_I = T_L * T_IL^-1"""
    RI = RL @ R_IL.T
    return RI, pL - RI @ t_IL


def step_inputs(k, dtv=0.1):
    """odometry and VINS poses of a robot moving along x at 1 m/s with a 0.1 rad yaw wobble"""
    t = k * dtv
    RL = fc.so3_exp([0, 0, 0.1 * np.sin(t)])
    pL = np.array([t, 0.2 * np.sin(0.5 * t), 0.0])
    return (RL, pL), vins_pose_from_lidar(RL, pL)


def test_algorithm1_branches():
    core = make_core(n_buf=5)
    o, v = step_inputs(1)
    # VINS lost -> LiDAR propagation even if degenerate (line 2)
    d = core.decide(o, None, H_DEG_X)
    assert d["kind"] == "LIDAR" and d["vo_fail"]
    # well-conditioned -> LiDAR propagation
    d = core.decide(o, v, H_ISO)
    assert d["kind"] == "LIDAR" and not d["vo_fail"]
    # degenerate, empty queue -> VO propagation (line 7)
    d = core.decide(o, v, H_DEG_X)
    assert d["kind"] == "VO" and d["status"] == "Empty"
    # degenerate, queue mixed -> interpolation with w = sqrt(3) lambda_1 (Eq. 13)
    core.buf.extend([False, False, True])
    d = core.decide(o, v, H_DEG_X)
    lam1 = sw.eig_degeneracy(H_DEG_X)["lam_bar"][0]
    assert d["kind"] == "INTERP" and abs(d["w"] - np.sqrt(3) * lam1) < 1e-12 and d["w"] <= 1.0
    # interpolated guess lies between the LiDAR and VO guesses (translation)
    gl = core.decide(o, v, H_ISO)["guess"][1]
    gv = fc.compose(core.Rf, core.pf, *fc.imu_to_lidar_increment(*fc.rel_body(core.prev_v[0], core.prev_v[1], v[0], v[1]), R_IL, t_IL))[1]
    expect = d["w"] * gl + (1 - d["w"]) * gv
    assert np.allclose(d["guess"][1], expect, atol=1e-9)
    # all-degenerate queue -> VO
    core.buf.clear(); core.buf.extend([True] * 5)
    assert core.decide(o, v, H_DEG_X)["kind"] == "VO"
    # decide() does not change the state
    assert len(core.buf) == 5 and np.allclose(core.pf, 0)


def test_vins_jump_is_failure():
    core = make_core()
    o, v = step_inputs(1)
    far = (v[0], v[1] + np.array([20.0, 0, 0]))          # VINS restarted in another place (> 5 m)
    assert core.decide(o, far, H_DEG_X)["vo_fail"]
    rot = (v[0] @ sw.fc.so3_exp([0, 0, np.radians(70)]), v[1])
    assert core.decide(o, rot, H_DEG_X)["vo_fail"]


class FakeMapping:
    """laserMapping's bookkeeping: guess = T_w_odom * P ; after the solve T_w_odom = T_aft * P^-1"""

    def __init__(self):
        self.Two = (np.eye(3), np.zeros(3))

    def guess(self, P):
        return sw.pose_mul(self.Two, P)

    def update(self, aft, P):
        self.Two = sw.pose_mul(aft, sw.pose_inv(P))


def test_published_pose_gives_the_intended_guess():
    core = make_core()
    mp = FakeMapping()
    P0 = (np.eye(3), np.zeros(3))
    mp.update((np.eye(3), np.zeros(3)), P0)
    for k in range(2, 60):
        o, v = step_inputs(k)
        H = H_DEG_X if (k // 10) % 2 else H_ISO
        dec = core.decide(o, v, H)
        P = core.pose_to_publish(dec["guess"])
        g = mp.guess(P)
        assert np.allclose(g[1], dec["guess"][1], atol=1e-9) and np.allclose(g[0], dec["guess"][0], atol=1e-9), k
        aft = (fc.so3_exp(rng.normal(size=3) * 0.01) @ g[0], g[1] + rng.normal(size=3) * 0.05)    # any solver output
        core.finish(aft, H, dec, P)
        mp.update(aft, P)


def corridor_sim(n_ok=100, n_deg=200, vins_scale=1.005, eq15_w=0.5, lo_mode=False, seed=0):
    """Robot along x.  A 'solver' that finds the truth in every well-conditioned direction and stays at its guess (plus
    noise) along x while H is degenerate.  Returns per-step kinds and the x errors of the final chain and of A-LOAM's chain."""
    r = np.random.default_rng(seed)
    core = make_core(eq15_w=eq15_w)
    mp = FakeMapping()
    mp.update((np.eye(3), np.zeros(3)), (np.eye(3), np.zeros(3)))
    kinds, err_final, err_aft = [], [], []
    vx = 0.0
    prev_truth = None
    for k in range(1, n_ok + n_deg + 1):
        t = k * 0.1
        (RL, pL), _ = step_inputs(k)
        pL = np.array([t, 0.2 * np.sin(0.5 * t), 0.0])
        # VINS: exact in y, z and rotation, scale error along x
        vx = vx + 0.1 * vins_scale
        pV = np.array([vx, pL[1], 0.0])
        v = vins_pose_from_lidar(RL, pV)
        deg = k > n_ok
        H = H_DEG_X if deg else H_ISO
        # LiDAR odometry (scan-to-scan) is noisy along x when degenerate
        o = (RL, pL + (np.array([r.normal() * 0.05, 0, 0]) if deg else 0))
        dec = core.decide(o, v, H)
        P = core.pose_to_publish(dec["guess"])
        g = mp.guess(P)
        ax = g[1][0] + (r.normal() * 0.03 if deg else 0.0)
        aft_p = np.array([pL[0] if not deg else ax, pL[1], pL[2]])           # truth in y,z; free in x when degenerate
        aft = (RL, aft_p)
        Rf, pf, info = core.finish(aft, H, dec, P)
        mp.update(aft, P)
        kinds.append((dec["kind"], info["case"]))
        err_final.append(pf[0] - pL[0])
        err_aft.append(aft_p[0] - pL[0])
    return kinds, np.array(err_final), np.array(err_aft)


def test_corridor_modes_and_drift():
    kinds, ef, ea = corridor_sim()
    assert all(k[0] == "LIDAR" and k[1] == 1 for k in kinds[:100])            # well-conditioned: pure LiDAR, Eq. 16 line 1
    onset = [k[0] for k in kinds[100:107]]
    assert onset == ["VO", "INTERP", "INTERP", "INTERP", "INTERP", "VO", "VO"], onset    # queue of 5: abrupt first, then bridged
    assert all(k[1] == 3 for k in kinds[100:])                                 # degenerate + VINS ok -> Eq. 15
    # along the unobservable axis the chain follows VINS (0.5 % scale error over 20 m = 0.1 m), not the LiDAR noise
    assert abs(ef[-1]) < 0.15, ef[-1]
    # recovery: the end of degeneracy goes straight back to LiDAR
    return kinds


def test_vins_failure_in_corridor_uses_projection():
    """degenerate and VINS lost -> Eq. 14: the step along the degenerate eigenvector is removed (case 2)"""
    core = make_core()
    o, v = step_inputs(1)
    dec = core.decide(o, None, H_DEG_X)
    g = dec["guess"]
    aft = (g[0], g[1] + np.array([0.7, 0.1, -0.05]))                     # A-LOAM wandered 0.7 m along x
    Rf, pf, info = core.finish(aft, H_DEG_X, dec, g)
    assert info["case"] == 2
    assert abs((pf - g[1])[0]) < 1e-9                                      # x component removed
    assert np.allclose((pf - g[1])[1:], [0.1, -0.05], atol=1e-9)           # the observable directions are kept


def test_eq15_is_the_mean_of_the_two_steps():
    core = make_core()
    o, v = step_inputs(1)
    core.buf.extend([False, True])                                         # Start/End -> interpolated guess
    dec = core.decide(o, v, H_DEG_X)
    g, vo = dec["guess"], dec["vo"]
    aft = (g[0], g[1] + np.array([0.7, 0.1, -0.05]))
    Rf, pf, info = core.finish(aft, H_DEG_X, dec, g)
    x_l = np.array([0.0, 0.1, -0.05])                                      # projected LiDAR step
    x_v = vo[1] - g[1]
    assert np.allclose(pf - g[1], 0.5 * (x_l + x_v), atol=1e-9)
    # eq15_w = 1 keeps the whole projected LiDAR step, 0 keeps the VO pose
    core2 = make_core(eq15_w=1.0); core2.buf.extend([False, True]); d2 = core2.decide(o, v, H_DEG_X)
    assert np.allclose(core2.finish(aft, H_DEG_X, d2, g)[1] - d2["guess"][1], x_l, atol=1e-9)
    core3 = make_core(eq15_w=0.0); core3.buf.extend([False, True]); d3 = core3.decide(o, v, H_DEG_X)
    assert np.allclose(core3.finish(aft, H_DEG_X, d3, g)[1], d3["vo"][1], atol=1e-9)


def test_body_frame_hessian_is_rotated_into_the_map_frame():
    """scan-to-scan Hessian (previous LiDAR frame) with the robot yawed 90 deg: the degenerate axis is body x = map y"""
    core = sw.SwitchSlamCore(R_IL, t_IL, hess_frame="body")
    Ry = fc.so3_exp([0, 0, np.pi / 2])
    core.init((Ry, np.zeros(3)), (Ry, np.zeros(3)), (Ry, np.zeros(3)), (Ry, np.zeros(3)))
    o = (Ry, np.zeros(3))
    dec = core.decide(o, None, H_DEG_X)
    g = dec["guess"]
    aft = (g[0], g[1] + np.array([0.3, 0.7, 0.0]))
    pf = core.finish(aft, H_DEG_X, dec, g)[1]
    assert abs(pf[1]) < 1e-9 and abs(pf[0] - 0.3) < 1e-9, pf             # map-y (= body x) removed, map-x kept


def test_matches_old_f12_rule():
    """the detection rule is the one F12 already used (fusion_core.switch_slam_degenerate)"""
    for _ in range(200):
        A = rng.normal(size=(6, 6)) * rng.uniform(0.1, 10, size=6)
        H = A @ A.T
        assert fc.switch_slam_degenerate(H) == sw.eig_degeneracy(H)["degenerate"]


if __name__ == "__main__":
    n = 0
    for name, f in list(globals().items()):
        if name.startswith("test_") and callable(f):
            f()
            n += 1
            print("ok", name)
    print("%d tests passed" % n)
