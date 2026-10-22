import sys, numpy as np
sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt
D = "/tmp/claude-0/g0mf/"
gt_t, gt_p = vt.load_gt(D + "ground_truth_path.csv")
d = [vt.load_v2_log(D + "switching_log_v2_G0_kf_run%d.csv" % i) for i in (1, 2, 3)]
def sc(x, **kw): return vt.ate(x["t"], vt.replay(x, **kw)[0], gt_t, gt_p)[0]
CT = [1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 1e-3]
CR = [3e-6, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 1e-2]
print("mean ATE over 3 runs; rows c_T, columns c_R", CR)
M = np.zeros((len(CT), len(CR)))
for i, ct in enumerate(CT):
    for j, cr in enumerate(CR):
        M[i, j] = np.mean([sc(x, c_t=ct, c_R=cr, kth=1e9) for x in d])
    print("%-8g %s" % (ct, " ".join("%.3f" % v for v in M[i])))
print("\nG0 alone mean %.3f" % np.mean([sc(x, c_t=0.0, mode="lidar") for x in d]))
i, j = np.unravel_index(M.argmin(), M.shape); print("min %.3f at c_T=%g c_R=%g" % (M[i, j], CT[i], CR[j]))
# per run at a plateau middle choice
for ct, cr in [(1e-4, 3e-5), (3e-5, 3e-5), (1e-4, 1e-4)]:
    print("c_T=%g c_R=%g per run:" % (ct, cr), np.round([sc(x, c_t=ct, c_R=cr, kth=1e9) for x in d], 3))
