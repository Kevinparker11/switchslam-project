#!/usr/bin/env python3
"""Reproduces the offline evidence behind fusion_node_v2 from OLD switching logs (groundfix-style, with
v_p/v_q, aft_x/y/z, l_p/l_q and Hl_ij columns).

Caveats (also in the plan doc): open-loop (the recorded scan-to-map poses came from a run with the old node
in the loop); the old logs have no scan-to-map orientation, so increments are composed as world-frame
positions after aligning the A-LOAM map frame to the VINS frame with the first 30 s only; the Hessian is the
scan-to-SCAN one (/laser_hessian).  Treat the numbers as evidence for a design, not as results.
Section 5 shows how much the replayed full-span numbers (above all the maximum) depend on which window is
used for that frame alignment; the live node composes body-frame increments and needs no such alignment.

usage: python3 offline_evidence.py --gt ground_truth_path.csv LOG1.csv [LOG2.csv ...]
"""
import argparse
import numpy as np
import pandas as pd
import fusion_core as fc
import v2_tools as vt

ap = argparse.ArgumentParser()
ap.add_argument("--gt", required=True)
ap.add_argument("logs", nargs="+")
ap.add_argument("--calib-end", type=float, default=vt.BAG0_END)
a = ap.parse_args()
gt_t, gt_p = vt.load_gt(a.gt)
I = np.eye(3)


def kappa_R(h):
    return fc.schur_blocks(h, "body")[2]


for f in a.logs:
    L = pd.read_csv(f)
    L = L[(L.time >= 1660857413) & (L.time <= gt_t[-1])].reset_index(drop=True)
    t = L.time.values
    v = L[["v_px", "v_py", "v_pz"]].values
    a0 = L[["aft_x", "aft_y", "aft_z"]].values
    print("\n==", f, "(%d rows)" % len(t))
    # 1. each estimator alone
    for name, cols in [("fused (logged)", ["fused_x", "fused_y", "fused_z"]), ("A-LOAM scan-to-map", ["aft_x", "aft_y", "aft_z"]),
                       ("A-LOAM scan-to-scan", ["l_px", "l_py", "l_pz"]), ("VINS-Mono", ["v_px", "v_py", "v_pz"])]:
        print("  %-22s ATE RMSE %.3f  max %.3f" % ((name,) + vt.ate(t, L[cols].values, gt_t, gt_p)))
    # 2. where is the VINS maximum?
    g = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
    R, tr = vt.umeyama(v, g)
    e = np.linalg.norm(v @ R.T + tr - g, axis=1)
    rel = t - t[0]
    print("  VINS max error in its first 20 s: %.2f m; afterwards: %.2f m" % (e[rel < 20].max(), e[rel >= 20].max()))
    # 3. frame offsets
    m30 = rel < 30
    for name, x in [("A-LOAM odom frame", L[["l_px", "l_py", "l_pz"]].values), ("A-LOAM map frame", a0)]:
        Rr, _ = vt.umeyama(v[m30], x[m30])
        print("  VINS world vs %-18s: %.1f deg (first 30 s)" % (name, np.degrees(np.linalg.norm(fc.so3_log(Rr)))))
    # 4. fusion variants, held-out bags 1-2
    Ra, ta = vt.umeyama(a0[m30], v[m30])
    aa = a0 @ Ra.T + ta
    H = L[["Hl_%d%d" % (i, j) for i in range(6) for j in range(6)]].values
    Rwb = [fc.quat_to_R(q) for q in L[["v_qx", "v_qy", "v_qz", "v_qw"]].values]
    S, kR = [], []
    for h, Rm in zip(H, Rwb):
        S_RR, S_tt, k_R, _ = fc.schur_blocks(h, "body")
        S.append(Rm @ S_tt @ Rm.T)
        kR.append(k_R)
    S, kR = np.array(S), np.array(kR)
    dv = np.vstack([np.zeros(3), np.diff(v, axis=0)])
    da = np.vstack([np.zeros(3), np.diff(aa, axis=0)])
    warm, gate = rel < 20, kR <= 15.7
    cal, test = t < a.calib_end, t >= a.calib_end

    def run(W):
        W = np.where(warm[:, None, None], I[None], W)
        return np.cumsum(np.einsum("nij,nj->ni", W, da) + np.einsum("nij,nj->ni", I[None] - W, dv), axis=0) + v[0]

    rows = [("VINS only", vt.ate(t, v, gt_t, gt_p, cal) + vt.ate(t, v, gt_t, gt_p, test) + vt.ate(t, v, gt_t, gt_p), np.nan)]
    best = None
    for c in [1e-5, 1e-4, 3e-4, 1e-3, 3e-3]:
        W = np.array([fc.info_weight(s, c) for s in S]) * gate[:, None, None]
        p = run(W)
        r = vt.rpe(t, p, gt_t, gt_p, cal & ~warm)
        rows.append(("directional c=%g, kappa_R gate" % c, vt.ate(t, p, gt_t, gt_p, cal) + vt.ate(t, p, gt_t, gt_p, test) + vt.ate(t, p, gt_t, gt_p), r))
        if best is None or r < best[1]:
            best = (c, r)
    p0 = run(np.zeros((len(t), 3, 3)))
    r0 = vt.rpe(t, p0, gt_t, gt_p, cal & ~warm)
    rows.insert(1, ("LiDAR warm-up 20 s, then VINS", vt.ate(t, p0, gt_t, gt_p, cal) + vt.ate(t, p0, gt_t, gt_p, test) + vt.ate(t, p0, gt_t, gt_p), r0))
    print("  %-34s %16s %16s %16s %10s" % ("variant", "bag0 RMSE/max", "bags1-2 RMSE/max", "full RMSE/max", "bag0 RPE1s"))
    for name, x, r in rows:
        print("  %-34s %8.3f/%6.2f  %8.3f/%6.2f  %8.3f/%6.2f %10.4f" % ((name,) + tuple(x) + (r,)))
    chosen = best[0] if best[1] < r0 else 0.0
    print("  c chosen on bag 0 by RPE(1 s): %g  (0 = keep VINS only)" % chosen)

    # 5. how much the replay depends on the A-LOAM -> VINS frame alignment (the live node needs none)
    Wd = np.array([fc.info_weight(s, 1e-3) for s in S]) * gate[:, None, None]
    print("  sensitivity to the 30-60 s window used to align the A-LOAM map frame to VINS (replay artefact):")
    print("  %-12s %7s %16s %16s %16s %14s" % ("window (s)", "angle", "warm-up full", "c=1e-3 full", "c=1e-3 bags1-2", "max at (s)"))
    for lo, hi in [(0, 30), (10, 40), (20, 50), (20, 80), (30, 90)]:
        mw = (rel >= lo) & (rel < hi)
        Rw, tw = vt.umeyama(a0[mw], v[mw])
        da = np.vstack([np.zeros(3), np.diff(a0 @ Rw.T + tw, axis=0)])
        pw, pd_ = run(np.zeros((len(t), 3, 3))), run(Wd)
        Rg, tg = vt.umeyama(pd_, g)
        kmax = np.argmax(np.linalg.norm(pd_ @ Rg.T + tg - g, axis=1))
        print("  [%2d, %2d)     %6.1f° %8.3f/%6.2f  %8.3f/%6.2f  %8.3f/%6.2f %10.0f" % (
            (lo, hi, np.degrees(np.linalg.norm(fc.so3_log(Rw)))) + vt.ate(t, pw, gt_t, gt_p) + vt.ate(t, pd_, gt_t, gt_p)
            + vt.ate(t, pd_, gt_t, gt_p, test) + (rel[kmax],)))
