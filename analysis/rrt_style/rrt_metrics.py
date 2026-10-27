"""Four metrics per recording and method, for the RRT*-paper-style Table 3 (27 Oct 2026).
usage: python3 -I rrt_metrics.py <log name> <outdir>      one process per recording (extrinsics are read at import)
Methods: GZ = GenZ-LIO alone, VI = VINS-Mono alone, SW = Switch-SLAM rule (translation switched, rotation from the VIO = F12), SWR = same rule switching the whole 6-DoF increment, G17 = RTS core without safeguards,
G20 = RTS-Fusion.  GenZ-LIO and VINS-Mono take no feedback, so the replay of each method equals a live run.
Metrics (all after the usual rigid alignment; positions in m, angles in degrees):
  ate   full-span ATE RMSE (Umeyama SE(3), no scale)          maxerr  largest position error of the run
  rpe10 RMS of position increments over 10 s (global rotation removed, as v2_tools.rpe)
  rot10 RMS angle of the relative-rotation error over 10 s windows; the constant sensor-to-ground-truth frame offset X is
        estimated by Kabsch on the relative rotation vectors (Re = X^T Rg X), so it needs no extrinsic calibration."""
import sys, os, json, numpy as np
from scipy.spatial.transform import Rotation as Rot, Slerp
ME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "improve", "universal")
exec(open(os.path.join(ME, "logs_all.py")).read())
H_ = os.path.join(ME, "..", "vio_consistency", "harness.py")
src = open(H_).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '')
src = src.replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H_)))
exec(src)
exec(open(os.path.join(ME, "configs.py")).read())
name, outd = sys.argv[1], sys.argv[2]
seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
gpath = [e for e in LOGS if e[0] == name][0][4]
_, _, gt_q = vt.load_gt_full(gpath)
t = np.asarray(d["t"]); N = len(t)

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
res["GZ"] = metrics(np.array([a[1] for a in d["aft"]]), [a[0] for a in d["aft"]])
V = np.full((N, 3), np.nan)
for i, v in enumerate(d["vins"]):
    if v is not None: V[i] = v[1] + v[0] @ vt.t_IL
res["VI"] = metrics(V, [None if v is None else v[0] for v in d["vins"]])
for c in ("G17", "G20", "SW", "SWR"):
    p, gam = run(sr, vt, fc4, d, K, **CFG[c](fc4))
    res[c] = metrics(p, list(ROT))
out = dict(log=name, seq=seq, n=N, methods=res)
os.makedirs(outd, exist_ok=True); json.dump(out, open(os.path.join(outd, name + ".json"), "w"))
print(name, {m: {k: round(v, 3) for k, v in r.items()} for m, r in res.items() if m in ("GZ", "G20", "SW")})
