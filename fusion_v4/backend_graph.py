"""Offline back end: loop closure + pose-graph optimisation on keyframes from one recorded run.

Inputs (all from one run of the batch with RECORD_KF=1):
  keyframes_<tag>.npz      from keyframe_recorder.py: scan time, A-LOAM pose, body-frame scan (1 cm int16)
  switching_log_v2_<tag>.csv  the node's per-scan log (front-end trajectory = fused pose)
The front-end trajectory supplies the odometry chain; loops are found by proximity in the current
estimate, verified by point-to-plane ICP (backend_icp.py), and added as between factors whose
information follows one of the models in backend_icp.loop_information ('iso', 'hessian', 'schur').
Everything is causal-free batch processing, like the challenge entries' bundle adjustment; no ground
truth is used except, optionally, to calibrate the odometry noise on the calibration segment (bag 0).
"""
import numpy as np
from scipy.spatial import cKDTree

import fusion_core as fc
import backend_icp as bi


# ----------------------------------------------------------------------------- data loading
def load_keyframes(path):
    z = np.load(path)
    t, pose, n = z["t"], z["pose"], z["n"].astype(int)
    pts = z["pts"].astype(np.float64) * float(z["scale"]) if "scale" in z else z["pts"].astype(np.float64)
    off = np.r_[0, np.cumsum(n)]
    clouds = [pts[off[k]:off[k + 1]] for k in range(len(n))]
    T_aft = [bi.se3(fc.quat_to_R(p[3:7]), p[:3]) for p in pose]
    return dict(t=np.asarray(t, float), T_aft=T_aft, clouds=clouds)


def front_end_poses(df, cols=("fused_x", "fused_y", "fused_z", "fused_qx", "fused_qy", "fused_qz", "fused_qw")):
    v = df[list(cols)].values.astype(float)
    return [bi.se3(fc.quat_to_R(r[3:7]), r[:3]) for r in v]


def poses_at(t_query, t_scan, T_scan, tol=0.02):
    """front-end pose at each keyframe time (exact scan times; nearest within tol s)"""
    idx = np.searchsorted(t_scan, t_query)
    out, ok = [], []
    for q, i in zip(t_query, idx):
        cands = [k for k in (i - 1, i) if 0 <= k < len(t_scan)]
        k = min(cands, key=lambda k: abs(t_scan[k] - q))
        out.append(T_scan[k])
        ok.append(abs(t_scan[k] - q) <= tol)
    return out, np.array(ok)


# ----------------------------------------------------------------------------- odometry noise
def load_gt_poses(path):
    """SubT-MRS csv or TUM ground truth -> t (s), positions, rotations"""
    import v2_tools as vt
    t, p, q = vt.load_gt_full(path)
    R = [fc.quat_to_R(qq) for qq in q]
    return t, p, R


def _rot_at(t, gt_t, gt_R):
    i = int(np.clip(np.searchsorted(gt_t, t), 1, len(gt_t) - 1))
    return fc.interp_pose(t, gt_t[i - 1], gt_R[i - 1], np.zeros(3), gt_t[i], gt_R[i], np.zeros(3))[0]


