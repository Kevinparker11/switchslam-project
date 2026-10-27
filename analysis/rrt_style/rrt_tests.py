"""RRT*-paper-style evaluation (Ganesan et al., ESWA 258 (2024) 125206, Tables 1-3) applied to our recordings.
Table A: min / median / max / mean of each method + improvement of G20 = (baseline - G20) / baseline on the mean (and median).
Table B: success rate (ATE <= 10 m, i.e. no gross divergence).
Table C: H0: M(baseline) = M(G20), H1: M(baseline) > M(G20), one-sided, alpha 0.05, paired by recording:
         Wilcoxon signed-rank (exact; primary, no normality assumed) and paired t-test (parametric version)."""
import json,glob,os,sys,numpy as np
from scipy import stats
S=os.path.dirname(os.path.abspath(__file__))+"/.."; U=S+"/clean4/analysis/improve/universal"
J={}
for d in (U+"/out",U+"/out_live",U+"/out_live2",U+"/out_gz",S+"/rrt/vins"):
    for f in glob.glob(d+"/*.json"):
        r=json.load(open(f)); J[(r['log'],r['cfg'])]=r
SEQ={'MF':'Multi Floor','LC':'Long Corridor','CV':'Cave02','C02':'Corridor02','GEO':'GEODE stairs (PC)','GZ':'Gazebo office'}
PREF=lambda n:n.split('-')[0]
logs=sorted({k[0] for k in J if k[1]=='G20'})
METH=[('GZ','GenZ-LIO alone'),('VI','VINS-Mono alone'),('G17','G17 (fusion, no gate)'),('G20','G20 (proposed)')]
SUCC=10.0
out=[]; P=lambda *a:out.append(" ".join(str(x) for x in a))
rows=[]
for sq in SEQ:
    L=[l for l in logs if PREF(l)==sq and all((l,m) in J for m,_ in METH)]
    if not L: continue
    A={m:np.array([J[(l,m)]['ate'] for l in L]) for m,_ in METH}
    X={m:np.array([J[(l,m)]['max'] for l in L]) for m,_ in METH}
    rows.append((sq,L,A,X))
P("## Table A - accuracy per environment (full-span ATE RMSE, m; n = recordings)")
P("| Environment | Method | n | Min | Median | Max | Mean | Improvement of G20 (mean) | Improvement of G20 (median) |"); P("|---|---|---|---|---|---|---|---|---|")
for sq,L,A,X in rows:
    for m,lab in METH:
        a=A[m]; g=A['G20']
        imp=lambda b,p: ("↑ %.1f%%"%(100*(b-p)/b)) if b>p else ("↓ %.1f%%"%(100*(p-b)/b))
        P(f"| {SEQ[sq]} | {lab} | {len(a)} | {a.min():.3f} | {np.median(a):.3f} | {a.max():.3f} | {a.mean():.3f} | {'-' if m=='G20' else imp(a.mean(),g.mean())} | {'-' if m=='G20' else imp(np.median(a),np.median(g))} |")
P("\n## Table B - success rate (run with full-span ATE <= %g m) and worst-case error (median of the per-run maximum error, m)"%SUCC)
P("| Environment | n | "+" | ".join(lab for _,lab in METH)+" |"); P("|---|---|"+"---|"*len(METH))
for sq,L,A,X in rows:
    P(f"| {SEQ[sq]} | {len(L)} | "+" | ".join(f"{100*np.mean(A[m]<=SUCC):.0f}% / {np.median(X[m]):.2f}" for m,_ in METH)+" |")
P("\n## Table C - hypothesis test, H0: M(baseline) = M(G20), H1: M(baseline) > M(G20) (one-sided, paired by recording, alpha = 0.05)")
P("| Baseline | Environment | n | G20 lower in | p (Wilcoxon, exact) | Reject H0 | p (paired t) | Reject H0 (t) |"); P("|---|---|---|---|---|---|---|---|")
fam=[]
for m,lab in METH[:-1]:
    for sq,L,A,X in rows:
        b,g=A[m],A['G20']; d=b-g; n=len(d)
        if n<3: P(f"| {lab} | {SEQ[sq]} | {n} | {int((d>0).sum())} of {n} | n too small | - | - | - |"); continue
        if np.all(d==0): pw=1.0
        else: pw=stats.wilcoxon(b,g,alternative='greater',method='exact' if n<=25 and len(set(np.round(np.abs(d[d!=0]),9)))==len(d[d!=0]) else 'auto',zero_method='wilcox').pvalue
        pt=stats.ttest_rel(b,g,alternative='greater').pvalue
        fam.append((pw,lab,sq))
        P(f"| {lab} | {SEQ[sq]} | {n} | {int((d>0).sum())} of {n} | {pw:.3g} | {'Yes' if pw<0.05 else 'No'} | {pt:.3g} | {'Yes' if pt<0.05 else 'No'} |")
# reverse direction where G20 lost: H1 M(G20) > M(baseline)
P("\n### Reverse direction (H1: M(G20) > M(baseline)), same data")
P("| Baseline | Environment | n | p (Wilcoxon) | G20 significantly worse |"); P("|---|---|---|---|---|")
for m,lab in METH[:-1]:
    for sq,L,A,X in rows:
        b,g=A[m],A['G20']; n=len(b)
        if n<3 or np.all(b==g): continue
        pw=stats.wilcoxon(g,b,alternative='greater').pvalue
        P(f"| {lab} | {SEQ[sq]} | {n} | {pw:.3g} | {'Yes' if pw<0.05 else 'No'} |")
# Holm over the forward family
fam.sort(); k=len(fam); P("\nHolm over the %d forward Wilcoxon tests (family-wise 0.05):"%k)
rej=[]; 
for i,(p,lab,sq) in enumerate(fam):
    if p<=0.05/(k-i): rej.append(f"{lab} / {SEQ[sq]} (p {p:.3g})")
    else: break
P("rejected after Holm: "+("; ".join(rej) if rej else "none"))
P("\nRecordings per environment: "+"; ".join(f"{SEQ[sq]}: {', '.join(L)}" for sq,L,A,X in rows))
open(S+"/rrt/rrt_tables.md","w").write("\n".join(out)); print("\n".join(out))
