"""Diagnosis only (GT): per 10 s window, speed error of LiDAR and VINS relative to GT (chord length ratio), and the LiDAR
translational information along the direction of travel (median c_T * u^T S_tt u)."""
import sys, os, json, numpy as np
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
exec(open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '').replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H))))
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
t = np.asarray(d["t"]); n = len(t); g = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1); ing = (t >= gt_t[0]) & (t <= gt_t[-1])
pa = np.array([a[1] for a in d["aft"]]); ok = np.array([v is not None for v in d["vins"]]); pv = np.array([v[1] if v is not None else [np.nan]*3 for v in d["vins"]])
rows = []; i = 0
while i < n:
    j = np.searchsorted(t, t[i] + 10.0)
    if j >= n: break
    if ok[i:j+1].all() and ing[i:j+1].all():
        Lg = np.linalg.norm(g[j] - g[i]); La = np.linalg.norm(pa[j] - pa[i]); Lv = np.linalg.norm(pv[j] - pv[i])
        # LiDAR information along travel (body frame of scan i)
        u = np.asarray(d["aft"][i][0]).T @ (pa[j] - pa[i]); u = u / max(np.linalg.norm(u), 1e-9)
        info = []
        for k in range(i, j, 5):
            if d["H"][k] is not None:
                _, S, _, _ = fc4.schur_blocks(d["H"][k], d["hess_frame"], np.asarray(d["aft"][k][0])); info.append(3e-6 * float(u @ S @ u))
        if Lg > 2: rows.append((t[i] - t[0], La / Lg, Lv / Lg, np.median(info) if info else np.nan))
    i = j
R = np.array(rows)
la, lv = np.log(R[:, 1]), np.log(R[:, 2])
print(json.dumps(dict(log=name, n=len(R), lidar_speed_err_rms=round(float(np.sqrt(np.mean(la**2))), 3), vins_speed_err_rms=round(float(np.sqrt(np.mean(lv**2))), 3),
   corr_lidar_vins=round(float(np.corrcoef(la, lv)[0, 1]), 2), info_along_med=round(float(np.nanmedian(R[:, 3])), 3),
   lidar_err_when_info_low=round(float(np.sqrt(np.mean(la[R[:, 3] < np.nanmedian(R[:, 3])]**2))), 3), lidar_err_when_info_high=round(float(np.sqrt(np.mean(la[R[:, 3] >= np.nanmedian(R[:, 3])]**2))), 3))))
