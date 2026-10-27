import sys,os,csv,numpy as np
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import v2_tools as vt
# usage: python3 -I score_iglio_fused.py <fused (I20) switching log> <GenZ-LIO (G0) switching log>; env IGLIO_GT = Multi Floor ground_truth_path.csv
gt_t,gt_p=vt.load_gt(os.environ["IGLIO_GT"])
gi=lambda tt:np.stack([np.interp(tt,gt_t,gt_p[:,k]) for k in range(3)],1)
def um(A,B):
    ma,mb=A.mean(0),B.mean(0);C=(B-mb).T@(A-ma)/len(A);U,Sg,Vt=np.linalg.svd(C);D=np.eye(3);D[2,2]=np.sign(np.linalg.det(U@Vt));Rr=U@D@Vt;return Rr,mb-Rr@ma
def load(path):
    rows=list(csv.DictReader(open(path))); g=lambda k:np.array([float(r[k]) for r in rows])
    t=g('time'); F=np.stack([g('fused_x'),g('fused_y'),g('fused_z')],1); A=np.stack([g('aft_x'),g('aft_y'),g('aft_z')],1)
    V=np.full((len(t),3),np.nan); d=vt.load_v2_log(path)
    for i,v in enumerate(d["vins"]):
        if v is not None: V[i]=v[1]+v[0]@vt.t_IL
    return t,F,A,V,rows
def ate(t,P,T0,T1):
    m=(t>=t[0]+T0)&(t<=t[0]+T1)&np.isfinite(P).all(1)&(t>=gt_t[0])&(t<=gt_t[-1]); G=gi(t[m]); Rr,tt=um(P[m],G); Q=(Rr@P[m].T).T+tt
    return round(float(np.sqrt((np.linalg.norm(Q-G,axis=1)**2).mean())),3)
t,F,A,V,rows=load(sys.argv[1]); tg,Fg,Ag,Vg,_=load(sys.argv[2])
print("rows",len(t),"span",round(t[-1]-t[0],1),"NaN fused",np.isnan(F).any())
st=np.linalg.norm(np.diff(F,axis=0),axis=1); print("fused max step",st.max().round(3),"| path",st.sum().round(1))
for (a,b) in ((0,120),(0,300),(40,300),(120,300)):
    print(f"window {a}-{b}s: fused {ate(t,F,a,b)}  iG-LIO(aft) {ate(t,A,a,b)}  VINS {ate(t,V,a,b)}  GenZ-LIO(G0) {ate(tg,Ag,a,b)}")
d=np.linalg.norm(F-A,axis=1); print("fused-vs-iGLIO dist (after fused starts): median %.3f p95 %.3f max %.3f"%(np.median(d[200:]),np.percentile(d[200:],95),d[200:].max()))
modes={}
for r in rows: modes[r['mode']]=modes.get(r['mode'],0)+1
print(modes)
gam=np.array([float(r['vio_gamma']) for r in rows]); s=np.array([float(r['s_vio']) for r in rows]); gate=np.array([float(r['gate']) for r in rows])
f=np.array([r['mode']=='FUSED' for r in rows])
print("gamma (fused rows): mean %.3f, frac 0: %.3f, frac 1: %.3f"%(gam[f].mean(),(gam[f]==0).mean(),(gam[f]==1).mean()))
print("s_vio: min %.3f median %.3f max %.3f"%(np.nanmin(s[f]),np.nanmedian(s[f]),np.nanmax(s[f])))
for c in ('wt0','wt1','wt2','wR0','wR1','wR2','sah_total_deg','dta','dtv'):
    x=np.array([float(r[c]) for r in rows])[f]; print(f"  {c}: p10/p50/p90",np.round(np.nanpercentile(x,[10,50,90]),4))
