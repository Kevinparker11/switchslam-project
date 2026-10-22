"""Noise-floor null for Channel T as the switching node computes it.

Perfectly degenerate scene: straight corridor (walls, floor, ceiling) along x, so every true
normal is perpendicular to x and the true smallest eigenvalue of T is 0. Range noise makes
lambda_min(T) > 0. The 99th percentile of that value is the smallest lambda_min that cannot be
explained by noise alone (null quantile, alpha = 0.01).

Pipeline copied from the node: points -> 0.2 m voxel downsample (A-LOAM surf_less_flat leaf)
-> 400 random query points -> k = 12 nearest neighbours in the downsampled cloud -> np.cov -> smallest-
eigenvector normal -> T = mean(n n^T). VLP-16 pattern: 16 rings, -15..+15 deg, 0.2 deg azimuth.
Corridor widths/heights and range limit are assumptions (hallway-like), varied below.
"""
import numpy as np
from scipy.spatial import cKDTree

rng = np.random.default_rng(7)
elev = np.deg2rad(np.arange(-15, 16, 2))
az = np.deg2rad(np.arange(0, 360, 0.2))
AZ, EL = np.meshgrid(az, elev)
D = np.stack([np.cos(EL) * np.cos(AZ), np.cos(EL) * np.sin(AZ), np.sin(EL)], -1).reshape(-1, 3)


def cast(width, height, z_sensor, rmax):
    planes = [(1, -width / 2), (1, width / 2), (2, -z_sensor), (2, height - z_sensor)]
    t = np.full(len(D), np.inf)
    for axis, val in planes:
        with np.errstate(divide="ignore", invalid="ignore"):
            tt = val / D[:, axis]
        t = np.minimum(t, np.where(tt > 0, tt, np.inf))
    ok = np.isfinite(t) & (t < rmax) & (t > 0.4)
    return D[ok], t[ok]


def voxel(P, leaf=0.2):
    key = np.floor(P / leaf).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    out = np.zeros((inv.max() + 1, 3)); cnt = np.bincount(inv)
    for i in range(3):
        out[:, i] = np.bincount(inv, P[:, i]) / cnt
    return out


def node_T(P, k=12, sub=400):
    tree = cKDTree(P)
    q = rng.choice(len(P), min(sub, len(P)), replace=False)
    _, idx = tree.query(P[q], k=k)
    Q = P[idx]
    Qc = Q - Q.mean(1, keepdims=True)
    C = np.einsum("nki,nkj->nij", Qc, Qc) / (k - 1)
    _, V = np.linalg.eigh(C)
    n = V[:, :, 0]
    T = n.T @ n / len(n)
    return np.linalg.eigvalsh(T)[0]


def null(width, height, rmax, sig, B=200):
    Dk, t = cast(width, height, 0.6, rmax)
    vals = []
    for _ in range(B):
        r = t + sig * rng.standard_normal(len(t))
        vals.append(node_T(voxel(Dk * r[:, None])))
    v = np.array(vals)
    return v.mean(), np.percentile(v, 99), len(t)


if __name__ == "__main__":
    print("width height rmax sigma_r | mean_l1  q99_l1  (raw points)")
    rows = []
    for (w, h) in [(2.0, 2.6), (3.0, 3.0)]:
        for rmax in [20.0, 40.0]:
            for sig in [0.0, 0.0225, 0.03, 0.045]:
                m, q, n = null(w, h, rmax, sig, B=60 if sig == 0 else 200)
                rows.append((w, h, rmax, sig, m, q))
                print(f"{w:4.1f} {h:4.1f} {rmax:5.0f} {sig:6.4f} | {m:.4f}  {q:.4f}  ({n})")
    qs = [r[5] for r in rows if r[3] > 0]
    print(f"max q99 over the noisy robustness band (sigma 0.0225-0.045 m) = {max(qs):.4f}")
    print(f"q99 at sigma 0.03 m (VLP-16 typical), all geometries = {[round(r[5],4) for r in rows if r[3]==0.03]}")
