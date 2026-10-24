"""Gate timeline (no GT): when does the G18/G19 gate open, and how large are the single-window disagreements |x| = |ln(|dv|/|da|)|
in the 10 s before and during each open stretch?  Also the largest single-window |x| while open on the recording."""
import sys, os, json, numpy as np
ME = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(ME, "logs_all.py")).read())
H = os.path.join(ME, "..", "vio_consistency", "harness.py")
exec(open(H).read().replace('exec(open(os.path.join(HERE, "logs.py")).read())', '').replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = "%s"' % os.path.dirname(os.path.abspath(H))))
name = sys.argv[1]; seq, sr, vt, fc4, d, K, gt_t, gt_p = setup(name)
class Rec(fc4.VioConsistency):
    def update(self, t, *a):
        n0 = len(self.xs); super().update(t, *a)
        X.append((t, self.xs[-1] if len(self.xs) > n0 else np.nan, self.g, self.r, len(self.xs)))
X = []
a = Rec(ref=0.156, stat="scale", rule="gate", avg=None, n_min=200)
run(sr, vt, fc4, d, K, adapt=a, vio_scale_T=10.0)
X = np.array(X); t0 = d["t"][0]
op = X[:, 2] > 0.5
idx = np.flatnonzero(np.diff(np.r_[0, op.astype(int), 0])); segs = list(zip(idx[::2], idx[1::2]))
out = dict(log=name, open_frac=round(float(op.mean()), 3), max_abs_x_open=round(float(np.nanmax(np.abs(X[op, 1]))), 3) if op.any() else None,
           p99_abs_x_open=round(float(np.nanquantile(np.abs(X[op, 1]), 0.99)), 3) if op.any() else None, stretches=[])
for s, e in segs[:4]:
    xs = np.abs(X[s:e, 1]); out["stretches"].append(dict(t=[round(X[s, 0] - t0, 1), round(X[e - 1, 0] - t0, 1)], r_at_open=round(float(X[s, 3]), 3),
        n_at_open=int(X[s, 4]), max_abs_x=round(float(np.nanmax(xs)), 3) if np.isfinite(xs).any() else None))
print(json.dumps(out))
