#!/usr/bin/env python3
"""Check that a ground-truth file matches a bag before any run (used for Long Corridor).

usage: python3 check_gt.py --gt ground_truth.csv --bag-start 1690254112.0 --bag-end 1690254392.0
(take the start/end times from `rosbag info`).  Accepts the SubT-MRS CSV format (timestamp in ns,
p_w_b_x/y/z, q_w_b_x/y/z/w) or a TUM file (t x y z qx qy qz qw, seconds, space separated)."""
import argparse

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--gt", required=True)
ap.add_argument("--bag-start", type=float, required=True)
ap.add_argument("--bag-end", type=float, required=True)
a = ap.parse_args()

try:
    g = pd.read_csv(a.gt)
    t = g["timestamp"].values.astype(float)
    p = g[["p_w_b_x", "p_w_b_y", "p_w_b_z"]].values
    fmt = "SubT-MRS csv"
except Exception:
    g = np.loadtxt(a.gt, comments="#")
    t, p = g[:, 0], g[:, 1:4]
    fmt = "TUM"
if t[0] > 1e12:                       # nanoseconds
    t = t / 1e9
path = float(np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1)))
ov0, ov1 = max(t[0], a.bag_start), min(t[-1], a.bag_end)
print("format %s, %d poses, %.1f Hz" % (fmt, len(t), (len(t) - 1) / max(t[-1] - t[0], 1e-9)))
print("GT  span %.1f .. %.1f  (%.1f s), path %.1f m, start (%.2f %.2f %.2f) end (%.2f %.2f %.2f)" % (
    t[0], t[-1], t[-1] - t[0], path, *p[0], *p[-1]))
print("bag span %.1f .. %.1f  (%.1f s)" % (a.bag_start, a.bag_end, a.bag_end - a.bag_start))
if ov1 <= ov0:
    print("NO OVERLAP: this ground truth does not belong to this bag")
else:
    frac = (ov1 - ov0) / (a.bag_end - a.bag_start)
    print("overlap %.1f s = %.0f%% of the bag  ->  %s" % (ov1 - ov0, 100 * frac,
          "OK" if frac > 0.9 else "PARTIAL: check you have the right file"))
