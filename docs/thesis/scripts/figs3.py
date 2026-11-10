"""Figures for the F26 version of the thesis report (same style as figs.py)."""
import sys
sys.argv = [sys.argv[0]] + sys.argv[1:]
_args = sys.argv[1:]
sys.argv = [sys.argv[0]]
exec(open("/home/claude/switchslam-project/docs/thesis/scripts/figs.py").read().split('if __name__ == "__main__":')[0])


def seg(ax, pts, color="#333333", ls="-"):
    xs, ys = zip(*pts)
    ax.plot(xs[:-1], ys[:-1], color=color, lw=1.1, ls=ls)
    ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1, ls=ls, shrinkA=0, shrinkB=0))


O = S + "/rep/fig3/"
os.makedirs(O, exist_ok=True)
F = S + "/f24fam/"
C_F26 = "#1b7f4c"
GTP = {"MF": D + "/g0_multifloor/ground_truth_path.csv", "LC": D + "/gt/lc_gt.txt", "C02": D + "/gt/c02_gt.txt",
       "CAVE": D + "/for_claude14/cave02_gt.txt", "GEODE": D + "/geode/gt_stairs_alpha.txt"}


def fig_flow3():
    fig = plt.figure(figsize=(6.4, 5.6)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    steps = ["Study of LiDAR and visual degeneracy and of\nswitching-based LiDAR-visual-inertial SLAM",
             "Build the pipeline: A-LOAM + VINS-Mono in Docker, ROS Noetic, bags, Gazebo",
             "First-generation switching node and a study\nof 15 detection rules on Multi Floor",
             "Design the channels: Schur R, Schur T and the\norientation-tensor channel (additional T)",
             "Diagnose live failures and add safeguards\n(F20 to F24), each with a rule written first",
             "Choose A-LOAM's scan-to-map guess from the\ndegeneracy status of the scan (F26, final)",
             "Live runs on six sequences with frozen settings;\nreplays only for diagnosis",
             "Compare with VINS-Mono, A-LOAM, earlier versions and published Switch-SLAM"]
    ys = np.linspace(0.94, 0.06, len(steps))
    for i, (y, s) in enumerate(zip(ys, steps)):
        box(ax, 0.5, y, 0.9, 0.082, s.replace("\n", " "), fc="#eef3fa" if i % 2 == 0 else "#ffffff", fs=10.5)
        if i < len(steps) - 1:
            arrow(ax, 0.5, y - 0.048, 0.5, ys[i + 1] + 0.048)
    fig.savefig(O + "f3_1_flow.png"); plt.close(fig)


def fig_arch3():
    fig = plt.figure(figsize=(7.6, 5.2)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    box(ax, 0.10, 0.84, 0.16, 0.08, "VLP-16 LiDAR", "#f4f4f4", fs=10)
    box(ax, 0.10, 0.56, 0.16, 0.08, "Camera + IMU", "#f4f4f4", fs=10)
    box(ax, 0.335, 0.84, 0.21, 0.10, "A-LOAM\nscan-to-map, Hessian H", "#fdf0e3", fs=9.5)
    box(ax, 0.335, 0.56, 0.21, 0.10, "VINS-Mono\nVIO pose", "#fbe4e1", fs=9.5)
    box(ax, 0.335, 0.30, 0.21, 0.10, "Keyframe scan\nk-NN PCA: normals, edges", "#f4f4f4", fs=9.5)
    box(ax, 0.62, 0.90, 0.25, 0.075, "Channel R: Schur $S_{RR}$\n+ rotation check", "#e8f1fb", fs=9.5)
    box(ax, 0.62, 0.775, 0.25, 0.075, "Channel T: Schur $S_{tt}$", "#e8f1fb", fs=9.5)
    box(ax, 0.62, 0.56, 0.25, 0.10, "Safeguards: VIO-trust check,\nanchored handover,\nmapping-guess guard", "#f6f0dc", fs=9.2)
    box(ax, 0.62, 0.30, 0.25, 0.11, "Additional T (orientation tensor G):\ngmax rule on $S_{tt}$\n+ heading read-out (SAH)", "#e7f5ec", fs=9.2)
    box(ax, 0.90, 0.58, 0.16, 0.36, "Fusion\n\n$W_R$, $W_t$\n\n$\\Delta t = W_t\\Delta t_L$\n$+(I-W_t)\\Delta t_V$", "#ffffff", fs=9.5)
    box(ax, 0.90, 0.12, 0.16, 0.07, "Fused pose", "#ffffff", fs=10)
    box(ax, 0.335, 0.135, 0.25, 0.10, "Scan-to-map guess (F26):\nstatus of the scan Hessian, queue 5\nLiDAR step / blend / VINS step", "#eaf4ee", ec="#1b7f4c", fs=8.8)
    arrow(ax, 0.18, 0.84, 0.23, 0.84); arrow(ax, 0.18, 0.56, 0.23, 0.56)
    seg(ax, [(0.10, 0.80), (0.10, 0.30), (0.23, 0.30)])
    arrow(ax, 0.44, 0.86, 0.495, 0.90); arrow(ax, 0.44, 0.82, 0.495, 0.775)
    arrow(ax, 0.44, 0.56, 0.495, 0.56); arrow(ax, 0.44, 0.30, 0.495, 0.30)
    for y0, y1 in [(0.90, 0.72), (0.775, 0.66), (0.56, 0.56), (0.30, 0.46)]:
        arrow(ax, 0.745, y0, 0.82, y1)
    arrow(ax, 0.90, 0.40, 0.90, 0.155)
    seg(ax, [(0.82, 0.12), (0.62, 0.12), (0.62, 0.135), (0.465, 0.135)], color="#1b7f4c", ls="--")
    seg(ax, [(0.205, 0.135), (0.19, 0.135), (0.19, 0.80), (0.23, 0.80)], color="#1b7f4c", ls="--")
    ax.text(0.50, 0.02, "closed loop: the fused pose plus the chosen step is A-LOAM's initial guess for the next scan",
            fontsize=8.6, color="#1b7f4c", ha="center")
    fig.savefig(O + "f3_2_arch.png"); plt.close(fig)


def _gt(bag):
    return V.load_gt_any(GTP[bag])


def fig_weights3():
    d = pd.read_csv(F + "LC_switching_log_v2_F26_kf_run1.csv")
    t = d.time.values - d.time.values[0]; mode = d["mode"].astype(str).values
    fu = mode == "FUSED"
    fig, ax = plt.subplots(3, 1, figsize=(6.6, 5.4), sharex=True, gridspec_kw=dict(hspace=0.18))
    for a in ax:
        for m, c in MODEC.items():
            idx = mode == m
            if idx.any(): a.fill_between(t, 0, 1, where=idx, color=c, transform=a.get_xaxis_transform(), step="mid", lw=0)
    w0 = np.where(fu, d.wt0, np.nan); w2 = np.where(fu, d.wt2, np.nan)
    ax[0].plot(t, w0, color=C_F26, lw=0.7, label="smallest eigenvalue of $W_t$"); ax[0].plot(t, w2, color=C_SW, lw=0.7, label="largest eigenvalue of $W_t$")
    ax[0].set_ylabel("LiDAR weight"); ax[0].set_ylim(0, 1.02); ax[0].legend(loc="lower right", ncol=2, frameon=False)
    ax[1].plot(t, np.where(fu, d.ot_ratio, np.nan), color="#6c3483", lw=0.7)
    ax[1].set_ylabel("OT ratio\n$\\lambda'/\\lambda$")
    ax[2].plot(t, d.sah_total_deg, color=C_F20, lw=1.0)
    ax[2].set_ylabel("SAH heading\ncorrection (deg)"); ax[2].set_xlabel("time (s)")
    ax[0].set_title("Long Corridor, F26 live run 1 (shaded: yellow warm-up, blue fused)", loc="left")
    fig.align_ylabels(ax)
    fig.savefig(O + "f5_weights.png", bbox_inches="tight"); plt.close(fig)
    fu_w0 = d.wt0[fu]
    print("LC F26 wt0 median", np.nanmedian(fu_w0), "wt2 median", np.nanmedian(d.wt2[fu]), "ot ratio p50/p95", np.nanpercentile(d.ot_ratio[fu], [50, 95]), "sah min", d.sah_total_deg.min(), d.sah_total_deg.max())


def _panel(ax, ttl, d, gt, paths, loc="best"):
    gt_t, gt_p = gt
    t = d.time.values.astype(float); G = V.gt_on(t, gt_t, gt_p); ok = np.isfinite(G).all(1)
    ax.plot(G[ok, 0], G[ok, 1], color=C_GT, lw=1.2, label="Ground truth")
    for lab, c, pre in paths:
        q, e = V.aligned(P(d, pre), G)
        ax.plot(q[:, 0], q[:, 1], color=c, lw=0.9, label="%s (%.2f m)" % (lab, np.sqrt(np.nanmean(e ** 2))))
    ax.set_aspect("equal", adjustable="datalim"); ax.set_title(ttl, loc="left"); ax.legend(frameon=False, loc=loc, fontsize=8.5)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")


def fig_traj3():
    fig, axs = plt.subplots(2, 2, figsize=(7.0, 6.6))
    pv = [("F26", C_F26, "fused_"), ("VINS-Mono alone", C_VINS, "v_p")]
    _panel(axs[0, 0], "(a) Multi Floor, F26 live", pd.read_csv(F + "MF_switching_log_v2_F26_kf_run1.csv"), _gt("MF"), pv)
    _panel(axs[0, 1], "(b) Long Corridor, F26 live", pd.read_csv(F + "LC_switching_log_v2_F26_kf_run1.csv"), _gt("LC"), pv)
    _panel(axs[1, 0], "(c) Corridor02, F26 live run 1", pd.read_csv(F + "C02_switching_log_v2_F26_kf_run1.csv"), _gt("C02"), pv, loc="center")
    f = pd.read_csv(S + "/f26z/farm_f26/switching_log_v2_F26_fwdrgb_live1.csv"); g = np.loadtxt(S + "/f26z/farm_f26/gt_f26.txt", comments="#")
    j = np.linalg.norm(np.diff(g[:, 1:3], axis=0), axis=1); k = int(np.argmax(j))
    tr = g[k + 1, 0] if j[k] > 0.5 else g[0, 0]; g = g[g[:, 0] >= tr]
    f = f[f.time >= max(tr, g[0, 0])].reset_index(drop=True)
    _panel(axs[1, 1], "(d) Farm L route, F26 live", f, (g[:, 0], g[:, 1:4]), pv)
    fig.tight_layout(); fig.savefig(O + "f5_traj.png"); plt.close(fig)


def fig_heldout3():
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.4))
    pv = [("F26", C_F26, "fused_"), ("A-LOAM output", C_ALOAM, "aft_")]
    _panel(axs[0], "(a) Cave02, F26 live", pd.read_csv(F + "CAVE_switching_log_v2_F26_kf_run1.csv"), _gt("CAVE"), pv)
    _panel(axs[1], "(b) GEODE stairs, F26 live run 2", pd.read_csv(F + "GEODE_switching_log_v2_F26_kf_run2.csv"), _gt("GEODE"), pv)
    fig.tight_layout(); fig.savefig(O + "f5_heldout.png"); plt.close(fig)


