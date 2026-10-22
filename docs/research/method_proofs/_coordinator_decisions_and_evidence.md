# Coordinator synthesis: final decisions, derivations, and numerical evidence

This file is NOT a literature note. It is the coordinator's decision for every weak
point in the thesis, built from the five literature notes in this folder plus the
coordinator's own numerical verification:
- script:  /mnt/user-data/outputs/verify_final_methods.py
- output:  /mnt/user-data/outputs/verify_final_methods_output.txt   (read it; all numbers below come from it)
The project's prior audit (36 items, Section 12 of the project methodology doc) is
summarized at the end of this file.

Everything numerical in the verification is SYNTHETIC (Python simulation of
point-to-plane ICP on simple planar scenes, 5 seeds). It supports the derivations;
it is not real-sensor validation. Say so in the report.

---------------------------------------------------------------------------------
## System facts (verified from code earlier in this project)
- A-LOAM: point-to-plane/line, Ceres, unit residual weights; Hessian H_l = J^T J,
  6x6, ordering [rotation, translation]. Published on /laser_hessian.
- Switching node (switching_node_schurbingham.py):
  * Channel R: Schur blocks S_RR, S_tt; L2-normalized eigenvalues vs Switch-SLAM
    semicircle threshold [0.12,0.27,0.48].
  * Channel T: PCA normals (k=12, <=400 pts) from A-LOAM planar cloud,
    T=(1/N)sum n n^T, degenerate if lambda3 < 0.15 (BINGHAM_ISO_THR, "empirical").
    NO periodicity term.
  * conf = clip((chanR_r+chanR_t+2 chanT)/4, 0.3, 1.0): logged, NOT used.
  * VO fail = features<20 OR position jump>1.5 m OR rotation jump>0.8 rad
    -> LIDAR_ONLY_SAFE (zero_degenerate on H_tt).
  * else 5-frame status_buf: none flagged->LIDAR_ONLY, all 5 flagged->TIGHTLY_COUPLED
    (unweighted (H_l+H_v)^-1(H_l d_l+H_v d_v)), mixed->TRANSITION (w_v=sqrt(3 lambda1)).
- Real Gazebo log (one run, 4017 frames): Channel R flagged ~80% of frames.

---------------------------------------------------------------------------------
## D1. LiDAR degeneracy detection (replaces semicircle on Schur blocks AND kappa>10)

DECISION: keep DCReg's Schur decoupling (S_RR, S_tt), but replace the threshold
with a two-part, per-eigen-direction test whose pieces are each derived:

Facts used (both verified in S1 to round-off, 1.2e-15):
  (S_tt)^-1 = [H^-1]_tt and (S_RR)^-1 = [H^-1]_RR  (block-inverse identity).
  => with residual noise sigma_r, Cov(t) marginal = sigma_r^2 S_tt^-1 (CRLB), so
     predicted std along eigenvector v of S_tt = sigma_r / sqrt(lambda_v).
  DCReg Prop. 2: S spectrum invariant to rescaling the eliminated block and to
  orthogonal basis change (so S fixes the rotation/translation units mixing).

(a) SIGNIFICANCE TEST ("is there any real information along v at all?")
  H0: direction v carries no true geometric information; the information measured
  along v is produced only by plane-normal estimation noise.
  The Jacobian row along v is perturbed by a_i^T e_i, e_i ~ N(0, C_i), where
    a_i = v (translation block), a_i = v x p_i (rotation block, since (p x e).v = e.(v x p)),
    C_i = normal-error covariance of correspondence i's local plane fit:
          var(normal tilt toward tangent t_j) = s^2/(k l_j), l_j local scatter
          eigenvalues, k=5 neighbours (A-LOAM), s^2 = point noise variance
          POOLED over all correspondences: s^2 = sum_i k l3_i / sum_i (k-3)
          (each plane fit leaves k-3 residual dof).
  Under H0: lambda_v = sum_i c_i z_i^2, z_i ~ N(0,1), c_i = a_i^T C_i a_i — a weighted
  sum of chi2(1). Satterthwaite (1946) approximation: lambda_v ~ g chi2(h),
  g = sum c^2/sum c, h = (sum c)^2/sum c^2. Reject H0 (direction really
  constrained) only if lambda_v > g * chi2_{h, 1-alpha} (UPPER tail), alpha=0.05.
  -> This is the correct-tail hypothesis test that Switch-SLAM attempted.