def odometry_sigmas_from_gt(kf_t, T_front, gt_t, gt_p, mask, gt_R=None, floor_t=0.005, floor_r_deg=0.02):
    """Per-keyframe-step noise of the front end, measured on the calibration segment only (mask).
    translation: RMS of world-frame step errors after aligning the segment to ground truth (isotropic);
    rotation: RMS of step rotation errors after estimating the fixed rotation between the ground-truth
    body frame and the LiDAR frame from the step rotation axes (isotropic; floor if no GT rotation).
    Returns sigmas [rot x3 (rad), trans x3 (m)] or None."""
    idx = np.where(mask)[0]
    idx = idx[idx + 1 < len(kf_t)]
    idx = idx[mask[idx + 1]]
    if len(idx) < 10:
        return None
    p = np.array([T[:3, 3] for T in T_front])
    g = np.stack([np.interp(kf_t, gt_t, gt_p[:, i]) for i in range(3)], 1)
    sel = np.unique(np.r_[idx, idx + 1])
    R, _ = _umeyama(p[sel], g[sel])
    de = (p[idx + 1] - p[idx]) @ R.T - (g[idx + 1] - g[idx])
    s_t = max(float(np.sqrt(np.mean(np.sum(de ** 2, 1)) / 3.0)), floor_t)
    s_r = np.radians(floor_r_deg)
    if gt_R is not None:
        dF = [T_front[k][:3, :3].T @ T_front[k + 1][:3, :3] for k in idx]
        Gk = [_rot_at(kf_t[k], gt_t, gt_R) for k in range(len(kf_t))]
        dG = [Gk[k].T @ Gk[k + 1] for k in idx]
        rf = np.array([fc.so3_log(r) for r in dF])
        rg = np.array([fc.so3_log(r) for r in dG])
        big = (np.linalg.norm(rf, axis=1) > np.radians(1.0)) & (np.linalg.norm(rg, axis=1) > np.radians(1.0))
        if big.sum() >= 5:
            U, _, Vt = np.linalg.svd(rf[big].T @ rg[big])        # rf ~ C rg  (C = LiDAR <- GT body)
            C = U @ np.diag([1.0, 1.0, np.sign(np.linalg.det(U @ Vt))]) @ Vt
            err = [np.linalg.norm(fc.so3_log(dF[n].T @ C @ dG[n] @ C.T)) for n in range(len(idx))]
            s_r = max(float(np.sqrt(np.mean(np.square(err)) / 3.0)), s_r)
    return np.r_[[s_r] * 3, [s_t] * 3]


