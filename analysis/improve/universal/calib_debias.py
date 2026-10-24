"""Largest de-biased consistency statistic r (spread of ln(|dv|/|da|) about its segment median, >= 200 windows) seen on a
recording, plus the robust segment scale.  The reference for the de-biased gate = the largest value on the four original
Multi Floor calibration recordings (MF-a1..a4), the same rule that gave 0.156 for the biased statistic."""
import sys, os, json, numpy as np
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
exec(open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '').replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H))))
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
class Rec(fc4.VioConsistency):
    def update(self, *a):
        super().update(*a)
        if len(self.rw) >= self.n_min: REC.append((self.r, self.s, len(self.xs)))
REC = []
a = Rec(ref=1e9, stat="scale", rule="gate", avg=None, n_min=200, debias=True)
run(sr, vt, fc4, d, K, adapt=a, vio_scale_seg=True)
r = np.array([x[0] for x in REC]); s = np.array([x[1] for x in REC])
print(json.dumps(dict(log=name, seq=seq, n=len(r), r_max=round(float(r.max()), 4) if len(r) else None, r_med=round(float(np.median(r)), 4) if len(r) else None,
      s_med=round(float(np.median(s)), 3) if len(s) else None, s_min=round(float(s.min()), 3) if len(s) else None, s_max=round(float(s.max()), 3) if len(s) else None)))
