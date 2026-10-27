"""Table 3 of the Hybrid-RRT* paper (Ganesan et al., ESWA 258 (2024) 125206) for this project: hypothesis test of the proposed method
against each baseline, per environment and parameter.  H0: M(ALGM1) = M(ALGM2)   H1: M(ALGM1) > M(ALGM2)   (ALGM1 = baseline, ALGM2 = proposed),
alpha = 0.05.  M = the per-recording value of the metric; the test is paired by recording (exact one-sided Wilcoxon signed-rank; the
paired t-test is given beside it).  Inputs: rrt/m/*.json (rrt_metrics.py), rrt/out_*.json (rrt_outage_metrics.py).
usage: python3 -I table3.py <dir with m/ and out_*.json> <output .md>"""
import sys, os, glob, json, numpy as np
from scipy import stats
D, OUT = sys.argv[1], sys.argv[2]
NAME = "RTS-Fusion"
PAR = [("ate", "ATE RMSE (m)"), ("maxerr", "max error (m)"), ("rpe10", "RPE 10 s (m)"), ("rot10", "rotation drift 10 s (deg)")]
SEQ = [("MF", "Multi Floor"), ("LC", "Long Corridor"), ("CV", "Cave02"), ("GEO", "GEODE stairs (PC)"), ("GZ", "Gazebo office")]
BASE = [("GZ", "GenZ-LIO alone"), ("VI", "VINS-Mono alone"), ("SW", "Switch-SLAM rule (re-run)"), ("SWR", "Switch-SLAM rule, whole-pose switch (variant)"), ("G17", "RTS-core (G17, no safeguards)")]
R = {}
for f in glob.glob(D + "/m/*.json"):
    r = json.load(open(f)); R[r["log"]] = r
def prefix(n): return n.split("-")[0]
def tests(b, p):
    m = np.isfinite(b) & np.isfinite(p); b, p = b[m], p[m]; n = len(b); d = b - p
    if n < 3: return n, None, None, None, int((d > 0).sum())
    if np.all(d == 0): pw, pr = 1.0, 1.0
    else:
        pw = stats.wilcoxon(b, p, alternative="greater", zero_method="wilcox").pvalue
        pr = stats.wilcoxon(p, b, alternative="greater", zero_method="wilcox").pvalue
    pt = stats.ttest_rel(b, p, alternative="greater").pvalue if np.any(d != 0) else 1.0
    return n, pw, pt, pr, int((d > 0).sum())
fmt = lambda x: "%.3g" % x
rows, fam = [], []
def block(title, groups, base_list, prop_key, getter):
    out = ["", "### " + title, "", "| Algorithm | Environment | Parameter | n | RTS better in | p-value (Wilcoxon) | Reject H0 | p-value (paired t) | Reject H0 (t) |", "|---|---|---|---|---|---|---|---|---|"]
    for bk, bl in base_list:
        for gk, gl, recs in groups:
            first = True
            for pk, pl in PAR:
                b = np.array([getter(r, bk, pk) for r in recs], float); p = np.array([getter(r, prop_key, pk) for r in recs], float)
                n, pw, pt, pr, k = tests(b, p)
                if pw is None:
                    out.append(f"| {bl if first else ''} | {gl if first else ''} | {pl} | {n} | - | n too small | - | - | - |")
                else:
                    rev = " (RTS significantly worse, p %s)" % fmt(pr) if pr < 0.05 else ""
                    out.append(f"| {bl if first else ''} | {gl if first else ''} | {pl} | {n} | {k} of {n} | {fmt(pw)} | {'Yes' if pw < 0.05 else 'No'}{rev} | {fmt(pt)} | {'Yes' if pt < 0.05 else 'No'} |")
                    fam.append((pw, bl, gl, pl))
                first = False
    return out
groups = []
for sk, sl in SEQ:
    recs = [r for n, r in sorted(R.items()) if prefix(n) == sk]
    if recs: groups.append((sk, sl, recs))
