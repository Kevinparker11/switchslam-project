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

## 9. Next runs

1. Live G20 on GEODE (PC, 0.5x, 2 runs) and Multi Floor (laptop, 1.0x, 2 runs): confirm the node matches the replay (G20 must equal G19 on Multi Floor and improve GEODE).
2. Gazebo office hallway and empty world with G18 / G19 / G20 / G21, 3 runs each.
