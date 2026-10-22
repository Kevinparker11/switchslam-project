import sys, numpy as np
sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt
U = "/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6/"
H = "/tmp/claude-0/ho/"
SEQ = {"Corridor02": (H + "switching_log_v2_G17_kf_run1.csv", U + "db62c9b7-corridor02_gt.txt", 1.71, 4.03),
       "Cave02": (H + "cave_log.csv", "/home/claude/data_in14/cave02_gt.txt", 4.40, 10.25)}
def errs(t, p, gt_t, gt_p):
    m = (t >= gt_t[0]) & (t <= gt_t[-1]) & np.isfinite(p).all(1)
    g = np.stack([np.interp(t[m], gt_t, gt_p[:, i]) for i in range(3)], 1)
    R, tr = vt.umeyama(p[m], g); return t[m], np.linalg.norm(p[m] @ R.T + tr - g, axis=1)
for name, (lp, gp, f16, vins_old) in SEQ.items():
    print("=" * 100, "\n", name, "\n", "=" * 100, sep="")
    gt_t, gt_p = vt.load_gt(gp); d = vt.load_v2_log(lp); L = d["df"]; t = d["t"]
    print("GT %d poses, %.0f..%.0f ; log %d rows, %.0f..%.0f ; overlap ok" % (len(gt_t), gt_t[0], gt_t[-1], len(t), t[0], t[-1]))
    print("modes:", L["mode"].value_counts().to_dict(), "| first FUSED +%.1f s" % ((L[L["mode"] == "FUSED"]["time"].min() - t[0]) if (L["mode"] == "FUSED").any() else float("nan")))
    fused = L[["fused_x", "fused_y", "fused_z"]].values
    genz = np.array([a[1] for a in d["aft"]]); vp = np.array([v[1] if v is not None else [np.nan]*3 for v in d["vins"]])
    ests = {"GenZ-LIO alone (aft pose)": genz, "VINS-Mono alone (live)": vp, "fused output (live G17)": fused,
            "replay G9 (R,T Schur)": vt.replay(d, c_t=3e-6, c_R=5e-6, kth=1e9)[0], "replay old rule G8": vt.replay(d, c_t=1e-4, kth=1e9)[0]}
    mask = None
    print("\n%-28s %8s %8s %12s" % ("estimator", "ATE", "max", "RPE 10 s"))
    for k, p in ests.items():
        a, mx = vt.ate(t, p, gt_t, gt_p); r = vt.rpe(t, p, gt_t, gt_p, np.isfinite(p).all(1), horizon=10.0)
        print("%-28s %8.2f %8.2f %12.3f" % (k, a, mx, r))
    print("(master F16 ATE %.2f, master VINS-Mono alone %.2f)" % (f16, vins_old))
    print("\nerror over time (m), every ~10 %% of the run:")
    cols = ["GenZ alone", "VINS alone", "fused"]
    print("  t(s)  " + "  ".join("%10s" % c for c in cols))
    E = {c: errs(t, p, gt_t, gt_p) for c, p in zip(cols, (genz, vp, fused))}
    te = E["GenZ alone"][0]
    for q in np.linspace(0.05, 0.99, 10):
        tt = te[0] + q * (te[-1] - te[0])
        print("  %5.0f " % (tt - te[0]) + "  ".join("%10.2f" % np.interp(tt, *E[c]) for c in cols))
    fu = L[L["mode"] == "FUSED"]
    print("FUSED medians: wt %s  wR %s  | SAH total %.2f deg" % (np.round(fu[["wt0", "wt1", "wt2"]].median().values, 3), np.round(fu[["wR0", "wR1", "wR2"]].median().values, 3), L["sah_total_deg"].iloc[-1]))
    # information scale vs Multi Floor
    tt_ = [np.trace(h[3:, 3:]) for h in d["H"] if h is not None]; rr_ = [np.trace(h[:3, :3]) for h in d["H"] if h is not None]
    print("trace(H_tt) pct 5/50/95:", np.round(np.percentile(tt_, [5, 50, 95]) / 1e6, 2), "e6   trace(H_RR):", np.round(np.percentile(rr_, [5, 50, 95]) / 1e6, 1), "e6   (Multi Floor: tt 3.5/8.2/19.9 e6, RR 70/1580/5050 e6)")
