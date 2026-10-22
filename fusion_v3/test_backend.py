#!/usr/bin/env python3
"""Tests for the offline back end on a synthetic room + corridor (checks the code, not the method's
value on real data).  Needs numpy, scipy, gtsam (pip install gtsam).  Run: python3 test_backend.py"""
import time
import numpy as np

import fusion_core as fc
import backend_icp as bi
import backend_graph as bg
import backend_synth as bs

rng = np.random.default_rng(3)
t0 = time.time()
world = bs.make_world()
print("world points:", len(world))


def ate(P, G):
    R, t = bg._umeyama(P, G)
    e = np.linalg.norm(P @ R.T + t - G, axis=1)
    return float(np.sqrt(np.mean(e ** 2))), float(e.max())


# 1. ICP recovers a known offset in the room (well constrained)
T_true = bi.se3(fc.so3_exp([0, 0, 0.3]), [-6.0, -1.0, 1.0])
tgt = bi.voxel_down(bs.scan(world, T_true, rng), 0.1)
n, curv = bi.estimate_normals(tgt)
keep = curv < 0.08
src = bi.voxel_down(bs.scan(world, T_true, rng), 0.2)
pert = bi.se3(fc.so3_exp([0.0, 0.0, np.radians(4)]), [0.3, -0.2, 0.05])
T, H, st = bi.icp_p2pl(src, tgt[keep], n[keep], pert)
err = bi.se3_log_small(T)
assert st["ok"] and np.linalg.norm(err[3:]) < 0.03 and np.degrees(np.linalg.norm(err[:3])) < 0.3, (err, st)
s = bi.schur_rad(H)
print("1. room ICP ok: residual %.3f m / %.3f deg, kappa_t %.1f, fitness %.2f" % (
    np.linalg.norm(err[3:]), np.degrees(np.linalg.norm(err[:3])), s["kappa_t"], st["fitness"]))

# 2. In the middle of the corridor the translation Schur block is degenerate along the corridor axis
T_c = bi.se3(np.eye(3), [30.0, 0.0, 1.0])
tgt = bi.voxel_down(bs.scan(world, T_c, rng), 0.1)
n, curv = bi.estimate_normals(tgt)
keep = curv < 0.08
src = bi.voxel_down(bs.scan(world, T_c, rng), 0.2)
pert = bi.se3(fc.so3_exp([0, 0, np.radians(2)]), [1.5, 0.15, 0.0])        # 1.5 m along the axis
T, H, st = bi.icp_p2pl(src, tgt[keep], n[keep], pert)
s = bi.schur_rad(H)
axis = s["Vt"][:, 0]
err = bi.se3_log_small(T)
assert abs(axis[0]) > 0.95 and s["kappa_t"] > 100, (axis, s["kappa_t"])
assert abs(err[4]) < 0.03 and abs(err[0 + 2]) < np.radians(0.3), err         # lateral + yaw recovered
assert abs(err[3] - 1.5) < 0.2, err                                            # along-axis left where it was
Lam_s, info = bi.loop_information(H, st, "schur")
Lam_h, _ = bi.loop_information(H, st, "hessian")
e_ax = np.r_[0, 0, 0, axis]
print("2. corridor ok: weakest translation direction %s, kappa_t %.0f; along-axis offset kept at %.2f m; "
      "information along the axis: hessian %.3g, schur %.3g, iso %.3g" % (
          np.round(axis, 3), s["kappa_t"], err[3], e_ax @ Lam_h @ e_ax, e_ax @ Lam_s @ e_ax,
          1 / max(st["msd"], 1e-4)))
assert info["dropped_t"] >= 1 and e_ax @ Lam_s @ e_ax < 1e-3

