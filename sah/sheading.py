"""Structure-anchored heading (SAH): a general, self-disabling yaw correction for a VIO-primary estimator.

No Manhattan / 90-degree assumption. Each LiDAR keyframe gives a histogram of the horizontal directions of its
vertical planar surfaces (walls, pillars, shelves...), levelled with the VIO gravity direction. A reference
direction histogram is built in the world frame from accepted keyframes (a "map of directions"). The heading
error of the estimator is the shift that best aligns the keyframe histogram with the reference (1-DoF
registration on the circle, axial: period 180 deg). Its variance comes from the alignment curve itself, so in
scenes without persistent vertical structure (caves, open fields, clutter) the measurement is flat, ambiguous or
inconsistent and is rejected or gets ~zero weight: the estimator then falls back to plain VIO yaw.

Fusion: 1-D Kalman filter on the heading error with process noise q (VIO yaw random walk) and a chi-square gate.
"""
import numpy as np
from scipy.spatial import cKDTree

NB = 360                     # bins over 180 deg -> 0.5 deg per bin
BIN = np.pi / NB


def planar_normals(P, k=12, pmin=0.5):
    tr = cKDTree(P)
    _, idx = tr.query(P, k=k)
    Q = P[idx] - P[idx].mean(1, keepdims=True)
    C = np.einsum("nki,nkj->nij", Q, Q) / k
    w, v = np.linalg.eigh(C)
    plan = (w[:, 1] - w[:, 0]) / np.maximum(w[:, 2], 1e-12)
    m = plan > pmin
    return v[m, :, 0], plan[m]


def level_rotation(u):
    """rotation taking the unit vector u (estimated world up in the estimator's world frame) to +z"""
    z = np.array([0, 0, 1.0])
    a = np.cross(u, z)
    s, c = np.linalg.norm(a), float(u @ z)
    if s < 1e-12:
        return np.eye(3)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]) / s
    th = np.arctan2(s, c)
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def direction_hist(n_world_levelled, w=None, max_tilt=0.25, smooth_bins=4):
    """axial histogram of horizontal normal directions of near-vertical planes; returns (hist, n_used)"""
    n = n_world_levelled
    m = np.abs(n[:, 2]) < max_tilt
    if m.sum() == 0:
        return np.zeros(NB), 0
    th = np.mod(np.arctan2(n[m, 1], n[m, 0]), np.pi)
    ww = np.ones(m.sum()) if w is None else w[m]
    h = np.bincount(np.minimum((th / BIN).astype(int), NB - 1), weights=ww, minlength=NB).astype(float)
    if smooth_bins > 0:
        x = np.arange(-3 * smooth_bins, 3 * smooth_bins + 1)
        g = np.exp(-0.5 * (x / smooth_bins) ** 2)
        h = np.real(np.fft.ifft(np.fft.fft(h) * np.fft.fft(np.roll(np.pad(g, (0, NB - len(g))), -3 * smooth_bins))))
    return np.maximum(h, 0), int(m.sum())


# null model: isotropic random normals. 99.9 % quantile of peak/mean of the smoothed histogram vs number of
# near-vertical points (Monte Carlo, 2000 draws each; see null_test.py). Structure must beat FACTOR x this.
_NULL_N = np.array([50, 100, 200, 400, 800, 1600, 3200], float)
_NULL_Q = np.array([5.17, 3.75, 2.82, 2.22, 1.82, 1.61, 1.37])
NULL_FACTOR = 1.5


def structured(h, npts):
    """True if the direction histogram is far more concentrated than random directions with the same count"""
    if npts < _NULL_N[0] or h.sum() <= 0:
        return False
    thr = NULL_FACTOR * float(np.interp(np.log(npts), np.log(_NULL_N), _NULL_Q))
    return h.max() / h.mean() >= thr


