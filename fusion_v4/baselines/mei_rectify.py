#!/usr/bin/env python3
"""ROS node: MEI camera image -> pinhole image without distortion (see mei_model.py). Needs cv2 and cv_bridge (the Noetic images have them).
usage: mei_rectify.py CAMERA_CONFIG IN_TOPIC OUT_TOPIC      (CAMERA_CONFIG = the VINS config of the sequence)
The header (stamp, frame_id) is kept. The output keeps the encoding of the input."""
import os
import sys

import cv2
import rospy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mei_model as mm  # noqa: E402


def main():
    cfg_path, topic_in, topic_out = rospy.myargv()[1:4]
    rospy.init_node("mei_rectify")
    cfg, _, _ = mm.load_vins_camera_config(cfg_path)
    mx, my = mm.rectify_maps(cfg)
    mx, my = cv2.convertMaps(mx, my, cv2.CV_16SC2)
    bridge = CvBridge()
    pub = rospy.Publisher(topic_out, Image, queue_size=5)
    n = [0]

    def cb(msg):
        img = bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        if img.shape[1] != mx.shape[1] or img.shape[0] != mx.shape[0]:
            rospy.logerr_throttle(5, "image %dx%d but the config says %dx%d" % (img.shape[1], img.shape[0], mx.shape[1], mx.shape[0]))
            return
        out = bridge.cv2_to_imgmsg(cv2.remap(img, mx, my, cv2.INTER_LINEAR), encoding=msg.encoding)
        out.header = msg.header
        pub.publish(out)
        n[0] += 1
        if n[0] % 200 == 1:
            rospy.loginfo("mei_rectify: %d frames", n[0])

    rospy.Subscriber(topic_in, Image, cb, queue_size=5, buff_size=2 ** 26)
    rospy.spin()


if __name__ == "__main__":
    main()
