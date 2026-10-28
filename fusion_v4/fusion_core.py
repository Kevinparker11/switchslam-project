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


def info_weight(S, c, gamma=1.0):
    """W = (cS + gamma I)^-1 cS : MAP weight of a LiDAR increment with information cS against a VIO
    information gamma I per step (gamma = 1: the unit VIO information of the original rule).
    Eigen-directions with little LiDAR information get weight ~0; gamma -> 0 gives W -> I."""
    if c <= 0:
        return np.zeros((3, 3))
    S = 0.5 * (S + S.T)
    lam, V = np.linalg.eigh(S)
    lam = np.clip(lam, 0.0, None)
    w = c * lam / (c * lam + max(float(gamma), 0.0) + 1e-300)
    return (V * w) @ V.T


class VioConsistency:
    """Online check of how far the VIO translation agrees with the LiDAR translation; its output gamma scales the
    VIO prior information in info_weight (gamma = 1: the unit VIO information used when c_T, c_R were calibrated
    on Multi Floor; gamma = 0: the LiDAR carries the step).  The R / T / SAH structure is not changed.

    Every scan closes a window of the last T seconds inside one continuous VIO segment.  Both relative motions are
    expressed in the LiDAR body frame at the window start (da: LiDAR, dv: VIO through T_IL).  Per window:
      stat 'vec'   : rho^2 = |dv - da|^2 / max(|da|, d_min)^2   (relative disagreement, scale and direction)
      stat 'scale' : ln(|dv| / |da|)^2, only windows with |da| >= d_min   (VIO scale against LiDAR scale)
    The causal statistic r = sqrt(mean over the windows that ended in the last `avg` s, or over all windows of the
    current VIO segment if avg is None); it needs >= n_min windows.
      rule 'ratio' : gamma = min(1, ref^2 / r^2)          (covariance matching, Mehra 1972)
      rule 'gate'  : gamma = 1 while r <= ref, else 0     (consistency test; ref = largest r seen on Multi Floor)
    While r is undefined (no motion) the previous gamma is held; at the start of every VIO segment gamma = 0 until
    the VIO has shown that it agrees with the LiDAR.  The estimate restarts whenever the VIO is lost or re-initialised."""

    def __init__(self, ref, stat="scale", rule="gate", T=10.0, avg=10.0, d_min=1.0, n_min=5, debias=False, T_loc=10.0,
                 proj=False, start_trusted=False):
        assert stat in ("vec", "scale") and rule in ("ratio", "gate")
        self.ref, self.stat, self.rule, self.T, self.avg, self.d_min, self.n_min = ref, stat, rule, T, avg, d_min, n_min
        # proj (round 2 of the OT study, V2): the window displacements are formed from per-step increments that were first
        # multiplied by the LiDAR translation weight of that step (both LiDAR channels: Schur T capped by the orientation
        # tensor), so the VIO is judged only along directions the LiDAR can vouch for; a LiDAR-degenerate axis carries no
        # evidence against the VIO.  update() then needs inc = (projected LiDAR increment, projected VIO increment), world frame.
        # start_trusted: gamma = 1 at the start of a segment until the check has enough windows to judge (V1b, V2);
        # False = untrusted until the VIO has agreed (the G20 behaviour).
        self.proj, self.start_trusted = proj, start_trusted
        # debias (stat 'scale', avg None): the test uses the spread of x = ln(|dv|/|da|) about its segment median, i.e. the
        # VIO is judged after its constant scale error has been removed by scale(); without it r = sqrt(mean x^2) mixes a
        # constant scale bias (correctable) with erratic motion (not correctable).
        self.debias, self.T_loc = debias, T_loc
        self.reset()

    def reset(self):
        self.ts, self.A, self.V, self.rw = [], [], [], []      # times, LiDAR poses, VIO poses, (t_end, value)
        self.i0, self.g, self.r = 0, (1.0 if getattr(self, "start_trusted", False) else 0.0), float("nan")
        self.CA, self.CV = [], []                               # proj: cumulative projected increments (world)
        self.sum, self.nused = 0.0, 0
        self.xs = []                                            # signed ln(|dv|/|da|) of every window (stat 'scale')
        self.s = 1.0
        self.xt, self.s_loc = [], 1.0                           # (t_end, x) of the windows ending in the last T_loc s

    def restart_windows(self):
        """Forget the stored poses, so that no window spans the next step (a LiDAR gap): the gate state and the statistics
        gathered so far are kept, and new windows form once T s of poses have been stored again."""
        self.ts, self.A, self.V, self.i0 = [], [], [], 0
        self.CA, self.CV = [], []

    def scale_local(self):
        """Local VIO scale: median |LiDAR displacement| / |VIO displacement| of the 10 s windows that ended in the last T_loc s
        (chord lengths, so per-scan jitter of either source does not inflate it); held when there is no motion."""
        return self.s_loc

    def scale(self):
        """Robust VIO scale correction for the current segment: s = exp(-median x) over its windows (>= n_min of them),
        i.e. the median ratio |LiDAR motion| / |VIO motion|; 1.0 before that.  The median ignores the few windows in which
        either source misbehaves (a LiDAR blow-up or a VIO re-initialisation transient cannot drag it)."""
        return self.s

    def update(self, t, aft, vins, R_IL, t_IL, inc=None):
        self.ts.append(t); self.A.append(aft); self.V.append(vins)
        if self.proj:
            ia, iv = (np.zeros(3), np.zeros(3)) if inc is None else (np.asarray(inc[0], float), np.asarray(inc[1], float))
            self.CA.append((self.CA[-1] if self.CA else np.zeros(3)) + ia)
            self.CV.append((self.CV[-1] if self.CV else np.zeros(3)) + iv)
        while self.i0 + 1 < len(self.ts) and self.ts[self.i0 + 1] <= t - self.T:
            self.i0 += 1
        if self.ts[self.i0] <= t - self.T + 1e-6 and self.i0 < len(self.ts) - 1:
            j = self.i0
            if self.proj:
                da, dv = self.CA[-1] - self.CA[j], self.CV[-1] - self.CV[j]
            else:
                _, da = rel_body(self.A[j][0], self.A[j][1], aft[0], aft[1])
                dRI, dtI = rel_body(self.V[j][0], self.V[j][1], vins[0], vins[1])
                _, dv = imu_to_lidar_increment(dRI, dtI, R_IL, t_IL)
            la = float(np.linalg.norm(da))
            if self.stat == "vec":
                self.rw.append((t, float(np.linalg.norm(dv - da)) ** 2 / max(la, self.d_min) ** 2))
            elif la >= self.d_min:
                x = float(np.log(max(float(np.linalg.norm(dv)), 1e-3) / la))
                self.rw.append((t, x ** 2))
                self.xs.append(x)
                self.xt.append((t, x))
                while self.xt and self.xt[0][0] <= t - self.T_loc:
                    self.xt.pop(0)
                if self.xt:
                    self.s_loc = float(np.exp(-np.median([v for _, v in self.xt])))
        while self.avg is not None and self.rw and self.rw[0][0] <= t - self.avg:
            self.rw.pop(0)
        if self.i0 > 2000:                                       # keep the buffers short
            k = self.i0
            self.ts, self.A, self.V, self.i0 = self.ts[k:], self.A[k:], self.V[k:], 0
            if self.proj:
                self.CA, self.CV = self.CA[k:], self.CV[k:]
        if len(self.rw) >= self.n_min:
            if self.debias and self.stat == "scale" and self.avg is None:
                med = float(np.median(self.xs))
                self.s = float(np.exp(-med))
                self.r = float(np.sqrt(np.mean((np.asarray(self.xs) - med) ** 2)))
            elif self.avg is None:                                # running mean over the whole segment
                self.sum += sum(v for _, v in self.rw[self.nused:]) if self.nused < len(self.rw) else 0.0
                self.nused = len(self.rw)
                self.r = float(np.sqrt(self.sum / self.nused))
                if self.stat == "scale" and self.xs:
                    self.s = float(np.exp(-np.median(self.xs)))
            else:
                self.r = float(np.sqrt(np.mean([v for _, v in self.rw])))
            if self.rule == "gate":
                self.g = 1.0 if self.r <= self.ref else 0.0
            else:
                self.g = float(min(1.0, self.ref ** 2 / max(self.r ** 2, 1e-12)))

    def gamma(self):
        return self.g

    def trusted(self):
        """long-run record of the VIO in this segment (used by the LiDAR blow-up guard)"""
        return self.g > 0.5


