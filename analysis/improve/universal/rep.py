"""Replay configurations on one recording (one process per recording, because v2_tools reads the extrinsics at import).
usage: python3 rep.py <log name> <cfg> [<cfg> ...]     results -> out/<log>__<cfg>.json"""
import sys, os, json, time, numpy as np
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
src = open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '')
src = src.replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H)))
exec(src)                      # defines setup(name) (reads LOGS) and run(...)
exec(open(os.path.join(ME, "configs.py")).read())     # CFG: name -> function(fc4) -> kwargs for run()
name = sys.argv[1]; cfgs = sys.argv[2:]
OUTD = os.environ.get("OUTD", "out"); os.makedirs(os.path.join(ME, OUTD), exist_ok=True)
seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
t = np.asarray(d["t"])
for c in cfgs:
    f = os.path.join(ME, OUTD, "%s__%s.json" % (name, c))
    if os.path.exists(f):
        continue
    t0 = time.time()
    if c == "GZ":            # GenZ-LIO alone: its own scan-to-map pose
        p = np.array([a[1] for a in d["aft"]]); gam = []
    else:
        p, gam = run(sr, vt, fc4, d, K, **CFG[c](fc4))
    rm, mx = vt.ate(t, p, gt_t, gt_p)
    fu = [g for m, g in gam if m == "FUSED"]
    res = dict(log=name, seq=seq, cfg=c, ate=rm, max=mx, n=len(t), fused=len(fu),
               g_open=float(np.mean([g > 0.5 for g in fu])) if fu else None,
               g_mean=float(np.mean(fu)) if fu else None, secs=round(time.time() - t0, 1))
    json.dump(res, open(f, "w")); print(json.dumps(res), flush=True)
