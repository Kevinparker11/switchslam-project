#!/usr/bin/env python
import rospy
from geometry_msgs.msg import PointStamped
import csv

f = open('/root/gt_leica.csv', 'w')
writer = csv.writer(f)
writer.writerow(['time', 'x', 'y', 'z'])

def callback(msg):
    writer.writerow([msg.header.stamp.to_sec(), msg.point.x, msg.point.y, msg.point.z])
    f.flush()

rospy.init_node('save_leica_gt')
rospy.Subscriber('/leica/position', PointStamped, callback)
print("Listening on /leica/position...")
rospy.spin()
