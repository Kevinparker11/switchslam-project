#!/usr/bin/env python3
import rospy
import csv
import time
from nav_msgs.msg import Odometry
from gazebo_msgs.msg import ModelStates

latest_gt = {"x": None, "y": None, "z": None}

def gt_callback(msg):
    try:
        idx = msg.name.index("husky")
    except ValueError:
        return
    p = msg.pose[idx].position
    latest_gt["x"] = p.x
    latest_gt["y"] = p.y
    latest_gt["z"] = p.z

log_file = open("aloam_only_log.csv", "w", newline="")
writer = csv.writer(log_file)
writer.writerow(["time", "lidar_x", "lidar_y", "lidar_z", "gt_x", "gt_y", "gt_z"])

count = [0]

def lidar_callback(msg):
    if latest_gt["x"] is None:
        return
    t = time.time()
    p = msg.pose.pose.position
    writer.writerow([t, p.x, p.y, p.z, latest_gt["x"], latest_gt["y"], latest_gt["z"]])
    log_file.flush()
    count[0] += 1
    if count[0] % 20 == 0:
        print("[%d] lidar=(%.2f,%.2f)  gt=(%.2f,%.2f)" % (count[0], p.x, p.y, latest_gt["x"], latest_gt["y"]))

def main():
    rospy.init_node("aloam_only_logger", anonymous=True)
    rospy.Subscriber("/gazebo/model_states", ModelStates, gt_callback)
    rospy.Subscriber("/laser_odom_to_init", Odometry, lidar_callback)
    print("Logging A-LOAM-only pose + ground truth... Ctrl+C to stop.")
    rospy.spin()

if __name__ == "__main__":
    try:
        main()
    finally:
        log_file.close()
        print("Saved aloam_only_log.csv")
