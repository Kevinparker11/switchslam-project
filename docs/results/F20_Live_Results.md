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
* Not a pass: LC runs 1 and 3 (3.38, 3.05) are worse than LiDAR alone in the run-1 replay comparison (2.21) and run 3's loop back end made it worse (3.05 to 3.61).

## Reading
F20 is not distinguishable from F16 on the front end (both Long Corridor means lie inside the F16 range), but it does not meet the Long Corridor Switch-SLAM target live, and the replay value (2.01) was optimistic: live run-to-run spread on Long Corridor is 1.96 to 3.38 m. Corridor02 matches replay closely (1.75 vs 1.71). The live result is a single batch; nothing was changed after seeing it.
