#!/usr/bin/env python3
"""Score a live F16 / F17 run.  usage: score_fused.py gt_live.txt switching_log_v2_<tag>.csv
Full-span ATE RMSE / max / end-point error (m), Umeyama SE(3), no scale, from max(reset, first FUSED/any fused row), for the fused output,
the A-LOAM output of the same log (aft_*, fed by the fused pose) and VINS-Mono alone (v_p*, rows where VINS exists).
Reset = largest ground-truth step > 0.5 m.  If the log has rot_gamma (F17): rows with the check closed, as % of FUSED rows and the time spans."""
import sys, csv
import numpy as np

def umeyama(src, dst):
    ms, md = src.mean(0), dst.mean(0)
    U, _, Vt = np.linalg.svd((dst - md).T @ (src - ms) / len(src))
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    return R, md - R @ ms

def ate(t, p, gt):
    m = (t >= gt[0, 0]) & (t <= gt[-1, 0]) & np.isfinite(p).all(1)
    t, p = t[m], p[m]
    if len(t) < 20:
        return None
    g = np.stack([np.interp(t, gt[:, 0], gt[:, i]) for i in (1, 2, 3)], 1)
    R, tr = umeyama(p, g)
    q = p @ R.T + tr
    e = np.linalg.norm(q - g, axis=1)
    return len(t), float(np.sqrt((e ** 2).mean())), float(e.max()), float(e[-1])

gt = np.loadtxt(sys.argv[1], comments="#", ndmin=2)
j = np.linalg.norm(np.diff(gt[:, 1:3], axis=0), axis=1)
k = int(np.argmax(j))
t_reset = gt[k + 1, 0] if j[k] > 0.5 else gt[0, 0]
g2 = gt[gt[:, 0] >= t_reset]
print("GT samples %d, reset at t=%.2f s (jump %.2f m), GT path after reset %.1f m" % (len(gt), t_reset, j[k], np.linalg.norm(np.diff(g2[:, 1:3], axis=0), axis=1).sum()))
rows = list(csv.DictReader(open(sys.argv[2])))
t = np.array([float(r["time"]) for r in rows])
mode = np.array([r["mode"] for r in rows])
def col(*names):
    return np.array([[float(r[n]) if r[n] not in ("", "nan") else np.nan for n in names] for r in rows])
ok = t >= t_reset
print("log rows after reset %d; modes: %s" % (ok.sum(), ", ".join("%s %d" % (m, (mode[ok] == m).sum()) for m in sorted(set(mode[ok])))))
for lab, names in (("FUSED output", ("fused_x", "fused_y", "fused_z")), ("A-LOAM output (fed by fused pose)", ("aft_x", "aft_y", "aft_z")),
                   ("VINS-Mono alone", ("v_px", "v_py", "v_pz"))):
    r = ate(t[ok], col(*names)[ok], g2)
    print("%-36s %s" % (lab, "too few samples" if r is None else "n=%d  ATE %.3f  max %.3f  end-point error %.3f m" % r))
if "rot_gamma" in rows[0]:
    rg = np.array([float(r["rot_gamma"]) for r in rows])
    fu = ok & (mode == "FUSED")
    cl = fu & (rg < 0.5)
    print("check closed on %d of %d FUSED rows (%.2f %%)" % (cl.sum(), fu.sum(), 100.0 * cl.sum() / max(fu.sum(), 1)))
    if cl.any():
        idx = np.where(cl)[0]
        br = np.where(np.diff(t[idx]) > 1.0)[0]
        st = np.r_[0, br + 1]; en = np.r_[br, len(idx) - 1]
        print("closed spans (s after reset): " + ", ".join("%.1f-%.1f" % (t[idx[a]] - t_reset, t[idx[b]] - t_reset) for a, b in zip(st, en)))
