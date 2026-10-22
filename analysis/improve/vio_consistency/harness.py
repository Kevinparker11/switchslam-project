"""Replay harness for the VINS-LiDAR consistency study (22 Oct 2026).
Exact offline replay of G17 / G18 / G19 / SAH-only on recorded GenZ-stack logs (GenZ-LIO takes no feedback from the
fusion, so the replay equals a live run: the default path reproduces the old core bit for bit).
logs.py lists the recordings (edit the paths for your machine). Uses sah/sah_replay3.py + sah/sheading.py and
fusion_v4/fusion_core.py from this repository."""
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
exec(open(os.path.join(HERE, "logs.py")).read())
def setup(name):
    ent = [e for e in LOGS if e[0] == name][0]
    _, seq, log, kf, gtp, ext = ent
    if ext != "-": os.environ["EXTRINSIC_YAML"] = ext
    sys.path.insert(0, os.path.join(REPO, "fusion_v4")); sys.path.insert(0, os.path.join(REPO, "sah"))
    import sah_replay3 as sr, v2_tools as vt
    import importlib.util
    spec = importlib.util.spec_from_file_location("fc4", os.path.join(REPO, "fusion_v4", "fusion_core.py"))
    fc4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(fc4)
    d = vt.load_v2_log(log); K = sr.kf_normals(kf); gt_t, gt_p = vt.load_gt(gtp)
    return seq, sr, vt, fc4, d, K, gt_t, gt_p
ROT = []
def run(sr, vt, fc4, d, KF, c_t=3e-6, c_R=5e-6, sah=True, adapt=None, **kw):
    sh, E3 = sr.sh, sr.E3
    core = fc4.FusionCore(vt.R_IL, vt.t_IL, c_t=c_t, c_R=c_R, gate=fc4.KappaGate(kth=1e9), t_warm=20.0, hess_frame=d["hess_frame"], vio_adapt=adapt, **kw)
    S = sh.StructureHeadingV6(bound_R=True) if sah else None
    keys = np.array(sorted(KF)); out = []; gam = []; Rprev = None; ROT.clear()
    for k in range(len(d["t"])):
        t = d["t"][k]
        R, p, info = core.step(t, d["aft"][k], d["vins"][k], d["H"][k])
        gam.append((info["mode"], info.get("gamma", 1.0)))
        if S is not None and Rprev is not None and d["vins"][k] is not None:
            uu = core.Rf @ (vt.R_IL.T @ (d["vins"][k][0].T @ E3)); S.add_turn(float(fc4.so3_log(core.Rf @ Rprev.T) @ uu))
        Rprev = core.Rf.copy()
        if S is not None and info["mode"] == "FUSED" and d["vins"][k] is not None:
            j = np.searchsorted(keys, t - 0.002)
            if j < len(keys) and abs(keys[j] - t) < 0.003:
                nb, plan = KF[keys[j]]
                u = core.Rf @ (vt.R_IL.T @ (d["vins"][k][0].T @ E3)); u /= np.linalg.norm(u)
                L = sh.level_rotation(u); nw = nb @ (L @ core.Rf).T
                h, npts = sh.direction_hist(nw, plan); corr = S.update(t, h, npts)
                if corr != 0.0:
                    core.Rf = fc4.so3_exp(-corr * u) @ core.Rf; Rprev = core.Rf.copy()
        out.append(core.pf.copy()); ROT.append(core.Rf.copy())
    return np.array(out), gam
