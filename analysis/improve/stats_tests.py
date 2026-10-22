import sys, numpy as np, itertools
from scipy import stats
sys.path.insert(0, "/home/claude/sah"); sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt, sah_replay3 as sr
rng = np.random.default_rng(1)

def holm(ps):
    o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for rank, i in enumerate(o):
        run = max(run, (m - rank) * ps[i]); adj[i] = min(1.0, run)
    return adj
def hedges_g(a, b):
    na, nb = len(a), len(b); sp = np.sqrt(((na-1)*np.var(a, ddof=1) + (nb-1)*np.var(b, ddof=1)) / (na+nb-2))
    return (np.mean(a) - np.mean(b)) / sp * (1 - 3/(4*(na+nb)-9))
def boot_diff(a, b, n=20000):
    d = [np.mean(rng.choice(a, len(a))) - np.mean(rng.choice(b, len(b))) for _ in range(n)]
    return np.percentile(d, [2.5, 97.5])
def two_sample(name, a, b, la, lb):
    a, b = np.asarray(a, float), np.asarray(b, float)
    w = stats.ttest_ind(a, b, equal_var=False)
    u = stats.mannwhitneyu(a, b, alternative="two-sided", method="exact")
    pt = stats.permutation_test((a, b), lambda x, y: np.mean(x) - np.mean(y), n_resamples=20000, permutation_type="independent", random_state=1)
    lo, hi = boot_diff(a, b)
    return dict(name=name, la=la, lb=lb, na=len(a), nb=len(b), ma=a.mean(), mb=b.mean(), diff=a.mean()-b.mean(), ci=(lo, hi),
                welch=w.pvalue, mwu=u.pvalue, perm=pt.pvalue, g=hedges_g(a, b), minp=2/np.math.comb(len(a)+len(b), len(a)) if hasattr(np, "math") else 0)
def show(r):
    print("%-34s %s n=%d mean %.3f  vs  %s n=%d mean %.3f | diff %+.3f  95%% boot CI [%+.3f, %+.3f] | Welch p=%.4f  MWU(exact) p=%.4f  perm p=%.4f | Hedges g=%.2f" % (
        r["name"], r["la"], r["na"], r["ma"], r["lb"], r["nb"], r["mb"], r["diff"], r["ci"][0], r["ci"][1], r["welch"], r["mwu"], r["perm"], r["g"]))

print("=" * 110, "\nA. BETWEEN CONFIGURATIONS: independent live runs (A-LOAM stack), two-sided\n", "=" * 110, sep="")
data = {
 "MF F8 1.0x": [0.74,0.51,0.54,0.77,0.73,0.62,0.58,0.59,0.47], "MF F8 0.5x": [0.73,0.52,0.56], "MF F16": [0.56,0.80,0.53,0.58,0.77,0.60],
 "LC F8": [4.76,4.87,3.97], "LC F16": [1.99,2.16,3.17,2.13,2.00,2.19],
 "C02 F8": [2.07,2.10,2.19], "C02 F16": [1.69,1.72,1.68,1.68,1.64,1.84],
}
rows = [two_sample("SAH effect, Long Corridor", data["LC F8"], data["LC F16"], "F8", "F16"),
        two_sample("SAH effect, Corridor02", data["C02 F8"], data["C02 F16"], "F8", "F16"),
        two_sample("SAH effect, Multi Floor (matched 0.5x)", data["MF F8 0.5x"], data["MF F16"], "F8", "F16"),
        two_sample("SAH effect, Multi Floor (all F8)", data["MF F8 1.0x"], data["MF F16"], "F8", "F16")]
for r in rows: show(r)
adj = holm([r["mwu"] for r in rows]); print("Holm-adjusted MWU p (4 tests):", np.round(adj, 4))
print("note: exact MWU minimum attainable two-sided p: 3v6 = %.4f, 3v3 = %.4f, 4v6 = %.4f, 4v9 = %.4f" % (2/84, 2/20, 2/210, 2/715))

