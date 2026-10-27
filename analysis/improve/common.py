import sys, glob, numpy as np
sys.path.insert(0, "/home/claude/fusion_v3")
import v2_tools as vt, fusion_core as fc
U = "/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6/"
GT = {"MF": "/mnt/user-data/uploads/ground_truth_path.csv", "LC": U + "26b723ff-corridor01_gt.txt",
      "C02": U + "db62c9b7-corridor02_gt.txt", "CAVE": "/home/claude/data_in14/cave02_gt.txt"}
def logs(seq, cfg="F8"):
    if seq == "CAVE": return sorted(glob.glob("/home/claude/data_in14/switching_log_v2_%s_run*.csv" % cfg))
    return sorted(glob.glob("/home/claude/data_in11/%s_switching_log_v2_%s_kf_run*.csv" % (seq, cfg)))
_gt = {}
def gt(seq):
    if seq not in _gt: _gt[seq] = vt.load_gt(GT[seq])
    return _gt[seq]
_d = {}
def load(path):
    if path not in _d: _d[path] = vt.load_v2_log(path)
    return _d[path]
def score(seq, d, p):
    gt_t, gt_p = gt(seq)
    return vt.ate(d["t"], np.asarray(p), gt_t, gt_p)[0]
def replay(d, **kw):
    kw.setdefault("kth", 1e9)
    return vt.replay(d, **kw)[0]
