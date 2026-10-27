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


if __name__ == "__main__":
    test_so3()
    test_extrinsic_increment()
    test_frames_never_mix()
    test_weights_follow_information()
    test_gate_and_failure()
    test_vins_loss_and_reinit()
    test_otsu()
    print("ALL TESTS PASSED")
