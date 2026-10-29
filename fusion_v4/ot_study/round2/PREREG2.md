# OT channel, round 2: the orientation tensor as a separate weight, and generality (pre-registered 2026-10-28T19:59Z, before any candidate below is run)

Structure kept fixed: Schur R (rotation, ROT_CHECK as in F20), Schur T (translation, C_T = 0.03), the orientation-tensor (OT) channel always on (heading read-out SAH unchanged), A-LOAM front end, VINS-Mono.
Baseline: F20 = SAH + ROT_CHECK + OT_SRC=geom + OT_MODE=min. Reference: F16.

## Notation (per scan, translation, LiDAR body frame)
A = S_tt (Schur translation information claimed by the solver). G = keyframe geometric orientation tensor (trace 1), rotated to the current frame. N = tr(H_tt). B = N G (the information the raw geometry supports, same total mass as the solver's).
W(X) = info_weight(X, c = 0.03, gamma) = (cX + gamma I)^-1 cX. gamma = VIO prior information (1 unless a VIO check is on).

## Candidates
Translation rules (all with SAH + ROT_CHECK, gamma = 1):
| tag | rule | kind |
|---|---|---|
| F20 (T_min) | per eigen-direction v_i of A: min(lambda_i, N v_i^T G v_i) | cap in the solver's basis (baseline) |
| T_gmin | B^1/2 min(M, I) B^1/2, M = B^-1/2 A B^-1/2 (generalised-eigen min) | basis-free cap: the largest information both channels support along their common (generalised) eigen-directions |
| T_gmax | B^1/2 max(M, I) B^1/2 | "safe fusion" (optimistic, for completeness) |
| T_psum | 2 (A^-1 + B^-1)^-1 = 2 A (A + B)^-1 B (matrix harmonic mean, parallel sum) | basis-free; series combination of the two uncertainties |
| T_agm | A # B = A^1/2 (A^-1/2 B A^-1/2)^1/2 A^1/2 (Ando geometric mean) | basis-free |
| T_ci | w A + (1 - w) B, w in [0, 1] maximising det (covariance intersection) | consistent fusion of two information claims of unknown correlation |
| T_wprod | W_A^1/2 W_B W_A^1/2 (W_A = W(A), W_B = W(B)) | OT as a separate third weight: AND of two weights |
| T_wmean | (W_A + W_B) / 2 | OT as a separate third weight: equal vote |
| T_min3 | min rule with G3 = (sum_planar n n^T + sum_linear (I - d d^T)/2 + sum_scatter I/3) / n_all | tensor alternative: scattered points (vegetation, clutter) count as isotropic support |
| T_minS | min rule with G_S = Schur translation block of the scan's own geometric 6-DoF Hessian (J = [p x n; n] per planar point, [p x e; e] / sqrt 2 for the two directions e normal to each line), divided by its tr(H_g,tt) | tensor alternative: rotation-translation coupling of the raw geometry |
Small regularisation where an inverse or square root of a rank-deficient B or A is needed: X + 1e-9 tr(X) I (numerical only).

VIO-trust variants (gamma), on top of a translation rule:
| tag | rule |
|---|---|
| V0 | gamma = 1 (as F16 / F20) |
| V1 | the G20 checks ported unchanged in form: segment-level and 5 s VINS-LiDAR scale-consistency gates (VIO_CHECK=1, VIO_CHECK_FAST=5) and the 2 s LiDAR blow-up guard (LIDAR_GUARD_T=2); VIO untrusted at the start of a segment until it has agreed. References recomputed for the A-LOAM stack by the G20 rule (largest value on the 6 Multi Floor F8 replays; guard excess 3x the largest 2 s excess on them). |
| V1b | V1 but the VIO is trusted at the start of a segment (gamma = 1 until a check has enough windows to judge) |
| V2 | V1b with the check statistic measured only along the directions both LiDAR channels support: each step's LiDAR and VIO increments are multiplied by P = W(A') (A' = the OT-capped information of the chosen rule) before the window displacements are formed; windows whose projected LiDAR displacement is under 1 m are not judged. Same reference rule as V1, recomputed with the projection. |

## Data (open-loop node-harness replays, real callbacks, SAH_SYNC=1)
MF: F8 kf runs 1-6 (calibration sequence). LC: F8 kf runs 1-3, C02: F8 kf runs 1-3 (SAH development data). GEODE stairs alpha: F16 kf runs 1-2 and F5 kf run 1 (real VINS-Mono scale failure; seen during the G20 design on the GenZ stack, so not clean held-out). Gazebo farm bag (gzfarm_nd): F8 kf run 1 and F5 kf run 1 (held-out for any change after G20; **scored once, after the final choice is fixed, not used for any choice**).
Own-setting checks before anything else: F16 on the GEODE F16 logs and F8 on the farm F8 log must reproduce the live ATE (19.77 / 17.54 / 0.99 m) within 0.02 m, else the sequence is dropped and this is reported.

## Conditions (MF, LC, C02)
- clean.
- FL, LiDAR solver fault (stage 3 of round 1): three 20 s windows at 25/50/75 % of the log, LiDAR pose slides 0.2 m/s along the weakest Schur direction, H_tt replaced by tr(H_tt)/3 I.
- FV, VIO scale fault: the same three windows; inside them the VINS translation increments are multiplied by 2.5 (the size of the GEODE failure); the offset stays afterwards. Rotation untouched.
- FS, sparse keyframes: every keyframe cloud randomly thinned to 25 % (fixed seed) before SAH and the OT channel.
GEODE: clean only (it is a real VIO failure).

## Metric and selection
Per log full-span ATE RMSE (Umeyama SE(3), no scale); per cell the mean over its logs. Cells: {MF, LC, C02} x {clean, FL, FV, FS} and GEODE clean = 13 cells.
Score of a candidate = mean over the 13 cells of ln(ATE_cand / ATE_F20) (negative = better than F20; every condition counts equally, so no single sequence or fault decides).
Admissible only if on clean MF, LC and C02 each mean is within +0.05 m of F20 (the "same as F16 / F20 on healthy data" target), and the OT channel is used (all candidates satisfy this).
Stage A: choose the translation rule (V0) with the lowest score among the admissible; if two are within 0.01 in score, the one listed first in the table above. Keep the best two for stage B.
Stage B: on the two stage-A finalists, V0 / V1 / V1b / V2; choose the lowest score with the same admissibility rule; ties within 0.01: V0, V1b, V2, V1 (fewest parts first).
Final check with loops: the chosen design and F20 through the loop back end (iso, 1 round, odometry 1.46 deg / 0.054 m) on MF, LC, C02 clean.
Held-out: the farm bag, scored once for F16, F20 and the chosen design; LiDAR alone and VINS alone of the same logs given beside them.
Reported whatever comes out; nothing is tuned after the scores are seen; replay numbers are not live numbers.

## Synthetic scenes (channel level, independent of these bags)
VLP-16-like scans ray-cast in: corridor, tunnel (cylinder), room, open field with poles/trunks, vegetation (scattered points), single wall, stairwell. A-LOAM-like features (curvature-selected edge and surf points matched to the true geometry) give an honest solver Hessian. For each scene and each tensor (G, G3, G_S): the ratio N v_i^T G v_i / lambda_i along the solver's eigen-directions (cap binds on an honest solver where < 1), and with a confident wrong solver (H_tt -> tr/3 I) how much of the false information each rule removes along the truly weak direction. Reported per scene; not used for selection.

## Amendment before any candidate was run (2026-10-28, after the own-setting checks only)
Own-setting checks: farm F8 replay 0.990 m = live 0.990 (exact). GEODE F16 replays 19.702 and 17.643 m against live 19.766 and 17.537 (differences -0.06 and +0.11 m, above the 0.02 m written above). Diagnosis: the replays equal the live logs row for row up to the first SAH correction (row 393 of 3444, row 391 of 3451) and diverge from there; the live SAH worker runs asynchronously (keyframe processing time decides when a correction lands), the replay runs it synchronously; besides that 10 rows of each log differ only in the mode at VINS re-initialisation boundaries. The 0.02 m tolerance was written to catch pipeline errors (extrinsics, frames) and cannot hold for SAH configurations on any sequence. GEODE is kept; every candidate on GEODE is compared with the F20 replay on the same logs, never with live numbers. The farm check (no SAH) is exact.

## Amendment 2, 2026-10-28 ~20:25Z: three candidates added from the synthetic channel test, before any stage-A replay score was read
The synthetic scenes (synth_scenes.py, seed 0; channel level only) showed two defects of the round-1 tensor G:
(1) on a flat open ground plane G reports 22 % horizontal support (truth: none) because k-NN neighbourhoods on a plane are elongated along the LiDAR rings and get classified as 'lines' (multi-scale classification, k = 12 and 36, does not remove it);
(2) the min rule compares absolute amounts (N v^T G v against lambda), but the solver's feature points and the voxelised keyframe points are different samples, so the cap also binds on well-constrained strong directions (corridor: the strongest-direction weight falls from 0.91 to 0.67).
Added candidates (stage A, same conditions, same score and admissibility rules; listed after T_minS in the tie order):
| tag | rule |
|---|---|
| T_smin | shape cap with G: lambda_i' = min(lambda_i, lambda_max tau_i / tau_max) (only the anisotropy of the two channels is compared, never their mass) |
| T_minRF | min rule with G_RF = G without 'lines' whose direction is within 30 deg of the azimuthal sweep direction z_body x p (spinning LiDAR) |
| T_sminRF | shape cap with G_RF |
Synthetic numbers that motivated them (seed 0, weight on the truly weakest direction with a confident wrong solver; none / min-G / smin-G / smin-G_RF): corridor 0.79 / 0.38 / 0.21 / 0.10, single wall 0.79 / 0.60 / 0.48 / 0.17, open ground 0.78 / 0.71 / 0.60 / 0.08, room 0.78 / 0.75 / 0.70 / 0.66 (room is not degenerate: no protection needed). Honest-solver weights on the weak direction unchanged by all four in seven of eight scenes; on open ground G_RF lowers it from 0.22 to 0.01 (the A-LOAM-like solver itself over-claims horizontal information on a bare plane).
G_RF assumes a spinning LiDAR with its axis along body z (true for every sequence here); for a non-repetitive scanner the ring test would drop real lines and is not claimed.
Replay harness: a keyframe-geometry cache (KF_CACHE) was added; F20 on MF1 is bit-identical with a cold and a warm cache.

## Stage A outcome (2026-10-28 22:05Z, all 714 replays complete)
Scores (mean ln ratio to F20 over 13 cells): gmax -0.0286, agm -0.0156, wmean -0.0156, psum -0.0146, ci -0.0144, smin -0.0135, minS -0.0081, min3 -0.0040, gmin -0.0008, F20 0, F16 -0.0067 (reference); not admissible: wprod +0.122 (LC +0.31, C02 +0.35 clean), minRF +0.014 (LC +0.12), sminRF +0.005 (LC +0.13, C02 +0.065).
Stage-A choice: gmax (no other rule within 0.01). Finalists for stage B: gmax and agm (agm -0.015581, wmean -0.015575: agm second).
Reading: gmax and agm raise the LiDAR translation information where the geometry supports more than the solver claims; they gain in the cells where the VINS is the weak sensor (FV, GEODE, C02 clean) and lose under the LiDAR fault (FL). The fail-safe rules (S' <= S_tt: min, gmin, smin, minS, min3, minRF, sminRF, wprod) do the opposite.

## Amendment 3, written before stage B is run: reported arms
Because a VIO check may take over exactly the cells in which gmax gains, two arms are added to stage B for reporting, **not eligible for the stage-B choice**: F20 (the baseline rule) and smin (the best-scoring admissible fail-safe rule), each with V1, V1b, V2. If a reported arm scores better than the stage-B choice it is reported as such, and both are scored on the held-out farm bag; the stage-B choice stays the choice of this study.
V1 / V1b references (A-LOAM stack, G20 rule on the 6 MF replays): VIO_CHECK_REF 0.157, VIO_CHECK_FAST_REF 0.277, LIDAR_GUARD_EX 4.325 (3 x 1.442). V2 references: recomputed per rule on MF with the projection (cal_v2.sh).

## Stage B outcome (2026-10-28 23:40Z, 612 replays complete)
Scores: gmax/V2 -0.1787, gmax/V1b -0.1781, agm/V2 -0.1750, gmax/V1 -0.1743, agm/V1b -0.1730, agm/V1 -0.1700 (all within 0.01 of the best), gmax/V0 -0.0286, agm/V0 -0.0156. Tie order V0, V1b, V2, V1 -> **stage-B choice: gmax + V1b** (named F21 below).
Reported arms (not eligible): smin/V1b -0.1720, smin/V2 -0.1720, F20/V1b -0.1655, F20/V2 -0.1647, F20/V1 -0.1636 (smin/V1 not admissible: C02 clean +0.051). None scores better than the choice, so only the choice, F16 and F20 are scored on the farm bag; F20/V1b is added there for reporting only (it separates the VIO check from the translation rule).

## Diagnostic arm (written before it is run; not a candidate, C_T stays frozen at 0.03)
gmax raises mainly the weakest-direction LiDAR weight (MF mean w0 0.694 -> 0.812, LC 0.643 -> 0.696, C02 0.718 -> 0.779; w2 almost unchanged). To see whether a constant gives the same, F20 + V1b is replayed with C_T = 0.056, the value at which the F20 weak-direction weight on MF would reach gmax's (c lambda from 2.27 to 4.26). Same 13 cells and the farm bag; reported beside F21, never selected.

## Final outcome (2026-10-29)
Loop back end (iso, clean): F20 MF 0.469 / LC 1.455 / C02 1.481; F20+V1b 0.470 / 1.457 / 1.481; F21 0.457 / 1.331 / 1.349.
Diagnostic arm (F20+V1b, C_T = 0.056, 13 cells): score -0.1905 (F21 -0.1781, F20+V1b -0.1655); farm 0.186 m (F21 0.280, F20+V1b 0.330); worse than F21 on MF-FL and C02-FL. Reported only, not selectable.
The stage-B choice stands: F21 = gmax + V1b. Conclusion and limits: docs/results/OT_Channel_Round2.md.
