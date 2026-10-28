"""Point-to-plane ICP that also returns the information matrix of its estimate (numpy + scipy).

Used by the offline back end to verify loop closures and to build degeneracy-aware loop factors.

Convention
  T (4x4) maps SOURCE points (body frame of keyframe j) into the TARGET frame (body frame of keyframe i):
  x_i = R x_j + t, i.e. T = T_i^-1 T_j, the measurement of a gtsam BetweenFactorPose3(i, j).
  Perturbation on the right, T <- T * Exp([w, v]), which is GTSAM's Pose3 local chart ordered
  [rotation(3), translation(3)].  So H = sum J^T J below is, up to the noise scale, the information of
  that between factor in GTSAM's own coordinates.  Rotation is in radians (unlike the A-LOAM patches).
"""
import numpy as np
from scipy.spatial import cKDTree

import fusion_core as fc

I6 = np.eye(6)


# ----------------------------------------------------------------------------- point-cloud helpers
def voxel_down(P, voxel):
    """centroid per voxel"""
    P = np.asarray(P, float).reshape(-1, 3)
    if len(P) == 0:
        return P
    k = np.floor(P / voxel).astype(np.int64) + (1 << 20)
    key = (k[:, 0] << 42) | (k[:, 1] << 21) | k[:, 2]
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    out = np.zeros((len(cnt), 3))
    np.add.at(out, inv.ravel(), P)
    return out / cnt[:, None]


def estimate_normals(P, k=10):
    """unit normals and surface variation (lambda_min / sum) from k nearest neighbours"""
    tree = cKDTree(P)
    _, idx = tree.query(P, k=min(k, len(P)))
    nb = P[idx]
    X = nb - nb.mean(1, keepdims=True)
    C = np.einsum("nki,nkj->nij", X, X) / X.shape[1]
    w, V = np.linalg.eigh(C)
    return V[:, :, 0], w[:, 0] / np.maximum(w.sum(1), 1e-12)


def transform(T, P):
    return P @ T[:3, :3].T + T[:3, 3]


def se3(R, t):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, t
    return T


def inv_se3(T):
    R, t = T[:3, :3], T[:3, 3]
    return se3(R.T, -R.T @ t)


def right_update(T, xi):
    dT = np.eye(4)
    dT[:3, :3], dT[:3, 3] = fc.so3_exp(xi[:3]), xi[3:]
    return T @ dT


def se3_log_small(T):
    """[w, v] with w = Log(R), v = t (first order); used only for sizes of corrections"""
    return np.r_[fc.so3_log(T[:3, :3]), T[:3, 3]]


# ----------------------------------------------------------------------------- degeneracy quantities
def schur_rad(H):
    """Schur complements of a 6x6 information matrix ordered [rotation (rad), translation (m)]."""
    H = 0.5 * (H + H.T)
    Hrr, Hrt, Htr, Htt = H[:3, :3], H[:3, 3:], H[3:, :3], H[3:, 3:]
    eps = 1e-12 * max(np.trace(H), 1.0)
    S_RR = Hrr - Hrt @ np.linalg.solve(Htt + eps * np.eye(3), Htr)
    S_tt = Htt - Htr @ np.linalg.solve(Hrr + eps * np.eye(3), Hrt)
    S_RR, S_tt = 0.5 * (S_RR + S_RR.T), 0.5 * (S_tt + S_tt.T)
    er, Vr = np.linalg.eigh(S_RR)
    et, Vt = np.linalg.eigh(S_tt)
    er, et = np.clip(er, 1e-12, None), np.clip(et, 1e-12, None)
    return dict(S_RR=S_RR, S_tt=S_tt, eR=er, VR=Vr, et=et, Vt=Vt,
                kappa_R=float(er[-1] / er[0]), kappa_t=float(et[-1] / et[0]))


# ----------------------------------------------------------------------------- ICP
def _degenerate_projector(H, tau_rot, tau_trans=None):
    """projector removing Schur eigen-directions (per block) weaker than tau x the block's strongest"""
    tau_trans = tau_rot if tau_trans is None else tau_trans
    s = schur_rad(H)
    P = np.eye(6)
    nt = nr = 0
    for k in range(3):
        if s["et"][k] < tau_trans * s["et"][-1]:
            e = np.r_[np.zeros(3), s["Vt"][:, k]]
            P -= np.outer(e, e)
            nt += 1
        if s["eR"][k] < tau_rot * s["eR"][-1]:
            e = np.r_[s["VR"][:, k], np.zeros(3)]
            P -= np.outer(e, e)
            nr += 1
    return P, nt, nr, s


def _linearise(src, tgt, tgt_n, tree, T, max_corr, huber):
    R, t = T[:3, :3], T[:3, 3]
    pw = src @ R.T + t
    d, j = tree.query(pw, k=1, distance_upper_bound=max_corr)
    m = np.isfinite(d)
    if m.sum() < 50:
        return None
    n, q, ps = tgt_n[j[m]], tgt[j[m]], src[m]
    r = np.einsum("ij,ij->i", n, pw[m] - q)
    mR = n @ R
    J = np.hstack([np.cross(ps, mR), mR])
    a = np.abs(r)
    w = np.where(a <= huber, 1.0, huber / np.maximum(a, 1e-12))
    return dict(J=J, r=r, w=w, d=d, m=m)


