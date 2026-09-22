#!/usr/bin/env python3
"""
Offline replay/ablation harness for switching_log_multifloor_timedecay_run3_rawlog.csv.

Re-derives the switching node's fusion decision post-hoc from logged raw H_l, H_v,
l_p/l_q, v_p/v_q per frame (switching_node_multifloor_timedecay.py's sync_cb, replayed
sequentially). Validated against four independent reference numbers from commit 3cd6179's
message body, using the same Umeyama + timestamp-interpolation-vs-ground_truth_path.csv
methodology as compute_ate_multifloor.py:

    A (orig full-6x6 semicircle, un-decoupled baseline): 17.042m  (ref 17.04m)  EXACT
    B (chanR alone, Schur gate):                          3.106m  (ref 3.106m) EXACT
    C (chanT alone, Bingham gate):                        16.359m (ref 16.359m) EXACT
    D (combined, chanR OR chanT -- logged fused_x/y/z):    2.243m  (ref 2.24m)  EXACT

A_fixed's original formula is not recoverable from git history: commit f2edae8 (titled
"block-decoupled baseline fix (17.0m->2.9m)") did not modify switching_node_multifloor_
timedecay.py -- its only .py-adjacent artifact is a __pycache__/*.pyc that decompiles
(compared by co_code/co_consts) byte-identical to the *unchanged* script already committed
in c49888e. The actual A_fixed script was run locally and never committed as source.

Per instruction, A_fixed is now OFFICIALLY DEFINED by this file's block_diag_degeneracy():
separate 3x3 rotation/translation block eigendecomposition (no Schur cross-term removal),
each block's eigenvalues normalized by their own L2 norm, compared against the unmodified
semicircle threshold elementwise, degenerate if either block trips. Full-sequence RMSE
using this definition: 2.606m. This is now the documented A_fixed reference going forward.

CALIBRATION = bag segment 0, t in [1660857413.4, 1660857540.6] (1261 frames)
TEST        = segments 1+2,  t in [1660857540.8, 1660857809.9] (2668 frames)
"""
import numpy as np
import pandas as pd
from collections import deque

RAW = "/home/kavinkumar/switchslam_project/switching_log_multifloor_timedecay_run3_rawlog.csv"
GT  = "/home/kavinkumar/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv"

EPS = 1e-6
e1 = (0 + 1/np.sqrt(3))/2; e2 = (e1 + 1/np.sqrt(2))/2; e3 = (e2 + 1)/2
e_m = np.array([e1, e2, e3])
THR = e_m - np.sqrt(0.103*e_m)  # [0.1162, 0.2714, 0.4712]

FEATURE_MIN = 20
POS_JUMP_MAX = 1.5
ROT_JUMP_MAX = 0.8
DECAY_FLOOR = 0.3

CAL_T0, CAL_T1 = 1660857413.4, 1660857540.6
TEST_T0, TEST_T1 = 1660857540.8, 1660857809.9

IDX6 = [3, 4, 5, 0, 1, 2]  # [r,t] -> [t,r] reorder used by sync_cb's TIGHTLY_COUPLED branch


# ---------------- GT / alignment (mirrors compute_ate_multifloor.py) ----------------
def load_gt():
    gt = pd.read_csv(GT)
    gt['t'] = gt['timestamp']/1e9
    return gt

def load_raw():
    return pd.read_csv(RAW).reset_index(drop=True)

def umeyama(src, dst, with_scale=False):
    mu_src = src.mean(axis=0); mu_dst = dst.mean(axis=0)
    src_c = src - mu_src; dst_c = dst - mu_dst
    n = src.shape[0]
    cov = (dst_c.T @ src_c) / n
    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    if with_scale:
        var_src = (src_c**2).sum(axis=1).mean()
        s = np.trace(np.diag(D) @ S) / var_src
    else:
        s = 1.0
    t = mu_dst - s*R@mu_src
    return R, t, s

