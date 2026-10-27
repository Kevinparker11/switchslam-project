#!/usr/bin/env python3
"""Make iG-LIO publish its LiDAR measurement information with every odometry message.

iG-LIO (Chen et al., RA-L 2024) solves a 15-state error-state MAP problem. In LIO::StepOptimize the Gauss-Newton
matrix H (15x15, state order [orientation, position, velocity, ba, bg]) is first filled with the LiDAR (GICP or
point-to-plane) terms and only afterwards with the IMU prior. The LiDAR-only information is therefore the 6x6 block
H[0:6, 0:6] right after the LiDAR constraints:  I = sum_i dres_i^T Lambda_i dres_i  (robust Cauchy weights and
gicp_constraint_gain included), with
    dres/dx = [ R * hat(mean_A)  |  -I ]   for the perturbation (dtheta_I, dp_W):
the rotation is a right perturbation in the IMU body frame (the cloud is in the IMU frame after T_imu_lidar), the position
is in the world frame. This patch reorders it to [dp_W, dtheta_I] -- exactly the convention of the GenZ-LIO patch
(genz/patch_genz_information.py) -- and writes it row-major into nav_msgs/Odometry.pose.covariance of /lio_odom. The field
then holds an INFORMATION matrix, not a covariance; only lio_bridge.py reads it (IGLIO_TOPICS in the bridge).
The information of the LAST iteration is exported (the converged state). It is zero while the map is still being built
(first 10 scans), when the bridge sends a near-zero information (weight ~ 0 -> VINS-Mono).

Usage (inside the container, on a clone of https://github.com/zijiechenrobotics/ig_lio at commit 2d79259):
    python3 patch_iglio_information.py /root/iglio_ws/src/ig_lio
Originals are kept as <file>.bak_info. Running it twice does nothing.
"""
import os
import shutil
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "/root/iglio_ws/src/ig_lio"
F_H = os.path.join(root, "include/ig_lio/lio.h")
F_CPP = os.path.join(root, "src/lio.cpp")
F_NODE = os.path.join(root, "src/ig_lio_node.cpp")
MARK = "IGLIO_INFO_PATCH"


def edit(path, old, new, count=1):
    src = open(path).read()
    if new in src:
        return False
    n = src.count(old)
    assert n == count, "%s: anchor found %d times (expected %d):\n%s" % (path, n, count, old)
    if not os.path.exists(path + ".bak_info"):
        shutil.copy(path, path + ".bak_info")
    open(path, "w").write(src.replace(old, new))
    return True


if all(MARK in open(p).read() for p in (F_H, F_CPP, F_NODE)):
    print("already patched, nothing to do")
    sys.exit(0)

# 1. header: member + getter
edit(F_H,
     "  size_t GetFinalIterations() { return iter_num_; }",
     "  size_t GetFinalIterations() { return iter_num_; }\n"
     "  // " + MARK + ": LiDAR-only information of the last iteration, [dp_W, dtheta_I] (zero before the map is built)\n"
     "  Eigen::Matrix<double, 6, 6> GetLidarInformation() { return lidar_information_; }")
edit(F_H,
     "  size_t iter_num_{0};",
     "  size_t iter_num_{0};\n"
     "  Eigen::Matrix<double, 6, 6> lidar_information_ = Eigen::Matrix<double, 6, 6>::Zero();  // " + MARK)

# 2. lio.cpp: zero it while the map is built, capture it after the LiDAR constraints (before the IMU prior)
edit(F_CPP,
     "  // Make sure the local map is dense enought to measurement update\n  if (lidar_frame_count_ <= 10) {",
     "  lidar_information_.setZero();  // " + MARK + "\n"
     "  // Make sure the local map is dense enought to measurement update\n  if (lidar_frame_count_ <= 10) {")
edit(F_CPP,
     '  // LOG(INFO) << "lidar H: " << std::endl << H << std::endl;',
     '  // LOG(INFO) << "lidar H: " << std::endl << H << std::endl;\n'
     "  {  // " + MARK + ": H holds the LiDAR terms only (the IMU prior is added below); reorder [ori, pos] -> [pos, ori]\n"
     "    const Eigen::Matrix<double, 6, 6> L = H.block<6, 6>(IndexErrorOri, IndexErrorOri);\n"
     "    lidar_information_.block<3, 3>(0, 0) = L.block<3, 3>(3, 3);\n"
     "    lidar_information_.block<3, 3>(0, 3) = L.block<3, 3>(3, 0);\n"
     "    lidar_information_.block<3, 3>(3, 0) = L.block<3, 3>(0, 3);\n"
     "    lidar_information_.block<3, 3>(3, 3) = L.block<3, 3>(0, 0);\n"
     "  }")

# 3. node: put it into the odometry message
edit(F_NODE,
     "  odom_pub.publish(odom_msg);",
     "  {  // " + MARK + ": pose.covariance carries the LiDAR INFORMATION [dp_W, dtheta_I], row-major\n"
     "    const Eigen::Matrix<double, 6, 6> info = lio_ptr->GetLidarInformation();\n"
     "    for (int r = 0; r < 6; ++r)\n"
     "      for (int c = 0; c < 6; ++c) odom_msg.pose.covariance[6 * r + c] = info(r, c);\n"
     "  }\n"
     "  odom_pub.publish(odom_msg);")
print("patched: information exported on /lio_odom pose.covariance")
