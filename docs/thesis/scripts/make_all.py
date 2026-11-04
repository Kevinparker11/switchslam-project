import sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/vid")
import vidlib as V

S = V.S
D = S + "/data"
GREEN, RED, ORANGE, BLUE = "#4fd18b", "#ff6b5e", "#f2994a", "#5aa9ff"
FOOT = ("Paths aligned to ground truth (Umeyama SE(3), no scale), each on its own. Map: keyframe scans of a recorded run of "
        "the same sequence, placed with that run's poses aligned to ground truth.")


def P(df, pre):
    return df[[pre + "x", pre + "y", pre + "z"]].values.astype(float)


def bag_case(seq):
    if seq == "MF":
        log, gt, kf = S + "/f24bag/MF_switching_log_v2_F24_kf_run1.csv", D + "/gt/mf_gt_a.csv", S + "/f24bag/MF_keyframes_F24_kf_run1.npz"
        title = "Multi Floor (SubT-MRS), F24 live run 1, front end only (no loop closure)"
        main = "F24 (final, live)"
    elif seq == "LC":
        log, gt, kf = S + "/f24bag/LC_switching_log_v2_F24_kf_run1.csv", D + "/gt/lc_gt.txt", S + "/f24bag/LC_keyframes_F24_kf_run1.npz"
        title = "Long Corridor (SubT-MRS), F24 live run 1, front end only (no loop closure)"
        main = "F24 (final, live)"
    elif seq == "CAVE":
        log, gt, kf = D + "/for_claude14/switching_log_v2_F16_run1.csv", D + "/for_claude14/cave02_gt.txt", D + "/g17_heldout/cave_kf.npz"
        title = "Cave02 (SubT-MRS, held out), F16 live run 1, front end only (no F24 run yet)"
        main = "F16 (live)"
    elif seq == "GEODE":
        log, gt, kf = D + "/geode/switching_log_v2_F16_kf_run1.csv", D + "/geode/gt_stairs_alpha.txt", None
        title = "GEODE stairs (held out), F16 live run 1: VINS-Mono fails (alone 270 m RMSE, not drawn)"
        main = "F16 (live)"
    d = pd.read_csv(log)
    t = d.time.values.astype(float); mode = d["mode"].astype(str).values
    gt_t, gt_p = V.load_gt_any(gt)
    g = V.gt_on(t, gt_t, gt_p)
    paths = []
    q, e = V.aligned(P(d, "fused_"), g); paths.append((main, GREEN, q, e))
    if seq == "GEODE":
        q, e = V.aligned(P(d, "aft_"), g); paths.append(("A-LOAM output", ORANGE, q, e))
    vp = P(d, "v_p")
    good = np.isfinite(vp).all(1) & (np.abs(vp).max(1) < 1e5)
    vp[~good] = np.nan
    if good.sum() > 100 and seq != "GEODE":
        q, e = V.aligned(vp, g); paths.append(("VINS-Mono alone", RED, q, e))
    M = MT = None
    if kf:
        M, MT = V.kf_map(kf, gt_t, gt_p)
    for lab, _, _, e in paths:
        print(seq, lab, "RMSE %.3f max %.2f" % (np.sqrt(np.nanmean(e ** 2)), np.nanmax(e)), flush=True)
    sub = "Top-down view"
    V.make(S + "/vid/%s_final.mp4" % seq, title, sub, t, mode, g, paths, FOOT if kf else FOOT.split(" Map:")[0], M, MT)


def c02():
    base = S + "/hb/out/C021/"
    A = pd.read_csv(base + "switching_log_v2_F20.csv"); B = pd.read_csv(base + "switching_log_v2_F21a.csv")
    L = pd.read_csv(D + "/for_claude8/switching_log_v2_F8_kf_run1.csv")
    t = B.time.values.astype(float); mode = B["mode"].astype(str).values
    gt_t, gt_p = V.load_gt_any(D + "/gt/c02_gt.txt")
    g = V.gt_on(t, gt_t, gt_p)
    qa, ea = V.aligned(P(A, "fused_"), g); qb, eb = V.aligned(P(B, "fused_"), g)
    vt_ = L.time.values.astype(float); vp = P(L, "v_p")
    vpi = np.stack([np.interp(t, vt_, vp[:, i], left=np.nan, right=np.nan) for i in range(3)], 1)
    qv, ev = V.aligned(vpi, g)
    paths = [("F24 (final, replay)", GREEN, qb, eb), ("F20 (replay)", ORANGE, qa, ea), ("VINS-Mono alone", RED, qv, ev)]
    for lab, _, _, e in paths:
        print("C02", lab, "RMSE %.3f max %.2f" % (np.sqrt(np.nanmean(e ** 2)), np.nanmax(e)), flush=True)
    M, MT = V.kf_map(D + "/kfc/C02_keyframes_F8_kf_run1.npz", gt_t, gt_p)
    V.make(S + "/vid/C02_final.mp4", "Corridor02 (SubT-MRS): F24 against F20, replay of live run 1 through the real fusion node",
           "Top-down view", t, mode, g, paths,
           "Open-loop replay: the logged A-LOAM and VINS-Mono poses of the run are fed to the fusion node. " + FOOT.split(". ", 1)[1],
           M, MT)


def farm():
    d = pd.read_csv(S + "/farm24/farm_f24/switching_log_v2_F24_farm_live1.csv")
    gt = np.loadtxt(S + "/farm24/farm_f24/gt_live.txt", comments="#")
    j = np.linalg.norm(np.diff(gt[:, 1:3], axis=0), axis=1); k = int(np.argmax(j))
    t_reset = gt[k + 1, 0] if j[k] > 0.5 else gt[0, 0]
    gt = gt[gt[:, 0] >= t_reset]
    d = d[d.time >= max(t_reset, gt[0, 0])].reset_index(drop=True)
    t = d.time.values.astype(float); mode = d["mode"].astype(str).values
    g = V.gt_on(t, gt[:, 0], gt[:, 1:4])
    paths = []
    for lab, c, pre in [("F24 (final, live)", GREEN, "fused_"), ("A-LOAM output", ORANGE, "aft_"), ("VINS-Mono alone", RED, "v_p")]:
        q, e = V.aligned(P(d, pre), g); paths.append((lab, c, q, e))
        print("FARM", lab, "RMSE %.3f max %.2f" % (np.sqrt(np.nanmean(e ** 2)), np.nanmax(e)), flush=True)
    V.make(S + "/vid/FARM_final.mp4", "Farm L route (Gazebo, Husky), F24 live run, front end only (no loop closure)",
           "Top-down view (the Gazebo world itself was not recorded)", t, mode, g, paths,
           "Paths aligned to the Gazebo ground truth (Umeyama SE(3), no scale), each on its own. The A-LOAM output is fed by the fused pose.",
           None, None, pad=4.0)


if __name__ == "__main__":
    s = sys.argv[1]
    if s == "C02": c02()
    elif s == "FARM": farm()
    else: bag_case(s)
