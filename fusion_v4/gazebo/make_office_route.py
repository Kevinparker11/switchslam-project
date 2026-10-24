#!/usr/bin/env python3
"""Plan the one-lap route through the Clearpath office world and write routes/office_loop.csv (x, y per 0.25 m).
usage: python3 make_office_route.py <path to cpr_office_gazebo/meshes/office.dae> [out.csv]
Rasterises the mesh (obstacles = surface between 0.15 and 1.2 m height), keeps cells with at least 0.55 m clearance (Husky
half-width 0.34 m plus margin), and joins hand-picked waypoints with A* (cost grows near walls). Needs numpy, scipy."""
import sys, heapq
import numpy as np
import xml.etree.ElementTree as ET
from scipy import ndimage as ndi
from scipy.ndimage import uniform_filter1d
NS = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
RES, X0, Y0, WX, WY, CLEAR = 0.1, -16.0, -13.0, 46.0, 27.0, 0.55
# waypoints (x, y): left wing incl. the dead-end lobe (entered and left by the same passage), centre, the ~10 m narrow hallway
# along y = 1, right wing, and back to the start
WAYPOINTS = [(0, 0), (-6, 3), (-11, 3.5), (-11.5, -1.5), (-8.5, -3), (-8.5, -8), (-8.5, -3), (-6, 1), (-1, 0.5), (2, 4), (-1, 5),
             (0, 0.5), (12, 6), (13, 10.5), (14.5, 6), (20, 0.5), (25, -3), (20, -1), (14, 3), (5, 1), (0, 0)]

def triangles(dae):
    t = ET.parse(dae); geo = {}
    for g in t.iterfind('.//c:geometry', NS):
        m = g.find('c:mesh', NS)
        pos = [i for i in m.find('c:vertices', NS).iterfind('c:input', NS) if i.get('semantic') == 'POSITION'][0].get('source')[1:]
        src = [s for s in m.iterfind('c:source', NS) if s.get('id') == pos][0]
        a = np.array(src.find('c:float_array', NS).text.split(), float).reshape(-1, 3); tr = []
        for p in m.iterfind('c:triangles', NS):
            ins = list(p.iterfind('c:input', NS)); off = max(int(i.get('offset')) for i in ins) + 1
            vo = [int(i.get('offset')) for i in ins if i.get('semantic') == 'VERTEX'][0]
            tr.append(np.array(p.find('c:p', NS).text.split(), int)[vo::off].reshape(-1, 3))
        for p in m.iterfind('c:polylist', NS):
            ins = list(p.iterfind('c:input', NS)); off = max(int(i.get('offset')) for i in ins) + 1
            vo = [int(i.get('offset')) for i in ins if i.get('semantic') == 'VERTEX'][0]
            vc = np.array(p.find('c:vcount', NS).text.split(), int); arr = np.array(p.find('c:p', NS).text.split(), int)[vo::off]
            k = 0; out = []
            for c in vc:
                out += [[arr[k], arr[k + j], arr[k + j + 1]] for j in range(1, c - 1)]; k += c
            tr.append(np.array(out))
        geo[g.get('id')] = (a, np.vstack(tr))
    T = []
    for n in t.iterfind('.//c:visual_scene/c:node', NS):
        mat = n.find('c:matrix', NS); ig = n.find('c:instance_geometry', NS)
        if ig is None: continue
        M = np.array(mat.text.split(), float).reshape(4, 4) if mat is not None else np.eye(4)
        a, tr = geo[ig.get('url')[1:]]; T.append(((a @ M[:3, :3].T) + M[:3, 3])[tr])
    return np.vstack(T)

def main():
    dae = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else "routes/office_loop.csv"
    T = triangles(dae); W, H = int(WX / RES), int(WY / RES)
    occ = np.zeros((H, W), bool); floor = np.zeros((H, W), bool); rng = np.random.default_rng(0)
    for A, B, C in T:
        n = int(max(3, 0.5 * np.linalg.norm(np.cross(B - A, C - A)) / (RES * RES) * 4))
        r1, r2 = rng.random(n), rng.random(n); f = r1 + r2 > 1; r1[f], r2[f] = 1 - r1[f], 1 - r2[f]
        P = A + np.outer(r1, B - A) + np.outer(r2, C - A)
        for sel, grid in ((P[(P[:, 2] > 0.15) & (P[:, 2] < 1.2)], occ), (P[P[:, 2] < 0.15], floor)):
            ix = ((sel[:, 0] - X0) / RES).astype(int); iy = ((sel[:, 1] - Y0) / RES).astype(int)
            ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H); grid[iy[ok], ix[ok]] = True
    free = ndi.binary_fill_holes(ndi.binary_closing(floor | occ, iterations=3)) & ~occ
    dist = ndi.distance_transform_edt(free) * RES
    cell = lambda x, y: (int(round((y - Y0) / RES)), int(round((x - X0) / RES)))
    lab, _ = ndi.label(dist > CLEAR); reach = lab == lab[cell(0, 0)]
    cost = 1 + 3 * np.clip(1.5 - dist, 0, None)
    def astar(a, b):
        sa, sb = cell(*a), cell(*b); assert reach[sa] and reach[sb], "waypoint not reachable: %s -> %s" % (a, b)
        g = {sa: 0}; pq = [(0, sa)]; came = {}
        while pq:
            _, u = heapq.heappop(pq)
            if u == sb: break
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                v = (u[0] + di, u[1] + dj)
                if not (0 <= v[0] < H and 0 <= v[1] < W) or not reach[v]: continue
                c = g[u] + cost[v] * (1.414 if di and dj else 1)
                if c < g.get(v, 1e18): g[v] = c; came[v] = u; heapq.heappush(pq, (c + np.hypot(v[0] - sb[0], v[1] - sb[1]), v))
        p = [sb]
        while p[-1] != sa: p.append(came[p[-1]])
        return np.array([(X0 + j * RES, Y0 + i * RES) for i, j in p[::-1]])
    P = np.vstack([astar(a, b) for a, b in zip(WAYPOINTS[:-1], WAYPOINTS[1:])])
    Ps = np.c_[uniform_filter1d(P[:, 0], 9, mode='nearest'), uniform_filter1d(P[:, 1], 9, mode='nearest')]
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(Ps, axis=0).T))]; t = np.arange(0, s[-1], 0.25)
    R = np.c_[np.interp(t, s, Ps[:, 0]), np.interp(t, s, Ps[:, 1])]
    d = np.array([dist[cell(x, y)] for x, y in R])
    print("lap %.0f m, clearance min %.2f / mean %.2f m" % (s[-1], d.min(), d.mean()))
    np.savetxt(out, R, fmt="%.3f", delimiter=",", header="x,y (m, world frame, 0.25 m spacing); one lap", comments="# ")
main()
