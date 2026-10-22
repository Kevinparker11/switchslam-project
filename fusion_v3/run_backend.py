#!/usr/bin/env python3
"""Offline back end on one recorded run: loop closure + pose graph, with an ablation of loop-factor models.

usage:
  python3 run_backend.py --log switching_log_v2_F1_run1.csv --kf keyframes_F1_run1.npz \
      --gt ~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv
options:
  --models none,iso,hessian,schur,schur_otsu,schur_gate   (default: all)
  --front fused|aft|vins_replay   odometry chain: the node's output (default), A-LOAM scan-to-map, or the
                             VINS-primary trajectory replayed from the same log (C_T = 0), for a paired check
  --odom-sigma auto|ROT_DEG,TRANS_M   per-keyframe odometry noise; auto = measured on the calibration
                             segment (bag 0) against ground truth, the same protocol as calibrate_c.py
  --out-prefix PATH          writes PATH_<model>.csv (time, x, y, z of every scan) for plotting
Ground truth is used only for scoring and, with --odom-sigma auto, for the calibration segment.
Needs numpy, scipy, pandas and gtsam (pip install gtsam).
"""
import argparse
import time

import numpy as np
import pandas as pd

import backend_graph as bg
import backend_icp as bi
import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--log", required=True)
ap.add_argument("--kf", required=True)
ap.add_argument("--gt", required=True)
ap.add_argument("--models", default=",".join(bg.MODELS))
ap.add_argument("--front", default="fused", choices=["fused", "aft", "vins_replay"])
ap.add_argument("--odom-sigma", default="auto")
ap.add_argument("--calib-end", type=float, default=vt.BAG0_END)
ap.add_argument("--min-gap", type=float, default=30.0)
ap.add_argument("--r-xy", type=float, default=8.0)
ap.add_argument("--rounds", type=int, default=1, help="loop-search rounds (1 = search once from the front-end poses; 2 re-searches from the corrected poses and failed on 1 of 6 real recordings)")
ap.add_argument("--out-prefix", default=None)
a = ap.parse_args()

t0 = time.time()
L = pd.read_csv(a.log)
L = L[pd.to_numeric(L["time"], errors="coerce").notna()].reset_index(drop=True)
t_scan = L["time"].astype(float).values
if a.front == "vins_replay":
    import fusion_core as fc
    d = vt.load_v2_log(a.log)
    core = fc.FusionCore(vt.R_IL, vt.t_IL, c_t=0.0, c_R=0.0, hess_frame=d["hess_frame"])
    T_scan = []
    for k in range(len(d["t"])):
        R, p, _ = core.step(d["t"][k], d["aft"][k], d["vins"][k], d["H"][k])
        T_scan.append(bi.se3(R, p))
    t_scan = d["t"]
else:
    cols = ("fused_x", "fused_y", "fused_z", "fused_qx", "fused_qy", "fused_qz", "fused_qw") if a.front == "fused" \
        else ("aft_x", "aft_y", "aft_z", "aft_qx", "aft_qy", "aft_qz", "aft_qw")
    T_scan = bg.front_end_poses(L, cols)
K = bg.load_keyframes(a.kf)
T_kf, ok = bg.poses_at(K["t"], t_scan, T_scan)
keep = np.where(ok)[0]
kf_t = K["t"][keep]
clouds = [K["clouds"][k] for k in keep]
T_kf = [T_kf[k] for k in keep]
gt_t, gt_p, gt_R = bg.load_gt_poses(a.gt)
print("run %s: %d scans, %d keyframes (%d matched to the log), median %d points per keyframe" % (
    a.log, len(t_scan), len(K["t"]), len(keep), int(np.median([len(c) for c in clouds]))))

if a.odom_sigma == "auto":
    sig = bg.odometry_sigmas_from_gt(kf_t, T_kf, gt_t, gt_p, kf_t < a.calib_end, gt_R=gt_R)
    if sig is None:
        sig = np.r_[[np.radians(0.1)] * 3, [0.02] * 3]
    src = "measured on the calibration segment"
else:
    r_deg, t_m = [float(x) for x in a.odom_sigma.split(",")]
    sig = np.r_[[np.radians(r_deg)] * 3, [t_m] * 3]
    src = "given"
print("odometry noise per keyframe step (%s): rotation %.3f deg, translation %.3f m" % (
    src, np.degrees(sig[0]), sig[3]))

segs = [("full span", np.ones(len(t_scan), bool)), ("bag 0", t_scan < a.calib_end), ("bags 1-2", t_scan >= a.calib_end)]
closer = bg.LoopCloser(clouds, min_gap_s=a.min_gap, r_xy=a.r_xy)
rows = []
for model in a.models.split(","):
    T_opt, loops = bg.run_backend(kf_t, clouds, T_kf, sig, model, rounds=a.rounds, closer=closer, verbose=True)
    P = bg.correct_all_scans(t_scan, T_scan, kf_t, T_kf, T_opt)
    r = [model, len(loops), sum(l["info"]["dropped_t"] > 0 for l in loops), sum(l["info"]["dropped_R"] > 0 for l in loops)]
    for _, m in segs:
        r += list(vt.ate(t_scan, P, gt_t, gt_p, m))
    rows.append(r)
    print("%-11s loops %3d | full %.3f / %.2f | bag0 %.3f / %.2f | bags1-2 %.3f / %.2f   (%.0f s)" % (
        model, len(loops), r[4], r[5], r[6], r[7], r[8], r[9], time.time() - t0))
    if a.out_prefix:
        pd.DataFrame({"time": t_scan, "x": P[:, 0], "y": P[:, 1], "z": P[:, 2]}).to_csv(
            "%s_%s.csv" % (a.out_prefix, model), index=False)
    if loops and model != "none":
        span = [(kf_t[l["i"]] - t_scan[0], kf_t[l["j"]] - t_scan[0]) for l in loops]
        print("            loops connect t+%s s" % ", ".join("%.0f<->%.0f" % s for s in span[:12]) +
              (" ..." if len(span) > 12 else ""))

print("\n%-11s %5s %8s %8s | %16s | %16s | %16s" % ("model", "loops", "drop_t", "drop_R", "full RMSE/max",
                                                   "bag 0 RMSE/max", "bags 1-2 RMSE/max"))
for r in rows:
    print("%-11s %5d %8d %8d | %8.3f / %5.2f | %8.3f / %5.2f | %8.3f / %5.2f" % tuple(r))
