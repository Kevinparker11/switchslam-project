#!/usr/bin/env python3
"""Summarise one live threshold run (log written by the configurable node).

Prints the rule used, how often each channel fired, the real mode shares, and how well the
combined flag tracked A-LOAM odometry drift (same 8 s drift labels as threshold_screen.py).
ATE comes from your existing multifloor_ate_eval.py; paste both outputs into the results table.

usage: python3 live_summary.py --log ~/runs/thr_S1_kappa10_run1.csv --gt ~/ground_truth_path.csv
"""
import argparse
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--log", required=True); ap.add_argument("--gt", required=True)
ap.add_argument("--window", type=float, default=8.0); ap.add_argument("--min-path", type=float, default=2.0)
ap.add_argument("--calib-end", type=float, default=1660857393.2 + 148.0)
a = ap.parse_args()

L = pd.read_csv(a.log).sort_values("time").reset_index(drop=True)
need = ["flag_R_rot", "flag_R_trans", "flag_T", "mode", "l_px", "l_py", "l_pz"]
miss = [c for c in need if c not in L.columns]
if miss: raise SystemExit(f"log is missing columns {miss}; was it written by the configurable node?")
rule = L["rule"].iloc[0] if "rule" in L.columns else "(rule column missing)"
fR = L.flag_R_rot.astype(bool) | L.flag_R_trans.astype(bool); fT = L.flag_T.astype(bool); f = (fR | fT).values

g = pd.read_csv(a.gt); gt_t = g.timestamp.values / 1e9; gt_p = g[["p_w_b_x", "p_w_b_y", "p_w_b_z"]].values
t = L.time.values; p = L[["l_px", "l_py", "l_pz"]].values
if t.max() < 1e9: raise SystemExit("log time is wall-clock or relative; use_sim_time must be true")
m = (t >= gt_t[0]) & (t <= gt_t[-1])
gi = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
mu_s, mu_d = p[m].mean(0), gi[m].mean(0)
U, _, Vt = np.linalg.svd((gi[m] - mu_d).T @ (p[m] - mu_s) / m.sum())
S = np.eye(3); S[2, 2] = -1 if np.linalg.det(U) * np.linalg.det(Vt) < 0 else 1
pa = (p - mu_s) @ (U @ S @ Vt).T + mu_d
edges = np.arange(t[m][0], t[m][-1], a.window); win = np.full(len(t), -1); drift = []
for k in range(len(edges) - 1):
    i = np.where((t >= edges[k]) & (t < edges[k + 1]))[0]
    path = np.linalg.norm(np.diff(gi[i], axis=0), axis=1).sum() if len(i) >= 5 else 0
    if path < a.min_path: drift.append(np.nan); continue
    drift.append(np.linalg.norm((pa[i[-1]] - pa[i[0]]) - (gi[i[-1]] - gi[i[0]])) / path); win[i] = k
drift = np.array(drift); lo, hi = np.nanpercentile(drift, [33.3, 66.7])
lab = np.full(len(t), np.nan); ok = win >= 0
lab[ok] = np.where(drift[win[ok]] >= hi, 1, np.where(drift[win[ok]] <= lo, 0, np.nan))
test = t >= a.calib_end

print(f"rule: {rule}")
print(f"frames {len(L)}, span {t[-1]-t[0]:.1f} s")
print(f"fire rate  Schur rot {L.flag_R_rot.mean():.3f}  Schur trans {L.flag_R_trans.mean():.3f}  T {fT.mean():.3f}  combined {f.mean():.3f}")
print("mode share:", ", ".join(f"{k} {v:.3f}" for k, v in L["mode"].value_counts(normalize=True).items()))
for name, sel in [("all", np.ones(len(t), bool)), ("bags 1-2 (held out)", test)]:
    b, gd = sel & (lab == 1), sel & (lab == 0)
    print(f"drift labels [{name}]: TPR {f[b].mean():.3f} (n={b.sum()})  FPR {f[gd].mean():.3f} (n={gd.sum()})")
print(f"drift terciles: good <= {lo:.3f} m/m, bad >= {hi:.3f} m/m")
