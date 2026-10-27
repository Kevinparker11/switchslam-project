import sys,os,csv,numpy as np
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import v2_tools as vt  # usage: IGLIO_GT=<Multi Floor ground_truth_path.csv> python3 -I diag_iglio_full.py (log paths edited below)
gt_t,gt_p=vt.load_gt(os.environ["IGLIO_GT"])
gi=lambda tt:np.stack([np.interp(tt,gt_t,gt_p[:,k]) for k in range(3)],1)
def um(A,B):
    ma,mb=A.mean(0),B.mean(0);C=(B-mb).T@(A-ma)/len(A);U,Sg,Vt=np.linalg.svd(C);D=np.eye(3);D[2,2]=np.sign(np.linalg.det(U@Vt));Rr=U@D@Vt;return Rr,mb-Rr@ma
def load(path):
    rows=list(csv.DictReader(open(path))); g=lambda k:np.array([float(r[k]) for r in rows])
    return g('time'),np.stack([g('aft_x'),g('aft_y'),g('aft_z')],1)
# reference alignment from GenZ-LIO run (good) to define a robust frame: align every run on its first 60 s to GT
tg,Pg=load('/tmp/claude-0/g0mf/switching_log_v2_G0_kf_run1.csv')
for r in (1,2,3):
    t,P=load(f'iglio_calib/runs_v2_iglio/switching_log_v2_I0_kf_run{r}.csv'); t0=t[0]
    m=(t-t0<=60)&(t>=gt_t[0]); Rr,tt=um(P[m],gi(t[m])); Q=(Rr@P.T).T+tt; ok=(t>=gt_t[0])&(t<=gt_t[-1]); e=np.where(ok,np.linalg.norm(Q-gi(np.clip(t,gt_t[0],gt_t[-1])),axis=1),np.nan)
    # genz error with same procedure
    mg=(tg-tg[0]<=60); Rg,tg2=um(Pg[mg],gi(tg[mg])); Qg=(Rg@Pg.T).T+tg2; eg=np.linalg.norm(Qg-gi(np.clip(tg,gt_t[0],gt_t[-1])),axis=1)
    first=np.where(e>1.0)[0]; fa=t[first[0]]-t0 if len(first) else None
    f5=np.where(e>5.0)[0]; f5t=t[f5[0]]-t0 if len(f5) else None
    st=np.linalg.norm(np.diff(P,axis=0),axis=1)
    print(f"run{r}: rows {len(t)} first error>1 m at {fa and round(fa,1)} s, >5 m at {f5t and round(f5t,1)} s; max step {st.max():.2f} m at {t[st.argmax()]-t0:.1f} s; error at 100/200/300/350 s:",[round(float(e[np.searchsorted(t-t0,x)]),2) for x in (100,200,300,350)], "| GenZ same alignment (60 s):",[round(float(eg[np.searchsorted(tg-tg[0],x)]),2) for x in (100,200,300,350)])
    # z and position timeline
    i=np.searchsorted(t-t0,[60,120,180,240,300,380]); print("   pos at 60..380 s:",[tuple(np.round(P[min(k,len(P)-1)],1)) for k in i])
i=np.searchsorted(tg-tg[0],[60,120,180,240,300,380]); print("GenZ pos:",[tuple(np.round(Pg[min(k,len(Pg)-1)],1)) for k in i])
print("GT   pos:",[tuple(np.round(gi(np.array([gt_t[0]+x]))[0],1)) for x in (60,120,180,240,300,380)])
