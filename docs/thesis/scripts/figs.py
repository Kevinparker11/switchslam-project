"""Print figures for the thesis report (white background, Times-like font)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/vid")
import vidlib as V
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib import font_manager as fm
from PIL import Image

for f in ["/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-regular.otf",
          "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-bold.otf",
          "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-italic.otf"]:
    try: fm.fontManager.addfont(f)
    except Exception: pass
plt.rcParams.update({"font.family": "TeX Gyre Termes", "font.size": 11, "axes.titlesize": 11, "axes.labelsize": 11,
                     "legend.fontsize": 9.5, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 200, "mathtext.fontset": "stix"})
S = V.S; D = S + "/data"; O = S + "/rep/fig/"
import os; os.makedirs(O, exist_ok=True)
C_F24, C_F20, C_VINS, C_ALOAM, C_GT, C_SW = "#1b7f4c", "#d9822b", "#c0392b", "#7f8c8d", "#111111", "#3b6fb6"
MODEC = {"WARMUP": "#f6e3a1", "FUSED": "#dbe9f7", "VO_FAIL": "#f5c6c0", "INIT": "#eeeeee"}


def P(df, pre):
    return df[[pre + "x", pre + "y", pre + "z"]].values.astype(float)


def box(ax, x, y, w, h, text, fc="#ffffff", ec="#333333", fs=10.5, bold=False):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.012,rounding_size=0.015", fc=fc, ec=ec, lw=1.1))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else "normal", wrap=True)


def arrow(ax, x0, y0, x1, y1, text=None, fs=9):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color="#333333", lw=1.1, shrinkA=0, shrinkB=0))
    if text:
        ax.text((x0 + x1) / 2 + 0.01, (y0 + y1) / 2, text, fontsize=fs, ha="left", va="center", color="#333333")


def fig_flow():
    fig = plt.figure(figsize=(5.6, 7.4)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    steps = ["Study of LiDAR and visual degeneracy and of\nswitching-based LiDAR-visual-inertial SLAM",
             "Build the pipeline: A-LOAM + VINS-Mono in Docker,\nROS Noetic, bag playback and Gazebo farm",
             "Design the channels: Schur R, Schur T and the\northogonal-tensor channel (additional T)",
             "Replay the logged runs through the fusion node,\nfreeze the constants on development data",
             "Diagnose live failures and add safeguards\n(F20 to F24), each with a rule written first",
             "Live runs on bags and in Gazebo; held-out\nsequences scored with frozen settings",
             "Compare with VINS-Mono, A-LOAM, earlier versions\nand the published Switch-SLAM results"]
    steps[2] = "Design the channels: Schur R, Schur T and the\norientation-tensor channel (additional T)"
    ys = np.linspace(0.93, 0.07, len(steps))
    for i, (y, s) in enumerate(zip(ys, steps)):
        box(ax, 0.5, y, 0.86, 0.095, s, fc="#eef3fa" if i % 2 == 0 else "#ffffff", fs=10.5)
        if i < len(steps) - 1:
            arrow(ax, 0.5, y - 0.05, 0.5, ys[i + 1] + 0.05)
    fig.savefig(O + "f3_1_flow.png"); plt.close(fig)


def fig_arch():
    fig = plt.figure(figsize=(7.6, 5.2)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    box(ax, 0.13, 0.86, 0.2, 0.09, "VLP-16 LiDAR", "#f4f4f4"); box(ax, 0.13, 0.62, 0.2, 0.09, "Camera + IMU", "#f4f4f4")
    box(ax, 0.40, 0.86, 0.22, 0.11, "A-LOAM\nscan-to-map + Hessian H", "#fdf0e3"); box(ax, 0.40, 0.62, 0.22, 0.11, "VINS-Mono\nVIO pose", "#fbe4e1")
    arrow(ax, 0.23, 0.86, 0.29, 0.86); arrow(ax, 0.23, 0.62, 0.29, 0.62)
    box(ax, 0.13, 0.38, 0.2, 0.11, "Keyframe scan\nk-NN PCA normals", "#f4f4f4"); arrow(ax, 0.13, 0.815, 0.13, 0.435)
    # channels
    box(ax, 0.66, 0.90, 0.24, 0.075, "Channel R: Schur S$_{RR}$\n+ rotation check", "#e8f1fb", fs=9.5)
    box(ax, 0.66, 0.77, 0.24, 0.075, "Channel T: Schur S$_{tt}$\nweight W$_t$", "#e8f1fb", fs=9.5)
    box(ax, 0.66, 0.42, 0.26, 0.11, "Additional T: orientation tensor G\ncap/raise of S$_{tt}$ (gmax)\n+ heading read-out (SAH)", "#e7f5ec", fs=9.5)
    arrow(ax, 0.51, 0.88, 0.54, 0.90); arrow(ax, 0.51, 0.84, 0.54, 0.77); arrow(ax, 0.23, 0.38, 0.53, 0.40)
    box(ax, 0.66, 0.60, 0.26, 0.10, "Safeguards: VIO-trust check,\nanchored handover, guess guard", "#f6f0dc", fs=9.5)
    arrow(ax, 0.51, 0.62, 0.53, 0.60)
    box(ax, 0.66, 0.16, 0.30, 0.10, "Fused increment\n$\\Delta t = W_t \\Delta t_L + (I-W_t)\\Delta t_V$", "#ffffff", fs=10, bold=False)
    for y0 in (0.865, 0.735, 0.55, 0.365):
        arrow(ax, 0.80 if y0 > 0.5 else 0.80, y0, 0.83, y0)
    ax.plot([0.83, 0.83], [0.365, 0.865], color="#333333", lw=1.1)
    arrow(ax, 0.83, 0.40, 0.83, 0.21)
    ax.annotate("", xy=(0.40, 0.80), xytext=(0.51, 0.16), arrowprops=dict(arrowstyle="-|>", color="#1b7f4c", lw=1.2, ls="--",
                connectionstyle="arc3,rad=-0.35"))
    ax.text(0.30, 0.22, "fused pose + VINS motion\n= initial guess of A-LOAM\n(closed loop)", fontsize=9, color="#1b7f4c", ha="center")
    box(ax, 0.92, 0.04, 0.14, 0.06, "fused pose", "#ffffff", fs=9.5)
    arrow(ax, 0.81, 0.13, 0.88, 0.07)
    fig.savefig(O + "f3_2_arch.png"); plt.close(fig)


def fig_weights():
    d = pd.read_csv(S + "/f24bag/LC_switching_log_v2_F24_kf_run1.csv")
    t = d.time.values - d.time.values[0]; mode = d["mode"].astype(str).values
    fu = mode == "FUSED"
    fig, ax = plt.subplots(3, 1, figsize=(6.6, 5.4), sharex=True, gridspec_kw=dict(hspace=0.18))
    for a in ax:
        for m, c in MODEC.items():
            idx = mode == m
            if idx.any(): a.fill_between(t, 0, 1, where=idx, color=c, transform=a.get_xaxis_transform(), step="mid", lw=0)
    w0 = np.where(fu, d.wt0, np.nan); w2 = np.where(fu, d.wt2, np.nan)
    ax[0].plot(t, w0, color=C_F24, lw=0.7, label="smallest eigenvalue of $W_t$"); ax[0].plot(t, w2, color=C_SW, lw=0.7, label="largest eigenvalue of $W_t$")
    ax[0].set_ylabel("LiDAR weight"); ax[0].set_ylim(0, 1.02); ax[0].legend(loc="lower right", ncol=2, frameon=False)
    ax[1].plot(t, np.where(fu, d.ot_ratio, np.nan), color="#6c3483", lw=0.7)
    ax[1].set_ylabel("OT ratio\n$\\lambda'/\\lambda$")
    ax[2].plot(t, d.sah_total_deg, color=C_F20, lw=1.0)
    ax[2].set_ylabel("SAH heading\ncorrection (deg)"); ax[2].set_xlabel("time (s)")
    ax[0].set_title("Long Corridor, F24 live run 1 (shaded: yellow warm-up, blue fused)", loc="left")
    fig.align_ylabels(ax)
    fig.savefig(O + "f3_3_weights.png", bbox_inches="tight"); plt.close(fig)


def fig_setup():
    fig = plt.figure(figsize=(7.4, 4.4)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((0.02, 0.05), 0.96, 0.82, fill=False, ec="#555555", lw=1, ls="--"))
    ax.text(0.03, 0.83, "Laptop: Ubuntu host, Docker network vins_bridge (ROS master 172.17.0.10)", fontsize=9.5, color="#555555")
    box(ax, 0.17, 0.62, 0.25, 0.16, "Bag player\n(ros:noetic, throw-away)\nrosbag play at 0.33-0.5x", "#f4f4f4", fs=9.5)
    box(ax, 0.17, 0.30, 0.25, 0.14, "Gazebo farm world\nHusky, VLP-16, camera, IMU\n(alternative source)", "#f4f4f4", fs=9.5)
    box(ax, 0.50, 0.66, 0.26, 0.17, "switchslam_gpu_v2\nroscore, A-LOAM,\nfusion_node_v2 (R, T, OT)", "#e8f1fb", fs=9.5)
    box(ax, 0.50, 0.30, 0.26, 0.14, "vinsmono_test\nVINS-Mono feature tracker\n+ estimator", "#fbe4e1", fs=9.5)
    box(ax, 0.83, 0.66, 0.24, 0.17, "RViz viewer\n(ros:noetic-desktop-full)\nmap, GT, fused path", "#e7f5ec", fs=9.5)
    box(ax, 0.83, 0.30, 0.24, 0.14, "Logs: switching_log_v2.csv,\nkeyframes.npz, node output\n-> ATE scoring", "#f6f0dc", fs=9.5)
    arrow(ax, 0.295, 0.64, 0.37, 0.66, "LiDAR"); arrow(ax, 0.295, 0.58, 0.37, 0.33, "camera, IMU")
    arrow(ax, 0.295, 0.33, 0.37, 0.60)
    arrow(ax, 0.50, 0.37, 0.50, 0.575, "/vins_estimator/odometry")
    arrow(ax, 0.63, 0.66, 0.71, 0.66); arrow(ax, 0.63, 0.62, 0.71, 0.33)
    fig.savefig(O + "f4_1_setup.png"); plt.close(fig)


def placeholder(name, text, w=6.4, h=3.4):
    fig = plt.figure(figsize=(w, h)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.add_patch(Rectangle((0.01, 0.02), 0.98, 0.96, fc="#f2f2f2", ec="#888888", lw=1.2, ls="--"))
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=12, color="#555555")
    fig.savefig(O + name); plt.close(fig)


def rviz_grid():
    fs = ["rviz_MF.png", "rviz_LC.png", "rviz_C02.png", "rviz_CAVE.png"]
    ims = [Image.open(S + "/vid/" + f).convert("RGB").resize((1200, 750)) for f in fs]
    G = Image.new("RGB", (2410, 1510), (255, 255, 255))
    for i, im in enumerate(ims): G.paste(im, ((i % 2) * 1210, (i // 2) * 760))
    G.save(O + "f4_3_rviz.png")


def traj_panels():
    fig, axs = plt.subplots(2, 2, figsize=(7.0, 6.6))
    cases = []
    d = pd.read_csv(S + "/f24bag/MF_switching_log_v2_F24_kf_run1.csv"); gt = V.load_gt_any(D + "/gt/mf_gt_a.csv")
    cases.append(("(a) Multi Floor, F24 live", d, gt, [("F24", C_F24, "fused_"), ("VINS-Mono alone", C_VINS, "v_p")]))
    d = pd.read_csv(S + "/f24bag/LC_switching_log_v2_F24_kf_run1.csv"); gt = V.load_gt_any(D + "/gt/lc_gt.txt")
    cases.append(("(b) Long Corridor, F24 live", d, gt, [("F24", C_F24, "fused_"), ("VINS-Mono alone", C_VINS, "v_p")]))
    B = pd.read_csv(S + "/hb/out/C021/switching_log_v2_F21a.csv"); A = pd.read_csv(S + "/hb/out/C021/switching_log_v2_F20.csv")
    B = B.assign(f20_x=A.fused_x.values, f20_y=A.fused_y.values, f20_z=A.fused_z.values)
    gt = V.load_gt_any(D + "/gt/c02_gt.txt")
    cases.append(("(c) Corridor02, F24 and F20 replay", B, gt, [("F24", C_F24, "fused_"), ("F20", C_F20, "f20_")]))
    f = pd.read_csv(S + "/farm24/farm_f24/switching_log_v2_F24_farm_live1.csv"); g = np.loadtxt(S + "/farm24/farm_f24/gt_live.txt", comments="#")
    f = f[f.time >= g[0, 0]].reset_index(drop=True)
    cases.append(("(d) Farm L route, F24 live", f, (g[:, 0], g[:, 1:4]), [("F24", C_F24, "fused_"), ("VINS-Mono alone", C_VINS, "v_p")]))
    for ax, (ttl, d, (gt_t, gt_p), paths) in zip(axs.ravel(), cases):
        t = d.time.values.astype(float); G = V.gt_on(t, gt_t, gt_p); ok = np.isfinite(G).all(1)
        ax.plot(G[ok, 0], G[ok, 1], color=C_GT, lw=1.2, label="Ground truth")
        for lab, c, pre in paths:
            q, e = V.aligned(P(d, pre), G)
            ax.plot(q[:, 0], q[:, 1], color=c, lw=0.9, label="%s (%.2f m)" % (lab, np.sqrt(np.nanmean(e ** 2))))
        ax.set_aspect("equal", adjustable="datalim"); ax.set_title(ttl, loc="left"); ax.legend(frameon=False, loc="best", fontsize=8.5)
        ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    fig.tight_layout(); fig.savefig(O + "f5_1_traj.png"); plt.close(fig)


def ablation_bars():
    cfg = ["F8", "F16", "F20", "F21", "F22", "F23"]
    ate = {"MF": [0.626, 0.560, 0.558, 0.583, 0.506, 0.531], "LC": [4.533, 1.983, 2.010, 1.970, 1.743, 1.703], "C02": [2.119, 1.709, 1.710, 1.571, 1.709, 1.569]}
    mx = {"MF": [1.33, 1.06, 1.06, 1.10, 0.99, 1.03], "LC": [12.89, 5.42, 5.48, 5.39, 3.57, 3.51], "C02": [3.77, 2.85, 2.87, 2.65, 2.87, 2.64]}
    names = {"MF": "Multi Floor", "LC": "Long Corridor", "C02": "Corridor02"}
    sw = {"MF": (1.61, 3.63), "LC": (2.42, 5.09)}
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.9))
    cols = ["#b0b0b0", "#8fb3d9", "#d9822b", "#e2b07a", "#1b7f4c", "#7cc49b"]
    for ax, k in zip(axs, ["MF", "LC", "C02"]):
        x = np.arange(len(cfg))
        ax.bar(x, ate[k], color=cols, edgecolor="#333333", lw=0.5)
        ax.plot(x, mx[k], "k_", ms=12, mew=1.4, label="max error")
        if k in sw:
            ax.axhline(sw[k][0], color=C_SW, lw=1, ls="--", label="Switch-SLAM RMSE")
        ax.set_xticks(x); ax.set_xticklabels(cfg, rotation=45); ax.set_title(names[k])
        if k == "LC": ax.set_ylim(0, 6.2); ax.text(0.3, 5.75, "F8 max\n12.9", fontsize=8, ha="center")
    axs[0].set_ylabel("ATE RMSE (m), bars; max (m), dashes")
    h, l = axs[0].get_legend_handles_labels()
    fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.legend(h, l, loc="lower center", ncol=2, frameon=False, fontsize=8.5)
    fig.savefig(O + "f5_2_ablation.png"); plt.close(fig)


def lc_err():
    d = pd.read_csv(S + "/f24bag/LC_switching_log_v2_F24_kf_run1.csv"); gt_t, gt_p = V.load_gt_any(D + "/gt/lc_gt.txt")
    t = d.time.values.astype(float); G = V.gt_on(t, gt_t, gt_p)
    q, e = V.aligned(P(d, "fused_"), G); qv, ev = V.aligned(P(d, "v_p"), G)
    mode = d["mode"].astype(str).values; tt = t - t[0]
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    for m, c in MODEC.items():
        idx = mode == m
        if idx.any(): ax.fill_between(tt, 0, 1, where=idx, color=c, transform=ax.get_xaxis_transform(), step="mid", lw=0)
    ax.plot(tt, ev, color=C_VINS, lw=0.8, label="VINS-Mono alone (5.61 m)")
    ax.plot(tt, e, color=C_F24, lw=1.1, label="F24 (2.12 m)")
    i = np.nanargmax(e); ax.plot(tt[i], e[i], "o", color=C_F24); ax.annotate("max %.2f m at %.1f s\n(LiDAR-only warm-up)" % (e[i], tt[i]), (tt[i], e[i]), (tt[i] + 30, e[i] + 3), fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.7))
    ax.axhline(5.09, color=C_SW, lw=1, ls="--", label="Switch-SLAM max 5.09 m")
    ax.set_xlabel("time (s)"); ax.set_ylabel("position error (m)"); ax.set_ylim(0, 14); ax.legend(frameon=False, ncol=3, fontsize=8.5, loc="upper right")
    fig.tight_layout(); fig.savefig(O + "f5_3_lc_err.png"); plt.close(fig)


def farm_err():
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    for tag, path, c in [("F23", S + "/farm23/farm_f23/switching_log_v2_F23_farm_live1.csv", C_F20),
                         ("F24", S + "/farm24/farm_f24/switching_log_v2_F24_farm_live1.csv", C_F24)]:
        d = pd.read_csv(path); g = np.loadtxt(path.rsplit("/", 1)[0] + "/gt_live.txt", comments="#")
        j = np.linalg.norm(np.diff(g[:, 1:3], axis=0), axis=1); k = int(np.argmax(j))
        tr = g[k + 1, 0] if j[k] > 0.5 else g[0, 0]; g = g[g[:, 0] >= tr]
        d = d[d.time >= max(tr, g[0, 0])].reset_index(drop=True)
        t = d.time.values.astype(float); G = V.gt_on(t, g[:, 0], g[:, 1:4])
        q, e = V.aligned(P(d, "fused_"), G)
        ax.plot(t - t[0], e, color=c, lw=1.0, label="%s (RMSE %.3f m, max %.2f m)" % (tag, np.sqrt(np.nanmean(e ** 2)), np.nanmax(e)))
        print(tag, np.sqrt(np.nanmean(e ** 2)), np.nanmax(e))
    ax.axhline(1.10, color=C_SW, lw=1, ls="--", label="Switch-SLAM max 1.10 m")
    ax.set_xlabel("time after the robot reset / first ground-truth sample (s)"); ax.set_ylabel("position error (m)")
    ax.legend(frameon=False, fontsize=8.5); fig.tight_layout(); fig.savefig(O + "f5_4_farm.png"); plt.close(fig)


def sw_bars():
    seqs = ["Multi Floor", "Long Corridor", "Farm"]
    ours = [(0.455, 0.92), (2.007, 4.80), (0.657, 0.897)]
    sw = [(1.61, 3.63), (2.42, 5.09), (0.38, 1.10)]
    vins = [(1.32, 4.77), (5.61, 13.01), (2.067, 3.306)]
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.9))
    x = np.arange(3); w = 0.26
    for a, k, ttl in [(axs[0], 0, "ATE RMSE (m)"), (axs[1], 1, "Maximum error (m)")]:
        a.bar(x - w, [v[k] for v in vins], w, color="#e8a39b", edgecolor="#333", lw=0.5, label="VINS-Mono alone (run 1 of the same sequence)")
        a.bar(x, [v[k] for v in sw], w, color="#9db8de", edgecolor="#333", lw=0.5, label="Switch-SLAM (published)")
        a.bar(x + w, [v[k] for v in ours], w, color="#7cc49b", edgecolor="#333", lw=0.5, label="F24 (live; Long Corridor: mean of 3 runs)")
        a.set_xticks(x); a.set_xticklabels(seqs); a.set_title(ttl)
    axs[0].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(O + "f5_5_switch.png"); plt.close(fig)


def heldout():
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.3))
    d = pd.read_csv(D + "/for_claude14/switching_log_v2_F16_run1.csv"); gt_t, gt_p = V.load_gt_any(D + "/for_claude14/cave02_gt.txt")
    t = d.time.values.astype(float); G = V.gt_on(t, gt_t, gt_p); ok = np.isfinite(G).all(1)
    q, e = V.aligned(P(d, "fused_"), G)
    axs[0].plot(G[ok, 0], G[ok, 1], color=C_GT, lw=1.1, label="Ground truth"); axs[0].plot(q[:, 0], q[:, 1], color=C_F20, lw=0.9, label="F16 live (%.2f m)" % np.sqrt(np.nanmean(e ** 2)))
    axs[0].set_title("(a) Cave02", loc="left")
    d = pd.read_csv(D + "/geode/switching_log_v2_F16_kf_run1.csv"); gt_t, gt_p = V.load_gt_any(D + "/geode/gt_stairs_alpha.txt")
    t = d.time.values.astype(float); G = V.gt_on(t, gt_t, gt_p); ok = np.isfinite(G).all(1)
    q, e = V.aligned(P(d, "fused_"), G); qa, ea = V.aligned(P(d, "aft_"), G)
    axs[1].plot(G[ok, 0], G[ok, 1], color=C_GT, lw=1.1, label="Ground truth"); axs[1].plot(q[:, 0], q[:, 1], color=C_F20, lw=0.9, label="F16 live (%.1f m)" % np.sqrt(np.nanmean(e ** 2)))
    axs[1].plot(qa[:, 0], qa[:, 1], color=C_ALOAM, lw=0.9, label="A-LOAM output (%.1f m)" % np.sqrt(np.nanmean(ea ** 2)))
    axs[1].set_title("(b) GEODE stairs", loc="left")
    for a in axs:
        a.set_aspect("equal", adjustable="datalim"); a.legend(frameon=False, fontsize=8.5); a.set_xlabel("x (m)"); a.set_ylabel("y (m)")
    fig.tight_layout(); fig.savefig(O + "f5_6_heldout.png"); plt.close(fig)


if __name__ == "__main__":
    for fn in sys.argv[1:]:
        globals()[fn]()
        print("ok", fn, flush=True)