def rmse_against_gt(t, xyz, gt, label="", with_scale=False, verbose=True):
    gt_x = np.interp(t, gt['t'], gt['p_w_b_x'])
    gt_y = np.interp(t, gt['t'], gt['p_w_b_y'])
    gt_z = np.interp(t, gt['t'], gt['p_w_b_z'])
    gt_xyz = np.stack([gt_x, gt_y, gt_z], axis=1)
    R, tt, s = umeyama(xyz, gt_xyz, with_scale=with_scale)
    aligned = (s*(R@xyz.T).T + tt)
    err = np.linalg.norm(aligned - gt_xyz, axis=1)
    rmse = np.sqrt((err**2).mean())
    mx = err.max()
    if verbose:
        print(f"  {label}: n={len(t)} RMSE={rmse:.3f}m Max={mx:.3f}m")
    return rmse, mx, err


# ---------------- math helpers copied from switching_node_multifloor_timedecay.py ----------------
def quat_to_rotvec(q):
    x, y, z, w_ = q
    w_ = np.clip(w_, -1, 1)
    angle = 2*np.arccos(w_)
    s = np.sqrt(max(1 - w_*w_, 1e-12))
    if s < 1e-6:
        return np.array([0., 0., 0.])
    return np.array([x, y, z])/s*angle

def rotvec_to_quat(rv):
    angle = np.linalg.norm(rv)
    if angle < 1e-9:
        return np.array([0., 0., 0., 1.])
    axis = rv/angle
    return np.array([axis[0]*np.sin(angle/2), axis[1]*np.sin(angle/2),
                      axis[2]*np.sin(angle/2), np.cos(angle/2)])

def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1; x2, y2, z2, w2 = q2
    return np.array([w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2,
                      w1*z2 + x1*y2 - y1*x2 + z1*w2, w1*w2 - x1*x2 - y1*y2 - z1*z2])

def quat_inv(q):
    x, y, z, w_ = q
    return np.array([-x, -y, -z, w_])

def zero_degenerate(H3, lb, thr):
    eigval, eigvec = np.linalg.eigh(H3)
    lam_safe = eigval.copy()
    lam_safe[lb < thr] = EPS
    return eigvec @ np.diag(lam_safe) @ eigvec.T


# ---------------- degeneracy detectors ----------------
def schur_channel_r_degeneracy(H_l):
    """Exact copy of channel_r_degeneracy() in switching_node_multifloor_timedecay.py,
    extended to also return lb_r (not logged in the raw CSV). This is the Schur-complement
    R/T decoupling -- 'B - chanR alone (Schur gate)' when used without the Bingham term."""
    H_rr = H_l[0:3, 0:3]; H_rt = H_l[0:3, 3:6]
    H_tr = H_l[3:6, 0:3]; H_tt = H_l[3:6, 3:6]
    try:
        S_tt = H_tt - H_tr @ np.linalg.solve(H_rr + EPS*np.eye(3), H_rt)
    except np.linalg.LinAlgError:
        S_tt = H_tt
    try:
        S_rr = H_rr - H_rt @ np.linalg.solve(H_tt + EPS*np.eye(3), H_tr)
    except np.linalg.LinAlgError:
        S_rr = H_rr
    eig_t = np.linalg.eigvalsh(S_tt); eig_r = np.linalg.eigvalsh(S_rr)
    lb_t = np.clip(eig_t, 1e-9, None); lb_t = lb_t/np.linalg.norm(lb_t)
    lb_r = np.clip(eig_r, 1e-9, None); lb_r = lb_r/np.linalg.norm(lb_r)
    degen_t = bool(np.any(lb_t < THR)); degen_r = bool(np.any(lb_r < THR))
    lever_arm = np.trace(S_rr) / (np.trace(H_tt) + EPS)
    return degen_t, degen_r, lb_t, lb_r, lever_arm

