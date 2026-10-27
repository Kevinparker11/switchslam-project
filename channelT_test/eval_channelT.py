#!/usr/bin/env python3
"""
eval_channelT.py  -  does Channel T add detection value beyond the Schur channel?

Inputs: a manifest CSV with one row per (sequence, run):
    seq,run,role,log,labels
    floor01,1,calib,degen_floor01_run1.csv,labels_floor01.csv
    corridor01,1,test,degen_corridor01_run1.csv,labels_corridor01.csv
  role = calib  -> used ONLY to fix thresholds and the combination weights
  role = test   -> held out; all verdicts come from these
  log  = degen_logger.py output (or an old switching-node log, auto-detected)
  labels = make_labels.py output for the same sequence and the same --range-max

Pre-registered verdict (fixed before any test data is looked at; see PROTOCOL):
  INCONCLUSIVE  if the held-out frames hold < 100 translation-degenerate scans, or
                < 30 degenerate scans that the Schur channel misses at its calibrated threshold
  PASS          if, for EVERY run index:
                  dAUC (Schur+T vs Schur)          >= 0.03 and its 95% block-bootstrap CI > 0
                  d recall at the calibrated 5% false-alarm point >= 0.05 and CI > 0
                  McNemar (combined vs Schur, per-scan correctness) p < 0.05 in favour of combined
                  dAUC > 0 in every test sequence that has >= 20 degenerate scans
                and T's p99 compute time < 20 ms (real-time at 10 Hz)
  FAIL          otherwise
"""
import argparse, sys
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

FPR = 0.05
BLOCK_S = 10.0
NBOOT = 2000


# ------------------------------------------------------------- per-frame scores
def load_log(path):
    d = pd.read_csv(path)
    if "t_scan" in d.columns:                       # degen_logger.py
        t = d["t_scan"].values
        H = d[[f"H_{i}{j}" for i in range(6) for j in range(6)]].values.reshape(-1, 6, 6)
        T1 = d["T_l1"].values
        Tv = d[["T_v1x", "T_v1y", "T_v1z"]].values
        Tms = d["T_ms"].values
    elif "bingham_l1" in d.columns:                 # old switching-node log
        d = d.dropna(subset=["time", "bingham_l1"])
        t = d["time"].values
        H = d[[f"Hl_{i}{j}" for i in range(6) for j in range(6)]].values.reshape(-1, 6, 6)
        T1 = d["bingham_l1"].values
        Tv = np.full((len(d), 3), np.nan)
        Tms = np.full(len(d), np.nan)
    else:
        sys.exit(f"{path}: unknown log format")
    H = 0.5 * (H + np.transpose(H, (0, 2, 1)))
    Hrr, Hrt, Htt = H[:, :3, :3], H[:, :3, 3:], H[:, 3:, 3:]
    Stt = Htt - np.transpose(Hrt, (0, 2, 1)) @ np.linalg.pinv(Hrr) @ Hrt
    Srr = Hrr - Hrt @ np.linalg.pinv(Htt) @ np.transpose(Hrt, (0, 2, 1))
    def inv_kappa(M):
        w = np.linalg.eigvalsh(M)
        return np.clip(w[:, 0], 1e-12, None) / np.clip(w[:, -1], 1e-12, None)
    wS, vS = np.linalg.eigh(Stt)
    out = pd.DataFrame(dict(
        t=t,
        schur_t=inv_kappa(Stt),          # 1/kappa(S_tt): DCReg's translational test (kappa>10 <=> <0.1)
        schur_r=inv_kappa(Srr),
        htt=inv_kappa(Htt),               # diagonal block, no coupling
        me=np.clip(np.linalg.eigvalsh(H)[:, 0], 1e-12, None),   # Zhang et al.: min eigenvalue of full H
        fcn=inv_kappa(H),                 # condition number of the full 6x6 H (Hinduja et al. style)
        T=T1,                             # smallest eigenvalue of the orientation tensor (trace 1)
        S_vx=vS[:, 0, 0], S_vy=vS[:, 1, 0], S_vz=vS[:, 2, 0],
        T_vx=Tv[:, 0], T_vy=Tv[:, 1], T_vz=Tv[:, 2], T_ms=Tms))
    return out.sort_values("t")


def merge(log, lab, tol=0.06):
    lab = lab[lab.gt_ok == 1].sort_values("t")
    m = pd.merge_asof(lab, log, on="t", direction="nearest", tolerance=tol)
    return m.dropna(subset=["schur_t", "T"])


