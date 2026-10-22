"""Near-range filter study for SAH on logged keyframes (F8 recordings, GT-scored).
Question 1: does the minimum range r_min change SAH accuracy on real data?
Question 2: does a body-fixed planar object at distance d (about 25 % of the points, angle oscillating 10-30 deg in the body frame,
            the same case as 'strong spurious direction' in sah_stress.py) get removed by r_min > d?
"""
import sys, os, pickle, hashlib; sys.path.insert(0, "/home/claude/sah"); sys.path.insert(0, "/home/claude/fusion_v3")
import numpy as np, v2_tools as vt, cand, sah_replay as sr, sheading as sh
from multiprocessing import Pool
CACHE = "/home/claude/sah/nrm_cache_r"; os.makedirs(CACHE, exist_ok=True)
KW = dict(v3=6, bound_R=True)           # SAH v7 as integrated

def normals(args):
    path, rmin, dobj, T0 = args
    key = hashlib.md5(("%s|%s|%s|%s" % (path, rmin, dobj, T0)).encode()).hexdigest()
    c = os.path.join(CACHE, key + ".pkl")
    if os.path.exists(c): return pickle.load(open(c, "rb"))
    z = np.load(path); n = z["n"]; pts = z["pts"].astype(float) * float(z["scale"]); off = np.concatenate([[0], np.cumsum(n)])
    out = {}
    for i, t in enumerate(z["t"]):
        P = pts[off[i]:off[i + 1]]
        if dobj is not None:                                   # body-fixed vertical plane at distance dobj
            a = np.radians(10) * np.sin((t - T0) / 20.0) + np.radians(20)
            s, h = np.meshgrid(np.arange(-4, 4.001, 0.2), np.arange(-1.0, 1.401, 0.2))
            Q = np.stack([dobj * np.cos(a) - s.ravel() * np.sin(a), dobj * np.sin(a) + s.ravel() * np.cos(a), h.ravel()], 1)
            P = np.vstack([P, Q])
        r = np.linalg.norm(P, axis=1); P = P[(r > rmin) & (r < 60)]
        if len(P) >= 50:
            nb, plan = sh.planar_normals(P); out[round(float(t), 3)] = (nb.astype(np.float32), plan.astype(np.float32))
    pickle.dump(out, open(c, "wb")); return out

def pairs(seq):
    f = {"LC": "sah/lc_pairs.txt", "C02": "sah/c02_pairs.txt", "MF": "sah/mf_pairs.txt"}[seq]
    return [a.split(":") for a in open(f).read().split()]

if __name__ == "__main__":
    seq = sys.argv[1]; rmins = [float(x) for x in sys.argv[2].split(",")]; dobjs = [None if x == "none" else float(x) for x in sys.argv[3].split(",")]
    nrun = int(sys.argv[4]) if len(sys.argv) > 4 else 99
    gt_t, gt_p = vt.load_gt(cand.SEQ[seq][0]); pr = pairs(seq)[:nrun]
    logs = [cand.load(lg) for lg, kf in pr]; T0 = min(d["t"][0] for d in logs)
    jobs = [(kf, rm, do, T0) for do in dobjs for rm in rmins for lg, kf in pr]
    with Pool(os.cpu_count()) as P: res = P.map(normals, jobs)
    it = iter(res)
    print("seq", seq, "runs", len(pr))
    base = [vt.ate(d["t"], sr.run(d, {}, sah_kw=None)[0], gt_t, gt_p)[0] for d in logs]
    print("F8 no SAH                      ", " ".join("%.3f" % x for x in base), "mean %.3f" % np.mean(base), flush=True)
    for do in dobjs:
        for rm in rmins:
            sc = []
            for d in logs:
                KF = next(it); p, st = sr.run(d, KF, sah_kw=KW); sc.append(vt.ate(d["t"], p, gt_t, gt_p)[0])
            print("object %-5s r_min %-4g  " % (do, rm), " ".join("%.3f" % x for x in sc), "mean %.3f" % np.mean(sc), flush=True)
