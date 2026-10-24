"""Diagnosis only (uses GT): for one recording and several configurations, split the error into
(a) heading: yaw of the fused trajectory relative to GT after SE(3) alignment, drift between first and last 10 %,
(b) scale: fused path length / GT path length over 10 s windows (median) and overall chord scale (Sim3 scale),
(c) ATE SE(3) and ATE after Sim(3) (scale allowed)."""
import sys, os, json, numpy as np
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read()); exec(open(os.path.join(ME, "configs.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
exec(open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '').replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H))))
name = sys.argv[1]; cfgs = sys.argv[2:]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
t = np.asarray(d["t"]); m = (t >= gt_t[0]) & (t <= gt_t[-1]); g = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
def sim3(P, G):
    mp, mg = P.mean(0), G.mean(0); X, Y = P - mp, G - mg
    U, S, Vt = np.linalg.svd(Y.T @ X / len(P)); D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ D @ Vt; s = np.trace(np.diag(S) @ D) / (X ** 2).sum(1).mean(); return R, s, mg - s * R @ mp
for c in cfgs:
    p = np.array([a[1] for a in d["aft"]]) if c == "GZ" else run(sr, vt, fc4, d, K, **CFG[c](fc4))[0]
    P, G = p[m], g[m]; R, s, tr = sim3(P, G)
    e3 = np.linalg.norm((s * P @ R.T + tr) - G, axis=1); se3, _ = vt.ate(t, p, gt_t, gt_p)
    # heading drift: direction of travel over 20 s chords, fused (aligned rotation, SE3) vs GT, first vs last 15 %
    R2, _ = vt.umeyama(P, G) if hasattr(vt, "umeyama") else (R, None)
    Q = P @ R2.T; k = max(1, int(np.searchsorted(t[m], t[m][0] + 20) ))
    def yaw(A): v = A[k:] - A[:-k]; return np.unwrap(np.arctan2(v[:, 1], v[:, 0]))
    dy = np.degrees(yaw(Q) - yaw(G)); ok = np.linalg.norm(G[k:] - G[:-k], axis=1) > 5
    n = len(dy); a, b = dy[: n // 7][ok[: n // 7]], dy[-n // 7:][ok[-n // 7:]]
    print(json.dumps(dict(log=name, cfg=c, ate=round(se3, 3), ate_sim3=round(float(np.sqrt((e3 ** 2).mean())), 3), sim3_scale=round(float(s), 4),
          yaw_start=round(float(np.median(a)), 2) if len(a) else None, yaw_end=round(float(np.median(b)), 2) if len(b) else None)))
