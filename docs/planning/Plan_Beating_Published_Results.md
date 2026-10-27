# Plan: beating published results (Multi Floor, Long Corridor)

Saved 2026-10-13. Full plan doc: https://claude.ai/code/artifact/16a215ee-ade4-46e5-abb3-a37bb9a5d62d
Code: `fusion_v2.zip` (fusion_core.py, fusion_node_v2.py, run_fusion_study.sh, calibrate_c.py, fusion_summary.py,
offline_evidence.py, patch_mapping_hessian.py, v2_tools.py, test_fusion_core.py, README.md).

## Targets (ATE RMSE / max, m)

| Source | Multi Floor | Long Corridor | Fair for us? |
|---|---|---|---|
| Switch-SLAM, RA-L 2024, Table II (mean of 3 runs, no loop closure, LOAM features + VINS-Mono) | 1.61 / 3.63 | 2.42 / 5.09 | Yes, the main target |
| SubT-MRS challenge, LiDAR track best (FAST-LIO2 + HBA), arXiv 2307.07607 Table 3 / supp. Table 9 | 0.401 | 1.454 | No: stronger front end plus back end |
| SubT-MRS challenge, FAST-LIO + pose graph | 0.577 | 1.254 | No, same reason |
| D²-LIO, Long_Corridor_1: FAST-LIO2 / D²-LIO | — | 1.08 / 1.65 | Reference only |
| DCReg, Cave02 | 0.0457 (prior-map localisation) | — | No, different task |

## Where we stand and why

- Old node: 1.39 ± 0.14 m RMSE, 4.58 ± 0.12 m max (3 runs). VINS-Mono alone 1.02–1.34 m.
- Three defects: (1) LIDAR_ONLY used scan-to-scan odometry (17.6 m alone) instead of scan-to-map (3–4 m);
  (2) VINS world and A-LOAM frames mixed without rotation (8–62° apart); (3) the maximum is VINS-Mono's
  start-up transient (first 20 s, robot covers ~21 m; it moves only 1.1 m before VINS-Mono starts).

## Method (fusion_node_v2)

VIO-primary, degeneracy-gated, information-weighted LiDAR correction on relative motion in the LiDAR body frame.
Per mapped scan: dt = W_t dt_lidar + (I − W_t) dt_vio, W_t = (c_T S_tt + I)⁻¹ c_T S_tt (Schur translation block),
applied only when κ(S_RR) ≤ 15.7 (Otsu, label-free; or online Otsu). c_R = 0 (rotation from VINS-Mono).
WARMUP (LiDAR only) before VINS-Mono and for 20 s after each (re)start; VO_FAIL on VINS loss/jump > 1 m.
A-LOAM's initial guess = fused pose moved by VINS-Mono motion. C_T chosen on bag 0 only (min 1-s RPE, do-no-harm).

## Offline evidence (open-loop replay of two old logs; positions only; scan-to-scan Hessian)

| Variant | Run A bags 1–2 | Run B bags 1–2 | Run A full | Run B full |
|---|---|---|---|---|
| VINS-Mono alone | 0.769 / 1.72 | 0.790 / 1.89 | 1.340 / 4.90 | 1.023 / 3.35 |
| + LiDAR warm-up | 0.769 / 1.72 | 0.790 / 1.89 | 1.264 / 4.08 | 0.953 / 2.45 |
| + gated Schur weights, C_T = 1e-3 | 0.652 / 1.43 | 0.729 / 1.47 | 1.219 / 4.13 | 0.808 / 1.85 |
| C_T chosen on bag 0 | 1e-3 | 0 (VINS only) | 1.219 / 4.13 | 0.953 / 2.45 |

Alignment sensitivity (offline_evidence.py section 5): depending on the window used to align A-LOAM's map frame
to VINS (0–90 s), the C_T = 1e-3 full-span max is 2.6–5.3 m (run A) and 1.6–5.1 m (run B); every max above 2 m
is in the first 2 s; RMSE stays 0.77–1.35 m; the bags 1–2 gain holds. RMSE target looks robust; max does not.

