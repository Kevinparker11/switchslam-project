"""Generic trajectory video: top-down map + paths against ground truth, error panel, mode strip.
Same layout and colours as LC_run1_F20_vs_F22.mp4."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/switchslam-project/fusion_v4")
import v2_tools as vt
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
from scipy.spatial.transform import Rotation as Rot

S = "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad"
BG, FG, GRID = "#0f1115", "#e8eaed", "#2a2e36"
MODE_COL = {"INIT": "#555b66", "WARMUP": "#f2c14e", "FUSED": "#5aa9ff", "VO_FAIL": "#ff6b5e"}


def load_gt_any(path):
    """TUM text (with or without a comment line) or the SubT csv, via v2_tools; returns (t, p)"""
    try:
        return vt.load_gt(path)
    except Exception:
        a = np.loadtxt(path, comments="#")
        return a[:, 0], a[:, 1:4]


def gt_on(t, gt_t, gt_p):
    return np.stack([np.interp(t, gt_t, gt_p[:, i], left=np.nan, right=np.nan) for i in range(3)], 1)


def aligned(p, g):
    ok = np.isfinite(g).all(1) & np.isfinite(p).all(1)
    R, tr = vt.umeyama(p[ok], g[ok])
    q = p @ R.T + tr
    e = np.linalg.norm(q - g, axis=1); e[~ok] = np.nan
    return q, e


def kf_map(npz, gt_t, gt_p, per_kf=450, zclip=(8, 92), seed=0):
    z = np.load(npz)
    kt, kp, kn = z["t"], z["pose"], z["n"]; off = np.r_[0, np.cumsum(kn)]
    pts = z["pts"].astype(np.float32) * float(z["scale"])
    kg = gt_on(kt, gt_t, gt_p); ok = np.isfinite(kg).all(1)
    Rk, tk = vt.umeyama(kp[ok, :3], kg[ok])
    rng = np.random.default_rng(seed)
    cl, ct = [], []
    for i in range(len(kt)):
        P = pts[off[i]:off[i + 1]]
        if len(P) == 0:
            continue
        P = P[rng.choice(len(P), min(per_kf, len(P)), replace=False)]
        W = Rot.from_quat(kp[i, 3:7]).apply(P) + kp[i, :3]
        cl.append(W @ Rk.T + tk); ct.append(np.full(len(P), kt[i]))
    M = np.vstack(cl); MT = np.concatenate(ct)
    if zclip:
        lo, hi = np.percentile(M[:, 2], zclip); k = (M[:, 2] > lo) & (M[:, 2] < hi); M, MT = M[k], MT[k]
    return M, MT


def make(out, title, subtitle, t, mode, g, paths, footnote, M=None, MT=None, fps=20, dur=36.0, pad=12.0, note=None):
    """paths: list of (label, colour, aligned positions q, error e)"""
    WT = t - t[0]; T_END = WT[-1]; NF = int(fps * dur)
    frames = np.linspace(0, len(t) - 1, NF).astype(int)
    okg = np.isfinite(g).all(1)
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    ax = fig.add_axes([0.04, 0.08, 0.55, 0.82], facecolor=BG)
    ax1 = fig.add_axes([0.66, 0.50, 0.31, 0.38], facecolor=BG)
    ax2 = fig.add_axes([0.66, 0.30, 0.31, 0.06], facecolor=BG)
    for a in (ax, ax1, ax2):
        for s in a.spines.values(): s.set_color(GRID)
        a.tick_params(colors=FG, labelsize=8)
    ax.set_aspect("equal", adjustable="datalim")
    xs = [g[okg, 0]] + [q[np.isfinite(q).all(1), 0] for _, _, q, _ in paths]
    ys = [g[okg, 1]] + [q[np.isfinite(q).all(1), 1] for _, _, q, _ in paths]
    xs, ys = np.concatenate(xs), np.concatenate(ys)
    ax.set_xlim(np.percentile(xs, 0.2) - pad, np.percentile(xs, 99.8) + pad)
    ax.set_ylim(np.percentile(ys, 0.2) - pad, np.percentile(ys, 99.8) + pad)
    ax.set_xlabel("x (m)", color=FG, fontsize=9); ax.set_ylabel("y (m)", color=FG, fontsize=9)
    ax.set_title(subtitle, color=FG, fontsize=11, loc="left")
    sc = ax.scatter([], [], s=0.6, c="#6b7686", linewidths=0) if M is not None else None
    (lg,) = ax.plot([], [], color="#ffffff", lw=1.6, alpha=0.9, label="Ground truth")
    (dg,) = ax.plot([], [], "o", mfc="none", mec="#ffffff", ms=9)
    lines, dots, elines = [], [], []
    for lab, c, q, e in paths:
        (l,) = ax.plot([], [], color=c, lw=1.6, label=lab); (d,) = ax.plot([], [], "o", color=c, ms=6)
        lines.append(l); dots.append(d)
        ax1.plot(WT, e, color=c, lw=1, alpha=0.3)
        (el,) = ax1.plot([], [], color=c, lw=1.6); elines.append(el)
    ax.legend(loc="upper right", facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=8)
    ax1.set_title("Position error against ground truth (m)", color=FG, fontsize=10, loc="left")
    cur = ax1.axvline(0, color=FG, lw=0.8)
    fu = np.where(mode == "FUSED")[0]
    if len(fu):
        ax1.axvline(WT[fu[0]], color="#f2c14e", lw=1, ls="--")
        ax1.text(WT[fu[0]] + 0.01 * T_END, 0.92, "fusion starts", color="#f2c14e", fontsize=8, transform=ax1.get_xaxis_transform())
    emax = np.nanmax([np.nanpercentile(e, 99.5) for _, _, _, e in paths])
    ax1.set_xlim(0, T_END); ax1.set_ylim(0, emax * 1.1); ax1.grid(color=GRID, lw=0.5)
    ax2.set_title("Mode of the fusion node", color=FG, fontsize=9, loc="left")
    for m, c in MODE_COL.items():
        idx = (mode == m)
        if idx.any(): ax2.fill_between(WT, 0, 1, where=idx, color=c, step="mid", lw=0)
    ax2.set_xlim(0, T_END); ax2.set_yticks([]); ax2.set_xlabel("time (s)", color=FG, fontsize=8)
    cur2 = ax2.axvline(0, color=FG, lw=1)
    ax2.text(0.0, -1.9, "yellow = LiDAR-only warm-up   blue = fused   red = VINS lost", color=FG, fontsize=8, transform=ax2.transAxes)
    txt = fig.text(0.66, 0.16, "", color=FG, fontsize=10.5, va="top", family="monospace")
    fig.text(0.04, 0.955, title, color=FG, fontsize=12, weight="bold")
    fig.text(0.04, 0.012, footnote, color="#8b93a1", fontsize=8)
    if note:
        fig.text(0.66, 0.92, note, color="#8b93a1", fontsize=8)

    def upd(k):
        i = frames[k]; tt = t[i]
        if sc is not None:
            m = MT <= tt; sc.set_offsets(M[m][:, :2])
        j = okg[:i + 1]
        lg.set_data(g[:i + 1][j, 0], g[:i + 1][j, 1])
        if okg[i]: dg.set_data([g[i, 0]], [g[i, 1]])
        s = "t = %6.1f s   mode %s\n\n" % (WT[i], mode[i])
        for (lab, c, q, e), l, d, el in zip(paths, lines, dots, elines):
            jj = np.isfinite(q[:i + 1]).all(1)
            l.set_data(q[:i + 1][jj, 0], q[:i + 1][jj, 1])
            if np.isfinite(q[i]).all(): d.set_data([q[i, 0]], [q[i, 1]])
            el.set_data(WT[:i + 1], e[:i + 1])
            mx = np.nanmax(e[:i + 1]) if np.isfinite(e[:i + 1]).any() else 0.0
            s += "%-18s %6.2f m  max %6.2f\n" % (lab[:18], e[i] if np.isfinite(e[i]) else 0.0, mx)
        txt.set_text(s)
        cur.set_xdata([WT[i]]); cur2.set_xdata([WT[i]])

    w = FFMpegWriter(fps=fps, bitrate=3500, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-preset", "veryfast"])
    with w.saving(fig, out, 100):
        for k in range(NF):
            upd(k); w.grab_frame()
    # last frame as a still for the report
    fig.savefig(out.replace(".mp4", "_last.png"), facecolor=BG, dpi=150)
    plt.close(fig)
    print("done", out, flush=True)
