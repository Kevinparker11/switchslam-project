import sys, numpy as np, os
sys.path.insert(0, "/home/claude/sah"); sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt, sah_replay3 as sr
D = "/tmp/claude-0/g0mf/"
gt_t, gt_p = vt.load_gt(D + "ground_truth_path.csv")
runs = []
for i in (1, 2, 3):
    runs.append((vt.load_v2_log(D + "switching_log_v2_G0_kf_run%d.csv" % i), sr.kf_normals(D + "keyframes_G0_kf_run%d.npz" % i)))
kw = dict(v3=6, bound_R=True)
V = [("G0: GenZ-LIO alone", None, dict(c_t=0.0, c_R=0.0, t_warm=1e12)),
     ("F8 rule (R from VINS), c_T=1e-4", None, dict(c_t=1e-4)),
     ("F16 rule (F8 + SAH), c_T=1e-4", kw, dict(c_t=1e-4)),
     ("R&T Schur (c_T=3e-6, c_R=5e-6)", None, dict(c_t=3e-6, c_R=5e-6)),
     ("R&T Schur + SAH", kw, dict(c_t=3e-6, c_R=5e-6)),
     ("R&T Schur + SAH in WARMUP too", kw, dict(c_t=3e-6, c_R=5e-6, sah_modes=("FUSED", "WARMUP")))]
for name, k, x in V:
    r, ap = [], []
    for d, K in runs:
        p, s = sr.run(d, K, sah_kw=k, **x); r.append(vt.ate(d["t"], p, gt_t, gt_p)[0]); ap.append(s.get("acc", 0) if s else 0)
    print("%-36s %s | mean %.3f sd %.3f" % (name, " ".join("%.3f" % v for v in r), np.mean(r), np.std(r, ddof=1)), flush=True)
