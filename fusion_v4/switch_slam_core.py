"""Switch-SLAM switching node (Lee et al., RA-L 2024, doi:10.1109/LRA.2024.3421792) as published:
Section III-C degeneracy detection (Eqs. 11-12), the status buffer and interpolation (Eq. 13), Section III-D visual-odometry
failure, Section III-E scan-to-map remapping (Eqs. 14-16) and Algorithm 1.  numpy only.

Why this file exists: F12 only borrowed the detection rule.  This is the whole switching node, written line by line from
the paper (no code was released).  docs/protocols/SwitchSLAM_Exact_Replica.md lists, for every equation, what the paper
says, what is implemented, and every place where the paper is silent and a choice had to be made (A1..A8) or where
the A-LOAM + VINS-Mono stack differs from the authors' (D1..D5).

Conventions (same as fusion_core): pose = (R, p) of the LiDAR in the A-LOAM map frame, R body->world.  Increments are
expressed in the body frame of the earlier pose.  Hessians are the A-LOAM patches' (rotation block in Ceres tangent
units, converted to radians with fusion_core.D_RAD).
"""
from collections import deque

import numpy as np

import fusion_core as fc

I3 = np.eye(3)
SQRT3 = float(np.sqrt(3.0))

# ---------------------------------------------------------------------------- Eqs. 11-12
CHI2 = 0.103                                         # "Chi-squared value for 2-DOFs at a 95% confidence level" (as published)
LT_PUBLISHED = np.array([0.12, 0.27, 0.48])          # "the non-heuristic threshold is determined as [0.12, 0.27, 0.48]"


def expectations():
    """e1 = 1/(2 sqrt 3) = 0.289, e2 = (e1 + 1/sqrt 2)/2 = 0.498, e3 = (e2 + 1)/2 = 0.749 (paper, text below Eq. 11)"""
    e1 = 1.0 / (2.0 * SQRT3)
    e2 = 0.5 * (e1 + 1.0 / np.sqrt(2.0))
    e3 = 0.5 * (e2 + 1.0)
    return np.array([e1, e2, e3])


def thresholds_from_formula(chi2=CHI2):
    """Eq. 12: lambda_t = e_m - sqrt(0.103 e_m).  Gives [0.116, 0.271, 0.471]; the paper prints [0.12, 0.27, 0.48]
    (0.48 is 0.01 above the formula).  The printed values are used by default."""
    e = expectations()
    return e - np.sqrt(chi2 * e)


def eig_degeneracy(H, lt=LT_PUBLISHED):
    """Section III-C.  The three smallest eigenvalues of the 6x6 scan-matching Hessian (in rad and m), normalised to
    unit norm, each compared with its threshold.  Returns the full eigen-decomposition for the remapping."""
    H = np.asarray(H, float).reshape(6, 6)
    Hr = fc.D_RAD @ (0.5 * (H + H.T)) @ fc.D_RAD
    lam, U = np.linalg.eigh(Hr)
    lam = np.clip(lam, 0.0, None)
    l3 = lam[:3]
    n = float(np.linalg.norm(l3))
    if n <= 0.0:
        lam_bar = np.zeros(3)
        flags = np.ones(3, bool)
    else:
        lam_bar = l3 / n
        flags = lam_bar < np.asarray(lt)
    return dict(lam=lam, U=U, lam_bar=lam_bar, flags=flags, degenerate=bool(flags.any()))


# ---------------------------------------------------------------------------- pose helpers
def pose_mul(a, b):
    return a[0] @ b[0], a[0] @ np.asarray(b[1], float) + np.asarray(a[1], float)


def pose_inv(a):
    return a[0].T, -a[0].T @ np.asarray(a[1], float)


def ortho(R):
    """nearest rotation matrix (products of many rotations drift off SO(3) by rounding, and pose_inv assumes R^T = R^-1)"""
    U, _, Vt = np.linalg.svd(R)
    return U @ Vt


