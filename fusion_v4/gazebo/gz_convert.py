#!/usr/bin/env python3
"""Turn a recorded Gazebo bag into a pipeline bag and a ground-truth file (runs inside switchslam_gpu_v2, needs rosbag + numpy).
usage: gz_convert.py <in.bag> <out.bag|-> <gt.txt> [ramp_seconds]
  out.bag   LiDAR, IMU and camera messages only (/gt/husky_pose is dropped); '-' writes only the ground truth.
  ramp_seconds  0 (default): the LiDAR is copied unchanged. > 0: the per-point 'time' field of /velodyne_points is REPLACED by a ramp over the
            azimuth, from 0 to ramp_seconds. Reason: Gazebo samples all rays at one instant and this plugin writes time = 0 for every point;
            a constant field makes GenZ-LIO rebuild the time from the azimuth (CloudConversion.cpp), i.e. it deskews as if the scan took
            0.1 s although it was instantaneous, adding a false correction in turns. A varying field over 0.1 ms keeps GenZ-LIO on the
            reported time and makes the implied motion during the sweep negligible.
  gt.txt    TUM format (t x y z qx qy qz qw, seconds, simulation clock = the header stamps of the sensors)."""
import sys
import numpy as np
import rosbag
src, dst, gtf = sys.argv[1:4]; ramp = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
TOP = ["/velodyne_points", "/imu/data", "/camera/image_raw", "/camera/camera_info"]
bag = rosbag.Bag(src); gt = []
out = rosbag.Bag(dst, "w") if dst != "-" else None
n = {t: 0 for t in TOP}; tr = None
for topic, msg, t in bag.read_messages(topics=TOP + ["/gt/husky_pose"]):
    if topic == "/gt/husky_pose":
        p, q = msg.pose.position, msg.pose.orientation
        gt.append((msg.header.stamp.to_sec(), p.x, p.y, p.z, q.x, q.y, q.z, q.w)); continue
    if out is None: continue
    if topic == "/velodyne_points" and ramp > 0:
        fo = {f.name: f.offset for f in msg.fields}
        for k in ("x", "y", "time"):
            if k not in fo: raise SystemExit("no '%s' field in /velodyne_points" % k)
        step = msg.point_step; npts = msg.width * msg.height
        arr = np.frombuffer(msg.data, dtype=np.uint8).copy()
        col = lambda name: np.ndarray((npts,), dtype="<f4", buffer=arr, offset=fo[name], strides=(step,))
        x, y, tv = col("x"), col("y"), col("time")
        if tr is None: tr = (float(np.nanmin(tv)), float(np.nanmax(tv)))
        az = np.arctan2(y, x)                                   # -pi .. pi
        tv[:] = ((az + np.pi) / (2 * np.pi) * ramp).astype("<f4")
        msg.data = arr.tobytes()
    out.write(topic, msg, t); n[topic] += 1
if out: out.close()
G = np.array(sorted(gt)); np.savetxt(gtf, G, fmt="%.6f", comments="# ", header="t x y z qx qy qz qw (Gazebo model pose of the Husky base_link, simulation clock)")
print("ground truth: %d poses, %.1f s, path %.1f m -> %s" % (len(G), G[-1, 0] - G[0, 0], np.sum(np.linalg.norm(np.diff(G[:, 1:4], axis=0), axis=1)), gtf))
if out: print("bag %s: %s; per-point time in the first scan before replacing it: %s s" % (dst, n, tr))
