"""Top-down trajectory figures for the paper (vector PDF).
fig_switch_seq.pdf : Multi Floor, Long Corridor, Farm (the sequences with Switch-SLAM values)
fig_other_seq.pdf  : Corridor02, Cave02, GEODE stairs
Each path is aligned to the ground truth with Umeyama SE(3), no scale; A-LOAM output and VINS-Mono alone are from the same run as DualChan-LVIO.
Needs the run logs of the session (vidlib and the data folders under the scratchpad)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/vid")
import vidlib as V
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

S = V.S; D = S + "/data"; K = S + "/f24cave/"
OUT = "/home/claude/switchslam-project/docs/paper/figures/"
C_GT, C_FUS, C_AL, C_VI = "#222222", "#1b7f4c", "#e08a00", "#c0392b"
plt.rcParams.update({"font.size": 7, "font.family": "serif", "axes.linewidth": 0.5, "pdf.fonttype": 42})
PUB = {"MF": "1.61 / 3.63", "LC": "2.42 / 5.09", "FARM": "0.38 / 1.10"}


def P3(d, pre):
    return d[[pre + "x", pre + "y", pre + "z"]].values.astype(float)


def stat(e):
    e = e[np.isfinite(e)]
    return np.sqrt(np.mean(e ** 2)), e.max()


def load(seq):
    if seq == "FARM":
        d = pd.read_csv(S + "/f26z/farm_f26/switching_log_v2_F26_fwdrgb_live1.csv")
        g = np.loadtxt(S + "/f26z/farm_f26/gt_f26.txt", comments="#")
        j = np.linalg.norm(np.diff(g[:, 1:3], axis=0), axis=1); k = int(np.argmax(j))
        tr = g[k + 1, 0] if j[k] > 0.5 else g[0, 0]
        g = g[g[:, 0] >= tr]; d = d[d.time >= max(tr, g[0, 0])].reset_index(drop=True)
        return d, (g[:, 0], g[:, 1:4])
    f, gtp = {"MF": ("MF", "gt/mf_gt_a.csv"), "LC": ("LC", "gt/lc_gt.txt"), "C02": ("C02", "gt/c02_gt.txt"),
              "CAVE": ("CAVE", "for_claude14/cave02_gt.txt"), "GEODE": ("GEODE", "geode/gt_stairs_alpha.txt")}[seq]
    d = pd.read_csv(K + "%s_switching_log_v2_F26_kf_run1.csv" % f)
    return d, V.load_gt_any(D + "/" + gtp)


def panel(ax, seq, name, pub=None, note=None):
    d, (gt_t, gt_p) = load(seq)
    t = d.time.values.astype(float); G = V.gt_on(t, gt_t, gt_p); ok = np.isfinite(G).all(1)
    ax.plot(G[ok, 0], G[ok, 1], color=C_GT, lw=1.1, zorder=2)
    lines = {}
    qf, ef = V.aligned(P3(d, "fused_"), G); lines["fus"] = stat(ef)
    qa, ea = V.aligned(P3(d, "aft_"), G); lines["al"] = stat(ea)
    ax.plot(qa[:, 0], qa[:, 1], color=C_AL, lw=0.7, zorder=3)
    vp = P3(d, "v_p"); good = np.isfinite(vp).all(1) & (np.abs(vp).max(1) < 1e5)
    vin = None
    if good.sum() > 100:
        v2 = vp.copy(); v2[~good] = np.nan
        qv, ev = V.aligned(v2, G); r = stat(ev)
        if r[0] < 25 and seq != "GEODE":
            ax.plot(qv[:, 0], qv[:, 1], color=C_VI, lw=0.7, zorder=3); vin = r
        else:
            vin = ("off", r[0])
    ax.plot(qf[:, 0], qf[:, 1], color=C_FUS, lw=0.9, zorder=4)
    f = "%.3f / %.3f" if seq == "FARM" else "%.2f / %.2f"
    l2 = ("DualChan-LVIO " + f + " m") % lines["fus"]
    l3 = ("Switch-SLAM, published: %s m" % pub) if pub else "Switch-SLAM: no published run"
    g2 = "%.2f / %.2f"
    l4 = ("A-LOAM " + g2) % lines["al"]
    if vin and vin[0] != "off":
        l4 += (", VINS " + g2) % vin
    elif vin:
        l4 += ", VINS off plot"
    ax.set_title(name + "\n" + l2 + "\n" + l3 + "\n" + l4, loc="left", fontsize=6.3, linespacing=1.25)
    ax.set_aspect("equal", adjustable="datalim"); ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.tick_params(labelsize=6, length=2, width=0.4)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    print(seq, "fus %.3f %.3f | A-LOAM %.3f %.3f" % (lines["fus"] + lines["al"]), vin, flush=True)


def figure(fname, items, legend_vins=True):
    fig, axs = plt.subplots(1, 3, figsize=(7.16, 3.0))
    for ax, it in zip(axs, items):
        panel(ax, *it)
    h = [Line2D([], [], color=C_GT, lw=1.1, label="ground truth"), Line2D([], [], color=C_FUS, lw=1.0, label="DualChan-LVIO"),
         Line2D([], [], color=C_AL, lw=0.8, label="A-LOAM output (same run)"),
         Line2D([], [], color=C_VI, lw=0.8, label="VINS-Mono alone (same run)")]
    fig.legend(handles=h, loc="lower center", ncol=4, frameon=False, fontsize=6.5, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(OUT + fname); plt.close(fig)


if __name__ == "__main__":
    figure("fig_switch_seq.pdf", [("MF", "(a) Multi Floor", PUB["MF"]), ("LC", "(b) Long Corridor", PUB["LC"]),
                                   ("FARM", "(c) Farm (Gazebo, about 80 m)", PUB["FARM"])])
    figure("fig_other_seq.pdf", [("C02", "(a) Corridor02"), ("CAVE", "(b) Cave02"), ("GEODE", "(c) GEODE stairs")])
