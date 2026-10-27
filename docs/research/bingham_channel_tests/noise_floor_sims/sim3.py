import numpy as np
from sim2 import *
rng2 = np.random.default_rng(5)
k, rmax = 20, 20
t, ok = cast(D, rmax); Dok = D[ok]; tok = t[ok]
n0, w0, V0, _ = normals_pca(Dok*tok[:,None], k)
l10, tvv0, _ = tensor_stats(n0)
print("noise-free pipeline l1 (deterministic estimator bias) =", l10)
for sig in [0.005, 0.01, 0.02, 0.03]:
    ls=[]; lc=[]; tv=[]
    for b in range(12):
        nA,_,_,_ = normals_pca(Dok*(tok+sig*rng2.standard_normal(len(tok)))[:,None], k)
        nB,_,_,_ = normals_pca(Dok*(tok+sig*rng2.standard_normal(len(tok)))[:,None], k)
        # sign alignment for cross product is irrelevant only if sign flips are consistent: align
        sgn = np.sign(np.sum(nA*nB,1)); nB = nB*sgn[:,None]
        T = nA.T@nB/len(nA); Ts = (T+T.T)/2
        lc.append(np.linalg.eigvalsh(Ts)[0])
        T2 = nA.T@nA/len(nA); ls.append(np.linalg.eigvalsh(T2)[0])
    ls=np.array(ls); lc=np.array(lc)
    print(f"sigma_r={sig}: self-T l1 mean={ls.mean():.3e} sd={ls.std():.1e} | excess over noise-free={ls.mean()-l10:.3e} ratio to sigma^2={(ls.mean()-l10)/sig**2:.1f} | cross-fit (2 indep. scans) l1 mean={lc.mean():.3e} sd={lc.std():.1e}")
