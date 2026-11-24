#!/usr/bin/env python3
"""Read-only diagnosis of one scored run: where does the error come from, and is it the trajectory or the clock?  Nothing is rescored or changed;
the score of the run stays the one score_tum.py printed.
usage (from fusion_v4/): python3 stock_liosam/diag_error_time.py --gt GT --est run/odom.tum [--window 30] [--fit-seconds 60]

Prints
  1. pose count, time spans of run and ground truth, whether the stamps overlap (a clock offset between bag and ground truth would show here)
  2. the estimated path length against the ground-truth path length over the same span, the largest single step and the number of steps above 3 m
  3. the error over time with the alignment fitted on the first --fit-seconds only (a healthy run grows slowly; a runaway shows a sudden jump), per window:
     poses, estimated path, ground-truth path, mean and max error; and the first times the error passes 5 m and 20 m
  4. a time-shift check: the full-span ATE after shifting the run's stamps by -20 .. +20 s. If a shift of a few seconds lowers the error a lot,
     the stamps and the ground truth are not on the same clock (a setup question); if no shift helps, it is the trajectory itself."""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import v2_tools as vt


def path_len(p):
    return float(np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1))) if len(p) > 1 else 0.0


def analyse(gt_t, gt_p, t, p, window=30.0, fit_seconds=60.0, shifts=None):
    """-> dict with the numbers printed by main(); pure function so it can be tested."""
    out = {}
    ok = np.isfinite(p).all(1)
    t, p = t[ok], p[ok]
    out["n"] = len(t)
    out["run_span"] = (float(t[0]), float(t[-1])) if len(t) else (np.nan, np.nan)
    out["gt_span"] = (float(gt_t[0]), float(gt_t[-1]))
    inside = (t >= gt_t[0]) & (t <= gt_t[-1])
    out["inside"] = int(inside.sum())
    if inside.sum() < 20:
        return out
    t, p = t[inside], p[inside]
    g = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
    steps = np.linalg.norm(np.diff(p, axis=0), axis=1)
    out["est_path"], out["gt_path"] = path_len(p), path_len(g)
    out["max_step"], out["steps_gt3"] = (float(steps.max()) if len(steps) else 0.0), int((steps > 3.0).sum())
    fit = t <= t[0] + fit_seconds
    if fit.sum() < 20:
        fit = np.zeros(len(t), bool)
        fit[:max(20, len(t) // 10)] = True
    R, tr = vt.umeyama(p[fit], g[fit])
    e = np.linalg.norm(p @ R.T + tr - g, axis=1)
    rows = []
    t0 = t[0]
    k = 0
    while t0 + k * window <= t[-1]:
        m = (t >= t0 + k * window) & (t < t0 + (k + 1) * window)
        if m.sum() > 1:
            rows.append((k * window, int(m.sum()), path_len(p[m]), path_len(g[m]), float(e[m].mean()), float(e[m].max())))
        k += 1
    out["rows"] = rows
    out["first_gt5"] = float(t[np.argmax(e > 5.0)] - t0) if (e > 5.0).any() else None
    out["first_gt20"] = float(t[np.argmax(e > 20.0)] - t0) if (e > 20.0).any() else None
    out["fit_ate"] = (float(np.sqrt((e[fit] ** 2).mean())), float(e[fit].max()))
    full = vt.ate(t, p, gt_t, gt_p)
    out["full_ate"] = full
    best = (0.0, full[0], full[1])
    for s in (shifts if shifts is not None else np.arange(-20.0, 20.01, 0.5)):
        r = vt.ate(t + s, p, gt_t, gt_p)
        if np.isfinite(r[0]) and r[0] < best[1]:
            best = (float(s), r[0], r[1])
    out["best_shift"] = best
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--est", required=True)
    ap.add_argument("--window", type=float, default=30.0)
    ap.add_argument("--fit-seconds", type=float, default=60.0)
    a = ap.parse_args()
    gt_t, gt_p = vt.load_gt(a.gt)
    E = np.loadtxt(a.est, ndmin=2)
    r = analyse(gt_t, gt_p, E[:, 0], E[:, 1:4], a.window, a.fit_seconds)
    print("poses %d, inside the ground-truth span %d" % (r["n"], r["inside"]))
    print("run stamps %.1f..%.1f   ground truth %.1f..%.1f" % (*r["run_span"], *r["gt_span"]))
    if "rows" not in r:
        print("too few poses inside the ground-truth span: the stamps of the run and of the ground truth do not overlap (clock or file problem)")
        return 0
    print("estimated path %.1f m, ground-truth path %.1f m over the same span; largest step %.2f m; steps above 3 m: %d" % (
        r["est_path"], r["gt_path"], r["max_step"], r["steps_gt3"]))
    print("alignment fitted on the first %.0f s (fit error rmse %.2f, max %.2f):" % (a.fit_seconds, *r["fit_ate"]))
    print("%8s %6s %10s %10s %10s %10s" % ("t_rel_s", "poses", "est_path", "gt_path", "err_mean", "err_max"))
    for row in r["rows"]:
        print("%8.0f %6d %10.1f %10.1f %10.2f %10.2f" % row)
    print("error first above 5 m at t_rel = %s s, above 20 m at %s s" % (
        "never" if r["first_gt5"] is None else "%.0f" % r["first_gt5"], "never" if r["first_gt20"] is None else "%.0f" % r["first_gt20"]))
    print("full-span score (same as score_tum): RMSE %.2f  max %.2f" % r["full_ate"])
    s, rm, mx = r["best_shift"]
    print("time-shift check: best shift %+.1f s gives RMSE %.2f, max %.2f (shift 0 gives %.2f)" % (s, rm, mx, r["full_ate"][0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
