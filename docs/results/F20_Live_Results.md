# F20 live results (batch of 2026-10-29, scored against the criteria pre-registered in OT_Channel_Study.md section 6)

Source: `for_claude_F20.zip` from the user's machine. **Multi Floor was not run** (no F20 entries in the MF results index; the gap between the end of the Long Corridor runs 01:44 and the first Corridor02 result 02:33 is one Corridor02 run, so the drive step was skipped, most likely the external drive was not mounted). Long Corridor and Corridor02 ran, 3 runs each, with the back end.

## Per-run ATE (m, full span)
| run | LC front | LC iso | LC ot | C02 front | C02 iso | C02 ot |
|---|---|---|---|---|---|---|
| 1 | 3.382 | 1.868 | 1.834 | 1.745 | 2.093 | 2.064 |
| 2 | 1.958 | 1.508 | 1.466 | 1.728 | 0.914 | 0.911 |
| 3 | 3.048 | 3.609 | 3.058 | 1.787 | 1.298 | 1.297 |
| mean | 2.796 | 2.328 | 2.119 | 1.753 | 1.435 | 1.424 |

Replay of the same design: LC 2.01 front / 1.455 iso; C02 1.71 / 1.481.

## Criteria
* P1 (structure live): OT tensor present on 100 % of fused rows in all 6 runs (median age 0.30 s LC, about 1.0 s C02); rotation check closed on 0 rows. **Pass** (LC and C02).
* P2 (inside the F16 live range): LC front 2.796 in 1.99-3.17 pass; C02 front 1.753 in 1.64-1.84 pass; C02 iso 1.435 in 0.807-1.853 pass; **LC iso 2.328 outside 1.312-2.125 fail**. MF not run.
* P3 (within Switch-SLAM): **LC front mean 2.796 is not below 2.42, fail; LC iso run 3 (3.609) is not below 2.42, fail.** MF not run.
* Also: LC run 1 (3.38) is worse than the LiDAR-only replay on the same log (2.21), and in LC run 3 the loop back end made the result worse (3.05 front end to 3.61 with iso loops).

## Reading
F20 is not distinguishable from F16 on the front end (both Long Corridor means lie inside the F16 range), but it does not meet the Long Corridor Switch-SLAM target live, and the replay value (2.01) was optimistic: live run-to-run spread on Long Corridor is 1.96 to 3.38 m. Corridor02 matches replay closely (1.75 vs 1.71). The live result is a single batch; nothing was changed after seeing it.

## Diagnosis of the Long Corridor live runs (29 Oct 2026, read-only, from the logs in the zip; nothing re-run)
Target: beat Switch-SLAM (RA-L Table II, front end, no loop closure) on Long Corridor, 2.42 m RMSE / 5.09 m max, and on Multi Floor, 1.61 / 3.63, with R, T and OT kept.
* Max error: live F20 on Long Corridor 8.44 / 4.91 / 8.03 m against 5.09, so two of three runs also fail the max target.
* **The fused output is worse than the A-LOAM pose logged in the same run in all three runs** (ATE, own alignment): fused 3.38 / 1.96 / 3.05, A-LOAM 2.21 / 0.70 / 2.38. (A-LOAM is seeded by the fused pose, so this is not an independent LiDAR-only result.) The same was seen in F16 runs 1-2.
* **A yaw step at the switch from WARMUP to FUSED (about 21.4 s).** Within 1-2 s of the switch the fused yaw is 6.8 / 6.2 / 6.1 deg off the A-LOAM yaw in the three runs (steady afterwards, then 5-18 deg later). Over 20-22 s the ground-truth yaw change is -5.4 / -8.9 / -8.9 deg, A-LOAM -6.1 / -8.1 / -8.1, VINS-Mono -8.6 / -10.1 / -9.9, fused -13.0 / -14.2 / -14.2. The switch happens during a turn; A-LOAM turns back by about +5 deg in the next 0.8 s while the VINS rotation does not. No steady-state time lag between the VINS and A-LOAM yaw increments (best lag 0 rows, corr 0.85-0.89), so a pose-latency cause is not supported; the cause of the step is not established.
* **Size of the effect:** rotating the post-switch fused path back by the step (6-8 deg, a bound on what removing the step could give) lowers the ATE only from 3.38 / 1.96 / 3.05 to 2.91 / 1.68 / 2.56 m (8 deg). So the step is part of the gap, not all of it; the mean would be about 2.4 m, no margin.
* Rotation weight: a replay of C_R = 1e-5 ... 3e-3 (R channel active) on the three Long Corridor F8 logs does not help (mean 1.99 / 2.05 / 2.55 / 3.06 / 2.67 / 2.01 against 1.97 at C_R = 0, F21 base). The R channel stays a safeguard, not a gain, on this data.
* Replay is blind to this: replays of F20 / F21 give 1.97-2.01 on Long Corridor, live gave 2.80. The replays use F8 logs, in which A-LOAM was not seeded by SAH-corrected poses.
