"""Unit tests for fusion_core (run: python3 test_fusion_core.py). Synthetic data only: they check the
geometry and the logic, not accuracy on real data."""
import numpy as np
import fusion_core as fc

rng = np.random.default_rng(0)


def rand_R():
    return fc.so3_exp(rng.normal(size=3) * 2)


def trajectory(n=400, dt=0.1):
    """smooth 3-D LiDAR-body trajectory (R_k, p_k)"""
    t = np.arange(n) * dt
    Rs, ps = [], []
    for tk in t:
        yaw, pitch, roll = 0.3 * np.sin(0.07 * tk) + 0.05 * tk, 0.05 * np.sin(0.3 * tk), 0.03 * np.cos(0.2 * tk)
        R = fc.so3_exp([0, 0, yaw]) @ fc.so3_exp([0, pitch, 0]) @ fc.so3_exp([roll, 0, 0])
        Rs.append(R)
        ps.append(np.array([np.cos(0.05 * tk) * 20, np.sin(0.05 * tk) * 15, 0.5 * np.sin(0.1 * tk)]))
    return t, Rs, ps


def to_frame(Rs, ps, Rw, tw):
    return [Rw @ R for R in Rs], [Rw @ p + tw for p in ps]


def lidar_to_imu_poses(Rs, ps, R_IL, t_IL):
    """IMU pose from LiDAR pose: T_W_I = T_W_L * T_IL^-1"""
    Rli, tli = R_IL.T, -R_IL.T @ t_IL
    return [R @ Rli for R in Rs], [p + R @ tli for R, p in zip(Rs, ps)]


def spd(scale_rot=5000.0, scale_t=300.0, weak=None):
    A = rng.normal(size=(6, 6))
    H = A @ A.T + np.diag([scale_rot] * 3 + [scale_t] * 3)
    if weak is not None:       # make one translation direction (body) weak
        H[3 + weak, :] *= 1e-3
        H[:, 3 + weak] *= 1e-3
    return H


def max_err(Rs, ps, Rf, pf):
    return max(np.linalg.norm(a - b) for a, b in zip(ps, pf)), max(np.linalg.norm(fc.so3_log(a.T @ b)) for a, b in zip(Rs, Rf))


def run(core, t, aft_R, aft_p, vins_R, vins_p, H=None, vins_from=0):
    Rf, pf = [], []
    for k in range(len(t)):
        v = (vins_R[k], vins_p[k]) if k >= vins_from else None
        R, p, _ = core.step(t[k], (aft_R[k], aft_p[k]), v, H if H is not None else spd())
        Rf.append(R)
        pf.append(p)
    return Rf, pf


def test_so3():
    for _ in range(200):
        w = rng.normal(size=3) * rng.uniform(0, 3)
        assert np.allclose(fc.so3_log(fc.so3_exp(w)), w, atol=1e-8) or np.linalg.norm(w) > np.pi
        R = rand_R()
        assert np.allclose(fc.quat_to_R(fc.R_to_quat(R)), R, atol=1e-9)
    print("so3/quat ok")


def test_extrinsic_increment():
    R_IL, t_IL = fc.so3_exp([0.01, -0.02, 0.005]), np.array([0.08, 0.029, 0.03])
    t, Rs, ps = trajectory(50)
    RI, pI = lidar_to_imu_poses(Rs, ps, R_IL, t_IL)
    for k in range(1, 50):
        dRL, dtL = fc.rel_body(Rs[k - 1], ps[k - 1], Rs[k], ps[k])
        dRI, dtI = fc.rel_body(RI[k - 1], pI[k - 1], RI[k], pI[k])
        dR2, dt2 = fc.imu_to_lidar_increment(dRI, dtI, R_IL, t_IL)
        assert np.allclose(dR2, dRL, atol=1e-10) and np.allclose(dt2, dtL, atol=1e-10)
    print("extrinsic increment ok")


