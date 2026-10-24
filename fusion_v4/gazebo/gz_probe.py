#!/usr/bin/env python3
"""Read one message of each sensor topic from a running Gazebo world and print what the SLAM stack will see (runs inside the container)."""
import sys, time
import rospy
from sensor_msgs.msg import PointCloud2, Image, Imu
import sensor_msgs.point_cloud2 as pc2
from rosgraph_msgs.msg import Clock

rospy.init_node("gz_probe", anonymous=True)
def one(topic, typ, timeout=30):
    try:
        return rospy.wait_for_message(topic, typ, timeout=timeout)
    except rospy.ROSException:
        return None
ok = True
def report(name, good, text):
    global ok
    ok = ok and good
    print("%-5s %-14s %s" % ("PASS" if good else "FAIL", name, text))

# simulation speed: sim clock against wall clock over 10 s
c0 = one("/clock", Clock); w0 = time.time()
time.sleep(10)
c1 = one("/clock", Clock); w1 = time.time()
if c0 and c1:
    rtf = (c1.clock.to_sec() - c0.clock.to_sec()) / (w1 - w0)
    report("real-time", rtf > 0.15, "simulation runs at %.2f x real time (a 10 min route takes about %.0f min)" % (rtf, 10.0 / max(rtf, 1e-3)))
else:
    report("real-time", False, "no /clock (use_sim_time world not running)")

m = one("/velodyne_points", PointCloud2)
if m is None:
    report("lidar", False, "no /velodyne_points")
else:
    names = [f.name for f in m.fields]
    pts = list(pc2.read_points(m, field_names=("x", "y", "z"), skip_nans=True))
    n = len(pts)
    report("lidar", n > 500, "fields %s, %d valid points in one scan (frame %s, stamp %.3f)" % (names, n, m.header.frame_id, m.header.stamp.to_sec()))
    report("lidar time", "time" in names, "per-point 'time' field %s (GenZ-LIO needs it: the converter adds a zero one when missing)" % ("present" if "time" in names else "MISSING"))

im = one("/camera/image_raw", Image)
if im is None:
    report("camera", False, "no /camera/image_raw (camera needs a display: Xvfb)")
else:
    import numpy as np
    a = np.frombuffer(im.data, dtype=np.uint8)
    report("camera", im.encoding in ("mono8", "8UC1") and a.std() > 3.0,
           "%dx%d %s, pixel std %.1f (a std below 3 means a blank image: no texture to track)" % (im.width, im.height, im.encoding, a.std()))

imu = one("/imu/data", Imu)
if imu is None:
    report("imu", False, "no /imu/data")
else:
    report("imu", True, "frame %s, accel (%.2f %.2f %.2f), gyro (%.3f %.3f %.3f)" % ((imu.header.frame_id,) + (imu.linear_acceleration.x, imu.linear_acceleration.y, imu.linear_acceleration.z, imu.angular_velocity.x, imu.angular_velocity.y, imu.angular_velocity.z)))
print("PROBE_RESULT %s" % ("OK" if ok else "FAILED"))
sys.exit(0 if ok else 1)
