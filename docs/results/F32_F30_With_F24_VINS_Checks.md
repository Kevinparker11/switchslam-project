# F32: F30 with F24's VINS-Mono failure checks (10 Nov 2026), rules written before any run

## Why
F30 (Switch-SLAM structure and output, our R / T / additional-T detection, the paper's VINS-Mono failure test) gave 13.04 and 195.58 m on GEODE, against F26 3.26 to 6.36 m. The run 2 log shows the divergence starting while VINS-Mono's steps were about 9 times the LiDAR's (median 1.18 m against 0.127 m) and were not flagged, because the paper-style test only fires above 5 m or 50 degrees (F30 doc). F24 and F26 reject such a VINS-Mono with a 1 m / 0.5 rad step guard and a scale-consistency gate. F32 gives F30 those two checks and changes nothing else. Goal set by the user: LiDAR odometry primary, results close to F26.

## What changes against F30
VINS-Mono counts as failed in Algorithm 1 (so the guess is the LiDAR's and a degenerate scan takes Eq. 16 line 2, the LiDAR along its well-conditioned directions only) when any of:
- the paper's own conditions (no pose for 1 s);
- a VINS-Mono step above **1 m** or **0.5 rad** between two scans (F24's `JUMP_MAX` and rotation guard, instead of 5 m / 50 degrees);
- F24's scale-consistency gate is closed: ln(|VINS motion| / |LiDAR motion|) over 10 s windows, segment RMS above **0.157**, or the last-5 s RMS above **0.277** (F24's `VIO_CHECK_REF`, `VIO_CHECK_FAST_REF`, calibrated on Multi Floor), trusted at the start of a segment (`VIO_CHECK_START=1`), reset when VINS-Mono is lost.
Everything else is F30: A-LOAM's pose is the output, the guess and the remap are Switch-SLAM's, the detection is our R (kappa 15.7), T (c_T 0.03) and additional T (min rule). All constants are F24's frozen values, none set for this test. Config `F32`; 20 detector and core tests pass, F30 unchanged (default values reproduce it).

## Runs (batches/f32_mf_geode.sh, about 47 min)
Multi Floor F30 run 1, Multi Floor F32 run 1, GEODE F32 run 1.

## Predictions written before the runs
- Multi Floor: VINS-Mono is consistent there (the gates were calibrated on it), so F32 should be close to F30. Whether either is close to F26 (0.54, n=1; F24 0.45 to 1.01, n=3) depends on the LiDAR-primary output itself, not on the checks. For context, the paper-rule replica SW gave 5.03 m on Multi Floor and A-LOAM alone 26.4 m in this stack.
- GEODE: with the checks, the bad VINS-Mono stretches become "failed", the run should behave like A-LOAM with its own guess, and the result should move toward F26 (3.26 to 6.36), which on GEODE is also close to A-LOAM.

## Reading rules
1. "Close to F26": on Multi Floor inside the F24 / F26 spread (0.45 to 1.01 m); on GEODE inside F26's range (3.26 to 6.36 m). Below these: "lower"; above: "higher".
2. n = 1 per bag supports no claim; a failed run counts.
3. Development data (Multi Floor is the calibration bag for the gates; GEODE is tuned-on data for F25 to F27). Adoption needs held-out bags and a rule written first.
4. Report from the log: share of scans with VINS-Mono failed (sw_vo_fail), vio_gamma closed, guess kinds and output branches.

## Result: Multi Floor run 1 (10 Nov 2026)
ATE RMSE / max = **6.05 / 12.48 m** (4041 poses, GT path 272.6 m). Additional-T precondition met (tensor for 4133 scans, missing 5). Reading rule 1: higher than the F24 / F26 range (0.45 to 1.01 m). For context: F26 0.54 m, Switch-SLAM replica SW 5.03 and 5.44 m, A-LOAM alone 26.4 m, VINS-Mono alone in this run 1.30 m.

From the log (`fusion_v4/offline_f32_diag.py`): R fired on 37.3 % of scans, T on 0.0 %, the additional T on 9.8 %, degenerate branch 46.4 %; output branches: full LiDAR step 2170, Eq. 15 fusion 1679, degenerate with VINS failed 199; VINS-Mono flagged failed on 5.0 % (all by the 1 m / 0.5 rad step guard; the scale gate never closed on Multi Floor, as predicted). The output equals A-LOAM's pose (both 6.05 m).

Where the error comes from: heading. Start-referenced heading error against ground truth: F32 12.6 deg at 100 s, 34.8 deg at 200 s, 32.4 deg at 300 s; F26 in its first run 5.9, 1.9, 1.2 deg. The 10 s rotation error has median 1.89 deg (F26 1.05 deg), 90th percentile 7.03 deg (F26 3.10 deg). F26 takes its rotation from VINS-Mono (c_R = 0) and anchors heading to wall structure (SAH); F32 outputs A-LOAM's rotation, which on Multi Floor drifts. The VINS checks are not the cause on this bag. Reading: one run; the heading figures are a log measure (Euler yaw, start-referenced), not a separate test.
