#!/usr/bin/env python3
"""Single-run farm test: does the orientation tensor T flag the windows where unfed A-LOAM fails, and does the Hessian Schur channel S_tt?
Protocol (written before the run): docs/results/ChannelT_Farm_Single_Test.md.
usage: python3 farm_T_vs_H.py degen_farm.csv aloam_prefix gt.txt     (aloam_prefix: <prefix>_odom.txt from aloam_logger.py)"""
import sys, os
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fusion_v4"))
import fusion_core as fc

WIN, STEP = 2.0, 1.0            # window length and stride (s)
FAIL_M = 0.3                    # a window fails if |path length of A-LOAM - path length of ground truth| over it exceeds this (m)
FLAG_Q = 0.10                   # an arm flags a window if its median score is below this quantile of the whole run
d = pd.read_csv(sys.argv[1])
od = np.loadtxt(sys.argv[2] + "_odom.txt", comments="#")
gt = np.loadtxt(sys.argv[3], comments="#")
j = np.linalg.norm(np.diff(gt[:, 1:3], axis=0), axis=1); k = int(np.argmax(j))
t_reset = gt[k + 1, 0] if j[k] > 0.5 else gt[0, 0]
gt = gt[gt[:, 0] >= t_reset]
t = d["t_hess_recv"].to_numpy()
H = d[[f"H_{i}{jj}" for i in range(6) for jj in range(6)]].to_numpy()
sH = np.array([np.linalg.eigvalsh(fc.schur_blocks(h.reshape(6, 6))[1])[0] for h in H])
sT = d["T_l1"].to_numpy()
m = t >= max(t_reset, od[0, 0])
t, sH, sT = t[m], sH[m], sT[m]
qH, qT = np.quantile(sH, FLAG_Q), np.quantile(sT, FLAG_Q)

def path(tab, a, b):
    s = tab[(tab[:, 0] >= a) & (tab[:, 0] <= b), 1:4]
    return float(np.linalg.norm(np.diff(s, axis=0), axis=1).sum()) if len(s) > 1 else np.nan

rows = []
for a in np.arange(t[0], t[-1] - WIN, STEP):
    b = a + WIN
    w = (t >= a) & (t < b)
    if w.sum() < 5:
        continue
    pa, pg = path(od, a, b), path(gt, a, b)
    rows.append((a - t_reset, abs(pa - pg), np.median(sH[w]), np.median(sT[w])))
R = np.array(rows)
fail = R[:, 1] > FAIL_M
n_ep = int(((np.diff(fail.astype(int)) == 1).sum()) + (1 if fail[0] else 0))
flagH, flagT = R[:, 2] < qH, R[:, 3] < qT

def auc(score, pos):
    a, b = score[pos], score[~pos]
    return float(((a[:, None] < b[None, :]) + 0.5 * (a[:, None] == b[None, :])).mean()) if len(a) and len(b) else float("nan")

print("scans %d, windows %d (%.0f s, stride %.0f s), failure windows %d in %d episode(s)" % (len(t), len(R), WIN, STEP, fail.sum(), n_ep))
print("failure window starts (s after reset): " + ", ".join("%.0f" % x for x in R[fail, 0]))
print("arm   flags failure windows   flags other windows   AUC (failure = low score)")
for name, fl, sc in (("S_tt", flagH, R[:, 2]), ("T   ", flagT, R[:, 3])):
    print("%s   %5.1f %%  (%d/%d)        %5.1f %%               %.3f" % (name, 100 * fl[fail].mean() if fail.any() else float("nan"), fl[fail].sum(), fail.sum(),
          100 * fl[~fail].mean(), auc(sc, fail)))
if fail.sum() < 5 or n_ep < 3:
    print("VERDICT: INCONCLUSIVE (fewer than 5 failure windows or fewer than 3 episodes)")
else:
    fT, fH, fp = flagT[fail].mean(), flagH[fail].mean(), flagT[~fail].mean()
    if fT >= 0.5 and fH < 0.25 and fp <= 0.15:
        print("VERDICT: T flags the failures that S_tt misses (adds value in this run)")
    elif fH >= 0.5:
        print("VERDICT: S_tt already flags the failures (T not needed in this run)")
    else:
        print("VERDICT: neither channel flags the failures (they are not translation-degeneracy failures, or both miss)")