def _umeyama(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    U, _, Vt = np.linalg.svd((dst - mu_d).T @ (src - mu_s) / len(src))
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    return R, mu_d - R @ mu_s


# ----------------------------------------------------------------------------- loop search and verification
class LoopCloser:
    def __init__(self, clouds, min_gap_s=30.0, r_xy=8.0, dz=2.0, n_cand=3, k_target=8, k_source=1,
                 voxel_tgt=0.15, voxel_src=0.25, max_planarity=0.08, fit_min=0.6, rmse_max=0.08,
                 max_corr_rot_deg=15.0, max_corr_trans=4.0):
        self.clouds = clouds
        self.__dict__.update(min_gap_s=min_gap_s, r_xy=r_xy, dz=dz, n_cand=n_cand, k_target=k_target,
                             k_source=k_source, voxel_tgt=voxel_tgt, voxel_src=voxel_src,
                             max_planarity=max_planarity, fit_min=fit_min, rmse_max=rmse_max,
                             max_corr_rot=np.radians(max_corr_rot_deg), max_corr_trans=max_corr_trans)
        self._tgt_cache = {}

    def submap(self, center, T_est, half):
        Ti_inv = bi.inv_se3(T_est[center])
        lo, hi = max(0, center - half), min(len(self.clouds) - 1, center + half)
        P = [bi.transform(Ti_inv @ T_est[m], self.clouds[m]) for m in range(lo, hi + 1) if len(self.clouds[m])]
        return np.vstack(P) if P else np.zeros((0, 3))

    def candidates(self, t, T_est, done):
        """for each keyframe j: up to n_cand earlier keyframes i (time gap > min_gap_s, horizontal
        distance < r_xy, |dz| < dz in the CURRENT estimate), nearest first and at least 3 keyframes
        apart.  Returns {j: [i, ...]} for keyframes j without a verified loop yet."""
        P = np.array([T[:3, 3] for T in T_est])
        tree = cKDTree(P[:, :2])
        out = {}
        for j in range(len(P)):
            if j in done:
                continue
            c = []
            for i in tree.query_ball_point(P[j, :2], self.r_xy):
                if t[j] - t[i] >= self.min_gap_s and abs(P[j, 2] - P[i, 2]) <= self.dz:
                    c.append((np.linalg.norm(P[j] - P[i]), i))
            sel = []
            for _, i in sorted(c):
                if all(abs(i - k) >= 3 for k in sel):
                    sel.append(i)
                if len(sel) == self.n_cand:
                    break
            if sel:
                out[j] = sel
        return out

    def _target(self, i, T_est):
        tgt = bi.voxel_down(self.submap(i, T_est, self.k_target), self.voxel_tgt)
        if len(tgt) < 200:
            return None
        n, curv = bi.estimate_normals(tgt, 10)
        keep = curv < self.max_planarity
        if keep.sum() < 200:
            return None
        return tgt[keep], n[keep], cKDTree(tgt[keep])

    def verify(self, i, j, T_est):
        T0 = bi.inv_se3(T_est[i]) @ T_est[j]
        key = (i, j, np.round(T0[:3, :], 4).tobytes())
        if key in self._tgt_cache:                 # same pair, same initial guess -> same result
            return self._tgt_cache[key]
        v = self._verify(i, j, T_est)
        self._tgt_cache[key] = v
        return v

    def _verify(self, i, j, T_est):
        tg = self._target(i, T_est)
        src = bi.voxel_down(self.submap(j, T_est, self.k_source), self.voxel_src)
        if tg is None or len(src) < 100:
            return None
        tgt, n, tree = tg
        T0 = bi.inv_se3(T_est[i]) @ T_est[j]
        T, H, st = bi.icp_p2pl(src, tgt, n, T0, tree=tree)
        if H is None or not st["ok"]:
            return None
        corr = bi.inv_se3(T0) @ T
        st["corr_rot"] = float(np.linalg.norm(fc.so3_log(corr[:3, :3])))
        st["corr_trans"] = float(np.linalg.norm(corr[:3, 3]))
        s = bi.schur_rad(H)
        st.update(kappa_R=s["kappa_R"], kappa_t=s["kappa_t"])
        st["accept_geom"] = bool(st["fitness"] >= self.fit_min and st["rmse_p2pl"] <= self.rmse_max
                                 and st["corr_rot"] <= self.max_corr_rot and st["corr_trans"] <= self.max_corr_trans)
        return dict(i=i, j=j, T=T, H=H, stats=st)

    def best_for(self, j, cands, T_est):
        """verify every candidate i for keyframe j; return the accepted one with the best fitness"""
        best = None
        for i in cands:
            v = self.verify(i, j, T_est)
            if v is not None and v["stats"]["accept_geom"] and (best is None or v["stats"]["fitness"] > best["stats"]["fitness"]):
                best = v
        return best


# ----------------------------------------------------------------------------- pose graph
def optimise(T_odom, odom_sigmas, loops, T_init=None, robust="huber", robust_k=1.345, prior_sigma=1e-4,
             chi2_drop=22.46, prune_rounds=2, odom_cov=None):
    """T_odom: front-end keyframe poses (define the odometry chain and the prior on keyframe 0);
    T_init: starting values (default T_odom).  Loops get a Huber kernel (bounded but non-zero pull, so
    true loops far from the drifted estimate still converge; a Cauchy kernel would discard them), then
    loops whose Mahalanobis residual at the solution exceeds chi2_drop (chi2_6 at 0.999) are removed and
    the graph is re-solved.  Sets L['used'] on every loop.  Returns the optimised poses."""
    import gtsam
    T_init = T_odom if T_init is None else T_init
    active = list(range(len(loops)))
    for L in loops:
        L["used"] = True
    for rnd in range(prune_rounds + 1):
        graph = gtsam.NonlinearFactorGraph()
        init = gtsam.Values()
        for k, T in enumerate(T_init):
            init.insert(k, gtsam.Pose3(T))
        graph.add(gtsam.PriorFactorPose3(0, gtsam.Pose3(T_odom[0]), gtsam.noiseModel.Isotropic.Sigma(6, prior_sigma)))
        on = gtsam.noiseModel.Diagonal.Sigmas(np.asarray(odom_sigmas, float))
        for k in range(len(T_odom) - 1):
            nk = on if odom_cov is None else gtsam.noiseModel.Gaussian.Covariance(np.asarray(odom_cov[k], float))
            graph.add(gtsam.BetweenFactorPose3(k, k + 1, gtsam.Pose3(bi.inv_se3(T_odom[k]) @ T_odom[k + 1]), nk))
        for a in active:
            L = loops[a]
            base = gtsam.noiseModel.Gaussian.Information(L["Lambda"])
            if robust == "huber":
                nm = gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Huber.Create(robust_k), base)
            elif robust == "cauchy":
                nm = gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Cauchy.Create(robust_k), base)
            else:
                nm = base
            graph.add(gtsam.BetweenFactorPose3(L["i"], L["j"], gtsam.Pose3(L["T"]), nm))
        params = gtsam.LevenbergMarquardtParams()
        params.setMaxIterations(200)
        res = gtsam.LevenbergMarquardtOptimizer(graph, init, params).optimize()
        T_init = [res.atPose3(k).matrix() for k in range(len(T_odom))]
        if rnd == prune_rounds or not active:
            break
        keep = []
        for a in active:
            L = loops[a]
            E = bi.inv_se3(L["T"]) @ bi.inv_se3(T_init[L["i"]]) @ T_init[L["j"]]
            e = np.r_[fc.so3_log(E[:3, :3]), E[:3, 3]]
            L["chi2"] = float(e @ L["Lambda"] @ e)
            if L["chi2"] <= chi2_drop:
                keep.append(a)
            else:
                L["used"] = False
        if len(keep) == len(active):
            break
        active = keep
    return T_init