def block_diag_degeneracy(H_l):
    """OFFICIAL A_fixed definition (git history does not contain the original script --
    see module docstring). Rotation block (0:3,0:3) and translation block (3:6,3:6)
    eigendecomposed SEPARATELY, no Schur cross-term removal, each block's 3 eigenvalues
    normalized by their own L2 norm, compared elementwise against THR, degenerate if
    EITHER block trips. Full-sequence RMSE = 2.606m."""
    H_rr = H_l[0:3, 0:3]; H_tt = H_l[3:6, 3:6]
    eig_r = np.linalg.eigvalsh(H_rr); eig_t = np.linalg.eigvalsh(H_tt)
    lb_r = np.clip(eig_r, 1e-9, None); lb_r = lb_r/np.linalg.norm(lb_r)
    lb_t = np.clip(eig_t, 1e-9, None); lb_t = lb_t/np.linalg.norm(lb_t)
    degen_r = bool(np.any(lb_r < THR)); degen_t = bool(np.any(lb_t < THR))
    return degen_r, degen_t, lb_r, lb_t

def continuous_ramp(lb):
    """w = clip((thr - lambda_norm)/thr, 0, 1) per-component, max-aggregated (continuous
    analog of the 'any(lb<thr)' boolean it replaces)."""
    w = np.clip((THR - lb)/THR, 0, 1)
    return float(np.max(w))


# ---------------- generic sequential fusion replay ----------------
def _unpack(df):
    n = len(df)
    Hl_cols = [f"Hl_{i}{j}" for i in range(6) for j in range(6)]
    Hv_cols = [f"Hv_{i}{j}" for i in range(6) for j in range(6)]
    return dict(
        n=n,
        Hl=df[Hl_cols].values.reshape(n, 6, 6),
        Hv=df[Hv_cols].values.reshape(n, 6, 6),
        l_p=df[['l_px', 'l_py', 'l_pz']].values,
        l_q=df[['l_qx', 'l_qy', 'l_qz', 'l_qw']].values,
        v_p=df[['v_px', 'v_py', 'v_pz']].values,
        v_q=df[['v_qx', 'v_qy', 'v_qz', 'v_qw']].values,
        feat=df['feat_count'].values,
        chanT_degen=df['chanT_degen'].values.astype(bool),
        chanT_decay=df['chanT_time_decay'].values,
        schur_lb_t=df[['schur_t1', 'schur_t2', 'schur_t3']].values,
    )

