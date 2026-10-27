import os
import sys, json, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")).read())
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
def sc(p): return vt.ate(d["t"], np.asarray(p), gt_t, gt_p)[0]
def fast(): return fc4.VioConsistency(ref=0.462, stat="scale", rule="gate", T=5.0, avg=5.0, d_min=0.5, n_min=5)
CANDS = {
 "seg200+fast5": lambda: fc4.VioChecks([fc4.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=200), fast()]),
 "seg100+fast5": lambda: fc4.VioChecks([fc4.VioConsistency(ref=0.210, stat="scale", rule="gate", avg=None, n_min=100), fast()]),
 "fast5 only":   fast,
}
res = {}
for c, mk in CANDS.items():
    p, gam = run(sr, vt, fc4, d, K, adapt=mk())
    g = np.array([x for m, x in gam if m == "FUSED"])
    res[c] = (round(sc(p), 3), round(float(g.mean()) if len(g) else 0.0, 2))
    p, _ = run(sr, vt, fc4, d, K, sah=False, adapt=mk()); res[c + " noSAH"] = (round(sc(p), 3), 0)
print(json.dumps({"name": name, **res}))
