#!/usr/bin/env python3
"""Read-only look at what the sensors deliver, in 5 s windows, to see what is in the data when a run starts to diverge.
Nothing is run, rescored or changed.

Two parts, run separately because the bag part needs ROS (use the liosam_stock image) and the ground-truth part does not:

  bag   (inside the image, like preflight.py):
        python3 stock_liosam/diag_inputs_window.py --imu /imu/data --lidar /velodyne_packets [--span 150] BAG [BAG ...]
        per window of the bag's header-stamp clock, counted from the first LiDAR message:
          imu n / max gap (ms) / max |gyro| (rad/s) / min and max |acc| (m/s^2) / largest step of the orientation quaternion (deg)
          scans / smallest and largest size (packets for velodyne_packets, points for a PointCloud2)
        A dropped IMU stretch shows as a large gap, a spike as a large gyro or acc, a lost stretch of LiDAR as fewer scans or smaller scans.
  gt    (on the host):
        python3 stock_liosam/diag_inputs_window.py --gt GT [--span 150]
        per window counted from the first ground-truth stamp: mean speed, path, and the total change of heading (deg), which says
        where the robot slows, stops or turns.
t_rel of the two parts differs by under 1 s (first LiDAR stamp against first ground-truth stamp); diag_error_time.py counts from the
first pose inside the ground-truth span."""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lio_inputs as li  # noqa: E402


def _windows(t_rel, window, span):
    n = int(np.ceil(span / window))
    return [(k * window, (k + 1) * window, (t_rel >= k * window) & (t_rel < (k + 1) * window)) for k in range(n)]


def quat_step_deg(q):
    """angle (deg) between consecutive unit quaternions (N,4) -> (N-1,)"""
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    d = np.abs(np.sum(q[1:] * q[:-1], axis=1))
    return np.degrees(2.0 * np.arccos(np.clip(d, -1.0, 1.0)))


def imu_windows(t, gyro, acc, quat, t0, window=5.0, span=150.0):
    """rows (t_rel, n, max_gap_ms, gyro_max, acc_min, acc_max, ori_step_max_deg); the gap of a window includes the gap to the previous sample."""
    o = np.argsort(t)
    t, gyro, acc, quat = t[o], gyro[o], acc[o], quat[o]
    gap = np.r_[0.0, np.diff(t)]
    step = np.r_[0.0, quat_step_deg(quat)] if len(t) > 1 else np.zeros(len(t))
    gn, an = np.linalg.norm(gyro, axis=1), np.linalg.norm(acc, axis=1)
    rows = []
    for a, _, m in _windows(t - t0, window, span):
        if m.sum() == 0:
            rows.append((a, 0, float("nan"), float("nan"), float("nan"), float("nan"), float("nan")))
            continue
        rows.append((a, int(m.sum()), 1000.0 * float(gap[m].max()), float(gn[m].max()), float(an[m].min()), float(an[m].max()),
                     float(step[m].max())))
    return rows


def spike_samples(t, acc, gyro, t0, thresh, limit=40):
    """IMU samples whose |acc| is above thresh (m/s^2), in time order: (t_rel, |acc|, |gyro|), at most limit rows; also returns the total count."""
    o = np.argsort(t)
    t, acc, gyro = t[o], acc[o], gyro[o]
    an = np.linalg.norm(acc, axis=1)
    idx = np.where(an > thresh)[0]
    return [(float(t[i] - t0), float(an[i]), float(np.linalg.norm(gyro[i]))) for i in idx[:limit]], int(len(idx))


def lidar_windows(t, size, t0, window=5.0, span=150.0):
    """rows (t_rel, scans, smallest size, largest size)"""
    rows = []
    for a, _, m in _windows(t - t0, window, span):
        rows.append((a, int(m.sum()), int(size[m].min()) if m.any() else 0, int(size[m].max()) if m.any() else 0))
    return rows


def gt_windows(gt_t, gt_p, window=5.0, span=150.0):
    """rows (t_rel, mean speed, path, turn_deg): turn = sum of the absolute heading changes between 1 s chords longer than 0.3 m."""
    t0 = gt_t[0]
    rows = []
    for a, b, _ in _windows(gt_t - t0, window, span):
        grid = t0 + np.arange(a, b + 1e-9, 1.0)
        if grid[-1] > gt_t[-1]:
            break
        p = np.stack([np.interp(grid, gt_t, gt_p[:, i]) for i in range(3)], 1)
        ch = np.diff(p[:, :2], axis=0)
        L = np.linalg.norm(ch, axis=1)
        path = float(np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1)))
        h = np.arctan2(ch[L > 0.3, 1], ch[L > 0.3, 0])
        dh = np.angle(np.exp(1j * np.diff(h))) if len(h) > 1 else np.zeros(0)
        rows.append((a, path / (b - a), path, float(np.degrees(np.abs(dh).sum()))))
    return rows


