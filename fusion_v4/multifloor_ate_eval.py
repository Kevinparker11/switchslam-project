#!/usr/bin/env python3
"""ATE for Multi Floor runs. Rigid SE(3) Umeyama, no scale; GT interpolated at estimate timestamps.
  --fmt aloam  : rostopic echo -p /aft_mapped_to_init > file.csv
  --fmt vins   : vins_result_no_loop.csv
  --fmt switch : switching-node log (time, fused_x/y/z; --cols aft for aft_x/y/z)"""
import argparse, sys
import numpy as np
import pandas as pd

BAG_START = 1660857392.50
BAG_END = 1660857810.02
DEFAULT_COMMON_START = 1660857413.0


def umeyama(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    cov = (dst - mu_d).T @ (src - mu_s) / len(src)
    U, _, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    return R, mu_d - R @ mu_s


def load_gt(path):
    g = pd.read_csv(path)
    return g["timestamp"].values / 1e9, g[["p_w_b_x", "p_w_b_y", "p_w_b_z"]].values


def load_est(path, fmt, cols):
    if fmt == "vins":
        d = pd.read_csv(path, header=None)
        return d[0].values / 1e9, d[[1, 2, 3]].values
    if fmt == "aloam":
        d = pd.read_csv(path)
        t = d["field.header.stamp"].values / 1e9
        p = d[["field.pose.pose.position.x", "field.pose.pose.position.y",
               "field.pose.pose.position.z"]].values
        return t, p
    d = pd.read_csv(path, usecols=lambda c: c in ("time", f"{cols}_x", f"{cols}_y", f"{cols}_z")).dropna()
    return d["time"].values, d[[f"{cols}_x", f"{cols}_y", f"{cols}_z"]].values


def ate(t, p, gt_t, gt_p, tmin=None):
    m = (t >= gt_t[0]) & (t <= gt_t[-1])
    if tmin is not None:
        m &= t >= tmin
    if m.sum() < 20:
        return None
    t, p = t[m], p[m]
    g = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
    R, tr = umeyama(p, g)
    e = np.linalg.norm(p @ R.T + tr - g, axis=1)
    return dict(n=len(t), rmse=float(np.sqrt((e ** 2).mean())), mx=float(e.max()),
                gt_len=float(np.linalg.norm(np.diff(g, axis=0), axis=1).sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--gt", required=True)
    ap.add_argument("--fmt", required=True, choices=["aloam", "vins", "switch"])
    ap.add_argument("--cols", default="fused", choices=["fused", "aft"])
    ap.add_argument("--common-start", type=float, default=DEFAULT_COMMON_START)
    a = ap.parse_args()
    gt_t, gt_p = load_gt(a.gt)
    t, p = load_est(a.file, a.fmt, a.cols)
    o = np.argsort(t)
    t, p = t[o], p[o]
    print(f"{a.file}: {len(t)} poses, t = {t[0]:.2f} .. {t[-1]:.2f}  ({t[-1]-t[0]:.1f} s)")
    if ((t >= gt_t[0]) & (t <= gt_t[-1])).sum() < 0.5 * len(t):
        sys.exit("ERROR: poses are outside the ground-truth time span (wall-clock stamps?). "
                 "use_sim_time was probably not set. Rerun the experiment.")
    print(f"starts {t[0]-BAG_START:5.1f} s after bag start, ends {BAG_END-t[-1]:5.1f} s before bag end")
    for label, tmin in [("full span of this run", None), (f"common window (>= {a.common_start:.0f})", a.common_start)]:
        r = ate(t, p, gt_t, gt_p, tmin)
        if r is None:
            print(f"  {label}: not enough overlapping poses")
        else:
            print(f"  {label}: n={r['n']:5d}  GT path {r['gt_len']:6.1f} m  RMSE = {r['rmse']:6.2f} m   Max = {r['mx']:6.2f} m")


if __name__ == "__main__":
    main()
