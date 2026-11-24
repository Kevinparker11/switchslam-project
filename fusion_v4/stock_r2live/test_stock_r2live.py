#!/usr/bin/env python3
"""Offline tests of the stock R2LIVE helpers (no ROS, no bags): python3 test_stock_r2live.py  (from fusion_v4/stock_r2live/).
Set R2LIVE_UPSTREAM=<clone of hku-mars/r2live at the pinned commit> to also check the patches against the real source."""
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
import r2_params as rp  # noqa: E402
import vel_to_r2live as vr  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LIO = os.path.join(HERE, "test_data", "upstream_lio_config.yaml")     # config/lio_config.yaml of the pinned commit
CAM = os.path.join(HERE, "test_data", "upstream_cam_config.yaml")     # config/filr_cam.yaml of the pinned commit
UPSTREAM_SRC = os.environ.get("R2LIVE_UPSTREAM", "/tmp/r2_up")
COMMIT = "e719ca266ab53ca8915ca4e1416152993f2a55d7"


def load_cam_yaml(text):
    return yaml.safe_load(text.replace("%YAML:1.0", "").replace("!!opencv-matrix", ""))


class Params(unittest.TestCase):
    def setUp(self):
        with open(LIO) as f:
            self.lio = f.read()
        with open(CAM) as f:
            self.cam = f.read()

    def make(self, cam_cfg, extr, imu="/imu/data"):
        from make_params import load_laser_to_imu
        R_il, t_il = load_laser_to_imu(extr)
        cfg, R_ic, t_ic = mm.load_vins_camera_config(cam_cfg)
        lio, ch1 = rp.make_lio(self.lio, t_il)
        cam, ch2 = rp.make_cam(self.cam, cfg, R_ic, t_ic, imu)
        return lio, cam, cfg, R_ic, t_ic, t_il, ch1 + ch2

    def test_lio_changes_only_two_keys_and_adds_the_offset(self):
        lio, cam, cfg, R_ic, t_ic, t_il, ch = self.make(os.path.join(REPO, "configs", "corridor", "corridor_config.yaml"),
                                                        os.path.join(REPO, "configs", "corridor", "corridor_extrinsics.yaml"))
        d, b = yaml.safe_load(lio), yaml.safe_load(self.lio)
        changed = {k for sec in b for k in b[sec] if d[sec][k] != b[sec][k]}
        self.assertEqual(changed, {"lidar_type", "N_SCANS"})
        self.assertEqual((d["feature_extraction"]["lidar_type"], d["feature_extraction"]["N_SCANS"]), (3, 1))
        self.assertEqual(set(d) - set(b), {"r2live_lio"})
        np.testing.assert_allclose(d["r2live_lio"]["lidar_offset_to_imu"], t_il, atol=1e-8)
        self.assertEqual(d["feature_extraction"]["using_raw_point"], 1)          # untouched upstream settings
        self.assertEqual(d["fast_lio"]["max_iteration"], 4)

    def test_cam_mei_block_and_extrinsics(self):
        lio, cam, cfg, R_ic, t_ic, t_il, ch = self.make(os.path.join(REPO, "configs", "corridor2", "corridor2_config.yaml"),
                                                        os.path.join(REPO, "configs", "corridor2", "corridor2_extrinsics.yaml"))
        d = load_cam_yaml(cam)
        self.assertEqual(d["model_type"], "MEI")
        self.assertEqual(d["imu_topic"], "/imu/data")
        self.assertEqual((d["image_width"], d["image_height"]), (int(cfg["image_width"]), int(cfg["image_height"])))
        self.assertAlmostEqual(d["mirror_parameters"]["xi"], cfg["mirror_parameters"]["xi"], places=8)
        for k in ("gamma1", "gamma2", "u0", "v0"):
            self.assertAlmostEqual(d["projection_parameters"][k], cfg["projection_parameters"][k], places=6)
        for k in ("k1", "k2", "p1", "p2"):
            self.assertAlmostEqual(d["distortion_parameters"][k], cfg["distortion_parameters"][k], places=8)
        np.testing.assert_allclose(np.array(d["extrinsicRotation"]["data"]).reshape(3, 3), R_ic, atol=1e-8)
        np.testing.assert_allclose(d["extrinsicTranslation"]["data"], t_ic, atol=1e-8)

    def test_cam_only_documented_things_change(self):
        lio, cam, *_ = self.make(os.path.join(REPO, "configs", "corridor2", "corridor2_config.yaml"),
                                 os.path.join(REPO, "configs", "corridor2", "corridor2_extrinsics.yaml"))
        d, b = load_cam_yaml(cam), load_cam_yaml(self.cam)
        changed = {k for k in b if d.get(k) != b[k]}
        self.assertLessEqual(changed, {"imu_topic", "model_type", "image_width", "image_height", "distortion_parameters", "projection_parameters",
                                       "extrinsicRotation", "extrinsicTranslation"})
        self.assertTrue({"imu_topic", "model_type", "projection_parameters", "extrinsicRotation", "extrinsicTranslation"} <= changed)
        self.assertEqual(set(d) - set(b), {"mirror_parameters"})
        for k in ("estimate_extrinsic", "estimate_td", "max_cnt", "acc_n", "gyr_n", "fisheye", "loop_closure"):
            self.assertEqual(d[k], b[k])

    def test_geode_pinhole(self):
        p = os.path.join(REPO, "fusion_v4", "geode", "geode_config.yaml")
        e = os.path.join(REPO, "fusion_v4", "geode", "geode_extrinsics.yaml")
        if not (os.path.exists(p) and os.path.exists(e)):
            self.skipTest("geode config not in the repo")
        lio, cam, cfg, *_ = self.make(p, e, imu="/imu/data")
        d = load_cam_yaml(cam)
        self.assertEqual(d["model_type"], "PINHOLE")
        self.assertNotIn("mirror_parameters", d)
        for k in ("fx", "fy", "cx", "cy"):
            self.assertAlmostEqual(d["projection_parameters"][k], cfg["projection_parameters"][k], places=6)

    def test_unknown_model_is_an_error(self):
        with self.assertRaises(ValueError):
            rp.camera_block({"model_type": "KANNALA_BRANDT", "image_width": 1, "image_height": 1, "distortion_parameters": {}, "projection_parameters": {}})

    def test_every_sequence_config_writes(self):
        for c in ("corridor", "corridor2", "cave02", "multifloor"):
            cam = os.path.join(REPO, "configs", c, c + "_config.yaml")
            ex = os.path.join(REPO, "configs", c, c + "_extrinsics.yaml")
            if os.path.exists(cam) and os.path.exists(ex):
                lio, camt, *_ = self.make(cam, ex)
                yaml.safe_load(lio)
                load_cam_yaml(camt)

    def test_main_writes_both_files(self):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([sys.executable, os.path.join(HERE, "r2_params.py"), "--lio-base", LIO, "--cam-base", CAM, "--extrinsics",
                                os.path.join(REPO, "configs", "corridor2", "corridor2_extrinsics.yaml"), "--camera-config",
                                os.path.join(REPO, "configs", "corridor2", "corridor2_config.yaml"), "--imu-topic", "/imu/data", "--out-dir", t],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(os.path.join(t, "lio_config.yaml")) and os.path.exists(os.path.join(t, "cam_config.yaml")))
            for k in ("lidar_type", "N_SCANS", "lidar_offset_to_imu", "extrinsicRotation", "deg from identity"):
                self.assertIn(k, r.stdout)