## Experiment plan (pass criteria fixed in advance)

0. Install + tests + 70-s smoke (expect VINS-Mono from ~20 s, FUSED from ~40 s).
1. F0 once, `calibrate_c.py` on bag 0 → LASER_C_T.
2. `REPEAT=3` F0–F5 (~2.5 h). Pass: F1/F2 mean full-span < 1.61 m RMSE and < 3.63 m max; F1 beats its own
   VINS-only replay on bags 1–2 in ≥ 2 of 3 runs; F3 (no gate) worse than F1.
3. Scan-to-map Hessian patch; M0, calibrate, M1 × 3; keep only if its paired gain beats F1's.
4. `REPEAT=5` best + F0 with the same LASER_C_T; mean ± sd; Wilcoxon vs F0 replay.
5. Long Corridor with correct GT (SuperLoc Corridor01 `1QbQamSktPAzJkf0GduAPTqQlxuxM0DBK`, or Sensor-Fusion
   folder `1bSGDe1FFQYEjs20P8L15pTx7T0HCn2L0`); target < 2.42 / 5.09 m.
6. FAST-LIO2 without loop closure as our own baseline.
Ties: < 0.3 m between separate runs; use paired replays for method-vs-F0.

## Novelty claims (incremental; read full texts of Selective KF, SA-LIVO, LODESTAR first)

1. Real-data, held-out, drift-labelled benchmark of 15 degeneracy rules inside a LiDAR–VIO system.
2. Switching-based evaluation cannot rank detectors when VIO is strong (ATE vs handover share ρ = −0.99).
3. Label-free Otsu threshold on κ(S_RR) (held-out J 0.48; no prior Otsu-for-degeneracy found).
4. Frame-consistent VIO-primary, gated, information-weighted correction with bag-0 calibration.
5. Two errors in Switch-SLAM's derivation (wrong χ² tail; unweighted Eq. 15), worded as analysis.

## Main risks

Offline-only evidence; the max depends on A-LOAM during the 20-s warm-up; calibration may pick C_T = 0;
VINS-Mono sets the floor; Switch-SLAM's alignment/span not stated; 0.401 m needs a different stack;
node never run in ROS yet; one sequence and the scan-to-scan Hessian so far.

## Update, 14 October 2026

**First live run.** F0 (VINS-Mono inside fusion_node_v2): 1.29 m RMSE, 2.51 m max, full span (3305 scans).
This already beats Switch-SLAM (1.61 / 3.63), so the method is judged only against F0 and F3 on paired runs.
Bag-0 calibration chose C_T = 0.003 (RPE curve fairly flat: 0.110 at C_T = 0, 0.097 at 0.003).
Batch F0-F5 x 3 launched with LASER_C_T=0.003.

**Leaderboard additions (RMSE, m).**
- Long Corridor, no back end: LODESTAR 1.386 (threshold grid-searched on this sequence), GenZ-ICP 1.982 / 1.99,
  DLIO 2.294, LIO-SAM 2.959, KISS-ICP 3.028, FAST-LIO2 3.113, iG-LIO 3.136, AdaLIO 3.160 (LODESTAR Table V).
- Long Corridor, with back end (challenge): 1.254 (FAST-LIO + pose graph), 1.454 (FAST-LIO2 + HBA).
- Multi Floor: FAST-LIO2 and LIO-SAM fail (NV-LIO, qualitative). GenZ-LIO (T-FR 2026) evaluates both sequences;
  its table could not be read (ask the user for the PDF).

**Novelty boundaries from full texts.**
- Selective Kalman Filter: Schur-complement covariances per block, per-eigendirection thresholds "based on
  practical requirements and experience", adaptive thresholds listed as future work; LiDAR-primary; no scale calibration.
- SA-LIVO: soft per-eigendirection weights gamma = min(sqrt(lambda)/sigma_min, 1), fixed SI floor, dataset-tuned
  thresholds; no separate LiDAR/vision scale calibration; not on SubT-MRS.
