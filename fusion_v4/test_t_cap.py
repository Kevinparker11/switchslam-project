#!/usr/bin/env python3
"""Synthetic checks of the additional-T fail-safe (fusion_core.t_cap_info / FusionCore(t_cap=True)). numpy only.
1. T off, or no T for a scan  -> bit-identical to F8.
2. Hessian built from the same normals as T -> the cap never binds (S_tt <= H_tt), ratio = 1, W unchanged.
3. Hessian inflated by wrong correspondences (isotropic fill) while T has no axial normals -> the axial weight falls, the others stay.
4. orientation_tensor on a synthetic corridor: smallest eigenvector along the corridor axis, trace 1.
"""
import numpy as np
import fusion_core as fc

rng = np.random.default_rng(1)


def hessian_from_normals(n, extra_iso=0.0):
    """point-to-plane Hessian, [rot(3), trans(3)] order as A-LOAM publishes; points on a sphere of radius 5 around the origin"""
    H = np.zeros((6, 6))
    for ni in n:
        p = rng.normal(size=3); p = 5 * p / np.linalg.norm(p)
        J = np.concatenate([np.cross(p, ni), ni])
        H += np.outer(J, J)
    if extra_iso > 0:
        m = int(extra_iso * len(n))
        for _ in range(m):
            ni = rng.normal(size=3); ni /= np.linalg.norm(ni)
            p = rng.normal(size=3); p = 5 * p / np.linalg.norm(p)
            J = np.concatenate([np.cross(p, ni), ni])
            H += np.outer(J, J)
    return H


def corridor_normals(N, axial_frac):
    """corridor along x: normals in the y-z plane, a fraction axial_frac along x"""
    n = []
    for _ in range(N):
        if rng.random() < axial_frac:
            v = np.array([1.0, 0.02 * rng.normal(), 0.02 * rng.normal()])
        else:
            a = rng.choice([0, 1]); v = np.array([0.0, 1.0, 0.0]) if a else np.array([0.0, 0.0, 1.0])
            v = v + 0.03 * rng.normal(size=3)
        n.append(v / np.linalg.norm(v))
    return np.array(n)


def tensor(n):
    return n.T @ n / len(n)


# --- 2. identical inputs: cap does not bind
n = corridor_normals(3000, 0.01)
H = hessian_from_normals(n)
T = tensor(n)
S_RR, S_tt, kR, kt = fc.schur_blocks(H, "body")
S2, ratio = fc.t_cap_info(H, S_tt, T, "body")
print("identical inputs: ratio %.4f" % ratio)
assert ratio > 0.4, "the cap should be mild when H and T come from the same normals (different random points, so not exactly 1)"
# exact identity case: H_tt = N T, no rotation block
Hid = np.zeros((6, 6)); Hid[3:, 3:] = len(n) * T; Hid[:3, :3] = np.eye(3) * 50
_, S_id, _, _ = fc.schur_blocks(Hid, "body")
_, r_id = fc.t_cap_info(Hid, S_id, T, "body")
print("exact H_tt = N T: ratio %.6f" % r_id)
assert abs(r_id - 1.0) < 1e-9

# --- 3. wrong correspondences inflate the solver's belief, T (raw scan) has almost no axial normals
n_true = corridor_normals(3000, 0.0)
H_bad = hessian_from_normals(n_true, extra_iso=0.30)     # 30 % wrong matches with random normals
T_true = tensor(n_true)
_, S_bad, _, _ = fc.schur_blocks(H_bad, "body")
S_cap, r_bad = fc.t_cap_info(H_bad, S_bad, T_true, "body")
ex = np.array([1.0, 0, 0])
w_before = fc.info_weight(S_bad, 0.03); w_after = fc.info_weight(S_cap, 0.03)
print("axial weight  uncapped %.4f  capped %.4f   (ratio %.3f);  y-z weights %.3f/%.3f -> %.3f/%.3f" % (
    ex @ w_before @ ex, ex @ w_after @ ex, r_bad, w_before[1, 1], w_before[2, 2], w_after[1, 1], w_after[2, 2]))
