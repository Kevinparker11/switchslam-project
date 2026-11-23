#!/usr/bin/env python3
"""Offline tests of the stock LVI-SAM helpers (no ROS, no bags): python3 test_stock_lvisam.py  (from fusion_v4/stock_lvisam/).
Set LVISAM_UPSTREAM=<clone of TixiaoShan/LVI-SAM at the pinned commit> to also run the writer on the real upstream config files."""
import os
import re
import sys
import unittest

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lvi_params as lp  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
UP = os.environ.get("LVISAM_UPSTREAM", "/tmp/lvi_up")

CAM_BASE = """%YAML:1.0

#common parameters
imu_topic: "/imu_raw"
image_topic: "/camera/image_raw"

lidar_to_cam_tx: 0.05
lidar_to_cam_ty: -0.07
lidar_to_cam_tz: -0.07
lidar_to_cam_rx: 0.0
lidar_to_cam_ry: 0.0
lidar_to_cam_rz: -0.04

# camera model
model_type: MEI
camera_name: camera

# Mono camera config
image_width: 720
image_height: 540
mirror_parameters:
   xi: 1.99
distortion_parameters:
   k1: -0.03
   k2: 0.15
   p1: 0.0001
   p2: -0.001
projection_parameters:
   gamma1: 669.89
   gamma2: 669.14
   u0: 377.94
   v0: 279.63
fisheye_mask: "/config/fisheye_mask_720x540.jpg"

acc_n: 0.02
extrinsicRotation: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0, 0, -1,
           -1, 0, 0,
           0, 1, 0]

extrinsicTranslation: !!opencv-matrix
   rows: 3
   cols: 1
   dt: d
   data: [0.0064, 0.0199, 0.0336]

fisheye: 1              # if using fisheye, trun on it.
loop_closure: 1                    # start loop closure
"""

LID_BASE = """PROJECT_NAME: "lvi_sam"
lvi_sam:
  pointCloudTopic: "/points_raw"               # Point cloud data
  imuTopic: "/imu_raw"                         # IMU data
  useImuHeadingInitialization: true
  imuAccNoise: 3.99e-03
  extrinsicTrans: [0.0, 0.0, 0.0]
  extrinsicRot: [-1, 0, 0, 0, 1, 0, 0, 0, -1]
  extrinsicRPY: [0, 1, 0, -1, 0, 0, 0, 0, 1]
  mappingProcessInterval: 0.15                  # seconds
  loopClosureEnableFlag: true
"""


def Rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def Ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def quat_xyzw(R):
    """Hamilton quaternion (x y z w), sign fixed so the largest component is positive."""
    w = np.sqrt(max(0.0, 1 + np.trace(R))) / 2
    if w > 1e-6:
        q = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1], 4 * w * w]) / (4 * w)
    else:
        i = np.argmax(np.diag(R))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(max(0.0, R[i, i] - R[j, j] - R[k, k] + 1)) / 2
        q = np.zeros(4)
        q[i] = s
        q[j] = (R[j, i] + R[i, j]) / (4 * s)
        q[k] = (R[k, i] + R[i, k]) / (4 * s)
        q[3] = (R[k, j] - R[j, k]) / (4 * s)
    return q if q[np.argmax(np.abs(q))] > 0 else -q


def rand_rot(seed):
    rng = np.random.RandomState(seed)
    return Rz(rng.uniform(-3, 3)) @ Ry(rng.uniform(-1.4, 1.4)) @ Rx(rng.uniform(-3, 3))


def angle_deg(R):
    return np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))