def align(h, ref, search_deg=15.0):
    """normalised circular cross-correlation over +-search; returns (shift rad, sigma rad, quality info) or None"""
    a = h - h.mean()
    b = ref - ref.mean()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return None
    cc = np.real(np.fft.ifft(np.fft.fft(a) * np.conj(np.fft.fft(b)))) / (na * nb)   # cc[s]: h shifted by -s matches ref
    S = int(round(np.radians(search_deg) / BIN))
    shifts = np.r_[np.arange(0, S + 1), np.arange(-S, 0)]
    vals = cc[shifts % NB]
    i = int(np.argmax(vals))
    s0, c0 = shifts[i], vals[i]
    # sub-bin parabola
    cm, cp = cc[(s0 - 1) % NB], cc[(s0 + 1) % NB]
    den = cm - 2 * c0 + cp
    off = 0.5 * (cm - cp) / den if den < 0 else 0.0
    shift = (s0 + off) * BIN
    # ambiguity: best value outside +-3 deg of the peak inside the search window (and the global best outside)
    far = np.abs(shifts - s0) > int(round(np.radians(3) / BIN))
    second = vals[far].max() if far.any() else -1.0
    # curvature -> sigma (Laplace approximation on a correlation "log-likelihood" scaled by the evidence)
    curv = max(-den, 1e-9) / BIN ** 2
    return dict(shift=shift, peak=c0, second=second, curv=curv)


class StructureHeading:
    """keyframe-rate heading corrector.
    Process model (physical, not tuned): VIO yaw error grows with time (gyro bias residual, q_t rad^2/s) and with
    the angle turned (gyro scale / misalignment, s_turn rad per rad). Measurement noise R is estimated online from
    the innovations (robust covariance matching), so no per-dataset noise setting is needed. Gates: null-model
    structure test, unique alignment peak, chi-square on the innovation, physical drift-rate bound."""

    def __init__(self, q_t=np.radians(0.05) ** 2, s_turn=0.02, R0=np.radians(3.0) ** 2, R_floor=np.radians(0.5) ** 2,
                 R_alpha=0.05, min_peak=0.5, min_margin=0.15, min_pts=150, gate_chi2=9.0, search_deg=15.0,
                 init_kf=5, rate_max=np.radians(0.1), fixed_R=None, fixed_q=None, P_max=None, bound_R=False):
        self.q_t, self.s_turn, self.R, self.R_floor, self.R_alpha = q_t, s_turn, R0, R_floor, R_alpha
        self.fixed_R, self.fixed_q = fixed_R, fixed_q
        self.P_max = P_max
        self.bound_R = bound_R      # True: drift gate uses measurement noise + physical drift only (not the prior)
        self.min_peak, self.min_margin, self.min_pts = min_peak, min_margin, min_pts
        self.gate, self.search, self.init_kf, self.rate_max = gate_chi2, search_deg, init_kf, rate_max
        self.ref, self.n_init, self.P, self.t_last, self.t_acc = None, 0, None, None, None
        self.turn = 0.0
        self.stats = dict(acc=0, rej_struct=0, rej_gate=0, init=0)

    def add_turn(self, dpsi):
        self.turn += abs(dpsi)

    def _measure(self, h, npts):
        if npts < self.min_pts or self.ref is None or not structured(h, npts):
            return None
        r = align(h, self.ref, self.search)
        if r is None or r["peak"] < self.min_peak or r["peak"] - r["second"] < self.min_margin:
            return None
        return r["shift"]

    def update(self, t, h, npts):
        if self.ref is None or self.n_init < self.init_kf:
            if npts >= self.min_pts and structured(h, npts):
                hn = h / h.sum()
                if self.ref is not None:
                    r = align(hn, self.ref, self.search)
                    if r is None or r["peak"] < self.min_peak or abs(r["shift"]) > np.radians(3.0):
                        self.ref, self.n_init = None, 0
                        self.stats["init_reset"] = self.stats.get("init_reset", 0) + 1
                        return 0.0
                self.ref = hn if self.ref is None else self.ref + hn
                self.n_init += 1
                self.stats["init"] += 1
                self.t_last, self.turn = t, 0.0
            return 0.0
        dt = max(0.0, t - self.t_last)
        q = self.fixed_q * dt if self.fixed_q is not None else self.q_t * dt + (self.s_turn * self.turn) ** 2
        P = (np.radians(1.0) ** 2 if self.P is None else self.P) + q
        if self.P_max is not None:
            P = min(P, self.P_max)
        self.t_last, self.turn = t, 0.0
        z = self._measure(h, npts)
        if z is None:
            self.P = P
            self.stats["rej_struct"] += 1
            return 0.0
        R = self.fixed_R if self.fixed_R is not None else self.R
        S = P + R
        if self.bound_R and self.t_acc is not None:
            bound = 3.0 * np.sqrt(R) + self.rate_max * max(0.0, t - self.t_acc)
        else:
            bound = 3.0 * np.sqrt(S) + self.rate_max * (0.0 if self.t_acc is None else max(0.0, t - self.t_acc))
        if z * z / S > self.gate or abs(z) > bound:
            self.P = P
            self.stats["rej_gate"] += 1
            return 0.0
        # robust covariance matching for R (Huber-clipped innovation)
        nu2 = min(z * z, 4.0 * S)
        self.R = max(self.R_floor, (1 - self.R_alpha) * self.R + self.R_alpha * max(nu2 - P, 0.0))
        K = P / S
        self.P = (1 - K) * P
        self.stats["acc"] += 1
        self.t_acc = t
        corr = K * z
        hc = np.roll(h, -int(round(corr / BIN)))
        if hc.sum() > 0:
            self.ref = self.ref + hc / hc.sum()
        return corr


