"""Drift labels shared by the screening scripts: A-LOAM odometry (l_p) vs ground truth, 8 s windows,
label 1 = top third of drift per metre, 0 = bottom third, NaN otherwise."""
import numpy as np, pandas as pd


def drift_labels(L, gt_path, window=8.0, min_path=2.0):
    g = pd.read_csv(gt_path); gt_t = g.timestamp.values / 1e9; gt_p = g[["p_w_b_x", "p_w_b_y", "p_w_b_z"]].values
    t = L.time.values; p = L[["l_px", "l_py", "l_pz"]].values; m = (t >= gt_t[0]) & (t <= gt_t[-1])
    gi = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
    mu_s, mu_d = p[m].mean(0), gi[m].mean(0)
    U, _, Vt = np.linalg.svd((gi[m] - mu_d).T @ (p[m] - mu_s) / m.sum())
    S = np.eye(3); S[2, 2] = -1 if np.linalg.det(U) * np.linalg.det(Vt) < 0 else 1
    pa = (p - mu_s) @ (U @ S @ Vt).T + mu_d
    edges = np.arange(t[m][0], t[m][-1], window); win = np.full(len(t), -1); drift = []
    for k in range(len(edges) - 1):
        i = np.where((t >= edges[k]) & (t < edges[k + 1]))[0]
        path = np.linalg.norm(np.diff(gi[i], axis=0), axis=1).sum() if len(i) >= 5 else 0
        if path < min_path: drift.append(np.nan); continue
        drift.append(np.linalg.norm((pa[i[-1]] - pa[i[0]]) - (gi[i[-1]] - gi[i[0]])) / path); win[i] = k
    drift = np.array(drift); lo, hi = np.nanpercentile(drift, [33.3, 66.7])
    lab = np.full(len(t), np.nan); ok = win >= 0
    lab[ok] = np.where(drift[win[ok]] >= hi, 1, np.where(drift[win[ok]] <= lo, 0, np.nan))
    return lab, win, drift
