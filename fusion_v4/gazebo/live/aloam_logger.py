#!/usr/bin/env python3
"""Passive logger for the standalone A-LOAM control (nothing is published, nothing in the run changes).
Writes two TUM-style files, 't x y z qx qy qz qw' on the simulation clock (same clock as gt_logger.py):
  <prefix>_aft.txt   A-LOAM scan-to-map output  (/aft_mapped_to_init)
  <prefix>_odom.txt  A-LOAM scan-to-scan odometry (/laser_odom_to_init)
usage: python3 aloam_logger.py /root/thr/aloam_C1   (stop with Ctrl-C)"""
import sys
import rospy
from nav_msgs.msg import Odometry

pre = sys.argv[1]
fa, fo = open(pre + "_aft.txt", "w"), open(pre + "_odom.txt", "w")
for f in (fa, fo):
    f.write("# t x y z qx qy qz qw (simulation clock)\n")

def mk(f):
    def cb(m):
        p, q = m.pose.pose.position, m.pose.pose.orientation
        f.write("%.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f\n" % (rospy.get_time(), p.x, p.y, p.z, q.x, q.y, q.z, q.w))
        f.flush()
    return cb

rospy.init_node("aloam_logger", anonymous=True)
rospy.Subscriber("/aft_mapped_to_init", Odometry, mk(fa), queue_size=50)
rospy.Subscriber("/laser_odom_to_init", Odometry, mk(fo), queue_size=50)
print("aloam_logger writing %s_aft.txt and %s_odom.txt" % (pre, pre), flush=True)
rospy.spin()
