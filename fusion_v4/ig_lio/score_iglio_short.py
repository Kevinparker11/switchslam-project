#!/usr/bin/env python3
"""Short test of the declared iG-LIO resolution change (Multi Floor, first ~110 s, iG-LIO alone).
usage: IGLIO_GT=<Multi Floor ground_truth_path.csv> python3 -I score_iglio_short.py <switching_log_v2_SMOKE_I0_run1.csv> <iglio_SMOKE_I0_run1.out>
Pass rule (fixed before the run; baseline = authors' frozen 0.5 m config, three full runs, point count of the downsampled scan):
  P1 median downsampled points per scan in frames 500-700 >= 150   (baseline 74; 456 at the start)
  P2 no scan with fewer than 20 downsampled points in the whole window   (baseline: starvation from frame ~550 on)
  P3 error at 105 s <= 2.5 m with the rigid alignment fitted on the first 40 s only   (GenZ-LIO reaches 2.2-2.5 m with the same fit; baseline iG-LIO 0.4-4.8 m)
All three must hold. This tests that the stairwell starvation is relieved over 110 s; it says nothing about full length."""
import sys, os, re, csv, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import v2_tools as vt
gt_t, gt_p = vt.load_gt(os.environ["IGLIO_GT"])
gi = lambda tt: np.stack([np.interp(tt, gt_t, gt_p[:, k]) for k in range(3)], 1)
def um(A, B):
    ma, mb = A.mean(0), B.mean(0); C = (B-mb).T @ (A-ma)/len(A); U, _, Vt = np.linalg.svd(C); D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(U @ Vt)); R = U @ D @ Vt; return R, mb-R @ ma
rows = list(csv.DictReader(open(sys.argv[1]))); g = lambda k: np.array([float(r[k]) for r in rows])
t = g("time"); P = np.stack([g("aft_x"), g("aft_y"), g("aft_z")], 1); t0 = t[0]
M = np.array([int(m[1]) for l in open(sys.argv[2], errors="ignore") for m in [re.search(r"total points: (\d+) precent", l)] if m])
m40 = (t-t0 <= 40) & (t >= gt_t[0]); R, tr = um(P[m40], gi(t[m40])); Q = (R @ P.T).T + tr
i = min(np.searchsorted(t-t0, 105.0), len(t)-1); ok = (t >= gt_t[0]) & (t <= gt_t[-1]); e = np.where(ok, np.linalg.norm(Q-gi(np.clip(t, gt_t[0], gt_t[-1])), axis=1), np.nan)
med = float(np.median(M[500:700])) if len(M) >= 700 else float("nan")
print(f"rows {len(t)}  scans logged {len(M)}  last pose time {t[-1]-t0:.1f} s")
print(f"median downsampled points: frames 0-100 {np.median(M[:100]):.0f}, 500-700 {med:.0f}; min over all {M.min()} (scans < 20 points: {(M < 20).sum()})")
print(f"error at 105 s (fit on first 40 s): {e[i]:.2f} m;  max over run {np.nanmax(e):.2f} m;  max step {np.linalg.norm(np.diff(P, axis=0), axis=1).max():.2f} m")
p1, p2, p3 = med >= 150, (M < 20).sum() == 0, e[i] <= 2.5
print("P1 points >=150:", p1, "| P2 no starved scan:", p2, "| P3 error <=2.5 m:", p3, "->", "PASS" if (p1 and p2 and p3) else "FAIL")