def test_frames_never_mix():
    """aft in one world frame, VINS (IMU poses) in another rotated by 60 deg: with perfect inputs the
    fused trajectory must equal the truth expressed in the aft frame, for any weights."""
    R_IL, t_IL = fc.so3_exp([0.01, -0.02, 0.005]), np.array([0.08, 0.029, 0.03])
    t, Rs, ps = trajectory()
    Ra, pa = to_frame(Rs, ps, fc.so3_exp([0, 0.1, 1.05]), np.array([3, -2, 1]))
    Rv0, pv0 = to_frame(Rs, ps, fc.so3_exp([0.2, -0.1, -0.4]), np.array([-5, 7, 0.3]))
    Rv, pv = lidar_to_imu_poses(Rv0, pv0, R_IL, t_IL)
    for c_t, c_R in [(0, 0), (1e-3, 0), (1e-2, 1e-4), (1e6, 1e6)]:
        core = fc.FusionCore(R_IL, t_IL, c_t=c_t, c_R=c_R, gate=fc.KappaGate(1e9), t_warm=5.0)
        Rf, pf = run(core, t, Ra, pa, Rv, pv, vins_from=20)
        e = max_err(Ra, pa, Rf, pf)
        assert e[0] < 1e-6 and e[1] < 1e-8, (c_t, c_R, e)
    print("frame-consistent fusion ok (60 deg world-frame offset, extrinsic, warm-up)")


def test_weights_follow_information():
    """LiDAR translation is wrong only along a direction the Hessian says is weak; VINS is noisy.
    The fused trajectory must ignore LiDAR along the weak direction and use it elsewhere."""
    t, Rs, ps = trajectory()
    noise_v = [np.zeros(3)]
    for k in range(1, len(t)):
        noise_v.append(noise_v[-1] + rng.normal(scale=0.01, size=3))   # VINS random-walk error
    pv = [p + n for p, n in zip(ps, noise_v)]
    # LiDAR error grows only along body-x (index 0); tell the Hessian that body-x is weak
    pa, acc = [], np.zeros(3)
    for k in range(len(t)):
        if k:
            acc = acc + Rs[k - 1] @ np.array([0.05, 0, 0])
        pa.append(ps[k] + acc)
    H = np.diag([20000.0, 20000, 20000, 1e-3, 3e5, 3e5])
    core = fc.FusionCore(c_t=1e-3, c_R=0, gate=fc.KappaGate(1e9), t_warm=0.0, hess_frame="body")
    Rf, pf = run(core, t, Rs, pa, Rs, pv, H=H)
    e_f = max(np.linalg.norm(a - b) for a, b in zip(ps, pf))
    e_v = max(np.linalg.norm(a - b) for a, b in zip(ps, pv))
    e_a = max(np.linalg.norm(a - b) for a, b in zip(ps, pa))
    assert e_f < 0.8 * e_v and e_f < 0.05 * e_a, (e_f, e_v, e_a)
    print("directional weights ok: fused max err %.3f vs VINS %.3f vs LiDAR %.3f m" % (e_f, e_v, e_a))


def test_gate_and_failure():
    t, Rs, ps = trajectory(100)
    pa = [p + np.array([0.0, 0.0, 0.01 * k]) for k, p in enumerate(ps)]    # LiDAR drifts in z
    H = spd()
    core = fc.FusionCore(c_t=1.0, gate=fc.KappaGate(kth=0.5), t_warm=0.0, hess_frame="body")   # gate always closed
    Rf, pf = run(core, t, Rs, pa, Rs, ps, H=H)
    assert max(np.linalg.norm(a - b) for a, b in zip(ps, pf)) < 1e-9
    # VINS jump of 5 m at k=50 must be rejected (LiDAR used for that step)
    pv = [p + (np.array([5.0, 0, 0]) if k >= 50 else 0) for k, p in enumerate(ps)]
    core = fc.FusionCore(c_t=0.0, gate=fc.KappaGate(kth=1e9), t_warm=0.0, hess_frame="body")
    Rf, pf, modes = [], [], []
    for k in range(100):
        R, p, info = core.step(t[k], (Rs[k], ps[k]), (Rs[k], pv[k]), H)
        Rf.append(R); pf.append(p); modes.append(info["mode"])
    assert modes[50] == "VO_FAIL" and max(np.linalg.norm(a - b) for a, b in zip(ps, pf)) < 1e-9
    print("gate closed -> VINS only; VINS jump rejected ok")


