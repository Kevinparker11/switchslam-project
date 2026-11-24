#!/usr/bin/env python3
"""Container-only input conversion for stock R2LIVE: a Velodyne cloud (x y z intensity ring time) becomes a cloud with the fields the
R2LIVE LiDAR front end reads into its point type (pcl::PointXYZINormal): x y z intensity and `curvature` = the point's time in
milliseconds from the scan start. R2LIVE's LIO takes the scan end time from the LAST point's curvature and de-skews with it; the Livox
handlers fill it from the point's offset_time, its Velodyne and Ouster handlers never fill it (scan end would equal scan start). The cloud
goes to /os1_cloud_node/points, the input of R2LIVE's Ouster handler (lidar_type 3), which copies whole points and so keeps curvature.
No coordinate changes and no point is added or dropped; the points are put in ascending time order (a permutation) so the last point is the
latest, as for a Livox scan. Run after cloud_adapter.py (NaN removed, time starts at 0).
usage: vel_to_r2live.py IN_TOPIC OUT_TOPIC"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stock_liosam"))
import lio_inputs as li  # noqa: E402

OUT_DTYPE = np.dtype({"names": ["x", "y", "z", "intensity", "curvature"], "formats": ["<f4"] * 5, "offsets": [0, 4, 8, 12, 16], "itemsize": 20})
OUT_FIELDS = [("x", 0), ("y", 4), ("z", 8), ("intensity", 12), ("curvature", 16)]      # all FLOAT32 (datatype 7)


def convert(fields, point_step, data, big_endian=False):
    """-> (bytes in OUT_DTYPE layout, number of points, number of negative times clipped to 0)."""
    a = li.cloud_to_array(fields, point_step, data, big_endian)
    names = a.dtype.names
    for need in ("x", "y", "z", "time"):
        if need not in names:
            raise ValueError("cloud has no field '%s'" % need)
    t = a["time"].astype(np.float64)
    neg = int((t < 0).sum())
    t = np.clip(t, 0, None)
    order = np.argsort(t, kind="stable")
    out = np.zeros(a.size, dtype=OUT_DTYPE)
    for k in ("x", "y", "z"):
        out[k] = a[k][order]
    out["intensity"] = a["intensity"][order] if "intensity" in names else 0.0
    out["curvature"] = (t[order] * 1000.0).astype(np.float32)
    return out.tobytes(), int(a.size), neg


def main():
    import rospy
    from sensor_msgs.msg import PointCloud2, PointField
    src, dst = rospy.myargv()[1:3]
    rospy.init_node("vel_to_r2live")
    pub = rospy.Publisher(dst, PointCloud2, queue_size=50)
    st = {"n": 0, "neg": 0}

    def cb(m):
        f = [(x.name, x.offset, x.datatype, x.count) for x in m.fields]
        data, n, neg = convert(f, m.point_step, m.data, m.is_bigendian)
        out = PointCloud2()
        out.header = m.header
        out.height, out.width = 1, n
        out.fields = [PointField(name=k, offset=o, datatype=7, count=1) for k, o in OUT_FIELDS]
        out.is_bigendian, out.point_step, out.row_step, out.data, out.is_dense = False, 20, 20 * n, data, True
        pub.publish(out)
        st["n"] += 1
        st["neg"] += neg

    rospy.Subscriber(src, PointCloud2, cb, queue_size=50)
    rospy.loginfo("vel_to_r2live %s -> %s", src, dst)
    rospy.spin()
    rospy.loginfo("vel_to_r2live done: %d clouds, %d negative times clipped to 0", st["n"], st["neg"])


if __name__ == "__main__":
    main()
