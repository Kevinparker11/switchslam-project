#!/usr/bin/env python3
"""Read-only check of the start of a bag for iG-LIO: gyro/acc statistics of every IMU topic over the first 20 s (iG-LIO initialises
its gyro bias from the first IMU samples and assumes the platform is static), and the per-point time field of the first scan of
every PointCloud2 topic (unit: seconds or milliseconds decides whether time_scale 1000 is right).
usage (inside a ROS noetic container): python3 check_bag_start.py <bag>"""
import sys, math, struct, rosbag
FMT = {1: "b", 2: "B", 3: "h", 4: "H", 5: "i", 6: "I", 7: "f", 8: "d"}
SZ = {1: 1, 2: 1, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 8: 8}
TIMEY = ("time", "t", "timestamp", "offset_time", "time_offset", "ts")

def norm(v): return math.sqrt(sum(x * x for x in v))

bag = rosbag.Bag(sys.argv[1])
info = bag.get_type_and_topic_info()[1]
t0 = bag.get_start_time()
print("== %s | start %.3f | duration %.1f s" % (sys.argv[1], t0, bag.get_end_time() - t0))
for top in [t for t, v in info.items() if v.msg_type == "sensor_msgs/Imu"]:
    g = []; a = []; ts = []
    for _, m, t in bag.read_messages(topics=[top]):
        s = t.to_sec() - t0
        if s > 20: break
        g.append((m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z))
        a.append((m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z)); ts.append(s)
    if not g: continue
    n = len(g); mg = [sum(x[i] for x in g) / n for i in range(3)]; ma = [sum(x[i] for x in a) / n for i in range(3)]
    sg = [math.sqrt(sum((x[i] - mg[i]) ** 2 for x in g) / n) for i in range(3)]
    first = min(n, int(2 * n / max(ts[-1], 1e-9)))     # first ~2 s
    m2 = [sum(x[i] for x in g[:first]) / max(first, 1) for i in range(3)]
    print("IMU %s: %d samples in 20 s (%.0f Hz) | mean gyro %s |%.3f| rad/s | gyro std %s | max |gyro| %.2f | mean gyro of first 2 s %s |%.3f| | mean acc %s |%.2f|" % (
        top, n, n / max(ts[-1], 1e-9), [round(x, 4) for x in mg], norm(mg), [round(x, 3) for x in sg], max(norm(x) for x in g),
        [round(x, 4) for x in m2], norm(m2), [round(x, 3) for x in ma], norm(ma)))
for top in [t for t, v in info.items() if v.msg_type == "sensor_msgs/PointCloud2"]:
    stamps = []
    for k, (_, m, t) in enumerate(bag.read_messages(topics=[top])):
        stamps.append(m.header.stamp.to_sec())
        if k == 0:
            f0 = m
        if k >= 2: break
    print("LiDAR %s: %d x %d points, point_step %d, scan period %.3f s, fields %s" % (
        top, f0.width, f0.height, f0.point_step, (stamps[1] - stamps[0]) if len(stamps) > 1 else float("nan"),
        [(f.name, f.offset, f.datatype) for f in f0.fields]))
    for f in f0.fields:
        if f.name.lower() in TIMEY and f.datatype in FMT:
            vals = []; fmt = "<" + FMT[f.datatype]
            for i in range(0, f0.width * f0.height, 7):
                o = i * f0.point_step + f.offset
                vals.append(struct.unpack_from(fmt, f0.data, o)[0])
            print("   time field '%s': min %.6g max %.6g (a 0.1 s scan reads max ~0.1 if seconds, ~100 if milliseconds, ~1e8 if nanoseconds)" % (f.name, min(vals), max(vals)))
