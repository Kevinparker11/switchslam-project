#!/usr/bin/env python3
"""Offline replay of the fusion core on logged runs, with and without the LiDAR-gap rule (gap_T).  GenZ-LIO and VINS-Mono take no
feedback from the fusion, so the replay of the core on a log equals a live run except for Channel T+ (SAH), which needs the keyframe
files and is left out here: this script compares the core with and without the gap rule, not absolute accuracy.
  python3 replay_gap.py <seq MF|LC|C02> <gt file> <extrinsics yaml or -> <log.csv> [<log.csv> ...]
Prints full-span ATE (m) per log: live fused (from the log), replay G20 (gap_T = 0), replay G20 + gap rule."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
seq, gtf, ext = sys.argv[1:4]
if ext != "-":
    os.environ["EXTRINSIC_YAML"] = ext
sys.path.insert(0, os.path.join(HERE, ".."))
import numpy as np
import fusion_core as fc
import v2_tools as vt

GUARD_EX = 0.72
def vio_checks():
    slow = fc.VioConsistency(ref=0.156, stat="scale", rule="gate", avg=None, n_min=200)
    fast = fc.VioConsistency(ref=0.278, stat="scale", rule="gate", avg=5.0, n_min=25)
    return fc.VioChecks([slow, fast])

def run(d, gap_T=0.0, c_t=3e-6, **kw):
    core = fc.FusionCore(vt.R_IL, vt.t_IL, c_t=c_t, c_R=5e-6, gate=fc.KappaGate(kth=1e9), t_warm=20.0, hess_frame=d["hess_frame"],
                         vio_adapt=vio_checks(), vio_scale_T=10.0, lidar_guard_T=2.0, lidar_guard_ex=3 * GUARD_EX, gap_T=gap_T, **kw)
    P, M = [], []
    for k in range(len(d["t"])):
        R, p, info = core.step(d["t"][k], d["aft"][k], d["vins"][k], d["H"][k])
        P.append(p.copy()); M.append(info["mode"])
    return np.array(P), M

if __name__ == "__main__":
    gt_t, gt_p = vt.load_gt(gtf)
    for path in sys.argv[4:]:
        d = vt.load_v2_log(path)
        t = np.asarray(d["t"])
        live = d["df"][["fused_x", "fused_y", "fused_z"]].values
        row = [os.path.basename(os.path.dirname(path)) or os.path.basename(path)]
        for name, P in (("live", live), ("replay", run(d)[0]), ("gap", run(d, gap_T=1.0)[0]), ("lidar", np.array([a[1] for a in d["aft"]]))):
            row.append("%s %.2f" % (name, vt.ate(t, P, gt_t, gt_p)[0]))
        print("  ".join(row), flush=True)
