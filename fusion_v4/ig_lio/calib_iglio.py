# Calibration of c_T, c_R for iG-LIO (rule fixed in IgLIO_Feasibility_Protocol.md, Phase A): G9 structure (R and T channels, no gate, no SAH),
# grid c_T {1,2,3,4,6,10,20,30}e-6 x c_R {2,5,10,20}e-6, 3 Multi Floor I0 recordings, exact offline replay. usage: IGLIO_GT=<Multi Floor ground_truth_path.csv> python3 calib_iglio.py <log dir> <out json> [procs]
import sys, os, json, time, itertools, numpy as np
from multiprocessing import Pool
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # fusion_v4/ig_lio/ -> repository root
sys.path.insert(0, REPO + "/fusion_v4")
import v2_tools as vt
import importlib.util
spec = importlib.util.spec_from_file_location("fc4", REPO + "/fusion_v4/fusion_core.py"); fc4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(fc4)
GT = os.environ["IGLIO_GT"]    # Multi Floor ground_truth_path.csv
D = sys.argv[1]
gt_t, gt_p = vt.load_gt(GT)
LOGS = {r: vt.load_v2_log("%s/switching_log_v2_I0_kf_run%d.csv" % (D, r)) for r in (1, 2, 3)}
def one(a):
    r, c_t, c_R = a
    d = LOGS[r]
    core = fc4.FusionCore(vt.R_IL, vt.t_IL, c_t=c_t, c_R=c_R, gate=fc4.KappaGate(kth=1e9), t_warm=20.0, hess_frame=d["hess_frame"])
    out = []
    for k in range(len(d["t"])):
        R, p, info = core.step(d["t"][k], d["aft"][k], d["vins"][k], d["H"][k]); out.append(core.pf.copy())
    rm, mx = vt.ate(np.asarray(d["t"]), np.array(out), gt_t, gt_p)
    return (r, c_t, c_R, rm, mx)
if __name__ == "__main__":
    CT = [1e-6, 2e-6, 3e-6, 4e-6, 6e-6, 1e-5, 2e-5, 3e-5]; CR = [2e-6, 5e-6, 1e-5, 2e-5]
    jobs = [(r, a, b) for a in CT for b in CR for r in (1, 2, 3)]
    if len(sys.argv) > 4 and sys.argv[4] == "time":
        t0 = time.time(); print(one(jobs[0]), "%.1f s" % (time.time() - t0)); sys.exit()
    # reference: iG-LIO alone (its own pose) and VINS alone
    for r in (1, 2, 3):
        d = LOGS[r]; p = np.array([a[1] for a in d["aft"]]); print("iG-LIO alone run", r, "%.3f / %.3f" % vt.ate(np.asarray(d["t"]), p, gt_t, gt_p), flush=True)
    with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 2) as P: res = P.map(one, jobs, chunksize=1)
    json.dump(res, open(sys.argv[2], "w")); print("done", len(res))
