"""Why do SW and SWF differ on a window when the rule almost never fires?  Compares the logs of two runs row by row (same bag, same window).
  python3 batches/window_compare.py ~/runs_cave02_sw/window180 SW SWF [run]
Prints, per run number: rows, share of scans with the rule fired (sw_degen) in each, share of rows where the mode or the case differs, and the
difference of the published (fused) and A-LOAM (aft) positions between the two runs: median, 95 %, max, and the same at the end of the window."""
import sys, glob, os
import numpy as np, pandas as pd

d, a, b = sys.argv[1:4]
runs = sys.argv[4:] or ["1", "2"]
for r in runs:
    fa, fb = [os.path.join(os.path.expanduser(d), "switching_log_v2_%s_kf_run%s.csv" % (c, r)) for c in (a, b)]
    if not (os.path.exists(fa) and os.path.exists(fb)):
        print("run %s: missing %s or %s" % (r, fa, fb)); continue
    A, B = [pd.read_csv(f) for f in (fa, fb)]
    A, B = [x[pd.to_numeric(x["time"], errors="coerce").notna()].reset_index(drop=True) for x in (A, B)]
    for x in (A, B): x["time"] = x["time"].astype(float)
    m = pd.merge_asof(A.sort_values("time"), B.sort_values("time"), on="time", suffixes=("_a", "_b"), direction="nearest", tolerance=0.02).dropna(subset=["fused_x_b"])
    print("run %s: %s %d rows, %s %d rows, matched %d" % (r, a, len(A), b, len(B), len(m)))
    print("  rule fired: %s %.1f %%, %s %.1f %%" % (a, 100 * (A["sw_degen"] == 1).mean(), b, 100 * (B["sw_degen"] == 1).mean()))
    print("  mode differs in %.1f %% of matched rows, sw_case differs in %.1f %%" % (100 * (m["mode_a"] != m["mode_b"]).mean(), 100 * (m["sw_case_a"] != m["sw_case_b"]).mean()))
    for name in ("fused", "aft"):
        dd = np.linalg.norm(m[["%s_%s_a" % (name, k) for k in "xyz"]].values - m[["%s_%s_b" % (name, k) for k in "xyz"]].values, axis=1)
        print("  %-5s position difference between the runs: median %.4f m, 95 %% %.4f m, max %.4f m, at the end %.4f m" % (name, np.median(dd), np.percentile(dd, 95), dd.max(), dd[-1]))
