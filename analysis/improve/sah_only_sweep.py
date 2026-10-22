# Usage: python3 -I sah_only_sweep.py <label> <log> <keyframes.npz> <ground truth | -> <extrinsics yaml | ->
# Replays SAH on/off at several LiDAR-trust levels (W=I = GenZ + SAH only). Needs /home/claude/sah and /home/claude/fusion_v3 paths (edit sys.path).
import sys, os, numpy as np
seq, log, kf, gtp, ext = sys.argv[1:6]
if ext != "-": os.environ["EXTRINSIC_YAML"] = ext
sys.path.insert(0, "/home/claude/sah")
import sah_replay3 as sr, v2_tools as vt
d = vt.load_v2_log(log); K = sr.kf_normals(kf)
if gtp == "-": gt_t, gt_p = d["t"], np.array([p for _, p in d["aft"]])
else: gt_t, gt_p = vt.load_gt(gtp)
def sc(p): return vt.ate(d["t"], np.asarray(p), gt_t, gt_p)[0]
res = {}
for name, ct, cr in [("G17 (x1)", 3e-6, 5e-6), ("x10", 3e-5, 5e-5), ("x100", 3e-4, 5e-4), ("W=I", 1e1, 1e1)]:
    p0, _ = sr.run(d, K, sah_kw=None, c_t=ct, c_R=cr)
    p1, st = sr.run(d, K, sah_kw=dict(v3=6, bound_R=True), c_t=ct, c_R=cr)
    res[name] = (sc(p0), sc(p1))
print(seq, " | ".join("%s: noSAH %.3f SAH %.3f" % (k, a, b) for k, (a, b) in res.items()))