g = lambda r, m, k: r["methods"][m][k]
L = ["# Table 3 for this project: hypothesis test of %s against each baseline" % NAME, "",
     "H0: M(ALGM1) = M(ALGM2), H1: M(ALGM1) > M(ALGM2); ALGM1 = baseline, ALGM2 = %s (= G20); 95 %% confidence (reject when p < 0.05). Paired by recording; \"RTS better in k of n\" counts the recordings where the baseline's value is larger. Recordings: %s." % (NAME, "; ".join("%s %d" % (sl, len(recs)) for _, sl, recs in groups))]
L += block("Real recordings and the Gazebo office", groups, BASE, "G20", g)
# Switch-SLAM published (Table II): one-sample, MF and LC only
pub = {"MF": (1.61, 3.63), "LC": (2.42, 5.09)}
L += ["", "### Switch-SLAM as published (RA-L 2024, Table II; one value per sequence, no per-run data)", "",
      "Test: one-sample exact Wilcoxon signed-rank of the %s per-recording values against the published value; H1: published > %s. Only the two metrics Switch-SLAM reports. Different setup and single run: indicative only." % (NAME, NAME), "",
      "| Algorithm | Environment | Parameter | published | n | RTS better in | p-value (Wilcoxon) | Reject H0 |", "|---|---|---|---|---|---|---|---|"]
for sk, sl, recs in groups:
    if sk not in pub: continue
    for i, (pk, pl) in enumerate(PAR[:2]):
        x = np.array([g(r, "G20", pk) for r in recs], float); c = pub[sk][i]; d = c - x
        pw = stats.wilcoxon(d, alternative="greater").pvalue
        L.append(f"| Switch-SLAM (published) | {sl} | {pl} | {c} | {len(x)} | {int((d > 0).sum())} of {len(x)} | {fmt(pw)} | {'Yes' if pw < 0.05 else 'No'} |")
# outage block
O = {}
for f in glob.glob(D + "/out_*.json"): O.update(json.load(open(f)))
bags = sorted({k.split("|")[0] for k in O})
og = lambda r, m, k: r[m][k]
rec = [{"G20": O[b + "|G20"]["fused"], "G23": O[b + "|G23"]["fused"], "GZ": O[b + "|G23"]["GZ"], "VI": O[b + "|G23"]["VI"]} for b in bags]
OG = lambda r, m, k: r[m][k]
L += block("Outage block: 9 bags with LiDAR outages (live logs); proposed = %s with the gap rule (G23)" % NAME,
           [("OUT", "LiDAR outages (9 bags)", rec)], [("GZ", "GenZ-LIO alone"), ("VI", "VINS-Mono alone"), ("G20", "%s without gap rule (G20)" % NAME)], "G23", OG)
fam.sort()
k = len(fam); rej = []
for i, (p, bl, gl, pl) in enumerate(fam):
    if p <= 0.05 / (k - i): rej.append((bl, gl, pl, p))
    else: break
L += ["", "Holm correction over all %d Wilcoxon tests above (family-wise 0.05): %d rejected." % (k, len(rej))]
L += ["", "Notes: (1) n = 4 cannot give an exact one-sided Wilcoxon p below 0.0625, so Cave02 and Gazebo cannot reach \"Yes\"; Corridor02 has one recording and is not tested. (2) \"Switch-SLAM rule (re-run)\" is our re-implementation of its detection rule (the three smallest normalised eigenvalues of the 6x6 Hessian against 0.12 / 0.27 / 0.48) as an all-or-nothing switch of the translation between GenZ-LIO and VINS-Mono, rotation always from VINS-Mono (the project's F12, defined on 13 Oct, before this test), replayed on the same recordings; the \"whole-pose\" variant switches the rotation too and is much worse (it mixes LiDAR rotation with VIO translation increments). Neither is the authors' code or pipeline; the rows against the published Switch-SLAM numbers are the fair comparison to the paper. (3) Outage block: GenZ-LIO alone and VINS-Mono alone come from the same live logs as the G23 run, G20 from its own live log; GenZ-LIO differs between the G20 and G23 runs of a bag (see Gap_Test_Results.md). Switch-SLAM is not run on the outage bags (its rule has no behaviour for missing LiDAR data)."]
open(OUT, "w").write("\n".join(L)); print("\n".join(L))
