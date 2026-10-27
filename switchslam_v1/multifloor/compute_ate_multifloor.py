#!/usr/bin/env python3
import sys
import numpy as np
import pandas as pd

GT = "/home/kavinkumar/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv"

def umeyama(src, dst, with_scale=False):
    # src, dst: Nx3, returns R,t,s such that dst ~= s*R@src + t
    mu_src = src.mean(axis=0); mu_dst = dst.mean(axis=0)
    src_c = src - mu_src; dst_c = dst - mu_dst
    n = src.shape[0]
    cov = (dst_c.T @ src_c) / n
    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2,2] = -1
    R = U @ S @ Vt
    if with_scale:
        var_src = (src_c**2).sum(axis=1).mean()
        s = np.trace(np.diag(D) @ S) / var_src
    else:
        s = 1.0
    t = mu_dst - s*R@mu_src
    return R, t, s

def load_gt():
    gt = pd.read_csv(GT)
    gt['t'] = gt['timestamp']/1e9
    return gt

def align_and_error(log_path, t_min=None, t_max=None, label="", with_scale=False):
    df = pd.read_csv(log_path)
    df = df.dropna(subset=['fused_x','fused_y','fused_z'])
    if t_min is not None:
        df = df[df['time']>=t_min]
    if t_max is not None:
        df = df[df['time']<=t_max]
    gt = load_gt()

    # interpolate GT onto fused timestamps
    t = df['time'].values
    gt_x = np.interp(t, gt['t'], gt['p_w_b_x'])
    gt_y = np.interp(t, gt['t'], gt['p_w_b_y'])
    gt_z = np.interp(t, gt['t'], gt['p_w_b_z'])
    gt_xyz = np.stack([gt_x,gt_y,gt_z], axis=1)

    est_xyz = df[['fused_x','fused_y','fused_z']].values

    R,tt,s = umeyama(est_xyz, gt_xyz, with_scale=with_scale)
    aligned = (s*(R@est_xyz.T).T + tt)

    err = np.linalg.norm(aligned-gt_xyz, axis=1)
    rmse = np.sqrt((err**2).mean())
    mx = err.max()
    print(f"{label}: n={len(df)} t=[{t.min():.1f},{t.max():.1f}] dur={t.max()-t.min():.1f}s  RMSE={rmse:.3f}m Max={mx:.3f}m scale={s:.3f}")
    return df, t, err, rmse, mx

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv)>1 else "/home/kavinkumar/switching_log_multifloor_full2.csv"
    with_scale = "--scale" in sys.argv
    df, t, err, rmse, mx = align_and_error(path, label="FULL (no exclusion)", with_scale=with_scale)

    t0 = t.min()
    # first 100s
    m100 = (t - t0) <= 100
    print(f"  first 100s: n={m100.sum()} mean_err={err[m100].mean():.3f}m rmse={np.sqrt((err[m100]**2).mean()):.3f}m max={err[m100].max():.3f}m")
    print(f"  after 100s: n={(~m100).sum()} mean_err={err[~m100].mean():.3f}m rmse={np.sqrt((err[~m100]**2).mean()):.3f}m max={err[~m100].max():.3f}m")

    align_and_error(path, t_min=t0+100, label="EXCLUDING first 100s", with_scale=with_scale)
    align_and_error(path, t_max=t0+150, label="FIRST SEGMENT ALONE (0-150s)", with_scale=with_scale)

    # error vs time in 20s chunks
    print("\n  error-vs-time (20s chunks):")
    chunk=20
    for lo in np.arange(0, t.max()-t0+chunk, chunk):
        hi=lo+chunk
        m = ((t-t0)>=lo)&((t-t0)<hi)
        if m.sum()==0: continue
        print(f"    [{lo:6.0f},{hi:6.0f})s n={m.sum():4d} mean={err[m].mean():6.3f}m max={err[m].max():6.3f}m")