# ---------------- GenZ stack: 4 independent GenZ-LIO runs on Multi Floor
D0 = "/tmp/claude-0/g0mf/"; D1 = "/tmp/claude-0/g17/"
gt_t, gt_p = vt.load_gt(D0 + "ground_truth_path.csv")
runs = [(D0 + "switching_log_v2_G0_kf_run%d.csv" % i, D0 + "keyframes_G0_kf_run%d.npz" % i) for i in (1, 2, 3)] + \
       [(D1 + "switching_log_v2_G17_kf_run1.csv", D1 + "keyframes_G17_kf_run1.npz")]
sah = dict(v3=6, bound_R=True)
def err_series(t, p):
    m = (t >= gt_t[0]) & (t <= gt_t[-1]) & np.isfinite(p).all(1)
    g = np.stack([np.interp(t[m], gt_t, gt_p[:, i]) for i in range(3)], 1)
    R, tr = vt.umeyama(p[m], g)
    return t[m], np.linalg.norm(p[m] @ R.T + tr - g, axis=1)
cfgs = {"G0": None, "G8": None, "G9": None, "G17": sah}
res, E = {k: [] for k in cfgs}, {k: [] for k in cfgs}
for lp, kp in runs:
    d = vt.load_v2_log(lp); K = sr.kf_normals(kp)
    out = {"G0": sr.run(d, K, c_t=0.0, c_R=0.0, t_warm=1e12)[0], "G8": sr.run(d, K, c_t=1e-4)[0],
           "G9": sr.run(d, K, c_t=3e-6, c_R=5e-6)[0], "G17": sr.run(d, K, sah_kw=sah, c_t=3e-6, c_R=5e-6)[0]}
    for k, p in out.items():
        te, e = err_series(d["t"], p); res[k].append(float(np.sqrt((e**2).mean()))); E[k].append((te, e))
print("\n", "=" * 110, "\nB. GenZ STACK, Multi Floor: 4 independent GenZ-LIO runs, same run -> paired\n", "=" * 110, sep="")
for k in cfgs: print("%-4s per-run ATE %s mean %.3f sd %.3f" % (k, np.round(res[k], 3), np.mean(res[k]), np.std(res[k], ddof=1)))
def paired(a, b, la, lb):
    a, b = np.asarray(a), np.asarray(b); d = a - b
    t = stats.ttest_rel(a, b); w = stats.wilcoxon(a, b, method="exact")
    lr = np.log(a/b); tl = stats.ttest_1samp(lr, 0); ci = stats.t.interval(0.95, len(lr)-1, loc=lr.mean(), scale=stats.sem(lr))
    print("%-10s vs %-4s mean diff %+.3f | paired t p=%.4f | Wilcoxon exact p=%.4f (min possible %.4f) | all %d/%d runs lower | mean ratio %.2f (95%% CI %.2f-%.2f, log-scale t)" % (
        la, lb, d.mean(), t.pvalue, w.pvalue, 2/2**len(d), int((d < 0).sum()), len(d), np.exp(lr.mean()), np.exp(ci[0]), np.exp(ci[1])))
paired(res["G9"], res["G0"], "G9", "G0"); paired(res["G17"], res["G0"], "G17", "G0"); paired(res["G17"], res["G9"], "G17", "G9"); paired(res["G8"], res["G0"], "G8 (old rule)", "G0")
print("\nG17 (4 GenZ runs) vs the A-LOAM stack, independent two-sided:")
for lab, b in (("F8 (9 runs)", data["MF F8 1.0x"]), ("F16 (6 runs)", data["MF F16"])):
    show(two_sample("MF G17 vs " + lab, res["G17"], b, "G17", "F")); 
show(two_sample("MF G0 (GenZ alone) vs F16", res["G0"], data["MF F16"], "G0", "F16"))

