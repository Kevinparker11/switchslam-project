import sys, os, json, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs.py")).read())
name = sys.argv[1]; ent = [e for e in LOGS if e[0] == name][0]
_, seq, log, kf, gtp, ext = ent
if ext != "-": os.environ["EXTRINSIC_YAML"] = ext
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "sah"))
import sah_replay3 as sr, v2_tools as vt
d = vt.load_v2_log(log); K = sr.kf_normals(kf)
gt_t, gt_p = vt.load_gt(gtp)
def sc(p): return vt.ate(d["t"], np.asarray(p), gt_t, gt_p)[0]
L = d["df"]; res = {}
res["live"] = sc(L[["fused_x","fused_y","fused_z"]].values)
res["GenZ"] = sc(vt.replay(d, 0.0, mode="lidar")[0])
res["VINS"] = sc(vt.replay(d, 0.0, mode="vins")[0])
res["G9"] = sc(sr.run(d, K, sah_kw=None, c_t=3e-6, c_R=5e-6)[0])
res["G17"] = sc(sr.run(d, K, sah_kw=dict(v3=6, bound_R=True), c_t=3e-6, c_R=5e-6)[0])
res["SAHonly"] = sc(sr.run(d, K, sah_kw=dict(v3=6, bound_R=True), c_t=1e1, c_R=1e1)[0])
print(json.dumps({"name": name, **{k: round(v, 3) for k, v in res.items()}}))
