#!/usr/bin/env python3
"""Choose the LiDAR information scale C_T on the CALIBRATION segment only (Multi Floor bag 0).

Criterion: RMS error of 1-s position increments (RPE) of the replayed fused trajectory on bag 0,
after the VIO warm-up.  Short-horizon error is what a fusion weight controls; whole-trajectory ATE is
dominated by slow drift and is a poor criterion.  The held-out numbers printed at the end are for
information only and must NOT be used to choose C_T.

usage: python3 calibrate_c.py --log switching_log_v2_F0_run1.csv --gt ground_truth_path.csv
       [--calib-end 1660857541.2] [--grid 0,1e-5,3e-5,1e-4,3e-4,1e-3,3e-3,1e-2] [--kappa-th 15.7]
Any v2 log works (ideally an F0 = VINS-primary run, which logs the scan-to-map poses and Hessians).
"""
import argparse
import numpy as np
import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--log", required=True)
ap.add_argument("--gt", required=True)
ap.add_argument("--calib-end", type=float, default=vt.BAG0_END)
ap.add_argument("--grid", default="0,1e-6,3e-6,1e-5,3e-5,1e-4,3e-4,1e-3,3e-3,1e-2,3e-2")
ap.add_argument("--kappa-th", type=float, default=15.7)
ap.add_argument("--kappa-mode", default="fixed")
ap.add_argument("--t-warm", type=float, default=20.0)
ap.add_argument("--horizon", type=float, default=1.0)
a = ap.parse_args()

d = vt.load_v2_log(a.log)
gt_t, gt_p = vt.load_gt(a.gt)
t = d["t"]
print("log %s: %d mapped scans, Hessian frame '%s'" % (a.log, len(t), d["hess_frame"]))
rows = []
for c in [float(x) for x in a.grid.split(",")]:
    p, modes = vt.replay(d, c, kth=a.kappa_th, kappa_mode=a.kappa_mode, t_warm=a.t_warm)
    calm = (t < a.calib_end) & (modes == "FUSED")
    rows.append((c, vt.rpe(t, p, gt_t, gt_p, calm, a.horizon), *vt.ate(t, p, gt_t, gt_p, t < a.calib_end),
                 *vt.ate(t, p, gt_t, gt_p, t >= a.calib_end), *vt.ate(t, p, gt_t, gt_p)))
print("%-9s %12s %16s | %22s %18s" % ("C_T", "bag0 RPE(1s)", "bag0 ATE/max", "held-out ATE/max (info)", "full ATE/max (info)"))
for c, r, a0, m0, a1, m1, a2, m2 in rows:
    print("%-9g %12.4f %8.3f/%6.2f | %14.3f/%6.2f %12.3f/%6.2f" % (c, r, a0, m0, a1, m1, a2, m2))
best = min(rows, key=lambda x: x[1] if np.isfinite(x[1]) else 1e9)
print("\nCHOSEN C_T = %g  (minimum bag-0 RPE(%gs)); use it for the held-out evaluation runs." % (best[0], a.horizon))
