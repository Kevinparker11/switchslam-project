#!/usr/bin/env python3
"""lio_bridge: lets fusion_node_v2 run on GenZ-LIO instead of A-LOAM, with no change to the fusion node.

GenZ-LIO (patched with genz/patch_genz_information.py) publishes
  /Odometry          IMU pose in its odom frame; pose.covariance = LiDAR-only information [dp_W, dtheta_I] (row-major 6x6)
  /cloud_registered  the deskewed scan in the same odom frame
This node republishes them in the form fusion_node_v2 / keyframe_recorder already read from A-LOAM:
  /laser_hessian              Float64MultiArray, 36 + 2 values: H (6x6, [rotation, translation], LiDAR body frame,
                              rotation in A-LOAM's quaternion-tangent units) + [nan, number of nonzero rows unknown -> nan]
  /aft_mapped_to_init         LiDAR pose T_WL = T_WI * T_IL (frame camera_init)
  /velodyne_cloud_registered  the registered scan (frame camera_init)
The Hessian is published before the pose, as A-LOAM's patch did, so the node pairs each pose with its own H.

Frames. GenZ's Jacobian is w.r.t. x = [dp_W (world position), dtheta_I (IMU body rotation, right perturbation)].
The fusion node expects y = [dtheta_L, dt_L] (LiDAR body rotation and LiDAR body translation, right perturbation).
With R_WL = R_WI R_IL, p_WL = p_WI + R_WI t_IL:
  dtheta_L = R_IL^T dtheta_I
  dt_L     = R_WL^T (dp_W - R_WI [t_IL]x dtheta_I)
so y = M x and the information becomes H_y = M^-T H_x M^-1. fusion_core multiplies by D = diag(.5,.5,.5,1,1,1)
(A-LOAM quaternion tangent -> radians), so we publish H_q = D^-1 H_y D^-1 and fusion_core recovers H_y exactly.
Environment: EXTRINSIC_YAML (same file and format as fusion_node_v2; default SubT-MRS Multi Floor laser_to_imu).
"""
import os
import numpy as np

E = os.environ.get
T_LI = np.array([[0.999945562, 0.009074807, 0.005149763, 0.080],
                 [-0.009060897, 0.999955255, -0.002718066, 0.029],
                 [-0.005174199, 0.002671256, 0.999983046, 0.030],
                 [0, 0, 0, 1.0]])
if E("EXTRINSIC_YAML"):
    import yaml
    with open(E("EXTRINSIC_YAML")) as f:
        T_LI = np.array(yaml.safe_load(f.read().replace("%YAML 1.2", ""))["laser_to_imu"]["data"]).reshape(4, 4)
_U, _, _Vt = np.linalg.svd(T_LI[:3, :3])
R_IL, t_IL = _U @ _Vt, T_LI[:3, 3].copy()
D_INV = np.diag([2.0, 2.0, 2.0, 1.0, 1.0, 1.0])
EPS = 1e-6


def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def lidar_information(H_x, R_WI, R_il=None, t_il=None):
    """H_x: 6x6 information in [dp_W, dtheta_I]. Returns H_y in [dtheta_L, dt_L] (radians, metres)."""
    R_il = R_IL if R_il is None else R_il
    t_il = t_IL if t_il is None else t_il
    R_WL = R_WI @ R_il
    M = np.zeros((6, 6))
    M[0:3, 3:6] = R_il.T
    M[3:6, 0:3] = R_WL.T
    M[3:6, 3:6] = -R_WL.T @ R_WI @ skew(t_il)
    Mi = np.linalg.inv(M)
    H = Mi.T @ np.asarray(H_x, float) @ Mi
    return 0.5 * (H + H.T)


def aloam_units(H_y):
    """[rad, m] information -> the units fusion_core expects from A-LOAM (it applies D = D_INV^-1 on both sides)"""
    return D_INV @ H_y @ D_INV


def main():
    import rospy
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import PointCloud2
    from std_msgs.msg import Float64MultiArray
    import fusion_core as fc

    rospy.init_node("lio_bridge")
    pub_h = rospy.Publisher("/laser_hessian", Float64MultiArray, queue_size=50)
    pub_o = rospy.Publisher("/aft_mapped_to_init", Odometry, queue_size=50)
    pub_c = rospy.Publisher("/velodyne_cloud_registered", PointCloud2, queue_size=20)
    n = [0, 0]

    def odom_cb(msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        R_WI = fc.quat_to_R([q.x, q.y, q.z, q.w])
        p_WI = np.array([p.x, p.y, p.z])
        H_x = np.array(msg.pose.covariance, float).reshape(6, 6)
        n[0] += 1
        if np.allclose(H_x, 0) or not np.all(np.isfinite(H_x)):
            n[1] += 1                     # no LiDAR rows this scan: near-zero information, so W ~ 0 (VINS) when FUSED
            H_x = np.zeros((6, 6))
        # EPS keeps the Schur complements defined when a direction has no rows at all (e.g. floor only);
        # it is ~1e-9 of a single well-measured point, so it does not change any weight.
        H_pub = aloam_units(lidar_information(H_x, R_WI) + EPS * np.eye(6)).ravel()
        pub_h.publish(Float64MultiArray(data=list(H_pub) + [np.nan, np.nan]))
        R_WL = R_WI @ R_IL
        p_WL = p_WI + R_WI @ t_IL
        om = Odometry()
        om.header.stamp = msg.header.stamp
        om.header.frame_id = "camera_init"
        om.child_frame_id = "/aft_mapped"
        om.pose.pose.position.x, om.pose.pose.position.y, om.pose.pose.position.z = p_WL
        qx, qy, qz, qw = fc.R_to_quat(R_WL)
        om.pose.pose.orientation.x, om.pose.pose.orientation.y, om.pose.pose.orientation.z, om.pose.pose.orientation.w = qx, qy, qz, qw
        pub_o.publish(om)
        if n[0] % 500 == 1:
            rospy.loginfo("lio_bridge: %d poses relayed, %d without LiDAR information", n[0], n[1])

    def cloud_cb(msg):
        msg.header.frame_id = "camera_init"
        pub_c.publish(msg)

    # defaults = GenZ-LIO; iG-LIO (FRONT=iglio) sets BRIDGE_ODOM=/lio_odom BRIDGE_CLOUD=/current_scan
    odom_topic, cloud_topic = E("BRIDGE_ODOM", "/Odometry"), E("BRIDGE_CLOUD", "/cloud_registered")
    rospy.Subscriber(odom_topic, Odometry, odom_cb, queue_size=200)
    rospy.Subscriber(cloud_topic, PointCloud2, cloud_cb, queue_size=20, buff_size=2 ** 24)
    print("lio_bridge listening: %s, %s -> /aft_mapped_to_init, /laser_hessian, "
          "/velodyne_cloud_registered; t_IL = %s" % (odom_topic, cloud_topic, np.round(t_IL, 3)), flush=True)
    rospy.spin()


if __name__ == "__main__":
    main()
