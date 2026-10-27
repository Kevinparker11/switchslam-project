import sys, numpy as np
sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt
D = "/tmp/claude-0/g0mf/"
gt_t, gt_p = vt.load_gt(D + "ground_truth_path.csv")
logs = [D + "switching_log_v2_G0_kf_run%d.csv" % i for i in (1, 2, 3)]
d = [vt.load_v2_log(p) for p in logs]
for p, x in zip(logs, d):
    nh = sum(h is not None for h in x["H"]); print(p.split("/")[-1], len(x["t"]), "scans,", nh, "with H, frame", x["hess_frame"])
# information scale
tt = [np.trace(h[3:, 3:]) for h in d[0]["H"] if h is not None]
rr = [np.trace(h[:3, :3]) for h in d[0]["H"] if h is not None]
print("trace(H_tt) percentiles 5/50/95: %s | trace(H_RR): %s" % (np.percentile(tt, [5, 50, 95]), np.percentile(rr, [5, 50, 95])))
def sc(x, **kw):
    return vt.ate(x["t"], vt.replay(x, **kw)[0], gt_t, gt_p)[0]
g0 = [sc(x, c_t=0.0, mode="lidar") for x in d]
v0 = [sc(x, c_t=0.0, mode="vins") for x in d]
print("GenZ-LIO alone (G0):", np.round(g0, 3), "mean %.3f sd %.3f" % (np.mean(g0), np.std(g0, ddof=1)))
print("VINS-Mono alone (live, per run):", np.round(v0, 3), "mean %.3f" % np.mean(v0))
grid = [0, 1e-9, 3e-9, 1e-8, 3e-8, 1e-7, 3e-7, 1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]
print("\nC_T     ATE per run (soft Schur translation weight, no gate)      mean")
res = []
for c in grid:
    r = [sc(x, c_t=c, kth=1e9) for x in d]
    res.append((c, np.mean(r), r)); print("%-8g %s  %.3f" % (c, np.round(r, 3), np.mean(r)))
b = min(res, key=lambda z: z[1]); print("\nbest grid point:", b[0], "mean %.3f" % b[1])
