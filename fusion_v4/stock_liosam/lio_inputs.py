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


def _quat_to_R(q):
    """q rows x, y, z, w -> (N, 3, 3) rotation matrices (body to world)."""
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    x, y, z, w = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - z * w); R[:, 0, 2] = 2 * (x * z + y * w)
    R[:, 1, 0] = 2 * (x * y + z * w); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - x * w)
    R[:, 2, 0] = 2 * (x * z - y * w); R[:, 2, 1] = 2 * (y * z + x * w); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def orientation_verdict(quat_xyzw, cov0, acc, n_static=200):
    """quat_xyzw (N,4), cov0 (N,) orientation_covariance[0], acc (N,3) linear acceleration, all in time order.
    status: ok | missing (zero quaternion or covariance[0] == -1) | constant (valid but never changes)
    gravity_err_deg: angle between the world-frame acceleration of the first n_static samples and +z (info; a large value
    means the orientation is not a z-up world attitude of the same body frame as the accelerometer)."""
    q = np.asarray(quat_xyzw, float)
    out = {"n": int(len(q)), "status": "missing", "gravity_err_deg": float("nan")}
    if len(q) == 0:
        return out
    nrm = np.linalg.norm(q, axis=1)
    flagged_absent = bool(np.all(np.asarray(cov0) == -1.0))
    if flagged_absent or np.mean(np.abs(nrm - 1.0) < 0.02) < 0.95:
        return out
    out["status"] = "constant" if float(np.max(np.std(q, axis=0))) < 1e-4 else "ok"
    k = min(n_static, len(q))
    R = _quat_to_R(q[:k])
    a = np.mean(np.einsum("nij,nj->ni", R, np.asarray(acc, float)[:k]), axis=0)
    out["gravity_err_deg"] = float(np.degrees(np.arccos(np.clip(a[2] / (np.linalg.norm(a) + 1e-12), -1, 1))))
    return out
