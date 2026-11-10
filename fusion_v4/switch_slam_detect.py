"""Degeneracy detection for the Switch-SLAM structure: Switch-SLAM's rule plus our R, T and additional-T channels.

The switching structure is not touched (switch_slam_core: LiDAR primary, VINS-Mono as the initial guess and as the remap
in the degenerate directions, status queue, Eqs. 13-16).  Only the question "is this scan degenerate, and in which
directions" is answered differently.  The answer is the union of:

  SW  Switch-SLAM's own rule on the coupled 6x6 Hessian (always on).
  R   rotation channel: the Schur complement S_RR = H_RR - H_Rt H_tt^-1 H_tR (rotation information with the
      translation already solved for), three eigenvalues, normalised to unit norm, each below [0.12, 0.27, 0.48].
  T   translation channel: S_tt = H_tt - H_tR H_RR^-1 H_Rt, same test.
  TT  additional T: S_tt is first combined with the orientation tensor T of the raw scan normals (fusion_core.t_combine,
      rule "min": along every eigen-direction of S_tt the information is min(solver, raw-scan support), the fail-safe rule of
      docs/results/ChannelT_Mini_Test_Protocol.md), then the same test.  TT replaces T when both are named.

Choices that are ours, not the paper's (docs/protocols/Switch_SLAM_With_Our_Detection_Protocol.md):
  D1  The paper's thresholds are applied to the three eigenvalues of each 3x3 block.  The paper's expectations (Eq. 11,
      e1 = 1/(2 sqrt 3) ...) are written for a unit-norm three-vector, which is what a 3x3 block gives.
  D2  The directions removed in the remap (Eq. 14) are the flagged eigenvectors of every channel that fired (the 6x6 ones
      as before, the 3x3 ones padded with zeros in the other block), orthonormalised as a set.
  D3  The interpolation weight of Eq. 13 uses the smallest normalised eigenvalue over the channels that are on.
"""
import numpy as np

import fusion_core as fc
import switch_slam_core as sw

CHANNELS = ("R", "T", "TT")


def parse_channels(s):
    ch = [c.strip().upper() for c in str(s).split(",") if c.strip()]
    for c in ch:
        if c not in CHANNELS:
            raise ValueError("unknown channel %s (use R, T, TT)" % c)
    return tuple(ch)


def _block_test(S, lt):
    """eigen test of a symmetric 3x3: returns lam_bar (ascending, unit norm), flags, eigenvectors"""
    S = 0.5 * (np.asarray(S, float) + np.asarray(S, float).T)
    lam, U = np.linalg.eigh(S)
    lam = np.clip(lam, 0.0, None)
    n = float(np.linalg.norm(lam))
    if n <= 0.0:
        return np.zeros(3), np.ones(3, bool), U
    lb = lam / n
    return lb, lb < np.asarray(lt), U


def schur_pair(H, eps=1e-9):
    """(S_RR, S_tt) of the Ceres-unit Hessian in (rad, m), regularised so that a rank-deficient block does not raise"""
    Hr = fc.D_RAD @ (0.5 * (np.asarray(H, float).reshape(6, 6) + np.asarray(H, float).reshape(6, 6).T)) @ fc.D_RAD
    Hrr, Hrt, Htr, Htt = Hr[:3, :3], Hr[:3, 3:], Hr[3:, :3], Hr[3:, 3:]
    sc = max(float(np.trace(Hr)) / 6.0, 1e-12)
    I3 = np.eye(3)
    S_RR = Hrr - Hrt @ np.linalg.solve(Htt + eps * sc * I3, Htr)
    S_tt = Htt - Htr @ np.linalg.solve(Hrr + eps * sc * I3, Hrt)
    return 0.5 * (S_RR + S_RR.T), 0.5 * (S_tt + S_tt.T)