- LODESTAR: condition-number threshold 1.5 grid-searched on SubT-MRS Long Corridor + HILTI Basement 4.
- Hinduja et al. IROS 2019: partially constrained loop factors from degeneracy-aware ICP (dynamic threshold).
- DeCOD 2026: corridor factors with degeneracy assumed from the environment.
=> Our clearest claim: label-free (Otsu) degeneracy cut, used both for front-end gating and loop factors.

**Lever: loop closure.** 88 of 248 one-metre Multi Floor keyframes revisit an earlier place (<4 m, same floor).

**fusion_v3 (delivered).** keyframe_recorder.py (ROS, RECORD_KF=1), backend_icp.py (coarse-to-fine p2pl ICP with
Schur-projected updates and information matrix), backend_graph.py (loop search, Huber + chi2 pruning, GTSAM,
odometry noise calibrated on bag 0 incl. rotation via hand-eye axis alignment), run_backend.py (ablation:
none / iso / hessian / schur / schur_otsu / schur_gate; --front fused | aft | vins_replay), check_gt.py,
calibrate_c.py --c-r-grid, config F6 (C_T + C_R).

**Synthetic check (code test only), ATE RMSE (m):**
| Scenario | none | iso (LIO-SAM-like) | hessian | schur | schur_otsu | schur_gate |
|---|---|---|---|---|---|---|
| room + 50 m corridor, out and back | 0.623 | 0.031 | 0.035 | 0.031 | 0.035 | 0.036 |
| room + 120 m corridor, out and back | 1.582 | 0.677 | 0.689 | 0.042 | 0.039 | 0.047 |
Mechanism: loops that keep information along a degenerate corridor axis lock in the along-axis drift.
Robust-kernel lesson: Cauchy discarded true loops far from the drifted estimate; Huber + chi2 pruning fixed it.

**Waiting on the user.** (1) batch results; (2) one RECORD_KF=1 run of F1 with LASER_C_T=0.003, then upload
for_claude.zip (results_index, summaries, F0/F1 logs, F1_kf log + keyframes npz); (3) Long Corridor ground truth
from Drive folder 1bSGDe1FFQYEjs20P8L15pTx7T0HCn2L0, checked with check_gt.py; (4) optionally the GenZ-LIO PDF.

## Update, 14 October 2026 (batch results, F0-F5 x 3, LASER_C_T = 0.003)

Full-span ATE RMSE / max (m), mean of 3 live runs, one global alignment (Umeyama, no scale):

| Config | RMSE | max | bags 1-2 (held out, own alignment) |
|---|---|---|---|
| F0 VINS-primary control | 1.275 | 2.47 | 0.751 |
| F1 gated (kappa <= 15.7) | 1.050 | 2.09 | 0.735 |
| F2 gated (online Otsu) | 1.046 | 2.07 | 0.701 |
| F3 no gate | 0.960 | 1.91 | 0.545 |
| F4 / F5 LiDAR only (scan-to-map) | 9.6-42.9 / 13.2-35.4 | 15-64 | 2.8-11 |
Switch-SLAM Table II: 1.61 / 3.63.

Pass criteria set in advance: (1) F1/F2 < 1.61 / 3.63: PASS. (2) F1 beats its own VINS replay on bags 1-2 in >= 2 of 3 runs: PASS
but small (gain 0.03-0.05 m; full span gain 0.22-0.27 m). (3) F3 worse than F1: FAILED, F3 is better in 3 of 3 runs
(held-out 0.534/0.535/0.567 vs 0.758/0.693/0.753). Paired replay on the F3 logs (gate on vs the live ungated run):
full 1.081/1.024/1.132 vs 0.936/0.927/1.018. Replays on the F0 and F1 logs agree (gate on 1.044 / 1.062, gate off 0.972 / 0.967).
Conclusion: the kappa gate costs accuracy here; the Schur information weighting W alone does the work. The Otsu-for-
front-end-gate claim is NOT supported on Multi Floor. F2 (online Otsu) ~ F1: no benefit either.
Rotation correction (C_R > 0) hurts in every replay (full span 1.46-2.4 m at C_R = 1e-3..1e-2): keep C_R = 0, drop F6.
Replay fidelity: replay of C_T = 0.003 ungated predicts 0.97 on the F0/F1 logs; live F3 gave 0.960.

