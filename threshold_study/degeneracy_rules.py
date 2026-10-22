"""Degeneracy threshold rules for the Multi Floor threshold study (one frame at a time).

Import from the switching node; choose rules with environment variables:
  SCHUR_RULE  semicircle | kappa | kappa_rot | diag_kappa | lmin | lmin_full | crlb | baarda |
              belsley | gvif | fcn | never | always
  SCHUR_VAL   number for kappa / kappa_rot / diag_kappa / lmin / lmin_full / belsley / gvif / fcn
  T_RULE      lmin | bingham | kappa | floor | crlb | woodcock | westin | demantke | off | always
  T_VAL       number for lmin / kappa / floor (ignored otherwise)
Defaults (semicircle, lmin 0.15) reproduce the old node exactly.

H_l is A-LOAM's /laser_hessian, ordered [rotation(3), translation(3)], rotation in Ceres
quaternion-tangent units (rotation angle = 2|delta|). Absolute rotation thresholds use radians.
lam_T is the ascending eigenvalue triple of the orientation tensor T (sums to 1).
"""
import os
import numpy as np

E1 = (0 + 1 / np.sqrt(3)) / 2; E2 = (E1 + 1 / np.sqrt(2)) / 2; E3 = (E2 + 1) / 2
SEMI_THR = np.array([E1, E2, E3]) - np.sqrt(0.103 * np.array([E1, E2, E3]))   # [0.116 0.271 0.471]
SIGMA_R = 0.03                    # VLP-16 datasheet range accuracy, +/-3 cm typical
TAU_T, TAU_R = 0.10, np.deg2rad(2.0)   # localizability tolerance used for labels by Nubert et al. 2022
CHI2_5_95 = 11.0705               # chi-square, 5 dof, 0.95 quantile
BAARDA_LAMBDA0 = 17.075           # non-centrality, alpha0 = 0.001, power 0.80, 1 dof (Baarda B-method)
_D = np.diag([0.5, 0.5, 0.5, 1, 1, 1])

SCHUR_RULE = os.environ.get("SCHUR_RULE", "semicircle")
SCHUR_VAL = float(os.environ.get("SCHUR_VAL", "nan"))
T_RULE = os.environ.get("T_RULE", "lmin")
T_VAL = float(os.environ.get("T_VAL", "0.15"))
N_NORMALS_DEFAULT = 400


def schur_quantities(H_l):
    H = 0.5 * (np.asarray(H_l, float).reshape(6, 6) + np.asarray(H_l, float).reshape(6, 6).T)
    Hr = _D @ H @ _D                              # rotation block in radians
    Hrr, Hrt, Htr, Htt = Hr[:3, :3], Hr[:3, 3:], Hr[3:, :3], Hr[3:, 3:]
    Stt = Htt - Htr @ np.linalg.solve(Hrr, Hrt)
    Srr = Hrr - Hrt @ np.linalg.solve(Htt, Htr)
    q = dict(
        et=np.clip(np.linalg.eigvalsh(Stt), 1e-12, None),
        er=np.clip(np.linalg.eigvalsh(Srr), 1e-12, None),
        edt=np.clip(np.linalg.eigvalsh(Htt), 1e-12, None),
        edr=np.clip(np.linalg.eigvalsh(Hrr), 1e-12, None),
        ef=np.linalg.eigvalsh(Hr),
        trHtt=float(np.trace(H[3:, 3:])),
        gvif=float(np.linalg.det(Htt) / np.linalg.det(Stt)),          # Fox & Monette 1992, Eq. 9
    )
    d = 1 / np.sqrt(np.diag(H)); es = np.linalg.eigvalsh(H * d[:, None] * d[None, :])
    q["belsley_ci"] = float(np.sqrt(es[-1] / es[0]))                   # Belsley et al. 1980, unit-length columns
    q["kt"] = q["et"][2] / q["et"][0]
    q["kr"] = q["er"][2] / q["er"][0]
    return q


