"""Round 2 of the OT study, channel-level test on synthetic scenes (PREREG2.md, last section).
VLP-16-like scans are ray-cast in eight scenes; an A-LOAM-like front end (ring curvature -> edge / surf features, lines and
planes fitted to 5 nearest feature points, as laserMapping does) gives an honest solver Hessian H; the keyframe orientation
tensors (T, G, G3, GS) come from the voxelised full scan exactly as in the node.  For each scene:
  honest solver: tau_i / lambda_i along the solver's eigen-directions (the cap binds where < 1) and the LiDAR weight along
                 the truly weakest direction for every rule;
  confident wrong solver (H_tt -> tr(H_tt)/3 I, the stage-3 fault): the LiDAR weight along that direction for every rule.
usage: python3 synth_scenes.py [seed]"""
import sys, os, numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/clean4/fusion_v4")
import fusion_core as fc
import structure_heading as shd
from scipy.spatial import cKDTree

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 0
rng = np.random.default_rng(SEED)
EL = np.radians(np.linspace(-15, 15, 16)); AZ = np.linspace(0, 2 * np.pi, 1800, endpoint=False)
DIRS = np.stack([np.cos(EL)[:, None] * np.cos(AZ)[None], np.cos(EL)[:, None] * np.sin(AZ)[None],
                 np.sin(EL)[:, None] * np.ones_like(AZ)[None]], -1)          # (16, 1800, 3)


def rect(c, n, u, hu, hv):
    n = np.asarray(n, float); n /= np.linalg.norm(n); u = np.asarray(u, float); u -= (u @ n) * n; u /= np.linalg.norm(u)
    return ("rect", np.asarray(c, float), n, u, np.cross(n, u), hu, hv)


def pole(cx, cy, r, z0, z1):
    return ("pole", cx, cy, r, z0, z1)


def tunnel(r, zc, L):
    return ("tunnel", r, zc, L)


def bush(c, r):
    return ("bush", np.asarray(c, float), r)


def cast(prims):
    D = DIRS.reshape(-1, 3)
    best = np.full(len(D), np.inf)
    for p in prims:
        t = np.full(len(D), np.inf)
        if p[0] == "rect":
            _, c, n, u, v, hu, hv = p
            den = D @ n
            with np.errstate(divide="ignore", invalid="ignore"):
                tt = (c @ n) / den
            P = D * tt[:, None]
            ok = (np.abs(den) > 1e-9) & (tt > 0.2) & (np.abs((P - c) @ u) <= hu) & (np.abs((P - c) @ v) <= hv)
            t[ok] = tt[ok]
        elif p[0] == "pole":
            _, cx, cy, r, z0, z1 = p
            a = D[:, 0] ** 2 + D[:, 1] ** 2; b = -2 * (D[:, 0] * cx + D[:, 1] * cy); cc = cx ** 2 + cy ** 2 - r ** 2
            disc = b * b - 4 * a * cc
            with np.errstate(invalid="ignore", divide="ignore"):
                tt = (-b - np.sqrt(disc)) / (2 * a)
            z = D[:, 2] * tt
            ok = (disc > 0) & (tt > 0.2) & (z >= z0) & (z <= z1)
            t[ok] = tt[ok]
        elif p[0] == "tunnel":
            _, r, zc, L = p
            a = D[:, 1] ** 2 + D[:, 2] ** 2; b = -2 * D[:, 2] * zc; cc = zc ** 2 - r ** 2
            disc = b * b - 4 * a * cc
            with np.errstate(invalid="ignore", divide="ignore"):
                tt = (-b + np.sqrt(disc)) / (2 * a)
            ok = (disc > 0) & (tt > 0.2) & (np.abs(D[:, 0] * tt) <= L)
            t[ok] = tt[ok]
        elif p[0] == "bush":
            _, c, r = p
            b = D @ c; cc = c @ c - r * r; disc = b * b - cc
            with np.errstate(invalid="ignore"):
                t1, t2 = b - np.sqrt(disc), b + np.sqrt(disc)
            ok = (disc > 0) & (t1 > 0.2)
            tt = t1 + rng.uniform(0, 0.6, len(D)) * (t2 - t1)    # foliage: the return comes from inside the crown
            t[ok] = tt[ok]
        best = np.minimum(best, t)
    best[best > 100] = np.inf
    rngs = best + rng.normal(0, 0.02, len(best))
    P = D * rngs[:, None]
    return P.reshape(16, 1800, 3), np.isfinite(best).reshape(16, 1800)


