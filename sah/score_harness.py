import sys; sys.path.insert(0,"/home/claude/fusion_v3"); sys.path.insert(0,"/home/claude/sah")
import pandas as pd, numpy as np, v2_tools as vt, cand
O="/home/claude/sah/harness_out"
for a in sys.argv[1:]:
    tag,seq,ref=a.split(":")
    L=pd.read_csv("%s/%s/switching_log_v2_%s.csv"%(O,tag,tag)); L=L[pd.to_numeric(L["time"],errors="coerce").notna()]
    gt_t,gt_p=vt.load_gt(cand.SEQ[seq][0])
    r=vt.ate(L["time"].astype(float).values,L[["fused_x","fused_y","fused_z"]].astype(float).values,gt_t,gt_p)
    print("%-16s ATE %.3f / %.2f  (%s)  total applied %.2f deg"%(tag,r[0],r[1],ref,float(L["sah_total_deg"].iloc[-1])))
