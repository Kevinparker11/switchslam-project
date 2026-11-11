#!/usr/bin/env python3
"""Offline check of the SWF IMU guess on a saved run: no ROS, no A-LOAM, no VINS-Mono, seconds per sequence.

Feeds imu_prop.ImuPropagator with the IMU of the bag (extract_imu.py) and the logged poses of a finished run as the scan updates, and
asks, scan by scan, how well the filter would have predicted the next increment BEFORE seeing the pose, in the LiDAR frame:
  one scan ahead, and three scans ahead (a few dropped scans), against the increment of the logged pose chain;
  next to two trivial predictors (zero motion, repeat the last logged increment);
  error split into along the direction of travel and across it (the corridor axis is where a scan-to-scan odometer slides);
  a sweep of the IMU-to-LiDAR time offset (a wrong offset is the most likely hidden fault);
  when the filter started (pose-aided start over the first 2 s window), gravity tilt, bias estimates.
Open loop: it cannot say whether A-LOAM stops sliding with this guess, because the guess changes what A-LOAM solves.  It says whether the guess is
good before a bag is played.  A guess whose one-scan error is not clearly below 'repeat the last increment' is not worth a closed-loop run.

usage: python3 offline_imu_check.py --imu imu.csv --log switching_log_v2_TAG.csv [--pose fused|aft] [--extrinsic-yaml F] [--csv out.csv]"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fusion_core as fc
import imu_prop as ip

T_LI = np.array([[0.999945562, 0.009074807, 0.005149763, 0.080],
                 [-0.009060897, 0.999955255, -0.002718066, 0.029],
                 [-0.005174199, 0.002671256, 0.999983046, 0.030],
                 [0, 0, 0, 1.0]])


def load_poses(path, which):
    L = pd.read_csv(path)
    L = L[pd.to_numeric(L["time"], errors="coerce").notna()].reset_index(drop=True)
    c = ["%s_%s" % (which, k) for k in ("x", "y", "z", "qx", "qy", "qz", "qw")]
    L = L.dropna(subset=c).reset_index(drop=True)
    t = L["time"].astype(float).values
    P = L[c[:3]].values.astype(float)
    Rs = [fc.quat_to_R(q) for q in L[c[3:]].values.astype(float)]
    return t, Rs, P


def run(imu, t, Rs, P, R_IL, t_IL, offset=0.0):
    """returns per-scan dict arrays for scans after the filter started"""
    f = ip.ImuPropagator(R_IL, t_IL)
    for r in imu:
        f.add(r[0] + offset, r[1:4], r[4:7])
    out = []
    started = None
    for k in range(len(t)):
        if not f.ready:
            if f.try_init(t[k], Rs[k], P[k]) and started is None:
                started = k
            continue
        rec = dict(k=k, t=t[k])
        if k >= 1:
            ref = fc.rel_body(Rs[k - 1], P[k - 1], Rs[k], P[k])
            inc = f.increment(t[k])
            rec["covered"] = inc is not None
            if inc is not None:
                e_t = inc[1] - ref[1]
                u = ref[1] / max(np.linalg.norm(ref[1]), 1e-9)
                rec.update(step=float(np.linalg.norm(ref[1])), e_t=float(np.linalg.norm(e_t)), e_along=float(e_t @ u),
                           e_across=float(np.linalg.norm(e_t - (e_t @ u) * u)),
                           e_r=float(np.degrees(np.linalg.norm(fc.so3_log(inc[0].T @ ref[0])))),
                           zero_t=float(np.linalg.norm(ref[1])), zero_r=float(np.degrees(np.linalg.norm(fc.so3_log(ref[0])))))
                if started is not None and k >= started + 2:
                    prev = fc.rel_body(Rs[k - 2], P[k - 2], Rs[k - 1], P[k - 1])
                    rec.update(rep_t=float(np.linalg.norm(prev[1] - ref[1])), rep_r=float(np.degrees(np.linalg.norm(fc.so3_log(prev[0].T @ ref[0])))))
        out.append(rec)
        f.update(t[k], Rs[k], P[k])
    return f, started, out


def ahead_errors(imu, t, Rs, P, R_IL, t_IL, ahead=3):
    """three scans ahead without update: state at scan k, prediction to scan k+ahead"""
    f = ip.ImuPropagator(R_IL, t_IL)
    for r in imu:
        f.add(r[0], r[1:4], r[4:7])
    errs = []
    for k in range(len(t)):
        if not f.ready:
            f.try_init(t[k], Rs[k], P[k]); continue
        if k + ahead < len(t):
            inc = f.increment(t[k + ahead])
            if inc is not None:
                ref = fc.rel_body(Rs[k], P[k], Rs[k + ahead], P[k + ahead])
                errs.append((t[k], float(np.linalg.norm(inc[1] - ref[1])), float(np.degrees(np.linalg.norm(fc.so3_log(inc[0].T @ ref[0])))),
                             float(np.linalg.norm(ref[1]))))
        f.update(t[k], Rs[k], P[k])
    return np.array(errs)


def q(x, p):
    x = np.asarray([v for v in x if np.isfinite(v)])
    return float(np.percentile(x, p)) if len(x) else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imu", required=True); ap.add_argument("--log", required=True)
    ap.add_argument("--pose", default="fused", choices=["fused", "aft"]); ap.add_argument("--extrinsic-yaml"); ap.add_argument("--csv")
    ap.add_argument("--no-sweep", action="store_true")
    a = ap.parse_args()
    T = T_LI
    if a.extrinsic_yaml:
        import yaml
        with open(a.extrinsic_yaml) as fh:
            T = np.array(yaml.safe_load(fh.read().replace("%YAML 1.2", ""))["laser_to_imu"]["data"]).reshape(4, 4)
    U, _, Vt = np.linalg.svd(T[:3, :3]); R_IL, t_IL = U @ Vt, T[:3, 3].copy()
    imu = pd.read_csv(a.imu).values.astype(float)
    t, Rs, P = load_poses(a.log, a.pose)
    print("IMU: %d samples, %.1f s, %.0f Hz;  poses (%s): %d scans, %.1f s, median step %.3f m"
          % (len(imu), imu[-1, 0] - imu[0, 0], len(imu) / (imu[-1, 0] - imu[0, 0]), a.pose, len(t), t[-1] - t[0],
             np.median([np.linalg.norm(P[i] - P[i - 1]) for i in range(1, len(P))])))
    if imu[0, 0] > t[0] + 0.5:
        print("WARNING: the IMU starts at %.1f, after the first pose %.1f (different clocks, or the IMU file is from another bag?)" % (imu[0, 0], t[0]))
    if imu[-1, 0] < t[-1] - 0.05:
        keep = t <= imu[-1, 0] - 0.05
        if keep.sum() < 50:
            print("WARNING: IMU span %.1f..%.1f does not cover the poses %.1f..%.1f (different clocks?)" % (imu[0, 0], imu[-1, 0], t[0], t[-1]))
        else:
            print("IMU file ends at +%.0f s: only the first %d scans (to +%.0f s) are checked" % (imu[-1, 0] - t[0], int(keep.sum()), t[keep][-1] - t[0]))
            t, Rs, P = t[keep], [r for r, k in zip(Rs, keep) if k], P[keep]
    f, started, rec = run(imu, t, Rs, P, R_IL, t_IL)
    if started is None:
        print("The filter never started: no 2 s window where the IMU and the poses give a gravity norm within 0.6 of 9.81 at any scan.")
        print("  SWF would use A-LOAM's increment for the whole run; check the first seconds of the IMU csv.")
        sys.exit(2)
    gdir = f.g / np.linalg.norm(f.g)
    print("Filter started at scan %d, +%.1f s after the first pose (init tries %d); |g| %.3f; |bg| at the end %.4f rad/s, |ba| %.3f m/s2; "
          "no-cover scans %d" % (started, t[started] - t[0], f.stats["init_tries"], np.linalg.norm(f.g), np.linalg.norm(f.bg), np.linalg.norm(f.ba), f.stats["no_cover"]))
    df = pd.DataFrame([r for r in rec if "e_t" in r])
    print("\nOne scan ahead, %d scans (LiDAR-frame increment, error against the logged pose chain)" % len(df))
    print("%-24s %9s %9s %9s %12s" % ("", "median", "90 %", "99 %", "unit"))
    for name, col, unit in (("IMU filter, translation", "e_t", "m"), ("  along travel (signed)", "e_along", "m"), ("  across travel", "e_across", "m"),
                            ("IMU filter, rotation", "e_r", "deg"), ("zero motion, translation", "zero_t", "m"),
                            ("repeat last, translation", "rep_t", "m"), ("repeat last, rotation", "rep_r", "deg")):
        if col in df:
            x = df[col].abs() if col == "e_along" else df[col]
            print("%-24s %9.4f %9.4f %9.4f %12s" % (name, q(x, 50), q(x, 90), q(x, 99), unit))
    ratio = q(df["e_t"], 50) / max(q(df["rep_t"], 50), 1e-9) if "rep_t" in df else float("nan")
    print("median translation error, IMU / repeat-last = %.2f   (below 1 means the IMU beats repeating the last step)" % ratio)
    e3 = ahead_errors(imu, t, Rs, P, R_IL, t_IL)
    if len(e3):
        print("\nThree scans ahead, no update in between (%d windows): translation error median %.4f m, 90 %% %.4f m (median travel %.3f m); rotation median %.3f deg"
              % (len(e3), np.median(e3[:, 1]), np.percentile(e3[:, 1], 90), np.median(e3[:, 3]), np.median(e3[:, 2])))
    print("\nBy 60 s segment (median one-scan translation error, m; travel per scan, m):")
    df["seg"] = ((df["t"] - t[0]) // 60).astype(int)
    for s, g in df.groupby("seg"):
        print("  %4d-%4d s  %.4f   step %.3f   along-signed %.4f" % (s * 60, s * 60 + 60, g["e_t"].median(), g["step"].median(), g["e_along"].median()))
    if not a.no_sweep:
        print("\nIMU time offset sweep (IMU stamps shifted by the offset; best = lowest median one-scan rotation error, which a time offset changes much more than the translation):")
        best, zero = None, None
        for off in np.arange(-0.1, 0.1001, 0.02):
            _, st, rr = run(imu, t, Rs, P, R_IL, t_IL, offset=off)
            d = pd.DataFrame([r for r in rr if "e_t" in r])
            if len(d):
                m_t, m_r = d["e_t"].median(), d["e_r"].median()
                print("  %+5.2f s   translation %.4f m   rotation %.3f deg" % (off, m_t, m_r))
                best = (m_r, off) if best is None or m_r < best[0] else best
                if abs(off) < 1e-9:
                    zero = m_r
        if best:
            off_bad = abs(best[1]) >= 0.04 and zero is not None and best[0] < 0.9 * zero          # at least 10 % better than no shift
            print("  best offset %+.2f s%s" % (best[1], "  (more than 10 %% better than 0 and %.2f s away: check the IMU / LiDAR stamps)" % abs(best[1]) if off_bad
                                               else "  (stamps look aligned)"))
    if a.csv:
        df.to_csv(a.csv, index=False); print("per-scan errors:", a.csv)


if __name__ == "__main__":
    main()
