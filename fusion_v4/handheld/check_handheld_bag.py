#!/usr/bin/env python3
"""Read-only check of the LVI-SAM Handheld bag before any run (11 Nov 2026). Prints what the pipeline needs and flags what is missing.
usage: python3 check_handheld_bag.py /path/handheld.bag          needs: pip install "rosbags==0.11.9" opencv-python-headless numpy
Checks: topics and counts and rates; duration; /points_raw (point count per scan, fields incl. ring/time); /imu_raw (rate, orientation present);
camera (compressed JPEG: size and channels; VINS-Mono needs RAW images); /gps/fix (count, status, horizontal / vertical covariance, gaps, span)."""
import sys
from pathlib import Path
import numpy as np
import cv2
from rosbags.highlevel import AnyReader

bag = Path(sys.argv[1])
NEED = {"/points_raw": "LiDAR (A-LOAM input, remapped from /velodyne_points)", "/imu_raw": "IMU (VINS-Mono imu_topic)",
        "/camera/image_raw/compressed": "camera (JPEG, must be republished to raw for VINS-Mono)", "/gps/fix": "only available ground-truth source"}
with AnyReader([bag]) as r:
    dur = r.duration / 1e9
    print("bag %s: %.1f s, %d messages, %d topics" % (bag.name, dur, r.message_count, len(r.topics)))
    for c in sorted(r.connections, key=lambda c: c.topic):
        print("  %-36s %-34s %8d msgs  %7.2f Hz" % (c.topic, c.msgtype, c.msgcount, c.msgcount / max(dur, 1e-9)))
    for t, why in NEED.items():
        print("%-8s %s  (%s)" % ("OK" if any(c.topic == t for c in r.connections) else "MISSING", t, why))
    first = {}
    gps = []
    for c, ts, raw in r.messages():
        if c.topic == "/gps/fix":
            m = r.deserialize(raw, c.msgtype)
            gps.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.latitude, m.longitude, m.altitude, m.status.status,
                        m.position_covariance[0], m.position_covariance[4], m.position_covariance[8]))
        elif c.topic not in first:
            first[c.topic] = (c, raw)
    if "/points_raw" in first:
        c, raw = first["/points_raw"]
        m = r.deserialize(raw, c.msgtype)
        print("\n/points_raw first scan: %d x %d points, fields %s, frame_id %s" % (m.height, m.width, [f.name for f in m.fields], m.header.frame_id))
        print("  ring field: %s (A-LOAM computes the ring itself, a ring field is not needed); time field: %s" %
              (any(f.name == "ring" for f in m.fields), any(f.name in ("time", "t") for f in m.fields)))
    if "/imu_raw" in first:
        c, raw = first["/imu_raw"]
        m = r.deserialize(raw, c.msgtype)
        print("/imu_raw frame_id %s, orientation_covariance[0] = %s (-1 means no orientation), first accel %s" %
              (m.header.frame_id, m.orientation_covariance[0], np.round([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z], 2)))
    if "/camera/image_raw/compressed" in first:
        c, raw = first["/camera/image_raw/compressed"]
        m = r.deserialize(raw, c.msgtype)
        img = cv2.imdecode(np.frombuffer(bytes(m.data), np.uint8), cv2.IMREAD_UNCHANGED)
        print("camera first frame: format %s, decoded %s, %d bytes compressed" % (m.format, None if img is None else (img.shape, str(img.dtype)), len(m.data)))
        if img is not None:
            per = img.size * img.itemsize
            n = r.topics["/camera/image_raw/compressed"].msgcount
            print("  raw size would be about %.1f GB for the whole bag (%d frames x %.2f MB): republish live instead of writing a raw bag" % (n * per / 1e9, n, per / 1e6))
    if gps:
        g = np.array(gps)
        gap = np.diff(g[:, 0])
        print("\n/gps/fix: %d fixes over %.1f s (%.2f Hz); status values %s" % (len(g), g[-1, 0] - g[0, 0], len(g) / max(g[-1, 0] - g[0, 0], 1e-9), sorted(set(g[:, 4].astype(int)))))
        print("  horizontal variance (m^2): median %.2f, 90th pct %.2f, max %.2f; vertical variance median %.1f" %
              (np.median(g[:, 5]), np.percentile(g[:, 5], 90), g[:, 5].max(), np.median(g[:, 7])))
        print("  gaps between fixes: median %.2f s, max %.1f s, %d gaps above 1 s" % (np.median(gap), gap.max(), (gap > 1.0).sum()))
        lat0, lon0 = np.radians(g[0, 1]), np.radians(g[0, 2])
        e = 6378137.0 * (np.radians(g[:, 2]) - lon0) * np.cos(lat0)
        n_ = 6378137.0 * (np.radians(g[:, 1]) - lat0)
        step = np.hypot(np.diff(e), np.diff(n_))
        print("  east-north extent %.0f x %.0f m, path %.0f m, steps above 5 m between fixes: %d" % (np.ptp(e), np.ptp(n_), step.sum(), (step > 5).sum()))
    else:
        print("\nno /gps/fix messages: there is no reference to score against")