# ---------------- v3: likelihood alignment + per-mode consistency ----------------
EPS_U = 0.1 / NB          # floor density: 10 % of uniform


def modes(h, rel=0.2, min_sep_deg=10.0):
    """local maxima of the axial histogram above rel*max, at least min_sep apart (circular)"""
    if h.max() <= 0:
        return []
    l, r = np.roll(h, 1), np.roll(h, -1)
    cand = np.where((h >= l) & (h > r) & (h >= rel * h.max()))[0]
    cand = cand[np.argsort(-h[cand])]
    sep = int(round(np.radians(min_sep_deg) / BIN))
    out = []
    for c in cand:
        if all(min(abs(c - o), NB - abs(c - o)) >= sep for o in out):
            out.append(int(c))
    return out


def loglik_curve(h, ref):
    """L[s] = sum_theta h(theta+s) log ref_n(theta) / sum h  (mean log-density of the keyframe directions under the
    reference, after shifting the keyframe by -s); axial, circular"""
    rn = ref / ref.sum()
    lr = np.log(rn + EPS_U)
    return np.real(np.fft.ifft(np.fft.fft(h) * np.conj(np.fft.fft(lr)))) / h.sum()


def align_ll(h, ref, search_deg=15.0, uniq=0.2):
    if h.sum() <= 0 or ref is None or ref.sum() <= 0:
        return None
    L = loglik_curve(h, ref)
    S = int(round(np.radians(search_deg) / BIN))
    shifts = np.r_[np.arange(0, S + 1), np.arange(-S, 0)]
    vals = L[shifts % NB]
    i = int(np.argmax(vals))
    s0, c0 = shifts[i], vals[i]
    cm, cp = L[(s0 - 1) % NB], L[(s0 + 1) % NB]
    den = cm - 2 * c0 + cp
    off = 0.5 * (cm - cp) / den if den < 0 else 0.0
    far = np.abs(shifts - s0) > int(round(np.radians(3) / BIN))
    second = vals[far].max() if far.any() else vals.min()
    rng_ = c0 - vals.min()
    gain = c0 - np.log(1.0 / NB + EPS_U)          # log likelihood ratio per point vs a uniform reference
    return dict(shift=(s0 + off) * BIN, gain=gain, unique=(c0 - second) / max(rng_, 1e-12), at_edge=abs(s0) >= S)


class StructureHeadingV3(StructureHeading):
    """as StructureHeading, but (a) the alignment is a likelihood of the keyframe directions under the learned
    direction distribution, so a keyframe that sees only some of the known directions is not penalised; (b) every
    dominant direction (mode) of the keyframe is aligned separately and the modes must agree: a moving or false
    planar object that disagrees with the walls makes the measurement inconsistent and it is rejected."""

    def __init__(self, min_gain=np.log(2.0), min_unique=0.2, mode_halfwidth_deg=8.0, mode_agree_deg=2.0, **kw):
        super().__init__(**kw)
        self.min_gain, self.min_unique = min_gain, min_unique
        self.mw = int(round(np.radians(mode_halfwidth_deg) / BIN))
        self.agree = np.radians(mode_agree_deg)

    def _measure(self, h, npts):
        if npts < self.min_pts or self.ref is None or not structured(h, npts):
            return None
        r = align_ll(h, self.ref, self.search)
        if r is None or r["gain"] < self.min_gain or r["unique"] < self.min_unique or r["at_edge"]:
            self.stats["rej_align"] = self.stats.get("rej_align", 0) + 1
            return None
        ms = modes(h)
        if len(ms) >= 2:
            sh_, w_ = [], []
            for m in ms:
                idx = (np.arange(m - self.mw, m + self.mw + 1)) % NB
                hm = np.zeros(NB); hm[idx] = h[idx]
                rm = align_ll(hm, self.ref, self.search)
                if rm is None or rm["gain"] < self.min_gain or rm["at_edge"]:
                    continue
                sh_.append(rm["shift"]); w_.append(hm.sum())
            if len(sh_) >= 2:
                sh_, w_ = np.array(sh_), np.array(w_) / np.sum(w_)
                if np.max(np.abs(sh_ - r["shift"])[w_ >= 0.15], initial=0.0) > self.agree:
                    self.stats["rej_modes"] = self.stats.get("rej_modes", 0) + 1
                    return None
        return r["shift"]


