import sys, numpy as np
sys.path.insert(0, "/home/claude/fusion_v4")
import v2_tools as vt
D = "/tmp/claude-0/g0mf/"
gt_t, gt_p = vt.load_gt(D + "ground_truth_path.csv")
d = [vt.load_v2_log(D + "switching_log_v2_G0_kf_run%d.csv" % i) for i in (1, 2, 3)]
def sc(x, **kw): return vt.ate(x["t"], vt.replay(x, **kw)[0], gt_t, gt_p)[0]
print("G0 alone:", np.round([sc(x, c_t=0.0, mode="lidar") for x in d], 3))
print("\nc_R grid with c_T = 1e-4 (translation weight on its plateau); rotation weight = Schur on S_RR, no gate")
print("c_R        per run                     mean")
for cr in [0, 1e-12, 1e-11, 1e-10, 3e-10, 1e-9, 3e-9, 1e-8, 3e-8, 1e-7, 1e-6, 1e-5, 1e-4]:
    r = [sc(x, c_t=1e-4, c_R=cr, kth=1e9) for x in d]
    print("%-10g %s  %.3f" % (cr, np.round(r, 3), np.mean(r)))
# where does VINS fail in run 2?
x = d[1]
vp = np.array([v[1] if v is not None else [np.nan]*3 for v in x["vins"]])
print("\nrun2: VINS-alone ATE (mode=vins) %.2f ; VINS rows present %d/%d" % (sc(x, c_t=0.0, mode="vins"), np.isfinite(vp[:,0]).sum(), len(vp)))