class Frames(unittest.TestCase):
    def test_M_is_a_rotation_and_maps_axes(self):
        M = lp.M_ROS_FROM_OPT
        self.assertAlmostEqual(np.linalg.det(M), 1.0)
        # column j of M is ROS axis j in optical coordinates: ROS x = optical z, ROS y = -optical x, ROS z = -optical y
        np.testing.assert_allclose(M[:, 0], [0, 0, 1])
        np.testing.assert_allclose(M[:, 1], [-1, 0, 0])
        np.testing.assert_allclose(M[:, 2], [0, -1, 0])

    def test_authors_rig_gives_their_180_deg_about_y(self):
        # upstream params_camera.yaml extrinsicRotation and params_lidar.yaml extrinsicRot (= IMU in LiDAR frame)
        R_ic = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]], float)
        R_lidar_imu = np.diag([-1.0, 1, -1])
        np.testing.assert_allclose(R_ic @ lp.M_ROS_FROM_OPT, np.diag([-1.0, 1, -1]), atol=1e-12)
        np.testing.assert_allclose(quat_xyzw(R_lidar_imu), [0, 1, 0, 0], atol=1e-12)           # tf::Quaternion(0,1,0,0)
        np.testing.assert_allclose(quat_xyzw(R_ic @ lp.M_ROS_FROM_OPT), [0, 1, 0, 0], atol=1e-12)
        rig = lp.rig_constants(R_lidar_imu.T, np.zeros(3), R_ic, np.zeros(3))
        np.testing.assert_allclose(rig["R_lidar_imu"], np.diag([-1.0, 1, -1]), atol=1e-12)
        np.testing.assert_allclose(rig["R_imu_camros"], np.diag([-1.0, 1, -1]), atol=1e-12)

    def test_lidar_side_convention(self):
        # LVI-SAM: acc_lidar = extRot acc_imu ; q_lidar = q_imu * Q(extRPY)
        R_il = rand_rot(1)
        rig = lp.rig_constants(R_il, np.array([0.1, -0.2, 0.3]), np.eye(3), np.zeros(3))
        R_w_lidar = rand_rot(2)
        R_w_imu = R_w_lidar @ R_il.T                       # the IMU frame seen from the world
        np.testing.assert_allclose(R_w_imu @ rig["ext_rpy"], R_w_lidar, atol=1e-12)
        a_imu = np.array([0.3, -1.0, 9.8])
        a_lidar = R_il.T @ a_imu                           # p_imu = R_il p_lidar  =>  p_lidar = R_il^T p_imu
        np.testing.assert_allclose(rig["ext_rot"] @ a_imu, a_lidar, atol=1e-12)
        np.testing.assert_allclose(rig["ext_trans"], -R_il.T @ np.array([0.1, -0.2, 0.3]), atol=1e-12)

    def test_lidar_to_camera_transform(self):
        R_il, t_il, R_ic, t_ic = rand_rot(3), np.array([0.08, 0.03, 0.03]), rand_rot(4), np.array([0.18, 0.05, -0.02])
        rig = lp.rig_constants(R_il, t_il, R_ic, t_ic)
        x, y, z, r, p, yw = rig["lidar_to_cam"]
        R = Rz(yw) @ Ry(p) @ Rx(r)                          # pcl::getTransformation / tf order
        pl = np.array([5.0, -2.0, 1.0])
        R_camros = R_ic @ lp.M_ROS_FROM_OPT
        want = R_camros.T @ (R_il @ pl + t_il - t_ic)       # the point in the camera (ROS axes) frame
        np.testing.assert_allclose(R @ pl + [x, y, z], want, atol=1e-10)

    def test_rpy_roundtrip(self):
        for s in range(5):
            R = rand_rot(10 + s)
            r, p, y = lp.rpy_from_matrix(R)
            np.testing.assert_allclose(Rz(y) @ Ry(p) @ Rx(r), R, atol=1e-10)

    def test_our_sequences_are_near_identity(self):
        seqs = [("configs/corridor/corridor_extrinsics.yaml", "configs/corridor/corridor_config.yaml"),
                ("configs/corridor2/corridor2_extrinsics.yaml", "configs/corridor2/corridor2_config.yaml"),
                ("configs/cave02/cave02_extrinsics.yaml", "configs/cave02/cave02_config.yaml"),
                ("fusion_v4/stock_liosam/seq/mf_extrinsics.yaml", "configs/multifloor/multifloor_config.yaml"),
                ("fusion_v4/geode/geode_extrinsics.yaml", "fusion_v4/geode/geode_config.yaml")]
        for ext, cam in seqs:
            if not os.path.exists(os.path.join(REPO, ext)):
                self.skipTest("repo files not present")
            R_il, t_il = lp.load_laser_to_imu(os.path.join(REPO, ext))
            cfg, R_ic, t_ic = lp.load_camera_config(os.path.join(REPO, cam))
            rig = lp.rig_constants(R_il, t_il, R_ic, t_ic)
            self.assertLess(angle_deg(rig["R_lidar_imu"]), 3.5, ext)
            self.assertLess(angle_deg(rig["R_imu_camros"]), 3.5, cam)
            self.assertLess(np.linalg.norm(rig["lidar_to_cam"][:3]), 0.4, ext)      # the sensors sit within a few dm


