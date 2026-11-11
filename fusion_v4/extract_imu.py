#!/usr/bin/env python3
"""Write the IMU of a bag folder to one CSV (t, gx, gy, gz, ax, ay, az; header stamps, IMU frame), for offline_imu_check.py.
Needs the ROS python modules, so run it in a ROS container:  bash extract_imu.sh BAG_DIR OUT.csv [topic] [seconds]
usage: python3 extract_imu.py BAG_DIR OUT.csv [topic1,topic2] [seconds]
  topics   default /imu/data,/cmu_sp1/imu/data (first one found is used)
  seconds  only the first N seconds of the bag (default 0 = the whole bag).  The bag index is used to jump to that part, so a big bag on a slow
           disk is read in seconds instead of being read from end to end; use it for the window screen (the first 180 s) and for quick checks."""
import csv
import glob
import os
import sys
import time

import rosbag
import rospy

bag_dir, out = sys.argv[1], sys.argv[2]
topics = (sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "/imu/data,/cmu_sp1/imu/data").split(",")
secs = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
bags = sorted(glob.glob(os.path.join(bag_dir, "*.bag")))
assert bags, "no .bag in %s" % bag_dir
starts = []
for b in bags:
    with rosbag.Bag(b) as bg:
        starts.append(bg.get_start_time())
t0 = min(starts)
t_end = t0 + secs if secs > 0 else None
rows, used, t_wall = [], None, time.time()
for b, st in zip(bags, starts):
    if t_end is not None and st > t_end:
        continue
    with rosbag.Bag(b) as bg:
        have = set(bg.get_type_and_topic_info().topics)
        use = used or next((t for t in topics if t in have), None)
        if use is None:
            continue
        used = use
        kw = {}
        if t_end is not None:
            kw["end_time"] = rospy.Time.from_sec(t_end)
        print("reading %s from %s%s" % (use, os.path.basename(b), " (first %.0f s)" % secs if secs > 0 else ""), flush=True)
        for _, m, _ in bg.read_messages(topics=[use], **kw):
            rows.append((m.header.stamp.to_sec(), m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z,
                         m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z))
            if len(rows) % 20000 == 0:
                print("  %d samples, bag time +%.0f s, %.0f s elapsed" % (len(rows), rows[-1][0] - t0, time.time() - t_wall), flush=True)
assert rows, "none of %s found in %s" % (topics, bags)
rows.sort()
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["t", "gx", "gy", "gz", "ax", "ay", "az"]); w.writerows(rows)
print("wrote %s: %d samples from %s, %.1f s, %.0f Hz" % (out, len(rows), used, rows[-1][0] - rows[0][0], len(rows) / max(rows[-1][0] - rows[0][0], 1e-9)))
