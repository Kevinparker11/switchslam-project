"""How far does the LiDAR outrun the VINS in short windows on healthy logs, and when does it in MF-b2 (GenZ divergence)?
No GT used.  Windows of T s inside VINS-valid stretches without VINS jumps."""
import sys, os, json, numpy as np
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
exec(open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '').replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H))))
name, T = sys.argv[1], float(sys.argv[2]); seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
t = np.asarray(d["t"]); n = len(t)
sa = np.zeros(n); sv = np.full(n, np.nan)
for k in range(1, n):
    _, da = fc4.rel_body(d["aft"][k-1][0], d["aft"][k-1][1], d["aft"][k][0], d["aft"][k][1]); sa[k] = np.linalg.norm(da)
    if d["vins"][k] is not None and d["vins"][k-1] is not None:
        dR, dt = fc4.rel_body(d["vins"][k-1][0], d["vins"][k-1][1], d["vins"][k][0], d["vins"][k][1])
        _, dvl = fc4.imu_to_lidar_increment(dR, dt, vt.R_IL, vt.t_IL); sv[k] = np.linalg.norm(dvl)
t0 = t[0]; out = []
i = 0
while i < n:
    j = np.searchsorted(t, t[i] + T)
    if j >= n: break
    s = slice(i + 1, j + 1)
    if np.isfinite(sv[s]).all() and sv[s].max() < 1.0 and t[i] - t0 > 30:
        La, Lv = sa[s].sum(), sv[s].sum()
        out.append((t[i] - t0, La, Lv))
    i = j
O = np.array(out)
x = np.log(np.maximum(O[:, 1], 1e-3) / np.maximum(O[:, 2], 1e-3)); ex = O[:, 1] - O[:, 2]
mv = O[:, 1] >= 0.3          # LiDAR moved at least 0.3 m in the window
res = dict(log=name, seq=seq, T=T, n=len(O), lr_max=round(float(x[mv].max()), 3) if mv.any() else None,
           lr_p999=round(float(np.quantile(x[mv], 0.999)), 3) if mv.any() else None, ex_max=round(float(ex.max()), 3), ex_p999=round(float(np.quantile(ex, 0.999)), 3))
if name == "MF-b2":
    k = np.argmax((ex > 0.5)); res["first_ex>0.5_at"] = round(float(O[k, 0]), 1)
    k = np.argmax((x > 0.7) & mv); res["first_lr>0.7_at"] = round(float(O[k, 0]), 1)
print(json.dumps(res))
