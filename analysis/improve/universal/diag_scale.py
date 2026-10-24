"""Diagnosis only (uses GT): in 10 s windows inside VINS-valid stretches, path length of GT, LiDAR (GenZ) and VINS.
Answers: is the LiDAR the metric reference everywhere, and how biased / noisy is the VINS scale per sequence?"""
import sys, os, json, numpy as np
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
src = open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '').replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H)))
exec(src)
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
t = np.asarray(d["t"]); pa = np.array([a[1] for a in d["aft"]])
ok = np.array([v is not None for v in d["vins"]])
pv = np.array([v[1] if v is not None else [np.nan]*3 for v in d["vins"]])
g = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1); ing = (t >= gt_t[0]) & (t <= gt_t[-1])
def plen(P): return float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())
rows = []; i = 0
while i < len(t):
    j = np.searchsorted(t, t[i] + 10.0)
    if j >= len(t): break
    seg = slice(i, j + 1)
    if ok[seg].all() and ing[seg].all():
        dv = np.linalg.norm(np.diff(pv[seg], axis=0), axis=1)
        if dv.max() < 1.0:                       # no VINS jump / re-init inside
            Lg, La, Lv = plen(g[seg]), plen(pa[seg]), float(dv.sum())
            if Lg > 2.0: rows.append((Lg, La, Lv))
    i = j
R = np.array(rows)
if len(R):
    la, lv = np.log(R[:, 1] / R[:, 0]), np.log(R[:, 2] / R[:, 0])
    print(json.dumps(dict(log=name, seq=seq, windows=len(R), lidar_vs_gt_med=round(float(np.exp(np.median(la))), 3), lidar_vs_gt_rms=round(float(np.sqrt(np.mean(la**2))), 3),
        vins_vs_gt_med=round(float(np.exp(np.median(lv))), 3), vins_vs_gt_rms=round(float(np.sqrt(np.mean(lv**2))), 3),
        vins_vs_lidar_med=round(float(np.exp(np.median(lv - la))), 3))))
else:
    print(json.dumps(dict(log=name, seq=seq, windows=0)))
