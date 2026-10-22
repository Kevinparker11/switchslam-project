import os
import sys, json, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")).read())
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
for stat in ("scale", "vec"):
    tr = fc4.VioConsistency(ref=1e9, stat=stat, rule="gate", avg=None, n_min=1); rs = []
    orig = tr.update
    def upd(*a, tr=tr, rs=rs, orig=orig):
        orig(*a); rs.append((a[0], tr.r, len(tr.rw)))
    tr.update = upd
    run(sr, vt, fc4, d, K, sah=False, adapt=tr)
    r = np.array(rs); r = r[np.isfinite(r[:, 1])]
    out = []
    for nmin in (50, 100, 200):
        m = r[:, 2] >= nmin
        out.append("n>=%d max %.3f med %.3f" % (nmin, r[m, 1].max() if m.any() else np.nan, np.median(r[m, 1]) if m.any() else np.nan))
    print(name, stat, " | ".join(out))
