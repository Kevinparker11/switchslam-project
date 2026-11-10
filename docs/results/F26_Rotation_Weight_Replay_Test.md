# F26: does a LiDAR rotation weight (the R channel) change the output? Open-loop replay, rules written before any run (10 Nov 2026)

## Question
In F26 the LiDAR rotation weight constant c_R is 0, so the output rotation is VINS-Mono's and the R Schur channel acts only through the rotation check, which closed on 0.0 % of fused scans on four bags and 3.6 % on GEODE. Would raising c_R, so that the LiDAR contributes rotation in the directions where its Schur information is high, help?
Earlier evidence (Configurations_Explained_and_Results_To_Date.md, 6.3, an older design with the same weight form): an active rotation weight from c_R = 0.003 made Multi Floor (0.62 to 1.3 to 2.0 m), Corridor02 (2.2 to 3.4 to 4.1) and Cave02 (4.5 to 5.7 to 8.8) worse and Long Corridor better (4.5 to 1.9). This test repeats the question on the F26 logs.

## Method
The real `fusion_node_v2` callbacks are driven offline (`ot_study/round3/node_harness.py`, `SAH_SYNC=1`) by the logged F26 runs and their keyframe scans, with F26's settings and one change, `C_R`:
- logs: Multi Floor run 1, Long Corridor run 1, Corridor02 runs 1 and 2, Cave02 run 1, GEODE runs 1 to 3 (all F26, live, 0.5x or 0.33x as recorded);
- grid: C_R in {0 (control), 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3} (the earlier protocol's grid plus 3e-3);
- score: ATE RMSE / max of the fused output against ground truth, Umeyama SE(3), no scale, full span, the same scorer as the live runs.
Limits, stated now: it is open loop. A-LOAM's poses and Hessians are the logged ones, so a changed output cannot change A-LOAM's matching (in the live loop the output seeds the guess). Each log is one trajectory, so a replay difference is one trajectory's difference, not a spread. The keyframe scans in the logs are the ones of the live run.

## Rules
1. Control (C_R = 0) must reproduce the live F26 score of the same log within max(0.05 m, 5 %). If it does not, the replay is not valid for that log and is reported, not adjusted.
2. A difference counts only if it exceeds the project's tie band, max(0.1 m, 10 %) of the control score, on that log.
3. "The R channel adds value" requires one C_R > 0 that improves at least two bags by more than the tie band and worsens none by more than the tie band, on bags that are not the calibration bag. Anything else is reported as "no gain shown" (or "harmful" where a bag worsens beyond the band).
4. A value chosen from this grid is not frozen and not claimed: all bags here are development data for F26 and the live feedback is not captured. Any adoption needs a live test on held-out bags with rules written first.

## Predictions written before the run
- C_R = 0 reproduces the live scores.
- Multi Floor, Corridor02 and Cave02 get worse with larger C_R (A-LOAM's rotation is the weaker one there, as the older replay found); Long Corridor may improve; GEODE unclear.
- No C_R satisfies rule 3.

## Results (10 Nov 2026, all 8 logs x 7 values run)

### Rule 1, control against live (RMSE / max, m)
| log | live F26 | replay C_R=0 | within max(0.05 m, 5 %)? |
|---|---|---|---|
| Multi Floor run 1 | 0.54 / 1.01 | 0.76 / 1.54 | no, replay void |
| Long Corridor run 1 | 2.10 / 3.73 | 2.06 / 3.58 | yes |
| Corridor02 run 1 | 1.93 / 3.46 | 2.36 / 4.15 | no, replay void |
| Corridor02 run 2 | 2.04 / 3.46 | 2.44 / 4.14 | no, replay void |
| Cave02 run 1 | 6.23 / 10.56 | 6.18 / 10.55 | yes |
| GEODE run 1 | 6.36 / 14.07 | 6.35 / 14.35 | yes |
| GEODE run 2 | 3.26 / 7.81 | 3.17 / 7.63 | yes |
| GEODE run 3 | 5.51 / 15.25 | 5.49 / 15.29 | yes |

Multi Floor and Corridor02 do not reproduce, so their rows below are reported but do not count for any rule. Likely reason (not tested): open loop, the logged A-LOAM poses were produced with the live output as the scan-matching guess, and the replay cannot feed a different output back; on these two bags the live scores are also the ones that depend most on that guess.

### Grid, ATE RMSE / max (m)
| log | 0 | 1e-5 | 3e-5 | 1e-4 | 3e-4 | 1e-3 | 3e-3 |
|---|---|---|---|---|---|---|---|
| MF (void) | 0.76/1.54 | 0.47/0.83 | 0.61/1.03 | 0.88/1.79 | 1.24/2.02 | 1.36/2.57 | 1.35/2.43 |
| LC | 2.06/3.58 | 1.83/3.24 | 1.82/3.10 | 2.76/4.74 | 3.43/5.84 | 2.54/5.09 | 2.04/4.34 |
| C02 run 1 (void) | 2.36/4.15 | 6.23/10.85 | 9.18/15.55 | 18.36/27.78 | 7.00/12.19 | 6.14/10.24 | 4.57/7.61 |
| C02 run 2 (void) | 2.44/4.14 | 5.18/8.93 | 7.27/12.77 | 8.32/14.87 | 6.28/11.42 | 4.32/7.58 | 3.49/5.92 |
| CAVE | 6.18/10.55 | 8.64/15.89 | 8.63/15.86 | 8.61/15.79 | 8.58/15.71 | 8.57/15.69 | 8.58/15.71 |
| GEODE run 1 | 6.35/14.35 | 6.75/14.60 | 6.73/14.51 | 6.71/14.41 | 6.69/14.42 | 6.60/13.74 | 6.60/13.87 |
| GEODE run 2 | 3.17/7.63 | 4.07/8.84 | 4.08/8.88 | 4.07/8.78 | 4.10/8.78 | 4.14/8.80 | 4.15/8.79 |
| GEODE run 3 | 5.49/15.29 | 4.76/12.05 | 4.74/11.97 | 4.70/11.84 | 4.67/11.76 | 4.67/11.77 | 4.66/11.80 |

### Rule readings (valid logs only: LC, Cave02, GEODE 1 to 3; tie band max(0.1 m, 10 %))
- Cave02 gets worse by +2.4 m at every C_R > 0.
- GEODE run 2 gets worse by +0.9 m at every C_R > 0; GEODE run 3 gets better by 0.7 to 0.8 m at every C_R > 0; GEODE run 1 is a tie (+0.25 to +0.40, inside the band).
- Long Corridor is better at 1e-5 and 3e-5 (-0.23, -0.24), worse at 1e-4 to 1e-3 (+0.5 to +1.4), a tie at 3e-3.
- Rule 3: no value improves two bags without worsening any. Reading: no gain shown, and harmful on Cave02 and GEODE run 2 for every value.
- The GEODE runs disagree with each other (run 2 worse, run 3 better) on the same bag with the same change, which is the size of the run-to-run difference in the logged A-LOAM input, not a measured effect of C_R.

### Against the predictions
- "Control reproduces live": false on Multi Floor and Corridor02, true on the other bags.
- "MF, C02, Cave get worse with larger C_R": Cave02 yes; Corridor02 yes but void; Multi Floor worse at C_R >= 1e-4 but better at 1e-5, void.
- "Long Corridor may improve": only at the smallest two values, and it is not monotone.
- "No C_R satisfies rule 3": true.

### Limits and status
Open loop, one trajectory per log, development data for F26. Nothing frozen, nothing claimed. The live feedback (output seeding A-LOAM) is not captured, so this cannot say what a live run with C_R > 0 would do. The two bags where the replay is void are those where a live test would matter most. F26 stays with C_R = 0.
