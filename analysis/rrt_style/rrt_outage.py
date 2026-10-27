import json,numpy as np,os
from scipy import stats
S=os.path.dirname(os.path.abspath(__file__))+"/.."
R={}
for q in ('MF','LC','C02'): R.update(json.load(open(S+f"/gap_score_{q}.json")))
bags=sorted({k.split('|')[0] for k in R})
G23=np.array([R[b+'|G23']['fused'] for b in bags]); G20=np.array([R[b+'|G20']['fused'] for b in bags])
GZ=np.array([R[b+'|G23']['g0'] for b in bags]); VI=np.array([R[b+'|G23']['vins'] for b in bags])
out=["## Outage block (gap test, 9 rewritten bags with LiDAR outages, live; proposed = G23)",
"| Method | n | Min | Median | Max | Mean | Success (ATE <= 10 m) | Improvement of G23 (median) |","|---|---|---|---|---|---|---|---|"]
for lab,a in (('GenZ-LIO alone (G23-run log)',GZ),('VINS-Mono alone',VI),('G20',G20),('G23 (proposed for outages)',G23)):
    im='-' if a is G23 else (("↑ %.1f%%"%(100*(np.median(a)-np.median(G23))/np.median(a))) if np.median(a)>np.median(G23) else ("↓ %.1f%%"%(100*(np.median(G23)-np.median(a))/np.median(a))))
    out.append(f"| {lab} | {len(a)} | {a.min():.2f} | {np.median(a):.2f} | {a.max():.2f} | {a.mean():.2f} | {100*np.mean(a<=10):.0f}% | {im} |")
out+=["","| Baseline | n | G23 lower in | p (Wilcoxon, exact) | Reject H0 | p (paired t) | Reject H0 (t) | p reverse (G23 worse) |","|---|---|---|---|---|---|---|---|"]
for lab,b in (('GenZ-LIO alone',GZ),('VINS-Mono alone',VI),('G20',G20)):
    pw=stats.wilcoxon(b,G23,alternative='greater').pvalue; pt=stats.ttest_rel(b,G23,alternative='greater').pvalue; pr=stats.wilcoxon(G23,b,alternative='greater').pvalue
    out.append(f"| {lab} | 9 | {int((b>G23).sum())} of 9 | {pw:.3g} | {'Yes' if pw<0.05 else 'No'} | {pt:.3g} | {'Yes' if pt<0.05 else 'No'} | {pr:.3g} |")
out.append("\nBags: "+", ".join(bags))
open(S+"/rrt/rrt_outage.md","w").write("\n".join(out)); print("\n".join(out))
