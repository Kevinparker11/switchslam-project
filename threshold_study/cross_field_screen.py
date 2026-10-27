#!/usr/bin/env python3
"""Offline screen of threshold rules borrowed from other fields (same labels and split as threshold_screen.py).

usage: python3 cross_field_screen.py --log LOG.csv --gt ground_truth_path.csv
"""
import argparse
import numpy as np, pandas as pd
from scipy.stats import chi2, ncx2, genpareto
from scipy.optimize import brentq

ap = argparse.ArgumentParser()
ap.add_argument("--log", required=True); ap.add_argument("--gt", required=True)
ap.add_argument("--calib-end", type=float, default=1660857393.2 + 148.0)
ap.add_argument("--window", type=float, default=8.0); ap.add_argument("--min-path", type=float, default=2.0)
a = ap.parse_args()

L = pd.read_csv(a.log).sort_values("time").reset_index(drop=True); n = len(L)
H = L[[f"Hl_{i}{j}" for i in range(6) for j in range(6)]].values.reshape(n, 6, 6)
H = 0.5 * (H + H.transpose(0, 2, 1))
Dm = np.diag([0.5, 0.5, 0.5, 1, 1, 1]); Hr = Dm @ H @ Dm            # rotation block in radians
Hrr, Hrt, Htr, Htt = Hr[:, :3, :3], Hr[:, :3, 3:], Hr[:, 3:, :3], Hr[:, 3:, 3:]
Stt = Htt - Htr @ np.linalg.solve(Hrr, Hrt); Srr = Hrr - Hrt @ np.linalg.solve(Htt, Htr)
et, er = np.linalg.eigvalsh(Stt), np.linalg.eigvalsh(Srr)
kmax = np.maximum(et[:, 2] / et[:, 0], er[:, 2] / er[:, 0])
l1, l2, l3 = (L[c].values for c in ("bingham_l1", "bingham_l2", "bingham_l3"))   # ascending

# 1. Belsley-Kuh-Welsch: scale columns of J to unit length  <=>  H -> D H D with unit diagonal
d = 1 / np.sqrt(np.einsum("nii->ni", H)); Hs = H * d[:, :, None] * d[:, None, :]
es = np.linalg.eigvalsh(Hs); CI = np.sqrt(es[:, 5] / es[:, 0])          # largest condition index of J
# 2. Fox & Monette generalized VIF of the translation block = det(H_tt)/det(S_tt) (= same for rotation block)
GVIF = np.linalg.det(Htt) / np.linalg.det(Stt); g3 = GVIF ** (1 / 3)
vif_max = np.array([np.linalg.eigvals(np.linalg.solve(s, h)).real.max() for s, h in zip(Stt, Htt)])
# 3. Baarda detectability: non-centrality for alpha0 = 0.001, power 0.80, 1 dof
lam0 = brentq(lambda x: ncx2.sf(chi2.ppf(0.999, 1), 1, x) - 0.80, 1, 100)
sig, tau_t, tau_R = 0.03, 0.10, np.deg2rad(2.0)
# 6. Westin (1997, /lambda_max) and Demantke (2011, sqrt) shape classes on T
cl, cp, cs = (l3 - l2) / l3, (l2 - l1) / l3, l1 / l3
s1, s2, s3 = np.sqrt(l3), np.sqrt(l2), np.sqrt(l1)
a1, a2, a3 = (s1 - s2) / s1, (s2 - s3) / s1, s3 / s1

rules = {
    "X1 Belsley CI(J scaled) > 30": CI > 30,
    "X1b Belsley CI > 10": CI > 10,
    "X2 GVIF^(1/3) > 10 (VIF rule per dim)": g3 > 10,
    "X2b GVIF^(1/3) > 5": g3 > 5,
    "X2c worst-direction VIF > 10": vif_max > 10,
    "X3 Baarda MDD > 0.10 m / 2 deg": (et[:, 0] < lam0 * (sig / tau_t) ** 2) | (er[:, 0] < lam0 * (sig / tau_R) ** 2),
    "X6 Westin argmax not spherical": (cs < np.maximum(cl, cp)),
    "X6b Demantke argmax not 3D": (a3 < np.maximum(a1, a2)),
}