def test_vins_loss_and_reinit():
    """VINS disappears for 0.6 s then comes back re-initialised in a NEW world frame: LiDAR must carry
    the gap and a fresh warm-up; the fused trajectory must stay exact with perfect inputs."""
    t, Rs, ps = trajectory(200)
    Rv1, pv1 = to_frame(Rs, ps, fc.so3_exp([0.0, 0.0, 0.7]), np.array([1.0, 2.0, 0.0]))
    Rv2, pv2 = to_frame(Rs, ps, fc.so3_exp([0.3, 0.0, -1.2]), np.array([-4.0, 0.0, 2.0]))
    core = fc.FusionCore(c_t=1e-3, gate=fc.KappaGate(1e9), t_warm=2.0, hess_frame="body")
    modes, pf = [], []
    for k in range(200):
        v = None if 100 <= k < 106 else ((Rv1[k], pv1[k]) if k < 100 else (Rv2[k], pv2[k]))
        R, p, info = core.step(t[k], (Rs[k], ps[k]), v, spd())
        modes.append(info["mode"]); pf.append(p)
    assert max(np.linalg.norm(a - b) for a, b in zip(ps, pf)) < 1e-6
    assert modes[100] == "VO_FAIL" and all(m == "WARMUP" for m in modes[101:126]) and modes[127] == "FUSED", modes[98:130]
    print("VINS loss + re-initialisation in a new frame ok (LiDAR bridges, warm-up restarts)")


def test_otsu():
    x = np.concatenate([rng.normal(0.8, 0.1, 3000), rng.normal(1.6, 0.1, 1000)])
    cut = fc.otsu_threshold(x)
    assert 1.0 < cut < 1.4, cut
    g = fc.KappaGate(kth=15.7, mode="otsu", min_samples=300, every=50)
    for v in 10 ** x[rng.permutation(len(x))][:1200]:
        g(v)
    assert 8 < g.kth < 30, g.kth
    print("otsu ok: cut %.2f (log10), online kth %.1f" % (cut, g.kth))




def test_weight_modes():
    """ablation variants: shapes, ranges and limiting cases"""
    H = np.diag([50.0, 60.0, 70.0, 400.0, 30.0, 200.0])
    H[0, 4] = H[4, 0] = 20.0
    S_RR, S_tt, kR, kt = fc.schur_blocks(H, "body")
    for m in fc.W_MODES:
        W = fc.translation_weight(m, H, S_tt, S_RR, 0.03, kR)
        assert W.shape == (3, 3) and np.allclose(W, W.T)
        ev = np.linalg.eigvalsh(W)
        assert ev.min() >= -1e-12 and ev.max() <= 1 + 1e-12, m
    assert np.allclose(fc.translation_weight("schur", H, S_tt, S_RR, 0.03, kR), fc.info_weight(S_tt, 0.03))
    # coupling makes the Schur weight smaller than the diagonal-block weight along the coupled axis
    Wd = fc.translation_weight("diag", H, S_tt, S_RR, 0.03, kR)
    Ws = fc.translation_weight("schur", H, S_tt, S_RR, 0.03, kR)
    assert Ws[1, 1] < Wd[1, 1]
    # proj keeps the strong directions only
    Wp = fc.translation_weight("proj", H, S_tt, S_RR, 0.03, kR)
    assert set(np.round(np.linalg.eigvalsh(Wp), 6)) <= {0.0, 1.0}
    # Switch-SLAM rule: a perfectly isotropic Hessian is not degenerate, a rank-deficient one is
    assert not fc.switch_slam_degenerate(np.eye(6) * 100)
    assert fc.switch_slam_degenerate(np.diag([100, 100, 100, 100, 100, 1e-6]))
    # the default (schur) path of FusionCore is unchanged by the new arguments
    core = fc.FusionCore(c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=0.0, hess_frame="body")
    assert core.w_mode == "schur"


def _straight_run(scale_v, n=400, dt=0.1, v=1.0, adapt=None, vio_scale_T=0.0):
    """walk along x at v m/s; VINS reports scale_v times the true motion; LiDAR is exact and well constrained"""
    core = fc.FusionCore(c_t=1.0, c_R=1.0, gate=fc.KappaGate(kth=1e9), t_warm=2.0, hess_frame="body",
                         vio_adapt=adapt, vio_scale_T=vio_scale_T)
    H = np.eye(6)
    for k in range(n):
        p = np.array([v * dt * k, 0.0, 0.0])
        R, pf, info = core.step(k * dt, (np.eye(3), p), (np.eye(3), scale_v * p), H)
    return pf, info, p


