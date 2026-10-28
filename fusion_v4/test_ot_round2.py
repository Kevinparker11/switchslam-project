#!/usr/bin/env python3
"""Checks of the round-2 OT rules (fusion_core.ot_matrix_rule / t_weight), the projected VIO check and scan_tensors_ext.
numpy only.  usage: python3 test_ot_round2.py"""
import numpy as np
import fusion_core as fc
import structure_heading as shd

rng = np.random.default_rng(3)
ok = []


def check(name, cond):
    ok.append(bool(cond))
    print("%-62s %s" % (name, "ok" if cond else "FAIL"))


def rand_psd(scale=1.0, cond=50.0):
    Q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    lam = scale * np.exp(rng.uniform(0, np.log(cond), 3))
    return (Q * lam) @ Q.T


def loewner_le(X, Y, tol=1e-7):
    """X <= Y in the Loewner order (relative tolerance)"""
    return np.linalg.eigvalsh(0.5 * ((Y - X) + (Y - X).T)).min() >= -tol * max(np.abs(Y).max(), 1.0)


# 1. matrix rules: identities and orderings
for k in range(200):
    A, B = rand_psd(10.0), rand_psd(10.0)
    gmin, gmax = fc.ot_matrix_rule("gmin", A, B), fc.ot_matrix_rule("gmax", A, B)
    hm = 0.5 * fc.ot_matrix_rule("psum", A, B)                 # harmonic mean
    gm = fc.ot_matrix_rule("agm", A, B)
    if k == 0:
        first = (gmin, gmax, hm, gm, A, B)
    good = (loewner_le(gmin, A) and loewner_le(gmin, B) and loewner_le(A, gmax) and loewner_le(B, gmax)
            and loewner_le(hm, gm) and loewner_le(gm, 0.5 * (A + B)))
    if not good:
        break
check("gmin <= A, B <= gmax; harmonic <= geometric <= arithmetic (200 pairs)", good)
A = rand_psd(5.0)
same = all(np.allclose(fc.ot_matrix_rule(m, A, A), A, rtol=1e-6, atol=1e-9) for m in ("gmin", "gmax", "psum", "agm", "ci"))
check("A = B gives A for gmin, gmax, psum, agm, ci", same)
# basis-free: rotating both inputs rotates the output
Q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
A, B = rand_psd(4.0), rand_psd(4.0)
inv = all(np.allclose(fc.ot_matrix_rule(m, Q @ A @ Q.T, Q @ B @ Q.T), Q @ fc.ot_matrix_rule(m, A, B) @ Q.T, rtol=1e-6, atol=1e-8)
          for m in ("gmin", "gmax", "psum", "agm", "ci"))
check("matrix rules are rotation-equivariant", inv)
# rank-deficient geometry (corridor: no support along x) -> gmin removes x
A = np.diag([5.0, 8.0, 9.0]); B = np.diag([1e-12, 10.0, 10.0])
g = fc.ot_matrix_rule("gmin", A, B)
check("gmin with B degenerate along x removes the solver's x information", g[0, 0] < 1e-6 * A[0, 0] and abs(g[1, 1] - 8.0) < 1e-6)

# 2. t_weight: weights are symmetric, PSD and <= I; W-rules sit between / below
H = np.zeros((6, 6)); H[:3, :3] = np.diag([40.0, 50.0, 60.0]); H[3:, 3:] = np.diag([30.0, 400.0, 500.0])
S_RR, S_tt, _, _ = fc.schur_blocks(H, "body")
T = np.diag([0.02, 0.48, 0.50])
allok = True
for m in fc.T_MODES + fc.T_MODES2:
    W, r = fc.t_weight(m, H, S_tt, T, 0.03, 1.0, "body")
    e = np.linalg.eigvalsh(0.5 * (W + W.T))
    allok &= bool(np.allclose(W, W.T, atol=1e-12) and e.min() >= -1e-12 and e.max() <= 1.0 + 1e-12 and np.isfinite(r))
