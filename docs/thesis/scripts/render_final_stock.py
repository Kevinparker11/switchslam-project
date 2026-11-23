"""RViz-style stills of the final version with STOCK A-LOAM as the A-LOAM line.
Per sequence: ground truth (white), stock A-LOAM from a separate run (orange), VINS-Mono alone from the F35 run (red, only where it
stays on the plot) and F35 (green), over the keyframe map of the F35 run.  Each path is aligned to the ground truth on its own
(Umeyama SE(3), no scale).  Stock logs: figure_data/stock/<SEQ>_stock.csv.gz, made by fusion_v4/stock_aloam/run_stock_aloam.sh
(the aft_ columns are the stock A-LOAM pose).
The Farm route was recorded live in Gazebo (fusion_v4/stock_aloam/farm_stock.sh): figure_data/stock/FARM_stock_aft.txt.gz (the
A-LOAM scan-to-map output) and FARM_stock_gt.txt.gz (ground truth of that run), both TUM text on the simulation clock.  As for the F35
farm run, the same time span as the F35 log (about 380 s from the start) is scored and drawn.
usage: python3 render_final_stock.py MF LC C02 CAVE GEODE FARM   (FIG_DATA, FIG_OUT as in render_final.py; images <SEQ>_stock.png)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vidlib as V
import render_final as R

K, D = R.K, R.D
CFG = {"MF": ("Multi Floor (SubT-MRS)", "/gt/mf_gt_a.csv", dict(yaw=-50, pitch=40)),
       "LC": ("Long Corridor (SubT-MRS)", "/gt/lc_gt.txt", dict(yaw=-70, pitch=50)),
       "C02": ("Corridor02 (SubT-MRS)", "/gt/c02_gt.txt", dict(yaw=-60, pitch=50)),
       "CAVE": ("Cave02 (SubT-MRS)", "/for_claude14/cave02_gt.txt", dict(yaw=-40, pitch=45)),
       "GEODE": ("GEODE stairs", "/geode/gt_stairs_alpha.txt", dict(yaw=-90, pitch=72))}
STOCK_C = "#ffaa28"


def farm_inputs():
    """F35 farm log after the reset with its ground truth, and the unmodified A-LOAM run (same time span as the F35 log) aligned to its own
    ground truth.  The two runs have separate simulation clocks, so they are tied together by the time since their own start."""
    d = R.rcsv(R.S + "/f26z/farm_f26/switching_log_v2_F26_fwdrgb_live1.csv")
    g = np.loadtxt(R.S + "/f26z/farm_f26/gt_f26.txt", comments="#")
    j = np.linalg.norm(np.diff(g[:, 1:3], axis=0), axis=1); k = int(np.argmax(j))
    t_reset = g[k + 1, 0] if j[k] > 0.5 else g[0, 0]
    g = g[g[:, 0] >= t_reset]
    d = d[d.time >= max(t_reset, g[0, 0])].reset_index(drop=True)
    t = d.time.values.astype(float); G = V.gt_on(t, g[:, 0], g[:, 1:4])
    a = np.loadtxt(R.S + "/stock/FARM_stock_aft.txt.gz", comments="#")
    a = a[a[:, 0] - a[0, 0] <= t[-1] - t[0]]
    gs = np.loadtxt(R.S + "/stock/FARM_stock_gt.txt.gz", comments="#")
    qs, es = V.aligned(a[:, 1:4], V.gt_on(a[:, 0], gs[:, 0], gs[:, 1:4]))
    return d, t, G, a[:, 0], qs, es


def run_farm():
    d, t, G, ts, qs, es = farm_inputs(); rs = R.stat(es)
    qf, ef = V.aligned(R.P3(d, "fused_"), G); rf = R.stat(ef)
    paths = [("A-LOAM: RMSE %.2f / max %.2f m" % rs, STOCK_C, qs)]
    vp = R.P3(d, "v_p"); good = np.isfinite(vp).all(1) & (np.abs(vp).max(1) < 1e5)
    vp2 = vp.copy(); vp2[~good] = np.nan
    qv, ev = V.aligned(vp2, G); rv = R.stat(ev)
    paths.append(("VINS-Mono: RMSE %.2f / max %.2f m" % rv, R.VINS_C, qv))
    paths.append(("F35: RMSE %.2f / max %.2f m" % rf, R.FUS_C, qf))
    foot = ("Each path aligned to the ground truth on its own (Umeyama SE(3), no scale); front end only, no loop closure; first " + ("%.0f" % (t[-1] - t[0])) + " s after "
            "the start. A-LOAM is the unmodified A-LOAM, run separately on the same route; VINS-Mono alone is taken from the F35 run, since it "
            "takes no input from the fusion. " + R.PUB["FARM"] + " The Gazebo world is not recorded; paths only.")
    R.render(os.path.join(R.OUT, "FARM_stock.png"), "Farm L route (Gazebo, Husky): F35 and A-LOAM, front end only",
             "RViz-style render: ground truth white, 5 m grid, paths only", None, G, paths, dict(yaw=-60, pitch=55, dist=70, grid=5), foot)
    print("FARM", "F35 %.2f / %.2f | A-LOAM %.2f / %.2f" % (rf + rs), flush=True)


def run(seq):
    if seq == "FARM":
        return run_farm()
    name, gt_rel, view = CFG[seq]
    d = R.rcsv("%s/%s_switching_log_v2_F26_kf_run1.csv" % (K, seq))
    stock = R.rcsv("%s/stock/%s_stock.csv" % (R.S, seq))
    gt_t, gt_p = V.load_gt_any(D + gt_rel)
    t = d.time.values.astype(float); G = V.gt_on(t, gt_t, gt_p)
    M, _ = V.kf_map("%s/%s_keyframes_F26_kf_run1.npz" % (K, seq), gt_t, gt_p, per_kf=1600, zclip=(1, 97))
    ts = stock.time.values.astype(float)
    qs, es = V.aligned(R.P3(stock, "aft_"), V.gt_on(ts, gt_t, gt_p)); rs = R.stat(es)
    qf, ef = V.aligned(R.P3(d, "fused_"), G); rf = R.stat(ef)
    paths = [("A-LOAM: RMSE %.2f / max %.2f m" % rs, STOCK_C, qs)]
    vp = R.P3(d, "v_p"); good = np.isfinite(vp).all(1) & (np.abs(vp).max(1) < 1e5)
    vtxt = ""
    vp2 = vp.copy(); vp2[~good] = np.nan
    if seq != "GEODE" and good.sum() > 100:
        qv, ev = V.aligned(vp2, G); rv = R.stat(ev)
        if rv[0] < 25:
            paths.append(("VINS-Mono: RMSE %.2f / max %.2f m" % rv, R.VINS_C, qv))
        else:
            vtxt = " VINS-Mono alone (RMSE %.1f m) is off the plot." % rv[0]
    else:
        _, ev = V.aligned(vp2, G); vtxt = " VINS-Mono alone (RMSE %.0f m) is off the plot." % R.stat(ev)[0]
    paths.append(("F35: RMSE %.2f / max %.2f m" % rf, R.FUS_C, qf))
    foot = ("Each path aligned to the ground truth on its own (Umeyama SE(3), no scale); front end only, no loop closure. A-LOAM is the "
            "unmodified A-LOAM, run separately on the same bag at the same replay rate; VINS-Mono alone is taken from the F35 run, since it "
            "takes no input from the fusion." + vtxt + " " + R.PUB.get(seq, R.NOPUB) + " Map: keyframe scans of the F35 run, coloured by height.")
    R.render(os.path.join(R.OUT, "%s_stock.png" % seq), "%s: F35 and A-LOAM, front end only" % name,
             "RViz-style render: ground truth white, 10 m grid, map coloured by height", M, G, paths, view, foot)
    print(seq, "F35 %.2f / %.2f | A-LOAM %.2f / %.2f" % (rf + rs), flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2 or any(s not in CFG and s != "FARM" for s in sys.argv[1:]):
        sys.exit(__doc__)
    for s in sys.argv[1:]:
        run(s)
