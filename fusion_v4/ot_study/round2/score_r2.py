"""Round 2 scoring (PREREG2.md): ATE per log, per cell means, score = mean over the 13 cells of ln(ATE / ATE_F20).
usage: python3 score_r2.py STAGE   (A: tags A_<rule>_<cond>; B: tags B_<rule>_<v>_<cond>, with V0 = the stage-A tag)
       python3 score_r2.py list TAGPREFIX ...   (raw per-cell table)"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score2 import ate_log
SEQ = {"MF": ["MF%d" % i for i in range(1, 7)], "LC": ["LC%d" % i for i in range(1, 4)], "C02": ["C02%d" % i for i in range(1, 4)],
       "GEO": ["GEO1", "GEO2", "GEO3"], "FARM": ["FARM1", "FARM2"]}
CELLS = [(s, c) for s in ("MF", "LC", "C02") for c in ("clean", "FL", "FV", "FS")] + [("GEO", "clean")]
CACHE = "r2/ate_cache.json"
os.makedirs("r2", exist_ok=True)
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def ate(tag, run, seq):
    p = "out/%s/switching_log_v2_%s.csv" % (run, tag); h = "out/%s/h_%s.txt" % (run, tag)
    if not (os.path.exists(p) and os.path.exists(h) and any(l.startswith("rows") for l in open(h))):
        return np.nan
    key = "%s|%s|%d" % (tag, run, int(os.path.getmtime(p)))
    if key not in cache:
        cache[key] = ate_log(p, seq)[0]
    return cache[key]

def cell(tag, s):
    v = np.array([ate(tag, r, s) for r in SEQ[s]])
    return float(np.mean(v)) if np.isfinite(v).all() else np.nan, v

def table(rules, tagf):
    res = {}
    for r in rules:
        res[r] = {}
        for (s, c) in CELLS:
            res[r][(s, c)] = cell(tagf(r, c), s)
    json.dump(cache, open(CACHE, "w"))
    return res

def report(res, base, order, label):
    print("%-10s" % label + "".join("%10s" % ("%s-%s" % (s, c)) for (s, c) in CELLS) + "   score  admissible")
    out = {}
    for r in order:
        m = [res[r][k][0] for k in CELLS]
        b = [res[base][k][0] for k in CELLS]
        sc = float(np.mean(np.log(np.array(m) / np.array(b))))
        adm = all(res[r][(s, "clean")][0] <= res[base][(s, "clean")][0] + 0.05 for s in ("MF", "LC", "C02"))
        out[r] = (sc, adm)
        print("%-10s" % ("/".join(r) if isinstance(r, tuple) else r) + "".join("%10.3f" % x for x in m) + "   %+.4f  %s" % (sc, "yes" if adm else "NO"))
    return out

if __name__ == "__main__":
    st = sys.argv[1]
    if st == "A":
        order = ["F20", "gmin", "gmax", "psum", "agm", "ci", "wprod", "wmean", "min3", "minS", "smin", "minRF", "sminRF", "F16"]
        res = table(order, lambda r, c: "A_%s_%s" % (r, c))
        out = report(res, "F20", order, "rule")
        cand = [r for r in order if r != "F16" and out[r][1] and np.isfinite(out[r][0])]
        cand.sort(key=lambda r: out[r][0])
        best = cand[0]
        ties = [r for r in cand if out[r][0] <= out[best][0] + 0.01]
        pick = min(ties, key=order.index)
        print("\nadmissible, by score:", ", ".join("%s %+.4f" % (r, out[r][0]) for r in cand))
        print("stage A choice (ties within 0.01 -> first listed): %s; finalists for stage B: %s" % (pick, ", ".join([pick] + [r for r in cand if r != pick][:1])))
    elif st == "B":
        rules = sys.argv[2].split(",")
        vs = ["V0", "V1", "V1b", "V2"]
        order = [(r, v) for r in rules for v in vs]
        tagf = lambda rv, c: ("A_%s_%s" % (rv[0], c)) if rv[1] == "V0" else ("B_%s_%s_%s" % (rv[0], rv[1], c))
        res = table(order + [("F20", "V0")], tagf)
        out = report(res, ("F20", "V0"), order + [("F20", "V0")], "rule/v")
        tie = {"V0": 0, "V1b": 1, "V2": 2, "V1": 3}
        cand = [k for k in order if out[k][1] and np.isfinite(out[k][0])]
        cand.sort(key=lambda k: out[k][0])
        best = cand[0]
        ties = [k for k in cand if out[k][0] <= out[best][0] + 0.01]
        pick = min(ties, key=lambda k: (tie[k[1]], rules.index(k[0])))
        print("\nadmissible, by score:", ", ".join("%s/%s %+.4f" % (k[0], k[1], out[k][0]) for k in cand))
        print("stage B choice:", pick)
    elif st == "list":
        for pre in sys.argv[2:]:
            for s in SEQ:
                m, v = cell(pre, s)
                print("%-28s %-5s %s = %.3f" % (pre, s, " ".join("%.2f" % x for x in v), m))
        json.dump(cache, open(CACHE, "w"))
