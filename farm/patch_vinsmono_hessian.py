#!/usr/bin/env python3
path = "/root/catkin_ws/src/VINS-Mono/vins_estimator/src/estimator.cpp"

with open(path, "r") as f:
    content = f.read()

include_anchor = '#include "estimator.h"'
include_addition = include_anchor + '\n#include <std_msgs/Float64MultiArray.h>\n#include <ros/ros.h>'
assert include_anchor in content, "include anchor not found"
content = content.replace(include_anchor, include_addition, 1)

solve_anchor = "ceres::Solve(options, &problem, &summary);"
hessian_block = solve_anchor + """

    // --- Hv (visual Hessian, newest pose only) extraction ---
    {
        static ros::Publisher pubVinsMonoHessian;
        static bool pub_initialized = false;
        if (!pub_initialized) {
            ros::NodeHandle nh_hess;
            pubVinsMonoHessian = nh_hess.advertise<std_msgs::Float64MultiArray>("/vins_mono_hessian", 100);
            pub_initialized = true;
        }

        ceres::Problem::EvaluateOptions eval_options;
        eval_options.parameter_blocks.push_back(para_Pose[WINDOW_SIZE]);
        ceres::CRSMatrix jacobian_crs;
        double cost_val;
        problem.Evaluate(eval_options, &cost_val, nullptr, nullptr, &jacobian_crs);

        if (jacobian_crs.num_rows > 0 && jacobian_crs.num_cols == 6) {
            Eigen::MatrixXd Jv = Eigen::MatrixXd::Zero(jacobian_crs.num_rows, jacobian_crs.num_cols);
            for (int row = 0; row < jacobian_crs.num_rows; ++row) {
                for (int idx = jacobian_crs.rows[row]; idx < jacobian_crs.rows[row + 1]; ++idx) {
                    Jv(row, jacobian_crs.cols[idx]) = jacobian_crs.values[idx];
                }
            }
            Eigen::MatrixXd Hv = Jv.transpose() * Jv;

            std_msgs::Float64MultiArray hv_msg;
            hv_msg.data.resize(Hv.rows() * Hv.cols());
            for (int r = 0; r < Hv.rows(); ++r)
                for (int c = 0; c < Hv.cols(); ++c)
                    hv_msg.data[r * Hv.cols() + c] = Hv(r, c);
            pubVinsMonoHessian.publish(hv_msg);
        }
    }"""
assert solve_anchor in content, "solve anchor not found"
content = content.replace(solve_anchor, hessian_block, 1)

with open(path, "w") as f:
    f.write(content)

print("VINS-Mono Hessian patch applied successfully.")
