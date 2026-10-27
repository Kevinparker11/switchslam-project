"""Core math for fusion_node_v2 (numpy only, Python 3.8+, works with the numpy in ROS Noetic).

VIO-primary, degeneracy-gated, information-weighted LiDAR correction, done on RELATIVE motion
in the LiDAR body frame, so the different world frames of VINS-Mono and A-LOAM never get mixed.

Conventions
  Pose = (R, p): R is 3x3 body->world rotation, p is the body origin in world.
  Relative motion k-1 -> k, expressed in the body frame at k-1:  dR = R0^T R1,  dt = R0^T (p1 - p0).
  T_IL = pose of the LiDAR frame in the IMU frame (SubT-MRS 'laser_to_imu'): x_imu = R_IL x_lidar + t_IL.
  Hessian H (6x6) is ordered [rotation(3), translation(3)] as published by the A-LOAM patches.
  Its rotation block is in Ceres quaternion-tangent units (angle = 2|delta|); D = diag(.5,.5,.5,1,1,1)
  converts it to radians.  hess_frame='world' for laserMapping (left perturbation of q_w_curr, t_w_curr),
  'body' for laserOdometry (q_last_curr, t_last_curr are already in the previous body frame).
"""
import numpy as np

D_RAD = np.diag([0.5, 0.5, 0.5, 1.0, 1.0, 1.0])
I3 = np.eye(3)


# ----------------------------------------------------------------------------- SO(3) helpers
def skew(w):
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]], float)


def so3_exp(w):
    th = float(np.linalg.norm(w))
    if th < 1e-12:
        return I3 + skew(w)
    K = skew(np.asarray(w, float) / th)
    return I3 + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def so3_log(R):
    c = (np.trace(R) - 1.0) / 2.0
    c = min(1.0, max(-1.0, c))
    th = np.arccos(c)
    if th < 1e-9:
        return np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / 2.0
    if np.pi - th < 1e-6:                      # near 180 deg: use the symmetric part
        A = (R + I3) / 2.0
        i = int(np.argmax(np.diag(A)))
        v = A[:, i] / np.sqrt(max(A[i, i], 1e-12))
        return v / np.linalg.norm(v) * th
    w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    return w * th / (2.0 * np.sin(th))


