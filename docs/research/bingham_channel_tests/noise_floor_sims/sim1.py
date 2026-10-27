import numpy as np
from scipy.stats import chi2
rng = np.random.default_rng(0)

# ---------- Sim 1: iid tangent noise about true normals perpendicular to v=x ----------
def sim_iid(N, s, B=4000):
    l1 = np.empty(B); tvv = np.empty(B)
    for b in range(B):
        # true normals: walls (+-y) and floor/ceiling (+-z), 60/40 split
        ang = np.where(rng.random(N) < 0.6, 0.0, np.pi/2)
        n0 = np.stack([np.zeros(N), np.cos(ang), np.sin(ang)], 1)
        # tangent basis: x and the in-yz-plane perpendicular
        t1 = np.tile([1.0, 0, 0], (N, 1))
        t2 = np.stack([np.zeros(N), -np.sin(ang), np.cos(ang)], 1)
        e = s*(rng.standard_normal((N,1))*t1 + rng.standard_normal((N,1))*t2)
        n = n0 + e
        n /= np.linalg.norm(n, axis=1, keepdims=True)
        T = n.T @ n / N
        w = np.linalg.eigvalsh(T)
        l1[b] = w[0]; tvv[b] = T[0,0]
    return l1, tvv

print("=== Sim1: iid isotropic tangent noise, per-axis std s (rad) ===")
for N, s in [(200, 0.05), (1000, 0.05), (5000, 0.02), (5000, 0.10)]:
    l1, tvv = sim_iid(N, s, B=1500)
    pred_mean = s**2*(1-2/N)
    q99_chi = s**2*chi2.ppf(0.99, N)/N
    print(f"N={N} s={s}: mean l1={l1.mean():.3e} pred s^2(1-2/N)={pred_mean:.3e}; mean Tvv={tvv.mean():.3e} (s^2={s**2:.3e}); "
          f"q99(l1)={np.quantile(l1,0.99):.3e}  q99(Tvv)={np.quantile(tvv,0.99):.3e}  chi2 pred q99={q99_chi:.3e}; "
          f"std l1={l1.std():.2e} pred sqrt(2/N)s^2={np.sqrt(2/N)*s**2:.2e}")
