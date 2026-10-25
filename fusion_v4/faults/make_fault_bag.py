#!/usr/bin/env python3
"""Rewrite a recorded sequence with sensor outages at fixed, pre-registered times (fault injection on real data).

usage (inside a ROS noetic container):
  python3 make_fault_bag.py --fault C10|C30|L10|L30|none --out <dir> <bag1> [<bag2> ...]      (bags in time order)
  C<s> = every camera topic (Image, CompressedImage, CameraInfo) is dropped for s seconds, L<s> = every LiDAR topic (PointCloud2, VelodyneScan)
  is dropped for s seconds; IMU and everything else are copied untouched; none = copy only (control for the rewrite itself).
Window rule (fixed before any data was looked at; fractions of the whole sequence span D = last - first message time, from the first message):
  10 s outages:  3 windows starting at 0.30 D, 0.55 D, 0.80 D        other durations: 2 windows starting at 0.40 D and 0.75 D
Messages are copied raw (no deserialisation) with their connection headers, so latched topics and message types are unchanged.
Writes <out>/<same file names> and <out>/fault_manifest.json (windows in bag time and seconds from the start, dropped counts per topic)."""
import argparse, json, os, sys

CAMERA_TYPES = {"sensor_msgs/Image", "sensor_msgs/CompressedImage", "sensor_msgs/CameraInfo"}
LIDAR_TYPES = {"sensor_msgs/PointCloud2", "velodyne_msgs/VelodyneScan"}


def windows(fault, t0, t1):
    """list of (start, end) in bag time for a fault code such as 'C10' ('none' gives [])."""
    if fault == "none":
        return []
    kind, dur = fault[0], float(fault[1:])
    assert kind in "CL" and dur > 0, "fault must be C<s>, L<s> or none"
    d = t1 - t0
    fr = (0.30, 0.55, 0.80) if dur <= 10 else (0.40, 0.75)
    return [(t0 + f * d, t0 + f * d + dur) for f in fr]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fault", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("bags", nargs="+")
    a = ap.parse_args(argv)
    import rosbag
    types, t0, t1 = {}, None, None
    for p in a.bags:
        with rosbag.Bag(p) as b:
            for topic, info in b.get_type_and_topic_info().topics.items():
                types[topic] = info.msg_type
            s, e = b.get_start_time(), b.get_end_time()
            t0 = s if t0 is None else min(t0, s)
            t1 = e if t1 is None else max(t1, e)
    kind = a.fault[0] if a.fault != "none" else None
    want = CAMERA_TYPES if kind == "C" else LIDAR_TYPES if kind == "L" else set()
    drop_topics = sorted(t for t, ty in types.items() if ty in want)
    win = windows(a.fault, t0, t1)
    print("sequence span %.1f s, topics dropped: %s" % (t1 - t0, drop_topics or "-"))
    for w in win:
        print("  window %.1f s .. %.1f s after the start (%.0f s long)" % (w[0] - t0, w[1] - t0, w[1] - w[0]))
    if any(w1 > t1 for w0, w1 in win):
        print("ERROR: a window ends after the last message (sequence too short for %s)" % a.fault)
        return 4
    if a.fault != "none" and not drop_topics:
        print("ERROR: no topic of the requested sensor type in these bags: %s" % types)
        return 2
    os.makedirs(a.out, exist_ok=True)
    dropped = {t: 0 for t in drop_topics}
    kept = {t: 0 for t in drop_topics}
    ds = set(drop_topics)
    for p in a.bags:
        outp = os.path.join(a.out, os.path.basename(p))
        with rosbag.Bag(p) as src, rosbag.Bag(outp, "w", compression="none") as dst:
            try:
                it = src.read_messages(raw=True, return_connection_header=True)
                first = True
            except TypeError:
                it = None
            if it is None:
                it = ((tp, m, t, None) for tp, m, t in src.read_messages(raw=True))
            for topic, msg, t, hdr in it:
                ts = t.to_sec()
                if topic in ds and any(w0 <= ts < w1 for w0, w1 in win):
                    dropped[topic] += 1
                    continue
                if topic in ds:
                    kept[topic] += 1
                if hdr is None:
                    dst.write(topic, msg, t, raw=True)
                else:
                    dst.write(topic, msg, t, raw=True, connection_header=hdr)
        print("wrote", outp)
    man = {"fault": a.fault, "t0": t0, "t1": t1, "windows_abs": win, "windows_rel": [[w0 - t0, w1 - t0] for w0, w1 in win],
           "dropped_topics": drop_topics, "dropped": dropped, "kept": kept, "types": types}
    json.dump(man, open(os.path.join(a.out, "fault_manifest.json"), "w"), indent=1)
    print("dropped messages:", dropped, " kept:", kept)
    if a.fault != "none" and sum(dropped.values()) == 0:
        print("ERROR: nothing was dropped")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
