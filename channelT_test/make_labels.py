#!/usr/bin/env python3
"""
make_labels.py  -  per-scan geometric degeneracy labels from REAL data.

Independent of every detector under test: it never looks at A-LOAM, the Hessian,
the Schur complement or the orientation tensor. It only uses
  * the real LiDAR scans (recorded from the replayed bag),
  * the dataset's ground-truth trajectory,
  * the dataset's survey-grade ground-truth map.

Label rule (perturbation test, after Nubert et al. IROS 2022, applied to real scans):
  1. place the scan at its ground-truth pose in the map, refine with point-to-plane ICP
     -> reference pose (also tells us if GT/extrinsic are trustworthy for this scan);
  2. displace the scan by `--trans-step` metres along each of 26 directions
     (and by `--rot-step` degrees about each of +/-x,y,z) in the LiDAR frame;
  3. run the same ICP back from each displaced start;
  4. the fraction of the displacement NOT recovered along the displaced direction
     is stored per direction. A scan is translation-degenerate when any direction
     keeps more than `--frac` of its displacement (default 0.5).
All per-direction fractions are written, so the threshold can be swept later without rerunning.

Usage
  # 0) check GT + extrinsic + map line up (prints fitness; stop here if it is poor)
  python3 make_labels.py --bag points.bag --topic /multifloor/velodyne_points \
      --gt Floor01_gt.txt --map hawkins_gt_map.pcd --check 30
  # 1) full labels, one scan per second
  python3 make_labels.py --bag points.bag --topic /multifloor/velodyne_points \
      --gt Floor01_gt.txt --map hawkins_gt_map.pcd --every 1.0 --out labels_floor01.csv
Ground truth: TUM text (t x y z qx qy qz qw) or the SubT-MRS CSV
(timestamp[ns], p_w_b_x.., q_w_b_..). --extrinsic: 4x4 text file T_body_lidar
(pose of the LiDAR in the GT body frame); identity if omitted.
"""
import argparse, sys, time
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R, Slerp

try:
    import open3d as o3d
except ImportError:
    sys.exit("open3d missing:  pip install open3d")
try:
    from rosbags.highlevel import AnyReader
except ImportError:
    sys.exit("rosbags missing:  pip install rosbags")
from pathlib import Path


# ---------------------------------------------------------------- inputs
def load_gt(path):
    """Return t (s), positions (N,3), quaternions xyzw (N,4)."""
    with open(path) as f:
        first = f.readline()
    if "," in first and any(c.isalpha() for c in first):
        g = pd.read_csv(path)
        cols = {c.lower(): c for c in g.columns}
        tcol = next(c for c in g.columns if "time" in c.lower() or "stamp" in c.lower())
        t = g[tcol].values.astype(float)
        t = t / 1e9 if t[0] > 1e12 else t
        px = [c for c in g.columns if c.lower().startswith("p") and c.lower()[-1] in "xyz"][:3]
        q = {}
        for c in g.columns:
            cl = c.lower()
            if cl.startswith("q") and cl[-1] in "xyzw":
                q[cl[-1]] = c
        if len(px) < 3 or len(q) < 4:
            sys.exit(f"could not find position/quaternion columns in {path}: {list(g.columns)}")
        P = g[px].values.astype(float)
        Q = g[[q["x"], q["y"], q["z"], q["w"]]].values.astype(float)
    else:
        d = np.loadtxt(path, comments="#")
        t, P, Q = d[:, 0], d[:, 1:4], d[:, 4:8]
        if t[0] > 1e12:
            t = t / 1e9
    o = np.argsort(t)
    return t[o], P[o], Q[o]


class GT:
    def __init__(self, path):
        self.t, self.P, self.Q = load_gt(path)
        self.slerp = Slerp(self.t, R.from_quat(self.Q))

    def pose(self, t):
        if t < self.t[0] or t > self.t[-1]:
            return None
        i = np.searchsorted(self.t, t)
        if i > 0 and min(abs(self.t[i] - t) if i < len(self.t) else 9, abs(t - self.t[i - 1])) > 0.2:
            return None                                   # gap in GT
        T = np.eye(4)
        T[:3, :3] = self.slerp([t]).as_matrix()[0]
        T[:3, 3] = [np.interp(t, self.t, self.P[:, k]) for k in range(3)]
        return T