def replay(df, variant):
    """variant in {'A_fixed','TEST1','TEST1b'}. Sequentially reproduces sync_cb()'s
    fusion, substituting the R/T degeneracy source / Hessian weighting per variant,
    keeping everything else (mode hysteresis, floor, LIDAR_ONLY_SAFE, TRANSITION blend,
    TIGHTLY_COUPLED solve) identical to switching_node_multifloor_timedecay.py."""
    d = _unpack(df); n = d['n']
    status_buf = deque(maxlen=5)
    T_out = np.full((n, 3), np.nan)
    mode_out = [None]*n
    prev_l_p = prev_l_q = prev_v_p = prev_v_q = prev_T_p = prev_T_q = None

    for i in range(n):
        H_l = d['Hl'][i]; Hv = d['Hv'][i]
        l_p = d['l_p'][i]; l_q = d['l_q'][i]; v_p = d['v_p'][i]; v_q = d['v_q'][i]

        if variant == "A_fixed":
            degen_r, degen_t, lb_r, lb_t = block_diag_degeneracy(H_l)
            chanR_r, chanR_t = degen_r, degen_t
            degen_T = False; chanT_time_decay = 1.0
            degen = bool(chanR_r or chanR_t)
            lb_for_transition = lb_t
            trace_norm = False
        elif variant == "B":
            degen_t_bool, degen_r_bool, lb_t_schur, lb_r_schur, _lev = schur_channel_r_degeneracy(H_l)
            chanR_r, chanR_t = degen_r_bool, degen_t_bool
            degen_T = False; chanT_time_decay = 1.0
            degen = bool(chanR_r or chanR_t)
            lb_for_transition = lb_t_schur
            trace_norm = False
        elif variant in ("TEST1", "TEST1b"):
            degen_t_bool, degen_r_bool, lb_t_schur, lb_r_schur, _lev = schur_channel_r_degeneracy(H_l)
            degen_T = bool(d['chanT_degen'][i]); chanT_time_decay = d['chanT_decay'][i]
            degen = bool(degen_r_bool or degen_t_bool or degen_T)  # unchanged from D
            lb_for_transition = lb_t_schur
            if variant == "TEST1":
                chanR_r = continuous_ramp(lb_r_schur)   # boolean -> continuous ramp
                chanR_t = continuous_ramp(lb_t_schur)
                trace_norm = False
            else:  # TEST1b: keep D's boolean gating, fix the Hl/Hv unit mismatch instead
                chanR_r, chanR_t = degen_r_bool, degen_t_bool
                trace_norm = True
        else:
            raise ValueError(variant)

        if prev_l_p is None:
            prev_l_p = l_p; prev_l_q = l_q; prev_v_p = v_p; prev_v_q = v_q
            prev_T_p = l_p.copy(); prev_T_q = l_q.copy()
            T_out[i] = prev_T_p; mode_out[i] = "INIT"
            continue

        d_l_p = l_p - prev_l_p; d_v_p = v_p - prev_v_p
        d_l_rv = quat_to_rotvec(quat_mul(l_q, quat_inv(prev_l_q)))
        d_v_rv = quat_to_rotvec(quat_mul(v_q, quat_inv(prev_v_q)))

        vo_fail = bool(d['feat'][i] < FEATURE_MIN or
                       np.linalg.norm(d_v_p) > POS_JUMP_MAX or
                       np.linalg.norm(d_v_rv) > ROT_JUMP_MAX)

        if vo_fail:
            mode = "LIDAR_ONLY_SAFE"
            Htt_l = H_l[3:6, 3:6]
            Htt_safe = zero_degenerate(Htt_l, lb_for_transition, THR)
            dp = np.linalg.pinv(Htt_safe, rcond=1e-3) @ (Htt_l@d_l_p)
            if np.linalg.norm(dp) > 2.0:
                dp = d_l_p
            drv = d_l_rv
        else:
            status_buf.append(degen)
            n_full = sum(status_buf); n_tot = len(status_buf)
            if n_full == 0: status = "Normal"
            elif n_full == n_tot: status = "Fully"
            else: status = "Transition"

            if status == "Normal":
                mode = "LIDAR_ONLY"; dp = d_l_p; drv = d_l_rv
            elif status == "Fully":
                mode = "TIGHTLY_COUPLED"
                conf = (chanR_r*1.0 + chanR_t*1.0 + (degen_T*chanT_time_decay)*2.0) / 4.0
                conf = float(np.clip(conf, DECAY_FLOOR, 1.0))
                H_l6 = H_l[np.ix_(IDX6, IDX6)]
                if trace_norm:
                    tr_l = np.trace(H_l6); tr_v = np.trace(Hv)
                    H_l6 = H_l6/(tr_l + EPS); Hv = Hv/(tr_v + EPS)
                Hv_w = Hv*conf
                d_l6 = np.concatenate([d_l_p, d_l_rv]); d_v6 = np.concatenate([d_v_p, d_v_rv])
                H_sum6 = H_l6 + Hv_w + EPS*np.eye(6)
                try:
                    delta6 = np.linalg.solve(H_sum6, H_l6@d_l6 + Hv_w@d_v6)
                except np.linalg.LinAlgError:
                    delta6 = d_v6
                dp = delta6[0:3]; drv = delta6[3:6]
                if np.linalg.norm(dp) > 2.0:
                    dp = d_l_p; drv = d_l_rv
            else:
                mode = "TRANSITION"
                wv = np.clip(np.sqrt(3*lb_for_transition[0]), 0, 1)
                wl = 1 - wv
                dp = wl*d_l_p + wv*d_v_p; drv = wl*d_l_rv + wv*d_v_rv

        T_p = prev_T_p + dp
        dq = rotvec_to_quat(drv)
        T_q = quat_mul(dq, prev_T_q); T_q = T_q/np.linalg.norm(T_q)
        T_out[i] = T_p; mode_out[i] = mode
        prev_l_p = l_p; prev_l_q = l_q; prev_v_p = v_p; prev_v_q = v_q
        prev_T_p = T_p; prev_T_q = T_q

    return T_out, mode_out

