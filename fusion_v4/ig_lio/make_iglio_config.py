#!/usr/bin/env python3
"""Write the ONE frozen iG-LIO configuration used for every sequence in fusion_v4 (FRONT=iglio).

Base: the iG-LIO authors' own Velodyne VLP-16 file (config/bg_velodyne.yaml, Botanic Garden). Their paper states that
iG-LIO "keeps identical parameters across all datasets", so one file for every sequence is the authors' own protocol
and adds no tuning on our test sequences. Only these are changed, for every sequence alike:
  - extrinsic: our own laser_to_imu (EXTRINSIC_YAML, the file fusion_node_v2 uses; default Multi Floor values), so that
    iG-LIO and the fusion node use the same calibration;
  - topics: IGLIO_LIDAR_TOPIC (default /velodyne_points), IGLIO_IMU_TOPIC (default /imu/data).
Everything else (resolutions, iterations, gains, noise) stays as the authors set it.
usage: python3 make_iglio_config.py <ig_lio source dir> <output yaml>
"""
import os
import sys

import numpy as np
import yaml

src_dir = sys.argv[1] if len(sys.argv) > 1 else "/root/iglio_ws/src/ig_lio"
out = sys.argv[2] if len(sys.argv) > 2 else "/root/thr/iglio_frozen.yaml"
base = os.path.join(src_dir, "config", os.environ.get("IGLIO_BASE_YAML", "bg_velodyne.yaml"))
if not os.path.exists(base):
    d = os.path.dirname(base)
    sys.exit("iG-LIO base config not found: %s\navailable in %s: %s" % (base, d, sorted(os.listdir(d)) if os.path.isdir(d) else "(no such folder)"))
cfg = yaml.safe_load(open(base))

T = np.array([[0.999945562, 0.009074807, 0.005149763, 0.080],
              [-0.009060897, 0.999955255, -0.002718066, 0.029],
              [-0.005174199, 0.002671256, 0.999983046, 0.030],
              [0, 0, 0, 1.0]])
if os.environ.get("EXTRINSIC_YAML"):
    with open(os.environ["EXTRINSIC_YAML"]) as f:
        T = np.array(yaml.safe_load(f.read().replace("%YAML 1.2", ""))["laser_to_imu"]["data"]).reshape(4, 4)
U, _, Vt = np.linalg.svd(T[:3, :3])
R = U @ Vt

cfg["lidar_topic"] = os.environ.get("IGLIO_LIDAR_TOPIC", "/velodyne_points")
cfg["imu_topic"] = os.environ.get("IGLIO_IMU_TOPIC", "/imu/data")
cfg["lidar_type"] = "velodyne"
cfg["t_imu_lidar"] = [float(x) for x in T[:3, 3]]
cfg["R_imu_lidar"] = [float(x) for x in R.ravel()]
with open(out, "w") as f:
    f.write("# fusion_v4 frozen iG-LIO config, generated from %s by make_iglio_config.py\n" % base)
    yaml.safe_dump(cfg, f, sort_keys=False)
print("wrote %s (base %s, extrinsic t = %s)" % (out, os.path.basename(base), np.round(T[:3, 3], 3)))
