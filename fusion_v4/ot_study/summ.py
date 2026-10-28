import sys, glob, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import ate_log
tags = sys.argv[1:]
seqs = {"MF": ["MF%d" % i for i in range(1, 7)], "LC": ["LC%d" % i for i in range(1, 4)], "C02": ["C02%d" % i for i in range(1, 4)]}
print("%-12s" % "config" + "".join("| %-44s" % s for s in seqs))
res = {}
for tg in tags:
    line = "%-12s" % tg
    for s, runs in seqs.items():
        v = []
        for r in runs:
            p = "out/%s/switching_log_v2_%s.csv" % (r, tg)
            h = "out/%s/h_%s.txt" % (r, tg)
            done = os.path.exists(h) and any(l.startswith("rows") for l in open(h))
            v.append(ate_log(p, s)[0] if (os.path.exists(p) and done) else np.nan)
        res[(tg, s)] = np.array(v)
        line += "| %s mean %.3f " % (" ".join("%.2f" % x for x in v), np.nanmean(v))
    print(line)
import pickle; pickle.dump(res, open("summ_%s.pkl" % "_".join(tags)[:60], "wb"))