def test_vio_consistency():
    S = np.diag([4.0, 1.0, 0.25])
    # gamma = 1 is the original weight, gamma = 0 trusts the LiDAR fully
    lam = np.diag(S)
    assert np.allclose(fc.info_weight(S, 0.5), np.diag(0.5 * lam / (0.5 * lam + 1)))
    assert np.allclose(fc.info_weight(S, 0.5, 1.0), fc.info_weight(S, 0.5))
    assert np.allclose(fc.info_weight(S, 0.5, 0.0), np.eye(3))
    # consistent VINS: the gate opens after n_min windows and the result equals the original rule
    chk = fc.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=20)
    pf, info, p = _straight_run(1.0, adapt=chk)
    assert info["gamma"] == 1.0 and np.allclose(pf, p)
    # VINS 1.5x too fast: without the check the fused path is too long, with it the LiDAR carries the steps
    pf0, _, p = _straight_run(1.5)
    assert pf0[0] > p[0] + 5.0
    chk = fc.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=20)
    pf1, info, p = _straight_run(1.5, adapt=chk)
    assert info["gamma"] == 0.0 and abs(pf1[0] - p[0]) < 1e-6
    # online scale correction removes a constant VINS scale error after the first window
    pf2, info, p = _straight_run(1.5, vio_scale_T=2.0)
    assert abs(info["s_vio"] - 1 / 1.5) < 1e-6 and abs(pf2[0] - p[0]) < 1.0
    # a VINS loss resets the check
    chk.update(0.0, (np.eye(3), np.zeros(3)), (np.eye(3), np.zeros(3)), np.eye(3), np.zeros(3))
    chk.reset()
    assert chk.gamma() == 0.0 and not chk.rw


def _guard_run(blowup, guard_T=0.0, fast=False, n=600, dt=0.1, v=1.0):
    """walk along x at v m/s; the VINS is exact; from t = 40 s the LiDAR runs away (each step `blowup` times too long)
    while its Hessian still looks healthy -- the GenZ-LIO divergence seen in Multi Floor run 2."""
    slow = fc.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=20)
    chk = fc.VioChecks([slow, fc.VioConsistency(ref=0.278, stat="scale", rule="gate", avg=5.0, n_min=25)]) if fast else slow
    core = fc.FusionCore(c_t=1.0, c_R=1.0, gate=fc.KappaGate(kth=1e9), t_warm=2.0, hess_frame="body",
                         vio_adapt=chk, vio_scale_T=10.0, lidar_guard_T=guard_T, lidar_guard_ex=2.16)
    H = np.eye(6); pl = np.zeros(3); flagged = 0
    for k in range(n):
        p = np.array([v * dt * k, 0.0, 0.0])
        if k > 0:
            pl = pl + (blowup if k * dt >= 40.0 else 1.0) * np.array([v * dt, 0.0, 0.0])
        R, pf, info = core.step(k * dt, (np.eye(3), pl.copy()), (np.eye(3), p), H)
        flagged += info.get("lidar_bad", 0)
    return pf, p, flagged, info


def test_lidar_guard_and_fast_check():
    # without the guard the scale correction follows the runaway LiDAR (G19 on Multi Floor run 2)
    pf0, p, n0, _ = _guard_run(3.0)
    assert pf0[0] > p[0] + 20.0 and n0 == 0
    # with the guard the VINS carries the steps once the LiDAR outruns it; the error stays bounded
    pf1, p, n1, info = _guard_run(3.0, guard_T=2.0)
    assert n1 > 100 and abs(pf1[0] - p[0]) < 3.0
    # the fast check closing the gate (it sees the disagreement too) must not switch the guard off
    pf2, p, n2, info = _guard_run(3.0, guard_T=2.0, fast=True)
    assert n2 > 100 and abs(pf2[0] - p[0]) < 3.0
    # healthy LiDAR: the guard never fires and the result is identical to running without it
    pfa, p, na, _ = _guard_run(1.0, guard_T=2.0, fast=True)
    pfb, p, nb, _ = _guard_run(1.0, fast=True)
    assert na == 0 and np.allclose(pfa, pfb)
    # the fast check drops a VINS that goes wrong after it has earned trust
    slow = fc.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=20)
    two = fc.VioChecks([slow, fc.VioConsistency(ref=0.278, stat="scale", rule="gate", avg=5.0, n_min=25)])
    I3 = np.eye(3); z = np.zeros(3); g = []
    for k in range(700):
        t = 0.1 * k; pa = np.array([0.1 * k, 0, 0])
        pv = pa.copy() if t < 40 else np.array([4.0 + 2.0 * 0.1 * (k - 400), 0, 0])   # VINS twice too fast after 40 s
        two.update(t, (I3, pa), (I3, pv), I3, z); g.append((t, two.gamma(), slow.gamma()))
    g = np.array(g)
    assert g[(g[:, 0] > 30) & (g[:, 0] < 40), 1].min() == 1.0          # trusted while consistent
    t_fast = g[(g[:, 0] >= 40) & (g[:, 1] == 0.0), 0].min()
    t_slow = g[(g[:, 0] >= 40) & (g[:, 2] == 0.0), 0].min()
    assert t_fast < 41.5 and t_fast < t_slow                            # the fast check reacts first


