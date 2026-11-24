#!/usr/bin/env python3
"""Offline tests of the stock FAST-LIVO helpers (no ROS, no bags): python3 test_stock_fastlivo.py  (from fusion_v4/stock_fastlivo/).
Set FASTLIVO_UPSTREAM, VIKIT_UPSTREAM, SOPHUS_UPSTREAM to clones at the pinned commits to also check the patches against the real source."""
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
import fl_params as fp  # noqa: E402
import mei_model as mm  # noqa: E402
from make_params import load_laser_to_imu  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MAIN = os.path.join(HERE, "test_data", "upstream_main_config.yaml")       # config/NTU_VIRAL.yaml of the pinned commit
CAM = os.path.join(HERE, "test_data", "upstream_camera_config.yaml")      # config/camera_NTU_VIRAL.yaml of the pinned commit
PINS = {"FASTLIVO": ("FASTLIVO_UPSTREAM", "/tmp/fl_up", "f7e1af5b10c89ba38c5e2c5e4d458195c58eba6b"),
        "VIKIT": ("VIKIT_UPSTREAM", "/tmp/vikit_up", "10871da6d84c8324212053c40f468c6ab4862ee0"),
        "SOPHUS": ("SOPHUS_UPSTREAM", "/tmp/sophus_up", "a621ff2e56c56c839a6c40418d42c3c254424b5c")}


def cfgs(c):
    return (os.path.join(REPO, "configs", c, c + "_config.yaml"), os.path.join(REPO, "configs", c, c + "_extrinsics.yaml"))


