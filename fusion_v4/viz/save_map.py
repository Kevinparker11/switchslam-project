#!/usr/bin/env python3
"""Save the map of a run from its keyframe file (keyframes_<tag>.npz, written by the batch) as a point cloud and a top-down picture.
usage: python3 save_map.py KEYFRAMES.npz [OUT_PREFIX] [--voxel 0.1]
writes OUT_PREFIX.pcd (open with pcl_viewer, CloudCompare, MeshLab or RViz) and OUT_PREFIX_topdown.png.
The map is in A-LOAM's frame (camera_init), built from the keyframe scans at their A-LOAM poses."""
import sys
import numpy as np

def q2R(q):
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def build(npz):
    z = np.load(npz); pose, n = z["pose"], z["n"]; off = np.r_[0, np.cumsum(n)]
    pts = z["pts"].astype(np.float32) * float(z["scale"])
    return np.vstack([pts[off[i]:off[i+1]] @ q2R(pose[i, 3:7]).T + pose[i, :3] for i in range(len(pose))]).astype(np.float32), pose[:, :3]

def voxel(P, v):
    k = np.floor(P / v).astype(np.int64); _, i = np.unique(k, axis=0, return_index=True); return P[np.sort(i)]

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]; vox = 0.1
    if "--voxel" in sys.argv: vox = float(sys.argv[sys.argv.index("--voxel") + 1]); a = [x for x in a if x != str(vox) and x != sys.argv[sys.argv.index("--voxel") + 1]]
    src = a[0]; out = a[1] if len(a) > 1 else src.rsplit(".", 1)[0] + "_map"
    P, T = build(src); print("keyframes %d, points %d" % (len(T), len(P)))
    if vox > 0: P = voxel(P, vox); print("after %.2f m voxel filter: %d points" % (vox, len(P)))
    with open(out + ".pcd", "w") as f:
        f.write("# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH %d\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS %d\nDATA ascii\n" % (len(P), len(P)))
        np.savetxt(f, P, fmt="%.3f")
    print("wrote", out + ".pcd")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        lo, hi = np.percentile(P[:, 2], [5, 95]); m = (P[:, 2] > lo) & (P[:, 2] < hi)
        fig, ax = plt.subplots(figsize=(12, 7), dpi=130); ax.scatter(P[m, 0], P[m, 1], s=0.3, c=P[m, 2], cmap="viridis", linewidths=0)
        ax.plot(T[:, 0], T[:, 1], color="#ff6b5e", lw=1); ax.set_aspect("equal"); ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_title("map from " + src.split("/")[-1] + " (colour = height, red = path)")
        fig.savefig(out + "_topdown.png", bbox_inches="tight"); print("wrote", out + "_topdown.png")
    except ImportError:
        print("matplotlib not installed: no picture (pip install matplotlib)")