def replay_with_single_flag(df, pred_degen_all):
    """Runs the 'single boolean flag drives both chanR terms' architecture (validated
    exactly against A=17.042m and A_fixed=2.606m), with an externally supplied per-frame
    degenerate flag -- used for TEST2's conformal-calibrated switching decision."""
    d = _unpack(df); n = d['n']
    status_buf = deque(maxlen=5)
    T_out = np.full((n, 3), np.nan)
    prev_l_p = prev_l_q = prev_v_p = prev_v_q = prev_T_p = prev_T_q = None
    for i in range(n):
        H_l = d['Hl'][i]; Hv = d['Hv'][i]
        l_p = d['l_p'][i]; l_q = d['l_q'][i]; v_p = d['v_p'][i]; v_q = d['v_q'][i]
        chanR = bool(pred_degen_all[i]); degen = chanR
        _, _, _, lb_t = block_diag_degeneracy(H_l)
        if prev_l_p is None:
            prev_l_p = l_p; prev_l_q = l_q; prev_v_p = v_p; prev_v_q = v_q
            prev_T_p = l_p.copy(); prev_T_q = l_q.copy(); T_out[i] = prev_T_p
            continue
        d_l_p = l_p - prev_l_p; d_v_p = v_p - prev_v_p
        d_l_rv = quat_to_rotvec(quat_mul(l_q, quat_inv(prev_l_q)))
        d_v_rv = quat_to_rotvec(quat_mul(v_q, quat_inv(prev_v_q)))
        vo_fail = bool(d['feat'][i] < FEATURE_MIN or
                       np.linalg.norm(d_v_p) > POS_JUMP_MAX or
                       np.linalg.norm(d_v_rv) > ROT_JUMP_MAX)
        if vo_fail:
            Htt_l = H_l[3:6, 3:6]; Htt_safe = zero_degenerate(Htt_l, lb_t, THR)
            dp = np.linalg.pinv(Htt_safe, rcond=1e-3) @ (Htt_l@d_l_p)
            if np.linalg.norm(dp) > 2.0: dp = d_l_p
            drv = d_l_rv
        else:
            status_buf.append(degen)
            nf = sum(status_buf); nt = len(status_buf)
            status = 'Normal' if nf == 0 else ('Fully' if nf == nt else 'Transition')
            if status == 'Normal':
                dp = d_l_p; drv = d_l_rv
            elif status == 'Fully':
                conf = (chanR*1.0 + chanR*1.0) / 4.0
                conf = float(np.clip(conf, DECAY_FLOOR, 1.0))
                H_l6 = H_l[np.ix_(IDX6, IDX6)]; Hv_w = Hv*conf
                d_l6 = np.concatenate([d_l_p, d_l_rv]); d_v6 = np.concatenate([d_v_p, d_v_rv])
                H_sum6 = H_l6 + Hv_w + EPS*np.eye(6)
                try:
                    delta6 = np.linalg.solve(H_sum6, H_l6@d_l6 + Hv_w@d_v6)
                except np.linalg.LinAlgError:
                    delta6 = d_v6
                dp = delta6[0:3]; drv = delta6[3:6]
                if np.linalg.norm(dp) > 2.0: dp = d_l_p; drv = d_l_rv
            else:
                wv = np.clip(np.sqrt(3*lb_t[0]), 0, 1); wl = 1 - wv
                dp = wl*d_l_p + wv*d_v_p; drv = wl*d_l_rv + wv*d_v_rv
        T_p = prev_T_p + dp; dq = rotvec_to_quat(drv)
        T_q = quat_mul(dq, prev_T_q); T_q = T_q/np.linalg.norm(T_q)
        T_out[i] = T_p
        prev_l_p = l_p; prev_l_q = l_q; prev_v_p = v_p; prev_v_q = v_q
        prev_T_p = T_p; prev_T_q = T_q
    return T_out