# ------------------------------------------------------------- statistics
def feats(df):
    return np.column_stack([np.log(df.schur_t), np.log(np.clip(df["T"], 1e-6, None))])


def flag(score, thr):
    return score < thr                         # low score = degenerate


def thr_at_fpr(score, y, fpr=FPR):
    return np.quantile(score[y == 0], fpr)


def blocks(df):
    """Block ids: contiguous BLOCK_S windows inside each sequence (frames are autocorrelated)."""
    return (df.seq.astype(str) + "_" + ((df.t - df.groupby("seq").t.transform("min")) // BLOCK_S)
            .astype(int).astype(str)).values


def boot_ci(df, stat, rng):
    b = blocks(df); ub = np.unique(b); idx = {k: np.where(b == k)[0] for k in ub}
    vals = []
    for _ in range(NBOOT):
        pick = rng.choice(ub, len(ub), replace=True)
        s = df.iloc[np.concatenate([idx[k] for k in pick])]
        if s.y.nunique() < 2:
            continue
        vals.append(stat(s))
    return np.percentile(vals, [2.5, 97.5])


def evaluate(cal, test, rng, label_col="label_trans"):
    cal = cal.assign(y=cal[label_col].astype(int)); test = test.assign(y=test[label_col].astype(int))
    if cal.y.sum() < 10 or (cal.y == 0).sum() < 10:
        sys.exit("calibration set needs >= 10 degenerate and >= 10 non-degenerate scans")
    lr = LogisticRegression(class_weight="balanced").fit(feats(cal), cal.y)
    # combined score: higher = more degenerate -> negate so low = degenerate, like the others
    comb = lambda df: -lr.decision_function(feats(df))
    thr = {k: thr_at_fpr(cal[k].values, cal.y.values) for k in ("schur_t", "T", "htt", "me", "fcn")}
    thr["comb"] = thr_at_fpr(comb(cal), cal.y.values)
    test = test.assign(comb=comb(test))
    y = test.y.values
    R = {}
    for k in ("schur_t", "htt", "me", "fcn", "T", "comb"):
        s = test[k].values
        f = flag(s, thr[k])
        R[k] = dict(auc=roc_auc_score(y, -s), recall=f[y == 1].mean(), fpr=f[y == 0].mean())
    fs, fc, ft = flag(test.schur_t.values, thr["schur_t"]), flag(test.comb.values, thr["comb"]), flag(test["T"].values, thr["T"])
    # McNemar on per-scan correctness
    cs, cc = fs == y.astype(bool), fc == y.astype(bool)
    b, c = int(np.sum(cs & ~cc)), int(np.sum(~cs & cc))
    p_mc = binomtest(c, b + c, 0.5, alternative="greater").pvalue if b + c else 1.0
    missed = (y == 1) & ~fs
    clean = (y == 0) & ~fs
    dauc = lambda s: roc_auc_score(s.y, -s.comb) - roc_auc_score(s.y, -s.schur_t)
    drec = lambda s: (flag(s.comb.values, thr["comb"])[s.y == 1].mean()
                      - flag(s.schur_t.values, thr["schur_t"])[s.y == 1].mean())
    per_seq = {}
    for sq, g in test.groupby("seq"):
        if g.y.sum() >= 20 and (g.y == 0).sum() >= 20:
            per_seq[sq] = dauc(g)
    return dict(R=R, n=len(test), n_pos=int(y.sum()), n_missed=int(missed.sum()),
                rescued=int((missed & ft).sum()), T_false_on_clean=float(ft[clean].mean()) if clean.any() else np.nan,
                dauc=dauc(test), dauc_ci=boot_ci(test, dauc, rng),
                drec=drec(test), drec_ci=boot_ci(test, drec, rng),
                mcnemar=(b, c, p_mc), per_seq=per_seq, thr=thr, coef=lr.coef_[0])


def angle_deg(a, b):
    c = np.abs(np.sum(a * b, 1)) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
    return np.degrees(np.arccos(np.clip(c, 0, 1)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--frac", type=float, help="re-threshold labels at this unrecovered fraction (sensitivity)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="channelT_frames.csv")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    man = pd.read_csv(a.manifest)
    frames = []
    for _, r in man.iterrows():
        lab = pd.read_csv(r["labels"])
        if a.frac is not None:
            fcols = [c for c in lab.columns if c.startswith("ft")]
            lab["label_trans"] = ((lab[fcols].max(1) > a.frac) & (lab.gt_ok == 1)).astype(int)
        m = merge(load_log(r["log"]), lab).assign(seq=r["seq"], run=int(r["run"]), role=r["role"])
        frames.append(m)
        print(f"{r['seq']:>12} run {r['run']} ({r['role']}): {len(m)} labelled scans, "
              f"{int(m.label_trans.sum())} translation-degenerate, {int(m.label_rot.sum())} rotation-degenerate")
    F = pd.concat(frames, ignore_index=True)
    F.to_csv(a.out, index=False)

    tms = F.T_ms.dropna()
    rt_ok = len(tms) == 0 or np.percentile(tms, 99) < 20
    if len(tms):
        print(f"\nChannel T compute time on the real runs: median {tms.median():.1f} ms, "
              f"p99 {np.percentile(tms, 99):.1f} ms (budget 20 ms at 10 Hz)")

    verdicts = []
    for run in sorted(F.run.unique()):
        cal = F[(F.role == "calib") & (F.run == run)]
        test = F[(F.role == "test") & (F.run == run)]
        if cal.empty or test.empty:
            print(f"\nrun {run}: needs both calib and test rows"); continue
        E = evaluate(cal, test, rng)
        print(f"\n===== run {run}: held-out test, {E['n']} scans, {E['n_pos']} translation-degenerate =====")
        print(f"{'detector':<34}{'AUC':>6}{'recall':>9}{'false alarm':>13}")
        names = dict(schur_t="Schur S_tt (1/kappa)", htt="H_tt diagonal block (1/kappa)",
                     me="Full-H min eigenvalue (Zhang)", fcn="Full-H condition number (1/kappa)", T="Channel T (l1 of orientation tensor)",
                     comb="Schur + T combined")
        for k in ("me", "fcn", "htt", "schur_t", "T", "comb"):
            x = E["R"][k]
            print(f"{names[k]:<34}{x['auc']:6.2f}{x['recall']:9.2f}{x['fpr']:13.2f}")
        print(f"\ndegenerate scans Schur misses: {E['n_missed']};  T catches {E['rescued']} of them")
        print(f"T false-alarm rate on scans Schur correctly calls fine: {E['T_false_on_clean']:.2f}")
        print(f"dAUC  (combined - Schur) = {E['dauc']:+.3f}  95% CI [{E['dauc_ci'][0]:+.3f}, {E['dauc_ci'][1]:+.3f}]")
        print(f"drecall at calibrated 5% FA = {E['drec']:+.3f}  95% CI [{E['drec_ci'][0]:+.3f}, {E['drec_ci'][1]:+.3f}]")
        b, c, p = E["mcnemar"]
        print(f"McNemar: Schur right/combined wrong {b}, combined right/Schur wrong {c}, one-sided p = {p:.4f}")
        print("dAUC per test sequence:", {k: round(v, 3) for k, v in E["per_seq"].items()})
        print("logistic weights (log Schur, log T):", np.round(E["coef"], 3))
        if E["n_pos"] < 100 or E["n_missed"] < 30:
            v = "INCONCLUSIVE"
        elif (E["dauc"] >= 0.03 and E["dauc_ci"][0] > 0 and E["drec"] >= 0.05 and E["drec_ci"][0] > 0
              and p < 0.05 and all(x > 0 for x in E["per_seq"].values())):
            v = "PASS"
        else:
            v = "FAIL"
        verdicts.append(v)
        print(f"run {run} verdict: {v}")

    # direction check on degenerate test scans (only for degen_logger logs)
    T = F[(F.role == "test") & (F.label_trans == 1)].dropna(subset=["T_vx"])
    if len(T):
        L = T[["weak_tx", "weak_ty", "weak_tz"]].values
        print(f"\nweak-direction error on degenerate test scans (median deg): "
              f"Schur {np.median(angle_deg(T[['S_vx','S_vy','S_vz']].values, L)):.0f}, "
              f"T {np.median(angle_deg(T[['T_vx','T_vy','T_vz']].values, L)):.0f}  "
              f"(label axis has 26-direction resolution, ~20 deg)")
    final = ("INCONCLUSIVE" if "INCONCLUSIVE" in verdicts else
             "PASS" if verdicts and all(v == "PASS" for v in verdicts) and rt_ok else "FAIL")
    print(f"\nFINAL (all runs must agree, real-time check {'ok' if rt_ok else 'FAILED'}): {final}")
    print(f"per-scan table saved to {a.out}")


if __name__ == "__main__":
    main()