def schur_flags(q, rule=None, val=None):
    """Returns (flag_rot, flag_trans). Scale-free rules are unaffected by the radian conversion."""
    rule = rule or SCHUR_RULE; val = SCHUR_VAL if val is None else val
    et, er = q["et"], q["er"]
    if rule == "semicircle":
        return bool((er / np.linalg.norm(er) < SEMI_THR).any()), bool((et / np.linalg.norm(et) < SEMI_THR).any())
    if rule == "kappa":
        return bool(q["kr"] > val), bool(q["kt"] > val)
    if rule == "kappa_rot":                  # rotation Schur block only (where the Multi Floor signal is)
        return bool(q["kr"] > val), False
    if rule == "baarda":                     # minimal detectable displacement > tolerance
        return (bool(er[0] < BAARDA_LAMBDA0 * (SIGMA_R / TAU_R) ** 2),
                bool(et[0] < BAARDA_LAMBDA0 * (SIGMA_R / TAU_T) ** 2))
    if rule == "belsley":                    # condition index of unit-length-scaled J (default 30)
        f = bool(q["belsley_ci"] > val); return f, f
    if rule == "gvif":                       # per-dimension coupling inflation GVIF^(1/3)
        f = bool(q["gvif"] ** (1 / 3) > val); return f, f
    if rule == "diag_kappa":
        return bool(q["edr"][2] / q["edr"][0] > val), bool(q["edt"][2] / q["edt"][0] > val)
    if rule == "lmin":
        return bool(er[0] < val), bool(et[0] < val)
    if rule == "lmin_full":
        f = bool(q["ef"][0] < val); return f, f
    if rule == "crlb":
        return bool(er[0] < (SIGMA_R / TAU_R) ** 2), bool(et[0] < (SIGMA_R / TAU_T) ** 2)
    if rule == "fcn":
        f = bool(q["ef"][5] / max(q["ef"][0], 1e-12) > val); return f, f
    if rule == "never":
        return False, False
    if rule == "always":
        return True, True
    raise ValueError("unknown SCHUR_RULE " + rule)


def t_flag(lam_T, trHtt=None, n_normals=N_NORMALS_DEFAULT, rule=None, val=None):
    rule = rule or T_RULE; val = T_VAL if val is None else val
    l1, l2, l3 = np.clip(np.sort(np.asarray(lam_T, float)), 1e-12, None)
    if rule == "lmin":                       # current node: 0.15; noise-floor q99: 0.045
        return bool(l1 < val)
    if rule == "floor":
        return bool(l1 <= val)
    if rule == "bingham":                    # uniformity test, chi2_5 at 5 %
        B = n_normals * 15 / 2 * ((l1 - 1 / 3) ** 2 + (l2 - 1 / 3) ** 2 + (l3 - 1 / 3) ** 2)
        return bool(B > CHI2_5_95)
    if rule == "kappa":                      # kappa(T) = l3/l1 ; Woodcock C = ln(l3/l1)
        return bool(l3 / l1 > val)
    if rule == "woodcock":                   # shape K < 1 = girdle
        return bool(np.log(l3 / l2) / np.log(l2 / l1) < 1)
    if rule == "westin":                     # Westin et al. 1997 (/lambda_max): flag unless spherical class wins
        return bool(l1 / l3 < max((l3 - l2) / l3, (l2 - l1) / l3))
    if rule == "demantke":                   # Demantke et al. 2011 (sqrt eigenvalues): flag unless 3D class wins
        s1, s2, s3 = np.sqrt(l3), np.sqrt(l2), np.sqrt(l1)
        return bool(s3 / s1 < max((s1 - s2) / s1, (s2 - s3) / s1))
    if rule == "crlb":
        return bool(trHtt is not None and trHtt * l1 < (SIGMA_R / TAU_T) ** 2)
    if rule == "off":
        return False
    if rule == "always":
        return True
    raise ValueError("unknown T_RULE " + rule)


def describe():
    return f"SCHUR_RULE={SCHUR_RULE} SCHUR_VAL={SCHUR_VAL} T_RULE={T_RULE} T_VAL={T_VAL}"


if __name__ == "__main__":          # replay check:  python3 degeneracy_rules.py OLD_LOG.csv
    import sys, pandas as pd
    L = pd.read_csv(sys.argv[1])
    Hc = [f"Hl_{i}{j}" for i in range(6) for j in range(6)]
    fR, fT = [], []
    for _, r in L.iterrows():
        q = schur_quantities(r[Hc].values)
        a, b = schur_flags(q, "semicircle")
        fR.append(a or b)
        fT.append(t_flag([r.bingham_l1, r.bingham_l2, r.bingham_l3], q["trHtt"], rule="lmin", val=0.15))
    print("semicircle == chanR_degen:", np.mean(np.array(fR) == L.chanR_degen.astype(bool).values))
    print("lmin 0.15  == chanT_degen:", np.mean(np.array(fT) == L.chanT_degen.astype(bool).values))
