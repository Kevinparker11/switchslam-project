import os
import sys, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")).read())
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
t = d["t"] - d["t"][0]
# per 1 s window, LiDAR frame
for k in range(len(t)):
    if not (38 <= t[k] <= 58): continue
    j = np.searchsorted(t, t[k] - 1.0)
    if d["vins"][k] is None or d["vins"][j] is None or (k % 10): continue
    Ra, pa = d["aft"][j]; Rb, pb = d["aft"][k]
    dRa, da = fc4.rel_body(Ra, pa, Rb, pb)
    dRI, dtI = fc4.rel_body(d["vins"][j][0], d["vins"][j][1], d["vins"][k][0], d["vins"][k][1])
    dRv, dv = fc4.imu_to_lidar_increment(dRI, dtI, vt.R_IL, vt.t_IL)
    ang = np.degrees(np.arccos(np.clip(da @ dv / (np.linalg.norm(da) * np.linalg.norm(dv) + 1e-9), -1, 1)))
    rot = np.degrees(np.linalg.norm(fc4.so3_log(dRa.T @ dRv)))
    print("t %5.1f |da| %.2f |dv| %.2f  angle %5.1f deg  rot diff %5.2f deg  mode %s" % (t[k], np.linalg.norm(da), np.linalg.norm(dv), ang, rot, d["df"]["mode"].iloc[k]))
