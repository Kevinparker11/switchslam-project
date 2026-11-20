"""Trajectory videos in the layout of make_final_videos.py (vidlib.make), with three lines: A-LOAM, VINS-Mono and F35.
A-LOAM is the unmodified A-LOAM run separately on the same bag (figure_data/stock/<SEQ>_stock.csv.gz, aft_ columns), the same
data as render_final_stock.py.  F35 and VINS-Mono alone come from the F35 live run.  Each path is aligned to the ground truth on
its own (Umeyama SE(3), no scale).  VINS-Mono is drawn only where it stays on the plot.  The Farm route has no separate A-LOAM run
yet, so it is not included.
usage: python3 make_final_videos_aloam.py MF LC C02 CAVE GEODE        (FIG_DATA as in vidlib; videos go to $FIG_OUT or $FIG_DATA/vid_final,
file <SEQ>_F35_ALOAM.mp4 and <SEQ>_F35_ALOAM_last.png)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vidlib as V
import render_final as R
import render_final_stock as RS

OUT = os.environ.get("FIG_OUT", os.path.join(V.S, "vid_final")); os.makedirs(OUT, exist_ok=True)
GREEN, ORANGE, RED = R.FUS_C, RS.STOCK_C, R.VINS_C


def on_grid(t, ts, x):
    """linear interpolation of a series given at ts onto t (NaN outside the series)"""
    x = np.asarray(x, float)
    if x.ndim == 1:
        return np.interp(t, ts, x, left=np.nan, right=np.nan)
    return np.stack([np.interp(t, ts, x[:, c], left=np.nan, right=np.nan) for c in range(x.shape[1])], 1)


def run(seq):
    name, gt_rel, _ = RS.CFG[seq]
    d = R.rcsv("%s/%s_switching_log_v2_F26_kf_run1.csv" % (R.K, seq))
    stock = R.rcsv("%s/stock/%s_stock.csv" % (R.S, seq))
    gt_t, gt_p = V.load_gt_any(R.D + gt_rel)
    t = d.time.values.astype(float); G = V.gt_on(t, gt_t, gt_p)
    mode = d["mode"].astype(str).values
    M, MT = V.kf_map("%s/%s_keyframes_F26_kf_run1.npz" % (R.K, seq), gt_t, gt_p, per_kf=900, zclip=(1, 97))
    ts = stock.time.values.astype(float)
    qs, es = V.aligned(R.P3(stock, "aft_"), V.gt_on(ts, gt_t, gt_p)); rs = R.stat(es)
    qf, ef = V.aligned(R.P3(d, "fused_"), G); rf = R.stat(ef)
    paths = [("A-LOAM", ORANGE, on_grid(t, ts, qs), on_grid(t, ts, es))]
    vp = R.P3(d, "v_p"); good = np.isfinite(vp).all(1) & (np.abs(vp).max(1) < 1e5)
    vp2 = vp.copy(); vp2[~good] = np.nan
    vtxt = ""
    if seq != "GEODE" and good.sum() > 100:
        qv, ev = V.aligned(vp2, G); rv = R.stat(ev)
        if rv[0] < 25:
            paths.append(("VINS-Mono", RED, qv, ev))
        else:
            vtxt = rv[0]
    else:
        _, ev = V.aligned(vp2, G); vtxt = R.stat(ev)[0]
    paths.append(("F35", GREEN, qf, ef))
    # one line only: vidlib.make puts the footnote on a single line, about 200 characters fit
    foot = ("Paths aligned to the ground truth, each on its own (Umeyama SE(3), no scale); front end only. A-LOAM: unmodified A-LOAM, separate run, same bag. ")
    foot += ("VINS-Mono: from the F35 run." if vtxt == "" else "VINS-Mono (RMSE %.0f m, from the F35 run) is off the plot." % vtxt)
    title = "%s: F35 and A-LOAM, front end only: F35 RMSE %.2f / max %.2f m, A-LOAM RMSE %.2f / max %.2f m" % ((name,) + rf + rs)
    print(seq, "F35 %.2f / %.2f | A-LOAM %.2f / %.2f" % (rf + rs), flush=True)
    V.make(os.path.join(OUT, "%s_F35_ALOAM.mp4" % seq), title, "Top-down view, keyframe scans of the F35 run", t, mode, G, paths, foot, M, MT)


if __name__ == "__main__":
    if len(sys.argv) < 2 or any(s not in RS.CFG for s in sys.argv[1:]):
        sys.exit(__doc__)
    for s in sys.argv[1:]:
        run(s)
