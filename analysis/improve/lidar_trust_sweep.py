# Usage: python3 -I lidar_trust_sweep.py <label> <G-stack switching log> <ground truth | -> <extrinsics yaml | ->
# Replays the fusion at LiDAR-trust scales x0.01...x10000 of the frozen G9 weights (c_T 3e-6, c_R 5e-6); "-" as ground truth = proxy: GenZ path.
# Diagnostic only (22 Oct 2026): run on held-out logs, so not a test of anything.
import sys, os, numpy as np
seq, log, gtp, ext = sys.argv[1:5]
if ext != "-": os.environ["EXTRINSIC_YAML"] = ext
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fusion_v4"))
import v2_tools as vt
d = vt.load_v2_log(log)
if gtp == "-":   # proxy: GenZ-LIO (aft) path as reference
    gt_t, gt_p = d["t"], np.array([p for _, p in d["aft"]])
else:
    gt_t, gt_p = vt.load_gt(gtp)
def sc(p): return vt.ate(d["t"], np.asarray(p), gt_t, gt_p)[0]
L = d["df"]
live = sc(L[["fused_x","fused_y","fused_z"]].values)
row = {"live": live, "GenZ alone": sc(vt.replay(d, c_t=0.0, mode="lidar")[0]), "VINS alone": sc(vt.replay(d, c_t=0.0, mode="vins")[0])}
for s in [0.01, 0.1, 1, 10, 100, 1000, 10000]:
    row["x%g" % s] = sc(vt.replay(d, c_t=3e-6*s, c_R=5e-6*s, kth=1e9)[0])
print(seq, " ".join("%s=%.3f" % (k, v) for k, v in row.items()))
