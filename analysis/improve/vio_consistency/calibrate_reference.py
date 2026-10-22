import os
import sys, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")).read())
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
out = {}
for stat in ("vec", "scale"):
    tr = fc4.VioConsistency(ref=1e9, stat=stat, rule="gate"); rs = []
    orig = tr.update
    def upd(*a, tr=tr, rs=rs, orig=orig):
        orig(*a); rs.append(tr.r)
    tr.update = upd
    run(sr, vt, fc4, d, K, sah=False, adapt=tr)
    out[stat] = np.array(rs)
np.savez("r_%s.npz" % name, **out)