(b) PRECISION TEST (requirement in physical units)
  constrained only if  sigma_r / sqrt(lambda_v - mu_v) <= tau,  mu_v = sum c_i
  (expected noise information, subtracted = bias correction),
  sigma_r^2 = r^T r/(m-6) from converged residuals,
  tau_t in metres, tau_R in radians: these are APPLICATION REQUIREMENTS (e.g., the
  per-frame error the system can tolerate), not tuned constants. Verification used
  tau_t=0.10 m, tau_R=1 deg.
  A direction is DEGENERATE if it fails (a) OR (b). Report which eigenvector(s).

Why (a) is essential (S4 evidence, real nearest-neighbour point-to-plane ICP, A-LOAM-like
0.4 m voxel map, k=5 plane fits, initial-guess error 0.2 m / 1 deg, 200 runs x 5 seeds):
  corridor (truly degenerate along x): actual std along weakest direction 12.96 cm,
  raw CRLB predicts 2.08 cm; ANEES 48.25 vs consistent band [2.67,3.35] -> the
  Hessian/CRLB is ~6x overconfident in std because normal noise manufactures fake
  information. CRLB-tolerance-only test flags 0.000 of corridor frames (misses all).
Detector verdicts (fraction of frames flagged degenerate, mean over 5 seeds):
                                 corridor(degen)  corridor_doors(ok)  open_80_10_10(ok)
  chosen (a)+(b)                    0.998            0.000               0.000
  CRLB tolerance only               0.000            0.000               0.000
  Switch-SLAM semicircle on S       1.000            1.000               1.000
  DCReg kappa(S)>10                 1.000            1.000               1.000
  Channel T lambda3<0.15            1.000            1.000               1.000
  => semicircle / kappa / lambda3 rules cannot tell degenerate from well-constrained
     scenes here (consistent with Channel R firing ~80% of frames in the real log).
  In well-constrained scenes the raw CRLB is mildly overconfident (ANEES 4.74, 3.76
  vs 3) -> calibrate an inflation factor from NEES in Gazebo before using tau.
Noise-model sanity: an earlier variant using a per-fit (5-point) noise estimate
underestimated the noise information ~2x and missed the corridor; pooling s^2
fixed it (corridor lambda_min 2.5 vs threshold 4.2; constrained scenes ~130 vs ~7-9).
=> the test is only as good as the noise model; it must be NEES-checked on real data.

Why not the alternatives:
- Switch-SLAM Eq.11-12: 0.103 is the LOWER 5% point of chi2(2) (CDF=0.050, verified S2);
  a 95% test uses the upper point 5.991, which makes all three thresholds negative
  ([-1.03,-1.23,-1.37]) so the rule could never fire. Also: per-eigenvalue (λ-e)^2/e is
  not a chi-squared statistic; e_m are hand-picked midpoints; the semicircle law is
  asymptotic for random symmetric matrices with independent entries (J^T J is PSD,
  6x6). Exact recomputed thresholds [0.116,0.271,0.471]. No published critique found
  (this is our analysis — flag as such).
- DCReg kappa>10 and min-eig 120: empirical sweep; X-ICP 250/180/35, Tuna 2025
  300/150/45 — thresholds move between papers/sensors; kappa is scale-only (cannot see
  uniformly weak information) and flagged all well-constrained scenes in S4.
- Zhang 2016 D=lambda_min+1 threshold: midpoint between test scenes (empirical).
- Closest published first-principles precedent: Hatleskog & Alexis (arXiv 2410.10784,
  2024) propagate datasheet point/normal noise into the Hessian, decision with s=10.
