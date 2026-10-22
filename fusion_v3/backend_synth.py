"""Synthetic world for testing the back end only (code correctness, not evidence about real data).

A 12 x 8 m room with a box, opening onto a 60 m corridor (2.5 m wide).  In the middle of the corridor a
25 m-range, 16-ring scanner sees only the two side walls, floor and ceiling, so scan matching is
degenerate along the corridor axis, as in the SubT-MRS Long Corridor sequence.  No occlusion modelling.
"""
import numpy as np

import fusion_core as fc
import backend_icp as bi


def _rect(p0, u, v, s):
    p0, u, v = (np.asarray(x, float) for x in (p0, u, v))
    a = np.arange(0, np.linalg.norm(u) + 1e-9, s) / max(np.linalg.norm(u), 1e-9)
    b = np.arange(0, np.linalg.norm(v) + 1e-9, s) / max(np.linalg.norm(v), 1e-9)
    A, B = np.meshgrid(a, b, indexing="ij")
    return p0 + A.reshape(-1, 1) * u + B.reshape(-1, 1) * v


def make_world(s=0.05, L=60.0, W=2.5, H=3.0):
    w = W / 2
    R = []
    # room x in [-12, 0], y in [-4, 4]
    R += [_rect([-12, -4, 0], [12, 0, 0], [0, 8, 0], s), _rect([-12, -4, H], [12, 0, 0], [0, 8, 0], s)]
    R += [_rect([-12, -4, 0], [0, 8, 0], [0, 0, H], s)]
    R += [_rect([-12, -4, 0], [12, 0, 0], [0, 0, H], s), _rect([-12, 4, 0], [12, 0, 0], [0, 0, H], s)]
    R += [_rect([0, -4, 0], [0, 4 - w, 0], [0, 0, H], s), _rect([0, w, 0], [0, 4 - w, 0], [0, 0, H], s)]
    # a box in the room
    b0, bs = np.array([-7.0, 1.5, 0.0]), 1.2
    R += [_rect(b0, [bs, 0, 0], [0, 0, bs], s), _rect(b0 + [0, bs, 0], [bs, 0, 0], [0, 0, bs], s),
          _rect(b0, [0, bs, 0], [0, 0, bs], s), _rect(b0 + [bs, 0, 0], [0, bs, 0], [0, 0, bs], s),
          _rect(b0 + [0, 0, bs], [bs, 0, 0], [0, bs, 0], s)]
    # corridor x in [0, L], y in [-w, w]
    R += [_rect([0, -w, 0], [L, 0, 0], [0, W, 0], s), _rect([0, -w, H], [L, 0, 0], [0, W, 0], s)]
    R += [_rect([0, -w, 0], [L, 0, 0], [0, 0, H], s), _rect([0, w, 0], [L, 0, 0], [0, 0, H], s)]
    R += [_rect([L, -w, 0], [0, W, 0], [0, 0, H], s)]
    return np.vstack(R)


def scan(world, T, rng, rings=np.linspace(-15, 15, 16), tol_deg=0.35, rmin=0.8, rmax=25.0, noise=0.01):
    R, t = T[:3, :3], T[:3, 3]
    pb = (world - t) @ R
    r = np.linalg.norm(pb, axis=1)
    m = (r > rmin) & (r < rmax)
    pb, r = pb[m], r[m]
    el = np.degrees(np.arcsin(np.clip(pb[:, 2] / r, -1, 1)))
    d = np.min(np.abs(el[:, None] - rings[None, :]), axis=1)
    pb = pb[d < tol_deg]
    return pb + rng.normal(0, noise, pb.shape)


def path(waypoints, step=1.0, height=1.0):
    """GT keyframe poses every `step` m along straight segments, heading along the motion"""
    T = []
    for a, b in zip(waypoints[:-1], waypoints[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = np.linalg.norm(b - a)
        yaw = np.arctan2(b[1] - a[1], b[0] - a[0])
        for s in np.arange(0, d, step):
            p = a + (b - a) * s / d
            T.append(bi.se3(fc.so3_exp([0, 0, yaw]), np.r_[p, height]))
    return T


def drifted(T_gt, rng, drift_world=(0.012, 0.0, 0.004), yaw_bias_deg=0.08, sig_t=0.005, sig_r_deg=0.03):
    """front-end-like odometry: GT increments + yaw bias + world-frame drift per step + noise"""
    out = [T_gt[0].copy()]
    for k in range(len(T_gt) - 1):
        d = bi.inv_se3(T_gt[k]) @ T_gt[k + 1]
        n = np.r_[np.radians(rng.normal(0, sig_r_deg, 3)) + [0, 0, np.radians(yaw_bias_deg)], rng.normal(0, sig_t, 3)]
        Tn = bi.right_update(out[-1] @ d, n)
        Tn[:3, 3] += np.asarray(drift_world)
        out.append(Tn)
    return out
