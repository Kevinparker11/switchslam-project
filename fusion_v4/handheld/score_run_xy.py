#!/usr/bin/env python3
"""Horizontal (x, y) full-span ATE of one fusion_node_v2 log against a GPS-derived TUM reference (z ignored).
Use for the LVI-SAM handheld bag, whose only reference is /gps/fix (vertical variance ~370 m^2, so z is not usable).
Alignment: one 2-D rigid fit (rotation about z + translation, no scale). Output line matches score_run.py.
Rule fixed before any run: log poses that fall inside a reference gap longer than --max-gap s (default 1.0) are left out
and counted, because the reference is linearly interpolated there.
usage: python3 score_run_xy.py --gt handheld_gps_xy_clean.txt --log switching_log_v2_TAG.csv [--max-gap 1.0]"""
import argparse

import numpy as np
import pandas as pd


def fit2d(src, dst):
    ms, md = src.mean(0), dst.mean(0)
    H = (src - ms).T @ (dst - md)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, d]) @ U.T
    return R, md - R @ ms


def score(t, xy, gt_t, gt_xy, max_gap=1.0):
    ok = (t >= gt_t[0]) & (t <= gt_t[-1]) & np.isfinite(xy).all(1)
    k = np.clip(np.searchsorted(gt_t, t) , 1, len(gt_t) - 1)
    gap = gt_t[k] - gt_t[k - 1]
    in_gap = ok & (gap > max_gap)
    use = ok & ~in_gap
    if use.sum() < 20:
        return None
    g = np.stack([np.interp(t[use], gt_t, gt_xy[:, i]) for i in range(2)], 1)
    R, tr = fit2d(xy[use], g)
    e = np.linalg.norm(xy[use] @ R.T + tr - g, axis=1)
    return dict(n=int(use.sum()), n_inside=int(ok.sum()), n_gap=int(in_gap.sum()),
                rmse=float(np.sqrt((e ** 2).mean())), mx=float(e.max()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--max-gap", type=float, default=1.0)
    ap.add_argument("--src", default="fused", choices=["fused", "aft", "vins"], help="which column pair of the log: fused output, A-LOAM output, VINS-Mono alone")
    a = ap.parse_args()
    g = np.loadtxt(a.gt)
    gt_t, gt_xy = g[:, 0], g[:, 1:3]
    L = pd.read_csv(a.log)
    L = L[L["mode"] != "INIT"]
    t = L["time"].values.astype(float)
    cand = {"fused": [("fused_x", "fused_y"), ("x", "y"), ("fx", "fy")], "aft": [("aft_x", "aft_y")], "vins": [("v_px", "v_py")]}[a.src]
    cols = next((c for c in cand if c[0] in L.columns and c[1] in L.columns), None)
    if cols is None:
        raise SystemExit("no x/y columns found; log columns are: %s" % list(L.columns))
    xy = L[list(cols)].values.astype(float)
    r = score(t, xy, gt_t, gt_xy, a.max_gap)
    sel = (gt_t >= t[0]) & (gt_t <= t[-1])
    path = float(np.sum(np.linalg.norm(np.diff(gt_xy[sel], axis=0), axis=1)))
    print("GT span %.1f..%.1f, log span %.1f..%.1f, %d of %d poses inside GT span; %d left out inside reference gaps > %.1f s" % (
        gt_t[0], gt_t[-1], t[0], t[-1], r["n_inside"], len(t), r["n_gap"], a.max_gap))
    print("full span of this run: n= %d  GT path in this span %6.1f m  RMSE = %6.2f m   Max = %6.2f m   (horizontal, 2-D alignment)" % (
        r["n"], path, r["rmse"], r["mx"]))
