#!/usr/bin/env python3
"""Paired offline ablation of the LiDAR translation weight (open-loop replay of logged runs).

usage: python3 ablation_weights.py --gt ground_truth_path.csv --c-t 0.03 LOG1.csv [LOG2.csv ...]
Every variant replays exactly the same logged A-LOAM scan-to-map poses, VINS-Mono poses and Hessians, so
differences come only from the weighting rule. Rotation is taken from VINS-Mono in every variant.
Open-loop replay does not feed the fused pose back into A-LOAM, so absolute numbers are worse than live
runs; use the ranking, then confirm the top variants live (WEIGHT_MODE=... in fusion_node_v2)."""
import argparse
import os

import numpy as np

import fusion_core as fc
import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--gt", required=True)
ap.add_argument("--c-t", type=float, default=0.03)
ap.add_argument("--alpha", type=float, default=None, help="const blend; default = mean Schur weight on bag 0")
ap.add_argument("--kth", type=float, default=15.7)
ap.add_argument("--modes", default=",".join(fc.W_MODES[:1] + ("schur_gate",) + fc.W_MODES[1:]))
ap.add_argument("--out", default=None, help="csv with one row per (log, mode)")
ap.add_argument("logs", nargs="+")
a = ap.parse_args()
gt_t, gt_p = vt.load_gt(a.gt)
modes = a.modes.split(",")
rows = []
for path in a.logs:
    d = vt.load_v2_log(path)
    t = d["t"]
    segs = dict(full=np.ones(len(t), bool), bag0=t < vt.BAG0_END, held=t >= vt.BAG0_END)
    alpha = a.alpha
    if alpha is None:   # mean eigenvalue of the Schur weight on the calibration bag only
        ws = []
        for k in range(len(t)):
            if t[k] < vt.BAG0_END and d["H"][k] is not None:
                S = fc.schur_blocks(d["H"][k], d["hess_frame"])[1]
                ws.append(np.trace(fc.info_weight(S, a.c_t)) / 3)
        alpha = float(np.mean(ws)) if ws else 0.7
    tag = os.path.basename(path).replace("switching_log_v2_", "").replace(".csv", "")
    for m in modes:
        # ours ("schur") is ungated as in the live F8 runs; "schur_gate" adds the kappa(S_RR) <= kth gate (F1-like)
        wm, kth = ("schur", 1e9) if m == "schur" else ("schur", a.kth) if m == "schur_gate" else (m, a.kth)
        p, md = vt.replay(d, a.c_t, kth=kth, w_mode=wm, alpha=alpha)
        full = vt.ate(t, p, gt_t, gt_p, segs["full"])
        held = vt.ate(t, p, gt_t, gt_p, segs["held"])
        b0 = vt.ate(t, p, gt_t, gt_p, segs["bag0"])
        r1 = vt.rpe(t, p, gt_t, gt_p, segs["held"], 1.0)
        r10 = vt.rpe(t, p, gt_t, gt_p, segs["held"], 10.0)
        rows.append((tag, m, full[0], full[1], b0[0], held[0], r1, r10, alpha))
        print("%-14s %-9s full %6.3f / %5.2f  bag0 %6.3f  held %6.3f  RPE1s %.4f  RPE10s %.3f" % (
            tag, m, full[0], full[1], b0[0], held[0], r1, r10), flush=True)
print()
R = {m: np.array([[r[2], r[5], r[6], r[7]] for r in rows if r[1] == m]) for m in modes}
ref = R["schur"] if "schur" in R else None
print("%-9s  n   full RMSE        held-out RMSE    RPE 1 s   RPE 10 s   wins vs schur (full)" % "mode")
for m in modes:
    x = R[m]
    wins = "" if ref is None or m == "schur" else "%d of %d" % (int(np.sum(x[:, 0] < ref[:, 0])), len(x))
    print("%-9s %2d  %.3f +- %.3f   %.3f +- %.3f   %.4f    %.3f     %s" % (
        m, len(x), x[:, 0].mean(), x[:, 0].std(ddof=1) if len(x) > 1 else 0, x[:, 1].mean(),
        x[:, 1].std(ddof=1) if len(x) > 1 else 0, x[:, 2].mean(), x[:, 3].mean(), wins))
if a.out:
    import csv
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["log", "mode", "full_rmse", "full_max", "bag0_rmse", "held_rmse", "rpe1_held", "rpe10_held", "alpha"])
        w.writerows(rows)