print("\n", "=" * 110, "\nC. RUN-TO-RUN VARIATION (chi-square tests on the variance)\n", "=" * 110, sep="")
def chi2_var(x, s0, label):
    n = len(x); s2 = np.var(x, ddof=1); stat = (n-1)*s2/s0**2
    p_hi = stats.chi2.sf(stat, n-1); lo = np.sqrt((n-1)*s2/stats.chi2.ppf(0.975, n-1)); hi = np.sqrt((n-1)*s2/stats.chi2.ppf(0.025, n-1))
    print("%-30s n=%d sd=%.3f  95%% CI for sigma [%.3f, %.3f] | H0 sigma=%.3f: chi2=%.2f, p(sigma > H0)=%.3f, p(sigma < H0)=%.3f" % (label, n, np.sqrt(s2), lo, hi, s0, stat, p_hi, 1-p_hi))
chi2_var(res["G0"], np.std(data["MF F16"], ddof=1), "G0 vs F16's sd (0.115)")
chi2_var(res["G17"], np.std(data["MF F16"], ddof=1), "G17 vs F16's sd (0.115)")
chi2_var(data["MF F16"], 0.115, "F16 (6 runs) vs 0.115")
lev = stats.levene(res["G0"], res["G17"], data["MF F16"], center="median"); print("Brown-Forsythe equal-variance test, G0 / G17 / F16 (run-level ATE): W=%.2f p=%.3f" % (lev.statistic, lev.pvalue))
print("F-test of variance ratio G0/G17: F=%.2f p=%.3f (two-sided)" % ((np.var(res["G0"], ddof=1)/np.var(res["G17"], ddof=1)), 2*min(stats.f.sf(np.var(res["G0"], ddof=1)/np.var(res["G17"], ddof=1), 3, 3), stats.f.cdf(np.var(res["G0"], ddof=1)/np.var(res["G17"], ddof=1), 3, 3))))

print("\n", "=" * 110, "\nD. WITHIN-RUN: do the 4 GenZ runs differ? per-30-s-window error (RMSE of position error per window)\n", "=" * 110, sep="")
def windows(te, e, w=30.0):
    k = ((te - te[0]) // w).astype(int); return np.array([np.sqrt((e[k == j]**2).mean()) for j in np.unique(k) if (k == j).sum() >= 20])
W = {c: [windows(*E[c][i]) for i in range(4)] for c in cfgs}
for c in ("G0", "G17"):
    kw = stats.kruskal(*W[c]); thr = np.median(np.concatenate(W[c]))
    tab = np.array([[ (w > thr).sum(), (w <= thr).sum()] for w in W[c]]); ch = stats.chi2_contingency(tab)
    print("%-4s windows/run %s | Kruskal-Wallis across runs: H=%.2f p=%.3f | chi-square homogeneity (window error above/below pooled median): chi2=%.2f dof=%d p=%.3f" % (
        c, [len(w) for w in W[c]], kw.statistic, kw.pvalue, ch[0], ch[2], ch[1]))
print("\nPaired per-window comparison inside each run (same windows, G17 vs G0), Wilcoxon signed-rank:")
for i in range(4):
    a, b = W["G17"][i], W["G0"][i]; w = stats.wilcoxon(a, b)
    print("  run %d: %d windows, G17 lower in %d, median window error %.3f vs %.3f m, p=%.4f" % (i+1, len(a), int((a < b).sum()), np.median(a), np.median(b), w.pvalue))
a = np.concatenate(W["G17"]); b = np.concatenate(W["G0"]); d = a - b
blocks = [(i, j) for i in range(4) for j in range(len(W["G17"][i]))]
bs = [np.mean(np.concatenate([ (W["G17"][i] - W["G0"][i])[rng.integers(0, len(W["G17"][i]), len(W["G17"][i]))] for i in rng.integers(0, 4, 4)])) for _ in range(5000)]
print("pooled %d windows: G17 lower in %d (%.0f%%), mean window-error change %+.3f m, run-resampled bootstrap 95%% CI [%+.3f, %+.3f]" % (len(d), int((d < 0).sum()), 100*(d < 0).mean(), d.mean(), *np.percentile(bs, [2.5, 97.5])))
print("\nHOW MANY GenZ RUNS are needed for a paired exact Wilcoxon to reach p<0.05 two-sided: n>=6 (min p: n=3 0.25, n=4 0.125, n=5 0.0625, n=6 0.031)")
