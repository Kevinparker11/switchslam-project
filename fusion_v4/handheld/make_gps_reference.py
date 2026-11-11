#!/usr/bin/env python3
"""GPS reference for the LVI-SAM Handheld bag (11 Nov 2026). Writes 't x y 0 0 0 0 1' (east, north in metres from the first kept fix; the format
score_run_xy.py reads) from /gps/fix.   usage: python3 make_gps_reference.py handheld.bag handheld_gps_xy_clean.txt [--var-max 1.0]
Cleaning rule, fixed before any score: a fix is dropped if NavSatStatus < 0 or its horizontal position variance (covariance[0] or [4], the larger)
exceeds --var-max (default 1.0 m^2, i.e. 1 m standard deviation). Nothing is smoothed or interpolated here. All counts are printed.
Why only horizontal: the vertical variance of this bag is about 370 m^2 (checker printout of 11 Nov 2026), so z is not a reference.
needs: pip install "rosbags==0.11.9" numpy"""
import sys
from pathlib import Path
import numpy as np
from rosbags.highlevel import AnyReader

bag, out = Path(sys.argv[1]), sys.argv[2]
vmax = float(sys.argv[sys.argv.index("--var-max") + 1]) if "--var-max" in sys.argv else 1.0
rows = []
with AnyReader([bag]) as r:
    conns = [c for c in r.connections if c.topic == "/gps/fix"]
    for c, ts, raw in r.messages(connections=conns):
        m = r.deserialize(raw, c.msgtype)
        rows.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.latitude, m.longitude, m.status.status,
                     max(m.position_covariance[0], m.position_covariance[4])))
g = np.array(rows)
bad_status, bad_var = g[:, 3] < 0, g[:, 4] > vmax
keep = ~(bad_status | bad_var)
print("fixes %d: dropped %d (status < 0: %d, horizontal variance > %.2f m^2: %d), kept %d" %
      (len(g), (~keep).sum(), bad_status.sum(), vmax, (bad_var & ~bad_status).sum(), keep.sum()))
print("status values among kept: %s; variance of kept: median %.3f, max %.3f m^2" %
      (sorted(set(g[keep, 3].astype(int))), np.median(g[keep, 4]), g[keep, 4].max()))
k = g[keep]
t = k[:, 0]
gap = np.diff(t)
print("kept span %.1f to %.1f (%.1f s); gaps above 1 s: %d (longest %.1f s)" % (t[0], t[-1], t[-1] - t[0], (gap > 1.0).sum(), gap.max()))
lat0, lon0 = np.radians(k[0, 1]), np.radians(k[0, 2])
e = 6378137.0 * (np.radians(k[:, 2]) - lon0) * np.cos(lat0)
n = 6378137.0 * (np.radians(k[:, 1]) - lat0)
print("path of kept fixes %.0f m, extent %.0f x %.0f m" % (np.hypot(np.diff(e), np.diff(n)).sum(), np.ptp(e), np.ptp(n)))
np.savetxt(out, np.c_[t, e, n, np.zeros(len(t)), np.zeros(len(t)), np.zeros(len(t)), np.zeros(len(t)), np.ones(len(t))], fmt="%.6f")
print("wrote", out)