class VioChecks:
    """Several VioConsistency checks at once (e.g. a slow segment-level test for a persistent scale bias and a fast
    one for a sudden blow-up); gamma = the smallest of their gammas."""

    def __init__(self, checks):
        self.checks = list(checks)
        self.proj = any(getattr(c, "proj", False) for c in self.checks)

    def reset(self):
        for c in self.checks:
            c.reset()

    def update(self, *a, **k):
        for c in self.checks:
            c.update(*a, **k)

    def restart_windows(self):
        for c in self.checks:
            c.restart_windows()

    def gamma(self):
        return min(c.gamma() for c in self.checks)

    def trusted(self):
        """the VIO's long-run record = the first (segment-level) check only: a fast check may close because the LiDAR,
        not the VIO, has just gone wrong, and that must not switch the LiDAR guard off"""
        return self.checks[0].trusted()


class RotConsistency:
    """Rotation analogue of VioConsistency (design B of docs/results/R_Channel_Rotation_Aware_Test_Protocol.md).
    Over windows of T_fast and T_slow seconds inside one continuous VIO segment it forms the rotation increment of the LiDAR
    output, dRa = R_a(i)^T R_a(j), and of the VIO moved to the LiDAR frame, dRv = R_IL^T (R_I(i)^T R_I(j)) R_IL, and takes
    e = || log(dRa^T dRv) || (rad).  The check is open (gamma_R = 1) while the latest e of both windows is <= its reference
    (the largest value on the A-LOAM-stack Multi Floor F8/F16 recordings), closed (gamma_R = 0) otherwise; it is open until
    the first window of a segment exists.  The LiDAR is the rotation reference, as for the translation check: the check cannot
    tell which sensor is wrong.
    guard > 0: a LiDAR rotation of more than `guard` rad over the last T_fast s marks the LiDAR step as failed (lidar_bad()).
    The estimate restarts whenever the VIO is lost or re-initialised."""

    def __init__(self, ref_fast, ref_slow, T_fast=2.0, T_slow=10.0, guard=0.0):
        self.ref_fast, self.ref_slow, self.T_fast, self.T_slow, self.guard = ref_fast, ref_slow, T_fast, T_slow, guard
        self.reset()

    def reset(self):
        self.ts, self.RA, self.RV = [], [], []
        self.e_fast = self.e_slow = float("nan")
        self.ang_fast = 0.0

    def restart_windows(self):
        self.ts, self.RA, self.RV = [], [], []

    def _win(self, t, T):
        """index of the newest stored pose at least T s old (None if the segment is shorter than T)"""
        if not self.ts or self.ts[0] > t - T + 1e-6:
            return None
        j = 0
        while j + 1 < len(self.ts) and self.ts[j + 1] <= t - T + 1e-6:
            j += 1
        return j

    def update(self, t, Ra, Rv_imu, R_IL):
        self.ts.append(t); self.RA.append(np.asarray(Ra, float)); self.RV.append(np.asarray(Rv_imu, float))
        for T in (self.T_fast, self.T_slow):
            j = self._win(t, T)
            if j is None or j >= len(self.ts) - 1:
                continue
            dRa = self.RA[j].T @ Ra
            dRv = R_IL.T @ (self.RV[j].T @ Rv_imu) @ R_IL
            e = float(np.linalg.norm(so3_log(dRa.T @ dRv)))
            if T == self.T_fast:
                self.e_fast, self.ang_fast = e, float(np.linalg.norm(so3_log(dRa)))
            else:
                self.e_slow = e
        while len(self.ts) > 2 and self.ts[1] <= t - self.T_slow - 1.0:      # keep the buffers short
            self.ts.pop(0); self.RA.pop(0); self.RV.pop(0)

    def lidar_bad(self):
        return self.guard > 0 and self.ang_fast > self.guard

    def gamma(self):
        if np.isfinite(self.e_fast) and self.e_fast > self.ref_fast:
            return 0.0
        if np.isfinite(self.e_slow) and self.e_slow > self.ref_slow:
            return 0.0
        return 1.0


