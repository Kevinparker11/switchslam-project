"""Unit test for FusionCore(handover=...) (run: python3 test_handover.py). Synthetic data: a VINS rotation that lags
the true rotation by a few degrees exactly at the warm-up -> FUSED switch and catches up one scan later (the transient seen in
the Long Corridor F20 runs).  'none' keeps that error in the heading for good; 'anchor' must not."""
import numpy as np
import fusion_core as fc

R_IL = fc.so3_exp([0.01, -0.02, 0.03]); t_IL = np.array([0.08, 0.03, 0.03])
T_LI_R = R_IL


def run(handover, lag_deg=5.0, n=500, dt=0.1, t_warm=20.0):
    core = fc.FusionCore(R_IL, t_IL, c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=t_warm, handover=handover)
    H = np.diag([50, 50, 50, 500, 500, 500.0])
    R_off_true = fc.so3_exp([0.02, -0.01, 1.2])          # VINS world -> map: arbitrary fixed rotation
    k_switch = int(round(t_warm / dt)) + 1               # first FUSED scan (VINS starts at scan 1)
    yaw_err = []
    for k in range(n):
        t = k * dt
        yaw = 0.4 * np.sin(0.15 * t) + 0.02 * t
        RL = fc.so3_exp([0.0, 0.0, yaw]); pL = np.array([np.cos(0.05 * t), np.sin(0.05 * t), 0.0]) * 10
        RLv = R_off_true.T @ RL                          # LiDAR orientation in the VINS world
        if k == k_switch - 1:                            # VINS lags by lag_deg at the scan before the switch
            RLv = RLv @ fc.so3_exp([0, 0, np.radians(lag_deg)])
        Rv = RLv @ R_IL.T                                # IMU orientation in the VINS world
        pv = R_off_true.T @ pL + Rv @ (-R_IL @ np.zeros(3))
        # IMU position consistent with the LiDAR position: p_L = p_I + R_I t_IL  ->  p_I = p_L - R_I t_IL (in VINS world)
        pv = R_off_true.T @ pL - Rv @ t_IL
        vins = (Rv, pv) if k >= 1 else None
        Rf, pf, info = core.step(t, (RL, pL), vins, H)
        if k > k_switch + 5:
            yaw_err.append(np.degrees(np.linalg.norm(fc.so3_log(RL.T @ Rf))))
    return float(np.mean(yaw_err)), info


e_none, _ = run("none")
e_anchor, _ = run("anchor")
e_none0, _ = run("none", lag_deg=0.0)
e_anchor0, _ = run("anchor", lag_deg=0.0)
print("mean heading error after the switch: none %.3f deg, anchor %.3f deg (no transient: %.4f / %.4f)" % (e_none, e_anchor, e_none0, e_anchor0))
assert e_none > 3.0, "the synthetic transient should leave an offset with the old handover"
assert e_anchor < 0.2, "the anchored handover must remove the transient"
assert e_none0 < 0.05 and e_anchor0 < 0.05, "without a transient both handovers are exact"
# robust mean ignores a few outliers
Rs = [fc.so3_exp([0, 0, 0.3 + 0.002 * np.sin(i)]) for i in range(100)] + [fc.so3_exp([0, 0, 0.5])] * 5
M = fc.robust_rotation_mean(Rs)
assert abs(fc.so3_log(M)[2] - 0.3) < 0.002, fc.so3_log(M)
print("robust mean ok:", fc.so3_log(M).round(4))
print("ALL HANDOVER TESTS PASSED")
