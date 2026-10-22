"""offline candidate policies on logged runs; ATE (full span, own scorer) per log"""
import sys, glob, os; sys.path.insert(0,"/home/claude/fusion_v3")
import numpy as np, v2_tools as vt, fusion_core as fc
E3=np.array([0,0,1.0])
SEQ={"MF":("/mnt/user-data/uploads/ground_truth_path.csv",["data_in4/switching_log_v2_F8_kf_run%d.csv"%i for i in (1,2,3)]+["data_in5/switching_log_v2_F8_kf_run%d.csv"%i for i in (4,5,6)]),
     "LC":("/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6/26b723ff-corridor01_gt.txt",["data_in7/switching_log_v2_F8_kf_run%d.csv"%i for i in (1,2,3)]),
     "C02":("/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6/db62c9b7-corridor02_gt.txt",["data_in8/switching_log_v2_F8_kf_run%d.csv"%i for i in (1,2,3)])}
_cache={}
def load(lg):
    if lg not in _cache: _cache[lg]=vt.load_v2_log("/home/claude/"+lg)
    return _cache[lg]
def run(d, c_t=0.03, K=0.0, w_mode="schur", rate_gate=None, win=10.0):
    core=fc.FusionCore(vt.R_IL, vt.t_IL, c_t=c_t, gate=fc.KappaGate(kth=1e9), t_warm=20.0, hess_frame=d["hess_frame"], w_mode=w_mode)
    out=[]; hist=[]
    for k in range(len(d["t"])):
        R,p,info=core.step(d["t"][k], d["aft"][k], d["vins"][k], d["H"][k])
        if K>0 and info["mode"]=="FUSED" and d["vins"][k] is not None:
            u=core.Rf@(vt.R_IL.T@(d["vins"][k][0].T@E3)); u/=np.linalg.norm(u)
            nu=float(fc.so3_log(d["aft"][k][0]@core.Rf.T)@u)
            ok=True
            if rate_gate is not None:
                hist.append((d["t"][k],nu))
                while hist and hist[0][0]<d["t"][k]-win: hist.pop(0)
                ok = abs(nu-hist[0][1]) <= rate_gate
            if ok:
                core.Rf=fc.so3_exp(K*nu*u)@core.Rf
        out.append(core.pf.copy())
    return np.array(out)
def score(seq, **kw):
    gt,logs=SEQ[seq]; gt_t,gt_p=vt.load_gt(gt); r=[]
    for lg in logs:
        d=load(lg); p=run(d,**kw); r.append(vt.ate(d["t"],p,gt_t,gt_p)[0])
    return np.array(r)
if __name__=="__main__":
    for name,kw in [("F8",{}),("F14",dict(w_mode="lidar")),("yawK0.01",dict(K=0.01)),("yawK0.05",dict(K=0.05)),("yawK1",dict(K=1.0)),
                    ("yawK0.05 gate2deg/10s",dict(K=0.05,rate_gate=np.radians(2))),("yawK0.05 gate1deg/10s",dict(K=0.05,rate_gate=np.radians(1)))]:
        print("%-24s"%name, " | ".join("%s %s mean %.2f"%(s," ".join("%.2f"%x for x in score(s,**kw)),score(s,**kw).mean()) for s in ("MF","LC","C02")), flush=True)