SWITCH_SLAM_LT = np.array([0.12, 0.27, 0.48])     # Switch-SLAM Eq. 12 thresholds (as published)
W_MODES = ("schur", "diag", "iso", "const", "proj", "switch_ss", "switch_kR", "lidar", "vins")


def orientation_tensor(pts, k=12, subsample=400, rng=None):
    """Channel T (additional T): T = (1/n) sum n n^T over local-PCA normals of a random subsample of a scan's planar points,
    computed from the raw points alone (no scan matching, no solver state).  Same recipe as channelT_test/degen_logger.py
    (k nearest neighbours including the point itself, subsample cap), in numpy only (brute-force neighbours).
    Returns (T 3x3 with trace 1, n) or None when there are too few points."""
    pts = np.asarray(pts, float)
    if len(pts) < k + 1:
        return None
    rng = rng if rng is not None else np.random.default_rng(0)
    m = min(len(pts), subsample)
    idx = rng.choice(len(pts), m, replace=False)
    q = pts[idx]
    d2 = (q * q).sum(1)[:, None] + (pts * pts).sum(1)[None, :] - 2.0 * q @ pts.T
    nn = np.argpartition(d2, k - 1, axis=1)[:, :k]
    nb = pts[nn]
    nb = nb - nb.mean(axis=1, keepdims=True)
    cov = np.einsum("mki,mkj->mij", nb, nb) / (k - 1)
    _, v = np.linalg.eigh(cov)
    n = v[:, :, 0]
    return n.T @ n / len(n), len(n)


T_MODES = ("min", "gmean", "harm", "tonly", "agree2", "hybrid", "max")