Re-calibration without the gate (bag 0 only; replay on F0_run1 and F1_run1 logs, C_R = 0):
- RPE horizon 1 s picks C_T = 0.003 (bag 0: 0.0908 / 0.0965; 0.01 is 0.0906 / 0.0978).
- Horizon 5 s picks 0.01 on both logs; 10 s and 20 s are ties between 0.01 and 0.03. Held-out RPE is best at 0.01 for 5/10/20 s.
- Replay at C_T = 0.01 ungated: full 0.798 / 0.761, max 1.71 / 1.63, bags 1-2 0.398 / 0.414 (VINS-only 0.77 / 0.79).
  C_T = 0.03: full 0.723 / 0.675 but short-horizon RPE worsens (0.098 / 0.105 on bag 0).
- The horizon rule was chosen after seeing held-out numbers; the live runs F7 (C_T = 0.01) and F8 (C_T = 0.03, sensitivity)
  are the fresh test. Nothing above 0.96 is claimed until F7 is run live.
Config F7 = no gate, C_T = 0.01 (UNGATED_C_T). F8 = no gate, 0.03.

Novelty re-aimed: front-end contribution = information-weighted (Schur) soft correction with a bag-0 calibrated scale; the hard
gate is dropped. Surviving claims: label-free Otsu cut for loop factors (back end, untested on real data), frame-consistent
VIO-primary correction, benchmark + analysis of Switch-SLAM derivation errors.

Still missing: keyframe recording run (not in for_claude.zip) -> run F7 with RECORD_KF=1 and upload; Long Corridor GT.

## Update, 14 October 2026 (F7 live run + loop-closure back end on real keyframes)

**F7 live (no gate, C_T = 0.01, one run, with keyframe recorder):** full span 0.854 / 1.66 m; bag 0 0.303; bags 1-2 0.441 (VINS replay 0.780);
after VINS start 0.773 / 1.79. Replay predicted 0.76-0.80. Short-horizon RPE (held-out) is worse than VINS (0.083 vs 0.068):
the correction trades 1-s smoothness for drift. Repeats (F7 x3, F8 x3) still pending.

**Back end on the F7_kf_run1 keyframes** (505 keyframes, median 1766 points; odometry noise measured on bag 0: 1.45 deg, 0.046 m per step;
2 loop-search rounds; Huber + chi2 pruning). Full-span ATE RMSE / max (m):

| Loop information | loops | full | bag 0 | bags 1-2 |
|---|---|---|---|---|
| none (front end F7) | 0 | 0.854 / 1.66 | 0.303 | 0.441 |
| iso (LIO-SAM style, scale 1, set before seeing real data) | 139 | 0.309 / 0.64 | 0.297 | 0.309 |
| hessian (inflate 10, floor 0.5 deg / 5 cm) | 137 | 0.599 / 1.43 | 0.649 | 0.545 |
| schur / schur_otsu | 137 | 0.605 / 1.44 ; 0.603 / 1.44 | 0.657 ; 0.655 | 0.548 ; 0.547 |
| schur_gate | 110 | 0.509 / 1.31 | 0.572 | 0.441 |

Sweeps (exploratory, GT-scored): iso scale 0.03/0.1/0.3/1/3/10 -> 0.355/0.401/0.287/0.309/0.376/1.017 (sweep run) ;
fixed-loop-set re-optimisation gives 0.298/0.296/0.291/0.309/0.394/0.517. Hessian family improves as it is loosened:
inflate 10 -> 0.599 (floor 2 deg: 0.544); 100 -> 0.460 (0.412); 1000 -> 0.359 (0.335). Never better than iso.
Schur directions: translation directions dropped in 0-2 of 137 loops, rotation in 24-27: Multi Floor loops are not
translation-degenerate, so the Schur projection has nothing to remove.
Blocked 6-fold cross-validation over loops (label-free): held-out loop translation residual 0.235/0.225/0.239/0.250/0.262/0.272 m at
scale 0.03/0.1/0.3/1/3/10; picks 0.1 (GT ATE 0.296 vs best 0.291); rises on the overconfident side where ATE degrades. Curve is flat on the loose side.

