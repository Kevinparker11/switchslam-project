#!/usr/bin/env python3
"""Input adapter for stock LIO-SAM, started only when preflight says the bag's cloud breaks one of LIO-SAM's input rules.
It changes the container of the data, never a point coordinate:
  --drop-nan     remove points whose x, y or z is not finite, set is_dense = true   (LIO-SAM shuts down on is_dense == false)
  --shift-time   if the per-point time is negative (relative to the scan END, as in GEODE), subtract the minimum so the
                 first point has time 0 and move the header stamp by the same amount (LIO-SAM reads time as an offset
                 from the scan start)
usage: cloud_adapter.py IN_TOPIC OUT_TOPIC [--drop-nan] [--shift-time]
"""
import argparse
import os
import sys

import rospy
from sensor_msgs.msg import PointCloud2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lio_inputs as li


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--drop-nan", action="store_true")
    ap.add_argument("--shift-time", action="store_true")
    a = ap.parse_args(rospy.myargv()[1:])
    rospy.init_node("liosam_cloud_adapter")
    pub = rospy.Publisher(a.dst, PointCloud2, queue_size=50)
    stats = {"n": 0, "shifted": 0}

    def cb(m):
        f = [(x.name, x.offset, x.datatype, x.count) for x in m.fields]
        data, n, tmin = li.adapt_cloud(f, m.point_step, m.data, a.shift_time, m.is_bigendian)
        out = PointCloud2()
        out.header = m.header
        if tmin < 0:
            out.header.stamp = m.header.stamp + rospy.Duration.from_sec(tmin)
            stats["shifted"] += 1
        out.height, out.width = 1, n
        out.fields, out.is_bigendian, out.point_step = m.fields, m.is_bigendian, m.point_step
        out.row_step, out.data, out.is_dense = n * m.point_step, data, True
        pub.publish(out)
        stats["n"] += 1

    rospy.Subscriber(a.src, PointCloud2, cb, queue_size=50)
    rospy.loginfo("adapter %s -> %s drop_nan=%s shift_time=%s", a.src, a.dst, a.drop_nan, a.shift_time)
    rospy.spin()
    rospy.loginfo("adapter done: %d clouds, %d shifted", stats["n"], stats["shifted"])


if __name__ == "__main__":
    main()
