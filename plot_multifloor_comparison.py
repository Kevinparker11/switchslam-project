#!/usr/bin/env python3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from compute_ate_multifloor import align_and_error, umeyama

baseline_path = "/home/kavinkumar/switching_log_multifloor_gt_run1_fresh.csv"
timedecay_path = "/home/kavinkumar/switching_log_multifloor_timedecay_run2.csv"

fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

for path, label, color in [(baseline_path, "Baseline (switching_node_multifloor_gt.py)", "tab:red"),
                            (timedecay_path, "Fix (switching_node_multifloor_timedecay.py)", "tab:blue")]:
    df, t, err, rmse, mx = align_and_error(path, label=label)
    t0 = t.min()
    axes[0].plot(t - t0, err, label=f"{label}\nRMSE={rmse:.2f}m Max={mx:.2f}m", color=color, linewidth=1)

axes[0].axvline(100, color="gray", linestyle="--", linewidth=1, label="t=100s (prior warmup-exclusion cutoff)")
axes[0].set_ylabel("Position error (m)")
axes[0].set_title("Multi Floor (Hawkins mine) full 3-segment sequence: ATE vs time")
axes[0].legend(loc="upper right", fontsize=9)
axes[0].grid(alpha=0.3)

# trajectory plot (aligned) for the fix run only, top-down XY
import pandas as pd
gt = pd.read_csv("/home/kavinkumar/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv")
df_fix = pd.read_csv(timedecay_path).dropna(subset=["fused_x","fused_y","fused_z"])
t_fix = df_fix["time"].values
gt_x = np.interp(t_fix, gt["timestamp"]/1e9, gt["p_w_b_x"])
gt_y = np.interp(t_fix, gt["timestamp"]/1e9, gt["p_w_b_y"])
est_xyz = df_fix[["fused_x","fused_y","fused_z"]].values
gt_xyz_full = np.stack([gt_x, gt_y, np.interp(t_fix, gt["timestamp"]/1e9, gt["p_w_b_z"])], axis=1)
R,tt,s = umeyama(est_xyz, gt_xyz_full, with_scale=False)
aligned = (s*(R@est_xyz.T).T + tt)

axes[1].plot(gt_x, gt_y, label="Ground truth", color="black", linewidth=1.5)
axes[1].plot(aligned[:,0], aligned[:,1], label="Fix (aligned)", color="tab:blue", linewidth=1, alpha=0.8)
axes[1].set_xlabel("X (m)")
axes[1].set_ylabel("Y (m)")
axes[1].set_title("Top-down trajectory (rigid-aligned): fix vs ground truth")
axes[1].legend(loc="best", fontsize=9)
axes[1].axis("equal")
axes[1].grid(alpha=0.3)

plt.tight_layout()
out = "/home/kavinkumar/switchslam_project/multifloor_baseline_vs_timedecay.png"
plt.savefig(out, dpi=130)
print("saved", out)