def quat_to_R(q):
    """q = (x, y, z, w)"""
    x, y, z, w = [float(v) for v in q]
    n = np.sqrt(x * x + y * y + z * z + w * w)
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def R_to_quat(R):
    """returns (x, y, z, w), w >= 0"""
    tr = np.trace(R)
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        w, x, y, z = 0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        w, x, y, z = (R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        w, x, y, z = (R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        w, x, y, z = (R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s
    q = np.array([x, y, z, w])
    return q if w >= 0 else -q


def rel_body(R0, p0, R1, p1):
    """relative motion 0 -> 1 in the body frame of pose 0"""
    return R0.T @ R1, R0.T @ (np.asarray(p1, float) - np.asarray(p0, float))


def compose(R, p, dR, dt):
    return R @ dR, np.asarray(p, float) + R @ dt


def imu_to_lidar_increment(dR_I, dt_I, R_IL, t_IL):
    """T_IL^-1 * dT_I * T_IL : the IMU-frame relative motion re-expressed for the LiDAR frame."""
    return R_IL.T @ dR_I @ R_IL, R_IL.T @ (dR_I @ t_IL + dt_I - t_IL)


def interp_pose(t, t0, R0, p0, t1, R1, p1):
    if t1 <= t0:
        return R1, np.asarray(p1, float)
    a = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
    return R0 @ so3_exp(a * so3_log(R0.T @ R1)), (1 - a) * np.asarray(p0, float) + a * np.asarray(p1, float)


# ----------------------------------------------------------------------------- degeneracy quantities
def schur_blocks(H, hess_frame="world", R_wb=None):
    """Schur complements of the A-LOAM Hessian in radians, expressed in the LiDAR body frame.
    returns S_RR (rad), S_tt, kappa_R, kappa_t"""
    H = np.asarray(H, float).reshape(6, 6)
    H = 0.5 * (H + H.T)
    Hr = D_RAD @ H @ D_RAD
    Hrr, Hrt, Htr, Htt = Hr[:3, :3], Hr[:3, 3:], Hr[3:, :3], Hr[3:, 3:]
    S_RR = Hrr - Hrt @ np.linalg.solve(Htt, Htr)
    S_tt = Htt - Htr @ np.linalg.solve(Hrr, Hrt)
    if hess_frame == "world" and R_wb is not None:     # world-frame perturbations -> body frame
        S_RR = R_wb.T @ S_RR @ R_wb
        S_tt = R_wb.T @ S_tt @ R_wb
    S_RR = 0.5 * (S_RR + S_RR.T)
    S_tt = 0.5 * (S_tt + S_tt.T)
    er = np.clip(np.linalg.eigvalsh(S_RR), 1e-12, None)
    et = np.clip(np.linalg.eigvalsh(S_tt), 1e-12, None)
    return S_RR, S_tt, float(er[-1] / er[0]), float(et[-1] / et[0])


def info_weight(S, c):
    """W = (cS + I)^-1 cS : MAP weight of a LiDAR increment with information cS against a unit VIO
    information per step.  Eigen-directions with little LiDAR information get weight ~0."""
    if c <= 0:
        return np.zeros((3, 3))
    S = 0.5 * (S + S.T)
    lam, V = np.linalg.eigh(S)
    lam = np.clip(lam, 0.0, None)
    w = c * lam / (c * lam + 1.0)
    return (V * w) @ V.T


SWITCH_SLAM_LT = np.array([0.12, 0.27, 0.48])     # Switch-SLAM Eq. 12 thresholds (as published)
W_MODES = ("schur", "diag", "iso", "const", "proj", "switch_ss", "switch_kR", "lidar", "vins")


def switch_slam_degenerate(H):
    """Switch-SLAM detection rule (Lee et al. RA-L 2024, Sec. III-C) as published: the three smallest
    eigenvalues of the 6x6 scan-matching Hessian (here in radians), normalised to unit norm, compared with
    [0.12, 0.27, 0.48]; degenerate if any is below its threshold."""
    Hr = D_RAD @ (0.5 * (np.asarray(H, float).reshape(6, 6) + np.asarray(H, float).reshape(6, 6).T)) @ D_RAD
    lam = np.sort(np.clip(np.linalg.eigvalsh(Hr), 0.0, None))[:3]
    n = np.linalg.norm(lam)
    if n <= 0:
        return True
    return bool(np.any(lam / n < SWITCH_SLAM_LT))


def translation_weight(w_mode, H, S_tt, S_RR, c, kR, kth=15.7, alpha=0.7, kth_dir=10.0):
    """3x3 weight on the LiDAR translation increment for the ablation variants.
    schur     : (c S_tt + I)^-1 c S_tt                      (ours: marginal translational information)
    diag      : same with the diagonal block H_tt            (ignores rotation-translation coupling)
    iso       : isotropic, same mean information tr(S_tt)/3 (no directionality)
    const     : alpha * I                                   (fixed complementary blend)
    proj      : hard per-direction 0/1 on S_tt, 0 where lam_max/lam_i > kth_dir (DCReg-style detection,
                Zhang-2016-style remapping)
    switch_ss : all-or-nothing, VIO when the Switch-SLAM rule fires, else LiDAR
    switch_kR : all-or-nothing, LiDAR when kappa(S_RR) <= kth, else VIO
    lidar / vins : W = I / W = 0"""
    if w_mode == "schur":
        return info_weight(S_tt, c)
    if w_mode == "diag":
        Hr = D_RAD @ (0.5 * (H + H.T)) @ D_RAD
        return info_weight(Hr[3:, 3:], c)
    if w_mode == "iso":
        lb = max(float(np.trace(S_tt)) / 3.0, 0.0)
        return (c * lb / (c * lb + 1.0)) * I3
    if w_mode == "const":
        return alpha * I3
    if w_mode == "proj":
        lam, V = np.linalg.eigh(0.5 * (S_tt + S_tt.T))
        lam = np.clip(lam, 1e-12, None)
        keep = (lam[-1] / lam) <= kth_dir
        return (V * keep.astype(float)) @ V.T
    if w_mode == "switch_ss":
        return np.zeros((3, 3)) if switch_slam_degenerate(H) else I3.copy()
    if w_mode == "switch_kR":
        return I3.copy() if kR <= kth else np.zeros((3, 3))
    if w_mode == "lidar":
        return I3.copy()
    if w_mode == "vins":
        return np.zeros((3, 3))
    raise ValueError("unknown w_mode %s" % w_mode)


def otsu_threshold(values, bins=64):
    """Otsu (1979) cut on a 1-D sample (use log10 kappa). Returns the cut in the same units."""
    x = np.asarray(values, float)
    x = x[np.isfinite(x)]
    if len(x) < 10 or np.ptp(x) <= 0:
        return np.nan
    hist, edges = np.histogram(x, bins)
    c = 0.5 * (edges[1:] + edges[:-1])
    w0 = np.cumsum(hist).astype(float)
    w1 = w0[-1] - w0
    m0 = np.cumsum(hist * c)
    mu0 = m0 / np.maximum(w0, 1)
    mu1 = (m0[-1] - m0) / np.maximum(w1, 1)
    return float(c[np.argmax(w0 * w1 * (mu0 - mu1) ** 2)])


class KappaGate:
    """Gate on kappa(S_RR).  mode 'fixed': kappa <= kth.  mode 'otsu': the cut is re-estimated
    label-free from the last `window` frames (log10 kappa, Otsu), starting from kth until
    `min_samples` frames have been seen."""

    def __init__(self, kth=15.7, mode="fixed", window=1200, min_samples=300, every=50):
        self.kth, self.mode, self.window, self.min_samples, self.every = kth, mode, window, min_samples, every
        self.buf, self.n = [], 0

    def __call__(self, kappa_R):
        if self.mode == "otsu":
            self.buf.append(np.log10(max(kappa_R, 1e-12)))
            if len(self.buf) > self.window:
                self.buf = self.buf[-self.window:]
            self.n += 1
            if len(self.buf) >= self.min_samples and self.n % self.every == 0:
                cut = otsu_threshold(self.buf)
                if np.isfinite(cut):
                    self.kth = float(10 ** cut)
        return bool(kappa_R <= self.kth), self.kth


# ----------------------------------------------------------------------------- the fusion step
class FusionCore:
    """Feed one LiDAR scan-to-map pose per call (with the VINS-Mono pose interpolated to the same time).

    modes: INIT (first call), WARMUP (no VINS yet, or within t_warm s of its first pose),
           VO_FAIL (VINS step rejected), FUSED (VIO increment corrected by gated, weighted LiDAR)."""

    def __init__(self, R_IL=I3, t_IL=np.zeros(3), c_t=1e-3, c_R=0.0, gate=None, t_warm=20.0,
                 hess_frame="world", jump_max=1.0, rot_jump_max=0.5, gate_trans=False, kth_t=1e9,
                 w_mode="schur", alpha=0.7, tau_R=0.0, c_Rb=1.0, bias_axis="all", clip_R=0.0):
        assert w_mode in W_MODES, w_mode
        # slow rotation-drift correction (complementary filter): tau_R = time constant in s (0 = off); the LiDAR-minus-VIO
        # rotation increment is low-passed with weight info_weight(S_RR, c_Rb) per eigen-direction
        self.tau_R, self.c_Rb, self.bias_axis = tau_R, c_Rb, bias_axis   # bias_axis "yaw": only about the gravity axis (VINS tilt is gravity-observable)
        self.bR = np.zeros(3)
        self.byaw = 0.0
        self.clip_R = clip_R          # bounded influence: per-step innovation clipped to +-clip_R rad (0 = off)
        self.t_prev = None
        self.w_mode, self.alpha = w_mode, alpha
        self.R_IL, self.t_IL = np.asarray(R_IL, float), np.asarray(t_IL, float)
        self.c_t, self.c_R, self.t_warm, self.hess_frame = c_t, c_R, t_warm, hess_frame
        self.gate = gate if gate is not None else KappaGate()
        self.jump_max, self.rot_jump_max = jump_max, rot_jump_max
        self.gate_trans, self.kth_t = gate_trans, kth_t
        self.Rf = self.pf = None
        self.prev_a = self.prev_v = None
        self.t_vins0 = None

    def initialised(self):
        return self.Rf is not None

    def predict(self, vins_now):
        """initial guess for the next scan: last fused pose moved by the VINS motion since then"""
        if self.Rf is None:
            return None
        if vins_now is None or self.prev_v is None:
            return self.Rf, self.pf
        dR_I, dt_I = rel_body(self.prev_v[0], self.prev_v[1], vins_now[0], vins_now[1])
        dR, dt = imu_to_lidar_increment(dR_I, dt_I, self.R_IL, self.t_IL)
        if np.linalg.norm(dt) > 3 * self.jump_max:
            return self.Rf, self.pf
        return compose(self.Rf, self.pf, dR, dt)

    def step(self, t, aft, vins=None, H=None, vo_fail=False):
        """aft = (R, p) LiDAR pose in the A-LOAM map frame; vins = (R, p) IMU pose in the VINS world
        frame at the same time (or None); H = 6x6 Hessian (or None). Returns (R, p, info)."""
        Ra, pa = np.asarray(aft[0], float), np.asarray(aft[1], float)
        info = dict(mode="INIT", gate=0, kappa_R=np.nan, kappa_t=np.nan, kth=np.nan,
                    wt=(np.nan,) * 3, wR=(np.nan,) * 3, dta=np.nan, dtv=np.nan)
        if vins is not None and self.t_vins0 is None:
            self.t_vins0 = t
        if self.Rf is None:
            self.Rf, self.pf = Ra.copy(), pa.copy()
            self.prev_a = (Ra, pa)
            self.prev_v = vins
            return self.Rf, self.pf, info

        dR_a, dt_a = rel_body(self.prev_a[0], self.prev_a[1], Ra, pa)
        vins_ok = vins is not None and not vo_fail
        jump = False
        if vins_ok and self.prev_v is not None:
            dR_I, dt_I = rel_body(self.prev_v[0], self.prev_v[1], vins[0], vins[1])
            dR_v, dt_v = imu_to_lidar_increment(dR_I, dt_I, self.R_IL, self.t_IL)
            jump = np.linalg.norm(dt_v) > self.jump_max or np.linalg.norm(so3_log(dR_v)) > self.rot_jump_max
        have_v = vins_ok and self.prev_v is not None and not jump
        lost = self.t_vins0 is not None and self.prev_v is not None and (not vins_ok or jump)
        info["dta"] = float(np.linalg.norm(dt_a))

        if not have_v:
            # VINS absent, still starting, jumped or re-initialised: LiDAR carries this step.
            # After a loss the VIO warm-up restarts, because a re-initialised VINS has the same
            # start-up transient as at the beginning of the run.
            mode = "VO_FAIL" if lost else "WARMUP"
            if lost:
                self.t_vins0 = None
            W_t, W_R = I3, I3
            dR_v, dt_v = dR_a, dt_a
        elif (t - self.t_vins0) < self.t_warm:
            mode, W_t, W_R = "WARMUP", I3, I3
        else:
            mode = "FUSED"
            info["dtv"] = float(np.linalg.norm(dt_v))
            if H is None:
                W_t = W_R = np.zeros((3, 3))
            else:
                S_RR, S_tt, kR, kt = schur_blocks(H, self.hess_frame, self.prev_a[0])
                ok, kth = self.gate(kR)
                if self.gate_trans:
                    ok = ok and kt <= self.kth_t
                info.update(kappa_R=kR, kappa_t=kt, kth=kth, gate=int(ok))
                if self.w_mode != "schur" and np.linalg.norm(dt_a) <= self.jump_max:
                    # ablation variants: no kappa gate, rotation always from VIO
                    W_t = translation_weight(self.w_mode, np.asarray(H, float).reshape(6, 6), S_tt, S_RR,
                                             self.c_t, kR, kth=self.gate.kth, alpha=self.alpha)
                    W_R = np.zeros((3, 3))
                elif self.w_mode != "schur":
                    W_t = W_R = np.zeros((3, 3))
                elif ok and np.linalg.norm(dt_a) <= self.jump_max:
                    W_t = info_weight(S_tt, self.c_t)
                    W_R = info_weight(S_RR, self.c_R)
                    if self.tau_R > 0 and self.t_prev is not None:
                        g = min(1.0, max(0.0, t - self.t_prev) / self.tau_R)
                        z = so3_log(dR_a) - so3_log(dR_v)
                        if self.bias_axis == "yaw":
                            gL = self.R_IL.T @ (self.prev_v[0].T @ np.array([0.0, 0.0, 1.0]))   # world up in the LiDAR frame
                            i_g = 1.0 / max(float(gL @ np.linalg.solve(S_RR + 1e-9 * I3, gL)), 1e-12)  # marginal information about yaw
                            w = self.c_Rb * i_g / (self.c_Rb * i_g + 1.0)
                            inn = float(z @ gL) - self.byaw
                            if self.clip_R > 0:
                                inn = float(np.clip(inn, -self.clip_R, self.clip_R))
                            self.byaw += g * w * inn
                            self.gL = gL
                        else:
                            inn = z - self.bR
                            if self.clip_R > 0:
                                inn = np.clip(inn, -self.clip_R, self.clip_R)
                            self.bR = self.bR + g * (info_weight(S_RR, self.c_Rb) @ inn)
                else:
                    W_t = W_R = np.zeros((3, 3))
            info["wt"] = tuple(np.sort(np.linalg.eigvalsh(0.5 * (W_t + W_t.T))))
            info["wR"] = tuple(np.sort(np.linalg.eigvalsh(0.5 * (W_R + W_R.T))))

        if lost:
            self.bR = np.zeros(3)
            self.byaw = 0.0
        phi_v = so3_log(dR_v)
        if mode == "FUSED":
            phi_v = phi_v + (self.byaw * getattr(self, "gL", np.zeros(3)) if self.bias_axis == "yaw" else self.bR)
        phi = W_R @ so3_log(dR_a) + (I3 - W_R) @ phi_v
        dt = W_t @ dt_a + (I3 - W_t) @ dt_v
        self.Rf, self.pf = compose(self.Rf, self.pf, so3_exp(phi), dt)
        # re-orthonormalise
        U, _, Vt = np.linalg.svd(self.Rf)
        self.Rf = U @ Vt
        self.prev_a = (Ra, pa)
        self.prev_v = vins
        self.t_prev = t
        info["mode"] = mode
        info["bR"] = float(abs(self.byaw)) if self.bias_axis == "yaw" else float(np.linalg.norm(self.bR))
        return self.Rf, self.pf, info
