import sys, numpy as np
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "0"]
import synth_scenes as ss
import structure_heading as shd
from scipy.spatial import cKDTree

def pca(P, idx):
    Q = P[idx] - P[idx].mean(1, keepdims=True)
    w, v = np.linalg.eigh(np.einsum("nki,nkj->nij", Q, Q) / idx.shape[1])
    return w, v

def G_ms(P, k1=12, k2=36):
    """multi-scale: planar at k2 -> plane (n from k2); else linear at k1 and k2 -> line (d from k2); else planar at k1 -> plane"""
    tr = cKDTree(P)
    i1 = tr.query(P, k1)[1]; i2 = tr.query(P, min(k2, len(P)))[1]
    w1, v1 = pca(P, i1); w2, v2 = pca(P, i2)
    pl1 = (w1[:, 1] - w1[:, 0]) / np.maximum(w1[:, 2], 1e-12); li1 = (w1[:, 2] - w1[:, 1]) / np.maximum(w1[:, 2], 1e-12)
    pl2 = (w2[:, 1] - w2[:, 0]) / np.maximum(w2[:, 2], 1e-12); li2 = (w2[:, 2] - w2[:, 1]) / np.maximum(w2[:, 2], 1e-12)
    P2 = pl2 > 0.5
    L = ~P2 & (li1 > 0.5) & (li2 > 0.5)
    P1 = ~P2 & ~L & (pl1 > 0.5)
    n = np.concatenate([v2[P2, :, 0], v1[P1, :, 0]]); d = v2[L, :, 2]
    tot = len(n) + len(d)
    return (n.T @ n + 0.5 * (len(d) * np.eye(3) - d.T @ d)) / tot, len(n), len(d)

def smin(A, B):
    lam, V = np.linalg.eigh(A); lam = np.clip(lam, 0, None)
    tau = np.clip(np.einsum("ij,jk,ki->i", V.T, B, V), 0, None)
    lam2 = np.minimum(lam, tau * lam.max() / max(tau.max(), 1e-300))
    return (V * lam2) @ V.T

if __name__ == '__main__':
  for name, prims in ss.scenes().items():
      P, ok = ss.cast(prims)
      H, ne, ns = ss.aloam_hessian(P, ok)
      A = ss.schur_tt(H); A = 0.5 * (A + A.T); N = np.trace(H[3:, 3:])
      lam, V = np.linalg.eigh(A); vw = V[:, 0]; c = (0.91 / 0.09) / lam[-1]
      Pk = P[ok]; r = np.linalg.norm(Pk, axis=1); Pk = ss.voxel(Pk[(r > 1) & (r < 60)], 0.25)
      if len(Pk) > 6000: Pk = Pk[ss.rng.choice(len(Pk), 6000, replace=False)]
      _, _, T, G, G3, GS = shd.scan_tensors_ext(Pk)
      Gm, npl, nli = G_ms(Pk)
      Hf = H.copy(); Hf[3:, 3:] = np.trace(H[3:, 3:]) / 3 * np.eye(3); Af = ss.schur_tt(Hf); Af = 0.5 * (Af + Af.T)
      wv = lambda W: float(vw @ W @ vw)
      ws = lambda W: float(V[:, 2] @ W @ V[:, 2])
      out = []
      for tn, X in (("G", G), ("Gms", Gm), ("T", T)):
          B = N * X
          tau = np.einsum("ij,jk,ki->i", V.T, B, V)
          for rn, f in (("min", lambda A_, B_: ss.weight("min", A_, B_, c)), ("smin", lambda A_, B_: ss.fc.info_weight(smin(A_, B_), c))):
              out.append("%s/%s weak h %.3f f %.3f strong h %.3f" % (rn, tn, wv(f(A, B)), wv(f(Af, B)), ws(f(A, B))))
      print("%-12s none weak h %.3f f %.3f strong %.3f | Gms lines %d planes %d | x,y,z share G %s Gms %s" % (name, wv(ss.fc.info_weight(A, c)), wv(ss.fc.info_weight(Af, c)), ws(ss.fc.info_weight(A, c)), nli, npl, np.round(np.diag(G), 2), np.round(np.diag(Gm), 2)))
      print("     " + " | ".join(out), flush=True)
