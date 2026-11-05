"""F26 guess rule (run: python3 test_guess_status.py): Switch-SLAM's status picks LiDAR / interpolation / VIO for the scan-to-map guess."""
import numpy as np
import fusion_core as fc
import guess_status as gs

R_IL = np.eye(3); t_IL = np.zeros(3)
H_ok = np.diag([800, 900, 1000, 700, 800, 900.0])                 # well conditioned (all three smallest eigenvalues similar)
H_bad = np.diag([1e4, 1e4, 1e4, 1e4, 1e4, 1.0])                   # one direction nearly unobservable -> lambda_bar_1 ~ 0


def make():
    core = fc.FusionCore(R_IL, t_IL, c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=1e12)
    core.Rf, core.pf = np.eye(3), np.zeros(3)
    return core, gs.StatusGuess(R_IL, t_IL)


def run(H, vins_step, odom_step, n=8):
    core, sg = make()
    odom = (np.eye(3), np.zeros(3)); vins = (np.eye(3), np.zeros(3))
    out = None
    for k in range(n):
        odom = (np.eye(3), odom[1] + np.array([odom_step, 0, 0]))
        vins = None if vins_step is None else (np.eye(3), (vins[1] if vins is not None else np.zeros(3)) + np.array([vins_step, 0, 0]))
        R, p = sg.guess(core, odom, vins, H)
        core.Rf, core.pf = R, p                                   # the fused pose follows the guess in this toy
        out = (p, sg.kind)
    return out


p, kind = run(H_ok, vins_step=0.30, odom_step=0.10)
print("not degenerate:", kind, "last guess x", round(float(p[0]), 3))
assert kind == "LIDAR" and abs(p[0] - 7 * 0.10) < 1e-9, "non-degenerate: A-LOAM's own increment"
p, kind = run(H_bad, vins_step=0.30, odom_step=0.10)
print("degenerate x8 :", kind, "last guess x", round(float(p[0]), 3))
assert kind == "VO" and p[0] > 7 * 0.10 + 0.5, "fully degenerate queue: the VINS increment"
p, kind = run(H_bad, vins_step=None, odom_step=0.10)
print("degenerate, no VINS:", kind, "last guess x", round(float(p[0]), 3))
assert kind == "LIDAR" and abs(p[0] - 7 * 0.10) < 1e-9, "VINS absent: LiDAR increment"
p, kind = run(H_bad, vins_step=1.5, odom_step=0.10)
print("degenerate, VINS step 1.5 m (> jump_max):", kind, "last guess x", round(float(p[0]), 3))
assert kind == "LIDAR", "F24's guard: a VINS step above jump_max is treated as absent"
p, kind = run(None, vins_step=0.30, odom_step=0.10)
assert kind == "LIDAR", "no Hessian: LiDAR"

# F27: A-LOAM's own increment replaces "no motion" only when the VINS motion was not usable
core = fc.FusionCore(R_IL, t_IL, c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=1e12, predict_guard=True)
core.Rf, core.pf = np.eye(3), np.zeros(3)
fb = gs.OdomFallback()
o0 = (np.eye(3), np.zeros(3)); o1 = (np.eye(3), np.array([0.2, 0, 0])); o2 = (np.eye(3), np.array([0.4, 0, 0]))
pred = core.predict(None); assert not core.guess_used_vins
assert np.allclose(fb.guess(core, pred, o0)[1], 0) and fb.kind == "INIT" or fb.kind in ("INIT", "VINS")   # first scan: nothing to difference
pred = core.predict(None)
R, p = fb.guess(core, pred, o1)
print("F27 VINS absent:", fb.kind, "guess x", round(float(p[0]), 3))
assert fb.kind == "ODOM" and abs(p[0] - 0.2) < 1e-9, "VINS unusable: the last fused pose plus A-LOAM's increment"
core.prev_v = (np.eye(3), np.zeros(3))
pred = core.predict((np.eye(3), np.array([0.05, 0, 0]))); assert core.guess_used_vins
R, p = fb.guess(core, pred, o2)
print("F27 VINS usable:", fb.kind, "guess x", round(float(p[0]), 3))
assert fb.kind == "VINS" and abs(p[0] - 0.05) < 1e-9, "VINS usable: F24 exactly"
pred = core.predict((np.eye(3), np.array([1.5, 0, 0])))        # step above jump_max: guard blocks it
assert not core.guess_used_vins
R, p = fb.guess(core, pred, (np.eye(3), np.array([0.6, 0, 0])))
assert fb.kind == "ODOM" and abs(p[0] - 0.2) < 1e-9
R, p = fb.guess(core, core.predict(None), (np.eye(3), np.array([10.0, 0, 0])))
assert fb.kind == "HOLD" and np.allclose(p, core.pf), "odometry blow-up: no motion"
print("ALL GUESS_STATUS TESTS PASSED")
