import sys, os, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/clean4/fusion_v4")
import v2_tools as vt
U = "/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6/"
S = "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/"
GT = {"MF": "/mnt/user-data/uploads/ground_truth_path.csv", "LC": U + "26b723ff-corridor01_gt.txt", "C02": U + "db62c9b7-corridor02_gt.txt",
      "GEO": S + "stairs_alpha_gt.txt", "FARM": S + "farm_g20/gt_farm.txt"}
_g = {}
def ate_log(path, seq, cols=("fused_x", "fused_y", "fused_z")):
    if seq not in _g: _g[seq] = vt.load_gt(GT[seq])
    L = pd.read_csv(path); L = L[pd.to_numeric(L["time"], errors="coerce").notna()]
    return vt.ate(L["time"].astype(float).values, L[list(cols)].astype(float).values, *_g[seq])
if __name__ == "__main__":
    print("%.3f / %.2f" % ate_log(sys.argv[1], sys.argv[2])[:2])
