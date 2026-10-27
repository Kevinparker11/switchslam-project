#!/usr/bin/env python3
"""Compare two ground-truth files that should describe the same recording (trust check).

usage: python3 compare_gt.py A B            e.g. ground_truth_path.csv floor01_gt.txt
Each file may be the SubT-MRS CSV (timestamp ns, p_w_b_x/y/z, ...) or TUM (t x y z qx qy qz qw, s).
Reports time overlap, the best time offset, and the position disagreement after an SE(3) alignment
(no scale). Two copies of one GT agree to ~0; two independent references should agree to a few cm."""
import sys

import numpy as np
import pandas as pd


def load(path):
    try:
        g = pd.read_csv(path)
        t = g["timestamp"].values.astype(float)
        p = g[["p_w_b_x", "p_w_b_y", "p_w_b_z"]].values.astype(float)
    except Exception:
        g = np.loadtxt(path, comments="#", delimiter=None)
        t, p = g[:, 0].astype(float), g[:, 1:4].astype(float)
    if t[0] > 1e12:
        t = t / 1e9
    o = np.argsort(t)
    return t[o], p[o]


def umeyama(A, B):
    """R, t minimising |R A + t - B| (rows are points)."""
    ma, mb = A.mean(0), B.mean(0)
    U, _, Vt = np.linalg.svd((B - mb).T @ (A - ma))
    S = np.eye(3)
    S[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ S @ Vt
    return R, mb - R @ ma


def disagreement(ta, pa, tb, pb, dt):
    m = (ta + dt >= tb[0]) & (ta + dt <= tb[-1])
    if m.sum() < 20:
        return None
    Q = np.stack([np.interp(ta[m] + dt, tb, pb[:, i]) for i in range(3)], 1)
    R, t = umeyama(pa[m], Q)
    e = np.linalg.norm((R @ pa[m].T).T + t - Q, axis=1)
    return np.sqrt(np.mean(e ** 2)), e.max(), m.sum(), e


ta, pa = load(sys.argv[1])
tb, pb = load(sys.argv[2])
for name, t, p in [(sys.argv[1], ta, pa), (sys.argv[2], tb, pb)]:
    L = np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1))
    print("%-40s %6d poses  %.1f Hz  span %.1f..%.1f (%.1f s)  path %.1f m" % (
        name[-40:], len(t), (len(t) - 1) / (t[-1] - t[0]), t[0], t[-1], t[-1] - t[0], L))
ov = min(ta[-1], tb[-1]) - max(ta[0], tb[0])
print("time overlap: %.1f s" % ov)
if ov <= 0:
    sys.exit("NO OVERLAP: these are not the same recording (or different time bases)")
best = None
for dt in np.arange(-2.0, 2.0001, 0.02):
    r = disagreement(ta, pa, tb, pb, dt)
    if r and (best is None or r[0] < best[1][0]):
        best = (dt, r)
dt, (rmse, mx, n, e) = best
r0 = disagreement(ta, pa, tb, pb, 0.0)
print("at zero offset:   RMSE %.3f m  max %.3f m" % (r0[0], r0[1]))
print("best offset %+.2f s: RMSE %.3f m  max %.3f m  (%d poses; median %.3f, p95 %.3f)" % (
    dt, rmse, mx, n, np.median(e), np.percentile(e, 95)))
verdict = ("identical (same file re-exported)" if rmse < 0.005 else
           "agree to cm level" if rmse < 0.05 else
           "agree to ~decimetre: usable, quote as GT uncertainty" if rmse < 0.2 else
           "DISAGREE: find out why before using either")
print("verdict:", verdict)
