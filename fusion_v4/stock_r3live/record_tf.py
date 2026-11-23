#!/usr/bin/env python3
"""Write the pose R3LIVE publishes on /tf (world -> /aft_mapped, the IMU pose after each LIO update) as TUM lines (t x y z qx qy qz qw).
Why /tf and not /aft_mapped_to_init: the tf is stamped with the scan end time (Measures.lidar_end_time), the Odometry message with the
wall-clock-of-the-bag at publication, which lags the scan by the processing time. Both carry the same pose.
usage: record_tf.py OUT.tum [CHILD_FRAME=aft_mapped]        stop with SIGINT"""
import sys


def tf_rows(transforms, child="aft_mapped"):
    """transforms: iterable of objects with .header.stamp.to_sec(), .child_frame_id, .transform.translation/.rotation (geometry_msgs/TransformStamped)."""
    rows = []
    for t in transforms:
        if t.child_frame_id.lstrip("/") != child:
            continue
        p, q = t.transform.translation, t.transform.rotation
        rows.append("%.6f %.6f %.6f %.6f %.8f %.8f %.8f %.8f" % (t.header.stamp.to_sec(), p.x, p.y, p.z, q.x, q.y, q.z, q.w))
    return rows


def main():
    import rospy
    from tf2_msgs.msg import TFMessage
    args = rospy.myargv()[1:]
    out = args[0]
    child = args[1] if len(args) > 1 else "aft_mapped"
    rospy.init_node("r3live_tf_recorder", disable_signals=False)
    f = open(out, "w", buffering=1)
    n = [0]

    def cb(m):
        for r in tf_rows(m.transforms, child):
            f.write(r + "\n")
            n[0] += 1

    rospy.Subscriber("/tf", TFMessage, cb, queue_size=2000)
    rospy.loginfo("recording /tf world->%s -> %s", child, out)
    rospy.spin()
    f.close()
    rospy.loginfo("recorded %d poses", n[0])


if __name__ == "__main__":
    main()
