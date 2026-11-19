#!/usr/bin/env python3
"""Full-span ATE of a TUM trajectory (t x y z qx qy qz qw) against the sequence's ground truth.
Same GT loader, same alignment (Umeyama SE(3), no scale) and the same printout as stock_aloam/score_aft.py.
usage (from fusion_v4/): python3 stock_liosam/score_tum.py --gt GT --est odom.tum"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--gt", required=True)
ap.add_argument("--est", required=True)
a = ap.parse_args()
gt_t, gt_p = vt.load_gt(a.gt)
E_ = np.loadtxt(a.est, ndmin=2)
if E_.shape[0] < 3:
    print("stock LIO-SAM output: only %d poses, no score" % E_.shape[0])
    sys.exit(0)
t, p = E_[:, 0], E_[:, 1:4]
m = (t >= gt_t[0]) & (t <= gt_t[-1]) & np.isfinite(p).all(1)
rmse, mx = vt.ate(t, p, gt_t, gt_p)
path = float(np.sum(np.linalg.norm(np.diff(gt_p, axis=0), axis=1)))
print("GT span %.1f..%.1f, run span %.1f..%.1f, %d of %d poses inside GT span" % (
    gt_t[0], gt_t[-1], t[0], t[-1], int(m.sum()), len(t)))
print("stock LIO-SAM scan-to-map output (/lio_sam/mapping/odometry), full span: n= %d  GT path %6.1f m  RMSE = %6.2f m   Max = %6.2f m" % (
    int(m.sum()), path, rmse, mx))
