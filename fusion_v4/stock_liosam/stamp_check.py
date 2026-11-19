#!/usr/bin/env python3
"""Do the IMU and the LiDAR messages of a bag use the same clock?  (stock LIO-SAM pairs them by header stamp.)
usage: stamp_check.py --imu TOPIC --lidar TOPIC BAG
For the first message of each topic it prints header.stamp minus the bag record time. If the two offsets differ by more than a
fraction of a second, the IMU and the LiDAR stamps are on different clocks and LIO-SAM cannot pair them."""
import argparse
import rosbag

ap = argparse.ArgumentParser()
ap.add_argument("--imu", required=True)
ap.add_argument("--lidar", required=True)
ap.add_argument("bag")
a = ap.parse_args()
b = rosbag.Bag(a.bag)
off = {}
for name, topic in (("IMU", a.imu), ("LIDAR", a.lidar)):
    for _, m, t in b.read_messages(topics=[topic]):
        off[name] = m.header.stamp.to_sec() - t.to_sec()
        print("%s_HEADER_MINUS_BAGTIME_S=%.3f" % (name, off[name]))
        break
d = off["IMU"] - off["LIDAR"]
print("IMU_MINUS_LIDAR_CLOCK_S=%.3f" % d)
print("SAME_CLOCK=%s" % ("yes" if abs(d) < 0.5 else "NO"))
