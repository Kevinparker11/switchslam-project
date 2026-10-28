import sys, numpy as np
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "0"]
import synth_scenes as ss
import structure_heading as shd
from synth_proto import smin   # noqa  (re-runs nothing: guarded below)
from scipy.spatial import cKDTree

def G_rf(P, k=12, cos_max=np.cos(np.radians(30))):
    """geometric tensor without scan-direction lines: a 'line' whose direction is within 30 deg of the azimuthal scan
    direction at that point (tangent of the LiDAR's sweep) is the ring sampling of a surface, not an edge -> dropped"""
    idx = cKDTree(P).query(P, k)[1]
    Q = P[idx] - P[idx].mean(1, keepdims=True)
    w, v = np.linalg.eigh(np.einsum("nki,nkj->nij", Q, Q) / k)
    pl = (w[:, 1] - w[:, 0]) / np.maximum(w[:, 2], 1e-12); li = (w[:, 2] - w[:, 1]) / np.maximum(w[:, 2], 1e-12)
    m = pl > 0.5; ml = (li > 0.5) & ~m
    d = v[:, :, 2]
    tng = np.c_[-P[:, 1], P[:, 0], np.zeros(len(P))]; tng /= np.maximum(np.linalg.norm(tng, axis=1, keepdims=True), 1e-9)
    ring = np.abs((d * tng).sum(1)) > cos_max
    ml2 = ml & ~ring
    n = v[m, :, 0]; dd = d[ml2]
    tot = len(n) + len(dd)
    return (n.T @ n + 0.5 * (len(dd) * np.eye(3) - dd.T @ dd)) / tot, ml.sum(), ml2.sum()

for name, prims in ss.scenes().items():
    P, ok = ss.cast(prims)
    H, ne, ns = ss.aloam_hessian(P, ok)
    A = ss.schur_tt(H); A = 0.5 * (A + A.T); N = np.trace(H[3:, 3:])
    lam, V = np.linalg.eigh(A); vw = V[:, 0]; c = (0.91 / 0.09) / lam[-1]
    Pk = P[ok]; r = np.linalg.norm(Pk, axis=1); Pk = ss.voxel(Pk[(r > 1) & (r < 60)], 0.25)
    if len(Pk) > 6000: Pk = Pk[ss.rng.choice(len(Pk), 6000, replace=False)]
    _, _, T, G, G3, GS = shd.scan_tensors_ext(Pk)
    Gr, nl, nl2 = G_rf(Pk)
    Hf = H.copy(); Hf[3:, 3:] = np.trace(H[3:, 3:]) / 3 * np.eye(3); Af = ss.schur_tt(Hf); Af = 0.5 * (Af + Af.T)
    wv = lambda W: float(vw @ W @ vw)
    allw = lambda W: np.round(np.sort(np.linalg.eigvalsh(W)), 2)
    out = []
    for tn, X in (("G", G), ("Grf", Gr)):
        B = N * X
        for rn, f in (("min", lambda A_, B_: ss.weight("min", A_, B_, c)), ("smin", lambda A_, B_: ss.fc.info_weight(smin(A_, B_), c))):
            out.append("%s/%s weak h %.3f f %.3f, honest W eig %s" % (rn, tn, wv(f(A, B)), wv(f(Af, B)), allw(f(A, B))))
    print("%-12s none weak h %.3f f %.3f W eig %s | lines %d -> %d | diag G %s Grf %s" % (name, wv(ss.fc.info_weight(A, c)), wv(ss.fc.info_weight(Af, c)), allw(ss.fc.info_weight(A, c)), nl, nl2, np.round(np.diag(G), 2), np.round(np.diag(Gr), 2)))
    print("     " + " | ".join(out), flush=True)
