#!/usr/bin/env python
"""GEODE bags hold only /left_camera/compressed (JPEG). VINS-Mono's feature_tracker wants sensor_msgs/Image.
Decodes each JPEG to mono8 and republishes on /left_camera/image_raw with the original header (stamp kept).
Runs in the ROS Kinetic VINS container (python2 or 3; needs cv2 + numpy, which cv_bridge already pulls in)."""
import cv2
import numpy as np
import rospy
from sensor_msgs.msg import CompressedImage, Image

rospy.init_node("geode_republish")
pub = rospy.Publisher("/left_camera/image_raw", Image, queue_size=5)
n = [0]


def cb(m):
    im = cv2.imdecode(np.frombuffer(bytearray(m.data), np.uint8), cv2.IMREAD_GRAYSCALE)
    if im is None:
        return
    o = Image()
    o.header = m.header
    o.height, o.width = im.shape
    o.encoding, o.is_bigendian, o.step = "mono8", 0, im.shape[1]
    o.data = im.tobytes()
    pub.publish(o)
    n[0] += 1
    if n[0] % 100 == 1:
        rospy.loginfo("geode_republish: %d frames, %dx%d", n[0], im.shape[1], im.shape[0])


rospy.Subscriber("/left_camera/compressed", CompressedImage, cb, queue_size=5, buff_size=2 ** 26)
rospy.spin()
