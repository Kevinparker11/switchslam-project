#!/usr/bin/env python3
"""Turn a recorded Gazebo bag into a pipeline bag and a ground-truth file (runs inside switchslam_gpu_v2, needs rosbag + numpy).
usage: gz_convert.py <in.bag> <out.bag|-> <gt.txt> [time_scale]
  out.bag   LiDAR, IMU and camera messages only (/gt/husky_pose is dropped). With time_scale != 1 the per-point 'time' field of
            /velodyne_points is multiplied by it. Gazebo samples all rays at one instant, but the plugin writes a time that grows with the
            azimuth (0 to 0.1 s); GenZ-LIO would deskew with it and add a false correction in turns. A scale of 1e-3 makes the implied
            sweep 0.1 ms, so the correction vanishes while the field stays 'varying' (a constant field makes GenZ-LIO reconstruct the
            time from the azimuth, which is the same false correction). '-' as out.bag writes only the ground truth.
  gt.txt    TUM format (t x y z qx qy qz qw, seconds, simulation clock = the header stamps of the sensors)."""
import sys
import numpy as np
import rosbag
src, dst, gtf = sys.argv[1:4]; scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
TOP = ["/velodyne_points", "/imu/data", "/camera/image_raw", "/camera/camera_info"]
bag = rosbag.Bag(src); gt = []
out = rosbag.Bag(dst, "w") if dst != "-" else None
n = {t: 0 for t in TOP}; tr = None
for topic, msg, t in bag.read_messages(topics=TOP + ["/gt/husky_pose"]):
    if topic == "/gt/husky_pose":
        p, q = msg.pose.position, msg.pose.orientation
        gt.append((msg.header.stamp.to_sec(), p.x, p.y, p.z, q.x, q.y, q.z, q.w)); continue
    if out is None: continue
    if topic == "/velodyne_points" and scale != 1.0:
        f = [f for f in msg.fields if f.name == "time"]
        if not f: raise SystemExit("no 'time' field in /velodyne_points")
        off, step = f[0].offset, msg.point_step; npts = msg.width * msg.height
        arr = np.frombuffer(msg.data, dtype=np.uint8).copy()
        tv = np.ndarray((npts,), dtype="<f4", buffer=arr, offset=off, strides=(step,))
        if tr is None: tr = (float(np.nanmin(tv)), float(np.nanmax(tv)))
        tv *= np.float32(scale); msg.data = arr.tobytes()
    out.write(topic, msg, t); n[topic] += 1
if out: out.close()
G = np.array(sorted(gt)); np.savetxt(gtf, G, fmt="%.6f", comments="# ", header="t x y z qx qy qz qw (Gazebo model pose of the Husky base_link, simulation clock)")
print("ground truth: %d poses, %.1f s, path %.1f m -> %s" % (len(G), G[-1, 0] - G[0, 0], np.sum(np.linalg.norm(np.diff(G[:, 1:4], axis=0), axis=1)), gtf))
if out: print("bag %s: %s; per-point time before scaling: %s s" % (dst, n, tr))
