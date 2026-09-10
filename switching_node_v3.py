#!/usr/bin/env python3
import rospy
import numpy as np
import csv
import time
import message_filters
from std_msgs.msg import Float64MultiArray
from nav_msgs.msg import Odometry
from gazebo_msgs.msg import ModelStates

e1 = (0 + 1/np.sqrt(3)) / 2
e2 = (e1 + 1/np.sqrt(2)) / 2
e3 = (e2 + 1) / 2
e_m = np.array([e1, e2, e3])
semicircle_threshold = e_m - np.sqrt(0.103 * e_m)

VO_FAIL_VELOCITY_BOUND = 3.0
REG_EPS = 1e-6

prev_lidar_pos = None
prev_visual_pos = None
prev_T = None
latest_gt = {"x": None, "y": None, "z": None}

log_file = open("switching_log_v3.csv", "w", newline="")
writer = csv.writer(log_file)
writer.writerow(["time", "mode", "l1", "l2", "l3", "s_vo_fail",
                  "fused_x", "fused_y", "fused_z", "gt_x", "gt_y", "gt_z"])

count = [0]

def gt_callback(msg):
    try:
        idx = msg.name.index("husky")
    except ValueError:
        return
    p = msg.pose[idx].position
    latest_gt["x"] = p.x
    latest_gt["y"] = p.y
    latest_gt["z"] = p.z

def sync_callback(hessian_msg, vhessian_msg, lidar_msg, visual_msg):
    global prev_lidar_pos, prev_visual_pos, prev_T
    if latest_gt["x"] is None:
        return

    H_l = np.array(hessian_msg.data).reshape(6, 6)
    Hv = np.array(vhessian_msg.data).reshape(6, 6)

    eigvals = np.linalg.eigvalsh(H_l)
    smallest3 = np.clip(eigvals[:3], 1e-9, None)
    lambda_bar = smallest3 / np.linalg.norm(smallest3)
    is_degenerate = bool(np.any(lambda_bar < semicircle_threshold))

    Htt_l = H_l[3:6, 3:6]
    Htt_v = Hv[0:3, 0:3]

    lidar_pos = np.array([lidar_msg.pose.pose.position.x,
                           lidar_msg.pose.pose.position.y,
                           lidar_msg.pose.pose.position.z])
    visual_pos = np.array([visual_msg.pose.pose.position.x,
                            visual_msg.pose.pose.position.y,
                            visual_msg.pose.pose.position.z])
    visual_vel = np.array([visual_msg.twist.twist.linear.x,
                            visual_msg.twist.twist.linear.y,
                            visual_msg.twist.twist.linear.z])
    s_vo_fail = bool(np.linalg.norm(visual_vel) > VO_FAIL_VELOCITY_BOUND)

    if prev_lidar_pos is None:
        prev_lidar_pos = lidar_pos
        prev_visual_pos = visual_pos
        prev_T = lidar_pos.copy()
        return

    delta_lidar = lidar_pos - prev_lidar_pos
    delta_visual = visual_pos - prev_visual_pos

    if s_vo_fail:
        mode = "LIDAR_ONLY"
        T_k = prev_T + delta_lidar
    elif not is_degenerate:
        mode = "LIDAR_ONLY"
        T_k = prev_T + delta_lidar
    else:
        mode = "TIGHTLY_COUPLED"
        H_sum = Htt_l + Htt_v + REG_EPS * np.eye(3)
        rhs = Htt_l @ delta_lidar + Htt_v @ delta_visual
        try:
            delta_fused = np.linalg.solve(H_sum, rhs)
        except np.linalg.LinAlgError:
            delta_fused = delta_visual
            mode = "TIGHTLY_COUPLED_FALLBACK"
        T_k = prev_T + delta_fused

    t = time.time()
    writer.writerow([t, mode, lambda_bar[0], lambda_bar[1], lambda_bar[2],
                      int(s_vo_fail), T_k[0], T_k[1], T_k[2],
                      latest_gt["x"], latest_gt["y"], latest_gt["z"]])
    log_file.flush()

    prev_lidar_pos = lidar_pos
    prev_visual_pos = visual_pos
    prev_T = T_k

    count[0] += 1
    if count[0] % 10 == 0:
        print(f"[{count[0]}] mode={mode:20s}  T_k={np.round(T_k,3)}  gt=({latest_gt['x']:.3f},{latest_gt['y']:.3f},{latest_gt['z']:.3f})")

def main():
    rospy.init_node("switching_node_v3", anonymous=True)
    rospy.Subscriber("/gazebo/model_states", ModelStates, gt_callback)
    hessian_sub = message_filters.Subscriber("/laser_hessian", Float64MultiArray)
    vhessian_sub = message_filters.Subscriber("/vins_mono_hessian", Float64MultiArray)
    lidar_sub = message_filters.Subscriber("/laser_odom_to_init", Odometry)
    visual_sub = message_filters.Subscriber("/vins_estimator/odometry", Odometry)
    ts = message_filters.ApproximateTimeSynchronizer(
        [hessian_sub, vhessian_sub, lidar_sub, visual_sub],
        queue_size=20, slop=0.15, allow_headerless=True)
    ts.registerCallback(sync_callback)
    print("Switching node v3 (with ground truth) listening... drive now. Ctrl+C to stop.")
    rospy.spin()

if __name__ == "__main__":
    try:
        main()
    finally:
        log_file.close()
        print("Saved switching_log_v3.csv")