**Reading.** (1) Loop closure takes 0.85 -> 0.31 m (-64%), below the challenge's best LiDAR entry (0.401, FAST-LIO2 + HBA; metric and
alignment may differ). (2) The result comes from a standard LIO-SAM-style loop weight; the degeneracy-aware loop weighting is NOT supported on
Multi Floor (worse unless made as loose as iso). Its test case is Long Corridor (needs GT). (3) Loop scale is insensitive between 0.03 and 1 and
breaks above 3 (1.0 m at 10). (4) Odometry noise was calibrated with bag-0 GT; loop search and optimisation use no GT.
Caveat: one recorded run; iso 0.287 at scale 0.3 is post hoc, quote 0.309 (scale 1) as the untuned number.
Novelty now: system-level (VIO-primary soft Schur correction + loop closure) and the analysis; label-free loop-scale CV is weak evidence only.
Next: F7 recordings x3 (RECORD_KF with REPEAT) for repeatability; Long Corridor GT + recording to test the Schur loop weighting where it should matter.

## Update, 14 October 2026 (F7 / F8 repeats, live, no gate)

Full-span ATE RMSE / max (m), one global alignment:
- F7 (C_T = 0.01): 0.91/1.82, 0.89/1.83, 0.88/1.79 (+ recorded run 0.854/1.66): mean 0.89 m, sd 0.015.
- F8 (C_T = 0.03): 0.74/1.65, 0.51/1.24, 0.54/1.20: mean 0.60 m, max mean 1.36 m (run-to-run spread larger).
- Trend with C_T (no gate): 0.003 -> 0.96, 0.01 -> 0.89, 0.03 -> 0.60. F0 1.275, Switch-SLAM 1.61 / 3.63.
- Caveat: C_T = 0.03 was run as a sensitivity point, not chosen by the bag-0 calibration rule (which picks 0.003-0.01);
  its selection uses full-span ATE on the evaluation sequence. Unbiased test = fixed C_T on Long Corridor.
- Next: F8 with keyframes x3 for the back end; F9 (C_T = 0.1) sensitivity x3; per-segment (bags 1-2) numbers from summaries.

**Back-end ablations on the F7_kf_run1 recording (iso loops, default scale).**
- Front end = VINS-Mono alone (replayed, C_T = 0): no loops 1.235 / 2.44, with loops 1.382 / 3.00 (123 loops; bag 0 0.350 -> 0.958).
  Loop closure on a drifting VINS-only trajectory makes it worse; it needs the LiDAR-corrected front end (F7: 0.854 -> 0.309).
- Wider loop search (min gap 15 s, radius 12 m): 156 loops, 0.321 / 0.64 vs 0.309 / 0.64. Extra loops are start-of-run (t = 0-29 s, robot nearly stationary); no gain. Loop search settings are not the limit.
- F7/F8 per-segment (mean of 3): bags 1-2 VINS replay 0.784, F7 0.451, F8 0.356; bag 0 0.44 / 0.44 / 0.45 (no gain on the calibration bag); 1-s RPE 0.067 -> 0.080 / 0.095.

## Update, 14 October 2026 (C_T sweep, no gate, live; full-span ATE RMSE, m, mean +- sd of n runs)

| C_T | n | full RMSE | max | bags 1-2 | 1-s RPE (VINS 0.067) |
|---|---|---|---|---|---|
| 0 (VINS only, F0) | 3 | 1.28 +- 0.02 | 2.47 | 0.75 | 0.067 |
| 0.003 (F3) | 3 | 0.96 +- 0.05 | 1.91 | 0.55 | 0.065 |
| 0.01 (F7) | 3 | 0.89 +- 0.01 | 1.81 | 0.45 | 0.081 |
| 0.03 (F8, incl. 3 recorded runs) | 6 | 0.65 +- 0.11 | 1.43 | 0.38 | 0.096 |
| 0.1 (F9) | 3 | 0.77 +- 0.23 | 1.58 | 0.45 | 0.111 |
| 0.3 (F10) | 3 | 0.68 +- 0.09 | 1.45 | 0.46 | 0.114 |

