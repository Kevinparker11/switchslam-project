#!/usr/bin/env python3
"""Write a VINS-Mono config for a SubT-MRS sequence from its published calibration files.

usage: python3 make_vins_config.py --intrinsics X_Intrinsics.yaml --extrinsics X_Extrinsics.yaml \
           --imu-topic /cmu_rc2/imu/data --image-topic /cmu_rc2/camera_1/image_raw --name corridor --out corridor_config.yaml
Camera model and parameters come from the intrinsics file ('rgb_camera' block), camera->IMU extrinsics from
'rgb_camera_to_imu'. IMU noise, feature-tracker and solver settings are copied unchanged from the Multi Floor
config (same SubT-MRS sensor pack: Epson M-G365 IMU), so nothing is tuned on the new sequence."""
import argparse
import re

import numpy as np

TEMPLATE = """%YAML:1.0
imu_topic: "{imu}"
image_topic: "{img}"
output_path: "/root/vins_output_{name}/"
model_type: {model}
camera_name: camera
image_width: {w}
image_height: {h}
{intr_block}
estimate_extrinsic: 0
extrinsicRotation: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [{r0}, {r1}, {r2},
         {r3}, {r4}, {r5},
         {r6}, {r7}, {r8}]
extrinsicTranslation: !!opencv-matrix
   rows: 3
   cols: 1
   dt: d
   data: [{t0}, {t1}, {t2}]
max_cnt: 150
min_dist: 30
freq: 10
F_threshold: 1.0
show_track: 1
equalize: 1
fisheye: {fisheye}
max_solver_time: 0.04
max_num_iterations: 8
keyframe_parallax: 10.0
acc_n: 0.08
gyr_n: 0.004
acc_w: 0.00004
gyr_w: 2.0e-6
g_norm: 9.81007
loop_closure: 0
load_previous_pose_graph: 0
fast_relocalization: 0
pose_graph_save_path: "/root/vins_output_{name}/pose_graph/"
estimate_td: 0
td: 0.0
rolling_shutter: 0
rolling_shutter_tr: 0
save_image: 0
visualize_imu_forward: 0
visualize_camera_size: 0.4
"""


def num(txt, key):
    m = re.search(r"\b%s\s*:\s*([-+0-9.eE]+)" % re.escape(key), txt)
    if not m:
        raise SystemExit("missing %s in intrinsics" % key)
    return float(m.group(1))


def matrix(txt, key):
    blk = txt[txt.index(key):]
    blk = blk[blk.index("data"):]
    vals = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", blk[:blk.index("]") + 1])
    return np.array([float(v) for v in vals[:16]]).reshape(4, 4)


ap = argparse.ArgumentParser()
ap.add_argument("--intrinsics", required=True)
ap.add_argument("--extrinsics", required=True)
ap.add_argument("--imu-topic", required=True)
ap.add_argument("--image-topic", required=True)
ap.add_argument("--name", required=True)
ap.add_argument("--camera-block", default="rgb_camera")
ap.add_argument("--extrinsic-key", default="rgb_camera_to_imu")
ap.add_argument("--out", required=True)
a = ap.parse_args()

it = open(a.intrinsics).read()
it = it[it.index(a.camera_block):]
model = re.search(r"model_type\s*:\s*(\w+)", it).group(1)
w, h = int(num(it, "image_width")), int(num(it, "image_height"))
if model.upper() == "MEI":
    intr = ("mirror_parameters:\n   xi: {xi!r}\ndistortion_parameters:\n   k1: {k1!r}\n   k2: {k2!r}\n   p1: {p1!r}\n"
            "   p2: {p2!r}\nprojection_parameters:\n   gamma1: {g1!r}\n   gamma2: {g2!r}\n   u0: {u0!r}\n   v0: {v0!r}").format(
        xi=num(it, "xi"), k1=num(it, "k1"), k2=num(it, "k2"), p1=num(it, "p1"), p2=num(it, "p2"),
        g1=num(it, "gamma1"), g2=num(it, "gamma2"), u0=num(it, "u0"), v0=num(it, "v0"))
    fisheye = 1
elif model.upper() == "PINHOLE":
    intr = ("distortion_parameters:\n   k1: {k1!r}\n   k2: {k2!r}\n   p1: {p1!r}\n   p2: {p2!r}\n"
            "projection_parameters:\n   fx: {fx!r}\n   fy: {fy!r}\n   cx: {cx!r}\n   cy: {cy!r}").format(
        k1=num(it, "k1"), k2=num(it, "k2"), p1=num(it, "p1"), p2=num(it, "p2"),
        fx=num(it, "fx"), fy=num(it, "fy"), cx=num(it, "cx"), cy=num(it, "cy"))
    fisheye = 0
else:
    raise SystemExit("camera model %s not handled; edit the config by hand" % model)

T = matrix(open(a.extrinsics).read(), a.extrinsic_key)
R, t = T[:3, :3], T[:3, 3]
err = np.abs(R @ R.T - np.eye(3)).max()
if err > 1e-3:
    raise SystemExit("rgb_camera_to_imu rotation is not orthonormal (err %.2g)" % err)
r = ["%.8f" % v for v in R.ravel()]
open(a.out, "w").write(TEMPLATE.format(imu=a.imu_topic, img=a.image_topic, name=a.name, model=model, w=w, h=h,
                                       intr_block=intr, fisheye=fisheye, t0="%.8f" % t[0], t1="%.8f" % t[1],
                                       t2="%.8f" % t[2], **{"r%d" % i: r[i] for i in range(9)}))
print("wrote %s: model %s %dx%d, camera->IMU t = %s, imu %s, image %s" % (a.out, model, w, h, np.round(t, 4),
                                                                      a.imu_topic, a.image_topic))
