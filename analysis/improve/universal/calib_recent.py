"""Largest 'recent' consistency statistic r (RMS of x over windows that ended in the last `avg` s, >= n_min of them) on a recording.
The reference for a fast companion check = the largest value on MF-a1..a4 (same calibration rule as 0.156)."""
import sys, os, json, numpy as np
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
exec(open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '').replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H))))
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
out = dict(log=name)
for avg, nmin in ((10.0, 50), (5.0, 25)):
    REC = []
    class Rec(fc4.VioConsistency):
        def update(self, *a):
            super().update(*a)
            if len(self.rw) >= self.n_min: REC.append(self.r)
    a = Rec(ref=1e9, stat="scale", rule="gate", avg=avg, n_min=nmin)
    run(sr, vt, fc4, d, K, adapt=a)
    out["max_r_avg%d" % avg] = round(float(np.max(REC)), 3) if REC else None
print(json.dumps(out))
