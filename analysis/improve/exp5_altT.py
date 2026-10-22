import sys, os, numpy as np
os.chdir("/home/claude"); sys.path.insert(0,"/home/claude/sah"); sys.path.insert(0,"/home/claude/fusion_v3")
import cand, v2_tools as vt, fusion_core as fc, sah_replay as sr
from scipy.stats import spearmanr, rankdata
H="/home/claude/"
KF={"MF":[H+"data_in4/keyframes_F8_kf_run%d.npz"%i for i in (1,2,3)]+[H+"data_in5/keyframes_F8_kf_run%d.npz"%i for i in (4,5,6)],
    "LC":[H+"data_kf/LC_keyframes_F8_kf_run%d.npz"%i for i in (1,2,3)],
    "C02":[H+"data_kf/C02_keyframes_F8_kf_run%d.npz"%i for i in (1,2,3)]}
WIN=10.0
def kabsch(src,dst):
    mu_s,mu_d=src.mean(0),dst.mean(0); U,_,Vt=np.linalg.svd((dst-mu_d).T@(src-mu_s)); S=np.eye(3)
    if np.linalg.det(U)*np.linalg.det(Vt)<0: S[2,2]=-1
    R=U@S@Vt; return R, mu_d-R@mu_s
def rank_resid(y,x):
    ry,rx=rankdata(y),rankdata(x); b=np.polyfit(rx,ry,1); return ry-np.polyval(b,rx)
rows=[]   # per window: seq, run, err/m (all), err/m along weak, schur lam_min, schur kappa, T l1, T_vv, dir agreement
for seq in ("MF","LC","C02"):
    gt_t,gt_p=vt.load_gt(cand.SEQ[seq][0])
    for run,(lg,kf) in enumerate(zip(cand.SEQ[seq][1],KF[seq])):
        d=cand.load(lg); N=sr.kf_normals(kf); keys=np.array(sorted(N))
        t=d["t"]; P=np.array([a[1] for a in d["aft"]]); Rl=[a[0] for a in d["aft"]]
        G=np.array([np.interp(t,gt_t,gt_p[:,c]) for c in range(3)]).T
        Ra,ta=kabsch(P,G)
        for kk in keys:
            k=int(np.searchsorted(t,kk-0.002))
            if k>=len(t) or abs(t[k]-kk)>0.003: continue
            k2=int(np.searchsorted(t,t[k]+WIN))
            if k2>=len(t) or d["H"][k] is None: continue
            dp=P[k2]-P[k]; dist=np.linalg.norm(G[k2]-G[k])
            if dist<2.0: continue
            e=Ra@dp-(G[k2]-G[k])
            S_RR,S_tt,kR,kt=fc.schur_blocks(np.asarray(d["H"][k],float),d["hess_frame"],Rl[k])
            w,V=np.linalg.eigh(S_tt); v_body=V[:,0]
            nb=N[kk][0].astype(float)
            if len(nb)<200: continue
            T=nb.T@nb/len(nb); tw,tV=np.linalg.eigh(T)
            vw=Ra@(Rl[k]@v_body)           # weakest Schur direction in the GT frame
            rows.append((seq,run,np.linalg.norm(e)/dist,abs(e@vw)/dist,w[0],kt,tw[0],float(v_body@T@v_body),abs(v_body@tV[:,0])))
import pickle; pickle.dump(rows,open("/home/claude/improve/exp5_rows.pkl","wb"))
print("windows per sequence:",{s:sum(1 for r in rows if r[0]==s) for s in ("MF","LC","C02")})
rng=np.random.default_rng(0)
def blockboot(fn,n,B=300,bl=10):
    idx=np.arange(n); out=[]
    nb=int(np.ceil(n/bl))
    for _ in range(B):
        st=rng.integers(0,n,nb); ii=np.concatenate([(s+np.arange(bl))%n for s in st])[:n]; out.append(fn(ii))
    return np.percentile(out,[2.5,97.5])
for seq in ("MF","LC","C02"):
    R=[r for r in rows if r[0]==seq]; n=len(R)
    ea=np.array([r[2] for r in R]); ew=np.array([r[3] for r in R]); lam=np.array([r[4] for r in R]); kt=np.array([r[5] for r in R])
    l1=np.array([r[6] for r in R]); tvv=np.array([r[7] for r in R]); ag=np.array([r[8] for r in R])
    print("\n== %s: %d windows of %.0f s (>=2 m travelled)"%(seq,n,WIN))
    print("   median |dir agreement| Schur-weak vs T-weak eigvec: %.2f"%np.median(ag))
    for lab,y in (("error/m (all)",ea),("error/m along Schur-weak dir",ew)):
        # predictors: higher predicted uncertainty should mean higher error
        sch=-lam; altl1=-l1; alttvv=-tvv
        rs=spearmanr(sch,y)[0]; r1=spearmanr(altl1,y)[0]; rv=spearmanr(alttvv,y)[0]
        pa=spearmanr(rank_resid(altl1,sch),rank_resid(y,sch))[0]; pv=spearmanr(rank_resid(alttvv,sch),rank_resid(y,sch))[0]
        f=lambda ii: spearmanr(rank_resid(altl1[ii],sch[ii]),rank_resid(y[ii],sch[ii]))[0]
        ci=blockboot(f,n)
        print("   %-30s Spearman: Schur lam_min %+.2f | alt-T l1 %+.2f | alt-T along Schur-weak dir %+.2f || partial alt-T l1 | Schur %+.2f [%.2f,%.2f]; partial T_vv | Schur %+.2f"%(lab,rs,r1,rv,pa,ci[0],ci[1],pv))
