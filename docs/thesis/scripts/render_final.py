"""RViz-style stills of the final version, one image per bag, with the stated comparisons drawn from the same run:
ground truth (white), final version (green), A-LOAM output of the same run (orange), VINS-Mono alone from the same run (red, only
where it stays on the plot).  The final version is called F35 in the report (repo name F26, see Report_Corrections_Log.md A10).
usage: render_final.py MF LC C02 CAVE GEODE FARM   (images go to $S/img/)"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/vid")
import vidlib as V
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm

S = V.S; D = S + "/data"; K = S + "/f24cave"
OUT = S + "/img"; os.makedirs(OUT, exist_ok=True)
BG = (15 / 255, 17 / 255, 21 / 255); GRIDC = (70 / 255, 74 / 255, 82 / 255)
GT_C, AFT_C, FUS_C, VINS_C = "#ffffff", "#ffaa28", "#4fd18b", "#ff6b5e"
PUB = {"MF": "Published Switch-SLAM (Table II, mean of three runs, a different system): RMSE 1.61 m, max 3.63 m.",
       "LC": "Published Switch-SLAM (Table II, mean of three runs, a different system): RMSE 2.42 m, max 5.09 m.",
       "FARM": "Published Switch-SLAM (Table II, mean of three runs, a different system): RMSE 0.38 m, max 1.10 m."}
NOPUB = "No Switch-SLAM value is published for this sequence."


def cam(center, dist, yaw, pitch, fov=50.0):
    y, p = np.radians(yaw), np.radians(pitch)
    eye = center + dist * np.array([np.cos(p) * np.cos(y), np.cos(p) * np.sin(y), np.sin(p)])
    f = center - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    Rcw = np.stack([r, u, -f])
    fpx = 0.5 / np.tan(np.radians(fov) / 2)

    def proj(X):
        Xc = (X - eye) @ Rcw.T
        z = -Xc[:, 2]
        ok = z > 0.5
        return np.stack([fpx * Xc[:, 0] / np.maximum(z, 1e-6), fpx * Xc[:, 1] / np.maximum(z, 1e-6)], 1), z, ok
    return proj


def render(out, title, sub, M, gt, paths, view, foot):
    allp = np.vstack([gt[np.isfinite(gt).all(1)]] + ([M] if M is not None else []))
    center = np.median(allp, 0)
    ext = np.percentile(allp, 98, 0) - np.percentile(allp, 2, 0)
    dist = view.get("dist", 1.25 * max(ext[0], ext[1]))
    proj = cam(center, dist, view.get("yaw", -60), view.get("pitch", 45), view.get("fov", 50))
    fig = plt.figure(figsize=(16, 10), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0.07, 1, 0.86], facecolor=BG); ax.set_axis_off()
    gz = np.percentile(allp[:, 2], 2)
    step = view.get("grid", 10)
    lo = np.floor((center[:2] - 0.9 * max(ext[:2]) - step) / step) * step
    hi = np.ceil((center[:2] + 0.9 * max(ext[:2]) + step) / step) * step
    for x in np.arange(lo[0], hi[0] + 1, step):
        L = np.stack([np.full(60, x), np.linspace(lo[1], hi[1], 60), np.full(60, gz)], 1); q, z, ok = proj(L)
        ax.plot(q[ok, 0], q[ok, 1], color=GRIDC, lw=0.6, zorder=1)
    for y in np.arange(lo[1], hi[1] + 1, step):
        L = np.stack([np.linspace(lo[0], hi[0], 60), np.full(60, y), np.full(60, gz)], 1); q, z, ok = proj(L)
        ax.plot(q[ok, 0], q[ok, 1], color=GRIDC, lw=0.6, zorder=1)
    if M is not None:
        q, z, ok = proj(M)
        h = M[:, 2]; hn = (h - np.percentile(h, 2)) / max(np.percentile(h, 98) - np.percentile(h, 2), 1e-6)
        col = cm.hsv(0.8 * (1 - np.clip(hn, 0, 1)))
        o = np.argsort(-z[ok])
        ax.scatter(q[ok][o, 0], q[ok][o, 1], s=0.35, c=col[ok][o], linewidths=0, alpha=0.75, zorder=2)
    hs = []
    q, z, ok = proj(np.nan_to_num(gt)); m = ok & np.isfinite(gt).all(1)
    hs.append(ax.plot(np.where(m, q[:, 0], np.nan), np.where(m, q[:, 1], np.nan), color=GT_C, lw=1.6, zorder=4, label="ground truth")[0])
    for lab, c, P in paths:
        q, z, ok = proj(np.nan_to_num(P)); m = ok & np.isfinite(P).all(1)
        hs.append(ax.plot(np.where(m, q[:, 0], np.nan), np.where(m, q[:, 1], np.nan), color=c, lw=1.8, zorder=5, label=lab)[0])
    ax.set_aspect("equal")
    xy = proj(allp)[0]
    ax.set_xlim(np.percentile(xy[:, 0], 0.5) - 0.05, np.percentile(xy[:, 0], 99.5) + 0.05)
    ax.set_ylim(np.percentile(xy[:, 1], 0.5) - 0.05, np.percentile(xy[:, 1], 99.5) + 0.05)
    ax.legend(handles=hs, loc="lower left", facecolor=BG, edgecolor=GRIDC, labelcolor="#e8eaed", fontsize=12)
    fig.text(0.015, 0.965, title, color="#e8eaed", fontsize=16, weight="bold")
    fig.text(0.015, 0.935, sub, color="#8b93a1", fontsize=11)
    fig.text(0.015, 0.025, foot, color="#c3c9d4", fontsize=10.5, va="bottom", wrap=True)
    fig.savefig(out, facecolor=BG, dpi=100)
    plt.close(fig)
    print("saved", out, flush=True)


def P3(df, pre):
    return df[[pre + "x", pre + "y", pre + "z"]].values.astype(float)


def stat(e):
    e = e[np.isfinite(e)]
    return np.sqrt(np.mean(e ** 2)), e.max()


def run(seq):
    kf = None
    if seq == "MF":
        d = pd.read_csv(K + "/MF_switching_log_v2_F26_kf_run1.csv"); gt = D + "/gt/mf_gt_a.csv"; kf = K + "/MF_keyframes_F26_kf_run1.npz"
        name, view = "Multi Floor (SubT-MRS)", dict(yaw=-50, pitch=40)
    elif seq == "LC":
        d = pd.read_csv(K + "/LC_switching_log_v2_F26_kf_run1.csv"); gt = D + "/gt/lc_gt.txt"; kf = K + "/LC_keyframes_F26_kf_run1.npz"
        name, view = "Long Corridor (SubT-MRS)", dict(yaw=-70, pitch=50)
    elif seq == "C02":
        d = pd.read_csv(K + "/C02_switching_log_v2_F26_kf_run1.csv"); gt = D + "/gt/c02_gt.txt"; kf = K + "/C02_keyframes_F26_kf_run1.npz"
        name, view = "Corridor02 (SubT-MRS)", dict(yaw=-60, pitch=50)
    elif seq == "CAVE":
        d = pd.read_csv(K + "/CAVE_switching_log_v2_F26_kf_run1.csv"); gt = D + "/for_claude14/cave02_gt.txt"; kf = K + "/CAVE_keyframes_F26_kf_run1.npz"
        name, view = "Cave02 (SubT-MRS)", dict(yaw=-40, pitch=45)
    elif seq == "GEODE":
        d = pd.read_csv(K + "/GEODE_switching_log_v2_F26_kf_run1.csv"); gt = D + "/geode/gt_stairs_alpha.txt"; kf = K + "/GEODE_keyframes_F26_kf_run1.npz"
        name, view = "GEODE stairs", dict(yaw=-90, pitch=72)
    elif seq == "FARM":
        d = pd.read_csv(S + "/f26z/farm_f26/switching_log_v2_F26_fwdrgb_live1.csv")
        g = np.loadtxt(S + "/f26z/farm_f26/gt_f26.txt", comments="#")
        j = np.linalg.norm(np.diff(g[:, 1:3], axis=0), axis=1); k = int(np.argmax(j))
        t_reset = g[k + 1, 0] if j[k] > 0.5 else g[0, 0]
        g = g[g[:, 0] >= t_reset]
        d = d[d.time >= max(t_reset, g[0, 0])].reset_index(drop=True)
        t = d.time.values.astype(float); G = V.gt_on(t, g[:, 0], g[:, 1:4])
        name, view = "Farm L route (Gazebo, Husky)", dict(yaw=-60, pitch=55, dist=70, grid=5)
        return finish(seq, d, t, G, G, None, name, view, "")
    t = d.time.values.astype(float)
    gt_t, gt_p = V.load_gt_any(gt)
    G = V.gt_on(t, gt_t, gt_p)
    M = None
    if kf:
        M, _ = V.kf_map(kf, gt_t, gt_p, per_kf=1600, zclip=(1, 97))
    finish(seq, d, t, G, G, M, name, view, "")


def finish(seq, d, t, G, Gfull, M, name, view, _):
    paths = []
    qf, ef = V.aligned(P3(d, "fused_"), G); rf = stat(ef)
    qa, ea = V.aligned(P3(d, "aft_"), G); ra = stat(ea)
    paths.append(("A-LOAM output, same run: RMSE %.2f / max %.2f m" % ra, AFT_C, qa))
    vp = P3(d, "v_p")
    good = np.isfinite(vp).all(1) & (np.abs(vp).max(1) < 1e5)
    vtxt = ""
    if good.sum() > 100 and seq != "GEODE":
        vp2 = vp.copy(); vp2[~good] = np.nan
        qv, ev = V.aligned(vp2, G); rv = stat(ev)
        if rv[0] < 25:
            paths.append(("VINS-Mono alone, same run: RMSE %.2f / max %.2f m" % rv, VINS_C, qv))
        else:
            vtxt = " VINS-Mono alone (RMSE %.1f m) is off the plot." % rv[0]
    elif seq == "GEODE":
        vp2 = vp.copy(); vp2[~good] = np.nan
        _, ev = V.aligned(vp2, G); vtxt = " VINS-Mono alone (RMSE %.0f m) is off the plot." % stat(ev)[0]
    paths.append(("F35 (final version): RMSE %.2f / max %.2f m" % rf, FUS_C, qf))
    pub = PUB.get(seq, NOPUB)
    foot = ("Each path aligned to the ground truth on its own (Umeyama SE(3), no scale); front end only, no loop closure; A-LOAM output "
            "and VINS-Mono alone are taken from the same run as F35, which feeds the fused pose to A-LOAM." + vtxt + " " + pub +
            (" Map: keyframe scans of this run, coloured by height." if M is not None else " The Gazebo world is not recorded; paths only."))
    sub = "RViz-style render: ground truth white, 10 m grid%s" % (", map coloured by height" if M is not None else "")
    if seq == "FARM":
        sub = "RViz-style render: ground truth white, 5 m grid, paths only"
    render(OUT + "/final_%s.png" % seq, "%s: F35 live run, front end only" % name, sub, M, Gfull, paths, view, foot)
    print(seq, "F35 RMSE %.3f max %.3f | A-LOAM %.3f %.3f" % (rf + ra), flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
