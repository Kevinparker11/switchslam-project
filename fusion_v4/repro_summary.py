#!/usr/bin/env python3
"""Reproduction-check verdict, rule fixed in docs/protocols/SwitchSLAM_Exact_Replica.md section 5 before any run:
SW (three runs per sequence) reproduces the published level if its mean ATE RMSE is within +-50 % of Switch-SLAM Table II on
BOTH Multi Floor (1.61 / 3.63) and Long Corridor (2.42 / 5.09).  SWM, SW1 and V7 are listed, never judged against the rule.
usage: python3 repro_summary.py [runs_v2_dir runs_corridor_dir]"""
import csv, os, sys
import numpy as np

H = os.path.expanduser("~")
dirs = {"Multi Floor": (sys.argv[1] if len(sys.argv) > 1 else H + "/runs_v2", 1.61, 3.63),
        "Long Corridor": (sys.argv[2] if len(sys.argv) > 2 else H + "/runs_corridor", 2.42, 5.09)}
ok = {}
okf = {}
print("ATE RMSE / max (m), full span, Umeyama SE(3); published = Switch-SLAM Table II (mean of 3 runs, no loop closure)")
for seq, (d, pr, pm) in dirs.items():
    rows = {}
    p = os.path.join(d, "results_index.csv")
    if os.path.exists(p):
        for r in csv.reader(open(p)):
            if len(r) >= 5 and r[0] != "tag" and "_kf_run" in r[0]:
                try: rows.setdefault(r[0].split("_kf_run")[0], []).append((float(r[3]), float(r[4])))
                except ValueError: pass
    print("\n%s   published %.2f / %.2f" % (seq, pr, pm))
    for c in ("F24", "SW", "SWI", "SWF", "SWM", "SW1", "V7"):
        v = rows.get(c)
        if not v: print("  %-4s no completed runs" % c); continue
        a = np.array(v)
        print("  %-4s n=%d  RMSE %s  mean %.2f (sd %.2f)  max-error mean %.2f   ratio to published RMSE %.2f"
              % (c, len(a), " ".join("%.2f" % x for x in a[:, 0]), a[:, 0].mean(), a[:, 0].std(ddof=1) if len(a) > 1 else float("nan"), a[:, 1].mean(), a[:, 0].mean() / pr))
    sw = rows.get("SW")
    ok[seq] = None if not sw or len(sw) < 3 else bool(0.5 * pr <= np.mean([x[0] for x in sw]) <= 1.5 * pr)
    sf = rows.get("SWF")
    okf[seq] = None if not sf or len(sf) < 3 else bool(0.5 * pr <= np.mean([x[0] for x in sf]) <= 1.5 * pr)
print()
if None in okf.values() or not okf: print("SWF VERDICT: not decided (SWF needs 3 completed runs on both sequences)")
elif all(okf.values()): print("SWF VERDICT: SWF reproduces the published level on both sequences (mean RMSE within +-50 %)")
else: print("SWF VERDICT: SWF does NOT reproduce the published level (%s)" % ", ".join("%s %s" % (k, "within" if v else "outside") for k, v in okf.items()))
if None in ok.values(): print("VERDICT: not decided (SW needs 3 completed runs on both sequences)")
elif all(ok.values()): print("VERDICT: SW reproduces the published level on both sequences -> report as 'Switch-SLAM as published (our implementation)'")
else: print("VERDICT: SW does NOT reproduce the published level (%s) -> report as 'our implementation of Switch-SLAM', no claim about the published system" %
           ", ".join("%s %s" % (k, "within" if v else "outside") for k, v in ok.items()))
