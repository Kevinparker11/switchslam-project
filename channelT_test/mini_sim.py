#!/usr/bin/env python3
"""Very short synthetic test of the orientation-tensor channel T against the Hessian Schur channel S_tt.
Protocol (written before the first run): docs/results/ChannelT_Mini_Test_Protocol.md.  usage: python3 mini_sim.py [--quick]"""
import sys
import numpy as np
from scipy.spatial import cKDTree

W, H_ROOM, RMAX = 3.0, 2.5, 25.0
RINGS = np.radians(np.linspace(-15, 15, 16))
AZ = np.radians(np.arange(0, 360, 0.2))
ORIGIN = np.array([0.0, 0.0, 1.25])
KS = [0, 1, 2, 3, 4, 6, 8, 12]
LABELS = [0.004, 0.002, 0.008]


def rays():
    az, rg = np.meshgrid(AZ, RINGS)
    d = np.stack([np.cos(rg) * np.cos(az), np.cos(rg) * np.sin(az), np.sin(rg)], -1).reshape(-1, 3)
    return d


def scene(K, rng):
    """list of (point on plane, normal, rect) ; rect None = infinite plane, else (axis1 range, axis2 range) for y,z"""
    P = [(np.array([0, W / 2, 0]), np.array([0, -1.0, 0]), None), (np.array([0, -W / 2, 0]), np.array([0, 1.0, 0]), None),
         (np.array([0, 0, 0.0]), np.array([0, 0, 1.0]), None), (np.array([0, 0, H_ROOM]), np.array([0, 0, -1.0]), None)]
    for _ in range(K):
        x = rng.uniform(3, 22) * rng.choice([-1, 1])
        side = rng.choice([-1, 1])
        y0 = side * (W / 2 - 0.2)
        lo, hi = sorted([y0, side * W / 2])
        nrm = np.array([-np.sign(x), 0, 0.0])          # face turned towards the scanner
        P.append((np.array([x, 0, 0]), nrm, ((lo, hi), (0.0, 2.1))))
    return P


def cast(d, planes):
    n = len(d)
    tbest = np.full(n, RMAX + 1.0)
    nbest = np.zeros((n, 3))
    for p0, nrm, rect in planes:
        den = d @ nrm
        with np.errstate(divide="ignore", invalid="ignore"):
            t = ((p0 - ORIGIN) @ nrm) / den
        ok = (den < -1e-9) & (t > 0.2) & (t < tbest)
        if rect is not None:
            hit = ORIGIN + t[:, None] * d
            ok &= (hit[:, 1] >= rect[0][0]) & (hit[:, 1] <= rect[0][1]) & (hit[:, 2] >= rect[1][0]) & (hit[:, 2] <= rect[1][1])
        tbest[ok] = t[ok]
        nbest[ok] = nrm
    m = tbest <= RMAX
    return tbest[m], nbest[m], m


def pca_normals(P, k=20):
    idx = cKDTree(P).query(P, k=k)[1]
    Q = P[idx] - P[idx].mean(1, keepdims=True)
    C = np.einsum("nki,nkj->nij", Q, Q) / k
    w, v = np.linalg.eigh(C)
    return v[:, :, 0]


def scores(P, n, rho, rng):
    N = len(P)
    T = (n[:, :, None] * n[:, None, :]).mean(0)
    sT = float(np.linalg.eigvalsh(T)[0])
    nh = n.copy()
    if rho > 0:
        bad = rng.random(N) < rho
        r = rng.normal(size=(bad.sum(), 3))
        nh[bad] = r / np.linalg.norm(r, axis=1, keepdims=True)
    J = np.concatenate([np.cross(P, nh), nh], 1)
    Hm = J.T @ J
    Hrr, Hrt, Htt = Hm[:3, :3], Hm[:3, 3:], Hm[3:, 3:]
    S = Htt - Hrt.T @ np.linalg.solve(Hrr, Hrt)
    sH = float(np.linalg.eigvalsh(0.5 * (S + S.T))[0] / N)
    return sH, sT, min(sH, sT)