def aloam_hessian(P, ok):
    """A-LOAM-like: ring curvature (10 neighbours), edges = curvature > 0.1 (<= 20 per sector of 6), surf = the rest
    (voxel 0.4 m); point-to-line on 5 nearest edge points (accepted if l3 > 3 l2), point-to-plane on 5 nearest surf points
    (accepted if all 5 within 0.2 m of the fitted plane). Returns the 6x6 Hessian (rotation [rad] first) and counts."""
    edges, surfs = [], []
    for k in range(16):
        Q = P[k][ok[k]]
        if len(Q) < 30:
            continue
        cs = np.zeros(len(Q))
        for j in range(5, len(Q) - 5):
            d = Q[j - 5:j + 6].sum(0) - 11 * Q[j]
            cs[j] = d @ d
        idx = np.arange(5, len(Q) - 5)
        sec = np.array_split(idx, 6)
        is_edge = np.zeros(len(Q), bool)
        for s in sec:
            o = s[np.argsort(-cs[s])][:20]
            is_edge[o[cs[o] > 0.1]] = True
        edges.append(Q[is_edge]); surfs.append(Q[idx][~is_edge[idx]])
    E = np.concatenate(edges); Sf = np.concatenate(surfs)
    Sd = shd.voxel_down(Sf, 0.4) if hasattr(shd, "voxel_down") else Sf
    H = np.zeros((6, 6)); ne = ns = 0
    if len(E) >= 5:
        tr = cKDTree(E)
        for p in E:
            nn = E[tr.query(p, 5)[1]]
            w, v = np.linalg.eigh(np.cov((nn - nn.mean(0)).T))
            if w[2] > 3 * w[1]:
                d = v[:, 2]
                a = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1.0, 0])
                e1 = np.cross(d, a); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
                for e in (e1, e2):
                    J = np.r_[np.cross(p, e), e] / np.sqrt(2.0)
                    H += np.outer(J, J)
                ne += 1
    tr = cKDTree(Sf)
    for p in Sd:
        nn = Sf[tr.query(p, 5)[1]]
        w, v = np.linalg.eigh(np.cov((nn - nn.mean(0)).T))
        n = v[:, 0]
        if np.all(np.abs((nn - nn.mean(0)) @ n) < 0.2):
            J = np.r_[np.cross(p, n), n]
            H += np.outer(J, J); ns += 1
    return H, ne, ns


def voxel(P, v):
    k = np.floor(P / v).astype(np.int64)
    _, inv = np.unique(k, axis=0, return_inverse=True)
    inv = inv.ravel()
    out = np.zeros((inv.max() + 1, 3)); np.add.at(out, inv, P)
    return out / np.bincount(inv)[:, None]


def schur_tt(H):
    Hrr, Hrt, Htt = H[:3, :3], H[:3, 3:], H[3:, 3:]
    return Htt - Hrt.T @ np.linalg.solve(Hrr + 1e-9 * np.trace(Hrr) * np.eye(3), Hrt)