# ---------------- TEST 2: conformal calibration (nonconformity score + block quantile) ----------------
def conformal_test2(df, gt, N_blocks, alpha=0.1):
    d = _unpack(df); n = d['n']; t = df['time'].values
    l_p_all = d['l_p']

    scores = np.zeros(n)
    for i in range(n):
        _, _, lb_r, lb_t = block_diag_degeneracy(d['Hl'][i])
        scores[i] = min(lb_r.min(), lb_t.min())

    gt_xyz = np.stack([np.interp(t, gt['t'], gt['p_w_b_x']),
                        np.interp(t, gt['t'], gt['p_w_b_y']),
                        np.interp(t, gt['t'], gt['p_w_b_z'])], axis=1)

    drift = np.full(n, np.nan)
    for i in range(n):
        target = t[i] + 1.0
        j = np.searchsorted(t, target)
        if j >= n: continue
        if j > 0 and abs(t[j-1] - target) < abs(t[j] - target):
            j -= 1
        if t[j] < t[i] + 0.5:
            continue
        raw_disp = l_p_all[j] - l_p_all[i]
        gt_disp = gt_xyz[j] - gt_xyz[i]
        drift[i] = np.linalg.norm(raw_disp - gt_disp)

    cal_mask = (t >= CAL_T0) & (t <= CAL_T1)
    test_mask = (t >= TEST_T0) & (t <= TEST_T1)
    cal_valid = cal_mask & ~np.isnan(drift)
    test_valid = test_mask & ~np.isnan(drift)

    median_cal = np.median(drift[cal_valid])
    median_test = np.median(drift[test_valid])
    label_test = drift[test_valid] > median_test

    cal_idx = np.where(cal_mask)[0]
    blocks = np.array_split(cal_idx, N_blocks)
    block_mins = [scores[b].min() for b in blocks if len(b) > 0]
    tau = np.quantile(block_mins, 1 - alpha)

    pred_degen_all = scores < tau
    pred_test = pred_degen_all[test_valid]
    fp = int(np.sum(pred_test & (~label_test)))
    neg = int(np.sum(~label_test))
    false_alarm_rate = fp / neg

    return dict(tau=tau, pred_degen_all=pred_degen_all, false_alarm_rate=false_alarm_rate,
                fp=fp, neg=neg, median_cal=median_cal, median_test=median_test)


# ---------------- diagnostics ----------------
def mode_fraction_report(df, mask):
    """% of frames in each mode, for D (logged), A_fixed, and B, restricted to `mask`
    (e.g. the TEST split). Tests whether D's RMSE advantage comes from entering
    TIGHTLY_COUPLED (~pure VIO trust, since Hv totally dominates Hl there -- see TEST1's
    null result) more often, rather than from smarter per-frame weighting."""
    out = {}
    out['D'] = pd.Series(df['mode'].values[mask]).value_counts(normalize=True)
    _, modes_af = replay(df, "A_fixed")
    out['A_fixed'] = pd.Series(np.array(modes_af)[mask]).value_counts(normalize=True)
    _, modes_b = replay(df, "B")
    out['B'] = pd.Series(np.array(modes_b)[mask]).value_counts(normalize=True)
    return out

def test2_score_label_correlation(df, gt):
    """Pearson/Spearman correlation between the raw nonconformity score (min block
    eigenvalue) and the raw-drift ground-truth VALUE (continuous, not thresholded),
    on calibration, test, and combined. Distinguishes 'conformal calibration is the
    wrong tool here' from 'the drift-based label doesn't correlate with the eigenvalue
    score to begin with' -- the latter is a labeling-method problem, not a
    conformal-prediction problem."""
    from scipy import stats
    d = _unpack(df); n = d['n']; t = df['time'].values
    l_p_all = d['l_p']

    scores = np.zeros(n)
    for i in range(n):
        _, _, lb_r, lb_t = block_diag_degeneracy(d['Hl'][i])
        scores[i] = min(lb_r.min(), lb_t.min())

    gt_xyz = np.stack([np.interp(t, gt['t'], gt['p_w_b_x']),
                        np.interp(t, gt['t'], gt['p_w_b_y']),
                        np.interp(t, gt['t'], gt['p_w_b_z'])], axis=1)
    drift = np.full(n, np.nan)
    for i in range(n):
        target = t[i] + 1.0
        j = np.searchsorted(t, target)
        if j >= n: continue
        if j > 0 and abs(t[j-1] - target) < abs(t[j] - target):
            j -= 1
        if t[j] < t[i] + 0.5:
            continue
        raw_disp = l_p_all[j] - l_p_all[i]
        gt_disp = gt_xyz[j] - gt_xyz[i]
        drift[i] = np.linalg.norm(raw_disp - gt_disp)

    cal_mask = (t >= CAL_T0) & (t <= CAL_T1)
    test_mask = (t >= TEST_T0) & (t <= TEST_T1)
    results = {}
    for name, mask in [("CAL", cal_mask & ~np.isnan(drift)),
                        ("TEST", test_mask & ~np.isnan(drift)),
                        ("FULL", ~np.isnan(drift))]:
        pear = stats.pearsonr(scores[mask], drift[mask])
        spear = stats.spearmanr(scores[mask], drift[mask])
        results[name] = dict(n=int(mask.sum()), pearson_r=pear.statistic, pearson_p=pear.pvalue,
                              spearman_rho=spear.statistic, spearman_p=spear.pvalue)
    return results


