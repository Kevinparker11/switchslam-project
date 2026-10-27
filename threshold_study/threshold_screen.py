#!/usr/bin/env python3
"""Offline screen of degeneracy thresholds on a raw-Hessian switching log (Multi Floor).

For every candidate rule it reports, from ONE recorded run:
  * how often the rule fires (per frame),
  * the share of frames the node would put in TIGHTLY_COUPLED (5-frame buffer, VO-fail rows kept),
  * how well its firing tracks real A-LOAM odometry drift against ground truth (8 s windows).
This is open-loop: a live run with the rule changes the fused pose, so the live numbers will differ.
Use it to predict and explain, not as the final result.

usage:
  python3 threshold_screen.py --log bingham_old_run1.csv --gt ground_truth_path.csv [--calib-end 1660857541.2]
"""
import argparse, json
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--log", required=True)
ap.add_argument("--gt", required=True)
ap.add_argument("--calib-end", type=float, default=1660857393.2 + 148.0,
                help="end of calibration data (sim time, s); default = end of multifloor_0.bag")
ap.add_argument("--window", type=float, default=8.0)
ap.add_argument("--min-path", type=float, default=2.0)
ap.add_argument("--n-normals", type=int, default=400, help="normals per scan used by Channel T")
ap.add_argument("--out", default="threshold_screen")
a = ap.parse_args()

L = pd.read_csv(a.log).sort_values("time").reset_index(drop=True)
n = len(L)
H = L[[f"Hl_{i}{j}" for i in range(6) for j in range(6)]].values.reshape(n, 6, 6)
H = 0.5 * (H + H.transpose(0, 2, 1))
# A-LOAM / Ceres: columns are [quaternion tangent delta (3), translation (3)].
# Ceres QuaternionPlusImpl uses q_delta = (cos|d|, sin|d|/|d| d), i.e. rotation angle = 2|d|.
# Convert the rotation block to radians for absolute (unit-bearing) thresholds: J_theta = J_delta / 2.
Dm = np.diag([0.5, 0.5, 0.5, 1, 1, 1])
Hrad = Dm @ H @ Dm
Hrr, Hrt, Htr, Htt = Hrad[:, :3, :3], Hrad[:, :3, 3:], Hrad[:, 3:, :3], Hrad[:, 3:, 3:]
Stt = Htt - Htr @ np.linalg.solve(Hrr, Hrt)
Srr = Hrr - Hrt @ np.linalg.solve(Htt, Htr)
et = np.clip(np.linalg.eigvalsh(Stt), 1e-12, None)        # ascending
er = np.clip(np.linalg.eigvalsh(Srr), 1e-12, None)
edt = np.clip(np.linalg.eigvalsh(Htt), 1e-12, None)
edr = np.clip(np.linalg.eigvalsh(Hrr), 1e-12, None)
ef = np.linalg.eigvalsh(Hrad)
kt, kr = et[:, 2] / et[:, 0], er[:, 2] / er[:, 0]
l1, l2, l3 = (L[c].values for c in ("bingham_l1", "bingham_l2", "bingham_l3"))  # l1 smallest

# Switch-SLAM semicircle thresholds exactly as the node computes them
e1 = (0 + 1 / np.sqrt(3)) / 2; e2 = (e1 + 1 / np.sqrt(2)) / 2; e3 = (e2 + 1) / 2
thr = np.array([e1, e2, e3]) - np.sqrt(0.103 * np.array([e1, e2, e3]))
nt = et / np.linalg.norm(et, axis=1, keepdims=True); nr = er / np.linalg.norm(er, axis=1, keepdims=True)

sig_r, tau_t, tau_R = 0.03, 0.10, np.deg2rad(2.0)
B = a.n_normals * 15 / 2 * ((l1 - 1 / 3) ** 2 + (l2 - 1 / 3) ** 2 + (l3 - 1 / 3) ** 2)
K_wood = np.log(l3 / l2) / np.log(l2 / np.clip(l1, 1e-12, None))
trHtt = np.trace(H[:, 3:, 3:], axis1=1, axis2=2)

rules = {
    "S0 semicircle (current)": (nt < thr).any(1) | (nr < thr).any(1),
    "S1 kappa(S)>10 DCReg": (kt > 10) | (kr > 10),
    "S2 kappa(S)>50 DCReg upper": (kt > 50) | (kr > 50),
    "S3 kappa(diag)>10 Nashed": (edt[:, 2] / edt[:, 0] > 10) | (edr[:, 2] / edr[:, 0] > 10),
    "S4 lmin(S)<10 LOAM odom": (et[:, 0] < 10) | (er[:, 0] < 10),
    "S5 lmin(S)<100 LOAM map": (et[:, 0] < 100) | (er[:, 0] < 100),
    "S5f lmin(H)<100 full ME": ef[:, 0] < 100,
    "S6 CRLB 0.10m/2deg": (et[:, 0] < (sig_r / tau_t) ** 2) | (er[:, 0] < (sig_r / tau_R) ** 2),
    "SF kappa(H)>10 full FCN": ef[:, 5] / np.clip(ef[:, 0], 1e-12, None) > 10,
    "T0 l1<0.15 (current)": l1 < 0.15,
    "T1 Bingham B>11.07": B > 11.07,
    "T2 kappa(T)>10 / Woodcock C>ln10": l3 / l1 > 10,
    "T3 noise floor l1<=0.045": l1 <= 0.045,
    "T4 CRLB tr(Htt)*l1<0.09": trHtt * l1 < (sig_r / tau_t) ** 2,
    "T5 Woodcock K<1 girdle": K_wood < 1,
    "C0 never (Switch-SLAM upper tail)": np.zeros(n, bool),
}

