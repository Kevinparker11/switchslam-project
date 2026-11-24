#!/usr/bin/env python3
"""Offline tests of the stock R3LIVE helpers (no ROS, no bags): python3 test_stock_r3live.py  (from fusion_v4/stock_r3live/)."""
import os
import re
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "baselines"))
sys.path.insert(0, os.path.join(HERE, "..", "stock_liosam"))
import mei_model as mm  # noqa: E402
import r3_params as rp  # noqa: E402
import record_tf  # noqa: E402
import vel_to_ouster as vo  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = os.path.join(HERE, "test_data", "upstream_r3live_config.yaml")   # config/r3live_config.yaml of the pinned commit
UPSTREAM_SRC = os.environ.get("R3LIVE_UPSTREAM", "/tmp/r3_up")           # optional: clone at the pinned commit, for the patch test


def active_lines(text):
    return [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]


class Params(unittest.TestCase):
    def setUp(self):
        with open(BASE) as f:
            self.base = f.read()
        self.ext = os.path.join(REPO, "fusion_v4", "stock_liosam", "seq")

    def make(self, cam_cfg, extr):
        from make_params import load_laser_to_imu
        R_il, t_il = load_laser_to_imu(extr)
        cfg, R_ic, t_ic = mm.load_vins_camera_config(cam_cfg)
        return rp.make(self.base, R_il, t_il, cfg, R_ic, t_ic), cfg, (R_ic, t_ic, t_il)

    def test_only_documented_keys_change(self):
        (out, ch, note), cfg, _ = self.make(os.path.join(REPO, "configs", "corridor2", "corridor2_config.yaml"),
                                            os.path.join(REPO, "configs", "corridor2", "corridor2_extrinsics.yaml"))
        d = yaml.safe_load(out)
        b = yaml.safe_load(self.base)
        changed = set()
        for sec in b:
            for k in b[sec]:
                if d[sec][k] != b[sec][k]:
                    changed.add(k)
        new = {k for sec in d for k in d[sec] if k not in b.get(sec, {})}
        self.assertEqual(changed, {"lidar_type", "record_offline_map", "image_width", "image_height", "camera_intrinsic",
                                   "camera_dist_coeffs", "camera_ext_R", "camera_ext_t"})
        self.assertEqual(new, {"lidar_offset_to_imu"})
        # everything not named stays, in particular the online estimation switches and the tracked points
        for k, v in (("estimate_i2c_extrinsic", 1), ("estimate_intrinsic", 1), ("maximum_vio_tracked_pts", 600)):
            self.assertEqual(d["r3live_common"][k], v)
        self.assertEqual(d["Lidar_front_end"]["lidar_type"], 3)
        self.assertEqual(d["r3live_common"]["record_offline_map"], 0)

    def test_values_follow_the_inputs(self):
        (out, ch, note), cfg, (R_ic, t_ic, t_il) = self.make(os.path.join(REPO, "configs", "corridor2", "corridor2_config.yaml"),
                                                             os.path.join(REPO, "configs", "corridor2", "corridor2_extrinsics.yaml"))
        d = yaml.safe_load(out)
        np.testing.assert_allclose(np.array(d["r3live_vio"]["camera_ext_R"]).reshape(3, 3), R_ic, atol=1e-8)
        np.testing.assert_allclose(d["r3live_vio"]["camera_ext_t"], t_ic, atol=1e-8)
        np.testing.assert_allclose(d["r3live_lio"]["lidar_offset_to_imu"], t_il, atol=1e-8)
        w, h, f, cx, cy = mm.rectified_pinhole(cfg)
        self.assertEqual((d["r3live_vio"]["image_width"], d["r3live_vio"]["image_height"]), (w, h))
        np.testing.assert_allclose(d["r3live_vio"]["camera_intrinsic"], [f, 0, cx, 0, f, cy, 0, 0, 1], atol=1e-6)
        self.assertEqual(d["r3live_vio"]["camera_dist_coeffs"], [0, 0, 0, 0, 0])      # rectified image has no distortion
        self.assertIn("rectified", note)

    def test_geode_pinhole_keeps_its_own_intrinsics(self):
        p = os.path.join(REPO, "fusion_v4", "geode", "geode_config.yaml")
        e = os.path.join(REPO, "fusion_v4", "geode", "geode_extrinsics.yaml")
        if not (os.path.exists(p) and os.path.exists(e)):
            self.skipTest("geode config not in the repo")
        (out, ch, note), cfg, _ = self.make(p, e)
        d = yaml.safe_load(out)
        pp, dd = cfg["projection_parameters"], cfg["distortion_parameters"]
        np.testing.assert_allclose(d["r3live_vio"]["camera_intrinsic"], [pp["fx"], 0, pp["cx"], 0, pp["fy"], pp["cy"], 0, 0, 1], atol=1e-6)
        np.testing.assert_allclose(d["r3live_vio"]["camera_dist_coeffs"], [dd["k1"], dd["k2"], dd["p1"], dd["p2"], 0.0], atol=1e-9)
        self.assertEqual(d["r3live_vio"]["image_width"], int(cfg["image_width"]))

    def test_unknown_camera_model_is_an_error(self):
        with self.assertRaises(ValueError):
            rp.camera_for({"model_type": "KANNALA_BRANDT"})

    def test_missing_key_is_an_error(self):
        with self.assertRaises(ValueError):
            rp._sub("a: 1\n", "lidar_type", "3", [])

    def test_every_sequence_config_writes(self):
        for c in ("corridor", "corridor2", "cave02", "multifloor"):
            cam = os.path.join(REPO, "configs", c, c + "_config.yaml")
            ex = os.path.join(REPO, "configs", c, c + "_extrinsics.yaml")
            if not (os.path.exists(cam) and os.path.exists(ex)):
                continue
            (out, ch, note), _, _ = self.make(cam, ex)
            yaml.safe_load(out)
            self.assertEqual(len([l for l in active_lines(out) if l.startswith("lidar_offset_to_imu")]), 1)

    def test_main_prints_every_change(self):
        with tempfile.TemporaryDirectory() as t:
            o = os.path.join(t, "o.yaml")
            r = subprocess.run([sys.executable, os.path.join(HERE, "r3_params.py"), "--base", BASE, "--extrinsics",
                                os.path.join(REPO, "configs", "corridor2", "corridor2_extrinsics.yaml"), "--camera-config",
                                os.path.join(REPO, "configs", "corridor2", "corridor2_config.yaml"), "--out", o], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            for k in ("lidar_type", "record_offline_map", "camera_intrinsic", "camera_ext_R", "lidar_offset_to_imu"):
                self.assertIn(k, r.stdout)
            self.assertIn("deg from identity", r.stdout)


class VelToOuster(unittest.TestCase):
    def cloud(self, n=5):
        dt = np.dtype({"names": ["x", "y", "z", "intensity", "ring", "time"], "formats": ["<f4", "<f4", "<f4", "<f4", "<u2", "<f4"],
                       "offsets": [0, 4, 8, 16, 20, 24], "itemsize": 32})
        a = np.zeros(n, dtype=dt)
        a["x"] = np.arange(n) + 1.0
        a["y"] = -2.0
        a["z"] = 0.5
        a["intensity"] = [10.0, 20.4, 300.0, 0.0, 70000.0][:n]
        a["ring"] = np.arange(n)
        a["time"] = np.linspace(0, 0.099, n)
        fields = [("x", 0, 7, 1), ("y", 4, 7, 1), ("z", 8, 7, 1), ("intensity", 16, 7, 1), ("ring", 20, 4, 1), ("time", 24, 7, 1)]
        return fields, 32, a.tobytes(), a

    def test_layout_is_ousters(self):
        self.assertEqual(vo.OUT_DTYPE.itemsize, 32)
        offs = {n: vo.OUT_DTYPE.fields[n][1] for n in vo.OUT_DTYPE.names}
        self.assertEqual(offs, dict(x=0, y=4, z=8, intensity=12, t=16, reflectivity=20, ring=22, ambient=24, range=28))
        self.assertEqual([(n, o, d) for n, o, d in vo.OUT_FIELDS], [("x", 0, 7), ("y", 4, 7), ("z", 8, 7), ("intensity", 12, 7), ("t", 16, 6),
                                                                      ("reflectivity", 20, 4), ("ring", 22, 2), ("ambient", 24, 4), ("range", 28, 6)])

    def test_points_unchanged_and_fields_converted(self):
        f, ps, data, a = self.cloud()
        out, n, neg = vo.convert(f, ps, data)
        self.assertEqual((n, neg), (5, 0))
        o = np.frombuffer(out, dtype=vo.OUT_DTYPE)
        for k in ("x", "y", "z"):
            np.testing.assert_array_equal(o[k], a[k])                                   # no coordinate changed
        np.testing.assert_allclose(o["t"], np.rint(a["time"].astype(np.float64) * 1e9), atol=1)
        self.assertEqual(int(o["t"][-1]), int(round(float(a["time"][-1]) * 1e9)))
        np.testing.assert_array_equal(o["ring"], np.arange(5))
        np.testing.assert_allclose(o["range"], np.rint(np.sqrt(a["x"].astype(np.float64) ** 2 + 4 + 0.25) * 1000), atol=1)
        self.assertEqual(int(o["reflectivity"][4]), 65535)                              # clipped, not wrapped
        self.assertEqual(int(o["ambient"][0]), 0)

    def test_negative_time_is_clipped_and_counted(self):
        f, ps, data, a = self.cloud()
        a["time"][0] = -0.01
        out, n, neg = vo.convert(f, ps, a.tobytes())
        self.assertEqual(neg, 1)
        self.assertEqual(int(np.frombuffer(out, dtype=vo.OUT_DTYPE)["t"][0]), 0)

    def test_missing_time_is_an_error_missing_ring_is_not(self):
        f, ps, data, a = self.cloud()
        with self.assertRaises(ValueError):
            vo.convert([x for x in f if x[0] != "time"], ps, data)
        out, n, _ = vo.convert([x for x in f if x[0] != "ring"], ps, data)
        self.assertEqual(n, 5)


class Recorder(unittest.TestCase):
    class T:
        def __init__(self, t, child, x):
            self.header = type("H", (), {"stamp": type("S", (), {"to_sec": lambda s: t})()})()
            self.child_frame_id = child
            self.transform = type("X", (), {"translation": type("P", (), {"x": x, "y": 0.0, "z": 0.0})(),
                                            "rotation": type("Q", (), {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})()})()

    def test_only_aft_mapped_is_kept_with_or_without_slash(self):
        rows = record_tf.tf_rows([self.T(1.5, "/aft_mapped", 1.0), self.T(1.6, "camera", 9.0), self.T(1.7, "aft_mapped", 2.0)])
        self.assertEqual(rows, ["1.500000 1.000000 0.000000 0.000000 0.00000000 0.00000000 0.00000000 1.00000000",
                                "1.700000 2.000000 0.000000 0.000000 0.00000000 0.00000000 0.00000000 1.00000000"])


class Build(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "Dockerfile")) as f:
            self.df = f.read()

    def test_pins_and_labels(self):
        self.assertIn("FROM ros@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d", self.df)
        self.assertIn("ARG R3LIVE_COMMIT=6143a38537f28cb36eb24e9bbe2e39c8f7967157", self.df)
        self.assertIn("ARG LIVOX_DRIVER_COMMIT=3d240d5666129e1a3052e78ee8487a04b08fdda3", self.df)
        self.assertIn('baseline.method="r3live"', self.df)
        self.assertIn('baseline.upstream_commit="6143a38537f28cb36eb24e9bbe2e39c8f7967157"', self.df)

    def test_portable_and_headless(self):
        code = "\n".join(l for l in self.df.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("march=native", code)
        self.assertIn("xvfb", code)
        self.assertIn("libcgal-dev", code)
        self.assertNotIn("r3live_meshing", code.replace("make-args r3live_LiDAR_front_end r3live_mapping", ""))

    def test_every_script_the_runner_and_container_call_exists(self):
        fusion = os.path.abspath(os.path.join(HERE, ".."))
        dirs = {"$S": "stock_r3live", "$L": "stock_liosam", "$B": "baselines"}
        missing = []
        for f in ("run_r3live.sh", "inside.sh"):
            with open(os.path.join(HERE, f)) as fh:
                txt = fh.read()
            for m in re.finditer(r"/repo/fusion_v4/([\w./-]+\.(?:py|sh))", txt):
                if not os.path.exists(os.path.join(fusion, m.group(1))):
                    missing.append((f, m.group(1)))
            for m in re.finditer(r"(\$[SLB])/([\w.-]+\.(?:py|sh))", txt):
                if not os.path.exists(os.path.join(fusion, dirs[m.group(1)], m.group(2))):
                    missing.append((f, dirs[m.group(1)] + "/" + m.group(2)))
        self.assertEqual(missing, [])

    def test_launch_in_inside_sh_is_upstreams(self):
        with open(os.path.join(HERE, "inside.sh")) as f:
            s = f.read()
        for needle in ('r3live_LiDAR_front_end" name="r3live_LiDAR_front_end"', 'type="r3live_mapping" name="r3live_mapping"',
                       'required="true"', "/laser_cloud_flat", "Xvfb :99", "/os_cloud_node/points"):
            self.assertIn(needle, s)
        self.assertNotIn("-march", s)
        self.assertIn("vio_pnp_errors.txt", s)

    def test_dockerfile_applies_both_patches_in_order(self):
        a = self.df.index("git apply /tmp/r3live_noetic_build.patch")
        b = self.df.index("git apply /tmp/r3live_rig.patch")
        self.assertLess(a, b)
        self.assertIn("r3live_noetic_build.patch r3live_rig.patch /tmp/", self.df)

    @unittest.skipUnless(os.path.isdir(os.path.join(UPSTREAM_SRC, "r3live")), "no upstream clone")
    def test_patch_applies_to_the_pinned_source(self):
        r = subprocess.run(["git", "-C", UPSTREAM_SRC, "apply", "--check", os.path.join(HERE, "r3live_noetic_build.patch")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run(["git", "-C", UPSTREAM_SRC, "apply", "--check", os.path.join(HERE, "r3live_rig.patch")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run(["git", "-C", UPSTREAM_SRC, "rev-parse", "HEAD"], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "6143a38537f28cb36eb24e9bbe2e39c8f7967157")
        with open(os.path.join(HERE, "r3live_rig.patch")) as f:
            p = f.read()
        self.assertIn("0.04165, 0.02326, -0.0284", p)                 # the upstream default stays the default
        self.assertEqual(len(re.findall(r"^\+Eigen::Vector3d Lidar_offset_to_IMU\(0\.04165, 0\.02326, -0\.0284\);", p, re.M)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
