#!/usr/bin/env python3
"""Write the LiDAR-to-IMU extrinsic of the running Gazebo robot for fusion_node_v2.  The IMU is the hector plugin on base_link
(husky_200hz_imu.urdf.xacro, bodyName base_link), so laser_to_imu = pose of the LiDAR frame in base_link, read from tf.
Needs Gazebo running.  usage: python3 make_live_extrinsics.py /root/thr/farm_live_extrinsics.yaml"""
import sys
import numpy as np
import rospy
import tf2_ros
from sensor_msgs.msg import PointCloud2

rospy.init_node("make_live_extrinsics", anonymous=True)
frame = rospy.wait_for_message("/velodyne_points", PointCloud2, timeout=60).header.frame_id
buf = tf2_ros.Buffer(); tf2_ros.TransformListener(buf)
tr = buf.lookup_transform("base_link", frame, rospy.Time(0), rospy.Duration(30)).transform
x, y, z, w = tr.rotation.x, tr.rotation.y, tr.rotation.z, tr.rotation.w
R = np.array([[1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
              [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
              [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]])
T = np.eye(4); T[:3, :3] = R; T[:3, 3] = [tr.translation.x, tr.translation.y, tr.translation.z]
with open(sys.argv[1], "w") as f:
    f.write("%%YAML 1.2\n---\n# Gazebo Husky (generation-1 rig as launched): LiDAR frame '%s' in base_link = IMU frame. x_imu = R x_sensor + t.\n" % frame)
    f.write("laser_to_imu:\n  rows: 4\n  cols: 4\n  data: [" + ",\n         ".join(", ".join("%.8f" % v for v in row) for row in T) + "]\n")
print("frame %s -> base_link, t = %s" % (frame, np.round(T[:3, 3], 4)), flush=True)
print("R =\n%s" % np.round(R, 4))
