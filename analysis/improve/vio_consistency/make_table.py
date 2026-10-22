import json, re, os, numpy as np
names = open("names.txt").read().split()
def bk(n, c):
    f = "bk/%s_%s.out" % (n, c)
    if not os.path.exists(f): return np.nan
    v = np.nan
    for line in open(f):
        if line.startswith("iso ") and "full" not in line:
            v = float(line.split("|")[1].split("/")[0])
    return v
rows = {}
for n in names:
    b = json.load(open("base_%s.json" % n)); e3 = json.load(open("ev3_%s.json" % n)); e5 = json.load(open("ev5_%s.json" % n))
    rows[n] = dict(GenZ=b["GenZ"], VINS=b["VINS"], G17=b["G17"], G18=e3["scaleSeg200"][0], G19=e5["sc10+seg"], SAHonly=b["SAHonly"],
                   G17L=bk(n, "G17"), G18L=bk(n, "G18"), G19L=bk(n, "G19"), SAHonlyL=bk(n, "SAHonly"), live=b["live"])
cols = ["GenZ", "G17", "G18", "G19", "SAHonly", "G17L", "G18L", "G19L", "SAHonlyL"]
print("%-10s " % "log" + " ".join("%8s" % c for c in cols))
for n in names: print("%-10s " % n + " ".join("%8.3f" % rows[n][c] for c in cols))
seqs = {"MF": [n for n in names if n.startswith("MF")], "C02": ["C02-G17"], "CAVE": ["CAVE-G17"], "GEO": [n for n in names if n.startswith("GEO")]}
print()
for s, ns in seqs.items():
    print("%-10s " % ("mean " + s) + " ".join("%8.3f" % np.mean([rows[n][c] for n in ns]) for c in cols))
json.dump(rows, open("rows.json", "w"), indent=1)