class Params(unittest.TestCase):
    def setUp(self):
        with open(MAIN) as f:
            self.main = f.read()
        with open(CAM) as f:
            self.cam = f.read()

    def make(self, c):
        cam_cfg, extr = cfgs(c)
        R_il, t_il = load_laser_to_imu(extr)
        cfg, R_ic, t_ic = mm.load_vins_camera_config(cam_cfg)
        R_cl, t_cl = fp.camera_from_lidar(R_il, t_il, R_ic, t_ic)
        m, ch1 = fp.make_main(self.main, R_il, t_il, R_cl, t_cl, "/os_cloud_node/points", "/imu/data", "/fastlivo_image")
        c2, ch2, note = fp.make_cam(self.cam, cfg)
        return m, c2, cfg, (R_il, t_il, R_ic, t_ic, R_cl, t_cl), ch1 + ch2

    def test_main_changes_only_the_listed_keys(self):
        m, c2, cfg, ex, ch = self.make("corridor2")
        d, b = yaml.safe_load(m), yaml.safe_load(self.main)

        def flat(x, p=""):
            return {p + k + "." + kk if isinstance(v, dict) else p + k: vv for k, v in x.items() for kk, vv in (v.items() if isinstance(v, dict) else [("", v)])}
        fd, fb = flat(d), flat(b)
        changed = {k for k in fb if fd[k] != fb[k]}
        allowed = {"common.lid_topic", "common.imu_topic", "camera.img_topic", "mapping.extrinsic_T", "mapping.extrinsic_R", "camera.Rcl", "camera.Pcl"}
        self.assertLessEqual(changed, allowed)
        self.assertTrue({"common.lid_topic", "common.imu_topic", "camera.img_topic", "mapping.extrinsic_R", "camera.Rcl", "camera.Pcl"} <= changed)
        self.assertEqual(set(fd), set(fb))
        for k in ("point_filter_num", "max_iteration", "filter_size_surf", "img_point_cov", "laser_point_cov", "ncc_thre"):
            self.assertEqual(d[k], b[k])
        self.assertEqual((d["preprocess"]["lidar_type"], d["preprocess"]["scan_line"], d["preprocess"]["blind"]), (3, 16, 4))
        self.assertEqual((d["mapping"]["acc_cov_scale"], d["mapping"]["gyr_cov_scale"]), (100, 10000))

    def test_lidar_imu_extrinsics_are_written_as_they_are(self):
        m, c2, cfg, (R_il, t_il, R_ic, t_ic, R_cl, t_cl), ch = self.make("corridor2")
        d = yaml.safe_load(m)
        np.testing.assert_allclose(np.array(d["mapping"]["extrinsic_R"]).reshape(3, 3), R_il, atol=1e-8)
        np.testing.assert_allclose(d["mapping"]["extrinsic_T"], t_il, atol=1e-8)

    def test_camera_from_lidar_maps_a_point_the_same_way_as_the_chain(self):
        rng = np.random.RandomState(3)

        def rot():
            q, _ = np.linalg.qr(rng.randn(3, 3))
            return q * np.sign(np.linalg.det(q))
        R_il, R_ic = rot(), rot()
        t_il, t_ic, p_l = rng.randn(3), rng.randn(3), rng.randn(3)
        R_cl, t_cl = fp.camera_from_lidar(R_il, t_il, R_ic, t_ic)
        p_imu = R_il @ p_l + t_il
        p_cam = R_ic.T @ (p_imu - t_ic)                      # inverse of p_imu = R_ic p_cam + t_ic
        np.testing.assert_allclose(R_cl @ p_l + t_cl, p_cam, atol=1e-12)

    def test_convention_matches_how_upstream_uses_it(self):
        # lidar_selection.cpp: Rci = Rcl * Rli, Pci = Rcl * Pli + Pcl with Rli = R_il^T, Pli = -R_il^T t_il (set_extrinsic); the IMU point must map to the camera point
        m, c2, cfg, (R_il, t_il, R_ic, t_ic, R_cl, t_cl), ch = self.make("corridor2")
        Rli, Pli = R_il.T, -R_il.T @ t_il
        Rci, Pci = R_cl @ Rli, R_cl @ Pli + t_cl
        p_imu = np.array([0.3, -0.2, 0.5])
        np.testing.assert_allclose(Rci @ p_imu + Pci, R_ic.T @ (p_imu - t_ic), atol=1e-10)

    def test_camera_mei_becomes_rectified_pinhole(self):
        m, c2, cfg, ex, ch = self.make("corridor2")
        d = yaml.safe_load(c2)
        w, h, f, cx, cy = mm.rectified_pinhole(cfg)
        self.assertEqual((d["cam_width"], d["cam_height"], d["cam_model"]), (w, h, "Pinhole"))
        self.assertAlmostEqual(d["cam_fx"], f, places=6)
        self.assertAlmostEqual(d["cam_fy"], f, places=6)
        self.assertAlmostEqual(d["cam_cx"], cx, places=6)
        self.assertEqual([d["cam_d%d" % i] for i in range(4)], [0, 0, 0, 0])

    def test_geode_pinhole_as_it_is(self):
        p, e = os.path.join(REPO, "fusion_v4", "geode", "geode_config.yaml"), os.path.join(REPO, "fusion_v4", "geode", "geode_extrinsics.yaml")
        if not (os.path.exists(p) and os.path.exists(e)):
            self.skipTest("geode config not in the repo")
        cfg, R_ic, t_ic = mm.load_vins_camera_config(p)
        c2, ch, note = fp.make_cam(self.cam, cfg)
        d = yaml.safe_load(c2)
        self.assertEqual(note, "PINHOLE as it is")
        self.assertAlmostEqual(d["cam_fx"], cfg["projection_parameters"]["fx"], places=6)
        self.assertAlmostEqual(d["cam_d0"], cfg["distortion_parameters"]["k1"], places=8)

    def test_every_sequence_config_writes(self):
        for c in ("corridor", "corridor2", "cave02", "multifloor"):
            if all(os.path.exists(x) for x in cfgs(c)):
                m, c2, *_ = self.make(c)
                yaml.safe_load(m)
                yaml.safe_load(c2)

    def test_main_script_writes_both_files(self):
        cam_cfg, extr = cfgs("corridor2")
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([sys.executable, os.path.join(HERE, "fl_params.py"), "--main-base", MAIN, "--cam-base", CAM, "--extrinsics", extr,
                                "--camera-config", cam_cfg, "--lid-topic", "/os_cloud_node/points", "--imu-topic", "/imu/data", "--img-topic", "/x", "--out-dir", t],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(os.path.join(t, "fastlivo_config.yaml")) and os.path.exists(os.path.join(t, "fastlivo_camera.yaml")))
            for k in ("Rcl", "Pcl", "cam_fx", "lid_topic"):
                self.assertIn(k, r.stdout)

    def test_unknown_camera_model_is_an_error(self):
        with self.assertRaises(ValueError):
            fp.make_cam(self.cam, {"model_type": "KANNALA_BRANDT"})


