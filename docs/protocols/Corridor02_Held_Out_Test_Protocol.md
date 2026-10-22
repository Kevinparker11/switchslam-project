# Corridor02 held-out test: protocol written before the scored runs (15 October 2026)

## Why
Long Corridor became a development sequence after the heading-drift analysis (see Long_Corridor_Setup_Log.md). Corridor02 (SubT-MRS Hawkins, RC1, `corridor02.bag`, 893 s, ground-truth path 695 m, start and end 2.7 m apart) has not been used for any design or setting decision.

## Frozen before the runs
- Method and code: fusion_node_v2 / FusionCore as shipped in fusion_v3.zip (rotation drift filter and other experiments are OFF: tau_R = 0, C_R = 0).
- Settings: C_T = 0.03, KAPPA_TH = 1e9 (ours), W_ALPHA = 0.7, WARMUP 20 s, hard-switch KAPPA_TH = 15.7 for F12; VINS-Mono IMU noise and tracker settings copied from Multi Floor; camera/IMU extrinsics and intrinsics from the published calibration files (corridor02_extrinsics.yaml, corridor02_Intrinsics.yaml).
- Back end (loop closure): iso loop weights, one search round, odometry noise 1.46 deg / 0.054 m, all frozen from Multi Floor bag 0; same loop-search and ICP-verification thresholds as for Long Corridor.
- Configurations, 3 runs each: F8 (ours, with keyframes), F0 (VINS-Mono only), F5 (A-LOAM only), F12 (hard switch), F14 (LiDAR translation always).
- Metric: ATE RMSE and max, Umeyama SE(3) without scale, full span, own scorer (score_run.py), exactly as for Multi Floor and Long Corridor. Ties below about 0.1-0.3 m are treated as ties.

## Facts established before running (no run results involved)
- Clock: header stamps (LiDAR 1645999726.28) and ground-truth span (1645999727.0 to 1646000619.7) agree with the bag's span on the header clock; no time shift needed. The record-time check in setup_sequence.sh reports "NO OVERLAP" because record times are August 2024; this is not used.
- Start: the platform is stationary for about 70 s (ground truth 0.0 m, IMU std 0.017 m/s2 / 0.001 rad/s), moves about 1.4 m in 70-100 s, then is still again. VINS-Mono initialises at 75.9 s into the 190 s smoke test, first FUSED row at 96.0 s. All methods are scored over their own logged span.
- Image topic /camera_1/image_raw, 640x480 bgr8, no gaps; LiDAR /velodyne_points PointCloud2 at about 10 Hz (no packet conversion).

## What will be reported, whatever the outcome
Per-run ATE for every configuration before and after loop closure; comparison with published numbers only where a published number for Corridor02 can be cited (to be looked up, none assumed). If a pipeline bug (topic, clock, container) is found, it is reported and fixed without touching any method setting, and the affected runs are repeated; no setting is tuned on this sequence.

---

# Results (17 October 2026), all 15 runs, replay at 0.33x, settings frozen as above, nothing tuned on this sequence

ATE RMSE in metres (Umeyama SE(3), no scale, full span), 3 runs each, front end only (no loop closure yet).
| Config | Runs | Mean +- sd | Rows per run |
|---|---|---|---|
| F8 ours (soft Schur weight, rotation from VINS) | 2.07, 2.10, 2.19 | 2.12 +- 0.06 | 8214-8266 |
| F12 hard switch (Switch-SLAM detection rule) | 2.17, 1.65, 1.80 | 1.87 +- 0.27 | 8243-8282 |
| F14 LiDAR translation always (W = I) | 1.67, 1.76, 1.78 | 1.74 +- 0.06 | 8194-8246 |
| F0 VINS-Mono alone | 4.03, 4.02, 4.03 | 4.03 +- 0.01 | 8191-8219 |
| F5 A-LOAM alone (no VINS prediction) | 58.57, 46.53, 92.95 | 66 +- 24 | 6763-7592 |
Max errors: F8 3.69-3.88, F12 2.93-3.78, F14 2.81-3.18, F0 6.73-6.76.

## Reading
- Clear: the fused variants (F8, F12, F14) are about half the error of VINS alone (4.03) and far better than A-LOAM alone.
- Not as hoped: always trusting LiDAR translation (F14, 1.74) beats our soft weighting (F8, 2.12) by about 0.4 m, more than the ties allowance and larger than either sd; the hard switch (F12, 1.87 +- 0.27) is on average also ahead but not separable from F8 with three runs. On Long Corridor the order was the reverse (F8 4.53, F12 5.43, F14 13.2 +- 8.7). No fixed choice wins on both sequences; F8 is the only one never worst among the fused variants, F14 is best here and catastrophic there. This does not support a claim that the soft weighting is best everywhere.
- F5 is compute-starved: 6763-7592 rows (10-24 % of scans skipped) against about 8200 for the others, so its numbers say little about A-LOAM's accuracy; it is reported with its row counts.

