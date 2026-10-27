"""honest measurement-error model: run F8 (no correction), at each keyframe compute SAH measurement z against a
reference built from the first structured keyframes, compare with the true heading error from GT."""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,"/home/claude/fusion_v3")
import numpy as np, v2_tools as vt, fusion_core as fc, cand, sah_replay as sr, sheading as sh
from scipy.spatial.transform import Rotation as Rot, Slerp
E3=np.array([0,0,1.0])
seq=sys.argv[1]; pairs=[a.split(":") for a in sys.argv[2:]]
gt=cand.SEQ[seq][0]; gt_t,gt_p,gt_q=vt.load_gt_full(gt); sl=Slerp(gt_t,Rot.from_quat(gt_q))
rows=[]
for lg,kf in pairs:
    d=cand.load(lg); KF=sr.kf_normals(kf); keys=np.array(sorted(KF))
    core=fc.FusionCore(vt.R_IL, vt.t_IL, c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=20.0, hess_frame=d["hess_frame"])
    ref=None; nref=0; e_ref=None; prev_yaw_turn=None; turned=0.0; tref=None
    for k in range(len(d["t"])):
        t=d["t"][k]; R,p,info=core.step(t,d["aft"][k],d["vins"][k],d["H"][k])
        if info["mode"]!="FUSED" or d["vins"][k] is None or not (gt_t[0]<=t<=gt_t[-1]): continue
        j=np.searchsorted(keys,t-0.002)
        if not (j<len(keys) and abs(keys[j]-t)<0.003): continue
        u=core.Rf@(vt.R_IL.T@(d["vins"][k][0].T@E3)); u/=np.linalg.norm(u); L=sh.level_rotation(u)
        nb,pl=KF[keys[j]]; h,n=sh.direction_hist(nb@(L@core.Rf).T,pl)
        # true heading error of the estimate (about up), relative to the start of FUSED
        Rg=sl(t).as_matrix()
        if tref is None: tref=t; Rg0=Rg; Rf0=core.Rf.copy()
        E=(Rf0@(Rg0.T@Rg))  # where the estimate should be
        e=float(fc.so3_log(core.Rf@E.T)@u)
        if not sh.structured(h,n): continue
        if nref<5:
            ref=h/h.sum() if ref is None else ref+h/h.sum(); nref+=1; e_ref=e if e_ref is None else e_ref; continue
        r=sh.align(h,ref,15.0)
        if r is None: continue
        rows.append((r["shift"],e-e_ref,t-tref,lg[-5],r["peak"],r["peak"]-r["second"],n,h.max()/h.mean(),r["curv"]))
R=np.array([x[:2]+x[4:] for x in rows]); TT=np.array([x[2] for x in rows]); LG=np.array([x[3] for x in rows]); err=np.degrees(R[:,0]-R[:,1])
print("%s: %d measurements; meas minus true heading error (deg): median %.2f, MAD-sigma %.2f, p90|.| %.2f, p99|.| %.2f, frac>5 %.3f"%(seq,len(R),np.median(err),1.4826*np.median(np.abs(err-np.median(err))),np.percentile(np.abs(err),90),np.percentile(np.abs(err),99),(np.abs(err)>5).mean()))
for name,col in (("peak",2),("margin",3),("npts",4),("peak/mean",5)):
    qs=np.percentile(R[:,col],[0,25,50,75,100])
    out=[]
    for a,b in zip(qs[:-1],qs[1:]):
        m=(R[:,col]>=a)&(R[:,col]<=b); out.append("[%.3g-%.3g]: sig %.2f p90 %.2f"%(a,b,1.4826*np.median(np.abs(err[m]-np.median(err[m]))),np.percentile(np.abs(err[m]),90)))
    print("  by %-9s"%name," | ".join(out))
np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)),"meas_%s.npy"%seq),R)
for g in sorted(set(LG)):
    m=LG==g; o=np.argsort(TT[m]); e1=err[m][o]; t1=TT[m][o]
    print("log",g," ".join("%.0fs:%+.1f"%(t1[i],np.median(e1[max(0,i-5):i+5])) for i in range(0,len(t1),max(1,len(t1)//16))))