class Build(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "Dockerfile")) as f:
            self.df = f.read()

    def test_pins_labels_portable(self):
        self.assertIn("FROM ros@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d", self.df)
        for name, (_, _, sha) in PINS.items():
            self.assertIn("ARG %s_COMMIT=%s" % (name, sha), self.df)
        self.assertIn("ARG LIVOX_DRIVER_COMMIT=3d240d5666129e1a3052e78ee8487a04b08fdda3", self.df)
        self.assertIn('baseline.method="fastlivo"', self.df)
        self.assertIn('baseline.upstream_commit="%s"' % PINS["FASTLIVO"][2], self.df)
        code = "\n".join(l for l in self.df.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("march=native", code)
        for p in ("sophus_noetic_build.patch", "vikit_noetic_build.patch", "fastlivo_noetic_build.patch", "fastlivo_rig.patch"):
            self.assertIn("apply /tmp/" + p, code)
            self.assertTrue(os.path.exists(os.path.join(HERE, p)))
        self.assertLess(code.index("make install"), code.index("catkin_make --pkg fast_livo"))

    def test_first_three_apt_steps_equal_those_of_r3live(self):
        pat = r"(RUN apt-get update.*?rm -rf /var/lib/apt/lists/\*\n)"
        mine = re.findall(pat, self.df, re.S)[:3]
        with open(os.path.join(HERE, "..", "stock_r3live", "Dockerfile")) as f:
            theirs = re.findall(pat, f.read(), re.S)[:3]
        self.assertEqual(len(mine), 3)
        self.assertEqual(mine, theirs)

    def test_every_script_the_runner_and_container_call_exists(self):
        fusion = os.path.abspath(os.path.join(HERE, ".."))
        dirs = {"$S": "stock_fastlivo", "$L": "stock_liosam", "$B": "baselines"}
        missing = []
        for f in ("run_fastlivo.sh", "inside.sh"):
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
        for needle in ('pkg="fast_livo" type="fastlivo_mapping" name="laserMapping"', "<rosparam command=\"load\" file=\"$OUT/fastlivo_config.yaml\" />",
                       '<rosparam file="$OUT/fastlivo_camera.yaml" />', "record_odom.py /aft_mapped_to_init", "/os_cloud_node/points"):
            self.assertIn(needle, s)
        self.assertNotIn("-march", s)

    def test_rig_patch_changes_one_line_and_only_the_stamp(self):
        with open(os.path.join(HERE, "fastlivo_rig.patch")) as f:
            p = f.read()
        plus = [l for l in p.splitlines() if l.startswith("+") and not l.startswith("+++")]
        minus = [l for l in p.splitlines() if l.startswith("-") and not l.startswith("---")]
        self.assertEqual((len(plus), len(minus)), (1, 1))
        self.assertIn("ros::Time::now()", minus[0])
        self.assertIn("LidarMeasures.last_update_time", plus[0])

    def test_patches_apply_to_the_pinned_sources(self):
        ran = 0
        for name, (env, default, sha) in PINS.items():
            src = os.environ.get(env, default)
            if not os.path.isdir(os.path.join(src, ".git")):
                continue
            self.assertEqual(subprocess.run(["git", "-C", src, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(), sha, name)
            patches = {"FASTLIVO": ["fastlivo_noetic_build.patch", "fastlivo_rig.patch"], "VIKIT": ["vikit_noetic_build.patch"], "SOPHUS": ["sophus_noetic_build.patch"]}[name]
            with tempfile.TemporaryDirectory() as t:
                subprocess.run(["git", "clone", "-q", src, t], check=True)
                subprocess.run(["git", "-C", t, "checkout", "-q", sha], check=True)
                for p in patches:
                    r = subprocess.run(["git", "-C", t, "apply", os.path.join(HERE, p)], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, p + ": " + r.stderr)
            ran += 1
        if ran == 0:
            self.skipTest("no upstream clones")


if __name__ == "__main__":
    unittest.main(verbosity=1)
