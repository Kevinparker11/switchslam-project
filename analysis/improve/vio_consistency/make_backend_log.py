import os
# writes a copy of the log whose fused_* columns hold the replayed trajectory of one configuration
import sys, json, numpy as np, pandas as pd
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")).read())
name, cfg = sys.argv[1], sys.argv[2]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
def seg(): return fc4.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=200)
CFG = {"G17": dict(), "G18": dict(adapt=seg()), "G19": dict(adapt=seg(), vio_scale_T=10.0), "SAHonly": dict(c_t=1e1, c_R=1e1)}
p, _ = run(sr, vt, fc4, d, K, **CFG[cfg]); R = list(ROT)
L = d["df"].copy()
q = np.array([fc4.R_to_quat(r) for r in R])
L[["fused_x", "fused_y", "fused_z"]] = p; L[["fused_qx", "fused_qy", "fused_qz", "fused_qw"]] = q
out = "bk/%s_%s.csv" % (name, cfg); L.to_csv(out, index=False)
print(name, cfg, "front ATE %.3f" % vt.ate(d["t"], p, gt_t, gt_p)[0], out)
