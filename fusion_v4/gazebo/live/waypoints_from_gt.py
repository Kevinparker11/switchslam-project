#!/usr/bin/env python3
"""Turn a manually driven run's ground-truth file into a WAYPOINTS string for waypoint_driver_route.py (11 Nov 2026).
usage: python3 waypoints_from_gt.py gt_plane.txt [spacing_m=8]
Uses the GT after the reset (largest step > 0.5 m, as score_fused.py), drops the standing time at the start and the end (a sample counts as
moving when it is more than 0.3 m from the first / last resting point), and takes one waypoint every `spacing` metres of path plus the
final point.  The driver's goal tolerance is 1.5 m, so the replay follows the manual path to about that accuracy.
Prints the start pose, the path length, and a ready line:  WAYPOINTS="x,y;x,y;..."   Also writes <gt>.waypoints.txt."""
import sys
import numpy as np

gt = np.loadtxt(sys.argv[1], comments="#", ndmin=2)
sp = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
j = np.linalg.norm(np.diff(gt[:, 1:3], axis=0), axis=1)
k = int(np.argmax(j))
g = gt[k + 1:] if j[k] > 0.5 else gt
xy = g[:, 1:3]
moved = np.linalg.norm(xy - xy[0], axis=1) > 0.3
i0 = max(int(np.argmax(moved)) - 1, 0)
back = np.linalg.norm(xy - xy[-1], axis=1) > 0.3
i1 = min(len(xy) - 1 - int(np.argmax(back[::-1])) + 1, len(xy) - 1)
p = xy[i0:i1 + 1]
s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
yaw0 = np.degrees(np.arctan2(2 * (g[i0, 7] * g[i0, 6] + g[i0, 4] * g[i0, 5]), 1 - 2 * (g[i0, 5] ** 2 + g[i0, 6] ** 2)))
print("after the reset: %d samples, moving part %d samples, path %.1f m, duration %.0f s, mean speed %.3f m/s"
      % (len(xy), len(p), s[-1], g[i1, 0] - g[i0, 0], s[-1] / max(g[i1, 0] - g[i0, 0], 1e-9)))
print("start of the moving part (%.2f, %.2f), heading %.0f deg; end (%.2f, %.2f); straight-line start to end %.1f m"
      % (p[0, 0], p[0, 1], yaw0, p[-1, 0], p[-1, 1], np.linalg.norm(p[-1] - p[0])))
idx = [int(np.searchsorted(s, d)) for d in np.arange(sp, s[-1] - 0.5 * sp, sp)] + [len(p) - 1]
wp = [tuple(np.round(p[i], 1)) for i in idx]
line = ";".join("%.1f,%.1f" % w for w in wp)
print("%d waypoints, spacing about %.0f m" % (len(wp), sp))
print('WAYPOINTS="%s"' % line)
open(sys.argv[1] + ".waypoints.txt", "w").write(line + "\n")
