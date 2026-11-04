"""RViz-style still renders (same colours as viz/live.rviz): dark background, 10 m grid, map coloured by height
(AxisColor), ground truth white, A-LOAM mapped path orange, fused path green. Orbit camera, perspective projection."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/vid")
import vidlib as V
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm

S = V.S; D = S + "/data"
BG = (15 / 255, 17 / 255, 21 / 255); GRIDC = (70 / 255, 74 / 255, 82 / 255)
GT_C, AFT_C, FUS_C = "#ffffff", (1.0, 170 / 255, 40 / 255), (79 / 255, 209 / 255, 139 / 255)


def cam(center, dist, yaw, pitch, fov=50.0):
    y, p = np.radians(yaw), np.radians(pitch)
    eye = center + dist * np.array([np.cos(p) * np.cos(y), np.cos(p) * np.sin(y), np.sin(p)])
    f = center - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    Rcw = np.stack([r, u, -f])          # camera axes (x right, y up, z back)
    fpx = 0.5 / np.tan(np.radians(fov) / 2)
    def proj(X):
        Xc = (X - eye) @ Rcw.T
        z = -Xc[:, 2]
        ok = z > 0.5
        return np.stack([fpx * Xc[:, 0] / np.maximum(z, 1e-6), fpx * Xc[:, 1] / np.maximum(z, 1e-6)], 1), z, ok
    return proj


def render(out, title, M, paths, gt, view, grid_z=None, legend_extra=None):
    allp = np.vstack([gt[np.isfinite(gt).all(1)]] + ([M] if M is not None else []))
    center = np.median(allp, 0) if view.get("center") is None else np.asarray(view["center"])
    ext = np.percentile(allp, 98, 0) - np.percentile(allp, 2, 0)
    dist = view.get("dist", 1.25 * max(ext[0], ext[1]))
    proj = cam(center, dist, view.get("yaw", -60), view.get("pitch", 45), view.get("fov", 50))
    fig = plt.figure(figsize=(16, 10), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG); ax.set_axis_off()
    # grid, 10 m cells, at the floor of the map
    gz = np.percentile(allp[:, 2], 2) if grid_z is None else grid_z
    lo = np.floor((center[:2] - 0.9 * max(ext[:2]) - 10) / 10) * 10; hi = np.ceil((center[:2] + 0.9 * max(ext[:2]) + 10) / 10) * 10
    for x in np.arange(lo[0], hi[0] + 1, 10):
        L = np.stack([np.full(60, x), np.linspace(lo[1], hi[1], 60), np.full(60, gz)], 1); q, z, ok = proj(L)
        ax.plot(q[ok, 0], q[ok, 1], color=GRIDC, lw=0.6, zorder=1)
    for y in np.arange(lo[1], hi[1] + 1, 10):
        L = np.stack([np.linspace(lo[0], hi[0], 60), np.full(60, y), np.full(60, gz)], 1); q, z, ok = proj(L)
        ax.plot(q[ok, 0], q[ok, 1], color=GRIDC, lw=0.6, zorder=1)
    if M is not None:
        q, z, ok = proj(M)
        h = M[:, 2]; hn = (h - np.percentile(h, 2)) / max(np.percentile(h, 98) - np.percentile(h, 2), 1e-6)
        col = cm.hsv(0.8 * (1 - np.clip(hn, 0, 1)))       # AxisColor-like: low red ... high violet
        o = np.argsort(-z[ok])
        ax.scatter(q[ok][o, 0], q[ok][o, 1], s=0.35, c=col[ok][o], linewidths=0, alpha=0.75, zorder=2)
    hs = []
    q, z, ok = proj(np.nan_to_num(gt)); m = ok & np.isfinite(gt).all(1)
    hs.append(ax.plot(np.where(m, q[:, 0], np.nan), np.where(m, q[:, 1], np.nan), color=GT_C, lw=1.6, zorder=4, label="ground truth")[0])
    for lab, c, P in paths:
        q, z, ok = proj(np.nan_to_num(P)); m = ok & np.isfinite(P).all(1)
        hs.append(ax.plot(np.where(m, q[:, 0], np.nan), np.where(m, q[:, 1], np.nan), color=c, lw=1.6, zorder=5, label=lab)[0])
    ax.set_aspect("equal")
    xy = proj(allp)[0]
    ax.set_xlim(np.percentile(xy[:, 0], 0.5) - 0.05, np.percentile(xy[:, 0], 99.5) + 0.05)
    ax.set_ylim(np.percentile(xy[:, 1], 0.5) - 0.05, np.percentile(xy[:, 1], 99.5) + 0.05)
    lg = ax.legend(handles=hs, loc="lower left", facecolor=BG, edgecolor=GRIDC, labelcolor="#e8eaed", fontsize=12)
    fig.text(0.015, 0.965, title, color="#e8eaed", fontsize=15, weight="bold")
    fig.text(0.015, 0.935, "RViz-style render (colours of viz/live.rviz): map coloured by height, 10 m grid", color="#8b93a1", fontsize=11)
    fig.savefig(out, facecolor=BG, dpi=100)
    plt.close(fig)
    print("saved", out, flush=True)


def P(df, pre):
    return df[[pre + "x", pre + "y", pre + "z"]].values.astype(float)


def case(seq):
    kf = None
    if seq == "MF":
        d = pd.read_csv(S + "/f24bag/MF_switching_log_v2_F24_kf_run1.csv"); gt = D + "/gt/mf_gt_a.csv"; kf = S + "/f24bag/MF_keyframes_F24_kf_run1.npz"
        title, lab, view = "Multi Floor: F24 live run 1", "F24 fused path", dict(yaw=-50, pitch=40)
        dfa = d
    elif seq == "LC":
        d = pd.read_csv(S + "/f24bag/LC_switching_log_v2_F24_kf_run1.csv"); gt = D + "/gt/lc_gt.txt"; kf = S + "/f24bag/LC_keyframes_F24_kf_run1.npz"
        title, lab, view = "Long Corridor: F24 live run 1", "F24 fused path", dict(yaw=-70, pitch=50)
        dfa = d
    elif seq == "C02":
        d = pd.read_csv(S + "/hb/out/C021/switching_log_v2_F21a.csv"); gt = D + "/gt/c02_gt.txt"; kf = D + "/kfc/C02_keyframes_F8_kf_run1.npz"
        title, lab, view = "Corridor02: F24 replay of live run 1", "F24 fused path (replay)", dict(yaw=-60, pitch=50)
        dfa = pd.read_csv(D + "/for_claude8/switching_log_v2_F8_kf_run1.csv")
    elif seq == "CAVE":
        d = pd.read_csv(D + "/for_claude14/switching_log_v2_F16_run1.csv"); gt = D + "/for_claude14/cave02_gt.txt"; kf = D + "/g17_heldout/cave_kf.npz"
        title, lab, view = "Cave02 (held out): F16 live run 1", "F16 fused path", dict(yaw=-40, pitch=45)
        dfa = d
    elif seq == "GEODE":
        d = pd.read_csv(D + "/geode/switching_log_v2_F16_kf_run1.csv"); gt = D + "/geode/gt_stairs_alpha.txt"
        title, lab, view = "GEODE stairs (held out): F16 live run 1 (no map recorded)", "F16 fused path", dict(yaw=-90, pitch=72)
        dfa = d
    elif seq == "FARM":
        d = pd.read_csv(S + "/farm24/farm_f24/switching_log_v2_F24_farm_live1.csv")
        g = np.loadtxt(S + "/farm24/farm_f24/gt_live.txt", comments="#")
        d = d[d.time >= g[0, 0]].reset_index(drop=True)
        t = d.time.values.astype(float); G = V.gt_on(t, g[:, 0], g[:, 1:4])
        qf, _ = V.aligned(P(d, "fused_"), G); qa, _ = V.aligned(P(d, "aft_"), G)
        render(S + "/vid/rviz_FARM.png", "Farm L route (Gazebo): F24 live run (paths only; the world is not recorded)", None,
               [("A-LOAM mapped path", AFT_C, qa), ("F24 fused path", FUS_C, qf)], G, dict(yaw=-60, pitch=55, dist=70))
        return
    t = d.time.values.astype(float)
    gt_t, gt_p = V.load_gt_any(gt)
    G = V.gt_on(t, gt_t, gt_p)
    qf, _ = V.aligned(P(d, "fused_"), G)
    ta = dfa.time.values.astype(float); pa = P(dfa, "aft_")
    pa_i = np.stack([np.interp(t, ta, pa[:, i], left=np.nan, right=np.nan) for i in range(3)], 1)
    qa, _ = V.aligned(pa_i, G)
    M = None
    if kf:
        M, _ = V.kf_map(kf, gt_t, gt_p, per_kf=1600, zclip=(1, 97))
    render(S + "/vid/rviz_%s.png" % seq, title, M, [("A-LOAM mapped path", AFT_C, qa), (lab, FUS_C, qf)], G, view)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        case(s)