def t_combine(mode, H, S_tt, T, hess_frame="world", R_wb=None):
    """Orientation-tensor (OT) channel combined with the Schur translation channel (design of 28 Oct 2026,
    docs/results/OT_Channel_Study.md).  Along each eigen-direction v_i of S_tt the solver claims lambda_i; the raw-scan
    normals support tau_i = N v_i^T T v_i with N = tr(H_tt) (same total mass: no free scale).  Per direction:
        min    : min(lambda, tau)                 fail-safe: the LiDAR is trusted only as far as BOTH channels allow
        gmean  : sqrt(lambda tau)                 equal-weight log-average of the two opinions
        harm   : 2 lambda tau / (lambda + tau)     harmonic mean (between min and gmean)
        tonly  : tau                              orientation tensor alone (solver used only for the directions and N)
        agree2 : lambda if 1/2 <= tau/lambda <= 2 else tau   (solver unless the two disagree by more than 2x)
        hybrid : Schur complement with H_tt replaced by N T:  N T - H_tR H_RR^-1 H_Rt  (raw-normal translation support,
                 solver's rotation-translation coupling), eigenvalues clipped at 0
        max    : max(lambda, tau)                 optimistic (for completeness; not a fail-safe)
    Returns (S_tt', min_i lambda_i'/lambda_i)."""
    H = np.asarray(H, float).reshape(6, 6)
    Hr = D_RAD @ (0.5 * (H + H.T)) @ D_RAD
    Htt = Hr[3:, 3:]
    Trot = np.asarray(T, float)
    if hess_frame == "world" and R_wb is not None:
        Htt = R_wb.T @ Htt @ R_wb
    N = float(np.trace(Htt))
    S = 0.5 * (S_tt + S_tt.T)
    lam, V = np.linalg.eigh(S)
    lam = np.clip(lam, 0.0, None)
    if mode == "hybrid":
        Hrr, Hrt, Htr = Hr[:3, :3], Hr[:3, 3:], Hr[3:, :3]
        C = Htr @ np.linalg.solve(Hrr, Hrt)
        if hess_frame == "world" and R_wb is not None:
            C = R_wb.T @ C @ R_wb
        Sh = N * Trot - C
        Sh = 0.5 * (Sh + Sh.T)
        lh, Vh = np.linalg.eigh(Sh)
        Sh = (Vh * np.clip(lh, 0.0, None)) @ Vh.T
        lam2 = np.clip(np.einsum("ij,jk,ki->i", V.T, Sh, V), 0.0, None)
        return Sh, float(np.min(lam2 / np.maximum(lam, 1e-300)))
    tau = np.clip(N * np.einsum("ij,jk,ki->i", V.T, Trot, V), 0.0, None)
    if mode == "min":
        lam2 = np.minimum(lam, tau)
    elif mode == "gmean":
        lam2 = np.sqrt(lam * tau)
    elif mode == "harm":
        lam2 = 2.0 * lam * tau / np.maximum(lam + tau, 1e-300)
    elif mode == "tonly":
        lam2 = tau
    elif mode == "agree2":
        r = tau / np.maximum(lam, 1e-300)
        lam2 = np.where((r >= 0.5) & (r <= 2.0), lam, tau)
    elif mode == "max":
        lam2 = np.maximum(lam, tau)
    else:
        raise ValueError("unknown OT mode %s" % mode)
    return (V * lam2) @ V.T, float(np.min(lam2 / np.maximum(lam, 1e-300)))


# Round 2 of the OT study (docs/results/OT_Channel_Round2.md): basis-free matrix combinations of A = S_tt (solver) and
# B = N T (raw geometry, same total mass), and two rules in which the OT channel is a separate weight.
T_MODES2 = ("gmin", "gmax", "psum", "agm", "ci", "wprod", "wmean", "smin")
W_RULES = ("wprod", "wmean")


def _sym(X):
    return 0.5 * (X + X.T)


def _reg(X, eps=1e-9):
    X = _sym(np.asarray(X, float))
    return X + eps * max(float(np.trace(X)), 1e-300) * I3


def _psd_apply(X, f):
    """f applied to the eigenvalues of the symmetric X (eigenvalues clipped at 0 first)"""
    lam, V = np.linalg.eigh(_sym(X))
    return (V * f(np.clip(lam, 0.0, None))) @ V.T