# ---------------- v4: per-mode local correlation, mode agreement, bounded prior ----------------
class StructureHeadingV4(StructureHeading):
    """Each dominant direction (mode) of the keyframe is aligned locally with the reference; directions not yet in
    the reference are skipped (learned later); when two or more directions are usable they must agree, otherwise
    the keyframe is rejected (a moving or false planar object disagrees with the walls). The prior variance is
    capped so that +-3 sigma never exceeds the search window: after a long gap the filter does not accept any peak
    in the window at full gain."""

    def __init__(self, mode_halfwidth_deg=8.0, mode_agree_deg=2.0, min_mode_w=0.15, **kw):
        kw.setdefault("P_max", (np.radians(kw.get("search_deg", 15.0)) / 3.0) ** 2)
        super().__init__(**kw)
        self.mw = int(round(np.radians(mode_halfwidth_deg) / BIN))
        self.S = int(round(np.radians(self.search) / BIN))
        self.agree, self.min_mode_w = np.radians(mode_agree_deg), min_mode_w

    def _mode_shift(self, h, m):
        idx = np.arange(m - self.mw, m + self.mw + 1) % NB
        a = h[idx] - h[idx].mean()
        if np.linalg.norm(a) < 1e-12:
            return None
        vals = []
        for s_ in range(-self.S, self.S + 1):
            b = self.ref[(idx - s_) % NB]          # keyframe direction theta matches reference theta - s
            b = b - b.mean()
            nb = np.linalg.norm(b)
            vals.append(-1.0 if nb < 1e-12 else float(a @ b) / (np.linalg.norm(a) * nb))
        vals = np.array(vals)
        i = int(np.argmax(vals))
        if i == 0 or i == len(vals) - 1:
            return None
        c0 = vals[i]
        far = np.abs(np.arange(len(vals)) - i) > int(round(np.radians(3) / BIN))
        second = vals[far].max() if far.any() else -1.0
        if c0 < self.min_peak or c0 - second < self.min_margin:
            return None
        den = vals[i - 1] - 2 * c0 + vals[i + 1]
        off = 0.5 * (vals[i - 1] - vals[i + 1]) / den if den < 0 else 0.0
        return (i - self.S + off) * BIN

    def _measure(self, h, npts):
        if npts < self.min_pts or self.ref is None or not structured(h, npts):
            return None
        ms = modes(h)
        tot = sum(h[(np.arange(m - self.mw, m + self.mw + 1)) % NB].sum() for m in ms) or 1.0
        rmax = self.ref.max()
        sh_, w_ = [], []
        for m in ms:
            win = np.arange(m - self.mw - self.S, m + self.mw + self.S + 1) % NB
            if self.ref[win].max() < 0.2 * rmax:      # direction not (yet) in the reference
                continue
            s_ = self._mode_shift(h, m)
            w = h[(np.arange(m - self.mw, m + self.mw + 1)) % NB].sum() / tot
            if s_ is not None and w >= self.min_mode_w:
                sh_.append(s_); w_.append(w)
        if not sh_:
            self.stats["rej_align"] = self.stats.get("rej_align", 0) + 1
            return None
        sh_, w_ = np.array(sh_), np.array(w_)
        if len(sh_) >= 2 and np.ptp(sh_) > self.agree:
            self.stats["rej_modes"] = self.stats.get("rej_modes", 0) + 1
            return None
        return float(np.sum(sh_ * w_) / np.sum(w_))