def cloud_xyz(msg):
    """PointCloud2 (rosbags message) -> (N,3) float64."""
    off = {f.name: f.offset for f in msg.fields}
    dt = np.dtype({"names": ["x", "y", "z"], "formats": ["<f4"] * 3,
                   "offsets": [off["x"], off["y"], off["z"]], "itemsize": msg.point_step})
    a = np.frombuffer(bytes(msg.data), dtype=dt, count=msg.width * msg.height)
    p = np.stack([a["x"], a["y"], a["z"]], 1).astype(np.float64)
    return p[np.isfinite(p).all(1)]


def scans(bag, topic, every):
    last = -1e18
    with AnyReader([Path(bag)]) as r:
        conns = [c for c in r.connections if c.topic == topic]
        if not conns:
            sys.exit(f"topic {topic} not in {bag}; topics: {sorted({c.topic for c in r.connections})}")
        for c, _, raw in r.messages(connections=conns):
            m = r.deserialize(raw, c.msgtype)
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            if t - last >= every:
                last = t
                yield t, cloud_xyz(m)


# ---------------------------------------------------------------- registration
def icp(src, tgt, init, max_corr, iters=50):
    r = o3d.pipelines.registration.registration_icp(
        src, tgt, max_corr, init,
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=iters))
    return r.transformation, r.fitness, r.inlier_rmse


def directions26():
    d = np.array([(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)
                  if (i, j, k) != (0, 0, 0)], float)
    return d / np.linalg.norm(d, axis=1, keepdims=True)


