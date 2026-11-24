#!/usr/bin/env python3
"""Offline tests of diag_error_time.py: python3 stock_liosam/test_diag_error_time.py (from fusion_v4/)."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import diag_error_time as dg  # noqa: E402


def gt_line(n=600, dt=0.1):
    t = 1000.0 + np.arange(n) * dt
    s = np.arange(n) * 0.1
    return t, np.stack([s, 2.0 * np.sin(s / 7.0), np.zeros(n)], 1)


class Diag(unittest.TestCase):
    def test_good_run_has_small_error_and_equal_paths(self):
        gt_t, gt_p = gt_line()
        r = dg.analyse(gt_t, gt_p, gt_t, gt_p + 0.01 * np.random.RandomState(0).randn(*gt_p.shape))
        self.assertLess(r["full_ate"][0], 0.05)
        self.assertAlmostEqual(r["est_path"] / r["gt_path"], 1.0, delta=0.1)
        self.assertIsNone(r["first_gt5"])
        self.assertEqual(r["best_shift"][0], 0.0)

    def test_runaway_is_located_in_time(self):
        gt_t, gt_p = gt_line()
        p = gt_p.copy()
        p[300:, 0] += np.cumsum(np.full(300, 0.5))              # the estimate runs away from t_rel = 30 s
        r = dg.analyse(gt_t, gt_p, gt_t, p, window=10.0, fit_seconds=20.0)
        self.assertTrue(25.0 <= r["first_gt5"] <= 45.0, r["first_gt5"])
        self.assertGreater(r["est_path"], 2 * r["gt_path"])
        self.assertGreater(r["rows"][-1][4], 20.0)

    def test_clock_offset_is_found_by_the_shift_check(self):
        gt_t, gt_p = gt_line()
        r = dg.analyse(gt_t, gt_p, gt_t + 3.0, gt_p)             # the run's stamps are 3 s late
        self.assertGreater(r["full_ate"][0], 0.2)
        self.assertAlmostEqual(r["best_shift"][0], -3.0, places=3)
        self.assertLess(r["best_shift"][1], 0.05)

    def test_no_overlap_is_reported_not_crashed(self):
        gt_t, gt_p = gt_line()
        r = dg.analyse(gt_t, gt_p, gt_t + 1.0e5, gt_p)
        self.assertEqual(r["inside"], 0)
        self.assertNotIn("rows", r)

    def test_nan_poses_are_ignored(self):
        gt_t, gt_p = gt_line()
        p = gt_p.copy()
        p[10, 0] = np.nan
        r = dg.analyse(gt_t, gt_p, gt_t, p)
        self.assertEqual(r["n"], len(gt_t) - 1)


if __name__ == "__main__":
    unittest.main()
