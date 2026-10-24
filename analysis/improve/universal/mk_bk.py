"""Write a copy of a recording's log whose fused_* columns hold the replayed trajectory of one configuration (for run_backend.py)."""
import sys, os, numpy as np, pandas as pd
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read()); exec(open(os.path.join(ME, "configs.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
exec(open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '').replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H))))
name, cfg = sys.argv[1], sys.argv[2]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
p, _ = run(sr, vt, fc4, d, K, **CFG[cfg](fc4)); R = list(ROT)
L = d["df"].copy(); q = np.array([fc4.R_to_quat(r) for r in R])
L[["fused_x", "fused_y", "fused_z"]] = p; L[["fused_qx", "fused_qy", "fused_qz", "fused_qw"]] = q
os.makedirs(os.path.join(ME, "bk"), exist_ok=True); L.to_csv(os.path.join(ME, "bk", "%s_%s.csv" % (name, cfg)), index=False)
ent = [e for e in LOGS if e[0] == name][0]
print("%s|%s|%s|%s|%s" % (name, cfg, ent[3], ent[4], ent[5]))
