#!/usr/bin/env python3
"""Write params_camera.yaml and params_lidar.yaml of one stock LVI-SAM run.

The ORIGINAL config files of the pinned LVI-SAM commit are copied and only these keys are replaced (every other value, such as
IMU noise, feature tracker settings, voxel sizes and N_SCAN 16, stays at the upstream default):

 params_lidar.yaml : pointCloudTopic, imuTopic, extrinsicTrans, extrinsicRot, extrinsicRPY, loopClosureEnableFlag (false)
 params_camera.yaml: imu_topic, image_topic, the camera model block (model_type .. projection_parameters, image size),
                     extrinsicRotation, extrinsicTranslation, lidar_to_cam_tx..rz, fisheye (0), loop_closure (0),
                     and two new keys, lidar_imu_rotation and imu_camros_rotation, read by lvisam_extrinsics.patch.

Frames. Our files give T_imu<-lidar = [R_il t_il] (laser_to_imu) and the camera as the VINS extrinsic [R_ic t_ic]
(optical axes x right, y down, z forward, p_imu = R_ic p_cam + t_ic).
 - LiDAR side (LVI-SAM include utility.h): acc_lidar = extRot * acc_imu, q_lidar = q_imu * Quaternion(extRPY) (no inverse in this
   older code, unlike the LIO-SAM commit used elsewhere), IMU position in the LiDAR frame = extTrans. So
   extrinsicRot = R_il^T, extrinsicRPY = R_il, extrinsicTrans = -R_il^T t_il.
 - Upstream hard-codes a 180 deg turn about y at two places for the authors' rig. Both are rotations the rig defines:
   initial_alignment.h: R_lidar_imu = R_il^T (LiDAR pose -> IMU pose),  visualization.cpp: R_imu_camros = R_ic * M, where
   M turns optical axes into ROS axes (x forward, y left, z up). The tests show that the authors' own config values
   give back exactly their 180 deg turn.
 - lidar_to_cam_*: the LiDAR cloud is moved into the camera (ROS axes) frame, p_c = R_camros_imu (R_il p_l + t_il - t_ic),
   written as x y z roll pitch yaw for pcl::getTransformation (R = Rz(yaw) Ry(pitch) Rx(roll)).
R matrices are projected to the nearest rotation (SVD) first.

usage: lvi_params.py --camera-base params_camera.yaml --lidar-base params_lidar.yaml --extrinsics laser_to_imu.yaml
          --camera-config <VINS config of the sequence> --points-topic T --imu-topic T --image-topic T --outdir DIR
"""
import argparse
import os
import re
import sys

import numpy as np
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stock_liosam"))
from make_params import _fmt_mat, _fmt_vec, _sub_once, load_laser_to_imu  # noqa: E402

# ROS camera axes (x forward, y left, z up) written in optical coordinates, as columns
M_ROS_FROM_OPT = np.array([[0.0, -1.0, 0.0], [0.0, 0.0, -1.0], [1.0, 0.0, 0.0]])


def nearest_rotation(R):
    U, _, Vt = np.linalg.svd(R)
    Q = U @ Vt
    if np.linalg.det(Q) < 0:
        raise ValueError("matrix is a reflection")
    return Q


def load_camera_config(path):
    """(config dict, R_ic, t_ic) of a VINS-Mono style config (OpenCV yaml)."""
    with open(path) as f:
        txt = f.read().replace("%YAML:1.0", "").replace("!!opencv-matrix", "")
    c = yaml.safe_load(txt)
    R = np.array(c["extrinsicRotation"]["data"], dtype=float).reshape(3, 3)
    t = np.array(c["extrinsicTranslation"]["data"], dtype=float).reshape(3)
    return c, nearest_rotation(R), t


def rpy_from_matrix(R):
    """roll, pitch, yaw with R = Rz(yaw) Ry(pitch) Rx(roll) (pcl::getTransformation / tf convention)."""
    pitch = -np.arcsin(np.clip(R[2, 0], -1.0, 1.0))
    return np.arctan2(R[2, 1], R[2, 2]), pitch, np.arctan2(R[1, 0], R[0, 0])


def rig_constants(R_il, t_il, R_ic, t_ic):
    R_camros = R_ic @ M_ROS_FROM_OPT                     # camera (ROS axes) in the IMU frame
    R_cl = R_camros.T @ R_il                             # LiDAR frame -> camera ROS frame
    t_cl = R_camros.T @ (t_il - t_ic)
    return {
        "ext_rot": R_il.T, "ext_rpy": R_il.copy(), "ext_trans": -R_il.T @ t_il,
        "R_lidar_imu": R_il.T, "R_imu_camros": R_camros,
        "lidar_to_cam": np.concatenate([t_cl, rpy_from_matrix(R_cl)]),
    }


def _num(x):
    return repr(float(x))


def camera_block(c):
    mt = c["model_type"]
    L = ["model_type: %s" % mt, "camera_name: %s" % c.get("camera_name", "camera"), "",
         "# Mono camera config", "image_width: %d" % c["image_width"], "image_height: %d" % c["image_height"]]
    if mt == "MEI":
        L += ["mirror_parameters:", "   xi: %s" % _num(c["mirror_parameters"]["xi"])]
    L.append("distortion_parameters:")
    L += ["   %s: %s" % (k, _num(c["distortion_parameters"][k])) for k in ("k1", "k2", "p1", "p2")]
    L.append("projection_parameters:")
    keys = ("gamma1", "gamma2", "u0", "v0") if mt == "MEI" else ("fx", "fy", "cx", "cy")
    L += ["   %s: %s" % (k, _num(c["projection_parameters"][k])) for k in keys]
    return "\n".join(L) + "\n"


