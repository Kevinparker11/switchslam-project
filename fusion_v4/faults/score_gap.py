import sys,os,glob,json,numpy as np,csv
S="/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad"; R=S+"/clean4"
GT={'MF':"/tmp/claude-0/g0mf/ground_truth_path.csv",'LC':"/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6/26b723ff-corridor01_gt.txt",'C02':"/home/claude/data_in14/cave02_gt.txt"}
EX={'MF':None,'LC':R+"/configs/corridor/corridor_extrinsics.yaml",'C02':R+"/configs/cave02/cave02_extrinsics.yaml"}
seq=sys.argv[1]
if EX[seq]: os.environ["EXTRINSIC_YAML"]=EX[seq]
sys.path.insert(0,R+"/fusion_v4"); import v2_tools as vt
gt_t,gt_p=vt.load_gt(GT[seq])
gi=lambda tt:np.stack([np.interp(tt,gt_t,gt_p[:,k]) for k in range(3)],1)
def um(A,B):
    ma,mb=A.mean(0),B.mean(0);C=(B-mb).T@(A-ma)/len(A);U,Sg,Vt=np.linalg.svd(C);D=np.eye(3);D[2,2]=np.sign(np.linalg.det(U@Vt));Rr=U@D@Vt;return Rr,mb-Rr@ma
def score(path):
    d=vt.load_v2_log(path); t=np.asarray(d["t"]); rows=list(csv.DictReader(open(path)))
    F=np.array([[float(x['fused_x']),float(x['fused_y']),float(x['fused_z'])] for x in rows])
    A=np.array([[float(x['aft_x']),float(x['aft_y']),float(x['aft_z'])] for x in rows])
    V=np.full((len(t),3),np.nan)
    for i,v in enumerate(d["vins"]):
        if v is not None: V[i]=v[1]+v[0]@vt.t_IL
    ok=(t>=gt_t[0])&(t<=gt_t[-1]); o={'rows':len(t),'nan':bool(np.isnan(F).any())}
    for n,P in (('fused',F),('g0',A),('vins',V)):
        mm=ok&np.isfinite(P).all(1); G=gi(t[mm]); Rr,tt=um(P[mm],G); Q=(Rr@P[mm].T).T+tt
        o[n]=float(np.sqrt((np.linalg.norm(Q-G,axis=1)**2).mean()))
    st=np.linalg.norm(np.diff(F,axis=0),axis=1); dt=np.diff(t); gap=dt>1.0
    o['maxstep']=float(st.max()); o['maxstep_nogap']=float(st[~gap].max()); o['ngap']=int(gap.sum()); o['maxgapstep']=float(st[gap].max()) if gap.any() else 0.0
    return o
res={}
for d in sorted(glob.glob(S+f"/gappack/{seq}_*B_r?")):
    tag=os.path.basename(d)
    for cfg in ('G20','G23'):
        res[tag+'|'+cfg]=score(d+f"/switching_log_v2_{cfg}_kf_run1.csv")
json.dump(res,open(S+f"/gap_score_{seq}.json",'w'),indent=1)
for k,v in res.items(): print(f"{k:14s} fused {v['fused']:9.2f} g0 {v['g0']:9.2f} vins {v['vins']:7.2f} | maxstep {v['maxstep']:8.1f} nogap {v['maxstep_nogap']:8.1f} gapstep {v['maxgapstep']:6.1f} ngap {v['ngap']} nan {v['nan']} rows {v['rows']}")
