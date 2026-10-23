#!/usr/bin/env python3
"""Write the ONE frozen GenZ-LIO configuration used for every sequence in fusion_v4.

Base: GenZ-LIO's own SubT-MRS Multi Floor file (experiments/subt_mrs/vlp16_multi_floor.yaml). Multi Floor is
already our tuning sequence, so taking its settings adds no new tuning on the test sequences. GenZ-LIO's paper
used a different file per sequence (voxel size, planar threshold, IMU noise differ); we do NOT, so our GenZ-only
numbers (config G0) may be worse than their Table 4 on Long Corridor and the caves. That is the honest protocol.
Only these are changed, for every sequence alike:
  - extrinsic: our own laser_to_imu (EXTRINSIC_YAML, the file fusion_node_v2 uses; default Multi Floor values),
    so GenZ-LIO and the fusion node use the same calibration;
  - topics: /velodyne_points, /imu/data;
  - publishing: the full deskewed scan (dense) for the keyframe recorder and SAH; no path/semantic clouds.
usage: python3 make_genz_config.py <genz-lio source dir> <output yaml>
"""
import os
import sys

import numpy as np
import yaml

src_dir = sys.argv[1] if len(sys.argv) > 1 else "/root/genz_ws/src/genz-lio"
out = sys.argv[2] if len(sys.argv) > 2 else "/root/thr/genz_frozen.yaml"
# Default (the frozen protocol): GenZ-LIO's own Multi Floor file for every sequence.
# GENZ_BASE_YAML=<file name under ros/config/experiments/subt_mrs/, or a full path> selects the authors' own file for a sequence
# (the "authors' config" protocol: the settings the GenZ-LIO paper used for that sequence, fixed by them, not tuned here).
_b = os.environ.get("GENZ_BASE_YAML", "vlp16_multi_floor.yaml")
base = _b if os.path.isabs(_b) else os.path.join(src_dir, "ros/config/experiments/subt_mrs", _b)
if not os.path.exists(base):
    d = os.path.dirname(base)
    sys.exit("GenZ base config not found: %s\navailable in %s: %s" % (base, d, sorted(os.listdir(d)) if os.path.isdir(d) else "(no such folder)"))
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

cfg["common"]["lidar_topic"] = os.environ.get("GENZ_LIDAR_TOPIC", "/velodyne_points")
cfg["common"]["imu_topic"] = os.environ.get("GENZ_IMU_TOPIC", "/imu/data")
cfg["mapping"]["extrinsic_est_en"] = False
cfg["mapping"]["extrinsic_t"] = [float(x) for x in T[:3, 3]]
cfg["mapping"]["extrinsic_r"] = [float(x) for x in R.ravel()]
pub = cfg.setdefault("publish", {})
pub.update(path_en=False, scan_publish_en=True, dense_publish_en=True, scan_bodyframe_pub_en=False,
           scan_semantic_publish_en=False, voxel_map_en=False)
with open(out, "w") as f:
    f.write("# fusion_v4 frozen GenZ-LIO config, generated from %s by make_genz_config.py\n" % base)
    yaml.safe_dump(cfg, f, sort_keys=False)
print("wrote %s (base %s, extrinsic t = %s)" % (out, os.path.basename(base), np.round(T[:3, 3], 3)))
