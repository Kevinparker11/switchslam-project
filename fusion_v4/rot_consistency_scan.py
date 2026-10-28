#!/usr/bin/env python3
"""Read-only scan of fusion_node_v2 logs: how often does the VINS-Mono rotation disagree with the LiDAR (A-LOAM) rotation?
No setting is changed and nothing is run live; it reads switching_log_v2_*.csv(.gz) and prints a table.

For every window of length W s inside FUSED rows (VINS valid) it forms the window rotation increments of the LiDAR output (aft_q*)
and of VINS-Mono (v_q*, an IMU pose, moved to the LiDAR frame with the extrinsic R_IL), and reports
  e   = || log( dR_aft^T dR_vins ) ||  (rad)             total rotation disagreement
  eY  = |component of that error about world-up|  (yaw), eT = the rest (tilt), world-up from the VINS gravity direction
  ang = rotation angle of the LiDAR increment (rad)       how much the robot turned in the window
usage: rot_consistency_scan.py [--w 2,10] [--ext EXTRINSIC.yaml] log1.csv[.gz] log2.csv ...
Extrinsic default: the Multi Floor T_LI of v2_tools (use --ext for another rig, e.g. the farm yaml from make_live_extrinsics.py)."""
import sys, re, argparse
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
import fusion_core as fc

ap = argparse.ArgumentParser()
ap.add_argument("logs", nargs="+")
ap.add_argument("--w", default="2,10", help="window lengths in s, comma separated")
ap.add_argument("--ext", default=None)
a = ap.parse_args()

T_LI = np.array([[0.999945562, 0.009074807, 0.005149763, 0.080], [-0.009060897, 0.999955255, -0.002718066, 0.029],
                 [-0.005174199, 0.002671256, 0.999983046, 0.030], [0, 0, 0, 1.0]])
if a.ext:
    txt = open(a.ext).read()
    blk = txt[txt.index("laser_to_imu"):]
    nums = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", blk[blk.index("data"):])
    T_LI = np.array([float(v) for v in nums[:16]]).reshape(4, 4)
U, _, Vt = np.linalg.svd(T_LI[:3, :3])
R_IL = U @ Vt


def Rs(d, pre):
    q = d[[pre + "qx", pre + "qy", pre + "qz", pre + "qw"]].values
    return [fc.quat_to_R(x) if np.isfinite(x).all() else None for x in q]


print("%-44s %5s %5s %-3s %5s | %5s %5s %5s | %5s %5s | %5s %5s" % ("log (last 2 path parts)", "rows", "FUSED", "W", "n", "e_p50", "e_p95", "e_max", "eY_mx", "eT_mx", "a_p95", "a_max"))
for path in a.logs:
    d = pd.read_csv(path)
    t = d["time"].values
    ok = (d["mode"] == "FUSED").values
    RA, RV = Rs(d, "aft_"), Rs(d, "v_")
    for W in [float(x) for x in a.w.split(",")]:
        es, ey, et, an = [], [], [], []
        i0 = 0
        step = max(1, int(np.searchsorted(t, t[0] + 1.0)))        # about 1 s between windows
        for i in range(0, len(t), step):
            j = int(np.searchsorted(t, t[i] + W))
            if j >= len(t) or not ok[i:j + 1].all() or RA[i] is None or RV[i] is None or RA[j] is None or RV[j] is None:
                continue
            dA = RA[i].T @ RA[j]
            dV = R_IL.T @ (RV[i].T @ RV[j]) @ R_IL
            err = fc.so3_log(dA.T @ dV)
            up = R_IL.T @ (RV[i].T @ np.array([0.0, 0.0, 1.0]))     # world up in the LiDAR frame at the window start
            e = float(np.linalg.norm(err)); y = abs(float(err @ up)); tl = float(np.sqrt(max(e * e - y * y, 0.0)))
            es.append(e); ey.append(y); et.append(tl); an.append(float(np.linalg.norm(fc.so3_log(dA))))
        es = np.array(es)
        if len(es) == 0:
            print("%-44s %5d %5d %-3g %5d" % ("/".join(path.split("/")[-2:])[-44:], len(d), ok.sum(), W, 0))
        else:
            print("%-44s %5d %5d %-3g %5d | %5.3f %5.3f %5.3f | %5.3f %5.3f | %5.2f %5.2f" % ("/".join(path.split("/")[-2:])[-44:], len(d), ok.sum(), W, len(es),
                  np.percentile(es, 50), np.percentile(es, 95), es.max(), max(ey), max(et), np.percentile(an, 95), max(an)))