# ---------- drift labels from A-LOAM odometry (l_p = /laser_odom_to_init, not fused) ----------
g = pd.read_csv(a.gt); gt_t = g.timestamp.values / 1e9; gt_p = g[["p_w_b_x", "p_w_b_y", "p_w_b_z"]].values
t = L.time.values; p = L[["l_px", "l_py", "l_pz"]].values
m = (t >= gt_t[0]) & (t <= gt_t[-1])
gi = np.stack([np.interp(t, gt_t, gt_p[:, i]) for i in range(3)], 1)
mu_s, mu_d = p[m].mean(0), gi[m].mean(0)
U, _, Vt = np.linalg.svd((gi[m] - mu_d).T @ (p[m] - mu_s) / m.sum())
S = np.eye(3); S[2, 2] = -1 if np.linalg.det(U) * np.linalg.det(Vt) < 0 else 1
R = U @ S @ Vt; pa = (p - mu_s) @ R.T + mu_d
edges = np.arange(t[m][0], t[m][-1], a.window)
win = np.full(n, -1); drift = []
for k in range(len(edges) - 1):
    i = np.where((t >= edges[k]) & (t < edges[k + 1]))[0]
    if len(i) < 5: drift.append(np.nan); continue
    path = np.linalg.norm(np.diff(gi[i], axis=0), axis=1).sum()
    if path < a.min_path: drift.append(np.nan); continue
    drift.append(np.linalg.norm((pa[i[-1]] - pa[i[0]]) - (gi[i[-1]] - gi[i[0]])) / path); win[i] = k
drift = np.array(drift)
lo, hi = np.nanpercentile(drift, [33.3, 66.7])
lab = np.full(n, np.nan)
ok = win >= 0
lab[ok] = np.where(drift[win[ok]] >= hi, 1, np.where(drift[win[ok]] <= lo, 0, np.nan))
calib = t < a.calib_end

# ---------- data-calibrated kappa thresholds (Neyman-Pearson 5 % FPR, Youden J), calibration bag only ----------
score = np.maximum(kt, kr)              # DCReg form: one kappa_th for both blocks
cg, cb = calib & (lab == 0), calib & (lab == 1)
grid = np.logspace(0, 4, 400)
fpr = np.array([(score[cg] > k).mean() for k in grid]); tpr = np.array([(score[cb] > k).mean() for k in grid])
k_np = grid[np.argmax(fpr <= 0.05)] if (fpr <= 0.05).any() else np.inf
k_yj = grid[np.argmax(tpr - fpr)]
rules["S7 kappa NP 5% (calibrated)"] = score > k_np
rules["S8 kappa Youden (calibrated)"] = score > k_yj
lg = np.linspace(0, 0.34, 341)
fprT = np.array([(l1[cg] < x).mean() for x in lg]); tprT = np.array([(l1[cb] < x).mean() for x in lg])
t_np = lg[np.where(fprT <= 0.05)[0].max()] if (fprT <= 0.05).any() else 0.0
t_yj = lg[np.argmax(tprT - fprT)]
rules["T6 l1 NP 5% (calibrated)"] = l1 < t_np
rules["T7 l1 Youden (calibrated)"] = l1 < t_yj

# ---------- mode share under the node's 5-frame buffer ----------
vofail = (L["mode"] == "LIDAR_ONLY_SAFE").values
def tc_share(flag):
    buf, tc = [], 0
    for f, v in zip(flag, vofail):
        if v: continue
        buf.append(bool(f)); buf = buf[-5:]
        tc += all(buf)
    return tc / max(1, (~vofail).sum())

rows = []
for name, f in rules.items():
    test = ~calib
    tb, tg = test & (lab == 1), test & (lab == 0)
    rows.append(dict(rule=name, fire_rate=f.mean(), tc_share_alone=tc_share(f),
                     tc_share_union_T0=tc_share(f | rules["T0 l1<0.15 (current)"]) if name.startswith("S") else np.nan,
                     tc_share_union_S0=tc_share(f | rules["S0 semicircle (current)"]) if name.startswith("T") else np.nan,
                     TPR_test=f[tb].mean(), FPR_test=f[tg].mean(), TPR_calib=f[cb].mean(), FPR_calib=f[cg].mean()))
R_ = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(f"log: {a.log}  frames={n}  calib frames={calib.sum()}  labelled bad/good (test) = {(~calib & (lab==1)).sum()}/{(~calib & (lab==0)).sum()}")
print(f"drift terciles (m per m): good <= {lo:.3f}, bad >= {hi:.3f};  windows={np.isfinite(drift).sum()}")
print(f"calibrated: kappa_NP5%={k_np:.2f}  kappa_Youden={k_yj:.2f}  T_NP5%: l1<{t_np:.3f}  T_Youden: l1<{t_yj:.3f}")
print("regression check vs logged flags: semicircle matches chanR_degen on",
      f"{(rules['S0 semicircle (current)'] == L.chanR_degen.astype(bool)).mean()*100:.1f}% of frames;",
      f"T0 matches chanT_degen on {(rules['T0 l1<0.15 (current)'] == L.chanT_degen.astype(bool)).mean()*100:.1f}%")
print(R_.round(3).to_string(index=False))
print("\nmedians: kappa(S_tt)=%.1f kappa(S_RR)=%.1f lmin(S_tt)=%.1f lmin(S_RR,rad)=%.1f l1(T)=%.3f B=%.0f" % (
    np.median(kt), np.median(kr), np.median(et[:, 0]), np.median(er[:, 0]), np.median(l1), np.median(B)))
R_.to_csv(a.out + ".csv", index=False)
json.dump(dict(kappa_np=float(k_np), kappa_youden=float(k_yj), T_np=float(t_np), T_youden=float(t_yj)),
          open(a.out + "_calibrated.json", "w"), indent=1)