def ot_matrix_rule(mode, A, B):
    """basis-free combination of two 3x3 PSD information matrices (A solver, B geometry)
        gmin : B^1/2 min(M, I) B^1/2, M = B^-1/2 A B^-1/2   (generalised-eigen min: what both support)
        gmax : B^1/2 max(M, I) B^1/2                        ('safe fusion', optimistic)
        psum : 2 (A^-1 + B^-1)^-1 = 2 A (A + B)^-1 B        (matrix harmonic mean / parallel sum)
        agm  : A # B = A^1/2 (A^-1/2 B A^-1/2)^1/2 A^1/2    (Ando geometric mean)
        ci   : w A + (1 - w) B, w in [0, 1] maximising det  (covariance intersection)"""
    A, B = _sym(np.asarray(A, float)), _sym(np.asarray(B, float))
    if mode in ("gmin", "gmax"):
        Br = _reg(B)
        Bh = _psd_apply(Br, np.sqrt)
        Bih = _psd_apply(Br, lambda w: 1.0 / np.sqrt(np.maximum(w, 1e-300)))
        M = _sym(Bih @ A @ Bih)
        f = (lambda m: np.minimum(m, 1.0)) if mode == "gmin" else (lambda m: np.maximum(m, 1.0))
        S = Bh @ _psd_apply(M, f) @ Bh
    elif mode == "psum":
        S = 2.0 * A @ np.linalg.solve(_reg(A + B), B)
    elif mode == "agm":
        Ar = _reg(A)
        Ah = _psd_apply(Ar, np.sqrt)
        Aih = _psd_apply(Ar, lambda w: 1.0 / np.sqrt(np.maximum(w, 1e-300)))
        S = Ah @ _psd_apply(_sym(Aih @ B @ Aih), np.sqrt) @ Ah
    elif mode == "ci":
        best, S = -np.inf, A
        for w in np.linspace(0.0, 1.0, 101):
            C = w * A + (1.0 - w) * B
            sgn, ld = np.linalg.slogdet(_reg(C))
            if sgn > 0 and ld > best:
                best, S = ld, C
    else:
        raise ValueError("unknown matrix rule %s" % mode)
    return _psd_apply(_sym(S), lambda w: w)


def t_weight(mode, H, S_tt, T, c, gamma=1.0, hess_frame="world", R_wb=None):
    """Translation weight W_t with the OT channel (round 1 rules T_MODES, round 2 rules T_MODES2).
    S-rules: W = info_weight(S', c, gamma) with S' the combined information.  W-rules (the OT channel as its own weight):
        wprod : W_A^1/2 W_B W_A^1/2     (W_A = info_weight(A), W_B = info_weight(N T): AND of the two weights)
        wmean : (W_A + W_B) / 2        (equal vote of the two weights)
    Returns (W, min_i lambda_i'/lambda_i along the solver's eigen-directions, or the W ratio for W-rules)."""
    if mode in T_MODES:
        S2, r = t_combine(mode, H, S_tt, T, hess_frame, R_wb)
        return info_weight(S2, c, gamma), r
    Hm = np.asarray(H, float).reshape(6, 6)
    Hr = D_RAD @ _sym(Hm) @ D_RAD
    Htt = Hr[3:, 3:]
    if hess_frame == "world" and R_wb is not None:
        Htt = R_wb.T @ Htt @ R_wb
    A = _sym(S_tt)
    B = float(np.trace(Htt)) * _sym(np.asarray(T, float))
    lam, V = np.linalg.eigh(A)
    lam = np.clip(lam, 0.0, None)
    if mode == "smin":
        # shape cap (scale-free): along each eigen-direction of A the solver's anisotropy lambda_i / lambda_max may not
        # exceed the geometry's tau_i / tau_max: lambda_i' = min(lambda_i, lambda_max tau_i / tau_max).  The total mass of the
        # two channels is never compared (their point sets differ), only how unevenly each spreads it over directions.
        tau = np.clip(np.einsum("ij,jk,ki->i", V.T, B, V), 0.0, None)
        lam2 = np.minimum(lam, tau * lam.max() / max(float(tau.max()), 1e-300))
        return info_weight((V * lam2) @ V.T, c, gamma), float(np.min(lam2 / np.maximum(lam, 1e-300)))
    if mode in W_RULES:
        WA, WB = info_weight(A, c, gamma), info_weight(B, c, gamma)
        if mode == "wprod":
            WAh = _psd_apply(WA, np.sqrt)
            W = _sym(WAh @ WB @ WAh)
        else:
            W = 0.5 * (WA + WB)
        wa = np.einsum("ij,jk,ki->i", V.T, WA, V)
        wn = np.einsum("ij,jk,ki->i", V.T, W, V)
        return W, float(np.min(wn / np.maximum(wa, 1e-300)))
    S2 = ot_matrix_rule(mode, A, B)
    lam2 = np.clip(np.einsum("ij,jk,ki->i", V.T, S2, V), 0.0, None)
    return info_weight(S2, c, gamma), float(np.min(lam2 / np.maximum(lam, 1e-300)))