def blend(w, dl, dv):
    """Eq. 13 on SO(3) x R^3: w * dT_l (+) (1-w) * dT_v in the tangent space"""
    phi = w * fc.so3_log(dl[0]) + (1.0 - w) * fc.so3_log(dv[0])
    return fc.so3_exp(phi), w * np.asarray(dl[1], float) + (1.0 - w) * np.asarray(dv[1], float)


def status_of(buf):
    """check(Q_s): 'Normal' (all L), 'Fully' (all D), 'Start/End' (both in the queue), 'Empty' (nothing stored yet)"""
    if len(buf) == 0:
        return "Empty"
    s = sum(1 for b in buf if b)
    return "Normal" if s == 0 else ("Fully" if s == len(buf) else "Start/End")


class SwitchSlamCore:
    """One call to decide() before each scan-to-map matching (Algorithm 1, lines 1-8) and one to finish() after it
    (line 9 = Eq. 16, line 10 = queue update).  decide() does not change any state, so it may be called for scans that
    A-LOAM later drops; only finish() advances the chain.

    n_buf     length of the status queue Q_s ("pre-defined size" in the paper, value not given)      [A2]
    lt        thresholds; LT_PUBLISHED (the printed values) or thresholds_from_formula()
    eq15_w    weight of the LiDAR term in Eq. 15.  The printed Eq. 15 has two plain squared norms, whose minimiser is
              the mean of the two steps, so 0.5 is the literal reading                                   [A4]
    vins_jump_pos / vins_jump_rot   VINS-Mono's own failure thresholds (5 m, 50 deg between consecutive states)
    rot_src   'lidar' (default, Switch-SLAM): the rotation of the output is A-LOAM's scan-to-map rotation.  'vins' (F33): on every scan
              where VINS-Mono is trusted (a pose is there, the step guard and the outside check pass, i.e. not vo_fail) the rotation
              increment of the guess is VINS-Mono's and the output keeps it (no rotation correction from the scan-to-map solve, as F26
              with c_R = 0); the translation follows the Switch-SLAM rule unchanged.  Without a trusted VINS-Mono: unchanged.
    hess_frame 'world': H is the scan-to-map Hessian (left perturbation of q_w_curr, t_w_curr, A-LOAM map frame);
               'body' : H is the scan-to-scan Hessian (previous LiDAR frame), rotated into the map frame for Eq. 14."""

    def __init__(self, R_IL=I3, t_IL=np.zeros(3), n_buf=5, lt=LT_PUBLISHED, eq15_w=0.5,
                 vins_jump_pos=5.0, vins_jump_rot=np.radians(50.0), hess_frame="body", detector=None, rot_src="lidar"):
        assert hess_frame in ("world", "body")
        assert rot_src in ("lidar", "vins")
        self.rot_src = rot_src                    # F33: "vins" = the rotation of the output comes from VINS-Mono whenever it is trusted
        self.detector = detector                  # None = Switch-SLAM's own rule (eig_degeneracy); else detector(H, T) -> dict
        self.R_IL, self.t_IL = np.asarray(R_IL, float), np.asarray(t_IL, float)
        self.buf = deque(maxlen=int(n_buf))
        self.lt = np.asarray(lt, float)
        self.eq15_w = float(eq15_w)
        self.jump_pos, self.jump_rot = float(vins_jump_pos), float(vins_jump_rot)
        self.hess_frame = hess_frame
        self.Rf = self.pf = None                  # T_{k-1}: final pose chain, in the A-LOAM map frame
        self.prev_o = self.prev_v = self.prev_aft = self.prev_pub = None
        self.prev_t = None                        # stamp of the last finished scan (used by the gyro prior)

    def initialised(self):
        return self.Rf is not None

    def init(self, aft, odom, vins, pub, t=None):
        """first mapped scan: the final chain starts on A-LOAM's pose; pub = the pose we published for this scan"""
        self.Rf, self.pf = np.asarray(aft[0], float).copy(), np.asarray(aft[1], float).copy()
        self.prev_aft = (self.Rf.copy(), self.pf.copy())
        self.prev_o, self.prev_v, self.prev_pub = odom, vins, pub
        self.prev_t = t

    # ------------------------------------------------------------------ Algorithm 1, lines 1-8
    def _detect(self, H, T_h):
        if self.detector is None:
            return eig_degeneracy(H, self.lt)
        return self.detector(H, T_h)

    def _T_in_H_frame(self, T, R_cur, dR_prev):
        """orientation tensor of the current scan (current LiDAR frame) in the frame of the Hessian: body = previous LiDAR
        frame (dR_prev = R_prev^T R_cur), world = the map frame (R_cur = current LiDAR rotation in the map)"""
        if T is None:
            return None
        R = dR_prev if self.hess_frame == "body" else R_cur
        return R @ np.asarray(T, float) @ R.T

    def decide(self, odom, vins, H, gyro_dR=None, t=None, T=None, vo_trusted=True):
        """odom = (R, p) A-LOAM scan-to-scan odometry pose of this scan; vins = (R, p) VINS-Mono IMU pose at the scan
        time or None (VINS lost / not initialised); H = Hessian used for the detection (6x6) or None.
        gyro_dR (SWI variant only) = integrated-gyro rotation increment of the LiDAR frame since the last finished scan; it replaces
        the rotation of the LiDAR increment (translation stays A-LOAM's).  None = the plain replica.  t = scan stamp."""
        dl = fc.rel_body(self.prev_o[0], self.prev_o[1], odom[0], odom[1]) if odom is not None and self.prev_o is not None \
            else (I3, np.zeros(3))
        gyro_deg = np.nan
        if gyro_dR is not None:
            gyro_deg = float(np.degrees(np.linalg.norm(fc.so3_log(dl[0].T @ gyro_dR))))
            dl = (np.asarray(gyro_dR, float), dl[1])
        dv, vo_fail = None, True
        if vins is not None and self.prev_v is not None:
            dR_I, dt_I = fc.rel_body(self.prev_v[0], self.prev_v[1], vins[0], vins[1])
            dv = fc.imu_to_lidar_increment(dR_I, dt_I, self.R_IL, self.t_IL)
            vo_fail = bool(np.linalg.norm(dv[1]) > self.jump_pos or np.linalg.norm(fc.so3_log(dv[0])) > self.jump_rot)
            if not vo_trusted:                                    # an outside check (F32: F24's VINS consistency gate) distrusts VINS
                vo_fail = True
        rot_vins = bool(self.rot_src == "vins" and dv is not None and not vo_fail)
        if rot_vins:                                              # F33: the rotation of the LiDAR increment is VINS-Mono's
            dl = (dv[0], dl[1])
        T_h = self._T_in_H_frame(T, self.Rf @ dl[0], dl[0])
        eig = self._detect(H, T_h) if H is not None else None
        degen = eig is not None and eig["degenerate"]
        status = status_of(self.buf)
        w = np.nan
        if vo_fail or not degen:                                  # line 2 -> line 3
            kind, d = "LIDAR", dl
        elif status == "Start/End":                               # line 4 -> line 5 (Eq. 13)
            w = float(eig["w_blend"]) if "w_blend" in eig else float(min(1.0, SQRT3 * eig["lam_bar"][0]))
            kind, d = "INTERP", blend(w, dl, dv)
        else:                                                     # line 6 -> line 7
            kind, d = "VO", dv
        guess = fc.compose(self.Rf, self.pf, d[0], d[1])
        vo_pose = None if vo_fail else fc.compose(self.Rf, self.pf, dv[0], dv[1])
        return dict(rot_vins=rot_vins, kind=kind, guess=guess, vo=vo_pose, t=t, T=T, T_h=T_h, gyro=gyro_dR is not None, gyro_deg=gyro_deg, vo_fail=vo_fail, eig=eig, status=status, w=w, odom=odom, vins=vins,
                    dtl=float(np.linalg.norm(dl[1])), dtv=float(np.linalg.norm(dv[1])) if dv is not None else np.nan)

    def pose_to_publish(self, guess):
        """laserMapping computes its guess as T_w_odom * (published pose), with T_w_odom = T_aft(prev) * P(prev)^-1 from
        the previous solve.  Publishing P(prev) * T_aft(prev)^-1 * guess makes the guess A-LOAM actually uses equal to
        `guess` (Algorithm 1's T_init), whatever the final chain and A-LOAM's own chain have drifted apart by."""
        R, p = pose_mul(self.prev_pub, pose_mul(pose_inv(self.prev_aft), guess))
        return ortho(R), p

    # ------------------------------------------------------------------ Algorithm 1, lines 9-10 (Eqs. 14-16)
    def finish(self, aft, H, dec, pub):
        """aft = (R, p): A-LOAM's scan-to-map solution started from dec['guess']; H = the Hessian of that matching (or
        the detection Hessian if none is given).  Returns (R, p, info)."""
        Ra, pa = np.asarray(aft[0], float), np.asarray(aft[1], float)
        Rg, pg = dec["guess"]
        if self.detector is None:
            eig = eig_degeneracy(H, self.lt) if H is not None else dec["eig"]
        elif H is None:
            eig = dec["eig"]
        else:                                                           # world frame: the tensor is rotated with the final pose
            eig = self._detect(H, dec["T_h"] if self.hess_frame == "body" else self._T_in_H_frame(dec["T"], Ra, None))
        x_full = np.concatenate([fc.so3_log(Ra @ Rg.T), pa - pg])      # Gauss-Newton displacement, left/world perturbation
        degen = eig is not None and eig["degenerate"]
        if not degen:
            case, x = 1, x_full                                         # Eq. 16, line 1: -H_l^-1 J^T d
        else:
            if "remove" in eig:                                         # our detection: directions of every channel that fired
                U = eig["remove"]
            else:
                U = eig["U"]
            if self.hess_frame == "body":                               # H in the previous LiDAR frame -> map frame
                Rp = self.prev_aft[0]
                U = np.block([[Rp, np.zeros((3, 3))], [np.zeros((3, 3)), Rp]]) @ U
            if "remove" in eig:
                x_l = x_full - U @ (U.T @ x_full)                       # the same projection as below, written on the removed set
            else:
                kept = [i for i in range(6) if not (i < 3 and eig["flags"][i])]
                Uk = U[:, kept]
                x_l = Uk @ (Uk.T @ x_full)                              # (U Lambda_p U^-1)^-1 J^T d : degenerate DOFs removed
            if dec["vo_fail"]:
                case, x = 2, x_l                                        # Eq. 16, line 2 (Eq. 14 with Lambda_p)
            else:
                Rv, pv = dec["vo"]
                x_v = np.concatenate([fc.so3_log(Rv @ Rg.T), pv - pg])  # VO step relative to the same initial guess
                case, x = 3, self.eq15_w * x_l + (1.0 - self.eq15_w) * x_v   # Eq. 15 / Eq. 16, line 3
        if dec.get("rot_vins"):                                         # F33: rotation stays VINS-Mono's
            x = np.concatenate([np.zeros(3), x[3:]])
        Rf = fc.so3_exp(x[:3]) @ Rg
        U_, _, Vt = np.linalg.svd(Rf)
        self.Rf, self.pf = U_ @ Vt, pg + x[3:]
        self.buf.append(bool(degen))                                    # line 10: Q_s <- current status
        self.prev_aft, self.prev_pub = (Ra.copy(), pa.copy()), pub
        self.prev_o, self.prev_v = dec["odom"], dec["vins"]
        self.prev_t = dec.get("t", self.prev_t)
        lam_bar = eig["lam_bar"] if eig is not None else np.full(3, np.nan)
        return self.Rf, self.pf, dict(chan=eig.get("chan") if eig is not None else None, nrem=(eig["remove"].shape[1] if eig is not None and "remove" in eig else -1), case=case, kind=dec["kind"], status=dec["status"], vo_fail=dec["vo_fail"], degen=bool(degen),
                                      lam_bar=lam_bar, w=dec["w"], step=float(np.linalg.norm(x[3:])), dtl=dec["dtl"], dtv=dec["dtv"], gyro=dec["gyro"], gyro_deg=dec["gyro_deg"], rot_vins=bool(dec.get("rot_vins")))
