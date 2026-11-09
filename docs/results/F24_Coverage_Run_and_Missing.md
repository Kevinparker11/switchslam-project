# F24: results to date on every dataset, and what has not been run (6 Nov 2026)

ATE RMSE / max in m, Umeyama SE(3), no scale, full span, front end only (A-LOAM + VINS-Mono), no loop closure, laptop unless stated, settings frozen. n = live runs. Sources: F24_to_F27_All_Bags.md, F24_Predict_Guard.md, F24_Live_Corridor02_Cave02_GEODE.md, F25_Fixes.md, Farm_Forward_Camera_Test.md, SwitchSLAM_TableII_Verified.md, Dataset_Test_Plan.md (protocols).

## A. Switch-SLAM's Table II datasets (the comparison with the paper)
| Dataset (paper) | Switch-SLAM published | F24 to date | Still to do |
|---|---|---|---|
| Fast Rotate (Gazebo, 115 m) | 1.50 / 0.23 | not run | recreation + run: protocol written (FastRotate_Plane_Test_Protocol.md); arms F5, F24, SW |
| Plane (Gazebo, 109 m) | 1.27 / 0.35 | not run; first attempt stopped at the fence (driver bug, fixed) | re-run: unfed A-LOAM, F24, SW |
| Farm (Gazebo, 536 m) | 1.10 / 0.38 | L route 80 m: 0.657 / 0.897 (sideways RGB 60 Hz, n=1); forward RGB 60 Hz 0.472 / 1.068 (n=1); forward grey 20 Hz 0.255 / 0.568 (n=1, not the paper's sensors) | repeats (paper = mean of 3); the paper's 536 m route with its fast-rotation and plane stretches is not reproduced |
| Handheld (LVI-SAM) | 3.07 / 1.25 | not run | availability of the bag not checked |
| Multi Floor (SubT-MRS) | 3.63 / 1.61 | **0.45 / 0.92, 1.01 / 1.73, 0.69 / 1.24** (n=3, mean 0.72 / 1.30) | done 7 Nov (runs 2, 3 read from results_index.csv; zip not yet seen) |
| Long Corridor (SubT-MRS) | 5.09 / 2.42 | 2.12 / 5.31, 2.15 / 5.57, 1.75 / 3.53 (n=3, mean 2.01) | done |
| ANYmal 1 to 4 (CERBERUS, LiDAR FOV cut to 180 degrees) | 2.96 / 1.29, 3.41 / 1.37, 3.68 / 1.61, 2.42 / 1.05 | not run | no download link found (Dataset_Test_Plan.md: skipped) |

## B. Our own extra bags (no published Switch-SLAM number)
| Dataset | F24 to date | Open |
|---|---|---|
| Corridor02 (SubT-MRS) | 1.47 / 2.51, **104.00 / 149.20 (failed)**, 1.29 / 2.68 (n=3); run 2 is a LiDAR failure (see below), development data | root cause of the failure; F26 repeats |
| Cave02 (SubT-MRS) | 7.55 / 12.63, 7.08 / 11.78, 7.11 / 11.76 (n=3, mean 7.25 / 12.06); F8 / F16 earlier 4.0 to 5.1, so the F24 level is stable, not a fluke | F16 + F23 matched repeat to find the cause |
| GEODE stairs alpha | 6.15 / 14.00, 9.15 / 25.44, 7.05 / 17.09, 6.56 / 16.46 (0.5x, n=4); 9.09 / 19.42 (0.25x) | A-LOAM-limited, spread 6.2 to 9.2 m |

## C. Held back in the dataset plan, never run with F24
SubT-MRS BlockLiDAR and BlockVisual (honesty counterpart: camera blocked), SubT-MRS Cave01, 03, 04, FusionPortableV2 `handheld_underground00` (total-station ground truth), FusionPortable v1 `20220216_corridor_day` (control), other GEODE alpha sequences (published results: nearly all methods fail).

## D. Repeats that would make single runs usable
Farm (n=1 per rig). One run supports no claim; Switch-SLAM's numbers are means of three.


## Corridor02 F24 run 2 failure (7 Nov 2026, read from the zip logs on 9 Nov)

F24 run 2 on Corridor02 ended at 104.00 / 149.20, while runs 1 and 3 gave 1.47 / 2.51 and 1.29 / 2.68. Same settings, same bag, same replay rate. It counts as a run (failed runs count).

What the logs show:
- No VO_FAIL, no LiDAR guard event: the mode is WARMUP then FUSED in all three runs (951 / 7345, 952 / 7460, 952 / 7385 rows).
- VINS-Mono alone is fine in all three runs (3.52, 3.55, 3.53 RMSE). A-LOAM alone is 2.32 and 1.66 in runs 1 and 3, and 103.61 in run 2. So the cause is A-LOAM, and the fused output followed it.
- A-LOAM and VINS agree to within about 1 m until 250 s and stay within 6.7 m of each other after fitting on 150 to 230 s in runs 1 and 3. In run 2 they separate at about 545 s (gap 6 m at 543 s, 15 m at 548 s, 49 m by 550 to 600 s, about 260 m by the end). At that time the robot is near (76, -106) in A-LOAM's frame.
- Over 545 to 555 s A-LOAM's y moves from -106 to -88 m (toward +y) while VINS and runs 1 and 3 go the other way (-129 to -141 m). The fused position moved with A-LOAM.
- The only warning signs in the log in that window: the rotation consistency value (rot_gamma) was 0 for about 10 s (545 to 555 s) and the VIO consistency value (vio_gamma) was 0 for one sample at 550 s. Neither held long enough to change the mode. The SAH keyframe statistics also differ: rej_modes 50 against 1 and 2, accepted keyframes 71 against 137 and 154.
- Context: the older F5 configuration (A-LOAM alone, no VINS prediction) failed on Corridor02 in all four runs (46.5 to 93.0 RMSE). F24 passes VINS motion to A-LOAM as its guess. The 21 earlier fused-family runs on this bag (F8, F12, F14, F16, F20, F24 run 1, F26) all ended between 1.47 and 2.19 RMSE; run 2 is the first fused failure in this folder. The VINS guess lowers the failure rate here, it does not remove it.
- Run 1 was made on the 4 Nov code; runs 2 and 3 on the newer commit, whose header adds `HANDOVER_TRUST=0 GUESS_MODE=vins` (the F24 defaults). The failure is therefore not explained by a changed setting, but this is not proven either way.

What this does and does not show: one failure in three runs on one bag. It is a documented failure mode of F24 (an A-LOAM scan-to-map wrong turn that the VIO consistency check did not hold on). It does not show the failure rate; three runs cannot. No fix is proposed from one event; the frozen settings stay as they are. Whether F26 (A-LOAM's own guess) would also fail here is untested.

Cave02 and GEODE runs from the same batch were stable: Cave02 7.55, 7.08, 7.11; GEODE (0.5x) 6.15, 9.15, 7.05, 6.56.
