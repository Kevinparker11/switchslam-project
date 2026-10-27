import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,"/home/claude/fusion_v3")
import numpy as np, v2_tools as vt, fusion_core as fc, cand, sah_replay as sr, sheading as sh
from scipy.spatial.transform import Rotation as Rot, Slerp
E3=np.array([0,0,1.0])
def trace(seq, lg, kf, kw={}):
    gt_t,gt_p,gt_q=vt.load_gt_full(cand.SEQ[seq][0]); sl=Slerp(gt_t,Rot.from_quat(gt_q))
    d=cand.load(lg); KF=sr.kf_normals(kf); keys=np.array(sorted(KF)); S=sh.DirectionSLAM(**kw)
    core=fc.FusionCore(vt.R_IL, vt.t_IL, c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=20.0, hess_frame=d["hess_frame"])
    rows=[]; tref=None
    for k in range(len(d["t"])):
        t=d["t"][k]; R,p,info=core.step(t,d["aft"][k],d["vins"][k],d["H"][k])
        if info["mode"]!="FUSED" or d["vins"][k] is None or not (gt_t[0]<=t<=gt_t[-1]): continue
        j=np.searchsorted(keys,t-0.002)
        if not (j<len(keys) and abs(keys[j]-t)<0.003): continue
        u=core.Rf@(vt.R_IL.T@(d["vins"][k][0].T@E3)); u/=np.linalg.norm(u); L=sh.level_rotation(u)
        nb,pl=KF[keys[j]]; obs,n,h=sh.mode_stats(nb@(L@core.Rf).T,pl)
        Rg=sl(t).as_matrix()
        if tref is None: tref=t; Rg0=Rg; Rf0=core.Rf.copy()
        e=float(fc.so3_log(core.Rf@(Rf0@(Rg0.T@Rg)).T)@u)
        nl=len(S.d); c=S.update_modes(t,obs,n,h)
        if c!=0: core.Rf=fc.so3_exp(-c*u)@core.Rf
        rows.append((t-tref,np.degrees(e),np.degrees(c),len(obs),len(S.d),np.degrees(np.sqrt(S.P[0,0])), np.degrees(min([o[1] for o in obs])) if obs else np.nan))
    return np.array(rows)
if __name__=="__main__":
    R=trace(sys.argv[1],sys.argv[2],sys.argv[3])
    print("t true_err corr nobs nlm sigP sig_obs_min")
    for r in R[::int(sys.argv[4])]: print("%5.0f %6.2f %6.2f %d %d %.2f %.2f"%tuple(r))
    big=np.abs(R[:,2])>0.5; print("corrections >0.5 deg:", " ".join("%.0f:%+.1f(err%+.1f)"%(r[0],r[2],r[1]) for r in R[big]))