- Frame dependence (arXiv 2608.15532, "Degenerate in Whose Frame?"): S_tt spectrum
  changes with body-frame origin (delta t' = delta t + d x delta phi); S_RR does not.
  Fix the frame (A-LOAM LiDAR frame) and state this as a limitation; cite their
  frame-equivariant generalized-eigenvalue alternative (tau=1e-2, tuned).
Implementation cost: A-LOAM patch must also publish, per planar correspondence, the
point p_i, fitted normal, and the 5-neighbour scatter eigenvalues/eigenvectors (or C_i),
plus final residuals. Selection bias (testing the minimum eigenvector) makes the test
conservative (more likely to call degenerate).

---------------------------------------------------------------------------------
## D2. Channel T (orientation tensor) — REMOVE as an independent channel

Proof: point-to-plane Jacobian row [ (p x n)^T, n^T ] => H_tt = sum n n^T = N*T exactly
(Gelfand 2003; Low 2004; verified S1, max diff 0). So Channel T is the translation
block of the Hessian divided by N, without coupling and without the amount of
information. Consequences:
- not independent of Channel R; the "two channels" double-count.
- dividing by N discards how much information there is: well-constrained scenes have
  lambda3(T) ~0.09-0.10 (S3), so lambda3<0.15 false-alarms (100% in S4).
- Bingham uniformity test is the wrong hypothesis: H0 = normals uniform on the sphere.
  Correct form B = (15N/2) sum(lambda_i - 1/3)^2 ~ chi2_5 (Bingham 1974; Mardia & Jupp)
  — note the project's earlier "15N" was missing the /2. In S3, B = 89–3849 for all
  scenes (crit 11.07) and grows linearly with N: rejects for degenerate and
  well-constrained scenes alike; separates nothing.
- Aliasing claim is unsupported: lambda3 of a second-moment tensor is blind to
  periodicity (a smooth corridor and a periodic-panel corridor can have identical T).
  Scenario 2 Part B validated a DIFFERENT score (concentration x periodicity) that is
  not in the deployed code. Aliasing (multi-modal cost) ≠ degeneracy (rank deficiency).
If a pre-registration (correspondence-free) predictor is wanted: apply the SAME D1
test to the scan's own points and normals (Gelfand stability analysis) — no new constant.
Aliasing detection = future work (e.g., cost/autocorrelation profile along weak
directions), labelled as a proposal; no dedicated LiDAR literature found.

---------------------------------------------------------------------------------
## D3. Scalar confidence `conf` (and conf_L/conf_V) — REMOVE

Proof that no scalar can encode directional degeneracy: c*H = U (cΛ) U^T keeps the same
eigenvectors and condition number; it rescales all 6 DOF equally. The weights
(1,1,2), the /4 and the [0.3,1] clip have no derivation. There is no visual conf in
code. The bilateral form (c_L H_l + c_V H_v)^-1(c_L H_l d_l + c_V H_v d_v) has the same
mean as covariance intersection with omega = c_L/(c_L+c_V); it is legitimate ONLY if
the Hessians are on a common information scale and omega is chosen by minimizing
det/trace of the fused covariance (D4) — i.e., the only defensible scalar is CI's
optimized omega, not a heuristic score. Visual trust enters through its information
matrix, not a scalar.

---------------------------------------------------------------------------------
## D4. Fusion equation — information-scaled, projected, covariance intersection

FINAL:
  I_l = H_l / sigma_l^2            (A-LOAM unit weights -> divide by residual variance;
                                    use final IRLS/Huber weights if robust loss active)
  I_l^p = U_p Λ_p U_p^T            (keep only eigen-directions that PASS D1; Zhang 2016
                                    solution remapping / Switch-SLAM Λ_p, information form)
  I_v = Schur-marginal information of the current pose from VINS-Mono's window
        (VINS already whitens residuals: sqrt_info = FOCAL_LENGTH/1.5 — mark as from notes)
  omega = argmin_w det( (w I_l^p + (1-w) I_v)^-1 )
  delta = (omega I_l^p + (1-omega) I_v)^-1 (omega I_l^p d_l + (1-omega) I_v d_v)
  fused covariance P = (omega I_l^p + (1-omega) I_v)^-1
  (equivalently via gradients: H d = -g avoids forming d_l when H_l is near-singular)
Proofs:
  - BLUE/Gauss–Markov: for independent unbiased x1 (P1), x2 (P2),
    x = (P1^-1+P2^-1)^-1(P1^-1 x1 + P2^-1 x2) is minimum variance (Loewner order). Needs
    unbiased, uncorrelated, correctly scaled, same tangent space. Our increments are
    correlated (shared IMU, shared prior T_{k-1}, LiDAR seeded from VO) and A-LOAM is
    biased along degenerate directions -> BLUE's covariance claim fails.
  - CI (Julier & Uhlmann 1997): consistent for ANY unknown cross-correlation;
    Reinhardt et al. 2015: tightest consistent bound for two estimates.
  - Projection removes the biased degenerate directions (Zhang 2016).
Evidence S5 (6-DOF, 4000 runs x 5 seeds; stylized magnitudes: LiDAR fake degenerate
info lambda=1.7 (CRLB ~1.5 cm, from S4 corridor) but true error 0.2 m along it):
                                      RMSE_t indep.   RMSE_t corr(0.6)   ANEES corr (<=6.11 ok)
  code now (H_l+H_v) unscaled          1.189 cm        1.195 cm            —
  scalar conf (H_l+0.65 H_v)           1.172           1.178               —
  info-weighted, NO projection         3.551           3.583               —
  BLUE + projection                    0.713           0.718               7.03 OVERCONFIDENT
  CI + projection (omega=0.83)         0.713           0.717               4.47 consistent
  (BLUE/CI equal RMSE here because along the degenerate axis both use vision only and
   elsewhere LiDAR dominates; the difference is consistency, which matters for the
   backend and for thresholds.)
Switch-SLAM Eq.15 as printed uses identity norms (a plain average of increments); the
information-consistent version is the form above — flag as a possible typesetting
issue, authors' code not checked.
Modes collapse to: VO healthy -> CI fusion with LiDAR projected (covers normal and
degenerate continuously). VO failed -> LiDAR projected, IMU-propagated prediction fills
the projected-out directions (Zhang 2016 remapping with x_p = IMU prediction).

---------------------------------------------------------------------------------
## D5. Visual channel

- The project's VO-fail constants are misattributed: VINS-Mono failureDetection()
  (estimator.cpp L621–667) restarts on acc-bias norm > 2.5, gyro-bias norm > 1.0,
  position jump > 5 m, z jump > 1 m; "features<2" and "rotation>50 deg" checks only
  print (return commented out). 20 is VINS-Mono's KEYFRAME rule (feature_manager.cpp
  L74). 1.5 m / 0.8 rad are project values. LVI-SAM uses the same plus speed > 30 m/s.