class VelToR2live(unittest.TestCase):
    def cloud(self):
        dt = np.dtype({"names": ["x", "y", "z", "intensity", "ring", "time"], "formats": ["<f4", "<f4", "<f4", "<f4", "<u2", "<f4"],
                       "offsets": [0, 4, 8, 16, 20, 24], "itemsize": 32})
        a = np.zeros(5, dtype=dt)
        a["x"] = [1.0, 2.0, 3.0, 4.0, 5.0]
        a["y"] = -2.0
        a["z"] = 0.5
        a["intensity"] = [10, 20, 30, 40, 50]
        a["time"] = [0.05, 0.0, 0.099, 0.02, 0.07]               # not in time order
        fields = [("x", 0, 7, 1), ("y", 4, 7, 1), ("z", 8, 7, 1), ("intensity", 16, 7, 1), ("ring", 20, 4, 1), ("time", 24, 7, 1)]
        return fields, 32, a.tobytes(), a

    def test_layout(self):
        self.assertEqual(vr.OUT_DTYPE.itemsize, 20)
        self.assertEqual([(k, o) for k, o in vr.OUT_FIELDS], [("x", 0), ("y", 4), ("z", 8), ("intensity", 12), ("curvature", 16)])

    def test_curvature_is_time_in_ms_and_last_point_is_the_latest(self):
        f, ps, data, a = self.cloud()
        out, n, neg = vr.convert(f, ps, data)
        o = np.frombuffer(out, dtype=vr.OUT_DTYPE)
        self.assertEqual((n, neg), (5, 0))
        self.assertTrue(np.all(np.diff(o["curvature"]) >= 0))
        self.assertAlmostEqual(float(o["curvature"][-1]), 99.0, places=3)        # 0.099 s -> 99 ms, read as the scan duration
        self.assertEqual(float(o["curvature"][0]), 0.0)

    def test_points_are_only_permuted(self):
        f, ps, data, a = self.cloud()
        out, n, _ = vr.convert(f, ps, data)
        o = np.frombuffer(out, dtype=vr.OUT_DTYPE)
        got = sorted(zip(o["x"], o["y"], o["z"], o["intensity"]))
        want = sorted(zip(a["x"], a["y"], a["z"], a["intensity"]))
        self.assertEqual(got, want)                                               # nothing changed, nothing dropped
        i = int(np.argmax(o["curvature"]))
        self.assertEqual(float(o["x"][i]), 3.0)                                   # the point with time 0.099 carries its own coordinates

    def test_negative_time_clipped_and_missing_time_is_an_error(self):
        f, ps, data, a = self.cloud()
        a["time"][1] = -0.01
        out, n, neg = vr.convert(f, ps, a.tobytes())
        self.assertEqual(neg, 1)
        with self.assertRaises(ValueError):
            vr.convert([x for x in f if x[0] != "time"], ps, data)


