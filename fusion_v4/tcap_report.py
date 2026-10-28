#!/usr/bin/env python3
"""tcap_report.py - validity, diagnostics and the pre-registered verdict for the additional-T single run.
   python3 tcap_report.py ~/runs_v2/switching_log_v2_F18_run1.csv --seq multifloor [--ate 0.55]   (ATE from the scorer if not given: results_index.csv)
Rules are those of docs/results/ChannelT_MultiFloor_Single_Test.md (fixed before the run); nothing here is tunable."""
import argparse, csv, os, sys
import numpy as np
import pandas as pd

RULES = {   # paper bar (Switch-SLAM Table), best / worst of the matched baseline runs of the same stack
    "multifloor": dict(paper=1.61, best=0.47, worst=0.77, base="F8 on Multi Floor, 9 live runs at 1.0x: 0.617 +- 0.107, range 0.47-0.77 (3 runs at 0.5x: 0.52-0.73)"),
    "longcorridor": dict(paper=2.42, best=1.99, worst=3.17, base="F16 on Long Corridor, 6 live runs at 0.5x: 2.27 +- 0.45, range 1.99-3.17"),
}
ap = argparse.ArgumentParser()
ap.add_argument("log"); ap.add_argument("--seq", required=True, choices=RULES); ap.add_argument("--ate", type=float)
ap.add_argument("--min-rows", type=int, default=3000)
a = ap.parse_args()
d = pd.read_csv(a.log)
for c in ("T_l1", "T_ms", "tcap_ratio"):
    if c not in d:
        sys.exit("no %s column: this log was not made with TCAP=1" % c)
F = d[d["mode"] == "FUSED"]
cov = F["T_l1"].notna().mean() if len(F) else 0.0
ratio = F["tcap_ratio"].dropna()
print("rows %d  FUSED rows %d  (%.1f %%)" % (len(d), len(F), 100 * len(F) / max(len(d), 1)))
print("VALIDITY: rows >= %d : %s ;  T present on %.1f %% of FUSED rows (need >= 90 %%) : %s" % (
    a.min_rows, "yes" if len(d) >= a.min_rows else "NO", 100 * cov, "yes" if cov >= 0.9 else "NO"))
valid = len(d) >= a.min_rows and cov >= 0.9
if len(ratio):
    print("DIAGNOSTICS (no verdict attached): tcap_ratio = smallest lambda'/lambda over the three Schur directions")
    print("   median %.3f  q10 %.3f  q90 %.3f ;  rows with ratio < 0.9: %.1f %% ;  < 0.5: %.1f %%" % (
        ratio.median(), ratio.quantile(.1), ratio.quantile(.9), 100 * (ratio < 0.9).mean(), 100 * (ratio < 0.5).mean()))
    print("   T smallest eigenvalue l1 median %.4f ;  T compute ms p50 %.1f  p99 %.1f" % (
        F["T_l1"].median(), F["T_ms"].median(), F["T_ms"].quantile(.99)))
ate = a.ate
if ate is None:
    idx = os.path.join(os.path.dirname(os.path.abspath(a.log)), "results_index.csv")
    tag = os.path.basename(a.log).replace("switching_log_v2_", "").replace(".csv", "")
    if os.path.exists(idx):
        for r in csv.DictReader(open(idx)):
            if r["tag"] == tag:
                ate = float(r["ate_full_rmse"])
if ate is None:
    sys.exit("ATE not found: pass --ate")
R = RULES[a.seq]
print("\nATE (full span) %.3f m ;  Switch-SLAM paper %.2f m ;  baseline: %s" % (ate, R["paper"], R["base"]))
if not valid:
    print("VERDICT: INVALID RUN (see VALIDITY); not a result. Report it and rerun from a clean restart.")
else:
    print("paper bar (ATE < %.2f m): %s" % (R["paper"], "met" if ate < R["paper"] else "NOT met"))
    if ate < R["best"]:
        print("VERDICT: BETTER than every baseline run (%.3f < %.2f): suggestive, one run; needs 3 repeats before it is claimed" % (ate, R["best"]))
    elif ate > R["worst"]:
        print("VERDICT: WORSE than every baseline run (%.3f > %.2f): T hurts in this run" % (ate, R["worst"]))
    else:
        print("VERDICT: INSIDE the baseline range (%.2f-%.2f): no difference detectable by a single run" % (R["best"], R["worst"]))