def fig_switch3():
    seqs = ["Multi Floor", "Long Corridor", "Farm"]
    ours = [(0.54, 1.01), (2.10, 3.73), (0.290, 0.562)]
    sw = [(1.61, 3.63), (2.42, 5.09), (0.38, 1.10)]
    vins = [(1.32, 4.77), (4.99, 10.85), (4.31, 6.95)]
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.9))
    x = np.arange(3); w = 0.26
    for a, k, ttl in [(axs[0], 0, "ATE RMSE (m)"), (axs[1], 1, "Maximum error (m)")]:
        a.bar(x - w, [v[k] for v in vins], w, color="#e8a39b", edgecolor="#333", lw=0.5, label="VINS-Mono alone (same run)")
        a.bar(x, [v[k] for v in sw], w, color="#9db8de", edgecolor="#333", lw=0.5, label="Switch-SLAM (published)")
        a.bar(x + w, [v[k] for v in ours], w, color="#7cc49b", edgecolor="#333", lw=0.5, label="F26 (live, one run each)")
        a.set_xticks(x); a.set_xticklabels(seqs); a.set_title(ttl)
        a.set_ylim(0, 1.45 * max(max(v[k] for v in vins), max(v[k] for v in sw)))
    axs[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(O + "f5_switch.png"); plt.close(fig)


def copy_old():
    import shutil
    shutil.copy(S + "/rep/oldimg/p38-000.png", O + "f4_gt.png")
    shutil.copy(S + "/rep/oldimg/p47-000.png", O + "f5_rules.png")


if __name__ == "__main__":
    for fn in _args:
        globals()[fn]()
        print("ok", fn, flush=True)
