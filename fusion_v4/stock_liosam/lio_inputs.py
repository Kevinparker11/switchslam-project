#!/usr/bin/env python3
"""Pure-numpy helpers shared by preflight.py and cloud_adapter.py (no ROS import, so they can be tested anywhere).

What stock LIO-SAM needs from a sequence (original source, include/utility.h and src/imageProjection.cpp):
  IMU    roll/pitch/yaw in sensor_msgs/Imu.orientation (9-axis); used for the initial attitude and a small roll/pitch weight
  cloud  float32 x y z intensity, uint16 ring, float32 time (seconds from the scan start, >= 0); is_dense must be true
         (the node shuts down on a cloud with is_dense == false, and without ring)
"""
import numpy as np

_DT = {1: "i1", 2: "u1", 3: "i2", 4: "u2", 5: "i4", 6: "u4", 7: "f4", 8: "f8"}


def cloud_dtype(fields, point_step, big_endian=False):
    """fields: iterable of (name, offset, datatype, count). Returns a structured dtype with the message's own layout."""
    names, formats, offsets = [], [], []
    pre = ">" if big_endian else "<"
    for name, off, dt, cnt in fields:
        if dt not in _DT:
            continue
        names.append(name)
        formats.append(pre + _DT[dt] if cnt <= 1 else (pre + _DT[dt], cnt))
        offsets.append(off)
    return np.dtype({"names": names, "formats": formats, "offsets": offsets, "itemsize": point_step})


def cloud_to_array(fields, point_step, data, big_endian=False):
    return np.frombuffer(bytes(data), dtype=cloud_dtype(fields, point_step, big_endian))


def cloud_report(fields, point_step, data, is_dense, big_endian=False):
    """What preflight prints about the first cloud of a bag."""
    fl = {f[0]: f for f in fields}
    arr = cloud_to_array(fields, point_step, data, big_endian)
    r = {"points": int(arr.size), "is_dense": bool(is_dense)}
    xyz_ok = all(k in fl for k in ("x", "y", "z"))
    r["nan_points"] = int((~np.isfinite(np.stack([arr[k] for k in ("x", "y", "z")], 1)).all(1)).sum()) if xyz_ok else -1
    r["ring"] = "missing" if "ring" not in fl else ("ok" if fl["ring"][2] == 4 else "wrongtype(%d)" % fl["ring"][2])
    if "time" not in fl:
        r["time"] = "missing"
        r["time_min"] = r["time_max"] = float("nan")
    else:
        t = arr["time"].astype(np.float64)
        t = t[np.isfinite(t)]
        r["time_min"] = float(t.min()) if t.size else float("nan")
        r["time_max"] = float(t.max()) if t.size else float("nan")
        if fl["time"][2] != 7:
            r["time"] = "wrongtype(%d)" % fl["time"][2]
        elif t.size == 0 or (r["time_max"] - r["time_min"]) < 1e-6:
            r["time"] = "empty"
        elif r["time_min"] < -1e-6:
            r["time"] = "negative"
        else:
            r["time"] = "ok"
    return r


def adapt_cloud(fields, point_step, data, shift_time, big_endian=False):
    """Drop points with a non-finite x, y or z. If shift_time and the per-point time is negative (relative to the scan end),
    shift it so the first point has time 0. Returns (bytes, n_points, tmin_shift).
    The caller moves the header stamp by tmin_shift and sets is_dense = True. No point coordinate is changed."""
    arr = cloud_to_array(fields, point_step, data, big_endian).copy()
    keep = np.isfinite(arr["x"]) & np.isfinite(arr["y"]) & np.isfinite(arr["z"])
    arr = arr[keep]
    tmin = 0.0
    if shift_time and "time" in arr.dtype.names and arr.size:
        m = float(np.nanmin(arr["time"]))
        if m < 0:
            tmin = m
            arr["time"] = (arr["time"].astype(np.float64) - m).astype(arr.dtype["time"])
    return arr.tobytes(), int(arr.size), tmin