# ---------------- v5: 1-D EKF "direction-landmark" SLAM ----------------
def mode_stats(n_levelled, w, max_tilt=0.25, halfwidth=np.radians(8.0), k_nb=12, sigma_floor=np.radians(0.5),
               rel=0.2, min_frac=0.1):
    """dominant horizontal directions of near-vertical planar points: list of (theta in [0,pi), sigma, weight).
    sigma = spread / sqrt(effective count); normals from k_nb neighbours are correlated, so n_eff = n / k_nb."""
    m = np.abs(n_levelled[:, 2]) < max_tilt
    if m.sum() < 30:
        return [], 0, np.zeros(NB)
    th = np.mod(np.arctan2(n_levelled[m, 1], n_levelled[m, 0]), np.pi)
    ww = np.ones(m.sum()) if w is None else w[m]
    h, npts = direction_hist(n_levelled, w, max_tilt)
    out = []
    for c in modes(h, rel=rel):
        c_ang = (c + 0.5) * BIN
        d = np.mod(th - c_ang + np.pi / 2, np.pi) - np.pi / 2          # axial difference
        sel = np.abs(d) < halfwidth
        if ww[sel].sum() < min_frac * ww.sum():
            continue
        mu = np.sum(ww[sel] * d[sel]) / ww[sel].sum()
        sd = np.sqrt(np.sum(ww[sel] * (d[sel] - mu) ** 2) / ww[sel].sum())
        neff = max(sel.sum() / k_nb, 1.0)
        out.append((float(np.mod(c_ang + mu, np.pi)), float(max(sigma_floor, sd / np.sqrt(neff))), float(ww[sel].sum() / ww.sum())))
    return out, npts, h


def adiff(a, b):
    return float(np.mod(a - b + np.pi / 2, np.pi) - np.pi / 2)


class DirectionSLAM:
    """state: heading error psi of the estimator and world directions d_j of vertical structure (axial angles).
    Every observed dominant direction theta_k (estimator frame) gives theta_k = d_j + psi + noise.
    - association by Mahalanobis distance (chi2 1-dof 99 %: 6.63); ambiguous (2 candidates) -> ignored;
      far from every landmark (> chi2 99.9 % 10.83) -> new landmark initialised from the current heading, so it
      carries the heading uncertainty and cannot pull the heading until it is re-observed after the heading has changed.
    - all associated directions of one keyframe are updated jointly; the stacked NIS must pass chi2(m, 99.9 %), so a
      moving or false plane that disagrees with the walls rejects the keyframe.
    - after each update the heading correction is applied to the estimator (error-state reset psi -> 0).
    - landmarks observed fewer than 3 times within 60 s of creation are dropped (transient objects).
    Constants are sensor/physics models, not fitted: VIO yaw random walk q_t, normal-estimate floor 0.5 deg."""

    CHI1_ASSOC, CHI1_NEW = 6.63, 10.83
    CHI_M = {1: 10.83, 2: 13.82, 3: 16.27, 4: 18.47, 5: 20.52}

    def __init__(self, q_t=np.radians(0.1) ** 2, P0=np.radians(0.5) ** 2, max_lm=30, search=np.radians(15.0), min_pts=150):
        self.q_t, self.max_lm, self.search, self.min_pts = q_t, max_lm, search, min_pts
        self.d = np.zeros(0)                 # landmark angles
        self.P = np.array([[P0]])            # covariance of [psi, d_1..d_n]
        self.nobs, self.tnew = [], []
        self.t_last = None
        self.stats = dict(acc=0, rej_struct=0, rej_nis=0, new=0, pruned=0, ambiguous=0, kf=0)

    def add_turn(self, dpsi):
        pass

    def _add_landmark(self, theta, sig, t):
        n = len(self.d)
        P = self.P
        Pn = np.zeros((n + 2, n + 2))
        Pn[:n + 1, :n + 1] = P
        # d_new = theta - psi  ->  var = P_psipsi + sig^2, cov(d_new, x) = -P[0, :]
        Pn[n + 1, :n + 1] = -P[0, :]
        Pn[:n + 1, n + 1] = -P[:, 0]
        Pn[n + 1, n + 1] = P[0, 0] + sig ** 2
        self.P = Pn
        self.d = np.r_[self.d, theta]
        self.nobs.append(1)
        self.tnew.append(t)
        self.stats["new"] += 1

    def _prune(self, t):
        keep = [i for i in range(len(self.d)) if not (self.nobs[i] < 3 and t - self.tnew[i] > 60.0)]
        if len(keep) < len(self.d):
            self.stats["pruned"] += len(self.d) - len(keep)
            idx = [0] + [i + 1 for i in keep]
            self.P = self.P[np.ix_(idx, idx)]
            self.d = self.d[keep]
            self.nobs = [self.nobs[i] for i in keep]
            self.tnew = [self.tnew[i] for i in keep]

    def update_modes(self, t, obs, npts, h):
        """obs: list of (theta, sigma, weight) in the estimator's levelled world frame. returns heading correction"""
        self.stats["kf"] += 1
        if self.t_last is not None:
            self.P[0, 0] += self.q_t * max(0.0, t - self.t_last)
        self.t_last = t
        if npts < self.min_pts or not obs or not structured(h, npts):
            self.stats["rej_struct"] += 1
            return 0.0
        self._prune(t)
        assoc, new = [], []
        for th, sg, w in obs:
            if len(self.d) == 0:
                new.append((th, sg)); continue
            inn = np.array([adiff(th, dj) for dj in self.d])
            var = self.P[0, 0] + np.diag(self.P)[1:] + 2 * self.P[0, 1:] + sg ** 2   # H = [1, ..., 1 at j]
            m2 = inn ** 2 / var
            near = np.where((m2 < self.CHI1_ASSOC) & (np.abs(inn) < self.search))[0]
            if len(near) == 1:
                assoc.append((int(near[0]), inn[near[0]], sg))
            elif len(near) > 1:
                self.stats["ambiguous"] += 1
            elif m2.min() > self.CHI1_NEW:
                new.append((th, sg))
        corr = 0.0
        if assoc:
            n = len(self.d)
            m = len(assoc)
            H = np.zeros((m, n + 1))
            z = np.zeros(m)
            R = np.zeros((m, m))
            for r, (j, inn, sg) in enumerate(assoc):
                H[r, 0] = 1.0
                H[r, j + 1] = 1.0
                z[r] = inn
                R[r, r] = sg ** 2
            S = H @ self.P @ H.T + R
            nis = float(z @ np.linalg.solve(S, z))
            if nis > self.CHI_M.get(m, 20.52 + 2 * (m - 5)):
                self.stats["rej_nis"] += 1
                return 0.0
            K = self.P @ H.T @ np.linalg.inv(S)
            dx = K @ z
            I_KH = np.eye(n + 1) - K @ H
            self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T          # Joseph form
            self.d = np.mod(self.d + dx[1:], np.pi)
            corr = float(dx[0])
            for j, _, _ in assoc:
                self.nobs[j] += 1
            self.stats["acc"] += 1
        # new landmarks after the correction: theta measured with the old heading -> subtract the correction
        for th, sg in new:
            if len(self.d) < self.max_lm:
                self._add_landmark(np.mod(th - corr, np.pi), sg, t)
        return corr


