#!/usr/bin/env python3
"""Publish the scan-to-MAP Hessian from A-LOAM's laserMapping.cpp on /mapping_hessian.

Message: std_msgs/Float64MultiArray with 38 values = H (6x6, row-major, [rotation(3), translation(3)],
Ceres EigenQuaternion tangent for rotation, world-frame perturbations) + [cost, number of residuals].
Same method as the existing patch_hessian.py for laserOdometry.cpp (problem.Evaluate after Solve).

Usage (inside the A-LOAM container):
    python3 patch_mapping_hessian.py [/root/catkin_ws/src/A-LOAM/src/laserMapping.cpp]
    cd /root/catkin_ws && catkin_make
The original file is kept as laserMapping.cpp.bak_mapping_hessian. Running it twice does nothing.
"""
import re
import shutil
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/root/catkin_ws/src/A-LOAM/src/laserMapping.cpp"
src = open(path).read()
if '"/mapping_hessian"' in src:
    print("already patched, nothing to do")
    sys.exit(0)
shutil.copy(path, path + ".bak_mapping_hessian")

# 1. include
anchor = "#include <ceres/ceres.h>"
assert src.count(anchor) == 1, "include anchor not found exactly once"
src = src.replace(anchor, anchor + "\n#include <std_msgs/Float64MultiArray.h>", 1)

# 2. global publisher, declared next to the existing global publishers (process() runs in its own thread)
m = re.search(r"^ros::Publisher\s+pubLaserCloudSurround[^\n]*;\s*$", src, flags=re.M)
assert m, "global publisher declaration line not found"
src = src[:m.end()] + "\nros::Publisher pubMappingHessian;" + src[m.end():]

# 3. advertise it next to /aft_mapped_to_init
m = re.search(r'^(\s*)pubOdomAftMapped\s*=\s*nh\.advertise<nav_msgs::Odometry>\("/aft_mapped_to_init",\s*100\);\s*$',
              src, flags=re.M)
assert m, "advertise line for /aft_mapped_to_init not found"
ind = m.group(1)
src = src[:m.end()] + "\n" + ind + 'pubMappingHessian = nh.advertise<std_msgs::Float64MultiArray>("/mapping_hessian", 100);' + src[m.end():]

# 4. evaluate J^T J after the mapping solve
anchor = "ceres::Solve(options, &problem, &summary);"
assert src.count(anchor) == 1, "ceres::Solve anchor not found exactly once in laserMapping.cpp"
block = anchor + """
					// --- scan-to-map Hessian for degeneracy-gated fusion (fusion_node_v2) ---
					{
						ceres::Problem::EvaluateOptions eval_options;
						eval_options.parameter_blocks.push_back(parameters);
						eval_options.parameter_blocks.push_back(parameters + 4);
						ceres::CRSMatrix jac;
						double cost_val = 0.0;
						problem.Evaluate(eval_options, &cost_val, nullptr, nullptr, &jac);
						Eigen::MatrixXd J = Eigen::MatrixXd::Zero(jac.num_rows, jac.num_cols);
						for (int r = 0; r < jac.num_rows; ++r)
							for (int idx = jac.rows[r]; idx < jac.rows[r + 1]; ++idx)
								J(r, jac.cols[idx]) = jac.values[idx];
						Eigen::MatrixXd Hm = J.transpose() * J;
						std_msgs::Float64MultiArray hm;
						hm.data.resize(Hm.rows() * Hm.cols() + 2);
						for (int r = 0; r < Hm.rows(); ++r)
							for (int c = 0; c < Hm.cols(); ++c)
								hm.data[r * Hm.cols() + c] = Hm(r, c);
						hm.data[Hm.rows() * Hm.cols()] = cost_val;
						hm.data[Hm.rows() * Hm.cols() + 1] = jac.num_rows;
						pubMappingHessian.publish(hm);
					}"""
src = src.replace(anchor, block, 1)
open(path, "w").write(src)
print("patched", path, "-> publishes /mapping_hessian (38 doubles). Now rebuild: cd /root/catkin_ws && catkin_make")
