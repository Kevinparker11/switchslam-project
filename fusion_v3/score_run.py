#!/usr/bin/env python3
"""Full-span ATE of one fusion_node_v2 log against any SubT-MRS ground truth (csv or TUM).
Prints the same 'full span of this run' line as multifloor_ate_eval.py, so run_fusion_study.sh can parse it.
usage: python3 score_run.py --gt GT --log switching_log_v2_TAG.csv"""
import argparse

import numpy as np

import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--gt", required=True)
ap.add_argument("--log", required=True)
a = ap.parse_args()
gt_t, gt_p = vt.load_gt(a.gt)
d = vt.load_v2_log(a.log)
L = d["df"]
p = L[["fused_x", "fused_y", "fused_z"]].values.astype(float)
t = d["t"]
m = (t >= gt_t[0]) & (t <= gt_t[-1]) & np.isfinite(p).all(1)
rmse, mx = vt.ate(t, p, gt_t, gt_p)
path = float(np.sum(np.linalg.norm(np.diff(gt_p, axis=0), axis=1)))
print("GT span %.1f..%.1f, log span %.1f..%.1f, %d of %d poses inside GT span" % (
    gt_t[0], gt_t[-1], t[0], t[-1], int(m.sum()), len(t)))
print("full span of this run: n= %d  GT path %6.1f m  RMSE = %6.2f m   Max = %6.2f m" % (int(m.sum()), path, rmse, mx))