- Switch-SLAM Sec. III-D explicitly rejects a visual Hessian eigenvalue test ("minimum
  eigenvalue of the Hessian of VO is unstable and remains large after failure", citing
  Demmel et al. ICCV 2021 — citation looks loose) and adopts VINS-Mono's failure
  detection; S_vo binary.
DECISION: (1) hard-failure flag = VINS-Mono's own criteria (state they are the authors'
empirical constants, not derived; no derived alternative exists in the literature);
(2) no separate visual threshold — visual information enters fusion via I_v and CI
weights it; (3) optional novel extension, labelled as such: Schur-marginalize to the
relative pose of the two newest keyframes (VIO has 4 unobservable DOF: yaw + 3
translation; gauge freedom makes absolute-pose information meaningless), and test the
information vision adds over IMU (generalized eigenvalue / log-det ratio) with the D1
style significance test. Degenerate motions (Wu & Roumeliotis): constant acceleration
-> scale unobservable; no rotation -> roll/pitch/yaw unobservable.

---------------------------------------------------------------------------------
## D6. Mode switching / hysteresis — Bernoulli CUSUM replaces the 5-frame buffer

Per-frame D1 verdict f_k in {0,1} with false-flag rate a and detection rate b.
Log-likelihood ratio increments: s = ln(b/a) if f_k=1, ln((1-b)/(1-a)) if 0.
g_k = max(0, g_{k-1} + s_k); switch to "degenerate" when g_k >= h; a second CUSUM with
roles swapped switches back. h chosen for an in-control average run length ARL0
(frames between false switches). Optimality: CUSUM minimizes worst-case detection delay
for a given ARL0 (Lorden 1971; Moustakides 1986; Page 1954; Basseville & Nikiforov).
Evidence S6 (a=0.05, b=0.90, 5 seeds): h=6.0 gives ARL0 = 3019 frames (~5 min at 10 Hz);
current buffer puts 22.0% of NON-degenerate frames in 'Transition' (any 1 flag of 5)
vs CUSUM 0.06% false alarms; detection delay buffer->Fully 5.99 frames vs CUSUM 2.27.
The √(3 lambda1) transition blend (Switch-SLAM Eq.13, heuristic) becomes unnecessary
because CI+projection is continuous.
Caveat: a, b must be measured (S4 shows the chosen test reached a≈0, b≈0.998 in sim).

