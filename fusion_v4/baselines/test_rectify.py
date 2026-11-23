#!/usr/bin/env python3
"""Offline tests of mei_model.py: python3 test_rectify.py  (from fusion_v4/baselines/)."""
import os
import unittest

import numpy as np

import mei_model as mm

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CFG = {"image_width": 640, "image_height": 480, "model_type": "MEI", "mirror_parameters": {"xi": 1.5},
       "distortion_parameters": {"k1": -0.07, "k2": 0.24, "p1": 0.002, "p2": 0.001},
       "projection_parameters": {"gamma1": 740.0, "gamma2": 660.0, "u0": 319.6, "v0": 235.2}}


class Mei(unittest.TestCase):
    def test_known_value(self):
        # xi = 1, no distortion, P = (1, 0, 1): z = 1 + sqrt(2), m = 1 / z
        u = mm.project_mei([[1.0, 0.0, 1.0]], 1.0, 0, 0, 0, 0, 500.0, 500.0, 320.0, 240.0)[0]
        np.testing.assert_allclose(u, [500.0 / (1 + np.sqrt(2)) + 320.0, 240.0], atol=1e-9)

    def test_optical_axis_hits_principal_point(self):
        u = mm.project_mei([[0.0, 0.0, 3.0]], **mm.mei_params(CFG))[0]
        np.testing.assert_allclose(u, [319.6, 235.2], atol=1e-9)

    def test_xi_zero_no_distortion_is_a_pinhole(self):
        c = dict(CFG, mirror_parameters={"xi": 0.0}, distortion_parameters={"k1": 0, "k2": 0, "p1": 0, "p2": 0})
        P = np.array([[0.3, -0.2, 2.0], [-1.0, 0.5, 4.0]])
        u = mm.project_mei(P, **mm.mei_params(c))
        np.testing.assert_allclose(u[:, 0], 740.0 * P[:, 0] / P[:, 2] + 319.6, atol=1e-9)
        np.testing.assert_allclose(u[:, 1], 660.0 * P[:, 1] / P[:, 2] + 235.2, atol=1e-9)

    def test_rectified_pixel_looks_where_the_ray_looks(self):
        w, h, f, cx, cy = mm.rectified_pinhole(CFG)
        mx, my = mm.rectify_maps(CFG)
        self.assertEqual(mx.shape, (480, 640))
        for (u, v) in [(10, 20), (320, 240), (600, 400), (100, 450)]:
            ray = np.array([[(u - cx) / f, (v - cy) / f, 1.0]])
            want = mm.project_mei(ray * 7.0, **mm.mei_params(CFG))[0]          # any depth on the ray gives the same pixel
            np.testing.assert_allclose([mx[v, u], my[v, u]], want, atol=1e-3)
        # the centre of the rectified image samples the principal point
        self.assertAlmostEqual(float(mx[int(round(cy)), int(round(cx))]), 319.6, delta=0.6)

    def test_central_scale_is_kept(self):
        # one pixel step in the rectified image moves the sampled pixel by gamma1 / mean(gamma) at the centre (1.0 when gamma1 = gamma2)
        w, h, f, cx, cy = mm.rectified_pinhole(CFG)
        mx, _ = mm.rectify_maps(CFG)
        c = int(round(cx))
        self.assertAlmostEqual(float(mx[240, c + 1] - mx[240, c]), 740.0 / 700.0, delta=0.01)

    def test_real_configs_cover_the_image(self):
        for cfgp in ("configs/corridor/corridor_config.yaml", "configs/corridor2/corridor2_config.yaml", "configs/cave02/cave02_config.yaml",
                     "configs/multifloor/multifloor_config.yaml"):
            p = os.path.join(REPO, cfgp)
            if not os.path.exists(p):
                self.skipTest("repo configs not present")
            cfg, R, t = mm.load_vins_camera_config(p)
            mx, my = mm.rectify_maps(cfg)
            w, h = cfg["image_width"], cfg["image_height"]
            inside = (mx >= 0) & (mx <= w - 1) & (my >= 0) & (my <= h - 1)
            self.assertGreater(inside.mean(), 0.97, cfgp)                      # almost every output pixel has a source pixel
            self.assertTrue(np.isfinite(mx).all() and np.isfinite(my).all())
            self.assertAlmostEqual(np.linalg.det(R), 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
