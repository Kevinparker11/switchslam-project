import os
import sys, json, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")).read())
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
def sc(p): return vt.ate(d["t"], np.asarray(p), gt_t, gt_p)[0]
CANDS = {  # stat, avg, n_min, threshold (= max of the same statistic on the 4 Multi Floor logs)
 "scale10":      ("scale", 10.0, 5, 0.252),
 "vec10":        ("vec", 10.0, 5, 0.463),
 "scaleSeg100":  ("scale", None, 100, 0.210),
 "scaleSeg200":  ("scale", None, 200, 0.156),
 "vecSeg200":    ("vec", None, 200, 0.247),
}
res = {}
for c, (stat, avg, nmin, thr) in CANDS.items():
    tr = fc4.VioConsistency(ref=thr, stat=stat, rule="gate", avg=avg, n_min=nmin)
    p, gam = run(sr, vt, fc4, d, K, adapt=tr)
    g = np.array([x for m, x in gam if m == "FUSED"])
    res[c] = (round(sc(p), 3), round(float(g.mean()) if len(g) else 0.0, 2))
print(json.dumps({"name": name, **res}))
