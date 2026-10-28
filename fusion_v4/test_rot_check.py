"""Unit tests for design B (RotConsistency / rot_adapt in FusionCore).  Synthetic data only: they test the logic.
run: python3 test_rot_check.py"""
import numpy as np
import fusion_core as fc

rng = np.random.default_rng(1)
DT, N = 0.1, 400
t = np.arange(N) * DT
R_IL, t_IL = np.eye(3), np.zeros(3)
H = np.diag([20000.0, 20000, 20000, 3e5, 3e5, 3e5])
REF2, REF10 = 0.34, 0.57


def truth(rate=0.5):
    Rs = [fc.so3_exp([0, 0, rate * tk]) for tk in t]
    ps = [np.array([0.5 * tk, 0.0, 0.0]) for tk in t]
    return Rs, ps


def core(adapt, c_R=0.0, guard=0.0):
    ra = fc.RotConsistency(REF2, REF10, guard=guard) if adapt else None
    return fc.FusionCore(R_IL, t_IL, c_t=0.03, c_R=c_R, gate=fc.KappaGate(1e9), t_warm=2.0, hess_frame="body", rot_adapt=ra)


def run(c, Ra, pa, Rv, pv):
    out = []
    for k in range(N):
        R, p, info = c.step(t[k], (Ra[k], pa[k]), (Rv[k], pv[k]), H)
        out.append((R, p, info))
    return out


def rot_err(out, Rs, k):
    return float(np.linalg.norm(fc.so3_log(Rs[k].T @ out[k][0])))


def test_healthy_equals_f16():
    """small rotation noise on both sources, c_R = 0: with the check the output equals F16 bit for bit and the check never closes"""
    Rs, ps = truth()
    Ra = [R @ fc.so3_exp(rng.normal(scale=0.002, size=3)) for R in Rs]
    Rv = [R @ fc.so3_exp(rng.normal(scale=0.002, size=3)) for R in Rs]
    o0 = run(core(False), Ra, ps, Rv, ps)
    o1 = run(core(True), Ra, ps, Rv, ps)
    assert all(np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) for a, b in zip(o0, o1))
    assert all(i[2].get("rot_gamma", 1.0) == 1.0 for i in o1)
    print("healthy data: design B == F16 bit for bit, check never closed")


def test_vins_rotation_failure():
    """from k0 for 6 s the VINS rotation freezes while the robot keeps turning at 0.5 rad/s (2 s = 1 rad > ref): F16 follows the
    VINS error (3 rad at the end of the failure), design B hands the rotation to the LiDAR once the 2 s window exceeds the reference"""
    Rs, ps = truth()
    k0, k1 = 150, 210
    Rv, off = [], None
    for k in range(N):
        if k < k0:
            Rv.append(Rs[k])
        elif k < k1:
            Rv.append(Rs[k0])
        else:
            Rv.append(Rs[k0] @ (Rs[k1].T @ Rs[k]))        # rotation increments resume, the offset stays
    o0 = run(core(False), Rs, ps, Rv, ps)
    o1 = run(core(True), Rs, ps, Rv, ps)
    e0, e1 = rot_err(o0, Rs, k1 - 1), rot_err(o1, Rs, k1 - 1)
    assert e0 > 2.5 and e1 < 0.45 and e1 < 0.2 * e0, (e0, e1)
    assert min(i[2]["rot_gamma"] for i in o1[k0:k1 + 25]) == 0.0
    print("VINS rotation failure: rotation error at the end of the failure F16 %.2f rad, design B %.2f rad" % (e0, e1))


def test_lidar_rotation_blowup_guard():
    """the LiDAR rotation jumps by 1.5 rad within 2 s while the VINS is right: with the guard the VIO carries the rotation after the guard angle is exceeded"""
    Rs, ps = truth(rate=0.1)
    k1 = 200
    Ra = [Rs[k] if k < k1 else Rs[k] @ fc.so3_exp([0, 0, min(1.5, 0.75 * (k - k1) * DT)]) for k in range(N)]
    o_ng = run(core(True, guard=0.0), Ra, ps, Rs, ps)
    o_g = run(core(True, guard=1.0), Ra, ps, Rs, ps)
    e_ng, e_g = rot_err(o_ng, Rs, N - 1), rot_err(o_g, Rs, N - 1)
    assert e_ng > 1.0 and e_g < 0.5 * e_ng, (e_ng, e_g)     # the guard trips once 1 rad has accrued, so some error remains
    print("LiDAR rotation blow-up: final rotation error without guard %.2f rad, with guard %.2f rad" % (e_ng, e_g))


def test_off_switch_and_gap_reset():
    c = fc.RotConsistency(REF2, REF10)
    c.update(0.0, np.eye(3), np.eye(3), np.eye(3))
    c.reset()
    assert c.gamma() == 1.0 and not np.isfinite(c.e_fast)
    print("reset ok")


if __name__ == "__main__":
    test_healthy_equals_f16()
    test_vins_rotation_failure()
    test_lidar_rotation_blowup_guard()
    test_off_switch_and_gap_reset()
    print("ALL ROT-CHECK TESTS PASSED")
