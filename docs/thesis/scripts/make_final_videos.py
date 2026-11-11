"""Trajectory videos of the final version (report name F35, repo name F26), one per bag, in the layout and colours of the earlier
live videos (vidlib.make: top-down map, paths against ground truth, error panel, mode strip), from the same live runs as the final RViz-style
stills (render_final.py).  Green = F35 (final version), orange = A-LOAM output of the same run, red = VINS-Mono alone from the same run
(only where it stays on the plot).  usage: make_final_videos.py MF LC C02 CAVE GEODE FARM   (videos go to $S/vid_final/)"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/vid")
import vidlib as V

S = V.S; D = S + "/data"; K = S + "/f24cave"
OUT = S + "/vid_final"; os.makedirs(OUT, exist_ok=True)
GREEN, ORANGE, RED = "#4fd18b", "#ffaa28", "#ff6b5e"
CASES = {
    "MF": ("Multi Floor (SubT-MRS)", "MF", D + "/gt/mf_gt_a.csv"),
    "LC": ("Long Corridor (SubT-MRS)", "LC", D + "/gt/lc_gt.txt"),
    "C02": ("Corridor02 (SubT-MRS)", "C02", D + "/gt/c02_gt.txt"),
    "CAVE": ("Cave02 (SubT-MRS)", "CAVE", D + "/for_claude14/cave02_gt.txt"),
    "GEODE": ("GEODE stairs", "GEODE", D + "/geode/gt_stairs_alpha.txt"),
}
PUB = {"MF": "1.61 / 3.63", "LC": "2.42 / 5.09", "FARM": "0.38 / 1.10"}


def P3(df, pre):
    return df[[pre + "x", pre + "y", pre + "z"]].values.astype(float)


def stat(e):
    e = e[np.isfinite(e)]
    return float(np.sqrt(np.mean(e ** 2))), float(e.max())


def run(seq):
    M = MT = None; pad = 12.0
    if seq == "FARM":
        d = pd.read_csv(S + "/f26z/farm_f26/switching_log_v2_F26_fwdrgb_live1.csv")
        g0 = np.loadtxt(S + "/f26z/farm_f26/gt_f26.txt", comments="#")
        j = np.linalg.norm(np.diff(g0[:, 1:3], axis=0), axis=1); k = int(np.argmax(j))
        t_reset = g0[k + 1, 0] if j[k] > 0.5 else g0[0, 0]
        g0 = g0[g0[:, 0] >= t_reset]
        d = d[d.time >= max(t_reset, g0[0, 0])].reset_index(drop=True)
        t = d.time.values.astype(float); G = V.gt_on(t, g0[:, 0], g0[:, 1:4])
        name, pad, sub = "Farm L route (Gazebo, Husky)", 8.0, "Top-down view (the Gazebo world itself was not recorded)"
    else:
        name, tag, gt = CASES[seq]
        d = pd.read_csv(K + "/%s_switching_log_v2_F26_kf_run1.csv" % tag)
        t = d.time.values.astype(float)
        gt_t, gt_p = V.load_gt_any(gt)
        G = V.gt_on(t, gt_t, gt_p)
        kf = K + "/%s_keyframes_F26_kf_run1.npz" % tag
        M, MT = V.kf_map(kf, gt_t, gt_p, per_kf=900, zclip=(1, 97))
        sub = "Top-down view, keyframe scans of this run"
    mode = d["mode"].astype(str).values
    qf, ef = V.aligned(P3(d, "fused_"), G); rf = stat(ef)
    qa, ea = V.aligned(P3(d, "aft_"), G); ra = stat(ea)
    paths = [("F35 (final)", GREEN, qf, ef), ("A-LOAM output", ORANGE, qa, ea)]
    vp = P3(d, "v_p"); good = np.isfinite(vp).all(1) & (np.abs(vp).max(1) < 1e5)
    vtxt = ""
    if seq == "GEODE" or good.sum() > 100:
        vp2 = vp.copy(); vp2[~good] = np.nan
        qv, ev = V.aligned(vp2, G); rv = stat(ev)
        if seq != "GEODE" and rv[0] < 25:
            paths.append(("VINS-Mono alone", RED, qv, ev))
        else:
            vtxt = " VINS-Mono alone (RMSE %.0f m) is off the plot." % rv[0]
    pub = ("Published Switch-SLAM (a different system, mean of three runs): %s m." % PUB[seq]) if seq in PUB else "No Switch-SLAM value is published for this sequence."
    title = "%s: F35 live run, front end only (no loop closure): RMSE %.2f / max %.2f m" % (name, rf[0], rf[1])
    foot = ("Paths aligned to the ground truth, each on its own (Umeyama SE(3), no scale); A-LOAM output and VINS-Mono alone are from the same run as F35." + vtxt + " " + pub)
    out = OUT + "/%s_F35_final.mp4" % seq
    print(seq, "F35 %.3f / %.3f | A-LOAM %.3f / %.3f" % (rf + ra), flush=True)
    V.make(out, title, sub, t, mode, G, paths, foot, M, MT, pad=pad)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
