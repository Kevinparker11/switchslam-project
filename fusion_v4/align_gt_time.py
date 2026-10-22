#!/usr/bin/env python3
"""Put a ground-truth file on the bag's clock when its timestamps are on another one.

Needed for SubT-MRS Long Corridor (corridor01_gt.txt starts at t = 1517157219 s, the bag at 1690254112 s).
The GT is first moved so that its first pose coincides with the bag start, then a remaining offset delta is
searched in +-window seconds.

Decision: the correlation of the rotation speed |omega|(t) of the GT with that of the VINS-Mono rotation and of
the A-LOAM scan-to-map rotation stored in the log. |omega| does not depend on the world frame, on position
drift or on the fusion output, so the choice does not favour the method under test. The VINS and A-LOAM
offsets must agree (spread <= --max-spread s) or nothing is written.
Cross-check (printed, not used): the delta that minimises the SE(3)-aligned ATE (Umeyama, no scale) of the
VINS, A-LOAM and fused trajectories; a warning is printed if the fused one differs by more than 0.3 s.
Run it on ONE recording that is not used for the reported results (RUN_START=0), then freeze the aligned
file for every method and run.

usage: python3 align_gt_time.py --gt corridor01_gt.txt --bag-start 1690254112.82 \
           --logs ~/runs_corridor/switching_log_v2_F8_run0.csv [--seq-env ~/runs_corridor/seq.env]
"""
import argparse
import os
import shutil

import numpy as np

import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--gt", required=True)
ap.add_argument("--bag-start", type=float, default=None, help="start time on the clock the logs use (default: first time in the logs). NOT the rosbag-info record time when the sensor header stamps are on another clock")
ap.add_argument("--check-only", action="store_true", help="only report the offsets, write nothing")
ap.add_argument("--logs", nargs="+", required=True)
ap.add_argument("--window", type=float, default=40.0, help="search +- this many seconds around start-to-start alignment")
ap.add_argument("--step", type=float, default=0.05)
ap.add_argument("--min-cover", type=float, default=0.6, help="fraction of trajectory samples that must fall in the shifted GT span")
ap.add_argument("--min-sharp", type=float, default=1.15, help="ATE at +-1 s must exceed the minimum by this factor to count")
ap.add_argument("--max-spread", type=float, default=0.3)
ap.add_argument("--min-corr", type=float, default=0.5, help="rotation-speed correlation needed at the peak")
ap.add_argument("--min-gap", type=float, default=0.1, help="peak must exceed the value at +-1 s by this much")
ap.add_argument("--out", default=None)
ap.add_argument("--seq-env", default=None, help="seq.env whose GT= line is pointed at the aligned file")
a = ap.parse_args()

gt_t, gt_p, gt_q = vt.load_gt_full(a.gt)
if a.bag_start is None:
    a.bag_start = min(float(vt.load_v2_log(p)["t"].min()) for p in a.logs)
base = a.bag_start - gt_t[0]


def curve(t, p, deltas):
    out = np.full(len(deltas), np.nan)
    ok = np.isfinite(p).all(1)
    t, p = t[ok], p[ok]
    for i, d in enumerate(deltas):
        gt = gt_t + base + d
        m = (t >= gt[0]) & (t <= gt[-1])
        if m.sum() < a.min_cover * len(t) or m.sum() < 50:
            continue
        g = np.stack([np.interp(t[m], gt, gt_p[:, k]) for k in range(3)], 1)
        R, tr = vt.umeyama(p[m], g)
        out[i] = np.sqrt((np.linalg.norm(p[m] @ R.T + tr - g, axis=1) ** 2).mean())
    return out


def best(t, p):
    coarse = np.arange(-a.window, a.window + 1e-9, a.step)
    c = curve(t, p, coarse)
    if not np.isfinite(c).any():
        return None
    d0 = coarse[np.nanargmin(c)]
    fine = np.arange(d0 - a.step, d0 + a.step + 1e-9, 0.01)
    f = curve(t, p, fine)
    d = fine[np.nanargmin(f)]
    e = float(np.nanmin(f))
    side = curve(t, p, np.array([d - 1.0, d + 1.0]))
    sharp = float(np.nanmin(side) / e) if np.isfinite(side).any() else np.nan
    return d, e, sharp


from scipy.spatial.transform import Rotation as Rot, Slerp


def omega_series(t, q, w=0.6, dt=0.1):
    """rotation speed (rad/s) over a w-second window on a regular grid; frame independent"""
    ok = np.isfinite(q).all(1) & (np.abs(np.linalg.norm(q, axis=1) - 1) < 0.05)
    t, q = t[ok], q[ok]
    keep = np.r_[True, np.diff(t) > 1e-6]
    t, q = t[keep], q[keep]
    if len(t) < 30:
        return None, None
    sl = Slerp(t, Rot.from_quat(q))
    g = np.arange(t[0] + w / 2, t[-1] - w / 2, dt)
    ang = (sl(g - w / 2).inv() * sl(g + w / 2)).magnitude() / w
    return g, ang