Reading: gain grows to C_T = 0.03 and then plateaus; 0.03, 0.1, 0.3 are not separable (sd 0.1-0.2). Run-to-run spread grows with C_T
(0.01 sd 0.01; 0.1 sd 0.23) and the 1-s RPE worsens (0.067 -> 0.11): the more weight on the LiDAR scan-to-map, the more it inherits A-LOAM's own
failure modes. F8's earlier three-run mean 0.60 was optimistic; six runs give 0.65. Choice for the Long Corridor test: C_T = 0.03 (middle of the plateau), fixed in advance.
The short F8_kf_run2 (2877 rows, failed the >= 3000 rule) is excluded; its rerun gave 0.73.

## Update, 14 October 2026 (loop closure on six recordings: F8 x3 at C_T 0.03, F9 x3 at C_T 0.1)

Full-span ATE RMSE / max (m), LIO-SAM-style loop weights (iso), per recording:

| Recording | front end only | 2 search rounds (old default) | 1 search round |
|---|---|---|---|
| F8_kf_run1 | 0.766 / 1.62 | 0.417 / 0.80 | 0.395 / 0.73 |
| F8_kf_run2 (rerun) | 0.731 / 1.61 | 0.300 / 0.72 | 0.306 / 0.73 |
| F8_kf_run3 | 0.619 / 1.24 | 0.846 / 2.56 (worse) | 0.356 / 0.87 |
| F9_kf_run1 | 0.512 / 1.24 | 0.271 / 0.56 | 0.272 / 0.56 |
| F9_kf_run2 | 0.851 / 1.66 | 0.477 / 0.98 | 0.470 / 0.99 |
| F9_kf_run3 | 0.944 / 1.84 | 0.321 / 0.61 | 0.327 / 0.62 |
| mean +- sd (n = 6) | 0.737 +- 0.156 | 0.439 +- 0.214 (5 of 6 improve) | 0.354 +- 0.071 (6 of 6 improve) |

- Loop correctness vs ground truth (diagnostic only): of 519 first-round loops in four recordings, 515 are good (median error 0.14 m vs about 1 m for the front end on the same pairs);
  4 are false matches about 3.3 m off (all with ICP corrections of 2.8-3.3 m, versus about 0.9 m for good loops). They do not change the ATE: removing them (oracle) gives identical scores.
- Run 3's failure with 2 rounds is in the second search round (loop search from the corrected trajectory), not a false loop. One round matches two rounds on 5 of 6 recordings and avoids that failure.
  Choosing 1 round was done after seeing this, so it is post hoc; Long Corridor is the fresh test. run_backend.py now defaults to 1 round.
- Leave-one-out consistency (re-solve without a loop and its near-duplicates, MAD z-score on the residual) flags all 4 false loops with 1-2 false rejects at z = 5, but is not needed for the ATE here.
- 5 of 6 one-round results are below the challenge's best Multi Floor entry (0.401 m); 0.470 is above. Metric and alignment of that entry may differ.

## Update, 14 October 2026 (batch 5: F8 recordings 4-6 and LiDAR-only + loops; C_T = 0.03 fixed in advance)

Three new recordings at C_T = 0.03 (F8_kf_run4-6, live full-span ATE RMSE 0.576 / 0.587 / 0.475) and one LiDAR-only recording (F4_kf_run1).
Back end: LIO-SAM-style loop weights (iso), 1 search round (default), odometry noise calibrated on bag 0.

| Recording | front end only | + iso loops, 1 round | loops | bags 1-2 (iso) |
|---|---|---|---|---|
| F8_kf_run4 | 0.576 / 1.24 | 0.360 / 0.96 | 142 | 0.354 |
| F8_kf_run5 | 0.587 / 1.24 | 0.363 / 0.75 | 130 | 0.366 |
| F8_kf_run6 | 0.475 / 1.04 | 0.303 / 0.85 | 139 | 0.296 |

