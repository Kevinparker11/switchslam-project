"""Shared helpers for calibrate_c.py and fusion_summary.py (numpy + pandas)."""
import numpy as np
import pandas as pd
import fusion_core as fc

import os

BAG0_END = 1660857393.2 + 148.0          # Multi Floor: end of multifloor_0.bag (calibration segment)
T_LI = np.array([[0.999945562, 0.009074807, 0.005149763, 0.080],
                 [-0.009060897, 0.999955255, -0.002718066, 0.029],
                 [-0.005174199, 0.002671256, 0.999983046, 0.030],
                 [0, 0, 0, 1.0]])
if os.environ.get("EXTRINSIC_YAML"):     # other sequences: SubT-MRS extrinsics file with laser_to_imu
    import re
    _txt = open(os.environ["EXTRINSIC_YAML"]).read()
    _blk = _txt[_txt.index("laser_to_imu"):]
    _nums = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", _blk[_blk.index("data"):])
    T_LI = np.array([float(v) for v in _nums[:16]]).reshape(4, 4)
_U, _, _Vt = np.linalg.svd(T_LI[:3, :3])
R_IL, t_IL = _U @ _Vt, T_LI[:3, 3].copy()


def umeyama(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    U, _, Vt = np.linalg.svd((dst - mu_d).T @ (src - mu_s) / len(src))
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    return R, mu_d - R @ mu_s


def load_gt_full(path):
    """SubT-MRS csv (timestamp ns, p_w_b_xyz, q_w_b_xyzw) or TUM text (t x y z qx qy qz qw, seconds).
    returns t (s), p (n,3), q (n,4 xyzw) sorted by time"""
    try:
        g = pd.read_csv(path)
        t = g["timestamp"].values.astype(float)
        p = g[["p_w_b_x", "p_w_b_y", "p_w_b_z"]].values.astype(float)
        q = g[["q_w_b_x", "q_w_b_y", "q_w_b_z", "q_w_b_w"]].values.astype(float)
    except (KeyError, ValueError):
        g = np.loadtxt(path, comments="#")
        t, p, q = g[:, 0].astype(float), g[:, 1:4].astype(float), g[:, 4:8].astype(float)
    if t[0] > 1e12:
        t = t / 1e9
    o = np.argsort(t)
    return t[o], p[o], q[o]


def load_gt(path):
    t, p, _ = load_gt_full(path)
    return t, p


def ate(t, p, gt_t, gt_p, mask=None):
    m = (t >= gt_t[0]) & (t <= gt_t[-1]) & np.isfinite(p).all(1)
    if mask is not None:
        m &= mask
    if m.sum() < 20:
        return np.nan, np.nan
    g = np.stack([np.interp(t[m], gt_t, gt_p[:, i]) for i in range(3)], 1)
    R, tr = umeyama(p[m], g)
    e = np.linalg.norm(p[m] @ R.T + tr - g, axis=1)
    return float(np.sqrt((e ** 2).mean())), float(e.max())


def rpe(t, p, gt_t, gt_p, mask, horizon=1.0):
    """RMS error of position increments over `horizon` s, after removing the segment's global rotation"""
    m = mask & (t >= gt_t[0]) & (t <= gt_t[-1]) & np.isfinite(p).all(1)
    idx = np.where(m)[0]
    if len(idx) < 20:
        return np.nan
    g = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
    R, _ = umeyama(p[idx], g[idx])
    j = np.searchsorted(t, t[idx] + horizon)
    ok = j < len(t)
    idx, j = idx[ok], j[ok]
    ok = m[j]
    idx, j = idx[ok], j[ok]
    de = (p[j] - p[idx]) @ R.T - (g[j] - g[idx])
    return float(np.sqrt((np.linalg.norm(de, axis=1) ** 2).mean()))


def load_v2_log(path):
    """returns dict with t, aft (list of (R,p)), vins (list of (R,p) or None), H (list or None), hess_frame, df"""
    L = pd.read_csv(path)
    L = L[pd.to_numeric(L["time"], errors="coerce").notna()].reset_index(drop=True)
    t = L["time"].astype(float).values
    q = L[["aft_qx", "aft_qy", "aft_qz", "aft_qw"]].values
    pa = L[["aft_x", "aft_y", "aft_z"]].values
    aft = [(fc.quat_to_R(qq), pp) for qq, pp in zip(q, pa)]
    vq = L[["v_qx", "v_qy", "v_qz", "v_qw"]].values
    vp = L[["v_px", "v_py", "v_pz"]].values
    vins = [None if not np.isfinite(qq).all() else (fc.quat_to_R(qq), pp) for qq, pp in zip(vq, vp)]
    Hc = ["Hl_%d%d" % (i, j) for i in range(6) for j in range(6)]
    Hv = L[Hc].values
    H = [None if not np.isfinite(h).all() else h.reshape(6, 6) for h in Hv]
    src = str(L["hess_src"].dropna().iloc[0]) if "hess_src" in L and L["hess_src"].notna().any() else "/laser_hessian"
    return dict(t=t, aft=aft, vins=vins, H=H, hess_frame="world" if "mapping" in src else "body", df=L)


def replay(d, c_t, c_R=0.0, kth=15.7, kappa_mode="fixed", t_warm=20.0, mode="fused", w_mode="schur", alpha=0.7, tau_R=0.0, c_Rb=1.0, bias_axis="all", clip_R=0.0):
    """open-loop replay of the fusion on a logged run (the recorded scan-to-map poses are fixed)"""
    core = fc.FusionCore(R_IL, t_IL, c_t=0.0 if mode == "vins" else c_t, c_R=0.0 if mode == "vins" else c_R,
                         gate=fc.KappaGate(kth=kth, mode=kappa_mode), t_warm=1e12 if mode == "lidar" else t_warm,
                         hess_frame=d["hess_frame"], w_mode=w_mode, alpha=alpha, tau_R=tau_R, c_Rb=c_Rb, bias_axis=bias_axis, clip_R=clip_R)
    out, modes = [], []
    for k in range(len(d["t"])):
        R, p, info = core.step(d["t"][k], d["aft"][k], d["vins"][k], d["H"][k])
        out.append(p.copy())
        modes.append(info["mode"])
    return np.array(out), np.array(modes)
