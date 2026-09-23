#!/usr/bin/env python3
path = "/root/catkin_ws/src/A-LOAM/src/laserOdometry.cpp"

with open(path, "r") as f:
    content = f.read()

include_anchor = "#include <cmath>"
include_addition = include_anchor + "\n#include <std_msgs/Float64MultiArray.h>"
assert include_anchor in content, "include anchor not found"
content = content.replace(include_anchor, include_addition, 1)

pub_anchor = 'ros::Publisher pubLaserPath = nh.advertise<nav_msgs::Path>("/laser_odom_path", 100);'
pub_addition = pub_anchor + '\n    ros::Publisher pubLaserHessian = nh.advertise<std_msgs::Float64MultiArray>("/laser_hessian", 100);'
assert pub_anchor in content, "publisher anchor not found"
content = content.replace(pub_anchor, pub_addition, 1)

solve_anchor = "ceres::Solve(options, &problem, &summary);"
hessian_block = solve_anchor + """

                    // --- Hessian (H_l) extraction for degeneracy detection ---
                    {
                        ceres::Problem::EvaluateOptions eval_options;
                        eval_options.parameter_blocks.push_back(para_q);
                        eval_options.parameter_blocks.push_back(para_t);
                        ceres::CRSMatrix jacobian_crs;
                        double cost_val;
                        problem.Evaluate(eval_options, &cost_val, nullptr, nullptr, &jacobian_crs);

                        Eigen::MatrixXd J = Eigen::MatrixXd::Zero(jacobian_crs.num_rows, jacobian_crs.num_cols);
                        for (int row = 0; row < jacobian_crs.num_rows; ++row) {
                            for (int idx = jacobian_crs.rows[row]; idx < jacobian_crs.rows[row + 1]; ++idx) {
                                J(row, jacobian_crs.cols[idx]) = jacobian_crs.values[idx];
                            }
                        }
                        Eigen::MatrixXd H_l = J.transpose() * J;

                        std_msgs::Float64MultiArray hessian_msg;
                        hessian_msg.data.resize(H_l.rows() * H_l.cols());
                        for (int r = 0; r < H_l.rows(); ++r)
                            for (int c = 0; c < H_l.cols(); ++c)
                                hessian_msg.data[r * H_l.cols() + c] = H_l(r, c);
                        pubLaserHessian.publish(hessian_msg);
                    }"""
assert solve_anchor in content, "solve anchor not found"
content = content.replace(solve_anchor, hessian_block, 1)

with open(path, "w") as f:
    f.write(content)

print("Patch applied successfully.")