**All six C_T = 0.03 recordings (F8_kf_run1-6), full-span ATE RMSE (m):** front end 0.626 +- 0.107; with loop closure **0.347 +- 0.036** (max 0.395, min 0.303);
6 of 6 improve and 6 of 6 are below the challenge's best Multi Floor value (0.401, FAST-LIO2 + HBA; metric and alignment may differ).
Wilcoxon signed-rank, front end vs loops (n = 6): p = 0.031 (smallest possible for n = 6). Live F8 over all nine live runs (no loops): 0.617 +- 0.107.
Caveat: the one-round setting was chosen after seeing the earlier recordings (post hoc), and C_T = 0.03 came from the full-span sweep on this sequence. The three new recordings
were not used for either choice and land in the same range (0.360 / 0.363 / 0.303 vs earlier F8 0.395 / 0.306 / 0.356), so repeatability holds; Long Corridor is still the unbiased test.

**LiDAR-only (A-LOAM scan-to-map, VINS-predicted) + loop closure: does not rescue it.** F4_kf_run1 live 7.752 / 14.23; with iso loops 8.181 / 15.70
(bag 0 1.255 -> 1.255, bags 1-2 4.234 -> 4.173). Only 2845 scans (< 3000 rule, so excluded from index means). The LiDAR-centred baseline is too far off
for the loop search to find or fix anything; the VIO-primary front end is what makes loop closure work (consistent with VINS-only + loops 1.235 -> 1.382).
(The 7.75 m F4 value is our own A-LOAM, not a published baseline.)

Checks: 1-s RPE (held-out) for the F8 recordings is 0.090 / 0.092 / 0.098 vs VINS 0.066 (worse, as before).
CORRECTION (same day): the summary rows "replay fused C_T = 0.03" (0.76-0.98) were replayed WITH the kappa <= 15.7 gate (fusion_summary default), not ungated. Ungated replay reproduces the live ATE exactly (0.576, 0.475), so replay arithmetic is exact; fusion_summary.py now prints both rows.

Next: Long Corridor (fresh sequence; needs bag + GT; see claude/Dataset_Test_Plan.md). C_T = 0.03 and 1 round fixed in advance.

## Update, 14 October 2026 (weighting ablation, paired replay on 12 logs; novelty review)

Replay of the same logged scan-to-map poses/Hessians with only the translation-weight rule changed (C_T = 0.03, rotation from VIO).
Held-out (bags 1-2) ATE RMSE, mean of 12 logs: ours (Schur, soft, no gate) 0.425; diagonal block 0.429 (8/12, p 0.05: no real difference);
isotropic 0.457 and constant 0.456 (ours better 11-12/12); per-direction 0/1 0.499, Switch-SLAM-rule hard switch 0.501, always-LiDAR translation 0.495
(ours better 12/12, p 0.0005, and 1-s RPE 0.095 vs 0.110); kappa(S_RR) gate 0.751 and kappa(S_RR) switch 0.788 (much worse). Full span: soft and hard tie (~0.69).
Detector rates over 12 logs: kappa(S_RR) > 15.7 in 37 % of frames, kappa(S_tt) > 10 in 0.2 %, Switch-SLAM rule 1.3-1.6 %.
Reading: soft > hard on held-out data; rotation-triggered whole-pose decisions are harmful; Schur vs diagonal does not matter on Multi Floor (translation coupling weak).
Live confirmation configs added: F11 iso, F12 switch_ss, F13 proj, F14 lidar-translation, F15 diag (WEIGHT_MODE env in fusion_node_v2).
Novelty review written to claude/Novelty_and_Research_Gap.md (gap matrix of 16 prior works; claims to make and to drop).
Long Corridor tooling: make_vins_config.py (reproduces the Multi Floor VINS config exactly), setup_sequence.sh, score_run.py, TUM ground truth support,
run_fusion_study.sh SEQ_ENV=... ; frozen settings for Long Corridor: C_T 0.03, 1 loop round, odometry noise 1.46 deg / 0.054 m from Multi Floor.
