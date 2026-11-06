# F24: results to date on every dataset, and what has not been run (6 Nov 2026)

ATE RMSE / max in m, Umeyama SE(3), no scale, full span, front end only (A-LOAM + VINS-Mono), no loop closure, laptop unless stated, settings frozen. n = live runs. Sources: F24_to_F27_All_Bags.md, F24_Predict_Guard.md, F24_Live_Corridor02_Cave02_GEODE.md, F25_Fixes.md, Farm_Forward_Camera_Test.md, SwitchSLAM_TableII_Verified.md, Dataset_Test_Plan.md (protocols).

## A. Switch-SLAM's Table II datasets (the comparison with the paper)
| Dataset (paper) | Switch-SLAM published | F24 to date | Still to do |
|---|---|---|---|
| Fast Rotate (Gazebo, 115 m) | 1.50 / 0.23 | not run | recreation + run: protocol written (FastRotate_Plane_Test_Protocol.md); arms F5, F24, SW |
| Plane (Gazebo, 109 m) | 1.27 / 0.35 | not run; first attempt stopped at the fence (driver bug, fixed) | re-run: unfed A-LOAM, F24, SW |
| Farm (Gazebo, 536 m) | 1.10 / 0.38 | L route 80 m: 0.657 / 0.897 (sideways RGB 60 Hz, n=1); forward RGB 60 Hz 0.472 / 1.068 (n=1); forward grey 20 Hz 0.255 / 0.568 (n=1, not the paper's sensors) | repeats (paper = mean of 3); the paper's 536 m route with its fast-rotation and plane stretches is not reproduced |
| Handheld (LVI-SAM) | 3.07 / 1.25 | not run | availability of the bag not checked |
| Multi Floor (SubT-MRS) | 3.63 / 1.61 | **0.45 RMSE / 0.92 max** (n=1) | 2 more runs (paper = mean of 3) |
| Long Corridor (SubT-MRS) | 5.09 / 2.42 | 2.12 / 5.31, 2.15 / 5.57, 1.75 / 3.53 (n=3, mean 2.01) | done |
| ANYmal 1 to 4 (CERBERUS, LiDAR FOV cut to 180 degrees) | 2.96 / 1.29, 3.41 / 1.37, 3.68 / 1.61, 2.42 / 1.05 | not run | no download link found (Dataset_Test_Plan.md: skipped) |

## B. Our own extra bags (no published Switch-SLAM number)
| Dataset | F24 to date | Open |
|---|---|---|
| Corridor02 (SubT-MRS) | 1.47 / 2.51 (n=1, development data) | F26 run planned |
| Cave02 (SubT-MRS) | 7.55 / 12.63 (n=1; F8 / F16 earlier 4.4) | F16 + F23 matched repeat to see if F24 regressed |
| GEODE stairs alpha | 6.15 / 14.00, 9.15 / 25.44 (0.5x), 9.09 / 19.42 (0.25x) (n=3) | A-LOAM-limited, spread 6 to 9 m |

## C. Held back in the dataset plan, never run with F24
SubT-MRS BlockLiDAR and BlockVisual (honesty counterpart: camera blocked), SubT-MRS Cave01, 03, 04, FusionPortableV2 `handheld_underground00` (total-station ground truth), FusionPortable v1 `20220216_corridor_day` (control), other GEODE alpha sequences (published results: nearly all methods fail).

## D. Repeats that would make single runs usable
Multi Floor (n=1), Corridor02 (n=1), Cave02 (n=1), Farm (n=1 per rig). One run supports no claim; Switch-SLAM's numbers are means of three.