class OurDetector:
    """callable: detector(H, T) -> dict with the keys of switch_slam_core.eig_degeneracy plus 'remove' (6 x r, orthonormal,
    in the frame of H) and 'chan' (which channel fired).  T = orientation tensor (3x3, trace 1) in the frame of H, or None."""

    def __init__(self, channels=("R", "T", "TT"), lt=sw.LT_PUBLISHED):
        self.channels = tuple(channels)
        self.lt = np.asarray(lt, float)

    def __call__(self, H, T=None):
        base = sw.eig_degeneracy(H, self.lt)
        cols = [base["U"][:, i] for i in range(3) if base["flags"][i]]
        chan = dict(SW=bool(base["degenerate"]), R=False, T=False, TT=False, T_missing=False)
        lam_min = float(base["lam_bar"][0])
        S_RR, S_tt = schur_pair(H)
        if "R" in self.channels:
            lb, fl, U = _block_test(S_RR, self.lt)
            chan["R"] = bool(fl.any())
            lam_min = min(lam_min, float(lb[0]))
            for i in range(3):
                if fl[i]:
                    cols.append(np.concatenate([U[:, i], np.zeros(3)]))
        use_tt = "TT" in self.channels
        if use_tt or "T" in self.channels:
            S = S_tt
            if use_tt:
                if T is None:
                    chan["T_missing"] = True                      # no tensor for this scan: plain Schur T for this scan
                else:
                    S, _ = fc.t_combine("min", H, S_tt, T)
            lb, fl, U = _block_test(S, self.lt)
            chan["TT" if use_tt and T is not None else "T"] = bool(fl.any())
            lam_min = min(lam_min, float(lb[0]))
            for i in range(3):
                if fl[i]:
                    cols.append(np.concatenate([np.zeros(3), U[:, i]]))
        out = dict(base)
        lb6 = np.array(base["lam_bar"], float)
        lb6[0] = lam_min
        out["lam_bar"] = lb6
        out["degenerate"] = bool(base["degenerate"] or any(chan[c] for c in ("R", "T", "TT")))
        if cols:
            Q, s, _ = np.linalg.svd(np.stack(cols, 1), full_matrices=False)
            out["remove"] = Q[:, s > 1e-6]
        else:
            out["remove"] = np.zeros((6, 0))
        out["chan"] = chan
        return out


class OwnDetector:
    """Our detection only, no Switch-SLAM thresholds.  R and T are judged separately, each with the threshold the thesis already uses.

      R   rotation Schur block S_RR: degenerate where lambda_max / lambda_i > KAPPA_TH (15.7, the frozen kappa gate of the fusion,
          fusion_core.KappaGate mode "fixed"); the flagged eigen-directions are the weak ones.
      T   translation Schur block S_tt: per-direction information weight w_i = c lambda_i / (c lambda_i + 1) with the frozen
          c_T = 0.03 (F8 to F29) against a unit VIO information, as fusion_core.info_weight; degenerate where w_i < 0.5, that is where
          the LiDAR carries less information than the VINS-Mono step (c lambda_i < 1).
      TT  additional T: the same S_tt first combined with the orientation tensor of the raw scan normals (fusion_core.t_combine,
          rule "min" by default), then the same per-direction test.  TT replaces T when named; with no tensor for a scan, plain T.

    Degenerate = any channel fires.  The removed directions are the flagged eigenvectors of the channels that fired (orthonormalised).
    Eq. 13 weight (guess blend): w = min(1, 2 min_i w_i, KAPPA_TH / kappa_R); it equals 1 at either threshold and falls to 0 as the
    information vanishes (our choice, D3: the paper's sqrt(3) lambda_bar_1 belongs to its normalised-eigenvalue rule)."""

    def __init__(self, channels=("R", "T", "TT"), c_t=0.03, gamma=1.0, kth_r=15.7, tt_rule="min"):
        self.channels = tuple(channels)
        self.c_t, self.gamma, self.kth_r, self.tt_rule = float(c_t), float(gamma), float(kth_r), tt_rule

    def __call__(self, H, T=None):
        S_RR, S_tt = schur_pair(H)
        cols = []
        chan = dict(SW=False, R=False, T=False, TT=False, T_missing=False)
        w_blend = 1.0
        kR = np.nan
        if "R" in self.channels:
            lam, U = np.linalg.eigh(S_RR)
            lam = np.clip(lam, 1e-12, None)
            kR = float(lam[-1] / lam[0])
            fl = (lam[-1] / lam) > self.kth_r
            chan["R"] = bool(fl.any())
            w_blend = min(w_blend, self.kth_r / kR)
            for i in range(3):
                if fl[i]:
                    cols.append(np.concatenate([U[:, i], np.zeros(3)]))
        use_tt = "TT" in self.channels
        if use_tt or "T" in self.channels:
            S = S_tt
            if use_tt:
                if T is None:
                    chan["T_missing"] = True
                else:
                    S, _ = fc.t_combine(self.tt_rule, H, S_tt, T)
            lam, U = np.linalg.eigh(0.5 * (S + S.T))
            lam = np.clip(lam, 0.0, None)
            w = self.c_t * lam / (self.c_t * lam + self.gamma)
            fl = w < 0.5
            chan["TT" if use_tt and T is not None else "T"] = bool(fl.any())
            w_blend = min(w_blend, 2.0 * float(w.min()))
            for i in range(3):
                if fl[i]:
                    cols.append(np.concatenate([np.zeros(3), U[:, i]]))
        out = dict(lam=np.full(6, np.nan), U=np.eye(6), lam_bar=np.array([np.nan, kR, np.nan]),
                   flags=np.zeros(3, bool), w_blend=float(min(1.0, w_blend)))
        out["degenerate"] = bool(chan["R"] or chan["T"] or chan["TT"])
        if cols:
            Q, s, _ = np.linalg.svd(np.stack(cols, 1), full_matrices=False)
            out["remove"] = Q[:, s > 1e-6]
        else:
            out["remove"] = np.zeros((6, 0))
        out["chan"] = chan
        return out
