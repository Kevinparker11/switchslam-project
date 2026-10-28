"""structure_heading: structure-anchored heading (SAH) for the VIO-primary fusion node.

Final design (offline name "v7"): StructureHeadingV6 with bound_R=True. Numpy only (scipy used if present).
A LiDAR keyframe gives an axial histogram of the horizontal directions of its near-vertical planar surfaces,
levelled with the VIO gravity direction. The estimator's heading error is the shift that best aligns the WHOLE
pattern with a reference learned in the world frame (normalised circular correlation, +-15 deg). Self-disabling:
null-model structure test (random-direction 99.9 % quantile x 1.5), unique correlation peak, per-direction
agreement veto, chi-square gate, physical drift gate (3 sigma_meas + 0.1 deg/s since the last accepted update),
prior capped at (search/3)^2. Measurement noise is estimated online. No setting was fitted to a test sequence.
Development results: claude/Structure_Heading_Development_Results.md (project docs).
"""
import numpy as np
try:
    from scipy.spatial import cKDTree
except Exception:          # the ROS container may not have scipy
    cKDTree = None

NB = 360                     # bins over 180 deg -> 0.5 deg per bin
BIN = np.pi / NB


def knn_idx(P, k):
    """indices of the k nearest neighbours (incl. the point itself)"""
    if cKDTree is not None:
        return cKDTree(P).query(P, k=k)[1]
    P32 = P.astype(np.float32)
    sq = (P32 ** 2).sum(1)
    out = np.empty((len(P), k), np.int64)
    for a in range(0, len(P), 512):
        D = sq[a:a + 512, None] - 2.0 * P32[a:a + 512] @ P32.T + sq[None, :]
        part = np.argpartition(D, k - 1, axis=1)[:, :k]
        o = np.argsort(np.take_along_axis(D, part, 1), axis=1)
        out[a:a + 512] = np.take_along_axis(part, o, 1)
    return out


def planar_normals(P, k=12, pmin=0.5):
    idx = knn_idx(P, k)
    Q = P[idx] - P[idx].mean(1, keepdims=True)
    C = np.einsum("nki,nkj->nij", Q, Q) / k
    w, v = np.linalg.eigh(C)
    plan = (w[:, 1] - w[:, 0]) / np.maximum(w[:, 2], 1e-12)
    m = plan > pmin
    return v[m, :, 0], plan[m]


def scan_tensors(P, k=12, pmin=0.5, lmin=0.5):
    """the planar normals of planar_normals() (identical output) plus two orientation tensors of the same k-NN PCA:
    T = mean n n^T over planar points (the orientation tensor of the normals) and
    G = (sum_planar n n^T + sum_linear (I - d d^T)/2) / (n_planar + n_linear), the geometric tensor that also counts
    linear features (direction d: an edge constrains translation in the plane normal to d).  Both have trace 1.
    Returns (normals, planarity, T, G); T and G are None when there are no such points."""
    idx = knn_idx(P, k)
    Q = P[idx] - P[idx].mean(1, keepdims=True)
    C = np.einsum("nki,nkj->nij", Q, Q) / k
    w, v = np.linalg.eigh(C)
    plan = (w[:, 1] - w[:, 0]) / np.maximum(w[:, 2], 1e-12)
    lin = (w[:, 2] - w[:, 1]) / np.maximum(w[:, 2], 1e-12)
    m = plan > pmin
    nb = v[m, :, 0]
    ml = (lin > lmin) & ~m
    d = v[ml, :, 2]
    T = nb.T @ nb / len(nb) if len(nb) else None
    tot = len(nb) + len(d)
    G = None
    if tot:
        G = (nb.T @ nb + 0.5 * (len(d) * np.eye(3) - d.T @ d)) / tot
    return nb, plan[m], T, G


