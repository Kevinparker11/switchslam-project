"""Four metrics (see rrt_metrics.py) for the 9 outage bags of the gap test (26 Oct 2026), from the recorded live logs:
GZ = GenZ-LIO alone (aft columns of the G23-run log), VI = VINS-Mono alone, G20 and G23 = the fused columns of the live logs.
usage: python3 -I rrt_outage_metrics.py <MF|LC|C02> <gappack dir> <out json>   (GT/extrinsics paths as in score_gap.py)"""
import sys, os, glob, json, csv, numpy as np
from scipy.spatial.transform import Rotation as Rot, Slerp
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
seqk, pack, outj = sys.argv[1:4]
GT = {'MF': os.environ["GT_MF"], 'LC': os.environ["GT_LC"], 'C02': os.environ["GT_C02"]}
EX = {'MF': None, 'LC': os.environ.get("EX_LC"), 'C02': os.environ.get("EX_C02")}
if EX[seqk]: os.environ["EXTRINSIC_YAML"] = EX[seqk]
sys.path.insert(0, os.path.join(REPO, "fusion_v4")); import v2_tools as vt
gt_t, gt_p, gt_q = vt.load_gt_full(GT[seqk])
def quat(L, a): return Rot.from_quat(L[[a + "qx", a + "qy", a + "qz", a + "qw"]].values.astype(float)).as_matrix()
def one(path):
    global t, N
    import pandas as pd
    L = pd.read_csv(path); L = L[pd.to_numeric(L["time"], errors="coerce").notna()].reset_index(drop=True)
    t = L["time"].astype(float).values; N = len(t)
    F = L[["fused_x", "fused_y", "fused_z"]].values.astype(float); RF = list(quat(L, "fused_"))
    A = L[["aft_x", "aft_y", "aft_z"]].values.astype(float); RA = list(quat(L, "aft_"))
    vq = L[["v_qx", "v_qy", "v_qz", "v_qw"]].values.astype(float); vp = L[["v_px", "v_py", "v_pz"]].values.astype(float)
    okv = np.isfinite(vq).all(1); RV = [None] * N; V = np.full((N, 3), np.nan)
    for i in np.where(okv)[0]:
        Ri = Rot.from_quat(vq[i]).as_matrix(); RV[i] = Ri; V[i] = vp[i] + Ri @ vt.t_IL
    return {"G23_or_G20": metrics(F, RF), "GZ": metrics(A, RA), "VI": metrics(V, RV)}
def rot_metric(Rm, horizon=10.0):
    ok = np.array([r is not None and np.isfinite(r).all() for r in Rm]) & (t >= gt_t[0]) & (t <= gt_t[-1])
    idx = np.where(ok)[0]
    if len(idx) < 50: return np.nan
    sl = Slerp(gt_t, Rot.from_quat(gt_q))
    Q = sl(np.clip(t, gt_t[0], gt_t[-1])).as_matrix()
    j = np.searchsorted(t, t[idx] + horizon); v = j < N
    idx, j = idx[v], j[v]; v = ok[j]; idx, j = idx[v], j[v]
    if len(idx) < 20: return np.nan
    Rm = np.array([Rm[i] if ok[i] else np.eye(3) for i in range(N)])
    Re = np.einsum('nji,njk->nik', Rm[idx], Rm[j]); Rg = np.einsum('nji,njk->nik', Q[idx], Q[j])
    ev = Rot.from_matrix(Re).as_rotvec(); gv = Rot.from_matrix(Rg).as_rotvec()
    w = np.linalg.norm(gv, axis=1) > 0.05
    if w.sum() < 10: w[:] = True
    U, _, Vt = np.linalg.svd(gv[w].T @ ev[w]); D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))]); Rr = Vt.T @ D @ U.T   # ev ~ Rr gv
    X = Rr.T
    err = Rot.from_matrix(np.einsum('nji,njk->nik', Re, np.einsum('ij,njk,kl->nil', X.T, Rg, X))).magnitude()
    return float(np.degrees(np.sqrt((err ** 2).mean())))

def metrics(P, Rm):
    ate, mx = vt.ate(t, P, gt_t, gt_p)
    m = np.isfinite(P).all(1)
    return dict(ate=ate, maxerr=mx, rpe10=vt.rpe(t, P, gt_t, gt_p, m, horizon=10.0), rot10=rot_metric(Rm))


res = {}
for dd in sorted(glob.glob(os.path.join(pack, seqk + "_*B_r?"))):
    tag = os.path.basename(dd)
    for cfg in ("G20", "G23"):
        r = one(os.path.join(dd, "switching_log_v2_%s_kf_run1.csv" % cfg))
        res[tag + "|" + cfg] = {"fused": r["G23_or_G20"], "GZ": r["GZ"], "VI": r["VI"]}
json.dump(res, open(outj, "w")); print(seqk, len(res), "logs")