def auc(score, pos):
    """P(score of a degenerate scan < score of a constrained scan); ties count 1/2"""
    a, b = score[pos], score[~pos]
    if len(a) == 0 or len(b) == 0:
        return np.nan
    return float(((a[:, None] < b[None, :]) + 0.5 * (a[:, None] == b[None, :])).mean())


def recall_at_fpr(cal_s, cal_pos, te_s, te_pos, fpr=0.05):
    neg = np.sort(cal_s[~cal_pos])
    if len(neg) == 0 or te_pos.sum() == 0:
        return np.nan
    thr = np.quantile(neg, fpr)                      # degenerate if score below thr
    return float((te_s[te_pos] < thr).mean())


def main():
    quick = "--quick" in sys.argv
    rng = np.random.default_rng(20261028)
    d = rays()
    ns = 3 if quick else 5
    rows = []                                          # (sigma, K, scene, truth_xx, {rho: (sH,sT,sHT)})
    for sigma in (0.02, 0.04):
        for K in KS:
            for sc in range(ns):
                planes = scene(K, rng)
                t, nt, m = cast(d, planes)
                for seed in range(2):
                    r2 = np.random.default_rng(rng.integers(1 << 30))
                    P = ORIGIN + (t + r2.normal(0, sigma, len(t)))[:, None] * d[m]
                    n = pca_normals(P)
                    txx = float((nt[:, 0] ** 2).mean())
                    out = {rho: scores(P, n, rho, r2) for rho in (0.0, 0.1, 0.3)}
                    rows.append((sigma, K, sc, seed, txx, out))
    print("scans: %d" % len(rows))
    for sigma in (0.02, 0.04):
        R = [r for r in rows if r[0] == sigma]
        txx = np.array([r[4] for r in R]); scene_id = np.array([r[1] * 100 + r[2] for r in R])
        print("\n=== sigma_r %.2f m: truth T_xx range %.4f - %.4f; scans with K=0: %d" % (sigma, txx.min(), txx.max(), sum(r[1] == 0 for r in R)))
        for lab in LABELS:
            pos = txx < lab
            print("-- label degenerate if T_true_xx < %.3f : %d degenerate / %d constrained scans" % (lab, pos.sum(), (~pos).sum()))
            for rho in (0.0, 0.1, 0.3):
                S = np.array([r[5][rho] for r in R])           # columns H, T, H+T
                res = {}
                ids = np.unique(scene_id)
                rng2 = np.random.default_rng(1)
                for j, name in enumerate(("H", "T", "H+T")):
                    res[name] = auc(S[:, j], pos)
                # bootstrap over scenes for AUC difference H+T - H
                diffs = []
                for _ in range(300):
                    pick = rng2.choice(ids, len(ids))
                    sel = np.concatenate([np.where(scene_id == s)[0] for s in pick])
                    a1, a0 = auc(S[sel, 2], pos[sel]), auc(S[sel, 0], pos[sel])
                    if np.isfinite(a1) and np.isfinite(a0):
                        diffs.append(a1 - a0)
                lo, hi = np.percentile(diffs, [2.5, 97.5])
                cal = np.array([(r[1] * 100 + r[2]) % 2 == 0 for r in R]); te = ~cal
                rec = {name: recall_at_fpr(S[cal, j], pos[cal], S[te, j], pos[te]) for j, name in enumerate(("H", "T", "H+T"))}
                print("   rho %.1f  AUC H %.3f  T %.3f  H+T %.3f | H+T - H = %+.3f [%.3f, %.3f] | recall@5%%FPR (held-out) H %.2f T %.2f H+T %.2f" %
                      (rho, res["H"], res["T"], res["H+T"], res["H+T"] - res["H"], lo, hi, rec["H"], rec["T"], rec["H+T"]))


if __name__ == "__main__":
    main()