# 3. Whole pipeline: room -> corridor -> back -> room, drifting odometry; compare loop models
wp = [(-9, 0), (-2, 0), (52, 0), (-2, 0.3), (-9, -2.5), (-9, 0.5)]
T_gt = bs.path(wp, step=1.0)
T_fe = bs.drifted(T_gt, rng, drift_world=(0.015, 0.0, 0.004), yaw_bias_deg=0.02)
clouds = [bi.voxel_down(bs.scan(world, T, rng), 0.2) for T in T_gt]
kf_t = np.arange(len(T_gt)) * 1.0                       # 1 m/s, keyframe every metre
G = np.array([T[:3, 3] for T in T_gt])
sig = np.r_[[np.radians(0.1)] * 3, [0.02] * 3]
res = {}
closer = bg.LoopCloser(clouds, min_gap_s=20.0, r_xy=6.0)
for model in bg.MODELS:
    T_opt, loops = bg.run_backend(kf_t, clouds, T_fe, sig, model, closer=closer)
    P = np.array([T[:3, 3] for T in T_opt])
    res[model] = ate(P, G)
    dropped = sum(L["info"]["dropped_t"] > 0 for L in loops)
    print("3. %-11s loops %3d (translation direction dropped in %3d)  ATE RMSE %.3f m  max %.3f m" % (
        model, len(loops), dropped, *res[model]))
for m in bg.MODELS[1:]:
    assert res[m][0] < 0.5 * res["none"][0], (m, res)

# 4. A long corridor (degenerate for ~100 m) driven out and back: loops that pin the corridor axis
#    (iso, hessian) lock in the along-axis drift between the two passes; Schur models must not.
world2 = bs.make_world(s=0.08, L=140.0)
wp = [(-9, 0), (-2, 0), (120, 0), (-2, 0.3), (-9, -2.5), (-9, 0.5)]
T_gt = bs.path(wp, step=1.0)
T_fe = bs.drifted(T_gt, rng, drift_world=(0.015, 0.0, 0.004), yaw_bias_deg=0.01)
clouds = [bi.voxel_down(bs.scan(world2, T, rng, rmax=20.0, tol_deg=0.5), 0.2) for T in T_gt]
kf_t = np.arange(len(T_gt)) * 1.0
G = np.array([T[:3, 3] for T in T_gt])
res2 = {}
closer = bg.LoopCloser(clouds, min_gap_s=20.0, r_xy=6.0)
for model in bg.MODELS:
    T_opt, loops = bg.run_backend(kf_t, clouds, T_fe, sig, model, closer=closer)
    P = np.array([T[:3, 3] for T in T_opt])
    res2[model] = ate(P, G)
    dropped = sum(L["info"]["dropped_t"] > 0 for L in loops)
    print("4. %-11s loops %3d (translation direction dropped in %3d)  ATE RMSE %.3f m  max %.3f m" % (
        model, len(loops), dropped, *res2[model]))
assert res2["schur_otsu"][0] < 0.5 * res2["iso"][0] and res2["schur_otsu"][0] < 0.5 * res2["hessian"][0], res2

# 5. odometry-noise calibration recovers injected noise through an unknown fixed body rotation
n = 200
gt_t = np.arange(n) * 1.0
Rg, pg = [np.eye(3)], [np.zeros(3)]
for k in range(n - 1):
    Rg.append(Rg[-1] @ fc.so3_exp(np.r_[rng.normal(0, 0.02, 2), rng.normal(0, 0.15)]))
    pg.append(pg[-1] + Rg[-1] @ np.r_[1.0, 0, 0])
C = fc.so3_exp([0.3, -0.2, 1.2])
TF = [bi.se3(Rg[0] @ C.T, pg[0])]
for k in range(n - 1):
    dF = C @ (Rg[k].T @ Rg[k + 1]) @ C.T @ fc.so3_exp(rng.normal(0, np.radians(0.1), 3))
    T = TF[-1].copy()
    T[:3, :3] = TF[-1][:3, :3] @ dF
    T[:3, 3] = TF[-1][:3, 3] + (pg[k + 1] - pg[k]) + rng.normal(0, 0.01, 3)
    TF.append(T)
sg = bg.odometry_sigmas_from_gt(gt_t, TF, gt_t, np.array(pg), np.ones(n, bool), gt_R=Rg)
assert abs(np.degrees(sg[0]) - 0.1) < 0.03 and abs(sg[3] - 0.01) < 0.004, sg
print("5. odometry noise recovered: %.3f deg, %.4f m (injected 0.100 deg, 0.0100 m)" % (np.degrees(sg[0]), sg[3]))
print("ALL BACK-END TESTS PASSED (%.0f s)" % (time.time() - t0))
