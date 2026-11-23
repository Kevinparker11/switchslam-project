#!/usr/bin/env python3
"""MEI (unified, omnidirectional) camera model of the VINS-Mono / camodocal front end, and the pinhole image that replaces it for
methods that only take a pinhole camera with radial-tangential distortion (R3LIVE, R2LIVE, FAST-LIVO). Pure numpy, no ROS.

Projection (camodocal CataCamera::spaceToPlane, the same code the VINS-Mono configs of our bags were calibrated for):
    z = Z + xi * |P|;  m = (X / z, Y / z);  m_d = m + distortion(m) (k1, k2 radial; p1, p2 tangential);  u = gamma1 m_d.x + u0, v = gamma2 m_d.y + v0

Rectification: an output pinhole image (no distortion, same size, principal point (u0, v0), focal length f = mean(gamma1, gamma2) / (1 + xi),
which keeps the pixel scale of the image centre) is filled by projecting the ray of every output pixel through the MEI model and sampling the
original image there (cv2.remap with the maps from rectify_maps). Optical centre and axes do not change, so the camera-IMU extrinsic of the
original camera is also the extrinsic of the rectified one."""
import numpy as np
import yaml


def load_vins_camera_config(path):
    """(dict of the VINS config, R_ic 3x3, t_ic 3) from an OpenCV-yaml VINS config (p_imu = R_ic p_cam + t_ic)."""
    with open(path) as f:
        txt = f.read().replace("%YAML:1.0", "").replace("!!opencv-matrix", "")
    c = yaml.safe_load(txt)
    R = np.array(c["extrinsicRotation"]["data"], dtype=float).reshape(3, 3)
    U, _, Vt = np.linalg.svd(R)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        raise ValueError("camera extrinsic rotation is a reflection")
    return c, R, np.array(c["extrinsicTranslation"]["data"], dtype=float).reshape(3)


def project_mei(P, xi, k1, k2, p1, p2, gamma1, gamma2, u0, v0):
    """P: (N, 3) points in the camera frame (x right, y down, z forward) -> (N, 2) pixels."""
    P = np.asarray(P, dtype=float)
    z = P[:, 2] + xi * np.linalg.norm(P, axis=1)
    mx, my = P[:, 0] / z, P[:, 1] / z
    mx2, my2, mxy = mx * mx, my * my, mx * my
    rho2 = mx2 + my2
    rad = k1 * rho2 + k2 * rho2 * rho2
    dx = mx * rad + 2.0 * p1 * mxy + p2 * (rho2 + 2.0 * mx2)
    dy = my * rad + 2.0 * p2 * mxy + p1 * (rho2 + 2.0 * my2)
    return np.stack([gamma1 * (mx + dx) + u0, gamma2 * (my + dy) + v0], axis=1)


def mei_params(cfg):
    d, p = cfg["distortion_parameters"], cfg["projection_parameters"]
    return dict(xi=cfg["mirror_parameters"]["xi"], k1=d["k1"], k2=d["k2"], p1=d["p1"], p2=d["p2"],
                gamma1=p["gamma1"], gamma2=p["gamma2"], u0=p["u0"], v0=p["v0"])


def rectified_pinhole(cfg):
    """(width, height, f, cx, cy) of the pinhole image that replaces an MEI camera."""
    m = mei_params(cfg)
    f = 0.5 * (m["gamma1"] + m["gamma2"]) / (1.0 + m["xi"])
    return int(cfg["image_width"]), int(cfg["image_height"]), f, m["u0"], m["v0"]


def rectify_maps(cfg):
    """float32 maps (map_x, map_y), shape (height, width), for cv2.remap(src, map_x, map_y, cv2.INTER_LINEAR)."""
    w, h, f, cx, cy = rectified_pinhole(cfg)
    uu, vv = np.meshgrid(np.arange(w, dtype=float), np.arange(h, dtype=float))
    rays = np.stack([(uu.ravel() - cx) / f, (vv.ravel() - cy) / f, np.ones(w * h)], axis=1)
    px = project_mei(rays, **mei_params(cfg))
    return px[:, 0].reshape(h, w).astype(np.float32), px[:, 1].reshape(h, w).astype(np.float32)
