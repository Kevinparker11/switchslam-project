import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt
U = "/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6/"
for name, lp, gp, mf in (("Corridor02 (new G17 @1.0x)", "/tmp/claude-0/ho/switching_log_v2_G17_kf_run1.csv", U + "db62c9b7-corridor02_gt.txt", "C02"),
                         ("Cave02 (new G17 @1.0x)", "/tmp/claude-0/ho/cave_log.csv", "/home/claude/data_in14/cave02_gt.txt", "CAVE")):
    d = vt.load_v2_log(lp); L = d["df"]; t = d["t"]; gt_t, gt_p = vt.load_gt(gp)
    print("==", name)
    m = L["mode"].values; fails = int(((m == "VO_FAIL") & (np.r_[["x"], m[:-1]] != "VO_FAIL")).sum())
    print("  VO_FAIL episodes: %d (rows %d of %d); first FUSED +%.1f s" % (fails, (m == "VO_FAIL").sum(), len(m), L[L['mode'] == 'FUSED']['time'].min() - t[0]))
    # stationary start: displacement of GenZ vs ground truth in the first 40 s
    for T in (30, 60, 90):
        i = np.searchsorted(t, t[0] + T)
        g0, g1 = np.interp(t[0] + 1, gt_t, gt_p[:, 0]), None
        gp0 = np.array([np.interp(t[0] + 1, gt_t, gt_p[:, k]) for k in range(3)]); gp1 = np.array([np.interp(t[0] + T, gt_t, gt_p[:, k]) for k in range(3)])
        e0, e1 = d["aft"][1][1], d["aft"][i][1]
        print("  first %2d s: ground truth moved %.2f m | GenZ-LIO moved %.2f m" % (T, np.linalg.norm(gp1 - gp0), np.linalg.norm(e1 - e0)))