## Conditions to disclose
- Replay at 0.33x because at 1.0x the laptop (Ryzen 5 5600H, mapping node saturating one core at 93 C) dropped about 40 % of scans (first attempt: 8 runs of 4628-5554 rows, discarded as below the pre-set row threshold; kept in ~/runs_corridor2/attempt1_rate1.0). The rate was chosen from the row rates alone, before any error value was looked at. At 0.33x F8 still loses about 20 % of scans in bag minutes 8-11 (454-555 rows against 595); a sensitivity run at 0.2x is planned.
- Corridor02 starts with the platform standing still for about 70 s; VINS-Mono initialises 75.9 s into the bag, first fused row at 96 s.
- No published result for Corridor02 was found (SuperLoc, arXiv 2412.02901, uses a "Corridor02" of its own, not SubT-MRS; the SubT-MRS paper and challenge tables list Long Corridor = Corridor01 only). Same-sequence published figures therefore do not exist for this test; the comparison is with our own baselines.
- For Long Corridor (Corridor01) a newer published value exists: SuperLoc reports ATE 0.817 on Corridor01 (arXiv 2412.02901, Table III, as read by an automated summary of the PDF; to be checked against the paper before citing), below the 1.254 challenge best used earlier.

---

# Log analysis after receiving for_claude8.zip (17 October 2026; no ground-truth file on my side, so only what the logs and the scorer output contain)

## Start-to-end gap of each logged trajectory (true gap 2.77 m, ground-truth path 695 m)
| Trajectory | gap (m), 3 runs |
|---|---|
| VINS-Mono alone | 13.0, 13.0, 13.1 |
| F8 fused | 4.54, 4.66, 5.04 |
| F12 fused | 4.46, 2.70, 3.28 |
| F14 fused | 3.30, 3.50, 3.27 |
Unlike Long Corridor (fused 21-25 m, caused by VINS-Mono heading drift), the fused trajectories here return close to the start: no large heading drift on Corridor02. The remaining 2 m RMSE is smaller-scale drift and noise.

## Weights actually used
- F8: gate open 100 % of the FUSED rows; median eigenvalues of the LiDAR translation weight 0.74 / 0.81 / 0.91, so 9-26 % of each translation increment still came from VINS-Mono on a sequence where LiDAR translation is well constrained.
- F12 (hard switch): LiDAR fully trusted in 47 % of the FUSED rows, VINS-only in the other 53 %.
- F14: LiDAR translation 100 %.
- Offline replay on the same logged data (summary_*.txt): the hard-switch rule gives 1.75-1.95 m on every log, the soft weighting 2.07-2.19 on its own logs and 2.0-2.7 on the others, so the 0.2-0.3 m advantage of the hard switch over F8 on this sequence is systematic, not run noise. Replaying the logged A-LOAM map pose as a LiDAR-only trajectory gives 1.48 / 3.78 / 4.18 m on the three F8 logs: it depends on the seed of the run, so it is not a stable alternative.
- VINS-Mono is the best locally (RPE 1 s 0.107 versus 0.171 for LiDAR and 0.140 for F8) but drifts globally (ATE 4.03 m).

## Not done, on purpose
No constant was changed after seeing these numbers. A smaller shrinkage constant would move F8 towards F14 on this sequence, but C_T = 0.03 was fixed on Multi Floor bag 0, and re-choosing it here would turn Corridor02 into a development sequence. Any change to the method needs a third untouched sequence.

---

# Loop-closure back end on the three F8 runs (17 October 2026), settings frozen from Multi Floor (iso weights, odometry noise 1.46 deg / 0.054 m, 8 m search radius, one round)

| Run | front end | after loop closure (iso) | accepted loops |
|---|---|---|---|
| F8_kf_run1 | 2.067 / 3.69 | 2.009 / 3.48 | 17 |
| F8_kf_run2 | 2.099 / 3.72 | 2.085 / 3.57 | 21 |
| F8_kf_run3 | 2.192 / 3.88 | 2.198 / 3.90 | 13 |
| mean | 2.119 | 2.097 | |

Loop closure changes the error by -0.06, -0.01 and +0.01 m: no measurable effect on Corridor02 (on Long Corridor it took 4.53 to 2.67 because the front-end drift there was large). The first twelve listed loops of every run connect t = 0 with t = 74-91 s, i.e. the stationary start (the platform stands still for about 70 s), so they are same-place matches with no drift to correct; the others are local revisits (84-89 s <-> 142-144 s, 323 s <-> 358-359 s). The list is cut at twelve, so I cannot say whether a start-to-end loop is among the remaining ones. backend_multi.py printed an empty table because its regex could not read the "nan" columns; fixed (the numbers above come from backend_F8_kf_run*.log).