def t_cap_info(H, S_tt, T, hess_frame="world", R_wb=None):
    """the 'min' rule of t_combine (F18, TCAP=1): lambda_i' = min(lambda_i, tr(H_tt) v_i^T T v_i)"""
    return t_combine("min", H, S_tt, T, hess_frame, R_wb)


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
                 w_mode="schur", alpha=0.7, tau_R=0.0, c_Rb=1.0, bias_axis="all", clip_R=0.0, vio_adapt=None,
                 vio_scale_T=0.0, vio_scale_dmin=1.0, vio_scale_proj=False, vio_scale_seg=False,
                 lidar_guard_T=0.0, lidar_guard_ex=0.0, vio_scale_along=False, gamma_min=0.0,
                 gap_T=0.0, gap_vmax=5.0, gap_wmax=2.0, switch_rot=False,
                 rot_adapt=None, rot_c_fail=1.0, rot_gamma_min=1e-3, t_cap=False, t_mode="min"):
        assert w_mode in W_MODES, w_mode
        # t_cap: the additional-T fail-safe (t_cap_info): the translation information of the Schur weight is capped, direction by
        # direction, by what the raw-scan orientation tensor T supports.  False = F8/F16 exactly (bit for bit); with no T for a
        # scan the weight is the uncapped one.
        self.t_cap, self.t_mode = t_cap, t_mode
        assert t_mode in T_MODES + T_MODES2, t_mode
        # switch_rot (w_mode 'switch_ss' only): the rotation follows the same all-or-nothing switch as the translation (the whole
        # 6-DoF increment from the LiDAR, or from the VIO when the Switch-SLAM rule fires); False = rotation always from the VIO (F12)
        self.switch_rot = switch_rot
        # rot_adapt: None (rotation weight exactly as before) or a RotConsistency (design B).  While its check is open the R weight
        # is the usual info_weight(S_RR, c_R, gamma) (zero for c_R = 0, i.e. rotation from the VIO, as in F8/F16); while it is
        # closed (the VIO rotation disagrees with the LiDAR beyond the reference) the LiDAR rotation carries the step in every
        # direction with LiDAR information: info_weight(S_RR, rot_c_fail, rot_gamma_min).  A LiDAR rotation flagged by the
        # guard gives W_R = 0 (the VIO carries the rotation).  rot_c_fail and rot_gamma_min are design values, not tuned.
        self.rot_adapt, self.rot_c_fail, self.rot_gamma_min = rot_adapt, rot_c_fail, rot_gamma_min
        # vio_adapt: None (unit VIO information, the original rule) or a VioConsistency; its gamma scales the VIO
        # information in both Schur weights (W_t and W_R).  The R / T / SAH structure is unchanged.
        self.vio_adapt = vio_adapt
        # vio_scale_T > 0: online VIO scale correction.  Monocular VIO scale is weakly observable and drifts; the LiDAR is
        # metric.  s = (LiDAR path length) / (VIO path length) over the last vio_scale_T s of the current VIO segment
        # (updated once the LiDAR moved >= vio_scale_dmin m in that span, else held); the VIO translation increment is
        # multiplied by s before the Schur-weighted fusion.  Restarts at every VIO loss / re-initialisation.
        # vio_scale_proj: measure both path lengths only along LiDAR-constrained motion, i.e. after projecting the
        # increments with the Schur translation weight W_t = info_weight(S_tt, c_t) (a LiDAR-degenerate corridor axis
        # then carries no scale evidence).
        self.vio_scale_T, self.vio_scale_dmin, self.vio_scale_proj = vio_scale_T, vio_scale_dmin, vio_scale_proj
        self.sbuf, self.s_vio = [], 1.0
        # vio_scale_seg: VIO translation increments are multiplied by vio_adapt.scale(), the robust (median) scale of the
        # current VIO segment, instead of the 10 s path-length ratio of vio_scale_T (used only with vio_adapt).
        self.vio_scale_seg = vio_scale_seg
        # lidar_guard_T > 0: LiDAR blow-up guard.  While the VIO is trusted (gamma > 0.5), if over the last lidar_guard_T s the
        # LiDAR path is longer than the (scale-corrected) VIO path by more than lidar_guard_ex m, the LiDAR increment is
        # treated as failed for this step: the VIO carries it (W = 0) and the consistency statistics are not fed.
        self.lidar_guard_T, self.lidar_guard_ex, self.gbuf = lidar_guard_T, lidar_guard_ex, []
        self.guard_on, self.shist = False, []            # guard state; (t, s_vio) history for the roll-back
        # vio_scale_along: the scale correction (either kind) changes only the component of the VIO increment along the LiDAR's
        # direction of travel (monocular scale error is an error in how far one moved, not in which direction)
        self.vio_scale_along = vio_scale_along
        # gamma_min > 0: the VINS prior never drops below gamma_min of its unit information.  With gamma = 0 the weight
        # (c S + gamma I)^-1 c S is the identity in every direction with ANY LiDAR information, however small, so a truly
        # degenerate LiDAR direction would be trusted fully; with a small floor such directions (c lambda << gamma_min) go to
        # the VINS while well-constrained ones are unchanged (c lambda >> gamma_min gives w ~ 1).
        self.gamma_min = gamma_min
        # slow rotation-drift correction (complementary filter): tau_R = time constant in s (0 = off); the LiDAR-minus-VIO
        # rotation increment is low-passed with weight info_weight(S_RR, c_Rb) per eigen-direction
        self.tau_R, self.c_Rb, self.bias_axis = tau_R, c_Rb, bias_axis   # bias_axis "yaw": only about the gravity axis (VINS tilt is gravity-observable)
        self.bR = np.zeros(3)
        self.byaw = 0.0
        self.clip_R = clip_R          # bounded influence: per-step innovation clipped to +-clip_R rad (0 = off)
        self.t_prev = None
        # gap_T > 0: LiDAR-gap rule.  A scan interval longer than gap_T s means the LiDAR delivered nothing (sensor outage, dropped
        # packets).  The LiDAR front end dead-reckons through the gap and can re-enter with a pose that is wrong by tens or hundreds
        # of metres, and the VIO displacement over the gap would look like a VINS jump (more than jump_max per step).  For that one
        # step: the jump limits of the VIO are scaled by the gap (gap_vmax m/s, gap_wmax rad/s), the LiDAR increment is ignored
        # (W = 0, the VIO carries the step), no consistency window spans the gap (the trust earned before it is kept), the scale
        # and guard buffers restart, and if the VIO is also unusable the pose is held.  0 = off (the behaviour of G20, bit for bit).
        self.gap_T, self.gap_vmax, self.gap_wmax, self.t_last = gap_T, gap_vmax, gap_wmax, None
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

    def step(self, t, aft, vins=None, H=None, vo_fail=False, T3=None):
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
            self.t_last = t
            return self.Rf, self.pf, info

        dR_a, dt_a = rel_body(self.prev_a[0], self.prev_a[1], Ra, pa)
        vins_ok = vins is not None and not vo_fail
        jump = False
        is_gap = self.gap_T > 0 and self.t_last is not None and (t - self.t_last) > self.gap_T
        thr_t, thr_R = self.jump_max, self.rot_jump_max
        if is_gap:
            thr_t = max(thr_t, self.gap_vmax * (t - self.t_last))
            thr_R = max(thr_R, self.gap_wmax * (t - self.t_last))
        if vins_ok and self.prev_v is not None:
            dR_I, dt_I = rel_body(self.prev_v[0], self.prev_v[1], vins[0], vins[1])
            dR_v, dt_v = imu_to_lidar_increment(dR_I, dt_I, self.R_IL, self.t_IL)
            jump = np.linalg.norm(dt_v) > thr_t or np.linalg.norm(so3_log(dR_v)) > thr_R
        have_v = vins_ok and self.prev_v is not None and not jump
        lost = self.t_vins0 is not None and self.prev_v is not None and (not vins_ok or jump)
        info["dta"] = float(np.linalg.norm(dt_a))
        lidar_bad = False
        if is_gap:
            self.gbuf, self.guard_on, self.shist, self.sbuf = [], False, [], []
        if self.lidar_guard_T > 0 and self.vio_adapt is not None:
            if have_v and not is_gap:
                # raw VINS motion: the guard must not depend on a scale estimate that the failing LiDAR itself feeds
                self.gbuf.append((t, float(np.linalg.norm(dt_a)), float(np.linalg.norm(dt_v))))
                while self.gbuf and self.gbuf[0][0] <= t - self.lidar_guard_T:
                    self.gbuf.pop(0)
                ex = sum(x[1] for x in self.gbuf) - sum(x[2] for x in self.gbuf)
                info["guard_ex"] = ex if self.vio_adapt.trusted() else float("nan")
                lidar_bad = self.vio_adapt.trusted() and ex > self.lidar_guard_ex
                if lidar_bad and not self.guard_on and self.vio_scale_T > 0:
                    # first flagged step: the excess built up over the guard window, so the scale samples of that
                    # window are suspect -- drop them and return to the scale held just before it
                    t_cut = t - 2.0 * self.lidar_guard_T
                    self.sbuf = [x for x in self.sbuf if x[0] <= t_cut]
                    old = [sv for (ts, sv) in self.shist if ts <= t_cut]
                    self.s_vio = old[-1] if old else 1.0
                self.guard_on = lidar_bad
            elif lost:
                self.gbuf, self.guard_on, self.shist = [], False, []
        info["lidar_bad"] = int(lidar_bad)
        if self.vio_scale_T > 0:
            if have_v and not lidar_bad and not is_gap:
                if self.vio_scale_proj and H is not None:
                    Wp = info_weight(schur_blocks(H, self.hess_frame, self.prev_a[0])[1], self.c_t)
                    self.sbuf.append((t, float(np.linalg.norm(Wp @ dt_a)), float(np.linalg.norm(Wp @ dt_v))))
                elif not self.vio_scale_proj:
                    self.sbuf.append((t, float(np.linalg.norm(dt_a)), float(np.linalg.norm(dt_v))))
                while self.sbuf and self.sbuf[0][0] <= t - self.vio_scale_T:
                    self.sbuf.pop(0)
                la, lv = sum(x[1] for x in self.sbuf), sum(x[2] for x in self.sbuf)
                if la >= self.vio_scale_dmin and lv > 1e-6:
                    self.s_vio = la / lv
                _s = self.s_vio
                if self.vio_scale_along and np.linalg.norm(dt_a) > 1e-6:
                    _u = dt_a / np.linalg.norm(dt_a)
                    dt_v = dt_v + (_s - 1.0) * float(_u @ dt_v) * _u
                else:
                    dt_v = _s * dt_v
            elif have_v:
                dt_v = self.s_vio * dt_v          # LiDAR flagged: hold the last scale, do not feed the buffer
            elif lost:
                self.sbuf, self.s_vio = [], 1.0
        info["s_vio"] = self.s_vio
        if self.lidar_guard_T > 0:
            self.shist.append((t, self.s_vio))
            while self.shist and self.shist[0][0] < t - 4.0 * self.lidar_guard_T - 1.0:
                self.shist.pop(0)
        gam = 1.0
        if self.vio_adapt is not None:
            if is_gap:
                self.vio_adapt.restart_windows()      # trust earned before the gap is kept; no window spans the LiDAR gap
            elif have_v and not lidar_bad:
                kw = {}
                if getattr(self.vio_adapt, "proj", False):
                    # V2: per-step increments weighted by this step's LiDAR translation weight (both LiDAR channels), world frame
                    if H is not None and np.isfinite(np.asarray(H, float)).all():
                        _, S_tt_p, _, _ = schur_blocks(H, self.hess_frame, self.prev_a[0])
                        if self.t_cap and T3 is not None:
                            Wp = t_weight(self.t_mode, H, S_tt_p, T3, self.c_t, 1.0, self.hess_frame, self.prev_a[0])[0]
                        else:
                            Wp = info_weight(S_tt_p, self.c_t)
                        kw["inc"] = (self.prev_a[0] @ (Wp @ dt_a), self.prev_a[0] @ (Wp @ dt_v))
                self.vio_adapt.update(t, (Ra, pa), (np.asarray(vins[0], float), np.asarray(vins[1], float)), self.R_IL, self.t_IL, **kw)
            elif lost:
                self.vio_adapt.reset()
            gam = max(self.vio_adapt.gamma(), self.gamma_min)
            _chk = getattr(self.vio_adapt, "checks", [self.vio_adapt])
            info["vio_r_slow"] = _chk[0].r
            info["vio_r_fast"] = _chk[1].r if len(_chk) > 1 else float("nan")
            if self.vio_scale_seg and have_v:
                self.s_vio = self.vio_adapt.scale_local() if self.vio_scale_seg == "local" else self.vio_adapt.scale()
                if self.vio_scale_along and np.linalg.norm(dt_a) > 1e-6:
                    _u = dt_a / np.linalg.norm(dt_a)
                    dt_v = dt_v + (self.s_vio - 1.0) * float(_u @ dt_v) * _u
                else:
                    dt_v = self.s_vio * dt_v
                info["s_vio"] = self.s_vio
            elif self.vio_scale_seg and lost:
                self.s_vio = 1.0
        info["gamma"] = gam
        rot_gam, rot_bad = 1.0, False
        if self.rot_adapt is not None:
            if is_gap:
                self.rot_adapt.restart_windows()
            elif have_v:
                self.rot_adapt.update(t, Ra, vins[0], self.R_IL)
                rot_bad = self.rot_adapt.lidar_bad()
            elif lost:
                self.rot_adapt.reset()
            rot_gam = self.rot_adapt.gamma()
            info["rot_gamma"], info["rot_e2"], info["rot_e10"] = rot_gam, self.rot_adapt.e_fast, self.rot_adapt.e_slow

        if is_gap:
            info["gap"] = 1
            W_t = W_R = np.zeros((3, 3))
            if have_v:
                mode = "GAP"                              # the VIO carries the step over the gap
            else:
                mode = "GAP_HOLD"                         # neither sensor can be trusted over the gap: hold the pose
                dR_v, dt_v = I3, np.zeros(3)
                if lost:
                    self.t_vins0 = None
        elif not have_v:
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
                    W_R = I3.copy() if (self.switch_rot and self.w_mode == "switch_ss" and float(np.abs(W_t - I3).max()) < 1e-12) else np.zeros((3, 3))
                elif self.w_mode != "schur":
                    W_t = W_R = np.zeros((3, 3))
                elif ok and np.linalg.norm(dt_a) <= self.jump_max and not lidar_bad:
                    if self.t_cap and T3 is not None:
                        W_t, info["tcap_ratio"] = t_weight(self.t_mode, H, S_tt, T3, self.c_t, gam, self.hess_frame, self.prev_a[0])
                    else:
                        W_t = info_weight(S_tt, self.c_t, gam)
                    W_R = info_weight(S_RR, self.c_R, gam)
                    if self.rot_adapt is not None:
                        if rot_bad:
                            W_R = np.zeros((3, 3))
                        elif rot_gam < 0.5:
                            W_R = info_weight(S_RR, self.rot_c_fail, self.rot_gamma_min)
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
        self.t_last = t
        info["mode"] = mode
        info["bR"] = float(abs(self.byaw)) if self.bias_axis == "yaw" else float(np.linalg.norm(self.bR))
        return self.Rf, self.pf, info
