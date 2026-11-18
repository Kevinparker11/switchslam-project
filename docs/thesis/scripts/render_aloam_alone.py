"""A-LOAM-alone view of one sequence: the A-LOAM scan-to-map pose (aft_ columns) of one or more run logs, drawn like the F35 images.
The logs are the switching_log_v2_*.csv(.gz) files of fusion_v4/run_fusion_study.sh (configuration F5) or of
fusion_v4/stock_aloam/run_stock_aloam.sh (stock A-LOAM).  Each path is aligned to the ground truth on its own (Umeyama SE(3), no scale).
usage:  python3 render_aloam_alone.py SEQ LOG [LOG ...]        SEQ = MF | LC | C02 | CAVE | GEODE
        FIG_DATA=<dir>  figure inputs (default: docs/thesis/figure_data)      FIG_OUT=<dir>  where the PNG goes
example (the three F5 Long Corridor runs shipped with the repo):
        python3 render_aloam_alone.py LC $(ls ../figure_data/data/for_claude7/switching_log_v2_F5_run*.csv.gz)"""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vidlib as V
import render_final as R

SEQ = {"MF": ("Multi Floor (SubT-MRS)", "/gt/mf_gt_a.csv", dict(yaw=-50, pitch=40)),
       "LC": ("Long Corridor (SubT-MRS)", "/gt/lc_gt.txt", dict(yaw=-70, pitch=50)),
       "C02": ("Corridor02 (SubT-MRS)", "/gt/c02_gt.txt", dict(yaw=-60, pitch=50)),
       "CAVE": ("Cave02 (SubT-MRS)", "/for_claude14/cave02_gt.txt", dict(yaw=-40, pitch=45)),
       "GEODE": ("GEODE stairs", "/geode/gt_stairs_alpha.txt", dict(yaw=-90, pitch=72))}
COLS = ["#ffaa28", "#ffd98a", "#c26b00", "#ffc15e", "#e08a00"]

if len(sys.argv) < 3 or sys.argv[1] not in SEQ:
    sys.exit(__doc__)
seq, logs = sys.argv[1], sys.argv[2:]
name, gt_rel, view = SEQ[seq]
gt_t, gt_p = V.load_gt_any(R.D + gt_rel)
paths, G_ref = [], None
for i, f in enumerate(logs):
    d = pd.read_csv(f)
    t = d.time.values.astype(float)
    G = V.gt_on(t, gt_t, gt_p)
    G_ref = G if G_ref is None else G_ref
    q, e = V.aligned(R.P3(d, "aft_"), G)
    r = R.stat(e)
    paths.append(("A-LOAM alone, run %d: RMSE %.2f / max %.2f m" % (i + 1, r[0], r[1]), COLS[i % len(COLS)], q))
    print(os.path.basename(f), "RMSE %.2f max %.2f" % r)
foot = ("A-LOAM scan-to-map output (aft_ columns of the run logs), front end only, no loop closure. Each path aligned to the ground truth "
        "on its own (Umeyama SE(3), no scale). Paths only; same route and view as the F35 image of this sequence.")
R.render(os.path.join(R.OUT, "%s_ALOAM_alone.png" % seq), "%s: A-LOAM alone, %d run(s), front end only" % (name, len(logs)),
         "RViz-style render: ground truth white, 10 m grid, paths only", None, G_ref, paths, view, foot)
