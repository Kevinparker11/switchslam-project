#!/usr/bin/env python3
"""Write the IMU of a bag folder to one CSV (t, gx, gy, gz, ax, ay, az; header stamps, IMU frame), for offline_imu_check.py.
Needs the ROS python modules, so run it in a ROS container:  bash extract_imu.sh BAG_DIR OUT.csv [topic]
usage: python3 extract_imu.py BAG_DIR OUT.csv [topic1,topic2]   (default topics /imu/data,/cmu_sp1/imu/data; first one found is used)"""
import csv
import glob
import os
import sys

import rosbag

bag_dir, out = sys.argv[1], sys.argv[2]
topics = (sys.argv[3] if len(sys.argv) > 3 else "/imu/data,/cmu_sp1/imu/data").split(",")
bags = sorted(glob.glob(os.path.join(bag_dir, "*.bag")))
assert bags, "no .bag in %s" % bag_dir
rows, used = [], None
for b in bags:
    with rosbag.Bag(b) as bg:
        have = set(bg.get_type_and_topic_info().topics)
        use = used or next((t for t in topics if t in have), None)
        if use is None:
            continue
        used = use
        for _, m, _ in bg.read_messages(topics=[use]):
            rows.append((m.header.stamp.to_sec(), m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z,
                         m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z))
assert rows, "none of %s found in %s" % (topics, bags)
rows.sort()
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["t", "gx", "gy", "gz", "ax", "ay", "az"]); w.writerows(rows)
print("wrote %s: %d samples from %s, %.1f s, %.0f Hz" % (out, len(rows), used, rows[-1][0] - rows[0][0], len(rows) / max(rows[-1][0] - rows[0][0], 1e-9)))
