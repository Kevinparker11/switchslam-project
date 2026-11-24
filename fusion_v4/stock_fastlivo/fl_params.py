#!/usr/bin/env python3
"""Write the two config files of one stock FAST-LIVO run from the upstream originals (config/NTU_VIRAL.yaml and config/camera_NTU_VIRAL.yaml).

Base: the NTU_VIRAL config, the only upstream one for a spinning LiDAR (Ouster, 16 lines, like our VLP-16) with a pinhole camera. The Avia and
Mid-360 configs are for Livox scanners.

main yaml, changed keys:
  common.lid_topic, common.imu_topic, camera.img_topic     the topics of this run
  mapping.extrinsic_T, mapping.extrinsic_R                 laser_to_imu of the sequence (p_imu = R p_lidar + T)
  camera.Rcl, camera.Pcl                                   camera <- LiDAR transform, p_cam = Rcl p_lidar + Pcl, from the sequence's
                                                           LiDAR-IMU and camera-IMU extrinsics: Rcl = R_ic^T R_il, Pcl = R_ic^T (t_il - t_ic)
camera yaml, changed keys: cam_width, cam_height, cam_fx, cam_fy, cam_cx, cam_cy, cam_d0..cam_d3 (k1 k2 p1 p2)
  MEI cameras go in as the rectified pinhole of baselines/mei_model.py (zero distortion), GEODE as its own pinhole
Everything else (point_filter_num 4, blind 4, filter sizes, ncc, img_point_cov, laser_point_cov, the IMU noise scales ...) stays at the upstream value.

usage: fl_params.py --main-base F --cam-base F --extrinsics laser_to_imu.yaml --camera-config CFG --lid-topic T --imu-topic T --img-topic T --out-dir D"""
import argparse
import os
import sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "stock_liosam"))
sys.path.insert(0, os.path.join(HERE, "..", "baselines"))
sys.path.insert(0, os.path.join(HERE, "..", "stock_r3live"))
from make_params import load_laser_to_imu  # noqa: E402
import mei_model as mm  # noqa: E402
from r3_params import _sub, _list, camera_for  # noqa: E402


def camera_from_lidar(R_il, t_il, R_ic, t_ic):
    """p_cam = Rcl p_lidar + Pcl, given p_imu = R_il p_lidar + t_il and p_imu = R_ic p_cam + t_ic."""
    return R_ic.T @ R_il, R_ic.T @ (t_il - t_ic)


def make_main(base, R_il, t_il, R_cl, t_cl, lid, imu, img):
    ch = []
    out = _sub(base, "lid_topic", '"%s"' % lid, ch)
    out = _sub(out, "imu_topic", '"%s"' % imu, ch)
    out = _sub(out, "img_topic", img, ch)
    out = _sub(out, "extrinsic_T", _list(t_il), ch, True)
    out = _sub(out, "extrinsic_R", _list(R_il), ch, True)
    out = _sub(out, "Rcl", _list(R_cl), ch, True)
    out = _sub(out, "Pcl", _list(t_cl), ch, True)
    return out, ch


def make_cam(base, cfg):
    ch = []
    w, h, K, dist, note = camera_for(cfg)
    out = _sub(base, "cam_width", str(w), ch)
    out = _sub(out, "cam_height", str(h), ch)
    out = _sub(out, "cam_fx", "%.10g" % K[0], ch)
    out = _sub(out, "cam_fy", "%.10g" % K[4], ch)
    out = _sub(out, "cam_cx", "%.10g" % K[2], ch)
    out = _sub(out, "cam_cy", "%.10g" % K[5], ch)
    for i, k in enumerate(("cam_d0", "cam_d1", "cam_d2", "cam_d3")):
        out = _sub(out, k, "%.10g" % dist[i], ch)
    return out, ch, note


def main():
    ap = argparse.ArgumentParser()
    for k in ("main-base", "cam-base", "extrinsics", "camera-config", "lid-topic", "imu-topic", "img-topic", "out-dir"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    R_il, t_il = load_laser_to_imu(a.extrinsics)
    cfg, R_ic, t_ic = mm.load_vins_camera_config(a.camera_config)
    R_cl, t_cl = camera_from_lidar(R_il, t_il, R_ic, t_ic)
    with open(a.main_base) as f:
        main_txt, ch1 = make_main(f.read(), R_il, t_il, R_cl, t_cl, a.lid_topic, a.imu_topic, a.img_topic)
    with open(a.cam_base) as f:
        cam_txt, ch2, note = make_cam(f.read(), cfg)
    yaml.safe_load(main_txt)
    yaml.safe_load(cam_txt)
    with open(os.path.join(a.out_dir, "fastlivo_config.yaml"), "w") as f:
        f.write(main_txt)
    with open(os.path.join(a.out_dir, "fastlivo_camera.yaml"), "w") as f:
        f.write(cam_txt)
    print("configs written to %s (camera: %s)" % (a.out_dir, note))
    for k, o, n in ch1 + ch2:
        print("  %-14s %s  ->  %s" % (k, o, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
