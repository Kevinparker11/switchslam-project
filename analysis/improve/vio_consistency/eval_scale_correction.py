import os
import sys, json, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")).read())
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
def sc(p): return vt.ate(d["t"], np.asarray(p), gt_t, gt_p)[0]
def seg(): return fc4.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=200)
res = {}
for c, kw in {"sc10": dict(vio_scale_T=10.0), "sc5": dict(vio_scale_T=5.0), "sc2": dict(vio_scale_T=2.0),
              "sc10+seg": dict(vio_scale_T=10.0, adapt=seg())}.items():
    p, gam = run(sr, vt, fc4, d, K, **kw); res[c] = round(sc(p), 3)
print(json.dumps({"name": name, **res}))
