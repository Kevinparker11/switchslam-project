import sys,os,csv,glob,numpy as np
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import v2_tools as vt   # usage: IGLIO_GT=<Multi Floor ground_truth_path.csv> python3 -I score_iglio_reps.py (paths of the logs edited below)
gt_t,gt_p=vt.load_gt(os.environ["IGLIO_GT"])
gi=lambda tt:np.stack([np.interp(tt,gt_t,gt_p[:,k]) for k in range(3)],1)
def um(A,B):
    ma,mb=A.mean(0),B.mean(0);C=(B-mb).T@(A-ma)/len(A);U,Sg,Vt=np.linalg.svd(C);D=np.eye(3);D[2,2]=np.sign(np.linalg.det(U@Vt));Rr=U@D@Vt;return Rr,mb-Rr@ma
def load(path):
    rows=list(csv.DictReader(open(path))); g=lambda k:np.array([float(r[k]) for r in rows])
    return g('time'),np.stack([g('aft_x'),g('aft_y'),g('aft_z')],1)
def ate(t,P,T0,T1):
    m=(t>=t[0]+T0)&(t<=t[0]+T1)&(t>=gt_t[0])&(t<=gt_t[-1]); G=gi(t[m]); Rr,tt=um(P[m],G); Q=(Rr@P[m].T).T+tt
    e=np.linalg.norm(Q-G,axis=1); return float(np.sqrt((e**2).mean())),float(e.max())
files={'I0 smoke (Stage 2)':'iglio_smoke/runs_v2_iglio/switching_log_v2_SMOKE_I0_run1.csv','I20 smoke (Stage 4, iG-LIO column)':'iglio_fused/runs_v2_iglio/switching_log_v2_SMOKE_I20_run1.csv'}
for f in sorted(glob.glob('iglio_reps/runs_v2_iglio/rep*_switching_log.csv')): files['repeat '+os.path.basename(f)[3]]=f
tg,Pg=load('/tmp/claude-0/g0mf/switching_log_v2_G0_kf_run1.csv')
print("GenZ-LIO (G0 run 1), same stretch 0-110 s:",[round(x,3) for x in ate(tg,Pg,0,110)])
print(f"{'run':36s} rows  ATE 0-60   ATE 0-110  max0-110  pos@100s            diverged(>2m)")
n=0; nd=0
for k,f in files.items():
    t,P=load(f); a60=ate(t,P,0,60)[0]; a,mx=ate(t,P,0,110); i=np.searchsorted(t-t[0],100.0); i=min(i,len(t)-1)
    dv=a>2.0; n+=1; nd+=dv
    print(f"{k:36s} {len(t):5d} {a60:8.3f} {a:10.3f} {mx:9.2f}   {np.round(P[i],1)}  {'YES' if dv else 'no'}")
print("diverged:",nd,"of",n)
