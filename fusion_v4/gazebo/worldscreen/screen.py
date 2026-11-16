"""Geometry-only degeneracy screen of Clearpath worlds: cast a simulated VLP-16 (16 rings -15..+15 deg, 440 samples,
0.4 m above base_link, max range 100 m) against the world mesh, estimate the surface normal at every hit, and report the
translation orientation tensor M = mean(n n^T) (trace 1). Its eigenvalues a <= b <= c say how well the three translation
directions are constrained: a near 0 means one direction (x, y or z) has no surface facing it (LiDAR slides along it).
Screen only: no Hessian rule, no noise, no motion; it ranks routes against each other, it does not predict A-LOAM failure."""
import sys
import numpy as np
from scipy.ndimage import uniform_filter
sys.path.insert(0, '/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad')
from mapworld import tris_of

VOX = 0.3


def sample_points(T, step=0.15, cap=3000):
    out = []
    rng = np.random.default_rng(0)
    for a, b, c in T:
        area = np.linalg.norm(np.cross(b - a, c - a)) / 2
        n = int(max(1, min(cap, area / (step * step))))
        u = rng.random((n, 1)); v = rng.random((n, 1))
        m = (u + v) > 1
        u[m] = 1 - u[m]; v[m] = 1 - v[m]
        out.append(a + u * (b - a) + v * (c - a))
    return np.vstack(out)


class World:
    def __init__(self, parts, pad=2.0):
        """parts: list of (dae path, yaw, xyscale, zscale)"""
        pts = []
        for path, yaw, xs, zs in parts:
            T = tris_of(path) * np.array([xs, xs, zs])
            c, s = np.cos(yaw), np.sin(yaw)
            R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
            pts.append(sample_points(T @ R.T))
        P = np.vstack(pts)
        self.lo = P.min(0) - pad
        self.hi = P.max(0) + pad
        self.shape = np.ceil((self.hi - self.lo) / VOX).astype(int) + 1
        idx = ((P - self.lo) / VOX).astype(int)
        occ = np.zeros(self.shape, np.float32)
        occ[idx[:, 0], idx[:, 1], idx[:, 2]] = 1.0
        self.occ = occ > 0
        sm = uniform_filter(occ, size=5, mode='constant')
        self.gx, self.gy, self.gz = np.gradient(sm)
        # ground height: lowest occupied voxel per column, filled by nearest
        zi = np.where(self.occ.any(2), self.occ.argmax(2), -1)
        self.ground = np.where(zi >= 0, self.lo[2] + zi * VOX, np.nan)
        # smooth terrain for ground normals (filled by nearest valid column, then smoothed)
        from scipy.ndimage import distance_transform_edt
        bad = ~np.isfinite(self.ground)
        if bad.any() and (~bad).any():
            ind = distance_transform_edt(bad, return_distances=False, return_indices=True)
            gf = self.ground[tuple(ind)]
        else:
            gf = np.nan_to_num(self.ground)
        gs = uniform_filter(gf, size=9, mode='nearest')
        self.gfill = gs
        self.tgx, self.tgy = np.gradient(gs, VOX)

    def ground_at(self, x, y):
        i = int((x - self.lo[0]) / VOX); j = int((y - self.lo[1]) / VOX)
        win = self.ground[max(i - 3, 0):i + 4, max(j - 3, 0):j + 4]
        return np.nanmedian(win) if np.isfinite(win).any() else np.nan


def rays():
    el = np.deg2rad(np.arange(-15, 16, 2.0))
    az = np.linspace(0, 2 * np.pi, 440, endpoint=False)
    E, A = np.meshgrid(el, az, indexing='ij')
    d = np.stack([np.cos(E) * np.cos(A), np.cos(E) * np.sin(A), np.sin(E)], -1).reshape(-1, 3)
    return d


D = rays()
STEPS = np.arange(1.0, 100.0, VOX * 0.5)


def scan(W, x, y, yaw_unused=0.0):
    g = W.ground_at(x, y)
    if not np.isfinite(g):
        return None
    o = np.array([x, y, g + 0.14 + 0.4])  # base_link about 0.14 m above ground, LiDAR 0.4 m above base_link
    hits = []
    P = o[None, None, :] + D[:, None, :] * STEPS[None, :, None]  # (rays, steps, 3)
    idx = ((P - W.lo) / VOX).astype(int)
    ok = (idx >= 0).all(-1) & (idx < W.shape).all(-1)
    idc = np.where(ok[..., None], idx, 0)
    occ = W.occ[idc[..., 0], idc[..., 1], idc[..., 2]] & ok
    first = occ.argmax(1)
    hit = occ.any(1)
    r = np.nonzero(hit)[0]
    ii = idc[r, first[r]]
    n = np.stack([W.gx[ii[:, 0], ii[:, 1], ii[:, 2]], W.gy[ii[:, 0], ii[:, 1], ii[:, 2]], W.gz[ii[:, 0], ii[:, 1], ii[:, 2]]], -1)
    nn = np.linalg.norm(n, axis=1)
    n = n / np.maximum(nn, 1e-9)[:, None]
    # ground hits (within 0.35 m of the local terrain surface): terrain normal instead of the voxel gradient
    zhit = W.lo[2] + ii[:, 2] * VOX
    gz = W.gfill[ii[:, 0], ii[:, 1]]
    isg = (zhit - gz) < 0.35
    tn = np.stack([-W.tgx[ii[:, 0], ii[:, 1]], -W.tgy[ii[:, 0], ii[:, 1]], np.ones(len(ii))], -1)
    tn /= np.linalg.norm(tn, axis=1, keepdims=True)
    n = np.where(isg[:, None], tn, n)
    good = (nn > 1e-6) | isg
    n = n[good]
    rng_ = STEPS[first[r]][good]
    self_ground_share = float(isg[good].mean()) if good.any() else 0.0
    return n, rng_, o


def metric(W, x, y):
    s = scan(W, x, y)
    if s is None:
        return None
    n, rg, o = s
    if len(n) < 50:
        return None
    M = (n[:, :, None] * n[:, None, :]).mean(0)
    w, V = np.linalg.eigh(M)
    zc = np.abs(n[:, 2])
    return dict(a=w[0], b=w[1], c=w[2], npts=len(n), med_range=float(np.median(rg)), far=float((rg > 30).mean()),
                vert=float((zc < 0.5).mean()))


def route_stats(W, xy, name):
    res = [metric(W, x, y) for x, y in xy]
    res = [r for r in res if r]
    a = np.array([r['a'] for r in res]); b = np.array([r['b'] for r in res])
    rg = np.array([r['med_range'] for r in res]); npts = np.array([r['npts'] for r in res])
    vt = np.array([r['vert'] for r in res])
    print('%-38s n=%3d  a median %.3f p10 %.3f min %.3f | a<0.02: %3.0f%%  a<0.05: %3.0f%% | vertical-surface hits %2.0f%% (min %2.0f%%) of %d/scan'
          % (name, len(a), np.median(a), np.percentile(a, 10), a.min(), 100 * (a < 0.02).mean(), 100 * (a < 0.05).mean(), 100 * np.median(vt), 100 * vt.min(), np.median(npts)))
    return a
