#!/usr/bin/env python
import rospy
import numpy as np
from geometry_msgs.msg import Twist
from gazebo_msgs.msg import ModelStates
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2

WAYPOINTS = [
    (0.0, 0.0), (0.0, -40.0), (-20.0, -40.0), (-40.0, -40.0),
]

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
    yaw = np.arctan2(2*(q.w*q.z + q.x*q.y), 1 - 2*(q.y*q.y + q.z*q.z))
    current_pos["x"] = p.x
    current_pos["y"] = p.y
    current_pos["yaw"] = yaw
    if last_pos[0] is not None:
        d = np.hypot(p.x - last_pos[0][0], p.y - last_pos[0][1])
        total_distance[0] += d
    last_pos[0] = (p.x, p.y)

def lidar_callback(msg):
    points = np.array(list(pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)),
                       dtype=np.float32)
    if len(points) == 0:
        return
    x, y, z = points[:,0], points[:,1], points[:,2]
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

def main():
    rospy.init_node("waypoint_driver_v4")
    rospy.Subscriber("/gazebo/model_states", ModelStates, model_callback)
    rospy.Subscriber("/velodyne_points", PointCloud2, lidar_callback, queue_size=1)
    pub = rospy.Publisher("/husky_velocity_controller/cmd_vel", Twist, queue_size=10)
    rate = rospy.Rate(10)

    print("Waiting for ground truth...")
    while current_pos["x"] is None and not rospy.is_shutdown():
        rate.sleep()
    print("Following smooth route, %d waypoints." % len(WAYPOINTS))

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
        dx = tx - current_pos["x"]
        dy = ty - current_pos["y"]
        dist = np.hypot(dx, dy)

        if dist < GOAL_TOLERANCE:
            print("Reached waypoint %d/%d (%.1f, %.1f). Total distance: %.1f m" %
                  (wp_idx+1, len(WAYPOINTS), tx, ty, total_distance[0]))
            wp_idx += 1
            continue

        target_yaw = np.arctan2(dy, dx)
        yaw_err = target_yaw - current_pos["yaw"]
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
