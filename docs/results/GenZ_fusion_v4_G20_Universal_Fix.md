# G20: a safety fix that keeps every good result and removes two failure modes (24 Oct 2026)

Metric: full-span ATE RMSE (m), Umeyama SE(3), no scale. All numbers are **exact offline replays** on 33 recorded GenZ-stack runs (GenZ-LIO and VINS-Mono take no feedback from the fusion, so a replay equals a live run; the replayed G19 reproduces all 15 healthy live G19 runs within 1 cm, and the unchanged G17 / G18 / G19 paths reproduce bit for bit after every code change below). Scripts: `analysis/improve/universal/`; tables and loop-closure outputs: `results_data/2026-10-24/`.

Recordings: Multi Floor 10 (MF-a1..a4 = the four calibration recordings of 21 Oct; MF-b1..b6 = the live G19 runs of 23 Oct, b2 is the run in which GenZ-LIO itself diverged), Long Corridor 6 (3 frozen GenZ config, 3 authors' config), Corridor02 1, Cave02 2, GEODE stairs α 14 (PC, 0.5x and 1.0x).

## 1. Where the method excels and where it lags (before the fix)

| Sequence | GenZ-LIO alone | Best fused front end | G19 | G19 + loops | Best published | Status |
|---|---|---|---|---|---|---|
| Long Corridor (clean test) | 1.96 | G19 1.73 | 1.73 | **1.41** | 0.82 SuperLoc, 1.25 challenge (loops), 1.55 iG-LIO, 1.90 GenZ-LIO | below Switch-SLAM (2.42), GenZ-LIO, FAST-LIO2; tie with iG-LIO / LODESTAR; above SuperLoc |
| Multi Floor | 0.53 | G17 / G18 0.30 | 0.36 | 0.32 | 0.25 iG-LIO, 0.26 GenZ-LIO | tie band, not below |
| Cave02 | 0.30 | GenZ / G19 0.31 | 0.31 | **0.30** | 0.43 | below (= front end) |
| GEODE α | 0.36 | GenZ 0.36 | 0.55 | 0.36 | 0.57 RELEAD | below, but G19 is worse than its own input |
| Corridor02 | 2.70 | G17 1.88 | 2.48 | 2.35 | 0.69 (sequence identity unconfirmed) | above |
| Multi Floor run 2 (GenZ diverged) | 5093 | G17 4.9 | **1113** | 1111 | | G19 follows the diverging LiDAR |

## 2. Diagnosis from the logs

1. **The LiDAR is the better speed reference everywhere.** Against ground truth, GenZ-LIO's 10 s displacement error is 0.9-4.4 % on every sequence, VINS-Mono's 4-6 % (healthy), 29 % (Cave02) and 240 % (GEODE). GenZ path length matches GT within 2.5 % (median per recording) on all sequences, corridors included. (`diag_scale.py`, `diag_speed.py`)
2. **Why G19 helps on Long Corridor.** The scan Hessian gives little information along the corridor (c_T u'S_tt u about 0.75, against 2-4.8 elsewhere), so the T channel takes about 57 % of the along-track motion from VINS. GenZ-LIO is IMU-aided and is not degenerate there, so G19's 10 s speed matching returns the LiDAR's better speed. A robust whole-segment scale (U0) does **not** help (2.1-3.7): the benefit is local speed matching, not a constant scale bias.
3. **Speed matching is a trade-off, not a fix.** Every speed-matching variant tried (10 s path, 10/30 s chord median, projected, along-track only) helps Long Corridor and costs Multi Floor (0.30 to 0.35-0.38); all but one (30 s chord, which helps Long Corridor least) also cost Corridor02 (1.9 to 2.5). No variant wins on all three, so none is part of the fix.
4. **Corridor02's ground truth is suspect.** The speed errors of LiDAR and VINS against GT are 0.82 correlated on Corridor02 and about 0 everywhere else. Two independent sensors erring together points to the GT (registration against a prior map in a degenerate corridor). Corridor02 numbers are reported but not used to choose anything.
5. **GEODE: trust earned too fast.** The VINS agrees with the LiDAR for the first ~20 s (segment r = 0.049 at 200 windows), the gate opens at 44 s, the VINS then degrades and the segment-level statistic needs ~10 s to close the gate. G19 ends 0.19 m (median) above GenZ-LIO alone; the fast check below recovers 0.07 m of that.
6. **Multi Floor run 2: the scale correction amplifies a LiDAR failure.** From 333 s GenZ-LIO accelerates (0.05 to 18 m per scan) while VINS stays at walking speed. G19's scale ratio (LiDAR path / VINS path) follows it to 375x. The consistency gate also blames the VINS, because it treats every disagreement as a VINS fault.

## 3. The fix (G20), structure unchanged (R channel, T channel, SAH)

| Part | What it does | Constant and where it comes from |
|---|---|---|
| Fast companion check | A second consistency check over the windows that ended in the last 5 s; γ = the smaller of the two checks. A VINS that goes wrong after earning trust is dropped within seconds. | 0.278 = largest 5 s value on MF-a1..a4 (same rule as 0.156) |
| LiDAR blow-up guard | While the VINS has a good long-run record (slow check open), a LiDAR path that outruns the raw VINS path by more than 2.16 m in 2 s marks the LiDAR step as failed: the VINS carries it, the statistics are not fed, and the scale is rolled back to its value before the excess began. | 2.16 m = 3 x the largest 2 s excess on MF-a1..a4 (0.72 m) |
| (G21 only) VINS information floor | γ ≥ 1e-3, so a truly degenerate LiDAR direction is never trusted fully when the gate is closed. Changes the 33 real results by ≤ 3 mm; kept out of G20 because no recording can show its benefit. | 1e-3 (design value) |

Node switches: `VIO_CHECK_FAST=5 LIDAR_GUARD_T=2` (G20), plus `GAMMA_MIN=1e-3` (G21). Defaults off; G0-G19 and the A-LOAM master are unchanged.

## 4. Results on all 33 recordings

| Sequence (recordings) | GenZ alone | G17 | G18 | G19 | **G20** |
|---|---|---|---|---|---|
| Multi Floor (9, b2 excluded) | 0.525 | 0.304 | 0.306 | 0.357 | **0.357** |
| Long Corridor (6) | 2.036 | 2.776 | 2.658 | 1.763 | **1.763** |
| Corridor02 (1) | 2.696 | 1.881 | 1.967 | 2.484 | **2.481** |
| Cave02 (2) | 0.301 | 4.695 | 0.427 | 0.306 | **0.306** |
| GEODE α (14) | 0.355 | 17.56 | 1.145 | 0.545 | **0.475** |
| Multi Floor run 2 (GenZ diverged) | 5093 | 4.91 | 4.91 | 1113 | **1.46** |

Medians per sequence. **G20 against G19, recording by recording: better on 12, identical on 21, worse on none.** The guard never fires on the 32 healthy recordings; the fast check only acts on GEODE.

With the loop-closure back end (iso, 1 round, odometry noise 1.46°, 0.054 m as for every earlier loop result):

| | G19 + loops | G20 + loops |
|---|---|---|
| GEODE α (14), median | 0.359 | **0.322** (better on 10, worse on 0) |
| Multi Floor run 2 | 1111 | **1.75** |
| all other recordings | unchanged (G20 = G19) | Long Corridor 1.41, Multi Floor 0.32, Cave02 0.30 |

## 5. What the fix does not do

- It does not lower Multi Floor, Long Corridor or Corridor02. The remaining gap there is (a) the speed-matching trade-off above and (b) the front end: our GenZ-LIO alone reaches 0.53 on Multi Floor and 2.70 on Corridor02 where the GenZ-LIO paper reports 0.26 and 0.69, while on Long Corridor (1.96 vs 1.90) and Cave02 (0.30 vs 0.44) it matches or beats the paper. The Multi Floor and Corridor02 front-end gap (configuration, extrinsics, ground-truth file and alignment) is the largest lever left and is not a fusion question.
- On GEODE G20 is still above GenZ-LIO alone (0.475 vs 0.355; with loops 0.32 vs about 0.25): the gate still opens for the first seconds of a VINS segment that later fails.

## 6. Variants tried and rejected (all in `configs.py`, results in `table_all.txt`)

| Variant | Idea | Why rejected |
|---|---|---|
| U0 | robust whole-segment scale (median of window ratios) | Long Corridor 3.44 (from 1.76) |
| U1, U3 | test on the spread about the median (scale bias removed), gate / covariance-matching weight | Cave02 1.0-1.3 (from 0.31): a de-biased VINS still is not good there; GEODE 1.3-2.6 |
| L10, L30, A10 | local chord scale (10 / 30 s), along-track only | trade-off: helps Long Corridor less than G19, still costs Multi Floor |
| G19p, A19p | scale from LiDAR-constrained motion only | Long Corridor 1.55 (better) but Multi Floor 0.38 (worse): trade-off |
| F10 | fast check over 10 s | weaker than 5 s on GEODE (0.511 vs 0.475), same elsewhere |
| guard on scale-corrected VINS | | the failing LiDAR feeds the scale before the guard fires (5.3 m error in the unit test); replaced by raw VINS + roll-back |

## 7. Status and honest reading

- **Development result.** G20 was designed on these 33 recordings after seeing them. Its two new constants come only from the four Multi Floor calibration recordings, by the same rule as 0.156, and the guard margin (3x) was fixed before testing; but the choice of what to add was made with all sequences in view. Long Corridor is no longer an untouched test.
- **Why it is called universal.** Both parts only act when one source is demonstrably failing, so on healthy data G20 is G19 exactly (21 of 33 recordings identical, the rest better). That property (never worse than G19) holds on every recording available; it still has to be shown on data not used here: a live run of G20, new bags, and the Gazebo worlds below.

## 8. Gazebo tests (simulation, exact ground truth)

Already in the LiDAR container: `cpr_gazebo` (Clearpath) with the Husky (VLP-16, camera, 200 Hz IMU) used in the generation-1 farm study.

| World (package) | What it stresses | Expected behaviour to check |
|---|---|---|
| Office hallway (`cpr_office_gazebo`) | indoor corridor, LiDAR weak along the axis | G19/G20 speed matching vs G18; exact GT removes the Corridor02 doubt |
| Construction (`cpr_office_gazebo`) | clutter, partial walls | registration quality, SAH with irregular walls |
| Inspection (`cpr_inspection_gazebo`) | hills, bridge, pipeline, cave/mine | vertical motion, cave-like section |
| Agriculture / solar farm (`cpr_agriculture_gazebo`) | repetitive rows | only Hessian statistics were checked in Sept, never ATE with the G configurations |
| Empty world (`husky_gazebo`) | no structure: LiDAR useless | VINS must carry everything; tests the guard and the information floor (G21) |
| Custom: long uniform tunnel, dark/textureless room | pure axial degeneracy / VINS failure | the two failure directions in isolation |
| AWS RoboMaker house / hospital / warehouse (ros1 branches, tested by AWS on Gazebo 7/9) | indoor rooms, corridors, aisles | may need small fixes on Gazebo 11 |

Simulation-specific issues to handle first:
1. The Gazebo Velodyne plugin publishes x, y, z, intensity, ring and **no per-point time**; GenZ-LIO deskews with per-point time. Add a zero `time` field (Gazebo scans have no motion distortion) or disable deskew, and check with `fusion_v4/genz/check_bag_fields.sh`.
2. Simulated scans have no motion distortion and noise-free returns, and textures are repetitive: both sensors can look better or worse than reality. Report simulation results separately from real data.
3. A wheeled robot on flat ground at constant speed makes monocular scale weakly observable: expect VINS scale drift (exercises the gate and scale correction).
4. Record bags (LiDAR, IMU, camera, `/gazebo/model_states` ground truth) and run them through the same `setup_sequence.sh` / `run_fusion_study.sh` pipeline, so simulation and real runs share every step after the sensors.

## 9. Live confirmation of G20 (laptop, 24 Oct 2026, 17:50-20:23)

Commit 4579ed2, the frozen G20 settings (`VIO_CHECK_FAST=5 LIDAR_GUARD_T=2`), RECORD_KF=1: Multi Floor 4 runs at 1.0x, Long Corridor 4 runs at 0.5x (frozen config), Cave02 2 runs at 0.5x. Each recording was also replayed with GenZ-LIO alone, G17, G18 and G19 (the GenZ-LIO and VINS-Mono outputs are shared). Full-span ATE RMSE (m):

| Run | GenZ-LIO alone | G17 | G18 | G19 | G20 replay | **G20 live** |
|---|---|---|---|---|---|---|
| Multi Floor 1 | 0.446 | 0.256 | 0.251 | 0.257 | 0.257 | **0.26** |
| Multi Floor 2 | 0.446 | 0.293 | 0.297 | 0.320 | 0.320 | **0.32** |
| Multi Floor 3 | 0.446 | 0.253 | 0.253 | 0.264 | 0.264 | **0.26** |
| Multi Floor 4 | 0.512 | 0.400 | 0.394 | 0.384 | 0.384 | **0.38** |
| Long Corridor 1 | 1.923 | 2.815 | 2.696 | 1.746 | 1.746 | **1.75** |
| Long Corridor 2 | 1.984 | 1.418 | 1.474 | 1.643 | 1.643 | **1.64** |
| Long Corridor 3 | 1.984 | 1.388 | 1.442 | 1.636 | 1.636 | **1.64** |
| Long Corridor 4 | 1.990 | 1.417 | 1.466 | 1.668 | 1.668 | **1.67** |
| Cave02 1 | 0.283 | 3.803 | 0.514 | 0.297 | 0.297 | **0.30** |
| Cave02 2 | 0.283 | 4.213 | 0.341 | 0.284 | 0.284 | **0.28** |

Medians: Multi Floor GenZ 0.446, G17 0.274, G19 = G20 0.292; Long Corridor GenZ 1.984, G17 1.418, G19 = G20 1.656; Cave02 GenZ 0.283, G19 = G20 0.291.

- **The live node equals the replay** on all 10 recordings (every difference is below the 0.01 m rounding of the live log), and **G20 equals G19 to the last digit on all 10**: the fast check and the guard never acted on healthy data, as designed. Together with the earlier 32 healthy recordings this is 42 recordings on which G20 = G19 or better, none worse.
- G20 beats GenZ-LIO alone on 4 of 4 Multi Floor and 4 of 4 Long Corridor recordings; on Cave02 it ties (0.297 / 0.284 against 0.283, inside the 0.1 m tie band).
- **What stays open.** (a) Long Corridor: G17 (no gate, no scale correction) is better than G19 / G20 on 3 of these 4 recordings (1.39-1.42 against 1.64-1.67) but 2.8 on the first; its 6-recording median earlier was 2.78, so it is high-variance, and G19 / G20 is the stable choice, not the best on every run. (b) The guard did not fire live because GenZ-LIO did not diverge in these 10 runs; its live action is shown only by the replay of Multi Floor run 2 (1113 to 1.46 m) and the unit test. (c) GEODE (PC) has no live G20 run; its 0.545 to 0.475 gain is a replay result.

Data: `results_data/2026-10-24/live_g20/`.

## 10. Gazebo office: a clean world where the fusion costs accuracy (25 Oct 2026)

Clearpath office world (44 x 25 m open floor with thin partition walls, a ~10 m hallway about 1.5 m wide), Husky, VLP-16 (1800 samples per ring), forward 640x480 mono camera, 200 Hz IMU, exact pose. One 639 s recording (2 laps of a 134 m planned route, 266 m driven, 0.5 m/s) replayed 4 times at 1.0x with G20 live (`fusion_v4/gazebo/`). The plugin writes per-point time = 0, so GenZ-LIO rebuilds the time from the azimuth (a false deskew: Gazebo samples all rays at one instant). Main data: the per-point time replaced by an azimuth ramp over 0.1 ms (3 runs, no GenZ warnings); sensitivity: the plugin time as recorded (1 run). The variant was chosen on this physical argument, before the scores were seen.

Full-span ATE (m), exact replay (the live G20 matches the replay within 0.01 m on the three ramp runs; 0.86 live against 0.82 replay on the plugin run):

| Run | GenZ-LIO alone | G17 | G18 | G19 | G20 | G20 live |
|---|---|---|---|---|---|---|
| ramp 1 (GenZ-LIO drifted) | 1.015 | 0.445 | 0.517 | 0.316 | 0.319 | 0.32 |
| ramp 2 | 0.141 | 0.474 | 0.477 | 0.449 | 0.449 | 0.45 |
| ramp 3 | 0.141 | 0.489 | 0.492 | 0.468 | 0.468 | 0.47 |
| plugin time | 0.493 | 0.819 | 0.812 | 0.752 | 0.816 | 0.86 |

- **Where the fusion loses.** On the two runs where GenZ-LIO alone is excellent (0.141 m over 266 m) every fusion variant is about 3x worse (0.45-0.49). When GenZ-LIO drifted (run 1) the fusion rescues it (0.32 against 1.015). VINS-Mono alone gives 0.75-0.78. The runs 2 and 3 of GenZ-LIO are bit-identical: not independent samples.
- **G20 is not identical to G19 here**: 3 mm worse on ramp 1 and **6 cm worse (0.816 against 0.752) on the plugin-time run**, where the fast check closes the gate on some windows. The "never worse than G19" property of section 7 therefore holds on the 42 real recordings only.
- **Channel split** (replay, ramp 2): LiDAR in both channels 0.141 (reproduces GenZ-LIO), + SAH 0.149, rotation channel only 0.177, **translation channel only 0.469**, both channels without SAH 0.458. The T channel (VINS-Mono translation increments) is the source of the loss; on ramp 1 the same channel is what rescues the run (0.640 with it off, 0.481 with it on). On the plugin-time run SAH alone costs 0.49 to 1.07 (a separate sensitivity of the structure heading to the false deskew).
- **Not a scale mismatch.** The median LiDAR translation information is of the same size in every environment (c_T x S_tt eigenvalues: Multi Floor 2.5 / 6.4 / 14, Long Corridor 0.4 / 16 / 38, Cave02 1.9 / 7.9 / 25, GEODE 1.8 / 4.9 / 10, Gazebo 1.7 / 5.5 / 24; min / mid / max), so the weight VINS-Mono gets (about 35 % along the weakest direction) is similar everywhere. What differs is how good GenZ-LIO is relative to VINS-Mono: the scan Hessian does not know that GenZ-LIO is IMU-aided.

## 11. Sensitivity of the T-channel scale c_T, and the G22 candidate (25 Oct 2026)

G20 settings, c_T varied (frozen value 3e-6, calibrated on the four Multi Floor recordings), replayed on all 47 recordings (45 real + 3 Gazebo ramp runs, Multi Floor run 2 excluded from medians). Median ATE (m):

| Sequence (n) | GenZ-LIO alone | c_T / 3 | **3e-6 (G20)** | **1e-5 (G22)** | 3e-5 | 1e-4 |
|---|---|---|---|---|---|---|
| Multi Floor (13) | 0.446 | 0.425 | **0.346** | 0.356 | 0.393 | 0.416 |
| Long Corridor (10) | 1.987 | 1.800 | 1.707 | **1.551** | 1.459 | 1.419 |
| Cave02 (4) | 0.283 | 0.315 | 0.296 | 0.287 | 0.285 | 0.284 |
| Corridor02 (1) | 2.696 | 3.131 | 2.481 | 2.197 | 2.213 | 2.250 |
| GEODE (14) | 0.355 | 0.610 | 0.475 | **0.394** | 0.365 | 0.356 |
| Gazebo ramp (3) | 0.141 (2 of 3), 1.015 | 0.559 | 0.449 | **0.305** | 0.219 | 0.186 |

Multi Floor, the sequence c_T was calibrated on, is the only one that prefers the current value; every other sequence improves with a larger one, and at 1e-4 the fusion approaches GenZ-LIO alone wherever that is good (GEODE 0.356 against 0.355) while still rescuing the drifting runs (Gazebo ramp 1: 0.224 against 1.015; Multi Floor run 2 stays at 1.6 m).

**G22 = G20 with c_T = 1e-5** (3.3x), frozen on 25 Oct 2026 (`run_fusion_study.sh G22`, `GENZ_C_T_G22` overrides). It is the largest step that keeps the calibration sequence within 0.01 m of G20 (Multi Floor median 0.346 to 0.356); 3e-5 already costs 0.047 on Multi Floor. Against G20, recording by recording (45 real recordings, a change counts above 0.05 m and 10 %): better on 15 (GEODE 11 of 14, Long Corridor 3 of 10, Corridor02 1), worse on 2 (Multi Floor MF-a2 0.49 to 0.63 and MF-b1 0.65 to 0.78), unchanged on 28. The Gazebo ramp runs improve from 0.449 to 0.305.

**Honest status.** This is an in-sample choice: the effect of c_T was seen on every recording before G22 was fixed, and the Multi Floor calibration recordings are among the ones that get worse. It is a development result until confirmed on recordings not used here (a new Gazebo world recorded before looking at any score, any new real bag). c_T does not fix the cause (the scan Hessian underrates an IMU-aided LiDAR) but moves the constant to a value that costs the calibration sequence 0.01 m and helps the others. The G20 fast check and guard are unchanged by G22.

Data: `results_data/2026-10-25/gazebo_office/` (batch log, replay JSONs, tables); scripts `analysis/improve/universal/` (`logs_all.py` has the four Gazebo recordings, `configs.py` D1-D5 and S03-S30).

## 12. Next runs

1. Held-out confirmation of G22 against G20: a second Gazebo world recorded and run before any score is looked at (construction or inspection), and the next real bag; G20 and G22 on the same recordings (replay is exact, one live G20 or G22 run per recording is enough).
2. Live G20 on GEODE (PC, 0.5x, 2 runs): needs the PC; the gain is replay-only until then.
3. Hypothesis-test table from the recordings (paired design, Holm), reporting G20 and G22 separately.
