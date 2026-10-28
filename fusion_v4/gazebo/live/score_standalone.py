#!/usr/bin/env python3
"""Score the standalone A-LOAM control.  usage: score_standalone.py gt.txt aloam_prefix
Full-span ATE RMSE / max (m), Umeyama SE(3), no scale, scored from max(reset, first A-LOAM output).
The reset (teleport to (0, 0, 0.2)) is the largest jump (> 0.5 m) between consecutive ground-truth samples."""
import sys
import numpy as np

def load(p):
    return np.loadtxt(p, comments="#", ndmin=2)

def umeyama(src, dst):
    ms, md = src.mean(0), dst.mean(0)
    U, _, Vt = np.linalg.svd((dst - md).T @ (src - ms) / len(src))
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    return R, md - R @ ms

def ate(t, p, gt):
    m = (t >= gt[0, 0]) & (t <= gt[-1, 0])
    t, p = t[m], p[m]
    if len(t) < 20:
        return None
    g = np.stack([np.interp(t, gt[:, 0], gt[:, i]) for i in (1, 2, 3)], 1)
    R, tr = umeyama(p, g)
    e = np.linalg.norm(p @ R.T + tr - g, axis=1)
    return len(t), float(np.sqrt((e ** 2).mean())), float(e.max()), float(np.linalg.norm((p @ R.T + tr)[-1] - g[-1]))

gt = load(sys.argv[1])
j = np.linalg.norm(np.diff(gt[:, 1:3], axis=0), axis=1)
k = int(np.argmax(j))
t_reset = gt[k + 1, 0] if j[k] > 0.5 else gt[0, 0]
print("GT samples %d, reset at t=%.2f s (jump %.2f m)" % (len(gt), t_reset, j[k]))
g2 = gt[gt[:, 0] >= t_reset]
path = np.linalg.norm(np.diff(g2[:, 1:3], axis=0), axis=1).sum()
print("GT path after reset %.1f m, end (%.1f, %.1f)" % (path, g2[-1, 1], g2[-1, 2]))
for name in ("aft", "odom"):
    a = load("%s_%s.txt" % (sys.argv[2], name))
    t0 = max(t_reset, a[0, 0])
    a = a[a[:, 0] >= t0]
    lab = {"aft": "A-LOAM scan-to-map (aft_mapped_to_init)", "odom": "A-LOAM scan-to-scan (laser_odom_to_init)"}[name]
    r = ate(a[:, 0], a[:, 1:4], g2)
    if r is None:
        print("%-44s too few samples" % lab)
    else:
        print("%-44s n=%d  ATE %.3f  max %.3f  end-point error %.3f m" % (lab, *r))