def test_gamma_floor():
    # a LiDAR direction with almost no information must go to the VINS even when the gate is closed (gamma = 0)
    S = np.diag([1e6, 1e6, 1e-3]); c = 3e-6          # c*lambda: 3, 3, 3e-9
    W0 = fc.info_weight(S, c, 0.0); Wf = fc.info_weight(S, c, 1e-3)
    assert np.allclose(np.diag(W0), [1, 1, 1])                       # no floor: the degenerate axis is trusted fully
    assert Wf[2, 2] < 1e-5 and Wf[0, 0] > 0.999                      # floor: degenerate axis -> VINS, others unchanged


if __name__ == "__main__":
    test_so3()
    test_extrinsic_increment()
    test_frames_never_mix()
    test_weights_follow_information()
    test_gate_and_failure()
    test_vins_loss_and_reinit()
    test_otsu()
    test_weight_modes()
    test_vio_consistency()
    test_lidar_guard_and_fast_check()
    test_gamma_floor()
    print("ALL TESTS PASSED")


def _gap_run(gap_T, teleport=300.0, vins_after=True, n=800, dt=0.1, v=1.0, k0=200, k1=500):
    """walk along x at v m/s with an exact VINS; the LiDAR delivers no scan for k0 <= k < k1 (30 s) and re-enters with a pose that
    is `teleport` m wrong (dead reckoning through the gap), then tracks the motion correctly again."""
    slow = fc.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=20)
    chk = fc.VioChecks([slow, fc.VioConsistency(ref=0.278, stat="scale", rule="gate", avg=5.0, n_min=25)])
    core = fc.FusionCore(c_t=1.0, c_R=1.0, gate=fc.KappaGate(kth=1e9), t_warm=2.0, hess_frame="body", vio_adapt=chk,
                         vio_scale_T=10.0, lidar_guard_T=2.0, lidar_guard_ex=2.16, gap_T=gap_T)
    H = np.eye(6); modes = []; pf = None
    for k in range(n):
        if k0 <= k < k1:
            continue
        x = v * dt * k
        pl = np.array([x + (teleport if k >= k1 else 0.0), 0.0, 0.0])
        vin = (np.eye(3), np.array([x, 0.0, 0.0])) if (vins_after or not (k == k1)) else None
        R, pf, info = core.step(k * dt, (np.eye(3), pl), vin, H)
        modes.append(info["mode"])
    return pf, v * dt * (n - 1), modes


def test_gap_rule():
    # off (default): the VIO displacement over the gap looks like a VINS jump, the LiDAR carries the step and the teleport is adopted
    pf0, x, m0 = _gap_run(0.0)
    assert pf0[0] > x + 250.0 and "GAP" not in m0
    # on: the VIO carries the step over the gap and the fused pose stays on the true path
    pf1, x, m1 = _gap_run(1.0)
    assert abs(pf1[0] - x) < 3.0 and m1.count("GAP") == 1
    # neither sensor usable over the gap (VINS missing at the first scan): the pose is held, the teleport is not adopted
    pf2, x, m2 = _gap_run(1.0, vins_after=False)
    assert m2.count("GAP_HOLD") == 1 and x - 40.0 < pf2[0] < x + 1.0
    # no gap in the data: identical to the rule being off, step for step
    for kw in (dict(teleport=0.0, k0=0, k1=0), dict(teleport=0.0, k0=10**6, k1=10**6)):
        pa, _, _ = _gap_run(1.0, **kw)
        pb, _, _ = _gap_run(0.0, **kw)
        assert np.array_equal(pa, pb)
