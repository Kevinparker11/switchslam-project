#!/usr/bin/env python3
"""Full-span ATE of the A-LOAM scan-to-map output (the aft_ columns) of one fusion_node_v2 log.
Same GT loader, same alignment (Umeyama SE(3), no scale) and same printout as score_run.py, which scores the fused_ columns.
Used for the stock A-LOAM runs, where the node only logs and A-LOAM's own pose is the result.
usage: python3 score_aft.py --gt GT --log switching_log_v2_TAG.csv   (run from fusion_v4/)"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--gt", required=True)
ap.add_argument("--log", required=True)
a = ap.parse_args()
gt_t, gt_p = vt.load_gt(a.gt)
d = vt.load_v2_log(a.log)
L = d["df"]
p = L[["aft_x", "aft_y", "aft_z"]].values.astype(float)
t = d["t"]
m = (t >= gt_t[0]) & (t <= gt_t[-1]) & np.isfinite(p).all(1)
rmse, mx = vt.ate(t, p, gt_t, gt_p)
path = float(np.sum(np.linalg.norm(np.diff(gt_p, axis=0), axis=1)))
print("GT span %.1f..%.1f, log span %.1f..%.1f, %d of %d poses inside GT span" % (
    gt_t[0], gt_t[-1], t[0], t[-1], int(m.sum()), len(t)))
print("A-LOAM scan-to-map output (aft_), full span: n= %d  GT path %6.1f m  RMSE = %6.2f m   Max = %6.2f m" % (int(m.sum()), path, rmse, mx))