assert ex @ w_after @ ex < ex @ w_before @ ex
assert w_after[1, 1] >= 0.9 * w_before[1, 1] and w_after[2, 2] >= 0.9 * w_before[2, 2]

# --- 1. FusionCore: off / no T -> identical
def run(core, T3):
    Rf = np.eye(3); out = []
    t = 0.0; pa = np.zeros(3); pv = np.zeros(3)
    for k in range(60):
        t += 0.1
        pa = pa + np.array([0.05, 0.0, 0.0]); pv = pv + np.array([0.048, 0.001, 0.0])
        R, p, info = core.step(t, (np.eye(3), pa), (np.eye(3), pv), H_bad, T3=T3)
        out.append(p.copy())
    return np.array(out), info

kw = dict(c_t=3e-2, gate=fc.KappaGate(kth=1e9), t_warm=0.0, hess_frame="body")
a, _ = run(fc.FusionCore(**kw), None)
b, _ = run(fc.FusionCore(t_cap=False, **kw), T_true)        # flag off: T ignored
c, _ = run(fc.FusionCore(t_cap=True, **kw), None)           # flag on, no T: uncapped
assert np.array_equal(a, b) and np.array_equal(a, c)
d, info = run(fc.FusionCore(t_cap=True, **kw), T_true)
print("with T: final x %.4f (uncapped %.4f);  tcap_ratio %.3f" % (d[-1, 0], a[-1, 0], info["tcap_ratio"]))
assert not np.array_equal(a, d)

# --- 4. orientation_tensor
pts = []
for _ in range(2500):
    x = rng.uniform(0, 20); s = rng.integers(0, 3)
    if s == 0: pts.append([x, 1.5, rng.uniform(-1, 1)])
    elif s == 1: pts.append([x, -1.5, rng.uniform(-1, 1)])
    else: pts.append([x, rng.uniform(-1.5, 1.5), -1.0])
pts = np.array(pts) + 0.005 * rng.normal(size=(2500, 3))
Tt, nn = fc.orientation_tensor(pts, 12, 400, np.random.default_rng(0))
lam, vec = np.linalg.eigh(Tt)
print("corridor T eigenvalues %s, weak axis %s, trace %.6f, n %d" % (np.round(lam, 4), np.round(np.abs(vec[:, 0]), 3), np.trace(Tt), nn))
assert abs(np.trace(Tt) - 1) < 1e-9 and abs(vec[0, 0]) > 0.99 and lam[0] < 0.02
# --- 5. all OT rules: positive semidefinite, ordered min <= harm <= gmean <= max per direction, tonly = tau
for H_, T_ in ((H_bad, T_true), (H, T)):
    _, S_ = fc.schur_blocks(H_, "body")[:2]
    lam, V = np.linalg.eigh(0.5 * (S_ + S_.T))
    vals = {}
    for m in fc.T_MODES:
        Sm, r = fc.t_combine(m, H_, S_, T_, "body")
        assert np.linalg.eigvalsh(0.5 * (Sm + Sm.T)).min() > -1e-6, m
        vals[m] = np.einsum("ij,jk,ki->i", V.T, Sm, V)
    assert np.all(vals["min"] <= vals["harm"] + 1e-6) and np.all(vals["harm"] <= vals["gmean"] + 1e-6) and np.all(vals["gmean"] <= vals["max"] + 1e-6)
    N = np.trace((fc.D_RAD @ (0.5 * (H_ + H_.T)) @ fc.D_RAD)[3:, 3:])
    assert np.allclose(vals["tonly"], N * np.einsum("ij,jk,ki->i", V.T, T_, V), rtol=1e-6)
print("OT rules: PSD, ordered, tonly = tau  ok")
print("ALL CHECKS PASSED")