def rot_corr(g_src, w_src, deltas):
    """Pearson correlation of the source rotation speed with the GT's, GT moved by base + delta"""
    out = np.full(len(deltas), np.nan)
    for i, d in enumerate(deltas):
        gt = gt_g + base + d
        m = (g_src >= gt[0]) & (g_src <= gt[-1])
        if m.sum() < a.min_cover * len(g_src) or m.sum() < 50:
            continue
        x = np.interp(g_src[m], gt, gt_w)
        y = w_src[m]
        if x.std() < 1e-9 or y.std() < 1e-9:
            continue
        out[i] = np.corrcoef(x, y)[0, 1]
    return out


def best_rot(g_src, w_src):
    coarse = np.arange(-a.window, a.window + 1e-9, a.step)
    c = rot_corr(g_src, w_src, coarse)
    if not np.isfinite(c).any():
        return None
    d0 = coarse[np.nanargmax(c)]
    fine = np.arange(d0 - a.step, d0 + a.step + 1e-9, 0.01)
    f = rot_corr(g_src, w_src, fine)
    d, pk = fine[np.nanargmax(f)], float(np.nanmax(f))
    side = rot_corr(g_src, w_src, np.array([d - 1.0, d + 1.0]))
    return d, pk, pk - float(np.nanmax(side))


gt_g, gt_w = omega_series(gt_t, gt_q)
if gt_g is None:
    raise SystemExit("ground truth has no usable orientation: cannot use the rotation-speed estimator")

print("GT: %d poses, %.1f s, starts at t = %.2f; start-to-start shift = %+.2f s" % (
    len(gt_t), gt_t[-1] - gt_t[0], gt_t[0], base))
rows, ate_fused = [], []
for path in a.logs:
    L = vt.load_v2_log(path)["df"]
    t = L["time"].astype(float).values
    tag = os.path.basename(path)
    for name, qc in [("aloam", ["aft_qx", "aft_qy", "aft_qz", "aft_qw"]), ("vins", ["v_qx", "v_qy", "v_qz", "v_qw"])]:
        g, w = omega_series(t, L[qc].values.astype(float))
        r = None if g is None else best_rot(g, w)
        if r is None:
            print("%-34s %-6s rotation speed: no usable overlap" % (tag, name))
            continue
        d, pk, gap = r
        use = pk >= a.min_corr and gap >= a.min_gap
        print("%-34s %-6s rotation-speed correlation %.2f at delta %+6.2f s (peak minus value at +-1 s: %.2f)  %s" % (
            tag, name, pk, d, gap, "USED" if use else "weak, not used"))
        if use:
            rows.append(d)
    for name, cols in [("vins", ["v_px", "v_py", "v_pz"]), ("aloam", ["aft_x", "aft_y", "aft_z"]), ("fused", ["fused_x", "fused_y", "fused_z"])]:
        r = best(t, L[cols].values.astype(float))
        if r is None:
            continue
        print("%-34s %-6s cross-check, ATE-minimising delta %+6.2f s (ATE %.2f m, +-1 s / best %.2f)" % (tag, name, r[0], r[1], r[2]))
        if name == "fused" and np.isfinite(r[2]) and r[2] >= a.min_sharp:
            ate_fused.append(r[0])
if not rows:
    raise SystemExit("rotation speed gives no clear peak: the trajectories do not constrain the time shift (nothing written)")
rows = np.array(rows)
spread = float(rows.max() - rows.min())
delta = float(np.median(rows))
print("offset from %d source(s): median %+.2f s, spread %.2f s" % (len(rows), delta, spread))
if spread > a.max_spread:
    raise SystemExit("sources disagree by more than %.2f s: not written. Check the log, or raise --max-spread knowingly." % a.max_spread)
if ate_fused and abs(np.median(ate_fused) - delta) > 0.3:
    print("WARNING: the ATE-minimising offset of the fused trajectory (%+.2f s) differs from the chosen one by %.2f s; "
          "look at both before trusting the alignment" % (np.median(ate_fused), abs(np.median(ate_fused) - delta)))

shift = base + delta
if a.check_only:
    print("check only: the ground truth needs a shift of %+.2f s to match the log clock (0 = already aligned); nothing written" % shift)
    raise SystemExit(0)
out = a.out or os.path.splitext(a.gt)[0] + "_aligned.txt"
with open(out, "w") as f:
    f.write("# %s shifted by %+.4f s to the bag clock (align_gt_time.py, delta %+.2f s from %d source(s))\n" % (
        os.path.basename(a.gt), shift, delta, len(rows)))
    for tt, pp, qq in zip(gt_t + shift, gt_p, gt_q):
        f.write("%.9f %.6f %.6f %.6f %.8f %.8f %.8f %.8f\n" % (tt, *pp, *qq))
print("wrote %s  (GT now spans %.1f .. %.1f)" % (out, gt_t[0] + shift, gt_t[-1] + shift))
if a.seq_env:
    shutil.copy(a.seq_env, a.seq_env + ".bak")
    lines = open(a.seq_env).read().splitlines()
    lines = [("GT=" + os.path.abspath(out)) if l.startswith("GT=") else l for l in lines]
    open(a.seq_env, "w").write("\n".join(lines) + "\n")
    print("updated GT= in %s (backup %s.bak)" % (a.seq_env, a.seq_env))
