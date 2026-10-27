#!/usr/bin/env python3
"""Choose GENZ_C_T (the scale of GenZ-LIO's LiDAR information in W_t = (c S_tt + I)^-1 c S_tt) on MULTI FLOOR ONLY.

Same rule that gave C_T = 0.03 for A-LOAM: the smallest full-span ATE over a log-spaced grid, on Multi Floor
(our tuning sequence), averaged over the given logs. Run it on G0 logs (GenZ alone): they contain the GenZ poses,
VINS-Mono poses and the bridged information of every scan. GenZ-LIO uses no feedback from the fusion node, so
replaying a G0 log with any c is EXACT, not an approximation (with A-LOAM it was approximate).
After choosing, freeze the value (GENZ_C_T=...) before running any other sequence.

usage: python3 calibrate_genz_c.py --gt ground_truth_path.csv switching_log_v2_G0_run1.csv [more G0 logs]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import v2_tools as vt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--gt", required=True)
ap.add_argument("logs", nargs="+")
ap.add_argument("--grid", default="0,1e-9,3e-9,1e-8,3e-8,1e-7,3e-7,1e-6,3e-6,1e-5,3e-5,1e-4,3e-4,1e-3,3e-3,1e-2")
a = ap.parse_args()
if "multi" not in a.gt.lower() and "ground_truth_path" not in a.gt:
    print("WARNING: calibrate on Multi Floor only; %s does not look like the Multi Floor ground truth." % a.gt)

gt_t, gt_p = vt.load_gt(a.gt)
grid = [float(x) for x in a.grid.split(",")]
D = [vt.load_v2_log(p) for p in a.logs]
for p, d in zip(a.logs, D):
    nh = sum(H is not None for H in d["H"])
    print("%s: %d scans, %d with information, Hessian frame %s" % (os.path.basename(p), len(d["t"]), nh, d["hess_frame"]))

res = []
for c in grid:
    r = [vt.ate(d["t"], vt.replay(d, c_t=c, kth=1e9)[0], gt_t, gt_p)[0] for d in D]
    res.append((c, np.mean(r), r))
lidar = [vt.ate(d["t"], vt.replay(d, c_t=0.0, mode="lidar")[0], gt_t, gt_p)[0] for d in D]

print("\nC_T          mean ATE (m)   per log")
for c, m, r in res:
    print("%-12g %-14.3f %s" % (c, m, " ".join("%.3f" % x for x in r)))
print("%-12s %-14.3f %s" % ("GenZ only", np.mean(lidar), " ".join("%.3f" % x for x in lidar)))
best = min(res, key=lambda x: x[1])
print("\nchosen GENZ_C_T = %g (mean ATE %.3f m). Freeze it now: export GENZ_C_T=%g" % (best[0], best[1], best[0]))
print("Look at the curve too: if the minimum sits on a plateau, take its middle (as was done for C_T = 0.03).")