def rel_err(T_ref, T):
    E = np.linalg.inv(T_ref) @ T                       # error expressed in the reference LiDAR frame
    return E[:3, 3], R.from_matrix(E[:3, :3]).as_rotvec()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bag", required=True); ap.add_argument("--topic", required=True)
    ap.add_argument("--gt", required=True); ap.add_argument("--map", required=True)
    ap.add_argument("--extrinsic", help="4x4 text file T_body_lidar")
    ap.add_argument("--every", type=float, default=1.0, help="seconds between labelled scans")
    ap.add_argument("--range-min", type=float, default=1.0)
    ap.add_argument("--range-max", type=float, default=100.0, help="use the SAME value as the detector run")
    ap.add_argument("--voxel", type=float, default=0.15)
    ap.add_argument("--crop", type=float, default=60.0, help="map crop radius around the scan (m)")
    ap.add_argument("--trans-step", type=float, default=0.5)
    ap.add_argument("--rot-step", type=float, default=5.0)
    ap.add_argument("--frac", type=float, default=0.5)
    ap.add_argument("--min-fitness", type=float, default=0.35)
    ap.add_argument("--max-gt-dev", type=float, default=0.5, help="m; larger ICP correction of GT -> gt_ok=0")
    ap.add_argument("--check", type=int, default=0, help="only test alignment on this many scans")
    ap.add_argument("--out", default="labels.csv")
    a = ap.parse_args()

    T_bl = np.loadtxt(a.extrinsic).reshape(4, 4) if a.extrinsic else np.eye(4)
    gt = GT(a.gt)
    print(f"GT: {len(gt.t)} poses, {gt.t[0]:.2f} .. {gt.t[-1]:.2f}")
    mp = o3d.io.read_point_cloud(a.map)
    if len(mp.points) == 0:
        sys.exit(f"empty or unreadable map {a.map} (open3d reads .pcd/.ply; convert .las first)")
    mp = mp.voxel_down_sample(a.voxel)
    mp.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=4 * a.voxel, max_nn=30))
    MP = np.asarray(mp.points)
    print(f"map: {len(MP)} points after {a.voxel} m voxel")
    dirs = directions26()
    rot_axes = np.vstack([np.eye(3), -np.eye(3)])

    rows, n_seen, t0 = [], 0, time.time()
    corr_log = []
    for t, P in scans(a.bag, a.topic, a.every):
        Tg = gt.pose(t)
        if Tg is None:
            continue
        rng = np.linalg.norm(P, axis=1)
        P = P[(rng > a.range_min) & (rng < a.range_max)]
        if len(P) < 500:
            continue
        sc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(P)).voxel_down_sample(a.voxel)
        T0 = Tg @ T_bl
        near = np.linalg.norm(MP - T0[:3, 3], axis=1) < a.crop
        tgt = mp.select_by_index(np.where(near)[0])
        if len(tgt.points) < 500:
            continue
        # reference pose: GT refined by ICP (coarse then fine)
        Tr, _, _ = icp(sc, tgt, T0, 1.0)
        Tr, fit, rmse = icp(sc, tgt, Tr, 0.3)
        dt_, dr_ = rel_err(T0, Tr)
        gt_dev_t, gt_dev_r = np.linalg.norm(dt_), np.degrees(np.linalg.norm(dr_))
        gt_ok = int(fit >= a.min_fitness and gt_dev_t <= a.max_gt_dev and gt_dev_r <= 3.0)
        n_seen += 1
        if a.check:
            corr_log.append(np.linalg.inv(T0) @ Tr)
            print(f"t={t:.2f}  fitness={fit:.2f}  rmse={rmse:.3f}  GT correction {gt_dev_t:.3f} m / {gt_dev_r:.2f} deg  -> gt_ok={gt_ok}")
            if n_seen >= a.check:
                C = np.array(corr_log)
                med_t = np.median(C[:, :3, 3], 0)
                med_r = R.from_matrix(C[:, :3, :3]).mean().as_rotvec()
                print("\nmedian correction (LiDAR frame): t =", np.round(med_t, 3),
                      " rotvec(deg) =", np.round(np.degrees(med_r), 2))
                print("Mostly gt_ok=1 and corrections of a few cm -> GT, extrinsic and map agree; run without --check.")
                print("A large, CONSISTENT correction -> wrong extrinsic/frame; fix --extrinsic before labelling.")
                return
            continue
        ft = np.zeros(len(dirs)); fr = np.zeros(len(rot_axes))
        if gt_ok:
            for i, d in enumerate(dirs):
                D = np.eye(4); D[:3, 3] = a.trans_step * d
                Te, _, _ = icp(sc, tgt, Tr @ D, max(1.0, 2 * a.trans_step))
                e, _ = rel_err(Tr, Te)
                ft[i] = float(e @ d) / a.trans_step
            for i, ax in enumerate(rot_axes):
                D = np.eye(4); D[:3, :3] = R.from_rotvec(np.radians(a.rot_step) * ax).as_matrix()
                Te, _, _ = icp(sc, tgt, Tr @ D, max(1.0, 2 * a.trans_step))
                _, w = rel_err(Tr, Te)
                fr[i] = float(w @ ax) / np.radians(a.rot_step)
        kt, kr = int(np.argmax(ft)), int(np.argmax(fr))
        row = dict(t=t, gt_ok=gt_ok, fitness=fit, rmse=rmse, gt_dev_t=gt_dev_t, gt_dev_r=gt_dev_r,
                   n_scan=len(sc.points),
                   trans_maxfrac=ft[kt], weak_tx=dirs[kt, 0], weak_ty=dirs[kt, 1], weak_tz=dirs[kt, 2],
                   rot_maxfrac=fr[kr], weak_rx=rot_axes[kr, 0], weak_ry=rot_axes[kr, 1], weak_rz=rot_axes[kr, 2],
                   label_trans=int(gt_ok and ft[kt] > a.frac), label_rot=int(gt_ok and fr[kr] > a.frac))
        row.update({f"ft{i:02d}": v for i, v in enumerate(ft)})
        row.update({f"fr{i}": v for i, v in enumerate(fr)})
        rows.append(row)
        if len(rows) % 20 == 0:
            pd.DataFrame(rows).to_csv(a.out, index=False)
            el = time.time() - t0
            print(f"{len(rows)} scans labelled ({el/len(rows):.1f} s/scan); "
                  f"gt_ok {np.mean([r['gt_ok'] for r in rows]):.0%}, "
                  f"translation-degenerate {np.mean([r['label_trans'] for r in rows]):.0%}")
    if a.check:
        print(f"only {n_seen} scans overlapped the GT")
        return
    df = pd.DataFrame(rows)
    df.to_csv(a.out, index=False)
    ok = df[df.gt_ok == 1]
    print(f"\nsaved {len(df)} scans to {a.out}; usable (gt_ok) {len(ok)}; "
          f"translation-degenerate {int(ok.label_trans.sum())}; rotation-degenerate {int(ok.label_rot.sum())}")
    print("settings:", vars(a))


if __name__ == "__main__":
    main()
