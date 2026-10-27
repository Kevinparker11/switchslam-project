#!/usr/bin/env python3
"""
range_filter.py  -  republish a real LiDAR cloud with points beyond --max_range removed.

Used to run the SAME real recording as a shorter-range sensor (20 m, 10 m), which is how
DCReg induces degeneracy on real data. Nothing else is changed: same points, same
timestamps, same noise. Labels must be made with the same --range-max.

  python3 -u range_filter.py _in:=/multifloor/velodyne_points _out:=/degen/points _max_range:=20
  (_max_range:=0 passes everything through unchanged)
"""
import numpy as np
import rospy
from sensor_msgs.msg import PointCloud2


def main():
    rospy.init_node("range_filter")
    rin = rospy.get_param("~in", "/multifloor/velodyne_points")
    rout = rospy.get_param("~out", "/degen/points")
    rmax = float(rospy.get_param("~max_range", 0.0))
    pub = rospy.Publisher(rout, PointCloud2, queue_size=5)

    def cb(msg):
        if rmax <= 0:
            pub.publish(msg); return
        off = {f.name: f.offset for f in msg.fields}
        n = msg.width * msg.height
        raw = np.frombuffer(msg.data, dtype=np.uint8).reshape(n, msg.point_step)
        xyz = np.stack([raw[:, off[c]:off[c] + 4].copy().view("<f4")[:, 0] for c in "xyz"], 1)
        keep = np.isfinite(xyz).all(1) & (np.linalg.norm(xyz, axis=1) <= rmax)
        out = PointCloud2(header=msg.header, height=1, width=int(keep.sum()), fields=msg.fields,
                          is_bigendian=msg.is_bigendian, point_step=msg.point_step,
                          row_step=msg.point_step * int(keep.sum()), is_dense=True,
                          data=raw[keep].tobytes())
        pub.publish(out)

    rospy.Subscriber(rin, PointCloud2, cb, queue_size=5)
    rospy.loginfo("range_filter %s -> %s, max_range %.1f m", rin, rout, rmax)
    rospy.spin()


if __name__ == "__main__":
    main()