check("t_weight: every rule gives a symmetric PSD weight <= I", allok)
WA = fc.info_weight(S_tt, 0.03); Wp, _ = fc.t_weight("wprod", H, S_tt, T, 0.03, 1.0, "body")
check("wprod <= W_A (the OT weight can only lower the Schur weight)", loewner_le(Wp, WA))
Wmin, _ = fc.t_weight("min", H, S_tt, T, 0.03, 1.0, "body")
S2, _ = fc.t_combine("min", H, S_tt, T, "body")
check("t_weight('min') equals info_weight(t_combine('min')) exactly (F20 unchanged)", np.array_equal(Wmin, fc.info_weight(S2, 0.03, 1.0)))

# 3. projected VIO check: LiDAR degenerate along the corridor axis x, the VIO overestimates x motion by 2x
def run_check(proj):
    chk = fc.VioConsistency(ref=0.2, stat="scale", rule="gate", avg=5.0, n_min=10, proj=proj, start_trusted=True)
    P = np.diag([0.0, 0.95, 0.95])                    # LiDAR translation weight: nothing along x
    pa, pv = np.zeros(3), np.zeros(3)
    for k in range(600):                              # 60 s at 10 Hz, 1 m/s along x with a slow sideways sway
        t = 0.1 * k
        da = np.array([0.1, 0.05 * np.cos(0.3 * t), 0.0])
        dv = np.array([0.2, 0.05 * np.cos(0.3 * t), 0.0])
        pa, pv = pa + da, pv + dv
        chk.update(t, (np.eye(3), pa.copy()), (np.eye(3), pv.copy()), np.eye(3), np.zeros(3),
                   inc=(P @ da, P @ dv) if proj else None)
    return chk.gamma()
check("unprojected check blames the VIO for the LiDAR-degenerate axis", run_check(False) == 0.0)
check("projected check does not judge along the degenerate axis", run_check(True) == 1.0)

def run_check2(proj):
    """the VIO is wrong across the corridor (a direction the LiDAR does constrain) -> both checks must close"""
    chk = fc.VioConsistency(ref=0.2, stat="scale", rule="gate", avg=5.0, n_min=10, proj=proj, start_trusted=True)
    P = np.diag([0.0, 0.95, 0.95])
    pa, pv = np.zeros(3), np.zeros(3)
    for k in range(600):
        t = 0.1 * k
        da = np.array([0.05, 0.15, 0.0]); dv = np.array([0.05, 0.4, 0.0])
        pa, pv = pa + da, pv + dv
        chk.update(t, (np.eye(3), pa.copy()), (np.eye(3), pv.copy()), np.eye(3), np.zeros(3),
                   inc=(P @ da, P @ dv) if proj else None)
    return chk.gamma()
check("projected check still closes when the VIO is wrong where the LiDAR is constrained", run_check2(True) == 0.0)

# 4. scan_tensors_ext: identical normals / T / G to scan_tensors; G3 and GS have the stated traces
P = np.concatenate([np.c_[rng.uniform(0, 20, 3000), rng.uniform(-1.5, 1.5, 3000), np.zeros(3000)],          # floor
                    np.c_[rng.uniform(0, 20, 2000), np.full(2000, 1.5), rng.uniform(0, 2.5, 2000)],          # wall
                    np.c_[rng.uniform(0, 20, 2000), np.full(2000, -1.5), rng.uniform(0, 2.5, 2000)],         # wall
                    rng.normal([10, 0, 1.2], 0.3, (400, 3))]) + rng.normal(0, 0.005, (7400, 3))             # clutter
nb, pl, T1, G1 = shd.scan_tensors(P)
nb2, pl2, T2, G2, G3, GS, GRF = shd.scan_tensors_ext(P)
check("scan_tensors_ext reproduces scan_tensors exactly", np.array_equal(nb, nb2) and np.array_equal(T1, T2) and np.array_equal(G1, G2))
check("tr(G3) = 1, tr(GS) <= tr(G) = 1, GS PSD", abs(np.trace(G3) - 1) < 1e-9 and np.trace(GS) <= 1 + 1e-9 and np.linalg.eigvalsh(GS).min() > -1e-9)
check("corridor: T weak along the axis x; the Schur block GS <= G (Loewner)", T2[0, 0] < 0.02 and loewner_le(GS, G2))

print("ALL OK" if all(ok) else "SOME CHECKS FAILED (%d of %d ok)" % (sum(ok), len(ok)))