def scenes():
    G = -0.8
    S = {}
    S["corridor"] = [rect([0, 0, G], [0, 0, 1], [1, 0, 0], 30, 1.0), rect([0, 0, 2.2], [0, 0, 1], [1, 0, 0], 30, 1.0),
                     rect([0, 1.0, 0.7], [0, 1, 0], [1, 0, 0], 30, 1.5), rect([0, -1.0, 0.7], [0, 1, 0], [1, 0, 0], 30, 1.5)]
    S["tunnel"] = [tunnel(2.0, 0.4, 30)]
    S["room"] = [rect([0, 0, G], [0, 0, 1], [1, 0, 0], 4, 3), rect([0, 0, 2.2], [0, 0, 1], [1, 0, 0], 4, 3),
                 rect([4, 0, 0.7], [1, 0, 0], [0, 1, 0], 3, 1.5), rect([-4, 0, 0.7], [1, 0, 0], [0, 1, 0], 3, 1.5),
                 rect([0, 3, 0.7], [0, 1, 0], [1, 0, 0], 4, 1.5), rect([0, -3, 0.7], [0, 1, 0], [1, 0, 0], 4, 1.5)]
    th = rng.uniform(0, 2 * np.pi, 30); rr = rng.uniform(3, 25, 30)
    S["poles"] = [rect([0, 0, G], [0, 0, 1], [1, 0, 0], 60, 60)] + [pole(r * np.cos(a), r * np.sin(a), 0.15, G, 3.2) for a, r in zip(th, rr)]
    th = rng.uniform(0, 2 * np.pi, 40); rr = rng.uniform(3, 25, 40); rb = rng.uniform(0.5, 1.2, 40)
    th2 = rng.uniform(0, 2 * np.pi, 6); rr2 = rng.uniform(4, 20, 6)
    S["vegetation"] = ([rect([0, 0, G], [0, 0, 1], [1, 0, 0], 60, 60)] +
                       [bush([r * np.cos(a), r * np.sin(a), G + b], b) for a, r, b in zip(th, rr, rb)] +
                       [pole(r * np.cos(a), r * np.sin(a), 0.2, G, 2.0) for a, r in zip(th2, rr2)])
    S["single_wall"] = [rect([0, 0, G], [0, 0, 1], [1, 0, 0], 60, 60), rect([0, 3, 0.7], [0, 1, 0], [1, 0, 0], 30, 1.5)]
    st = [rect([-2, 0, 1.6], [1, 0, 0], [0, 1, 0], 1.0, 2.4), rect([2, 1.0, 1.6], [0, 1, 0], [1, 0, 0], 4, 2.4),
          rect([2, -1.0, 1.6], [0, 1, 0], [1, 0, 0], 4, 2.4), rect([-0.5, 0, G], [0, 0, 1], [1, 0, 0], 1.5, 1.0)]
    for i in range(10):
        x0 = 1.0 + 0.28 * i; z = G + 0.18 * (i + 1)
        st += [rect([x0 + 0.14, 0, z], [0, 0, 1], [1, 0, 0], 0.14, 1.0), rect([x0, 0, z - 0.09], [1, 0, 0], [0, 1, 0], 1.0, 0.09)]
    S["stairwell"] = st
    S["open_ground"] = [rect([0, 0, G], [0, 0, 1], [1, 0, 0], 60, 60)]
    return S


RULES = ["none", "min", "smin", "gmin", "psum", "agm", "ci", "wprod", "wmean", "gmax"]


def weight(rule, A, B, c):
    if rule == "none":
        return fc.info_weight(A, c)
    if rule == "min":
        lam, V = np.linalg.eigh(A); lam = np.clip(lam, 0, None)
        tau = np.clip(np.einsum("ij,jk,ki->i", V.T, B, V), 0, None)
        return fc.info_weight((V * np.minimum(lam, tau)) @ V.T, c)
    if rule == "smin":
        lam, V = np.linalg.eigh(A); lam = np.clip(lam, 0, None)
        tau = np.clip(np.einsum("ij,jk,ki->i", V.T, B, V), 0, None)
        return fc.info_weight((V * np.minimum(lam, tau * lam.max() / max(tau.max(), 1e-300))) @ V.T, c)
    if rule in ("wprod", "wmean"):
        WA, WB = fc.info_weight(A, c), fc.info_weight(B, c)
        if rule == "wmean":
            return 0.5 * (WA + WB)
        lw, Vw = np.linalg.eigh(WA); Wh = (Vw * np.sqrt(np.clip(lw, 0, None))) @ Vw.T
        return Wh @ WB @ Wh
    return fc.info_weight(fc.ot_matrix_rule(rule, A, B), c)


