"""usage: python3 summ2.py [--held] [--cols aft|vins] TAG ...  -> per-sequence ATE of each tag (dev set unless --held)"""
import sys, os, numpy as np, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score2 import ate_log
a = sys.argv[1:]; held = "--held" in a; a = [x for x in a if x != "--held"]
cols = ("fused_x", "fused_y", "fused_z")
if "--cols" in a:
    i = a.index("--cols"); c = a[i + 1]; a = a[:i] + a[i + 2:]
    cols = {"aft": ("aft_x", "aft_y", "aft_z"), "vins": ("v_px", "v_py", "v_pz")}[c]
seqs = {"FARM": ["FARM1", "FARM2"]} if held else {"MF": ["MF%d" % i for i in range(1, 7)], "LC": ["LC%d" % i for i in range(1, 4)],
        "C02": ["C02%d" % i for i in range(1, 4)], "GEO": ["GEO1", "GEO2", "GEO3"]}
res = {}
for tg in a:
    line = "%-16s" % tg
    for s, runs in seqs.items():
        v = []
        for r in runs:
            p = "out/%s/switching_log_v2_%s.csv" % (r, tg); h = "out/%s/h_%s.txt" % (r, tg)
            done = os.path.exists(h) and any(l.startswith("rows") for l in open(h))
            v.append(ate_log(p, s, cols)[0] if (os.path.exists(p) and done) else np.nan)
        res[(tg, s)] = np.array(v)
        line += "| %s: %s = %.3f " % (s, " ".join("%.2f" % x for x in v), np.nanmean(v))
    print(line, flush=True)
os.makedirs("r2", exist_ok=True)
for (tg, s), v in res.items():
    pickle.dump(v, open("r2/%s__%s%s.pkl" % (tg, s, "_held" if held else ""), "wb"))
