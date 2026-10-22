#!/usr/bin/env python3
"""Make GenZ-LIO publish its LiDAR measurement information with every odometry message.

After the ESIKF update, the 6x6 information of the LiDAR measurements alone (no IMU prior),
    I = J^T diag(R_inv) J,   J = h_x[:, 0:6]   (columns: world position dp_W (3), IMU-body rotation dtheta_I (3)),
is written row-major into nav_msgs/Odometry.pose.covariance of /Odometry. The field then holds an
INFORMATION matrix, not a covariance; only lio_bridge.py reads it. This is the GenZ-LIO counterpart of the
A-LOAM Hessian patch (patch_mapping_hessian.py): the same quantity (J^T W J of the registration residuals),
evaluated at the converged state of the scan.

Usage (inside the container, on a clone of https://github.com/cocel-postech/genz-lio):
    python3 patch_genz_information.py /root/genz_ws/src/genz-lio
Originals are kept as <file>.bak_info. Running it twice does nothing.
"""
import os
import shutil
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "/root/genz_ws/src/genz-lio"
F_HPP = os.path.join(root, "cpp/genz_lio/core/HybridMetricUpdate.hpp")
F_CPP = os.path.join(root, "cpp/genz_lio/core/HybridMetricUpdate.cpp")
F_RES = os.path.join(root, "cpp/genz_lio/core/GenZLIO.hpp")
F_LIO = os.path.join(root, "cpp/genz_lio/core/GenZLIO.cpp")
F_ROS = os.path.join(root, "ros/src/OdometryServer.cpp")
MARK = "GENZ_INFO_PATCH"


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


if all(MARK in open(p).read() for p in (F_HPP, F_CPP, F_RES, F_LIO, F_ROS)):
    print("already patched, nothing to do")
    sys.exit(0)

# 1. HybridMetricUpdate: keep the information of the last iteration
edit(F_HPP,
     "    const Stats &stats() const { return stats_; }",
     "    const Stats &stats() const { return stats_; }\n"
     "    // " + MARK + ": LiDAR-only information J^T R_inv J of the last iteration, [dp_W, dtheta_I]\n"
     "    const Eigen::Matrix<double, 6, 6> &information() const { return information_; }")
edit(F_HPP,
     "    Stats stats_;",
     "    Stats stats_;\n"
     "    Eigen::Matrix<double, 6, 6> information_ = Eigen::Matrix<double, 6, 6>::Zero();  // " + MARK)

edit(F_CPP,
     "    if (total < 1) {\n        data.valid = false;\n        return;\n    }",
     "    if (total < 1) {\n        information_.setZero();  // " + MARK + "\n        data.valid = false;\n        return;\n    }")
edit(F_CPP,
     "    fillPlaneRows(state, data);\n    if (point_count > 0) fillPointRows(state, data);\n}",
     "    fillPlaneRows(state, data);\n    if (point_count > 0) fillPointRows(state, data);\n"
     "    {   // " + MARK + ": R holds inverse variances (silenced rows have zero Jacobian)\n"
     "        const Eigen::MatrixXd J = data.h_x.leftCols(6);\n"
     "        information_ = J.transpose() * data.R.col(0).asDiagonal() * J;\n"
     "    }\n}")

# 2. Result carries it
edit(F_RES,
     "        bool update_rejected = false;",
     "        bool update_rejected = false;\n"
     "        // " + MARK + ": LiDAR-only information of the update, [dp_W, dtheta_I] (zero if none)\n"
     "        Eigen::Matrix<double, 6, 6> information = Eigen::Matrix<double, 6, 6>::Zero();")
edit(F_LIO,
     "    result.point_matches = update_.stats().point_matches;",
     "    result.point_matches = update_.stats().point_matches;\n"
     "    if (!result.update_rejected) result.information = update_.information();  // " + MARK)

# 3. ROS: put it into the odometry message
edit(F_ROS,
     "    odom.twist.twist.linear.z = result.velocity.z();\n    odom_pub_.publish(odom);",
     "    odom.twist.twist.linear.z = result.velocity.z();\n"
     "    // " + MARK + ": pose.covariance carries the LiDAR INFORMATION [dp_W, dtheta_I], row-major\n"
     "    for (int r = 0; r < 6; ++r)\n"
     "        for (int c = 0; c < 6; ++c) odom.pose.covariance[6 * r + c] = result.information(r, c);\n"
     "    odom_pub_.publish(odom);")
print("patched: information exported on /Odometry pose.covariance")
