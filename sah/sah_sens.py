import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,"/home/claude/fusion_v3")
import numpy as np, v2_tools as vt, cand, sah_replay as sr
seq=sys.argv[1]; pairs=[a.split(":") for a in sys.argv[2:]]
gt_t,gt_p=vt.load_gt(cand.SEQ[seq][0]); data=[(cand.load(lg),sr.kf_normals(kf)) for lg,kf in pairs]
D=np.radians
for name,kw in [("default",{}),("q_t x1/9",dict(q_t=D(0.05/3)**2)),("q_t x9",dict(q_t=D(0.15)**2)),("s_turn /3",dict(s_turn=0.007)),("s_turn x3",dict(s_turn=0.06)),
                ("R0 1deg",dict(R0=D(1)**2)),("R0 6deg",dict(R0=D(6)**2)),("search 10deg",dict(search_deg=10.0)),("search 25deg",dict(search_deg=25.0))]:
    r=[vt.ate(d["t"],sr.run(d,KF,sah_kw=kw)[0],gt_t,gt_p)[0] for d,KF in data]
    print("%-14s %s mean %.3f"%(name," ".join("%.3f"%x for x in r),np.mean(r)),flush=True)
