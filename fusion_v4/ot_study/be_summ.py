import sys, re, os, numpy as np
seqs = {"MF": ["MF%d" % i for i in range(1, 7)], "LC": ["LC%d" % i for i in range(1, 4)], "C02": ["C02%d" % i for i in range(1, 4)]}
for tag in sys.argv[1:]:
    for model in ("none", "iso", "ot"):
        line = "%-10s %-5s" % (tag, model)
        for s, runs in seqs.items():
            v = []; nl = []
            for r in runs:
                p = "out/%s/be_%s.txt" % (r, tag); x = np.nan; n = 0
                if os.path.exists(p):
                    for l in open(p):
                        m = re.match(r"^%s\s+(\d+)\s+\d+\s+\d+\s+\|\s+([\d.]+)" % model, l)
                        if m: x = float(m.group(2)); n = int(m.group(1))
                v.append(x); nl.append(n)
            line += "| %s: %s mean %.3f (loops %s) " % (s, " ".join("%.2f" % x for x in v), np.nanmean(v), "/".join(map(str, nl)))
        print(line)