def main():
    out = []
    print("seed %d" % SEED)
    for name, prims in scenes().items():
        P, ok = cast(prims)
        H, ne, ns = aloam_hessian(P, ok)
        A = schur_tt(H); A = 0.5 * (A + A.T)
        N = np.trace(H[3:, 3:])
        lam, V = np.linalg.eigh(A); lam = np.clip(lam, 0, None)
        vw = V[:, 0]                                         # truly weakest translation direction (honest solver)
        c = (0.91 / 0.09) / max(lam[-1], 1e-12)              # operating point: strongest direction weight 0.91 (as on the logs)
        Pk = P[ok]; r = np.linalg.norm(Pk, axis=1); Pk = Pk[(r > 1.0) & (r < 60.0)]
        Pk = voxel(Pk, 0.25)
        if len(Pk) > 6000:
            Pk = Pk[rng.choice(len(Pk), 6000, replace=False)]
        nb, pl, T, Gt, G3, GS, GRF = shd.scan_tensors_ext(Pk)
        Hf = H.copy(); Hf[3:, 3:] = np.trace(H[3:, 3:]) / 3.0 * np.eye(3)
        Af = schur_tt(Hf); Af = 0.5 * (Af + Af.T)
        row = dict(scene=name, n_edge=ne, n_surf=ns, n_kf=len(Pk), lam_ratio=lam[0] / lam[-1])
        for tn, X in (("T", T), ("G", Gt), ("G3", G3), ("GS", GS), ("GRF", GRF)):
            if X is None:
                continue
            B = N * X
            tau = np.einsum("ij,jk,ki->i", V.T, B, V)
            row["min_tau_over_lam_" + tn] = float(np.min(tau / np.maximum(lam, 1e-300)))
            row["cap_loss_" + tn] = float(1 - np.minimum(lam, tau).sum() / lam.sum())
        B = N * Gt
        for rl in RULES:
            row["w_honest_" + rl] = float(vw @ weight(rl, A, B, c) @ vw)
            row["w_fault_" + rl] = float(vw @ weight(rl, Af, B, c) @ vw)
        vs = V[:, 2]
        for tn, X in (("G", Gt), ("G3", G3), ("GS", GS), ("T", T), ("GRF", GRF)):
            for rl in ("min", "smin"):
                row["w_honest_%s_%s" % (rl, tn)] = float(vw @ weight(rl, A, N * X, c) @ vw)
                row["w_fault_%s_%s" % (rl, tn)] = float(vw @ weight(rl, Af, N * X, c) @ vw)
                row["w_strong_%s_%s" % (rl, tn)] = float(vs @ weight(rl, A, N * X, c) @ vs)
        out.append(row)
        print("%-12s edges %5d surf %5d kf %5d  weak/strong %.3f | tau/lam min: T %.2f G %.2f G3 %.2f GS %.2f | cap loss G %.3f"
              % (name, ne, ns, len(Pk), row["lam_ratio"], row.get("min_tau_over_lam_T", np.nan), row["min_tau_over_lam_G"],
                 row["min_tau_over_lam_G3"], row["min_tau_over_lam_GS"], row["cap_loss_G"]))
        print("   weight on the weak axis, honest: " + " ".join("%s %.3f" % (rl, row["w_honest_" + rl]) for rl in RULES))
        print("   weight on the weak axis, FAULT : " + " ".join("%s %.3f" % (rl, row["w_fault_" + rl]) for rl in RULES))
        print("   by tensor (honest weak / fault weak / honest strong): " + " | ".join(
              "%s-%s %.2f/%.2f/%.2f" % (rl, tn, row["w_honest_%s_%s" % (rl, tn)], row["w_fault_%s_%s" % (rl, tn)], row["w_strong_%s_%s" % (rl, tn)])
              for tn in ("T", "G", "G3", "GS", "GRF") for rl in ("min", "smin")), flush=True)
    import pickle
    pickle.dump(out, open("synth_scenes_seed%d.pkl" % SEED, "wb"))


if __name__ == "__main__":
    main()
