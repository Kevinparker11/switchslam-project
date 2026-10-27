import sys, numpy as np, os
os.chdir("/home/claude")
sys.path.insert(0,"/home/claude/sah"); sys.path.insert(0,"/home/claude/fusion_v3")
import cand, v2_tools as vt, sah_replay2 as sr
H="/home/claude/"
KF={"MF":[H+"data_in4/keyframes_F8_kf_run%d.npz"%i for i in (1,2,3)]+[H+"data_in5/keyframes_F8_kf_run%d.npz"%i for i in (4,5,6)],
    "LC":[H+"data_kf/LC_keyframes_F8_kf_run%d.npz"%i for i in (1,2,3)],
    "C02":[H+"data_kf/C02_keyframes_F8_kf_run%d.npz"%i for i in (1,2,3)]}
kw=dict(v3=6,bound_R=True)
V=[("F8 (no SAH)",None,dict()),("F16 (SAH FUSED only, tw20)",kw,dict()),("SAH also in WARMUP, tw20",kw,dict(sah_modes=("FUSED","WARMUP"))),
   ("F16 tw10",kw,dict(t_warm=10.0)),("F16 tw0",kw,dict(t_warm=0.0)),("SAH in WARMUP + tw0 (same as tw0)",kw,dict(t_warm=0.0,sah_modes=("FUSED","WARMUP")))]
for seq in ("MF","LC","C02"):
    gt_t,gt_p=vt.load_gt(cand.SEQ[seq][0]); logs=cand.SEQ[seq][1]
    D=[(cand.load(l),sr.kf_normals(k)) for l,k in zip(logs,KF[seq])]
    for name,k,x in V:
        r=[]
        for d,K in D:
            p,s=sr.run(d,K,sah_kw=k,**x); r.append(vt.ate(d["t"],p,gt_t,gt_p)[0])
        print("%-4s %-36s %s | mean %.3f sd %.3f"%(seq,name," ".join("%.2f"%v for v in r),np.mean(r),np.std(r,ddof=1)),flush=True)
