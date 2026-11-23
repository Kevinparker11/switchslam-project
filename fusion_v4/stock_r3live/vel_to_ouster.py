#!/usr/bin/env python3
"""Container-only input conversion for stock R3LIVE: a Velodyne cloud (x y z intensity ring time) becomes the field layout of an Ouster cloud,
the one non-Livox format its front end reads (its Velodyne handler is an empty stub, `velo16_handler { // TODO }`).
No coordinate is changed and no point is dropped or added. Fields written (Ouster names and types, as the R3LIVE front end's
ouster_ros::Point expects): x y z float32, intensity float32, t uint32 = per-point time in nanoseconds from the scan start,
reflectivity uint16 = intensity, ring uint8 = ring, ambient uint16 = 0, range uint32 = distance in mm.
Run after cloud_adapter.py (NaN removed, time starts at 0).   usage: vel_to_ouster.py IN_TOPIC OUT_TOPIC   (OUT_TOPIC is /os_cloud_node/points)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stock_liosam"))
import lio_inputs as li  # noqa: E402

OUT_DTYPE = np.dtype({"names": ["x", "y", "z", "intensity", "t", "reflectivity", "ring", "ambient", "range"],
                      "formats": ["<f4", "<f4", "<f4", "<f4", "<u4", "<u2", "u1", "<u2", "<u4"],
                      "offsets": [0, 4, 8, 12, 16, 20, 22, 24, 28], "itemsize": 32})
# sensor_msgs/PointField datatypes: INT8=1 UINT8=2 INT16=3 UINT16=4 INT32=5 UINT32=6 FLOAT32=7 FLOAT64=8
OUT_FIELDS = [("x", 0, 7), ("y", 4, 7), ("z", 8, 7), ("intensity", 12, 7), ("t", 16, 6), ("reflectivity", 20, 4),
              ("ring", 22, 2), ("ambient", 24, 4), ("range", 28, 6)]


def convert(fields, point_step, data, big_endian=False):
    """Velodyne cloud message data -> (bytes in OUT_DTYPE layout, number of points, number of negative times clipped to 0)."""
    a = li.cloud_to_array(fields, point_step, data, big_endian)
    names = a.dtype.names
    for need in ("x", "y", "z", "time"):
        if need not in names:
            raise ValueError("cloud has no field '%s'" % need)
    out = np.zeros(a.size, dtype=OUT_DTYPE)
    x, y, z = (a[k].astype(np.float32) for k in ("x", "y", "z"))
    out["x"], out["y"], out["z"] = x, y, z
    inten = a["intensity"].astype(np.float64) if "intensity" in names else np.zeros(a.size)
    out["intensity"] = inten
    out["reflectivity"] = np.clip(np.rint(inten), 0, 65535)
    tt = a["time"].astype(np.float64)
    neg = int((tt < 0).sum())
    out["t"] = np.rint(np.clip(tt, 0, None) * 1e9)
    out["ring"] = np.clip(a["ring"].astype(np.int64), 0, 255) if "ring" in names else 0     # R3LIVE's Ouster path never reads ring
    out["range"] = np.clip(np.rint(np.sqrt(x.astype(np.float64) ** 2 + y.astype(np.float64) ** 2 + z.astype(np.float64) ** 2) * 1000.0), 0, 2 ** 32 - 1)
    return out.tobytes(), int(a.size), neg


def main():
    import rospy
    from sensor_msgs.msg import PointCloud2, PointField
    src, dst = rospy.myargv()[1:3]
    rospy.init_node("vel_to_ouster")
    pub = rospy.Publisher(dst, PointCloud2, queue_size=50)
    st = {"n": 0, "neg": 0}

    def cb(m):
        f = [(x.name, x.offset, x.datatype, x.count) for x in m.fields]
        data, n, neg = convert(f, m.point_step, m.data, m.is_bigendian)
        out = PointCloud2()
        out.header = m.header
        out.height, out.width = 1, n
        out.fields = [PointField(name=k, offset=o, datatype=d, count=1) for k, o, d in OUT_FIELDS]
        out.is_bigendian, out.point_step, out.row_step, out.data, out.is_dense = False, 32, 32 * n, data, True
        pub.publish(out)
        st["n"] += 1
        st["neg"] += neg

    rospy.Subscriber(src, PointCloud2, cb, queue_size=50)
    rospy.loginfo("vel_to_ouster %s -> %s", src, dst)
    rospy.spin()
    rospy.loginfo("vel_to_ouster done: %d clouds, %d negative times clipped to 0", st["n"], st["neg"])


if __name__ == "__main__":
    main()
