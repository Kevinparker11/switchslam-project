#!/usr/bin/env python3
"""End-to-end check of run_backend.py on synthetic files in the real formats (node log CSV, recorder
npz, SubT-MRS ground-truth CSV).  Checks file handling, not the method.  Run: python3 test_backend_cli.py"""
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import fusion_core as fc      # noqa: E402
import backend_icp as bi      # noqa: E402
import backend_synth as bs    # noqa: E402

rng = np.random.default_rng(7)
work = tempfile.mkdtemp()
world = bs.make_world()
T_kf_gt = bs.path([(-9, 0), (-2, 0), (45, 0), (-2, 0.3), (-9, -2.5), (-9, 0.5)], step=1.0)
# scans at 0.1 m spacing (0.5 m/s, 5 Hz) between keyframes: interpolate GT
t0 = 1660857393.2
T_scan_gt, t_scan, kf_idx = [], [], []
for k in range(len(T_kf_gt) - 1):
    A, B = T_kf_gt[k], T_kf_gt[k + 1]
    for s in range(10):
        a = s / 10.0
        R, p = fc.interp_pose(a, 0.0, A[:3, :3], A[:3, 3], 1.0, B[:3, :3], B[:3, 3])
        if s == 0:
            kf_idx.append(len(t_scan))
        T_scan_gt.append(bi.se3(R, p))
        t_scan.append(t0 + 0.2 * len(t_scan))
t_scan = np.array(t_scan)
T_fe = bs.drifted(T_scan_gt, rng, drift_world=(0.0015, 0.0, 0.0004), yaw_bias_deg=0.002, sig_t=0.0005, sig_r_deg=0.003)

# ground truth csv (SubT-MRS format)
q = np.array([fc.R_to_quat(T[:3, :3]) for T in T_scan_gt])
P = np.array([T[:3, 3] for T in T_scan_gt])
pd.DataFrame({"timestamp": (t_scan * 1e9).astype(np.int64), "p_w_b_x": P[:, 0], "p_w_b_y": P[:, 1], "p_w_b_z": P[:, 2],
              "q_w_b_x": q[:, 0], "q_w_b_y": q[:, 1], "q_w_b_z": q[:, 2], "q_w_b_w": q[:, 3]}).to_csv(
    os.path.join(work, "gt.csv"), index=False)
# node log (only the columns run_backend needs for --front fused)
qf = np.array([fc.R_to_quat(T[:3, :3]) for T in T_fe])
Pf = np.array([T[:3, 3] for T in T_fe])
pd.DataFrame({"time": t_scan, "mode": "FUSED", "fused_x": Pf[:, 0], "fused_y": Pf[:, 1], "fused_z": Pf[:, 2],
              "fused_qx": qf[:, 0], "fused_qy": qf[:, 1], "fused_qz": qf[:, 2], "fused_qw": qf[:, 3]}).to_csv(
    os.path.join(work, "log.csv"), index=False)
# recorder npz: keyframe = every 10th scan; pose = (here) ground truth, cloud in the body frame
pts, n, pose, kt = [], [], [], []
for i in kf_idx:
    C = bi.voxel_down(bs.scan(world, T_scan_gt[i], rng), 0.25)
    pts.append(np.round(C / 0.01).astype(np.int16))
    n.append(len(C))
    pose.append(np.r_[T_scan_gt[i][:3, 3], fc.R_to_quat(T_scan_gt[i][:3, :3])])
    kt.append(t_scan[i])
np.savez_compressed(os.path.join(work, "kf.npz"), t=np.array(kt), pose=np.array(pose), n=np.array(n),
                    pts=np.vstack(pts), scale=0.01)
out = subprocess.run([sys.executable, os.path.join(here, "run_backend.py"), "--log", os.path.join(work, "log.csv"),
                      "--kf", os.path.join(work, "kf.npz"), "--gt", os.path.join(work, "gt.csv"),
                      "--models", "none,iso,schur_otsu", "--min-gap", "20", "--r-xy", "6",
                      "--out-prefix", os.path.join(work, "traj")], capture_output=True, text=True)
print(out.stdout[-2500:])
print(out.stderr[-2000:])
assert out.returncode == 0
rows = [l.split() for l in out.stdout.splitlines() if l.startswith(("none ", "iso ", "schur_otsu "))]
full = {r[0]: float(r[5]) for r in rows}
assert full["schur_otsu"] < full["none"], full
assert os.path.exists(os.path.join(work, "traj_schur_otsu.csv"))
print("BACK-END CLI TEST PASSED", full)
