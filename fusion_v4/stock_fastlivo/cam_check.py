#!/usr/bin/env python3
"""Is the camera topic in the first bag, and how fast is it?  usage: cam_check.py --topic T BAG   (run in the container)
Prints CAMERA_TOPIC_OK=yes|no, CAMERA_HZ and the message type."""
import argparse
import sys

import rosbag

ap = argparse.ArgumentParser()
ap.add_argument("--topic", required=True)
ap.add_argument("bag")
a = ap.parse_args()
b = rosbag.Bag(a.bag)
info = b.get_type_and_topic_info().topics
if a.topic not in info:
    print("CAMERA_TOPIC_OK=no (%s is not in %s)" % (a.topic, a.bag))
    sys.exit(0)
dur = max(b.get_end_time() - b.get_start_time(), 1e-6)
print("CAMERA_TOPIC_OK=yes")
print("CAMERA_TYPE=%s" % info[a.topic].msg_type)
print("CAMERA_HZ=%.1f" % (info[a.topic].message_count / dur))
