#!/usr/bin/env python3
"""Cut the first N seconds of chosen topics out of a bag into a small bag.
Uses the bag index and copies the raw message bytes, so only that part of the input is read (`rosbag filter` scans the whole
input bag) and nothing is deserialised. Refuses to start when the output folder has too little free space, so it cannot fill a disk.
usage: make_slice.py IN.bag OUT.bag --topics T1 [T2 ...] [--seconds 70]
Run it inside the liosam_stock image (it needs the rosbag python module)."""
import argparse
import os
import shutil
import sys

import rosbag
import rospy

ap = argparse.ArgumentParser()
ap.add_argument("inp")
ap.add_argument("out")
ap.add_argument("--topics", nargs="+", required=True)
ap.add_argument("--seconds", type=float, default=70.0)
a = ap.parse_args()

bag = rosbag.Bag(a.inp)
t0, t1 = bag.get_start_time(), bag.get_end_time()
present = set(bag.get_type_and_topic_info().topics)
missing = [t for t in a.topics if t not in present]
if missing:
    print("WARNING: not in the bag: %s" % ", ".join(missing))
topics = [t for t in a.topics if t in present]
if not topics:
    sys.exit("none of the requested topics is in %s" % a.inp)
frac = min(1.0, a.seconds / max(t1 - t0, 1e-6))
est = os.path.getsize(a.inp) * frac                      # upper bound: the other topics are left out
outdir = os.path.dirname(os.path.abspath(a.out))
free = shutil.disk_usage(outdir).free
print("input %.1f GB, %.0f s; slice of %.0f s: at most about %.1f GB; free in %s: %.1f GB"
      % (os.path.getsize(a.inp) / 1e9, t1 - t0, a.seconds, est / 1e9, outdir, free / 1e9))
if free < 1.5 * est + 1e9:
    sys.exit("REFUSED: not enough free space in %s (need about %.1f GB)" % (outdir, (1.5 * est + 1e9) / 1e9))
n = 0
with rosbag.Bag(a.out, "w") as ob:
    for topic, msg, t in bag.read_messages(topics=topics, end_time=rospy.Time.from_sec(t0 + a.seconds), raw=True):
        ob.write(topic, msg, t, raw=True)
        n += 1
print("wrote %d messages to %s (%.2f GB)" % (n, a.out, os.path.getsize(a.out) / 1e9))
