"""replay F8 + structure-anchored heading on logged runs with their keyframes"""
import sys, os, pickle; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, "/home/claude/fusion_v3")
import numpy as np, v2_tools as vt, fusion_core as fc
import sheading as sh
E3 = np.array([0, 0, 1.0])
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nrm_cache")
os.makedirs(CACHE, exist_ok=True)

def kf_normals(path):
    c = os.path.join(CACHE, path.replace("/", "_") + ".pkl")
    if os.path.exists(c):
        return pickle.load(open(c, "rb"))
    z = np.load(path); n = z["n"]; pts = z["pts"].astype(float) * float(z["scale"]); off = np.concatenate([[0], np.cumsum(n)])
    out = {}
    for i, t in enumerate(z["t"]):
        P = pts[off[i]:off[i + 1]]
        if len(P) >= 50:
            nb, plan = sh.planar_normals(P)
            out[round(float(t), 3)] = (nb.astype(np.float32), plan.astype(np.float32))
    pickle.dump(out, open(c, "wb"))
    return out

def run(d, KF, c_t=0.03, w_mode="schur", sah_kw=None, t_end=None, transform=None, t_warm=20.0, sah_modes=("FUSED",)):
    core = fc.FusionCore(vt.R_IL, vt.t_IL, c_t=c_t, gate=fc.KappaGate(kth=1e9), t_warm=t_warm, hess_frame=d["hess_frame"], w_mode=w_mode)
    if sah_kw is not None:
        kw_ = dict(sah_kw); v = kw_.pop('v3', False); cls = {False: sh.StructureHeading, True: sh.StructureHeadingV3, 4: sh.StructureHeadingV4, 5: sh.DirectionSLAM, 6: sh.StructureHeadingV6}[v]
        S = cls(**kw_)
    else:
        S = None
    keys = np.array(sorted(KF)); out = []; Rprev = None
    for k in range(len(d["t"])):
        t = d["t"][k]
        if t_end is not None and t > t_end: break
        R, p, info = core.step(t, d["aft"][k], d["vins"][k], d["H"][k])
        if S is not None and Rprev is not None and d["vins"][k] is not None:
            uu = core.Rf @ (vt.R_IL.T @ (d["vins"][k][0].T @ E3)); S.add_turn(float(fc.so3_log(core.Rf @ Rprev.T) @ uu))
        Rprev = core.Rf.copy()
        if S is not None and info["mode"] in sah_modes and d["vins"][k] is not None:
            j = np.searchsorted(keys, t - 0.002)
            if j < len(keys) and abs(keys[j] - t) < 0.003:
                nb, plan = KF[keys[j]]
                if transform is not None: nb, plan = transform(nb, plan, t)
                u = core.Rf @ (vt.R_IL.T @ (d["vins"][k][0].T @ E3)); u /= np.linalg.norm(u)
                L = sh.level_rotation(u)
                nw = nb @ (L @ core.Rf).T
                if isinstance(S, sh.DirectionSLAM):
                    obs, npts, h = sh.mode_stats(nw, plan)
                    corr = S.update_modes(t, obs, npts, h)
                else:
                    h, npts = sh.direction_hist(nw, plan)
                    corr = S.update(t, h, npts)
                if corr != 0.0:
                    core.Rf = fc.so3_exp(-corr * u) @ core.Rf
                    Rprev = core.Rf.copy()
        out.append(core.pf.copy())
    return np.array(out), (S.stats if S is not None else {})