class Build(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "Dockerfile")) as f:
            self.df = f.read()

    def test_pins_labels_portable(self):
        self.assertIn("FROM ros@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d", self.df)
        self.assertIn("ARG R2LIVE_COMMIT=" + COMMIT, self.df)
        self.assertIn("ARG LIVOX_DRIVER_COMMIT=3d240d5666129e1a3052e78ee8487a04b08fdda3", self.df)
        self.assertIn('baseline.method="r2live"', self.df)
        self.assertIn('baseline.upstream_commit="%s"' % COMMIT, self.df)
        code = "\n".join(l for l in self.df.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("march=native", code)
        self.assertIn("libceres-dev", code)
        self.assertLess(code.index("r2live_noetic_build.patch && git apply /tmp/r2live_rig.patch") if "r2live_noetic_build.patch && git apply" in code else 0, len(code))

    def test_first_three_apt_steps_equal_those_of_r3live(self):
        # identical text means a Docker layer cache hit on the desktop and layers shared with the R3LIVE image on the laptop
        pat = r"(RUN apt-get update.*?rm -rf /var/lib/apt/lists/\*\n)"
        mine = re.findall(pat, self.df, re.S)[:3]
        with open(os.path.join(HERE, "..", "stock_r3live", "Dockerfile")) as f:
            theirs = re.findall(pat, f.read(), re.S)[:3]
        self.assertEqual(len(mine), 3)
        self.assertEqual(mine, theirs)

    def test_every_script_the_runner_and_container_call_exists(self):
        fusion = os.path.abspath(os.path.join(HERE, ".."))
        dirs = {"$S": "stock_r2live", "$L": "stock_liosam", "$B": "baselines"}
        missing = []
        for f in ("run_r2live.sh", "inside.sh"):
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
        for needle in ('pkg="feature_tracker" type="feature_tracker"', 'pkg="r2live" type="lio_feat_extract"', 'pkg="r2live" type="r2live"',
                       'name="lidar_drag_cam_tim" type="int" value="10"', 'name="if_lidar_start_first" type="int" value="1"',
                       '<remap from="/livox/imu"', "/os1_cloud_node/points"):
            self.assertIn(needle, s)
        self.assertNotIn("-march", s)

    @unittest.skipUnless(os.path.isdir(os.path.join(UPSTREAM_SRC, "r2live")), "no upstream clone")
    def test_patches_apply_to_the_pinned_source_in_order(self):
        r = subprocess.run(["git", "-C", UPSTREAM_SRC, "rev-parse", "HEAD"], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), COMMIT)
        with tempfile.TemporaryDirectory() as t:
            subprocess.run(["git", "clone", "-q", UPSTREAM_SRC, t], check=True)
            for p in ("r2live_noetic_build.patch", "r2live_rig.patch"):
                r = subprocess.run(["git", "-C", t, "apply", os.path.join(HERE, p)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, p + ": " + r.stderr)
        with open(os.path.join(HERE, "r2live_rig.patch")) as f:
            p = f.read()
        self.assertEqual(len(re.findall(r"^\+Eigen::Vector3d Lidar_offset_to_IMU\(0\.04165, 0\.02326, -0\.0284\);", p, re.M)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
