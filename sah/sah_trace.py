"""trace: heading error of the corrected estimate vs GT, measurement, acceptance (per keyframe)"""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,"/home/claude/fusion_v3")
import numpy as np, v2_tools as vt, fusion_core as fc, cand, sah_replay as sr, sheading as sh
from scipy.spatial.transform import Rotation as Rot, Slerp
E3=np.array([0,0,1.0])
def trace(seq, lg, kf, kw, every=40):
    gt_t,gt_p,gt_q=vt.load_gt_full(cand.SEQ[seq][0]); sl=Slerp(gt_t,Rot.from_quat(gt_q))
    d=cand.load(lg); KF=sr.kf_normals(kf); keys=np.array(sorted(KF))
    kw_=dict(kw); v=kw_.pop('v3',False); S={False: sh.StructureHeading, True: sh.StructureHeadingV3, 4: sh.StructureHeadingV4}[v](**kw_)
    core=fc.FusionCore(vt.R_IL, vt.t_IL, c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=20.0, hess_frame=d["hess_frame"])
    rows=[]; Rprev=None; tref=None
    orig_measure=S._measure
    for k in range(len(d["t"])):
        t=d["t"][k]; R,p,info=core.step(t,d["aft"][k],d["vins"][k],d["H"][k])
        if Rprev is not None and d["vins"][k] is not None:
            uu=core.Rf@(vt.R_IL.T@(d["vins"][k][0].T@E3)); S.add_turn(float(fc.so3_log(core.Rf@Rprev.T)@uu))
        Rprev=core.Rf.copy()
        if info["mode"]!="FUSED" or d["vins"][k] is None or not (gt_t[0]<=t<=gt_t[-1]): continue
        j=np.searchsorted(keys,t-0.002)
        if not (j<len(keys) and abs(keys[j]-t)<0.003): continue
        u=core.Rf@(vt.R_IL.T@(d["vins"][k][0].T@E3)); u/=np.linalg.norm(u); L=sh.level_rotation(u)
        nb,pl=KF[keys[j]]; h,n=sh.direction_hist(nb@(L@core.Rf).T,pl)
        Rg=sl(t).as_matrix()
        if tref is None: tref=t; Rg0=Rg; Rf0=core.Rf.copy()
        e=float(fc.so3_log(core.Rf@(Rf0@(Rg0.T@Rg)).T)@u)
        z=orig_measure(h,n) if S.ref is not None and S.n_init>=S.init_kf else None
        st0=dict(S.stats); corr=S.update(t,h,n)
        if corr!=0.0: core.Rf=fc.so3_exp(-corr*u)@core.Rf; Rprev=core.Rf.copy()
        rows.append((t-tref,np.degrees(e),np.nan if z is None else np.degrees(z),np.degrees(corr),len(sh.modes(h)),sh.structured(h,n)))
    R=np.array(rows,dtype=float)
    print("t  true_err  meas  corr  nmodes structured")
    for r in R[::every]: print("%5.0f %6.2f %6.2f %6.2f %d %d"%tuple(r))
    return R
if __name__=="__main__":
    v={"v1":False,"v4":4}[sys.argv[4]]
    trace(sys.argv[1],sys.argv[2],sys.argv[3],dict(v3=v),int(sys.argv[5]) if len(sys.argv)>5 else 40)
