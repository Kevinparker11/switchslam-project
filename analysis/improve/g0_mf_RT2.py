import sys, numpy as np
sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt
D = "/tmp/claude-0/g0mf/"
gt_t, gt_p = vt.load_gt(D + "ground_truth_path.csv")
d = [vt.load_v2_log(D + "switching_log_v2_G0_kf_run%d.csv" % i) for i in (1, 2, 3)]
def sc(x, **kw): return vt.ate(x["t"], vt.replay(x, **kw)[0], gt_t, gt_p)[0]
CT = [3e-7, 1e-6, 2e-6, 3e-6, 5e-6, 1e-5]
CR = [3e-7, 1e-6, 2e-6, 3e-6, 5e-6, 1e-5, 3e-5]
print("mean ATE (3 runs); rows c_T, columns c_R", CR)
for ct in CT:
    print("%-8g %s" % (ct, " ".join("%.3f" % np.mean([sc(x, c_t=ct, c_R=cr, kth=1e9) for x in d]) for cr in CR)))
print()
for ct, cr in [(3e-6, 3e-6), (3e-6, 1e-5), (1e-5, 1e-5), (2e-6, 2e-6)]:
    r = [sc(x, c_t=ct, c_R=cr, kth=1e9) for x in d]
    print("c_T=%g c_R=%g runs %s mean %.3f sd %.3f" % (ct, cr, np.round(r, 3), np.mean(r), np.std(r, ddof=1)))
