#!/usr/bin/env python3
"""Summary of one fusion_node_v2 run, with a PAIRED ablation from the same run's recorded data.

VINS-Mono differs from run to run (1.02-1.34 m RMSE on Multi Floor), so comparing two separate runs
mixes the method's effect with VINS noise.  This script replays, open-loop on the SAME recorded
scan-to-map poses and VINS poses: VINS-primary (C_T=0), LiDAR-only, and the run's own setting, and
reports them next to the live result.  The live number is the one to compare with published results.

usage: python3 fusion_summary.py --log switching_log_v2_TAG.csv --gt ground_truth_path.csv [--c-t 1e-3]
"""
import argparse
import numpy as np
import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--log", required=True)
ap.add_argument("--gt", required=True)
ap.add_argument("--c-t", type=float, default=None, help="C_T used in the run (default: read nothing, use 1e-3)")
ap.add_argument("--kappa-th", type=float, default=15.7)
ap.add_argument("--calib-end", type=float, default=vt.BAG0_END)
a = ap.parse_args()

d = vt.load_v2_log(a.log)
gt_t, gt_p = vt.load_gt(a.gt)
L, t = d["df"], d["t"]
live = L[["fused_x", "fused_y", "fused_z"]].values.astype(float)
modes = L["mode"].astype(str).values
print("log:", a.log, "| scans %d, span %.1f s, Hessian frame %s" % (len(t), t[-1] - t[0], d["hess_frame"]))
print("mode share:", ", ".join("%s %.3f" % (m, np.mean(modes == m)) for m in sorted(set(modes))))
f = modes == "FUSED"
if f.any() and "gate" in L:
    g = L["gate"].values[f].astype(float)
    print("gate open in FUSED: %.3f | median LiDAR weight eigenvalues (min/mid/max) when open: %s"
          % (np.nanmean(g), np.round(np.nanmedian(L[["wt0", "wt1", "wt2"]].values[f][g > 0], 0), 3) if (g > 0).any() else "-"))
    print("kappa threshold at end: %.2f" % L["kth"].values[f][-1])
segs = [("full span", np.ones(len(t), bool)), ("bag 0 (calibration)", t < a.calib_end),
        ("bags 1-2 (held out)", t >= a.calib_end), ("after VINS start (>=1660857413)", t >= 1660857413.0)]
c = 1e-3 if a.c_t is None else a.c_t
cands = [("LIVE fused (this run)", live)]
for name, mode, cc in [("replay VINS-primary (C_T=0)", "vins", 0.0), ("replay LiDAR only", "lidar", 0.0),
                       ("replay fused C_T=%g" % c, "fused", c)]:
    p, _ = vt.replay(d, cc, kth=a.kappa_th, mode=mode)
    cands.append((name, p))
print("\n%-32s" % "ATE RMSE / max (m)" + "".join("%34s" % s[0] for s in segs))
for name, p in cands:
    print("%-32s" % name + "".join("%25.3f / %6.2f" % vt.ate(t, p, gt_t, gt_p, m) for _, m in segs))
print("\nRPE(1 s) held-out: " + ", ".join("%s %.4f" % (n, vt.rpe(t, p, gt_t, gt_p, t >= a.calib_end)) for n, p in cands))
