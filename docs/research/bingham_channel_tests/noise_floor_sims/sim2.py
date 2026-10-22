import numpy as np, sys
from scipy.spatial import cKDTree
rng = np.random.default_rng(1)

# VLP-16-like corridor, ray cast. Sensor at origin; corridor along x.
elev = np.deg2rad(np.arange(-15, 16, 2))
az = np.deg2rad(np.arange(0, 360, 0.2))
AZ, EL = np.meshgrid(az, elev)
D = np.stack([np.cos(EL)*np.cos(AZ), np.cos(EL)*np.sin(AZ), np.sin(EL)], -1).reshape(-1, 3)
ym, yp, zm, zp = -1.5, 1.5, -1.0, 1.5  # wall/floor/ceiling positions

def cast(D, rmax):
    t = np.full(len(D), np.inf)
    for axis, val in [(1, ym), (1, yp), (2, zm), (2, zp)]:
        with np.errstate(divide='ignore', invalid='ignore'):
            tt = val / D[:, axis]
        tt = np.where(tt > 0, tt, np.inf)
        t = np.minimum(t, tt)
    ok = np.isfinite(t) & (t < rmax)
    return t, ok

def normals_pca(P, k):
    tree = cKDTree(P)
    _, idx = tree.query(P, k=k)
    Q = P[idx]                      # (N,k,3)
    Qc = Q - Q.mean(1, keepdims=True)
    M = np.einsum('nki,nkj->nij', Qc, Qc)   # scatter (sum)
    w, V = np.linalg.eigh(M)
    n = V[:, :, 0]
    return n, w, V, idx

def tensor_stats(n, vaxis=0):
    T = n.T @ n / len(n)
    w = np.linalg.eigvalsh(T)
    return w[0], T[vaxis, vaxis], T

def run(k, rmax, sig_r=0.02, B=40):
    t, ok = cast(D, rmax)
    Dok = D[ok]; tok = t[ok]
    P0 = Dok * tok[:, None]
    n0, w0, V0, _ = normals_pca(P0, k)
    l1_0, tvv0, _ = tensor_stats(n0)
    l1s, tvvs = [], []
    pred = []
    for b in range(B):
        r = tok + sig_r*rng.standard_normal(len(tok))
        P = Dok * r[:, None]
        n, w, V, idx = normals_pca(P, k)
        l1, tvv, T = tensor_stats(n)
        l1s.append(l1); tvvs.append(tvv)
        if b == 0:
            # plug-in analytic prediction: per-point x-variance sigma_n^2 * sum_m (u_m.x)^2 / lam_m
            # sigma_n^2 per patch from residual SS: lam3/(k-3); also using true sigma_r*cos(alpha)
            lam = w; U = V
            sig2 = lam[:, 0] / (k - 3)
            vx = U[:, 0, 1]**2 / lam[:, 1] + U[:, 0, 2]**2 / lam[:, 2]   # x comp of in-plane axes
            s2_i = sig2 * vx
            # with ideal-cos(alpha) sigma
            cosa = np.abs(np.sum(n0 * Dok, 1))
            s2_i_ideal = (sig_r*cosa)**2 * (V0[:, 0, 1]**2 / w0[:, 1] + V0[:, 0, 2]**2 / w0[:, 2])
            pred = (s2_i.mean(), s2_i_ideal.mean(), np.median(np.sqrt(s2_i)), np.median(np.sqrt(s2_i_ideal)))
    l1s = np.array(l1s); tvvs = np.array(tvvs)
    print(f"k={k} rmax={rmax} N={len(tok)} sigma_r={sig_r}: noise-free l1={l1_0:.2e} Tvv={tvv0:.2e}")
    print(f"   noisy: mean l1={l1s.mean():.3e} sd={l1s.std():.2e} max={l1s.max():.3e}; mean Tvv={tvvs.mean():.3e}")
    print(f"   plug-in pred mean floor: residual-based={pred[0]:.3e}, ideal(sigma_r cos a)={pred[1]:.3e}; median per-point sd(rad) resid={pred[2]:.3f}, ideal={pred[3]:.3f}")
    return l1s

if __name__ == "__main__":
    for k, rmax in [(20, 10), (20, 20), (20, 40), (10, 20), (40, 20)]:
        run(k, rmax)
