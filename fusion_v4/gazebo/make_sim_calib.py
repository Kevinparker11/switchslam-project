#!/usr/bin/env python3
"""Write the camera and extrinsic calibration files of the Gazebo Husky in the SubT-MRS format that setup_sequence.sh / make_vins_config.py read.
usage: python3 make_sim_calib.py <out dir>      -> gazebo_intrinsics.yaml, gazebo_extrinsics.yaml
All values come from husky_sim_extras.urdf.xacro and the Husky IMU plugin (hector, bodyName base_link: the IMU frame IS base_link):
  LiDAR   velodyne frame at base_link (0, 0, 0.4), no rotation                -> laser_to_imu  = identity rotation, t = (0, 0, 0.4)
  camera  camera_link at base_link (0.3, 0, 0.3), no rotation; Gazebo camera looks along +x, image right = -y, image down = -z
          optical frame (x right, y down, z forward) axes in the base frame: (0,-1,0), (0,0,-1), (1,0,0)  -> R_ic columns
  intrinsics: 640x480, horizontal fov 1.3962634 rad -> fx = fy = 320 / tan(fov / 2), cx = 320, cy = 240, no distortion"""
import math, os, sys
import numpy as np
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
fov = 1.3962634; f = 320.0 / math.tan(fov / 2)
R_ic = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]], float)      # columns = optical x, y, z expressed in the IMU (base) frame
assert abs(np.linalg.det(R_ic) - 1) < 1e-9 and np.allclose(R_ic @ R_ic.T, np.eye(3))
T_ic = np.eye(4); T_ic[:3, :3] = R_ic; T_ic[:3, 3] = [0.3, 0.0, 0.3]
T_li = np.eye(4); T_li[:3, 3] = [0.0, 0.0, 0.4]
fmt = lambda T: ",\n         ".join(", ".join("%.8f" % v for v in row) for row in T)
open(os.path.join(out, "gazebo_intrinsics.yaml"), "w").write(
"""# Gazebo Husky camera (husky_sim_extras.urdf.xacro): 640x480, horizontal fov %.7f rad, ideal pinhole
rgb_camera:
  model_type: PINHOLE
  camera_name: camera
  image_width: 640
  image_height: 480
  distortion_parameters:
     k1: 0.0
     k2: 0.0
     p1: 0.0
     p2: 0.0
  projection_parameters:
     fx: %.6f
     fy: %.6f
     cx: 320.0
     cy: 240.0
""" % (fov, f, f))
open(os.path.join(out, "gazebo_extrinsics.yaml"), "w").write(
"""%%YAML 1.2
---
# Gazebo Husky: IMU frame = base_link (hector IMU plugin, bodyName base_link). x_imu = R x_sensor + t.
laser_to_imu:
  rows: 4
  cols: 4
  data: [%s]

rgb_camera_to_imu:
  rows: 4
  cols: 4
  data: [%s]

acc_n: 0.08
gyr_n: 0.004
acc_w: 0.00004
gyr_w: 2.0e-6
""" % (fmt(T_li), fmt(T_ic)))
print("wrote %s/gazebo_intrinsics.yaml (fx = fy = %.3f) and gazebo_extrinsics.yaml" % (out, f))