def icp_p2pl(src, tgt, tgt_n, T0, schedule=(3.0, 1.5, 0.8), iters=(15, 15, 20), huber=0.1, tol=1e-5,
             tree=None, tau_update=0.01, inlier_dist=0.2):
    """Coarse-to-fine Gauss-Newton point-to-plane ICP with Huber weights.  Updates along Schur
    eigen-directions weaker than tau_update x the strongest of their block are dropped (as in
    Zhang et al. 2016, applied per rotation / translation block), so ICP cannot wander along a corridor
    axis.  Returns T, H (6x6, [rot rad, trans m], Huber-weighted J^T J at the solution), stats."""
    tree = tree if tree is not None else cKDTree(tgt)
    T = np.array(T0, float)
    stats = dict(ok=False, iters=0)
    for max_corr, n_it in zip(schedule, iters):
        for it in range(n_it):
            L = _linearise(src, tgt, tgt_n, tree, T, max_corr, huber)
            if L is None:
                stats.update(reason="too few correspondences")
                return T, None, stats
            Jw = L["J"] * L["w"][:, None]
            H = 0.5 * (Jw.T @ L["J"] + L["J"].T @ Jw)
            g = Jw.T @ L["r"]
            P, _, _, _ = _degenerate_projector(H, tau_update)
            mu = 1e-9 * np.trace(H)
            dx = -P @ np.linalg.solve(P @ H @ P + (np.eye(6) - P) * max(np.trace(H), 1.0) + mu * np.eye(6), P @ g)
            T = right_update(T, dx)
            stats["iters"] += 1
            if np.linalg.norm(dx[:3]) < tol and np.linalg.norm(dx[3:]) < tol:
                break
    L = _linearise(src, tgt, tgt_n, tree, T, schedule[-1], huber)
    if L is None:
        stats.update(reason="too few correspondences at the end")
        return T, None, stats
    J, r, w, d, m = L["J"], L["r"], L["w"], L["d"], L["m"]
    H = (J * w[:, None]).T @ J
    inl = d[m] < inlier_dist
    stats.update(ok=True, n_corr=int(m.sum()), fitness=float(np.sum(d < inlier_dist) / len(src)),
                 msd=float(np.mean(d[m] ** 2)), sigma2=float(np.sum(w * r * r) / np.sum(w)),
                 rmse_p2pl=float(np.sqrt(np.mean(r[inl] ** 2))) if inl.any() else np.nan)
    return T, 0.5 * (H + H.T), stats


# ----------------------------------------------------------------------------- loop-factor information
def loop_information(H, stats, model, inflate=10.0, floor_rot_deg=0.5, floor_trans=0.05,
                     tau_rot=0.05, tau_trans=0.05, scale=1.0):
    """6x6 information (GTSAM Pose3 order [rot, trans]) for a verified loop:
      'iso'     : LIO-SAM style, variance = ICP fitness score (mean squared NN distance) on all six axes
      'hessian' : CRLB of the point-to-plane estimate, H / sigma^2, inflated (x `inflate`) for correlated
                  residuals, plus a covariance floor (floor_rot_deg, floor_trans) on every axis
      'schur'   : 'hessian', then information removed along Schur eigen-directions whose eigenvalue is
                  below tau x the strongest of its block (translation and rotation separately), so a
                  loop cannot pin a degenerate direction (e.g. along a corridor axis)
    Returns (Lambda, info dict)."""
    if model == "iso":
        return scale * I6 / max(stats["msd"], 1e-4), dict(dropped_t=0, dropped_R=0)
    if model == "ot":
        # orientation-tensor loop factor (28 Oct 2026, docs/results/OT_Channel_Study.md): same total information as
        # 'iso' (trace 6/msd), but the translation part is shaped by the orientation tensor of the matched surface
        # normals, T = H_tt / tr(H_tt) (H_tt = sum w n n^T over the ICP correspondences): Lambda_t = 3 T / msd.
        # A loop then constrains translation only along directions in which its surfaces have normals (no free scale).
        Htt = 0.5 * (H[3:, 3:] + H[3:, 3:].T)
        T = Htt / max(float(np.trace(Htt)), 1e-12)
        Lam = np.zeros((6, 6))
        Lam[:3, :3] = I6[:3, :3]
        Lam[3:, 3:] = 3.0 * T
        Lam = scale * Lam / max(stats["msd"], 1e-4) + 1e-6 * I6
        return Lam, dict(dropped_t=int(np.linalg.eigvalsh(T)[0] < 0.01), dropped_R=0)
    Lam = H / max(stats["sigma2"], 1e-6) / inflate
    lam, V = np.linalg.eigh(0.5 * (Lam + Lam.T))
    lam = np.clip(lam, 1e-9 * max(lam[-1], 1e-9), None)
    Sigma = (V / lam) @ V.T + np.diag([np.radians(floor_rot_deg) ** 2] * 3 + [floor_trans ** 2] * 3)
    Lam = np.linalg.inv(Sigma)
    info = dict(dropped_t=0, dropped_R=0)
    if model == "schur":
        P, info["dropped_t"], info["dropped_R"], _ = _degenerate_projector(H, tau_rot, tau_trans)
        Lam = P @ Lam @ P
    Lam = scale * (0.5 * (Lam + Lam.T)) + 1e-6 * I6        # keep it positive definite for GTSAM
    return Lam, info
