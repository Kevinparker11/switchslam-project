#!/usr/bin/env python3
"""Does this sequence give stock LIO-SAM what it needs? Reads only the bag index and a few thousand IMU messages
(runs inside the liosam_stock image, which has the rosbag python module).

usage: preflight.py --imu TOPIC (--points TOPIC | --packets TOPIC) BAG [BAG ...]
Prints KEY=value lines (the runner reads these) and a short human summary.
  ORIENTATION  ok | missing | constant      judged on the quaternion (unit norm, changing, gravity along +z); a driver flag
               covariance[0] = -1 alone does not decide. missing/constant: stock LIO-SAM is not applicable
  RING         ok | missing | wrongtype     missing: not applicable
  TIME         ok | negative | missing | empty | wrongtype
  DENSE        yes | no                     no: the node would shut down; the adapter drops NaN points and sets the flag
  ADAPT_NAN, ADAPT_TIME  1 when the adapter is needed (negative time is shifted to start at 0)
"""
import argparse
import sys

import numpy as np
import rosbag

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import lio_inputs as li  # noqa: E402


def sample_imu(bags, topic, n=2000):
    q, c, a = [], [], []
    b = rosbag.Bag(bags[0])
    t0, t1 = b.get_start_time(), b.get_end_time()
    for start in (t0, t0 + 0.5 * (t1 - t0)):
        k = 0
        import rospy
        for _, m, _ in b.read_messages(topics=[topic], start_time=rospy.Time.from_sec(start)):
            q.append([m.orientation.x, m.orientation.y, m.orientation.z, m.orientation.w])
            c.append(m.orientation_covariance[0])
            a.append([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z])
            k += 1
            if k >= n:
                break
    return np.array(q), np.array(c), np.array(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imu", required=True)
    ap.add_argument("--points", default="")
    ap.add_argument("--packets", default="")
    ap.add_argument("bags", nargs="+")
    a = ap.parse_args()
    res = {}
    info = rosbag.Bag(a.bags[0]).get_type_and_topic_info().topics
    dur = rosbag.Bag(a.bags[0]).get_end_time() - rosbag.Bag(a.bags[0]).get_start_time()
    for name, tp in (("IMU", a.imu), ("LIDAR", a.points or a.packets)):
        if tp not in info:
            print("TOPIC_MISSING=%s (%s is not in %s)" % (name, tp, a.bags[0]))
            print("VERDICT=NOT_RUN")
            return 0
        res[name + "_HZ"] = "%.1f" % (info[tp].message_count / max(dur, 1e-6))
    q, c, acc = sample_imu(a.bags, a.imu)
    ov = li.orientation_verdict(q, c, acc)
    res["ORIENTATION"] = ov["status"]
    res["ORIENT_GRAVITY_ERR_DEG"] = "%.1f" % ov["gravity_err_deg"]
    res["ORIENT_FLAGGED_ABSENT_BY_DRIVER"] = int(ov["flagged_absent"])
    res["IMU_SAMPLES"] = ov["n"]
    res["ADAPT_NAN"] = 0
    res["ADAPT_TIME"] = 0
    if a.points:
        b = rosbag.Bag(a.bags[0])
        for _, m, _ in b.read_messages(topics=[a.points]):
            f = [(x.name, x.offset, x.datatype, x.count) for x in m.fields]
            r = li.cloud_report(f, m.point_step, m.data, m.is_dense, m.is_bigendian)
            res["POINTS_IN_FIRST_SCAN"] = r["points"]
            res["RING"] = r["ring"]
            res["TIME"] = r["time"]
            res["TIME_RANGE_S"] = "%.4f..%.4f" % (r["time_min"], r["time_max"])
            res["DENSE"] = "yes" if r["is_dense"] else "no"
            res["NAN_POINTS_FIRST_SCAN"] = r["nan_points"]
            res["ADAPT_NAN"] = int((not r["is_dense"]) or r["nan_points"] > 0)
            res["ADAPT_TIME"] = int(r["time"] == "negative")
            break
    else:
        # velodyne_pointcloud with model VLP16 writes ring and time (inside.sh logs the converted fields). The SIGN of the
        # time depends on which packet stamp the recorded scan header carries (lio_inputs.packet_time_report), so it is
        # read from the packets of the first 50 scans instead of assumed.
        f_off, l_off = [], []
        for _, m, _ in rosbag.Bag(a.bags[0]).read_messages(topics=[a.packets]):
            if m.packets:
                h = m.header.stamp.to_sec()
                f_off.append(m.packets[0].stamp.to_sec() - h)
                l_off.append(m.packets[-1].stamp.to_sec() - h)
            if len(f_off) >= 50:
                break
        pt = li.packet_time_report(f_off, l_off)
        res["RING"] = "ok"
        res["TIME"] = pt["time"]
        res["TIME_RANGE_S"] = "%.4f..%.4f" % (pt["time_min"], pt["time_max"])
        res["SCAN_HEADER_IS_PACKET"] = pt["header_is"]
        res["DENSE"] = "yes"
        res["ADAPT_TIME"] = int(pt["time"] == "negative")
        res["CONVERTED_FROM_PACKETS"] = a.packets
    for k, v in res.items():
        print("%s=%s" % (k, v))
    bad = []
    if res["ORIENTATION"] != "ok":
        bad.append("IMU orientation %s (LIO-SAM needs a 9-axis IMU)" % res["ORIENTATION"])
    if res["RING"] != "ok":
        bad.append("ring field %s" % res["RING"])
    if res["TIME"] in ("missing", "empty", "wrongtype") or str(res["TIME"]).startswith("wrongtype"):
        bad.append("per-point time %s (deskew would be off)" % res["TIME"])
    print("VERDICT=%s" % ("NOT_APPLICABLE: " + "; ".join(bad) if bad else "OK"))
    if res["ORIENT_FLAGGED_ABSENT_BY_DRIVER"] and res["ORIENTATION"] == "ok":
        print("NOTE=the driver sets orientation_covariance[0] = -1 (orientation not provided), but the quaternion is a unit "
              "quaternion that changes and puts gravity along +z (error %s deg). LIO-SAM ignores the covariance and reads the "
              "quaternion, so it is used as it is; how it is produced (e.g. a 6-axis filter with free yaw) is not stated by the bag."
              % res["ORIENT_GRAVITY_ERR_DEG"])
    if not bad and float(res["ORIENT_GRAVITY_ERR_DEG"]) > 15:
        print("NOTE=orientation does not put gravity along +z (error %s deg): check the orientation convention of this IMU"
              % res["ORIENT_GRAVITY_ERR_DEG"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
