#!/usr/bin/env python3
"""Read-only report of one F17 log: how often the rotation check closed, and the largest disagreement seen.
usage: look_report.py switching_log_v2_F17_run1.csv"""
import sys
import numpy as np
import pandas as pd
d = pd.read_csv(sys.argv[1])
f = d[d["mode"] == "FUSED"]
print("rows %d, FUSED %d" % (len(d), len(f)))
if "rot_gamma" not in d.columns:
    sys.exit("no rot_gamma column: the run was not made with ROT_CHECK=1")
closed = (f["rot_gamma"] < 0.5)
print("check closed on %d of %d FUSED rows (%.2f %%)" % (closed.sum(), len(f), 100.0 * closed.mean()))
print("rot_e2  max %.3f rad (reference 0.340), rot_e10 max %.3f rad (reference 0.570)" % (np.nanmax(f["rot_e2"]), np.nanmax(f["rot_e10"])))
if closed.any():
    t = f["time"].values[closed.values]
    print("closed between t = %.1f and %.1f s of the log (%.0f s span); first closures at %s" % (t[0] - d["time"].iloc[0], t[-1] - d["time"].iloc[0], t[-1] - t[0], np.round(t[:5] - d["time"].iloc[0], 1)))
w = f[["wR0", "wR1", "wR2"]]
print("median R-weight eigenvalues (FUSED rows, check open): %s" % np.round(np.nanmedian(w[~closed.values].values, 0), 3))