def otsu_tau(kappas, lo=10.0, hi=1000.0, default=0.05):
    """label-free degeneracy cut: Otsu (1979) on log10 kappa of this run's verified loops; a Schur
    eigen-direction is dropped when its eigenvalue is below 1/kappa_cut of the strongest in its block.
    The cut is kept in [lo, hi] (kappa < lo is never degenerate, kappa > hi always is)."""
    k = np.asarray(kappas, float)
    if len(k) < 10:
        return default, np.nan
    cut = fc.otsu_threshold(np.log10(k))
    kc = float(np.clip(10 ** cut, lo, hi)) if np.isfinite(cut) else 1.0 / default
    return 1.0 / kc, kc


MODELS = ("none", "iso", "hessian", "schur", "schur_otsu", "schur_gate", "ot")


def run_backend(kf_t, clouds, T_front_kf, odom_sigmas, model, rounds=2, closer=None, info_kw=None,
                verbose=False, odom_cov=None):
    """model: 'none' | 'iso' (LIO-SAM-like) | 'hessian' | 'schur' (fixed tau 0.05) |
    'schur_otsu' (tau from Otsu on this run's loop kappas, label-free) | 'schur_gate' (schur_otsu, and
    loops whose kappa_R is above the Otsu cut are rejected).  Returns optimised keyframe poses, loops."""
    if model == "none":
        return list(T_front_kf), []
    closer = closer or LoopCloser(clouds)
    info_kw = dict(info_kw or {})
    lam_model = "schur" if model.startswith("schur") else model
    T_est = list(T_front_kf)
    found = {}
    loops = []
    for r in range(rounds):
        for j, cands in closer.candidates(kf_t, T_est, set(found)).items():
            v = closer.best_for(j, cands, T_est)
            if v is not None:
                found[j] = v
        acc = list(found.values())
        kw = dict(info_kw)
        gate = np.inf
        if model in ("schur_otsu", "schur_gate"):
            kw["tau_trans"], kc_t = otsu_tau([v["stats"]["kappa_t"] for v in acc])
            kw["tau_rot"], kc_R = otsu_tau([v["stats"]["kappa_R"] for v in acc])
            if model == "schur_gate":
                gate = kc_R
        loops = []
        for v in acc:
            if v["stats"]["kappa_R"] > gate:
                continue
            Lam, inf = bi.loop_information(v["H"], v["stats"], lam_model, **kw)
            loops.append(dict(i=v["i"], j=v["j"], T=v["T"], Lambda=Lam, info=inf, stats=v["stats"]))
        T_est = optimise(T_front_kf, odom_sigmas, loops, T_init=T_est, odom_cov=odom_cov)
        loops = [L for L in loops if L.get("used", True)]
        if verbose:
            extra = ""
            if model in ("schur_otsu", "schur_gate"):
                extra = ", kappa cuts t %.0f R %.0f" % (1 / kw["tau_trans"], 1 / kw["tau_rot"])
            print("  round %d: %d accepted loops, %d kept after the chi2 check%s" % (r + 1, len(acc), len(loops), extra))
    return T_est, loops


def correct_all_scans(t_scan, T_scan_front, kf_t, T_kf_front, T_kf_opt):
    """apply each keyframe's correction to the front-end motion of the scans that follow it"""
    k = np.clip(np.searchsorted(kf_t, t_scan, side="right") - 1, 0, len(kf_t) - 1)
    C = [T_kf_opt[m] @ bi.inv_se3(T_kf_front[m]) for m in range(len(kf_t))]
    return np.array([(C[k[s]] @ T_scan_front[s])[:3, 3] for s in range(len(t_scan))])
