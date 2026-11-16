"""Rasterise a Clearpath world mesh (Collada) into a top-down map: ground height, structure mask,
and report straight open runs. Usage: mapworld.py mesh.dae yaw_rad out_prefix [xy_scale z_scale]"""
import sys
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

NS = '{http://www.collada.org/2005/11/COLLADASchema}'


def tris_of(path):
    r = ET.parse(path).getroot()
    u = r.find('.//' + NS + 'unit')
    sc = float(u.attrib.get('meter', 1)) if u is not None else 1.0
    geoms = {}
    for g in r.iter(NS + 'geometry'):
        m = g.find(NS + 'mesh')
        srcs = {}
        for s in m.findall(NS + 'source'):
            fa = s.find(NS + 'float_array')
            if fa is not None:
                srcs[s.attrib['id']] = np.array(fa.text.split(), float)
        vmap = {}
        for v in m.findall(NS + 'vertices'):
            for i in v.findall(NS + 'input'):
                if i.attrib['semantic'] == 'POSITION':
                    vmap[v.attrib['id']] = i.attrib['source'][1:]
        T = []
        for el in list(m.findall(NS + 'triangles')) + list(m.findall(NS + 'polylist')):
            inputs = el.findall(NS + 'input')
            stride = max(int(i.attrib['offset']) for i in inputs) + 1
            voff = None
            for i in inputs:
                if i.attrib['semantic'] == 'VERTEX':
                    voff = int(i.attrib['offset'])
                    pid = vmap[i.attrib['source'][1:]]
            P = srcs[pid].reshape(-1, 3) * sc
            p = np.array(el.find(NS + 'p').text.split(), int).reshape(-1, stride)[:, voff]
            if el.tag == NS + 'triangles':
                T.append(P[p].reshape(-1, 3, 3))
            else:
                vc = np.array(el.find(NS + 'vcount').text.split(), int)
                k = 0
                for c in vc:
                    idx = p[k:k + c]
                    for j in range(1, c - 1):
                        T.append(P[[idx[0], idx[j], idx[j + 1]]].reshape(1, 3, 3))
                    k += c
        if T:
            geoms[g.attrib['id']] = np.vstack(T)
    # node transforms
    out = []
    for n in r.iter(NS + 'node'):
        ig = n.find(NS + 'instance_geometry')
        if ig is None:
            continue
        gid = ig.attrib['url'][1:]
        if gid not in geoms:
            continue
        mat = n.find(NS + 'matrix')
        M = np.array(mat.text.split(), float).reshape(4, 4) if mat is not None else np.eye(4)
        M[:3, 3] *= sc
        A = geoms[gid]
        A = A @ M[:3, :3].T + M[:3, 3]
        out.append(A)
    return np.vstack(out) if out else np.vstack(list(geoms.values()))


def raster(T, res=1.0, step=0.5):
    # sample points on every triangle
    pts = []
    for a, b, c in T:
        area = np.linalg.norm(np.cross(b - a, c - a)) / 2
        n = int(max(1, min(400, area / (step * step))))
        u = np.random.rand(n, 1)
        v = np.random.rand(n, 1)
        m = (u + v) > 1
        u[m] = 1 - u[m]
        v[m] = 1 - v[m]
        pts.append(a + u * (b - a) + v * (c - a))
    return np.vstack(pts)


if __name__ == '__main__':
    path, yaw, outp = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    xs = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    zs = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    np.random.seed(0)
    T = tris_of(path)
    T = T * np.array([xs, xs, zs])
    c, s = np.cos(yaw), np.sin(yaw)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    T = T @ R.T
    P = raster(T)
    print('triangles', len(T), 'points', len(P), 'x', P[:, 0].min().round(1), P[:, 0].max().round(1),
          'y', P[:, 1].min().round(1), P[:, 1].max().round(1), 'z', P[:, 2].min().round(1), P[:, 2].max().round(1))
    np.save(outp + '_pts.npy', P.astype(np.float32))
    res = 1.0
    x0, y0 = np.floor(P[:, 0].min()), np.floor(P[:, 1].min())
    nx = int(np.ceil(P[:, 0].max() - x0)) + 1
    ny = int(np.ceil(P[:, 1].max() - y0)) + 1
    ix = ((P[:, 0] - x0) / res).astype(int)
    iy = ((P[:, 1] - y0) / res).astype(int)
    zmin = np.full((nx, ny), np.nan)
    zmax = np.full((nx, ny), np.nan)
    for i, j, z in zip(ix, iy, P[:, 2]):
        if np.isnan(zmin[i, j]) or z < zmin[i, j]:
            zmin[i, j] = z
        if np.isnan(zmax[i, j]) or z > zmax[i, j]:
            zmax[i, j] = z
    np.savez(outp + '_grid.npz', zmin=zmin, zmax=zmax, x0=x0, y0=y0, res=res)
    fig, ax = plt.subplots(1, 2, figsize=(16, 7))
    ext = [x0, x0 + nx, y0, y0 + ny]
    im = ax[0].imshow(zmin.T, origin='lower', extent=ext, cmap='terrain')
    ax[0].set_title('ground height (min z per 1 m cell)')
    plt.colorbar(im, ax=ax[0], shrink=0.7)
    h = zmax - zmin
    ax[1].imshow((h > 0.8).T, origin='lower', extent=ext, cmap='gray_r')
    ax[1].set_title('structure (cells with > 0.8 m of vertical extent)')
    for a in ax:
        a.set_xlabel('x [m]')
        a.set_ylabel('y [m]')
        a.grid(alpha=.3)
    plt.tight_layout()
    plt.savefig(outp + '_map.png', dpi=80)
