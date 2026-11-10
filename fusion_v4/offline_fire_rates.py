import sys, csv, numpy as np
sys.path.insert(0,'/home/claude/switchslam-project/fusion_v4')
import switch_slam_detect as sd, switch_slam_core as sw
det=sd.OwnDetector(("R","T"))
for bag,f in [("Multi Floor","f24fam/MF_switching_log_v2_F24_kf_run1.csv"),("Long Corridor","f24fam/LC_switching_log_v2_F24_kf_run1.csv"),
              ("Corridor02","f24fam/C02_switching_log_v2_F24_kf_run1.csv"),("Cave02","f24fam/CAVE_switching_log_v2_F24_kf_run1.csv"),
              ("GEODE","f24fam/GEODE_switching_log_v2_F24_kf_run1.csv")]:
    n=r=t=anyd=pap=0
    with open(f) as fh:
        rd=csv.DictReader(fh)
        for row in rd:
            try: H=np.array([float(row["Hl_%d%d"%(i,j)]) for i in range(6) for j in range(6)]).reshape(6,6)
            except Exception: continue
            if not np.isfinite(H).all() or not H.any(): continue
            d=det(H,None); n+=1; r+=d["chan"]["R"]; t+=d["chan"]["T"]; anyd+=d["degenerate"]; pap+=sw.eig_degeneracy(H)["degenerate"]
    print("%-14s scans %5d  R %5.1f%%  T %5.1f%%  R or T %5.1f%%   (paper rule %5.1f%%)"%(bag,n,100*r/n,100*t/n,100*anyd/n,100*pap/n))
