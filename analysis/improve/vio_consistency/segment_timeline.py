import os
import sys, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")).read())
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
tr = fc4.VioConsistency(ref=1e9, stat="scale", rule="gate", avg=None, n_min=1); rs = []
orig = tr.update
def upd(*a):
    orig(*a); rs.append((a[0] - d["t"][0], tr.r, len(tr.rw)))
tr.update = upd
_, gam = run(sr, vt, fc4, d, K, sah=False, adapt=tr)
r = np.array(rs)
for tt in [24, 30, 34, 38, 42, 44, 46, 50, 54, 60]:
    k = np.searchsorted(r[:, 0], tt); 
    if k < len(r): print("t %5.1f  segment rms ln-scale %.3f  windows %d" % (r[k, 0], r[k, 1], r[k, 2]))