# ---------------- v6: global-pattern measurement (v1) + mode-agreement veto + bounded prior ----------------
class StructureHeadingV6(StructureHeadingV4):
    """measurement = shift of the WHOLE direction pattern of the keyframe against the reference (as v1): it only
    passes when the keyframe shows the same set of directions as the reference, i.e. when the platform sees the same
    structure again (revisit-type anchoring). A keyframe in a part of the building with other wall angles fails the
    correlation and is ignored instead of being snapped to the nearest known direction (the v4 failure on Corridor02).
    The per-direction alignment of v4 is kept only as a veto: if two dominant directions imply different shifts
    (moving or false plane), the keyframe is rejected. Prior variance capped (search window = 3 sigma)."""

    def _measure(self, h, npts):
        z = StructureHeading._measure(self, h, npts)
        if z is None:
            return None
        ms = modes(h)
        tot = sum(h[(np.arange(m - self.mw, m + self.mw + 1)) % NB].sum() for m in ms) or 1.0
        rmax = self.ref.max()
        sh_ = []
        for m in ms:
            w = h[(np.arange(m - self.mw, m + self.mw + 1)) % NB].sum() / tot
            win = np.arange(m - self.mw - self.S, m + self.mw + self.S + 1) % NB
            if w < self.min_mode_w or self.ref[win].max() < 0.2 * rmax:
                continue
            s_ = self._mode_shift(h, m)
            if s_ is None:
                self.stats["rej_modes"] = self.stats.get("rej_modes", 0) + 1
                return None
            sh_.append(s_)
        if len(sh_) >= 2 and (np.ptp(sh_) > self.agree or np.max(np.abs(np.array(sh_) - z)) > self.agree):
            self.stats["rej_modes"] = self.stats.get("rej_modes", 0) + 1
            return None
        return z
