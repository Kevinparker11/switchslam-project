#!/usr/bin/env python3
"""Cut a time segment of the LVI-SAM handheld bag and write it as a new ROS 1 bag with RAW images, because
VINS-Mono cannot read /camera/image_raw/compressed. Keeps /imu_raw and /points_raw byte for byte, decodes each JPEG
to sensor_msgs/Image on /camera/image_raw (same header), and drops /imu_correct and /gps/fix.
Nothing is changed in the data: only the image encoding.
usage: python3 make_raw_segment.py --bag handheld.bag --out OUTDIR/handheld_seg.bag [--start 0] [--duration 200]
needs: pip install "rosbags==0.11.9" opencv-python-headless numpy"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from rosbags.highlevel import AnyReader
from rosbags.rosbag1 import Writer
from rosbags.typesys import Stores, get_typestore

ap = argparse.ArgumentParser()
ap.add_argument("--bag", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--start", type=float, default=0.0, help="seconds after the first message")
ap.add_argument("--duration", type=float, default=200.0)
a = ap.parse_args()

KEEP = {"/imu_raw", "/points_raw", "/camera/image_raw/compressed"}
ts = get_typestore(Stores.ROS1_NOETIC)
Image = ts.types["sensor_msgs/msg/Image"]
out = Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
if out.exists():
    out.unlink()
n = {}
with AnyReader([Path(a.bag)]) as r:
    t0 = r.start_time + int(a.start * 1e9)
    t1 = t0 + int(a.duration * 1e9)
    conns = [c for c in r.connections if c.topic in KEEP]
    with Writer(out) as w:
        wc = {}
        for c in conns:
            if c.topic == "/camera/image_raw/compressed":
                wc[c.topic] = w.add_connection("/camera/image_raw", "sensor_msgs/msg/Image", typestore=ts)
            else:
                wc[c.topic] = w.add_connection(c.topic, c.msgtype, typestore=ts)
        for c, t, raw in r.messages(connections=conns, start=t0, stop=t1):
            if c.topic == "/camera/image_raw/compressed":
                m = r.deserialize(raw, c.msgtype)
                img = cv2.imdecode(np.frombuffer(bytes(m.data), np.uint8), cv2.IMREAD_UNCHANGED)
                if img is None:
                    n["bad_jpeg"] = n.get("bad_jpeg", 0) + 1
                    continue
                enc = "mono8" if img.ndim == 2 else "bgr8"
                h, wd = img.shape[:2]
                msg = Image(header=m.header, height=h, width=wd, encoding=enc, is_bigendian=0,
                            step=wd * (1 if img.ndim == 2 else 3), data=np.ascontiguousarray(img).reshape(-1))
                w.write(wc[c.topic], t, ts.serialize_ros1(msg, "sensor_msgs/msg/Image"))
                n["image %s %dx%d" % (enc, wd, h)] = n.get("image %s %dx%d" % (enc, wd, h), 0) + 1
            else:
                w.write(wc[c.topic], t, raw)
                n[c.topic] = n.get(c.topic, 0) + 1
print("wrote", out, "%.1f MB" % (out.stat().st_size / 1e6))
for k, v in sorted(n.items()):
    print("  %-28s %d" % (k, v))
