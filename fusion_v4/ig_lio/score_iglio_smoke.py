import sys,os,csv,numpy as np
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import v2_tools as vt
# usage: python3 -I score_iglio_smoke.py <iglio switching log> <GenZ-LIO (G0) switching log>; env IGLIO_GT = Multi Floor ground_truth_path.csv
gt_t,gt_p=vt.load_gt(os.environ["IGLIO_GT"])
gi=lambda tt:np.stack([np.interp(tt,gt_t,gt_p[:,k]) for k in range(3)],1)
def um(A,B):
    ma,mb=A.mean(0),B.mean(0);C=(B-mb).T@(A-ma)/len(A);U,Sg,Vt=np.linalg.svd(C);D=np.eye(3);D[2,2]=np.sign(np.linalg.det(U@Vt));Rr=U@D@Vt;return Rr,mb-Rr@ma
def load(path):
    rows=list(csv.DictReader(open(path)))
    g=lambda k:np.array([float(r[k]) for r in rows])
    t=g('time'); A=np.stack([g('aft_x'),g('aft_y'),g('aft_z')],1)
    V=np.full((len(t),3),np.nan)
    d=vt.load_v2_log(path)
    for i,v in enumerate(d["vins"]):
        if v is not None: V[i]=v[1]+v[0]@vt.t_IL
    H=np.stack([g(f'Hl_{i}{j}') for i in range(6) for j in range(6)],1).reshape(-1,6,6)
    return t,A,V,H
def ate(t,P,T):
    m=(t<=t[0]+T)&np.isfinite(P).all(1)&(t>=gt_t[0])&(t<=gt_t[-1]); G=gi(t[m]); Rr,tt=um(P[m],G); Q=(Rr@P[m].T).T+tt
    return float(np.sqrt((np.linalg.norm(Q-G,axis=1)**2).mean())), int(m.sum())
def spec(H):
    out=[]
    for h in H:
        if not np.isfinite(h).all() or np.abs(h).max()==0: continue
        Htt,Htr,Hrr=h[:3,:3],h[:3,3:],h[3:,3:]
        try:
            Stt=Htt-Htr@np.linalg.solve(Hrr,Htr.T); Srr=Hrr-Htr.T@np.linalg.solve(Htt,Htr)
        except np.linalg.LinAlgError: continue
        out.append(np.r_[np.linalg.eigvalsh((Stt+Stt.T)/2),np.linalg.eigvalsh((Srr+Srr.T)/2),np.trace(Stt),np.trace(Srr)])
    return np.array(out)
ti,Ai,Vi,Hi=load(sys.argv[1]); tg,Ag,Vg,Hg=load(sys.argv[2])
print("rows iglio",len(ti),"genz",len(tg),"span",ti[-1]-ti[0],tg[-1]-tg[0])
print("any NaN in iglio aft:",np.isnan(Ai).any(),"| path length (m):",np.linalg.norm(np.diff(Ai,axis=0),axis=1).sum(),"| max step:",np.linalg.norm(np.diff(Ai,axis=0),axis=1).max())
for T in (60,120):
    print(f"first {T}s ATE: iG-LIO {ate(ti,Ai,T)}  GenZ-LIO(G0 run1) {ate(tg,Ag,T)}  VINS(iglio log) {ate(ti,Vi,T)}  VINS(G0 log) {ate(tg,Vg,T)}")
print("GT path length same window:",np.linalg.norm(np.diff(gi(ti[ti<=ti[0]+120]),axis=0),axis=1).sum())
for name,t,H in (("iG-LIO",ti,Hi),("GenZ-LIO",tg,Hg)):
    m=t<=t[0]+120; sp=spec(H[m]); print(f"\n{name}: Hessian rows usable {len(sp)}")
    if len(sp)==0: continue
    q=lambda x:np.percentile(x,[10,50,90])
    for k,lab in ((0,'S_tt eig min'),(1,'S_tt eig mid'),(2,'S_tt eig max'),(3,'S_RR eig min'),(4,'S_RR eig mid'),(5,'S_RR eig max'),(6,'tr S_tt'),(7,'tr S_RR')):
        print(f"  {lab:14s} p10/p50/p90: {q(sp[:,k] if k<6 else sp[:,k])}")
    print("  condition S_tt (max/min) median:",np.median(sp[:,2]/np.maximum(sp[:,0],1e-30)),"| S_RR:",np.median(sp[:,5]/np.maximum(sp[:,3],1e-30)))
    print("  median 6x6 H diag:",np.round(np.median(np.stack([np.diag(h) for h in H[m] if np.isfinite(h).all()]),axis=0),1))
