#!/usr/bin/env python3
"""Write the two config files of one stock R2LIVE run from the upstream originals (config/lio_config.yaml, config/filr_cam.yaml).

lio_config.yaml, changed keys:
  feature_extraction.lidar_type  3   the Ouster handler (vel_to_r2live.py puts the cloud on its topic; the Velodyne handler never fills the
                                     per-point time, see vel_to_r2live.py)
  feature_extraction.N_SCANS     1   upstream 6 is the Livox line count; the Ouster handler reads N_SCANS points per step, 1 = the whole cloud in order
  r2live_lio.lidar_offset_to_imu     (new section, read by r2live_rig.patch) the LiDAR origin in the IMU frame, t of laser_to_imu. R2LIVE has no
                                     LiDAR-IMU rotation (frames assumed aligned; the angle of ours is printed)
cam config (VINS-Mono style, camodocal models: MEI and PINHOLE are both supported, so no rectification), changed:
  imu_topic, model_type, image_width, image_height, mirror_parameters (MEI), distortion_parameters, projection_parameters,
  extrinsicRotation, extrinsicTranslation (camera in the IMU frame, p_imu = R p_cam + t, estimate_extrinsic stays 0 as upstream: trusted)
Everything else (feature tracker settings, IMU noise, estimate_td 1, filter sizes, ...) stays at the upstream value.

usage: r2_params.py --lio-base F --cam-base F --extrinsics laser_to_imu.yaml --camera-config CFG --imu-topic T --out-dir D"""
import argparse
import os
import re
import sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "stock_liosam"))
sys.path.insert(0, os.path.join(HERE, "..", "baselines"))
sys.path.insert(0, os.path.join(HERE, "..", "stock_r3live"))
from make_params import load_laser_to_imu  # noqa: E402
import mei_model as mm  # noqa: E402
from r3_params import _sub, _list  # noqa: E402


def make_lio(base, t_il):
    ch = []
    out = _sub(base, "lidar_type", "3", ch)
    out = _sub(out, "N_SCANS", "1", ch)
    out = out.rstrip("\n") + "\n\nr2live_lio:\n   lidar_offset_to_imu: %s   # new section, read by r2live_rig.patch\n" % _list(t_il)
    ch.append(("lidar_offset_to_imu", "(compiled in: authors' Avia 0.04165, 0.02326, -0.0284)", _list(t_il)))
    return out, ch


def camera_block(cfg):
    model = cfg["model_type"]
    lines = ["model_type: %s" % model, "camera_name: camera", "image_width: %d" % int(cfg["image_width"]), "image_height: %d" % int(cfg["image_height"])]
    d, p = cfg["distortion_parameters"], cfg["projection_parameters"]
    if model == "MEI":
        lines += ["mirror_parameters:", "   xi: %.10g" % cfg["mirror_parameters"]["xi"]]
        proj = [("gamma1", p["gamma1"]), ("gamma2", p["gamma2"]), ("u0", p["u0"]), ("v0", p["v0"])]
    elif model == "PINHOLE":
        proj = [("fx", p["fx"]), ("fy", p["fy"]), ("cx", p["cx"]), ("cy", p["cy"])]
    else:
        raise ValueError("camera model %s is not handled" % model)
    lines += ["distortion_parameters:"] + ["   %s: %.10g" % (k, d.get(k, 0.0)) for k in ("k1", "k2", "p1", "p2")]
    lines += ["projection_parameters:"] + ["   %s: %.10g" % (k, v) for k, v in proj]
    return "\n".join(lines) + "\n\n"


def make_cam(base, cfg, R_ic, t_ic, imu_topic):
    ch = []
    start = base.index("model_type:")
    end = base.index("# Extrinsic parameter between IMU and Camera.")
    block = camera_block(cfg)
    out = base[:start] + block + base[end:]
    ch.append(("camera model block", "(upstream rig: PINHOLE 640x512)", " ".join(block.split())))
    out = _sub(out, "imu_topic", '"%s"' % imu_topic, ch)
    for key, val in (("extrinsicRotation", R_ic), ("extrinsicTranslation", t_ic)):
        i = out.index(key + ":")
        pat = re.compile(r"^(\s+)data:\s*\[[^\]]*\]", re.M)
        m = pat.search(out, i)
        if m is None:
            raise ValueError("no active data line after %s" % key)
        out = out[:m.start()] + m.group(1) + "data: " + _list(val) + out[m.end():]
        ch.append((key, "(upstream rig)", _list(val)))
    return out, ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lio-base", required=True)
    ap.add_argument("--cam-base", required=True)
    ap.add_argument("--extrinsics", required=True)
    ap.add_argument("--camera-config", required=True)
    ap.add_argument("--imu-topic", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    R_il, t_il = load_laser_to_imu(a.extrinsics)
    cfg, R_ic, t_ic = mm.load_vins_camera_config(a.camera_config)
    with open(a.lio_base) as f:
        lio, ch1 = make_lio(f.read(), t_il)
    with open(a.cam_base) as f:
        cam, ch2 = make_cam(f.read(), cfg, R_ic, t_ic, a.imu_topic)
    yaml.safe_load(lio)
    yaml.safe_load(cam.replace("%YAML:1.0", "").replace("!!opencv-matrix", ""))
    with open(os.path.join(a.out_dir, "lio_config.yaml"), "w") as f:
        f.write(lio)
    with open(os.path.join(a.out_dir, "cam_config.yaml"), "w") as f:
        f.write(cam)
    print("configs written to %s; camera model %s (used as it is)" % (a.out_dir, cfg["model_type"]))
    for k, o, n in ch1 + ch2:
        print("  %-22s %s  ->  %s" % (k, o, n))
    print("  LiDAR-IMU rotation %.2f deg from identity (R2LIVE assumes aligned frames and ignores it)"
          % np.degrees(np.arccos(np.clip((np.trace(R_il) - 1) / 2, -1, 1))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
