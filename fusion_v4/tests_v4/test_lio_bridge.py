"""Check lio_bridge.lidar_information against a numerical Jacobian of point-to-plane residuals
taken directly w.r.t. LiDAR-body perturbations, and that fusion_core recovers it from the published units."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lio_bridge as lb, fusion_core as fc
rng = np.random.default_rng(3)
def expm(w): return fc.so3_exp(w)
for trial in range(5):
    R_WI = expm(rng.normal(size=3)); p_WI = rng.normal(size=3) * 5
    R_IL = expm(rng.normal(size=3) * 0.2); t_IL = rng.normal(size=3) * 0.3
    N = 200
    pL = rng.normal(size=(N, 3)) * 6
    nW = rng.normal(size=(N, 3)); nW /= np.linalg.norm(nW, axis=1, keepdims=True)
    w = rng.uniform(10, 1000, N)                       # inverse variances
    # GenZ rows: [n_W, A], A = [p_body]x R_WI^T n
    pB = pL @ R_IL.T + t_IL
    rows = np.array([np.r_[nW[i], lb.skew(pB[i]) @ R_WI.T @ nW[i]] for i in range(N)])
    Hx = rows.T @ (w[:, None] * rows)
    Hy = lb.lidar_information(Hx, R_WI, R_IL, t_IL)
    # numerical: residual r_i(y) = n_i . (R_WL Exp(th) pL_i + p_WL + R_WL dt)
    R_WL = R_WI @ R_IL; p_WL = p_WI + R_WI @ t_IL
    def res(y):
        Rp = R_WL @ expm(y[:3]); pp = p_WL + R_WL @ y[3:]
        return np.einsum("ij,ij->i", nW, pL @ Rp.T + pp)
    J = np.zeros((N, 6)); h = 1e-6
    for k in range(6):
        e = np.zeros(6); e[k] = h; J[:, k] = (res(e) - res(-e)) / (2 * h)
    Hnum = J.T @ (w[:, None] * J)
    err = np.linalg.norm(Hy - Hnum) / np.linalg.norm(Hnum)
    # fusion_core view: schur_blocks(D_INV Hy D_INV, body) must equal the Schur blocks of Hy
    S_RR, S_tt, kR, kt = fc.schur_blocks(lb.aloam_units(Hy), "body")
    Srr = Hy[:3, :3] - Hy[:3, 3:] @ np.linalg.solve(Hy[3:, 3:], Hy[3:, :3])
    Stt = Hy[3:, 3:] - Hy[3:, :3] @ np.linalg.solve(Hy[:3, :3], Hy[:3, 3:])
    e2 = max(np.linalg.norm(S_RR - Srr) / np.linalg.norm(Srr), np.linalg.norm(S_tt - Stt) / np.linalg.norm(Stt))
    print("trial %d: relative error vs numerical %.2e | fusion_core Schur blocks %.2e" % (trial, err, e2))
    assert err < 1e-6 and e2 < 1e-9
print("lio_bridge information transform OK")
