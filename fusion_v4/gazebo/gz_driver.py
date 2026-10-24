#!/usr/bin/env python3
"""Drive the simulated Husky along a planned route (pure pursuit) and publish the exact pose as the ground truth (inside the container).
usage: gz_driver.py <route.csv> [laps] [speed m/s]
Publishes /gt/husky_pose (PoseStamped, world frame, simulation time, from /gazebo/model_states; the model pose is the base_link
frame, which is also the IMU frame of the Husky simulation) and drives /husky_velocity_controller/cmd_vel.
Exit 0 at the end of the route, 3 if the robot gets stuck."""
import sys, math
import numpy as np
import rospy
from geometry_msgs.msg import Twist, PoseStamped
from gazebo_msgs.msg import ModelStates

route = np.loadtxt(sys.argv[1], delimiter=",", comments="#")
laps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
V = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
R = np.vstack([route] * laps)
LOOK, WMAX, SPIN = 0.5, 0.6, 0.9      # look-ahead (m), max yaw rate (rad/s), heading error above which it turns on the spot (rad)
pose = {"x": None, "y": None, "yaw": None}; last_pub = [-1.0]

def cb(msg):
    if "husky" not in msg.name:
        rospy.logerr_throttle(5, "no model named 'husky' in /gazebo/model_states: %s" % list(msg.name)); return
    p = msg.pose[msg.name.index("husky")]; q = p.orientation
    pose["x"], pose["y"] = p.position.x, p.position.y
    pose["yaw"] = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    t = rospy.get_time()
    if t - last_pub[0] >= 0.0099:
        last_pub[0] = t; m = PoseStamped(); m.header.stamp = rospy.Time.now(); m.header.frame_id = "world"; m.pose = p; gt.publish(m)

rospy.init_node("gz_driver")
gt = rospy.Publisher("/gt/husky_pose", PoseStamped, queue_size=200)
cmd = rospy.Publisher("/husky_velocity_controller/cmd_vel", Twist, queue_size=5)
rospy.Subscriber("/gazebo/model_states", ModelStates, cb, queue_size=1)
while pose["x"] is None and not rospy.is_shutdown(): rospy.sleep(0.2)
t0 = rospy.get_time()
while rospy.get_time() - t0 < 5.0 and not rospy.is_shutdown(): rospy.sleep(0.1)       # let the IMU and the sensors settle
print("driver: start (%.2f, %.2f), route %d points, %d lap(s), %.1f m/s" % (pose["x"], pose["y"], len(R), laps, V), flush=True)
idx = 0; best = (0, rospy.get_time()); done_dist = 0.0; rate = rospy.Rate(20); last_report = 0
while not rospy.is_shutdown():
    x, y, yaw = pose["x"], pose["y"], pose["yaw"]
    hi = min(len(R), idx + 12)                                  # progress at most 3 m per step along the route: out-and-back parts (the dead-end lobe) revisit places
    j = idx + int(np.argmin(np.hypot(R[idx:hi, 0] - x, R[idx:hi, 1] - y))); idx = max(idx, j)
    if idx >= len(R) - 2 and math.hypot(R[-1, 0] - x, R[-1, 1] - y) < 0.6: break
    k = idx
    while k < len(R) - 1 and math.hypot(R[k, 0] - x, R[k, 1] - y) < LOOK: k += 1
    err = math.atan2(R[k, 1] - y, R[k, 0] - x) - yaw; err = math.atan2(math.sin(err), math.cos(err))
    m = Twist()
    if abs(err) > SPIN: m.angular.z = WMAX * (1 if err > 0 else -1)
    else:
        m.linear.x = max(0.15, V * (1 - abs(err) / 1.2)); m.angular.z = float(np.clip(1.6 * err, -WMAX, WMAX))
    cmd.publish(m)
    if idx > best[0] + 4: best = (idx, rospy.get_time())
    elif rospy.get_time() - best[1] > 40: print("driver: STUCK at (%.2f, %.2f), route index %d" % (x, y, idx), flush=True); cmd.publish(Twist()); sys.exit(3)
    if rospy.get_time() - last_report > 30:
        last_report = rospy.get_time(); print("driver: sim t %.0f s, route %d%%, at (%.1f, %.1f)" % (last_report, 100 * idx // len(R), x, y), flush=True)
    rate.sleep()
for _ in range(10): cmd.publish(Twist()); rospy.sleep(0.1)
print("driver: DONE route at sim t %.0f s" % rospy.get_time(), flush=True)