def packet_time_report(first_off, last_off):
    """Per-point time that velodyne_pointcloud will write for velodyne_packets, read from the packets alone.
    The converter (velodyne_pointcloud 1.6/1.7, rawdata.cc) sets time = packet stamp - scan header stamp + firing offset
    (0 .. 1.33 ms), so the sign is decided by which packet the recorded scan header carries:
      first_off, last_off   per scan: first packet stamp - header stamp, last packet stamp - header stamp (seconds)
    header = first packet  -> times 0 .. ~0.1 s, what LIO-SAM expects (TIME ok)
    header = last packet   -> times ~-0.1 .. 0 s, relative to the scan END (TIME negative: LIO-SAM finds no IMU before
                              the scan start, so its deskew gives every point the rotation 0, i.e. deskew is off)
    Returns dict: header_is ('first' | 'last' | 'other'), time ('ok' | 'negative'), time_min, time_max (s, medians)."""
    f = np.asarray(first_off, float)
    l = np.asarray(last_off, float)
    out = {"n": int(f.size), "header_is": "other", "time": "ok", "time_min": float("nan"), "time_max": float("nan")}
    if f.size == 0:
        out["time"] = "empty"
        return out
    fm, lm = float(np.median(f)), float(np.median(l))
    out["time_min"], out["time_max"] = fm, lm + 0.00133
    if abs(fm) < 0.002 and lm > 0.02:
        out["header_is"] = "first"
    elif abs(lm) < 0.002 and fm < -0.02:
        out["header_is"] = "last"
    out["time"] = "negative" if fm < -0.001 else "ok"
    return out


def stamp_report(t):
    """IMU header stamps in arrival (bag) order -> rate, gaps and stamps that do not increase (LIO-SAM integrates with
    dt = t_k - t_(k-1); dt <= 0 or a long gap breaks the preintegration)."""
    t = np.asarray(t, float)
    out = {"n": int(t.size)}
    if t.size < 3:
        return out
    dt = np.diff(t)
    pos = dt[dt > 0]
    med = float(np.median(pos)) if pos.size else float("nan")
    out.update({"rate_hz": 1.0 / med if med > 0 else float("nan"), "dt_median_ms": 1000 * med,
                "dt_max_ms": 1000 * float(dt.max()), "nonincreasing": int((dt <= 0).sum()),
                "gaps_over_3x": int((dt > 3 * med).sum()) if med > 0 else 0})
    return out


def _quat_to_R(q):
    """q rows x, y, z, w -> (N, 3, 3) rotation matrices (body to world)."""
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    x, y, z, w = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - z * w); R[:, 0, 2] = 2 * (x * z + y * w)
    R[:, 1, 0] = 2 * (x * y + z * w); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - x * w)
    R[:, 2, 0] = 2 * (x * z - y * w); R[:, 2, 1] = 2 * (y * z + x * w); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def orientation_verdict(quat_xyzw, cov0, acc, n_static=200, flagged_gravity_max_deg=20.0):
    """quat_xyzw (N,4), cov0 (N,) orientation_covariance[0], acc (N,3) linear acceleration, all in time order.
    The quaternion itself decides, not the driver's covariance flag (LIO-SAM never reads the covariance):
      missing   zero or non-unit quaternion, or covariance[0] == -1 (REP-145 'not provided') together with a quaternion
                that does not put gravity along +z within flagged_gravity_max_deg
      constant  unit quaternion that never changes
      ok        unit quaternion that changes over time (if the driver flagged it absent, flagged_absent is True and the
                gravity check had to pass)
    gravity_err_deg: angle between the world-frame acceleration of the first n_static samples and +z."""
    q = np.asarray(quat_xyzw, float)
    out = {"n": int(len(q)), "status": "missing", "gravity_err_deg": float("nan"), "flagged_absent": False}
    if len(q) == 0:
        return out
    nrm = np.linalg.norm(q, axis=1)
    out["flagged_absent"] = bool(np.all(np.asarray(cov0) == -1.0))
    if np.mean(np.abs(nrm - 1.0) < 0.02) < 0.95:
        return out
    k = min(n_static, len(q))
    R = _quat_to_R(q[:k])
    a = np.mean(np.einsum("nij,nj->ni", R, np.asarray(acc, float)[:k]), axis=0)
    out["gravity_err_deg"] = float(np.degrees(np.arccos(np.clip(a[2] / (np.linalg.norm(a) + 1e-12), -1, 1))))
    if out["flagged_absent"] and out["gravity_err_deg"] > flagged_gravity_max_deg:
        return out
    out["status"] = "constant" if float(np.max(np.std(q, axis=0))) < 1e-4 else "ok"
    return out
