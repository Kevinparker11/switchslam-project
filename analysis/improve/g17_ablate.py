import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/sah"); sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt, sah_replay3 as sr
D = "/tmp/claude-0/g17/"
gt_t, gt_p = vt.load_gt("/tmp/claude-0/g0mf/ground_truth_path.csv")
log = D + "switching_log_v2_G17_kf_run1.csv"
d = vt.load_v2_log(log); L = d["df"]
print("modes:", L["mode"].value_counts().to_dict())
fu = L[L["mode"] == "FUSED"]
print("first FUSED at +%.1f s; SAH total applied %.2f deg; max step %.3f deg; rows with correction %d" % (
    fu["time"].min() - L["time"].min(), L["sah_total_deg"].iloc[-1], L["sah_corr_deg"].abs().max(), (L["sah_corr_deg"].abs() > 0).sum()))
print("wt (translation weights) FUSED rows, median per axis:", np.round(fu[["wt0", "wt1", "wt2"]].median().values, 3))
print("wR (rotation weights) FUSED rows, median per axis:", np.round(fu[["wR0", "wR1", "wR2"]].median().values, 3))
def sc(**kw): return vt.ate(d["t"], vt.replay(d, **kw)[0], gt_t, gt_p)[0]
live = vt.ate(d["t"], L[["fused_x", "fused_y", "fused_z"]].values, gt_t, gt_p)[0]
print("\nfrom this one live G17 run (same GenZ + VINS data in every row):")
print("  live G17 log (fused output)      %.3f" % live)
print("  GenZ-LIO alone (G0)              %.3f" % sc(c_t=0.0, mode="lidar"))
print("  VINS-Mono alone                  %.3f" % sc(c_t=0.0, mode="vins"))
print("  old rule G8 (c_T 1e-4, R=VINS)    %.3f" % sc(c_t=1e-4, kth=1e9))
print("  G9 (c_T 3e-6, c_R 5e-6)          %.3f" % sc(c_t=3e-6, c_R=5e-6, kth=1e9))
K = sr.kf_normals(D + "keyframes_G17_kf_run1.npz")
p, s = sr.run(d, K, sah_kw=dict(v3=6, bound_R=True), c_t=3e-6, c_R=5e-6)
print("  G17 replay (G9 + SAH)            %.3f" % vt.ate(d["t"], p, gt_t, gt_p)[0])