def _cv_matrix_data(text, key, M):
    pat = re.compile(r"(%s:\s*!!opencv-matrix\s*rows:\s*\d+\s*cols:\s*\d+\s*dt:\s*d\s*data:\s*)\[[^\]]*\]" % key)
    if len(pat.findall(text)) != 1:
        raise ValueError("matrix %s not found once in the base params_camera.yaml" % key)
    return pat.sub(lambda m: m.group(1) + "[" + ", ".join("%.9f" % v for v in M.reshape(-1)) + "]", text, count=1)


def _cv_matrix(key, M, comment):
    rows, cols = M.shape
    d = ", ".join("%.9f" % v for v in M.reshape(-1))
    return "\n# %s\n%s: !!opencv-matrix\n   rows: %d\n   cols: %d\n   dt: d\n   data: [%s]\n" % (comment, key, rows, cols, d)


def make_camera(base, cfg, R_ic, t_ic, rig, imu_topic, image_topic):
    ch = []
    out = _sub_once(base, "imu_topic", '"%s"' % imu_topic, ch)
    out = _sub_once(out, "image_topic", '"%s"' % image_topic, ch)
    for k, v in zip(("lidar_to_cam_tx", "lidar_to_cam_ty", "lidar_to_cam_tz", "lidar_to_cam_rx", "lidar_to_cam_ry", "lidar_to_cam_rz"),
                    rig["lidar_to_cam"]):
        out = _sub_once(out, k, "%.9f" % v, ch)
    pat = re.compile(r"^model_type:.*?(?=^fisheye_mask:)", re.M | re.S)
    if len(pat.findall(out)) != 1:
        raise ValueError("camera model block not found once in the base params_camera.yaml")
    ch.append(("camera model block", "MEI 720x540 (authors' camera)", "%s %dx%d (ours)" % (cfg["model_type"], cfg["image_width"], cfg["image_height"])))
    out = pat.sub(lambda m: camera_block(cfg), out, count=1)
    out = _cv_matrix_data(out, "extrinsicRotation", R_ic)
    out = _cv_matrix_data(out, "extrinsicTranslation", t_ic.reshape(3, 1))
    ch.append(("extrinsicRotation / extrinsicTranslation", "authors' camera-IMU", "ours (camera config of the sequence)"))
    out = _sub_once(out, "fisheye", "0", ch)
    out = _sub_once(out, "loop_closure", "0", ch)
    out += _cv_matrix("lidar_imu_rotation", rig["R_lidar_imu"], "orientation of the IMU frame in the LiDAR frame (read by lvisam_extrinsics.patch)")
    out += _cv_matrix("imu_camros_rotation", rig["R_imu_camros"], "orientation of the camera, ROS axes, in the IMU frame (read by lvisam_extrinsics.patch)")
    ch.append(("lidar_imu_rotation, imu_camros_rotation", "(new keys; upstream hard-codes 180 deg about y)", "from the sequence extrinsics"))
    return out, ch


def make_lidar(base, rig, points_topic, imu_topic):
    ch = []
    out = _sub_once(base, "pointCloudTopic", '"%s"' % points_topic, ch)
    out = _sub_once(out, "imuTopic", '"%s"' % imu_topic, ch)
    out = _sub_once(out, "extrinsicTrans", _fmt_vec(rig["ext_trans"]), ch)
    out = _sub_once(out, "extrinsicRot", _fmt_mat(rig["ext_rot"]), ch)
    out = _sub_once(out, "extrinsicRPY", _fmt_mat(rig["ext_rpy"]), ch)
    out = _sub_once(out, "loopClosureEnableFlag", "false", ch)
    return out, ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera-base", required=True)
    ap.add_argument("--lidar-base", required=True)
    ap.add_argument("--extrinsics", required=True)
    ap.add_argument("--camera-config", required=True)
    ap.add_argument("--points-topic", required=True)
    ap.add_argument("--imu-topic", required=True)
    ap.add_argument("--image-topic", required=True)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    R_il, t_il = load_laser_to_imu(a.extrinsics)
    cfg, R_ic, t_ic = load_camera_config(a.camera_config)
    rig = rig_constants(R_il, t_il, R_ic, t_ic)
    cam, ch1 = make_camera(open(a.camera_base).read(), cfg, R_ic, t_ic, rig, a.imu_topic, a.image_topic)
    lid, ch2 = make_lidar(open(a.lidar_base).read(), rig, a.points_topic, a.imu_topic)
    yaml.safe_load(lid)
    os.makedirs(a.outdir, exist_ok=True)
    open(os.path.join(a.outdir, "params_camera.yaml"), "w").write(cam)
    open(os.path.join(a.outdir, "params_lidar.yaml"), "w").write(lid)
    print("keys changed from the upstream files:")
    for name, ch in (("params_camera.yaml", ch1), ("params_lidar.yaml", ch2)):
        for k, o, n in ch:
            print("  %-18s %-42s %s  ->  %s" % (name, k, o, n))
    for k in ("R_lidar_imu", "R_imu_camros"):
        ang = np.degrees(np.arccos(np.clip((np.trace(rig[k]) - 1) / 2, -1, 1)))
        print("  rotation %s is %.2f deg from identity" % (k, ang))
    return 0


if __name__ == "__main__":
    sys.exit(main())