class Writer(unittest.TestCase):
    def setUp(self):
        self.R_il = Rz(0.02) @ Ry(0.01)
        self.t_il = np.array([0.08, 0.03, 0.03])
        self.R_ic = np.array([[-0.0205, -0.0004, 0.9998], [-0.9996, -0.0202, -0.0205], [0.0202, -0.9998, 0.0]])
        self.R_ic = lp.nearest_rotation(self.R_ic)
        self.t_ic = np.array([0.18, 0.047, -0.02])
        self.rig = lp.rig_constants(self.R_il, self.t_il, self.R_ic, self.t_ic)
        self.cfg_mei = {"model_type": "MEI", "camera_name": "camera", "image_width": 640, "image_height": 480,
                        "mirror_parameters": {"xi": 1.5}, "distortion_parameters": {"k1": -0.07, "k2": 0.24, "p1": 0.002, "p2": 0.001},
                        "projection_parameters": {"gamma1": 740.7, "gamma2": 660.2, "u0": 319.6, "v0": 235.2}}
        self.cfg_pin = {"model_type": "PINHOLE", "camera_name": "camera", "image_width": 1224, "image_height": 1024,
                        "distortion_parameters": {"k1": -0.05, "k2": 0.11, "p1": -5e-05, "p2": 1.6e-04},
                        "projection_parameters": {"fx": 1178.9, "fy": 1179.1, "cx": 606.6, "cy": 520.4}}

    def test_lidar_file_changes_only_the_six_keys(self):
        out, ch = lp.make_lidar(LID_BASE, self.rig, "/pts", "/imu")
        self.assertEqual(len(ch), 6)
        d = yaml.safe_load(out)["lvi_sam"]
        old = yaml.safe_load(LID_BASE)["lvi_sam"]
        self.assertEqual((d["pointCloudTopic"], d["imuTopic"], d["loopClosureEnableFlag"]), ("/pts", "/imu", False))
        np.testing.assert_allclose(np.array(d["extrinsicRot"]).reshape(3, 3), self.R_il.T, atol=1e-8)
        np.testing.assert_allclose(np.array(d["extrinsicRPY"]).reshape(3, 3), self.R_il, atol=1e-8)
        for k in old:
            if k not in ("pointCloudTopic", "imuTopic", "extrinsicTrans", "extrinsicRot", "extrinsicRPY", "loopClosureEnableFlag"):
                self.assertEqual(d[k], old[k], k)
        self.assertEqual(d["useImuHeadingInitialization"], True)      # upstream default of LVI-SAM stays
        self.assertIn("# Point cloud data", out)

    def _cam(self, cfg):
        return lp.make_camera(CAM_BASE, cfg, self.R_ic, self.t_ic, self.rig, "/imu/data", "/camera_1/image_raw")

    def test_camera_file_mei(self):
        out, ch = self._cam(self.cfg_mei)
        self.assertIn('imu_topic: "/imu/data"', out)
        self.assertIn('image_topic: "/camera_1/image_raw"', out)
        self.assertIn("model_type: MEI", out)
        self.assertIn("image_width: 640", out)
        self.assertIn("xi: 1.5", out)
        self.assertIn("gamma1: 740.7", out)
        self.assertNotIn("720", out.replace("fisheye_mask_720x540", ""))
        self.assertIn('fisheye_mask: "/config/fisheye_mask_720x540.jpg"', out)      # line after the block is untouched
        self.assertRegex(out, r"\nfisheye: 0 ")
        self.assertRegex(out, r"\nloop_closure: 0 ")
        self.assertIn("acc_n: 0.02", out)                                            # IMU noise untouched
        self.assertIn("lidar_imu_rotation: !!opencv-matrix", out)
        self.assertIn("imu_camros_rotation: !!opencv-matrix", out)
        # with the OpenCV tag removed the file is plain yaml: check the matrices
        d = yaml.safe_load(out.replace("%YAML:1.0", "").replace("!!opencv-matrix", ""))
        np.testing.assert_allclose(np.array(d["extrinsicRotation"]["data"]).reshape(3, 3), self.R_ic, atol=1e-8)
        np.testing.assert_allclose(d["extrinsicTranslation"]["data"], self.t_ic, atol=1e-8)
        np.testing.assert_allclose(np.array(d["lidar_imu_rotation"]["data"]).reshape(3, 3), self.R_il.T, atol=1e-8)
        np.testing.assert_allclose(np.array(d["imu_camros_rotation"]["data"]).reshape(3, 3), self.rig["R_imu_camros"], atol=1e-8)
        self.assertAlmostEqual(d["lidar_to_cam_tx"], self.rig["lidar_to_cam"][0], places=8)

    def test_camera_file_pinhole(self):
        out, _ = self._cam(self.cfg_pin)
        self.assertIn("model_type: PINHOLE", out)
        self.assertIn("fx: 1178.9", out)
        self.assertNotIn("mirror_parameters", out)
        self.assertNotIn("gamma1", out)
        self.assertIn("image_height: 1024", out)

    def test_missing_key_is_an_error(self):
        with self.assertRaises(ValueError):
            lp.make_lidar(LID_BASE.replace("extrinsicRPY", "extrinsicXYZ"), self.rig, "/p", "/i")

    @unittest.skipUnless(os.path.exists(os.path.join(UP, "config", "params_camera.yaml")), "no upstream clone (LVISAM_UPSTREAM)")
    def test_real_upstream_files(self):
        with open(os.path.join(UP, "config", "params_camera.yaml")) as f:
            cam = f.read()
        with open(os.path.join(UP, "config", "params_lidar.yaml")) as f:
            lid = f.read()
        out_c, ch_c = lp.make_camera(cam, self.cfg_mei, self.R_ic, self.t_ic, self.rig, "/imu/data", "/camera_1/image_raw")
        out_l, ch_l = lp.make_lidar(lid, self.rig, "/p", "/i")
        self.assertEqual(len(ch_l), 6)
        # every untouched line of the upstream file is still there, in the same order
        keep = [l for l in cam.splitlines() if l.strip() and not l.lstrip().startswith("#") and not re.match(r"^\s+-?\d", l)]
        changed = ("imu_topic", "image_topic", "lidar_to_cam_", "model_type", "camera_name", "image_width", "image_height",
                   "mirror_parameters", "xi:", "distortion_parameters", "k1:", "k2:", "p1:", "p2:", "projection_parameters",
                   "gamma1", "gamma2", "u0:", "v0:", "fisheye:", "loop_closure:", "data:")
        for l in keep:
            if not l.strip().startswith(changed):
                self.assertIn(l, out_c.splitlines(), l)
        yaml.safe_load(out_l)


if __name__ == "__main__":
    unittest.main(verbosity=1)
