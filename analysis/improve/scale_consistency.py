# Ground-truth-free check: VINS-Mono vs LiDAR displacement over 10 s windows (median |ln ratio|). Edit the log paths at the bottom.
import sys, numpy as np, pandas as pd
# VINS-vs-LiDAR disagreement without ground truth: over 10 s windows (VINS healthy in both ends), compare the
# displacement vectors in the body-independent sense: |norm(dV) - norm(dL)| / max(norm(dL), 1 m) and the angle between them.
def stat(log, win=10.0):
    L = pd.read_csv(log); L = L[pd.to_numeric(L["time"], errors="coerce").notna()].reset_index(drop=True)
    t = L.time.values; A = L[["aft_x","aft_y","aft_z"]].values; V = L[["v_px","v_py","v_pz"]].values
    ok = np.isfinite(V).all(1) & (L["mode"].values == "FUSED")
    # VINS frame restarts on re-init; use only windows fully inside one FUSED stretch
    rel = []; 
    idx = np.where(ok)[0]
    for i in idx[::10]:
        j = np.searchsorted(t, t[i] + win)
        if j >= len(t) or not ok[i:j+1].all(): continue
        dL = A[j] - A[i]; dV = V[j] - V[i]
        if np.linalg.norm(dL) < 1.0: continue          # ignore (nearly) stationary windows
        rel.append(np.linalg.norm(dV) / np.linalg.norm(dL))   # path-length ratio (VINS scale vs LiDAR)
    rel = np.array(rel)
    return len(rel), np.median(np.abs(np.log(rel))) if len(rel) else float("nan"), np.percentile(np.abs(np.log(rel)), 90) if len(rel) else float("nan")
for name, p in [("Multi Floor", "/tmp/claude-0/g17/switching_log_v2_G17_kf_run1.csv"),
                ("Corridor02 0.33x", "lap/runs_corridor2_rate033_L_genz/switching_log_v2_G17_kf_run1.csv"),
                ("Cave02 0.5x", "lap/runs_cave02_rate05_L_genz/switching_log_v2_G17_kf_run1.csv"),
                ("GEODE (PC)", "geo1/runs_geode_P_genz/switching_log_v2_G17_kf_run1.csv")]:
    n, med, p90 = stat(p); print("%-18s windows %4d  median |ln(VINS/LiDAR displacement)| %.3f  p90 %.3f" % (name, n, med, p90))
