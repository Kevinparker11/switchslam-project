#!/usr/bin/env python3
"""Write the r3live_config.yaml of one stock R3LIVE run.

The ORIGINAL config/r3live_config.yaml of the pinned commit is copied and only these keys are replaced (everything else, including the
filter sizes, the online estimation of camera-IMU extrinsic and intrinsics (both 1 upstream), maximum_vio_tracked_pts and lidar_time_delay, stays):

 Lidar_front_end.lidar_type     3   the Ouster path (our Velodyne cloud is converted to Ouster fields by vel_to_ouster.py; the Velodyne handler is a stub)
 r3live_common.record_offline_map  0   no map file is written at the end (output only; the laptop disk cannot take it)
 r3live_vio.image_width / image_height / camera_intrinsic / camera_dist_coeffs
                                the camera the method sees: for the MEI cameras the rectified pinhole of baselines/mei_model.py
                                (no distortion), for GEODE its own pinhole intrinsics and k1 k2 p1 p2 (k3 = 0)
 r3live_vio.camera_ext_R / camera_ext_t   camera-IMU extrinsic of the sequence. In R3LIVE `rot_ext_i2c` is the camera orientation in the
                                IMU frame (R_w2c = R_w2imu * rot_ext_i2c), the same convention as the VINS-Mono extrinsic
 r3live_lio.lidar_offset_to_imu  (new key, read by r3live_rig.patch) the LiDAR origin in the IMU frame, t of laser_to_imu. Upstream compiles in
                                the offset of the authors' Livox Avia. R3LIVE has no LiDAR-IMU rotation: it assumes the frames are aligned
                                (our rotations are within 3 degrees; the angle is printed)

usage: r3_params.py --base r3live_config.yaml --extrinsics laser_to_imu.yaml --camera-config CFG --out OUT.yaml
"""
import argparse
import os
import re
import sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "stock_liosam"))
sys.path.insert(0, os.path.join(HERE, "..", "baselines"))
from make_params import load_laser_to_imu  # noqa: E402
import mei_model as mm  # noqa: E402


def _list(v):
    return "[" + ", ".join("%.9g" % x for x in np.asarray(v, dtype=float).reshape(-1)) + "]"


def _sub(text, key, value, changes, multiline_list=False):
    """Replace the value of the active (not commented) key `key` once."""
    if multiline_list:
        pat = re.compile(r"^(\s*%s:\s*)\[[^\]]*\]" % re.escape(key), re.M)
    else:
        pat = re.compile(r"^(\s*%s:[ \t]*)[^\s#][^#\n]*?([ \t]*(#.*)?)$" % re.escape(key), re.M)
    hits = pat.findall(text)
    if len(hits) != 1:
        raise ValueError("key %s found %d times as an active line in the base config (expected 1)" % (key, len(hits)))
    m = pat.search(text)
    old = " ".join(m.group(0)[len(m.group(1)):].split("#")[0].split())
    changes.append((key, old, value))
    return pat.sub(lambda mm_: mm_.group(1) + value + ("" if multiline_list else mm_.group(2)), text, count=1)


def camera_for(cfg):
    """(width, height, K 3x3, dist[5], note) of the camera R3LIVE gets."""
    if cfg["model_type"] == "MEI":
        w, h, f, cx, cy = mm.rectified_pinhole(cfg)
        return w, h, np.array([f, 0, cx, 0, f, cy, 0, 0, 1.0]), np.zeros(5), "MEI -> rectified pinhole (no distortion)"
    if cfg["model_type"] == "PINHOLE":
        p, d = cfg["projection_parameters"], cfg["distortion_parameters"]
        return (int(cfg["image_width"]), int(cfg["image_height"]), np.array([p["fx"], 0, p["cx"], 0, p["fy"], p["cy"], 0, 0, 1.0]),
                np.array([d["k1"], d["k2"], d["p1"], d["p2"], 0.0]), "PINHOLE as it is")
    raise ValueError("camera model %s is not handled" % cfg["model_type"])


def make(base, R_il, t_il, cfg, R_ic, t_ic):
    ch = []
    w, h, K, dist, note = camera_for(cfg)
    out = _sub(base, "lidar_type", "3", ch)
    out = _sub(out, "record_offline_map", "0", ch)
    out = _sub(out, "image_width", str(w), ch)
    out = _sub(out, "image_height", str(h), ch)
    out = _sub(out, "camera_intrinsic", _list(K), ch, True)
    out = _sub(out, "camera_dist_coeffs", _list(dist), ch, True)
    out = _sub(out, "camera_ext_R", _list(R_ic), ch, True)
    out = _sub(out, "camera_ext_t", _list(t_ic), ch, True)
    pat = re.compile(r"^(\s*)(lidar_time_delay:[^\n]*\n)", re.M)
    if len(pat.findall(out)) != 1:
        raise ValueError("lidar_time_delay not found once")
    out = pat.sub(lambda m: m.group(1) + m.group(2) + m.group(1) + "lidar_offset_to_imu: " + _list(t_il) + "   # new key, read by r3live_rig.patch\n", out, count=1)
    ch.append(("lidar_offset_to_imu", "(compiled in: authors' Avia 0.04165, 0.02326, -0.0284)", _list(t_il)))
    return out, ch, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--extrinsics", required=True)
    ap.add_argument("--camera-config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R_il, t_il = load_laser_to_imu(a.extrinsics)
    cfg, R_ic, t_ic = mm.load_vins_camera_config(a.camera_config)
    with open(a.base) as f:
        base = f.read()
    text, ch, note = make(base, R_il, t_il, cfg, R_ic, t_ic)
    yaml.safe_load(text)
    with open(a.out, "w") as f:
        f.write(text)
    print("config written: %s (keys changed from the upstream file; camera: %s)" % (a.out, note))
    for k, o, n in ch:
        print("  %-22s %s  ->  %s" % (k, o, n))
    ang = np.degrees(np.arccos(np.clip((np.trace(R_il) - 1) / 2, -1, 1)))
    print("  LiDAR-IMU rotation %.2f deg from identity (R3LIVE assumes aligned frames and ignores it)" % ang)
    return 0


if __name__ == "__main__":
    sys.exit(main())