# labels (identical to threshold_screen.py)
g = pd.read_csv(a.gt); gt_t = g.timestamp.values / 1e9; gt_p = g[["p_w_b_x", "p_w_b_y", "p_w_b_z"]].values
t = L.time.values; p = L[["l_px", "l_py", "l_pz"]].values; m = (t >= gt_t[0]) & (t <= gt_t[-1])
gi = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
mu_s, mu_d = p[m].mean(0), gi[m].mean(0)
U, _, Vt = np.linalg.svd((gi[m] - mu_d).T @ (p[m] - mu_s) / m.sum())
S = np.eye(3); S[2, 2] = -1 if np.linalg.det(U) * np.linalg.det(Vt) < 0 else 1
pa = (p - mu_s) @ (U @ S @ Vt).T + mu_d
edges = np.arange(t[m][0], t[m][-1], a.window); win = np.full(n, -1); drift = []
for k in range(len(edges) - 1):
    i = np.where((t >= edges[k]) & (t < edges[k + 1]))[0]
    path = np.linalg.norm(np.diff(gi[i], axis=0), axis=1).sum() if len(i) >= 5 else 0
    if path < a.min_path: drift.append(np.nan); continue
    drift.append(np.linalg.norm((pa[i[-1]] - pa[i[0]]) - (gi[i[-1]] - gi[i[0]])) / path); win[i] = k
drift = np.array(drift); lo, hi = np.nanpercentile(drift, [33.3, 66.7])
lab = np.full(n, np.nan); ok = win >= 0
lab[ok] = np.where(drift[win[ok]] >= hi, 1, np.where(drift[win[ok]] <= lo, 0, np.nan))
calib = t < a.calib_end

# 4. Otsu on log10 kappa_max (calibration bag only, no labels)
x = np.log10(kmax[calib]); hist, be = np.histogram(x, 64); c = 0.5 * (be[1:] + be[:-1])
w0 = np.cumsum(hist); w1 = w0[-1] - w0; m0 = np.cumsum(hist * c)
mu0 = m0 / np.maximum(w0, 1); mu1 = (m0[-1] - m0) / np.maximum(w1, 1)
k_otsu = 10 ** c[np.argmax(w0 * w1 * (mu0 - mu1) ** 2)]
rules["X4 Otsu split of log kappa(S)"] = kmax > k_otsu
# 5. SPOT / peaks over threshold (risk q, t = 98 % quantile) on log kappa, calibration bag
z = np.log10(kmax[calib]); t98 = np.quantile(z, 0.98); pk = z[z > t98] - t98
gam, _, sc = genpareto.fit(pk, floc=0)
spot = {}
for q in (0.01, 0.001):
    zq = t98 + sc / gam * ((q * len(z) / len(pk)) ** (-gam) - 1) if abs(gam) > 1e-6 else t98 - sc * np.log(q * len(z) / len(pk))
    spot[q] = 10 ** zq; rules[f"X5 SPOT risk {q}"] = kmax > 10 ** zq

vofail = (L["mode"] == "LIDAR_ONLY_SAFE").values
def tc_share(flag):
    buf, tc = [], 0
    for f, v in zip(flag, vofail):
        if v: continue
        buf.append(bool(f)); buf = buf[-5:]; tc += all(buf)
    return tc / max(1, (~vofail).sum())

test = ~calib; tb, tg = test & (lab == 1), test & (lab == 0)
rows = [dict(rule=k, fire_rate=f.mean(), tc_share=tc_share(f), TPR_test=f[tb].mean(), FPR_test=f[tg].mean(),
             J_test=f[tb].mean() - f[tg].mean()) for k, f in rules.items()]
pd.set_option("display.width", 200)
print(f"lambda0(Baarda, a=0.001, power 0.8) = {lam0:.3f};  Baarda cut-offs: lmin(S_tt) < {lam0*(sig/tau_t)**2:.3f}, lmin(S_RR,rad) < {lam0*(sig/tau_R)**2:.2f}")
print(f"Otsu kappa = {k_otsu:.1f};  SPOT kappa: q=0.01 -> {spot[0.01]:.1f}, q=0.001 -> {spot[0.001]:.1f};  GPD shape {gam:.3f}")
print(f"medians: Belsley CI {np.median(CI):.1f}; GVIF^(1/3) {np.median(g3):.2f} (max {g3.max():.1f}); worst-dir VIF {np.median(vif_max):.2f} (max {vif_max.max():.1f})")
print(f"Westin cl/cp/cs medians {np.median(cl):.2f}/{np.median(cp):.2f}/{np.median(cs):.2f}")
print(pd.DataFrame(rows).round(3).to_string(index=False))
masked = (np.maximum(np.linalg.eigvalsh(Htt)[:, 2] / np.linalg.eigvalsh(Htt)[:, 0], np.linalg.eigvalsh(Hrr)[:, 2] / np.linalg.eigvalsh(Hrr)[:, 0]) <= 10) & (kmax > 10)
print(f"frames where the diagonal blocks pass kappa<=10 but the Schur blocks fail (masked by coupling): {masked.mean()*100:.1f}%")
print(f"  of those, GVIF^(1/3) median {np.median(g3[masked]) if masked.any() else float('nan'):.2f} vs {np.median(g3[~masked]):.2f} elsewhere")