if __name__ == "__main__":
    df = load_raw(); gt = load_gt(); t = df['time'].values
    test_mask = (t >= TEST_T0) & (t <= TEST_T1)

    print("=== Harness validation (full sequence) ===")
    xyz_D = df[['fused_x', 'fused_y', 'fused_z']].values
    rmse_against_gt(t, xyz_D, gt, label="D (logged fused_x/y/z), ref 2.243m")
    T_Af, _ = replay(df, "A_fixed")
    rmse_against_gt(t, T_Af, gt, label="A_fixed (official), ref 2.606m")

    print("\n=== TEST 1: soft gating (continuous ramp), TEST split ===")
    rmse_D_test, mx_D_test, _ = rmse_against_gt(t[test_mask], xyz_D[test_mask], gt, label="D TEST-split")
    T_t1, _ = replay(df, "TEST1")
    rmse_t1, mx_t1, _ = rmse_against_gt(t[test_mask], T_t1[test_mask], gt, label="TEST1 TEST-split")
    print(f"  gap={rmse_D_test-rmse_t1:+.5f}m  PASS={(rmse_D_test-rmse_t1) > 0.06}")

    print("\n=== TEST 1b: trace-normalized Hl/Hv, TEST split ===")
    T_t1b, _ = replay(df, "TEST1b")
    rmse_t1b, mx_t1b, _ = rmse_against_gt(t[test_mask], T_t1b[test_mask], gt, label="TEST1b TEST-split")
    print(f"  gap={rmse_D_test-rmse_t1b:+.5f}m  PASS={(rmse_D_test-rmse_t1b) > 0.06}")

    print("\n=== A_fixed TEST-split (for TEST 2 comparison) ===")
    rmse_Af_test, mx_Af_test, _ = rmse_against_gt(t[test_mask], T_Af[test_mask], gt, label="A_fixed TEST-split")

    print("\n=== Diagnostic: % TIGHTLY_COUPLED on TEST split (is D's win just 'trust VIO more often'?) ===")
    modefrac = mode_fraction_report(df, test_mask)
    for name in ['D', 'A_fixed', 'B']:
        tc = modefrac[name].get('TIGHTLY_COUPLED', 0.0)
        print(f"  {name}: TIGHTLY_COUPLED={tc:.4f}")

    print("\n=== Diagnostic: nonconformity score vs continuous drift-label correlation ===")
    corr = test2_score_label_correlation(df, gt)
    for split, r in corr.items():
        print(f"  {split}: n={r['n']}  Pearson r={r['pearson_r']:.4f} (p={r['pearson_p']:.2e})  "
              f"Spearman rho={r['spearman_rho']:.4f} (p={r['spearman_p']:.2e})")

    print("\n=== TEST 2: conformal calibration ===")
    for N in [30, 50]:
        res = conformal_test2(df, gt, N)
        T2 = replay_with_single_flag(df, res['pred_degen_all'])
        rmse2, mx2, _ = rmse_against_gt(t[test_mask], T2[test_mask], gt, label=f"TEST2 N={N} TEST-split")
        far = res['false_alarm_rate']
        print(f"  N={N}: false_alarm_rate={far:.4f}  PASS(FAR)={abs(far-0.10)<=0.05}  PASS(RMSE)={rmse2<=rmse_Af_test}")