---------------------------------------------------------------------------------
## D7. Backend
Not implemented; no proof needed. Either implement (iSAM2 factor graph, LIO-SAM style,
fused pose + P from D4 as odometry factor — CI covariance is consistent, so it is safe
to use as a factor), or scope it out explicitly as a limitation.

## D8. DCReg mitigation
State: detection math borrowed, PCG mitigation not used; D4 projection is the
mitigation actually used (Zhang 2016 remapping lineage).

---------------------------------------------------------------------------------
## D9. Validation protocol (replaces v1/v2 synthetic SPD tests)
- Ground truth from geometry (protocol of arXiv 2608.15532): Gazebo worlds with known
  degenerate directions: rectangular corridor (1 translational), circular tunnel
  (translation along axis + rotation about axis), corner/room (0). Per-direction labels
  also from ground-truth pose error projected onto eigen-directions. Never define GT
  with the detector's own quantity/threshold.
- Detection metrics with Wilson 95% intervals; n >= 1068 labelled frames per class for
  ±0.03 at p=0.5 (S7: 400 -> ±0.049, 800 -> ±0.035, 3000 -> ±0.018). 5 seeds/runs;
  McNemar test for paired detector comparisons.
- Covariance calibration: ANEES over N runs must lie in
  [chi2_{α/2}(N n_x)/N, chi2_{1-α/2}(N n_x)/N] (6-DOF, N=50: [5.08,7.00]); derive the
  CRLB inflation factor from it.
- Threshold sensitivity: sweep alpha and tau on a log grid; ROC/PR; tune on some worlds,
  test on others (not random frames of one run); show ATE/RPE plateau vs threshold.
- Trajectory: ATE/RPE with evo (Sturm 2012 definitions; SE(3) Umeyama alignment for
  LiDAR-centric, 4-DoF for VIO per Zhang & Scaramuzza 2018); forced-mode ablations on
  the same bag (LiDAR-only, VIO-only, current switching, new method); per-segment RPE;
  Wilcoxon signed-rank; 5–10 runs, report median and spread.
- Datasets: GEODE (used by DCReg; tunnels, independent GT), SubT-MRS, ENWIDE (X-ICP),
  FusionPortable.
- Real log reinterpretation: LIDAR_ONLY_SAFE 0.96 vs TIGHTLY_COUPLED 30.5 mean error is
  confounded by segment; must be re-tested with forced-mode replays.
- Scenario 2 Part A ("Hessian blind to aliasing") is about aliasing, which D2 says is a
  separate problem; Part B tested a non-deployed score — retire both claims.

---------------------------------------------------------------------------------
## New errors found during this research (add to the audit)
N1. Switch-SLAM's own Eq.11–12 uses the lower 5% chi2(2) point (0.103) as if it were
    the 95% critical value — the borrowed threshold inherits a statistical error.
N2. Channel T is mathematically H_tt/N — not an independent channel.
N3. The Bingham statistic written earlier in the project (15N·Σ(λ−1/3)²) is off by a
    factor 2; correct is (15N/2)·Σ(λ−1/3)². And it tests the wrong hypothesis.
N4. Scenario 2 Part B validated a periodicity score that is not in the deployed code.
N5. VO-failure constants attributed to VINS-Mono are not VINS-Mono's (20 = keyframe rule).
N6. The code's fusion mixes an un-normalized A-LOAM Hessian with a whitened VINS
    Hessian -> the relative weighting is arbitrary (depends on unlogged magnitudes).
N7. The 5-frame buffer sends ~22% of normal frames to TRANSITION at a 5% per-frame
    false-flag rate (S6).
N8. Raw CRLB/Hessian covariance is overconfident in corridors (S4 ANEES 48 vs 3), so a
    CRLB-only threshold would miss degeneracy — the noise-floor test is required.

---------------------------------------------------------------------------------
## Prior audit (Section 12 of project doc), item → decision
A1–A6 thresholds → D1 (and D2 for Channel T items A4–A5).
B7–B13 conf → D3, D4.
C14–C17 fusion equation → D4.
D18–D19 switching → D6.
E20–E21 visual → D5; E22 backend → D7; E23 DCReg mitigation → D8; E24 feedback loop
(documentation fix only, no method decision needed).
F25–F33 validation → D9.
G34–G36 explanation errors (already corrected; no method needed).
