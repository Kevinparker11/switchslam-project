#!/usr/bin/env python3
"""Write the params.yaml of one stock LIO-SAM run.

The ORIGINAL config/params.yaml of the pinned LIO-SAM commit is copied and exactly these keys are replaced, nothing else:
  pointCloudTopic, imuTopic            the topics of the sequence
  extrinsicRot, extrinsicRPY, extrinsicTrans   from the sequence's laser_to_imu matrix (see below)
  loopClosureEnableFlag                false (the Switch-SLAM table is without loop closure; same as every other run here)
Every other value (noise, voxel sizes, thresholds, N_SCAN 16, Horizon_SCAN 1800, ...) stays at the upstream default.

Extrinsic convention (LIO-SAM include/utility.h): acc_lidar = extRot * acc_imu, q_lidar = q_imu * inverse(extRPY),
and the IMU position in the LiDAR frame is extTrans. Our files give T_imu<-lidar = [R t], i.e. p_imu = R p_lidar + t, so
  extrinsicRot = extrinsicRPY = R^T,   extrinsicTrans = -R^T t.
R is projected to the nearest rotation (SVD) first, as fusion_node_v2.py does.

usage: make_params.py --base params.yaml --extrinsics laser_to_imu.yaml --points-topic T --imu-topic T --out params_run.yaml
"""
import argparse
import re
import sys

import numpy as np
import yaml


def load_laser_to_imu(path):
    with open(path) as f:
        txt = f.read().replace("%YAML 1.2", "")
    T = np.array(yaml.safe_load(txt)["laser_to_imu"]["data"], dtype=float).reshape(4, 4)
    U, _, Vt = np.linalg.svd(T[:3, :3])
    R = U @ Vt
    if np.linalg.det(R) < 0:
        raise ValueError("laser_to_imu rotation is a reflection")
    return R, T[:3, 3].copy()


def liosam_extrinsics(R_il, t_il):
    """(extrinsicRot, extrinsicRPY, extrinsicTrans) for a T_imu<-lidar = [R_il t_il]."""
    Rt = R_il.T
    return Rt, Rt.copy(), -Rt @ t_il


def _fmt_mat(M):
    r = ["%.9f" % v for v in M.reshape(-1)]
    return "[" + ",\n                 ".join(", ".join(r[i:i + 3]) for i in range(0, 9, 3)) + "]"


def _fmt_vec(v):
    return "[" + ", ".join("%.9f" % x for x in v) + "]"


def _sub_once(text, key, value_text, changes):
    # an active (not commented) key; arrays may span lines: value ends at the first ']' for lists, at end of line otherwise
    if value_text.startswith("["):
        pat = re.compile(r"^(\s*%s:\s*)\[[^\]]*\]" % re.escape(key), re.M)
    else:
        pat = re.compile(r"^(\s*%s:\s*)[^\s#][^#\n]*?(\s*(#.*)?)$" % re.escape(key), re.M)
    hits = pat.findall(text)
    if len(hits) != 1:
        raise ValueError("key %s found %d times in the base params.yaml (expected 1)" % (key, len(hits)))
    m = pat.search(text)
    old = m.group(0)[len(m.group(1)):].split("#")[0].strip()
    changes.append((key, " ".join(old.split()), " ".join(value_text.split())))
    if value_text.startswith("["):
        return pat.sub(lambda mm: mm.group(1) + value_text, text, count=1)
    return pat.sub(lambda mm: mm.group(1) + value_text + mm.group(2), text, count=1)


def make(base_text, R_il, t_il, points_topic, imu_topic):
    rot, rpy, tr = liosam_extrinsics(R_il, t_il)
    changes = []
    out = base_text
    out = _sub_once(out, "pointCloudTopic", '"%s"' % points_topic, changes)
    out = _sub_once(out, "imuTopic", '"%s"' % imu_topic, changes)
    out = _sub_once(out, "extrinsicTrans", _fmt_vec(tr), changes)
    out = _sub_once(out, "extrinsicRot", _fmt_mat(rot), changes)
    out = _sub_once(out, "extrinsicRPY", _fmt_mat(rpy), changes)
    out = _sub_once(out, "loopClosureEnableFlag", "false", changes)
    return out, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--extrinsics", required=True)
    ap.add_argument("--points-topic", required=True)
    ap.add_argument("--imu-topic", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R, t = load_laser_to_imu(a.extrinsics)
    text, changes = make(open(a.base).read(), R, t, a.points_topic, a.imu_topic)
    yaml.safe_load(text)  # must still parse
    with open(a.out, "w") as f:
        f.write(text)
    print("params written: %s (keys changed from the upstream file):" % a.out)
    for k, o, n in changes:
        print("  %-22s %s  ->  %s" % (k, o, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