def scan_tensors_ext(P, k=12, pmin=0.5, lmin=0.5):
    """scan_tensors() plus two alternative orientation tensors from the same k-NN PCA (round 2 of the OT study):
    G3 = (sum_planar n n^T + sum_linear (I - d d^T)/2 + sum_scatter I/3) / n_all  (scattered points, neither planar nor
         linear, e.g. vegetation or clutter, count as isotropic translational support; trace 1);
    GS = translation Schur block of the scan's own geometric 6-DoF Hessian, H_g = sum J J^T with J = [p x n; n] per planar
         point and [p x e; e] / sqrt(2) for the two directions e normal to each line direction d (p = the point, LiDAR
         frame), divided by the number of planar + linear points (so tr(GS) <= tr(G) = 1: the rotation coupling of the
         raw geometry removed, as the solver's Schur complement does).
    GRF = G without scan-direction lines: a linear point whose direction d lies within 30 deg of the azimuthal sweep
         direction of a spinning LiDAR at that point (z_body x p) is the ring sampling of a surface, not an edge (ring
         spacing grows with range, so k-NN neighbourhoods on a plane are elongated along the ring) and is dropped.
    Returns (normals, planarity, T, G, G3, GS, GRF); tensors are None when there are no such points."""
    idx = knn_idx(P, k)
    Q = P[idx] - P[idx].mean(1, keepdims=True)
    C = np.einsum("nki,nkj->nij", Q, Q) / k
    w, v = np.linalg.eigh(C)
    plan = (w[:, 1] - w[:, 0]) / np.maximum(w[:, 2], 1e-12)
    lin = (w[:, 2] - w[:, 1]) / np.maximum(w[:, 2], 1e-12)
    m = plan > pmin
    nb = v[m, :, 0]
    ml = (lin > lmin) & ~m
    d = v[ml, :, 2]
    ms = ~m & ~ml
    T = nb.T @ nb / len(nb) if len(nb) else None
    tot = len(nb) + len(d)
    G = G3 = GS = GRF = None
    tng = np.c_[-P[:, 1], P[:, 0], np.zeros(len(P))]
    tng /= np.maximum(np.linalg.norm(tng, axis=1, keepdims=True), 1e-9)
    ring = np.abs((v[:, :, 2] * tng).sum(1)) > np.cos(np.radians(30.0))
    d_rf = v[ml & ~ring, :, 2]
    if len(nb) + len(d_rf):
        GRF = (nb.T @ nb + 0.5 * (len(d_rf) * np.eye(3) - d_rf.T @ d_rf)) / (len(nb) + len(d_rf))
    if tot:
        G = (nb.T @ nb + 0.5 * (len(d) * np.eye(3) - d.T @ d)) / tot
        G3 = (nb.T @ nb + 0.5 * (len(d) * np.eye(3) - d.T @ d) + ms.sum() / 3.0 * np.eye(3)) / (tot + ms.sum())
        Pp, Pl = P[m], P[ml]
        Jp = np.concatenate([np.cross(Pp, nb), nb], 1)                  # (np, 6)
        rows = [Jp]
        if len(d):
            a = np.where(np.abs(d[:, 0:1]) < 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]]))
            e1 = np.cross(d, a); e1 /= np.linalg.norm(e1, axis=1, keepdims=True)
            e2 = np.cross(d, e1)
            for e in (e1, e2):
                rows.append(np.concatenate([np.cross(Pl, e), e], 1) / np.sqrt(2.0))
        J = np.concatenate(rows, 0)
        Hg = J.T @ J
        Hrr, Hrt, Htt = Hg[:3, :3], Hg[:3, 3:], Hg[3:, 3:]
        Hrr = Hrr + 1e-9 * max(np.trace(Hrr), 1e-300) * np.eye(3)
        GS = (Htt - Hrt.T @ np.linalg.solve(Hrr, Hrt)) / tot
        GS = 0.5 * (GS + GS.T)
    return nb, plan[m], T, G, G3, GS, GRF


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



def make_sah():
    """the frozen configuration used in the study"""
    return StructureHeadingV6(bound_R=True)