def read_bag(bags, imu_topic, lidar_topic, span):
    import rosbag
    imu_t, g, ac, q, li_t, li_n, f_off, l_off, cov0 = [], [], [], [], [], [], [], [], []
    start = None
    for path in bags:
        b = rosbag.Bag(path)
        if start is None:
            start = b.get_start_time()
        for topic, m, rt in b.read_messages(topics=[imu_topic, lidar_topic]):
            if rt.to_sec() > start + span + 20.0:
                break
            if topic == imu_topic:
                imu_t.append(m.header.stamp.to_sec())
                g.append([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])
                ac.append([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z])
                q.append([m.orientation.x, m.orientation.y, m.orientation.z, m.orientation.w])
                cov0.append(m.orientation_covariance[0])
            else:
                li_t.append(m.header.stamp.to_sec())
                li_n.append(len(m.packets) if hasattr(m, "packets") else int(m.width) * int(m.height))
                if hasattr(m, "packets") and m.packets:
                    f_off.append(m.packets[0].stamp.to_sec() - li_t[-1])
                    l_off.append(m.packets[-1].stamp.to_sec() - li_t[-1])
        b.close()
    return (np.array(imu_t), np.array(g), np.array(ac), np.array(q), np.array(li_t), np.array(li_n, dtype=int),
            np.array(f_off), np.array(l_off), np.array(cov0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bags", nargs="*")
    ap.add_argument("--imu", default="")
    ap.add_argument("--lidar", default="")
    ap.add_argument("--gt", default="")
    ap.add_argument("--span", type=float, default=150.0)
    ap.add_argument("--window", type=float, default=5.0)
    ap.add_argument("--spikes", type=float, default=0.0, help="also list the IMU samples with |acc| above this many m/s^2 (e.g. 40)")
    a = ap.parse_args()
    if a.bags:
        if not (a.imu and a.lidar):
            ap.error("--imu and --lidar are needed with a bag")
        it, g, ac, q, lt, ln, fo, lo, c0 = read_bag(a.bags, a.imu, a.lidar, a.span)
        if len(lt) == 0 or len(it) < 2:
            print("no messages read: imu %d, lidar %d" % (len(it), len(lt)))
            return 1
        t0 = float(lt.min())
        print("t0 = first LiDAR header stamp %.2f; IMU messages read %d, LiDAR messages read %d" % (t0, len(it), len(lt)))
        st = li.stamp_report(it)
        print("IMU stamps: rate %.1f Hz, dt median %.2f ms, max %.1f ms, non-increasing %d, gaps over 3x median %d" % (
            st.get("rate_hz", float("nan")), st.get("dt_median_ms", float("nan")), st.get("dt_max_ms", float("nan")),
            st.get("nonincreasing", -1), st.get("gaps_over_3x", -1)))
        k = min(400, len(it))
        an = np.linalg.norm(ac[:k], axis=1)
        ov = li.orientation_verdict(q, c0, ac)
        print("IMU first %d samples: |acc| median %.3f m/s^2 (LIO-SAM imuGravity 9.80511), orientation %s, gravity from the "
              "orientation vs from the accelerometer differ by %.2f deg" % (k, float(np.median(an)), ov["status"], ov["gravity_err_deg"]))
        if len(fo):
            pt = li.packet_time_report(fo, lo)
            print("scan header = %s packet over %d scans; per-point time from velodyne_pointcloud %.4f..%.4f s -> %s" % (
                pt["header_is"], pt["n"], pt["time_min"], pt["time_max"],
                "LIO-SAM deskew works" if pt["time"] == "ok" else "NEGATIVE: LIO-SAM deskew is off unless the time is shifted"))
        ir = imu_windows(it, g, ac, q, t0, a.window, a.span)
        lr = lidar_windows(lt, ln, t0, a.window, a.span)
        print("%7s | %5s %8s %9s %7s %7s %9s | %5s %5s %5s" % ("t_rel_s", "imu_n", "gap_ms", "gyro_max", "acc_min", "acc_max", "ori_deg", "scans", "smin", "smax"))
        for x, y in zip(ir, lr):
            print("%7.0f | %5d %8.1f %9.2f %7.2f %7.2f %9.3f | %5d %5d %5d" % (x[0], x[1], x[2], x[3], x[4], x[5], x[6], y[1], y[2], y[3]))
        if a.spikes > 0:
            rows, total = spike_samples(it, ac, g, t0, a.spikes)
            print("IMU samples with |acc| above %.0f m/s^2: %d (first %d shown); t_rel from the first LiDAR stamp" % (a.spikes, total, len(rows)))
            for r in rows:
                print("   t_rel %8.3f s   |acc| %7.1f m/s^2   |gyro| %5.2f rad/s" % r)
    if a.gt:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        import v2_tools as vt
        gt_t, gt_p = vt.load_gt(a.gt)
        print("ground truth from %.2f, %d poses" % (gt_t[0], len(gt_t)))
        print("%7s | %9s %8s %9s" % ("t_rel_s", "speed_m_s", "path_m", "turn_deg"))
        for r in gt_windows(gt_t, gt_p, a.window, a.span):
            print("%7.0f | %9.2f %8.1f %9.1f" % r)
    if not a.bags and not a.gt:
        ap.error("give a bag (with --imu and --lidar) or --gt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
