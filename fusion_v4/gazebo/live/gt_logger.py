#!/usr/bin/env python3
"""Passive ground-truth logger for the live Gazebo farm run (the old switching node logged gt_x/y/z itself; fusion_node_v2 does not).
Writes 't x y z qx qy qz qw' (simulation clock, the format of gt_farm.txt) at 20 Hz from /gazebo/model_states, model 'husky'.
It publishes nothing and changes nothing in the run.  usage: python3 gt_logger.py /root/thr/gt_live.txt   (stop with Ctrl-C)"""
import sys
import rospy
from gazebo_msgs.msg import ModelStates

out = open(sys.argv[1], "w")
out.write("# t x y z qx qy qz qw (Gazebo model pose of the Husky base_link, simulation clock)\n")
last = [-1.0]

def cb(m):
    t = rospy.get_time()
    if t - last[0] < 0.05 or "husky" not in m.name:
        return
    last[0] = t
    p = m.pose[m.name.index("husky")]
    out.write("%.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f\n" % (t, p.position.x, p.position.y, p.position.z,
                                                         p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w))
    out.flush()

rospy.init_node("gt_logger", anonymous=True)
rospy.Subscriber("/gazebo/model_states", ModelStates, cb, queue_size=1)
print("gt_logger writing %s" % sys.argv[1], flush=True)
rospy.spin()
out.close()
