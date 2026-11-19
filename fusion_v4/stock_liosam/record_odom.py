#!/usr/bin/env python3
"""Write nav_msgs/Odometry as TUM lines (t x y z qx qy qz qw), t = the message header stamp (bag clock).
usage: record_odom.py TOPIC OUT.tum        stop with SIGINT"""
import sys

import rospy
from nav_msgs.msg import Odometry


def main():
    topic, out = rospy.myargv()[1:3]
    rospy.init_node("liosam_recorder", disable_signals=False)
    f = open(out, "w", buffering=1)
    n = [0]

    def cb(m):
        p, q = m.pose.pose.position, m.pose.pose.orientation
        f.write("%.6f %.6f %.6f %.6f %.8f %.8f %.8f %.8f\n" % (m.header.stamp.to_sec(), p.x, p.y, p.z, q.x, q.y, q.z, q.w))
        n[0] += 1

    rospy.Subscriber(topic, Odometry, cb, queue_size=1000)
    rospy.loginfo("recording %s -> %s", topic, out)
    rospy.spin()
    f.close()
    rospy.loginfo("recorded %d poses", n[0])


if __name__ == "__main__":
    main()
