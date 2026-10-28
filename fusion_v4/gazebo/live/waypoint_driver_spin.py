#!/usr/bin/env python
"""Phase 3 driver of docs/results/R_Channel_Rotation_Aware_Test_Protocol.md: switchslam_v1/farm/waypoint_driver_v4.py (same L route,
0.25 m/s, same obstacle avoidance) with one change: after reaching each of the waypoints (0,-20), (0,-40), (-20,-40), (-40,-40) the robot
turns once on the spot through 360 degrees at SPIN_RATE rad/s (counter-clockwise), then drives on.  The extra waypoint (0,-20) lies on the
first leg of the old route, so the path is the same L.  Four turns in total.  SPIN_RATE defaults to 1.2 rad/s (env SPIN_RATE)."""
import os
import rospy
import numpy as np
from geometry_msgs.msg import Twist
from gazebo_msgs.msg import ModelStates
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2

WAYPOINTS = [(0.0, -20.0), (0.0, -40.0), (-20.0, -40.0), (-40.0, -40.0)]   # starts at (0,0); a spin follows each of these
SPIN_RATE = float(os.environ.get("SPIN_RATE", "1.2"))
GOAL_TOLERANCE = 1.5
MAX_LINEAR_ACCEL = 0.05
LINEAR_SPEED = 0.25
ANGULAR_GAIN = 0.8
MAX_ANGULAR = 0.5
OBSTACLE_DISTANCE = 1.5
FORWARD_HALF_ANGLE = 0.5
TURN_SPEED = 0.6

current_pos = {"x": None, "y": None, "yaw": None}
total_distance = [0.0]
last_linear = [0.0]
last_pos = [None]
obstacle_ahead = [False]
turn_direction = [1.0]


def model_callback(msg):
    try:
        idx = msg.name.index("husky")
    except ValueError:
        return
    p = msg.pose[idx].position
    q = msg.pose[idx].orientation
    current_pos["yaw"] = np.arctan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    current_pos["x"], current_pos["y"] = p.x, p.y
    if last_pos[0] is not None:
        total_distance[0] += np.hypot(p.x - last_pos[0][0], p.y - last_pos[0][1])
    last_pos[0] = (p.x, p.y)


def lidar_callback(msg):
    points = np.array(list(pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)), dtype=np.float32)
    if len(points) == 0:
        return
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    height_ok = (z >= -0.3) & (z <= 0.5)
    angle = np.arctan2(y, x)
    dist = np.hypot(x, y)
    forward_mask = (x > 0) & (np.abs(angle) < FORWARD_HALF_ANGLE) & (dist < 8.0) & height_ok
    min_forward_dist = dist[forward_mask].min() if forward_mask.any() else float('inf')
    was_blocked = obstacle_ahead[0]
    obstacle_ahead[0] = min_forward_dist < OBSTACLE_DISTANCE
    if obstacle_ahead[0] and not was_blocked:
        turn_direction[0] = 1.0 if np.random.rand() > 0.5 else -1.0
        print("Obstacle at %.2fm, turning to avoid." % min_forward_dist)


def spin_once(pub, rate):
    """one full counter-clockwise turn on the spot; the turned angle is integrated from the ground-truth yaw"""
    pub.publish(Twist())
    rospy.sleep(1.0)
    acc, prev = 0.0, current_pos["yaw"]
    t0 = rospy.get_time()
    while not rospy.is_shutdown() and acc < 2 * np.pi - 0.05 and rospy.get_time() - t0 < 4 * 2 * np.pi / SPIN_RATE:
        cmd = Twist()
        cmd.angular.z = SPIN_RATE
        pub.publish(cmd)
        rate.sleep()
        d = current_pos["yaw"] - prev
        acc += (d + np.pi) % (2 * np.pi) - np.pi
        prev = current_pos["yaw"]
    pub.publish(Twist())
    rospy.sleep(1.0)
    print("Spin done: turned %.2f rad in %.1f s (commanded %.2f rad/s)" % (acc, rospy.get_time() - t0, SPIN_RATE))
    last_linear[0] = 0.0


def main():
    rospy.init_node("waypoint_driver_spin")
    rospy.Subscriber("/gazebo/model_states", ModelStates, model_callback)
    rospy.Subscriber("/velodyne_points", PointCloud2, lidar_callback, queue_size=1)
    pub = rospy.Publisher("/husky_velocity_controller/cmd_vel", Twist, queue_size=10)
    rate = rospy.Rate(10)
    print("Waiting for ground truth...")
    while current_pos["x"] is None and not rospy.is_shutdown():
        rate.sleep()
    # the first leg starts from the current position; the route is (0,0) -> (0,-20) -> (0,-40) -> (-20,-40) -> (-40,-40)
    print("Following the L route with a 360 degree turn at each of %d waypoints (SPIN_RATE %.2f rad/s)." % (len(WAYPOINTS), SPIN_RATE))
    wp_idx = 0
    while not rospy.is_shutdown() and wp_idx < len(WAYPOINTS):
        cmd = Twist()
        if obstacle_ahead[0]:
            cmd.angular.z = turn_direction[0] * TURN_SPEED
            cmd.linear.x = 0.0
            pub.publish(cmd)
            rate.sleep()
            continue
        tx, ty = WAYPOINTS[wp_idx]
        dx, dy = tx - current_pos["x"], ty - current_pos["y"]
        if np.hypot(dx, dy) < GOAL_TOLERANCE:
            print("Reached waypoint %d/%d (%.1f, %.1f). Total distance: %.1f m" % (wp_idx + 1, len(WAYPOINTS), tx, ty, total_distance[0]))
            spin_once(pub, rate)
            wp_idx += 1
            continue
        yaw_err = np.arctan2(dy, dx) - current_pos["yaw"]
        yaw_err = np.arctan2(np.sin(yaw_err), np.cos(yaw_err))
        cmd.angular.z = np.clip(ANGULAR_GAIN * yaw_err, -MAX_ANGULAR, MAX_ANGULAR)
        target_linear = LINEAR_SPEED if abs(yaw_err) < 0.4 else 0.0
        last_linear[0] = last_linear[0] + np.clip(target_linear - last_linear[0], -MAX_LINEAR_ACCEL, MAX_LINEAR_ACCEL)
        cmd.linear.x = last_linear[0]
        pub.publish(cmd)
        rate.sleep()
    pub.publish(Twist())
    print("Route complete. Total distance travelled: %.1f m" % total_distance[0])


if __name__ == "__main__":
    main()
