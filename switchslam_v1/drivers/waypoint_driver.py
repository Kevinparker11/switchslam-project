#!/usr/bin/env python
import rospy
import numpy as np
from geometry_msgs.msg import Twist
from gazebo_msgs.msg import ModelStates

TARGET_DISTANCE = 536.0
WAYPOINTS = [(0.0, 0.0), (-20.0, -30.0)]
GOAL_TOLERANCE = 1.0
LINEAR_SPEED = 0.4
ANGULAR_GAIN = 1.5
MAX_ANGULAR = 0.8

current_pos = {"x": None, "y": None, "yaw": None}
total_distance = [0.0]
last_pos = [None]

def model_callback(msg):
    try:
        idx = msg.name.index("husky")
    except ValueError:
        return
    p = msg.pose[idx].position
    q = msg.pose[idx].orientation
    yaw = np.arctan2(2*(q.w*q.z + q.x*q.y), 1 - 2*(q.y*q.y + q.z*q.z))
    current_pos["x"] = p.x
    current_pos["y"] = p.y
    current_pos["yaw"] = yaw

    if last_pos[0] is not None:
        d = np.hypot(p.x - last_pos[0][0], p.y - last_pos[0][1])
        total_distance[0] += d
    last_pos[0] = (p.x, p.y)

def main():
    rospy.init_node("waypoint_driver")
    rospy.Subscriber("/gazebo/model_states", ModelStates, model_callback)
    pub = rospy.Publisher("/husky_velocity_controller/cmd_vel", Twist, queue_size=10)
    rate = rospy.Rate(10)

    print("Waiting for ground truth...")
    while current_pos["x"] is None and not rospy.is_shutdown():
        rate.sleep()
    print("Starting waypoint drive.")

    wp_idx = 0
    while not rospy.is_shutdown() and total_distance[0] < TARGET_DISTANCE:
        tx, ty = WAYPOINTS[wp_idx]
        dx = tx - current_pos["x"]
        dy = ty - current_pos["y"]
        dist = np.hypot(dx, dy)

        if dist < GOAL_TOLERANCE:
            wp_idx = (wp_idx + 1) % len(WAYPOINTS)
            print("Reached waypoint %d, switching. Total distance: %.1f m" % (wp_idx, total_distance[0]))
            continue

        target_yaw = np.arctan2(dy, dx)
        yaw_err = target_yaw - current_pos["yaw"]
        yaw_err = np.arctan2(np.sin(yaw_err), np.cos(yaw_err))

        cmd = Twist()
        cmd.angular.z = np.clip(ANGULAR_GAIN * yaw_err, -MAX_ANGULAR, MAX_ANGULAR)
        if abs(yaw_err) < 0.5:
            cmd.linear.x = LINEAR_SPEED
        pub.publish(cmd)
        rate.sleep()

    pub.publish(Twist())
    print("Done. Total distance travelled: %.1f m" % total_distance[0])

if __name__ == "__main__":
    main()
