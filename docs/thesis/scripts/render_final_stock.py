"""RViz-style stills of the final version with STOCK A-LOAM as the A-LOAM line.
Per sequence: ground truth (white), stock A-LOAM from a separate run (orange), VINS-Mono alone from the F35 run (red, only where it
stays on the plot) and F35 (green), over the keyframe map of the F35 run.  Each path is aligned to the ground truth on its own
(Umeyama SE(3), no scale).  Stock logs: figure_data/stock/<SEQ>_stock.csv.gz, made by fusion_v4/stock_aloam/run_stock_aloam.sh
(the aft_ columns are the stock A-LOAM pose).
usage: python3 render_final_stock.py MF LC C02 CAVE GEODE        (FIG_DATA, FIG_OUT as in render_final.py; images <SEQ>_stock.png)"""
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


def run(seq):
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
    if len(sys.argv) < 2 or any(s not in CFG for s in sys.argv[1:]):
        sys.exit(__doc__)
    for s in sys.argv[1:]:
        run(s)
