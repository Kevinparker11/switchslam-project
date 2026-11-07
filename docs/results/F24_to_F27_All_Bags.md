# F24 to F27: versions and every tested value on every bag (6 Nov 2026)

ATE RMSE / max in m, Umeyama SE(3), no scale, full span, front end only (A-LOAM + VINS-Mono), no loop closure, laptop. Values copied from F24_Predict_Guard.md, F24_Live_Corridor02_Cave02_GEODE.md, F25_Fixes.md, F26_Status_Guess.md, Report_Comparison_Table_Draft.md. n = number of live runs. "not run" = no result exists. Last version is F27; there is no F28.

## Versions (each differs from the one before only as stated)
| Version | Change | Config in run_fusion_study.sh | Status |
|---|---|---|---|
| F24 | F23 (F21 + anchored handover) + PREDICT_GUARD: no VINS motion in A-LOAM's mapping guess while VINS fails | `F24` | frozen reference |
| F25A | F24 + HANDOVER_TRUST: skip the anchor while VINS is distrusted (found in the GEODE log) | `F25A` | tried, not adopted |
| (F25 standstill hold, ZUPT) | offline only, no gain even with a perfect flag | none (code kept, default off) | not a version |
| F26 | F24 with the scan-to-map guess chosen by Switch-SLAM's degeneracy status (`GUESS_MODE=status`) | `F26` | development variant |
| F27 | F24 with A-LOAM's own increment instead of "no motion" when the VINS motion is unusable (`GUESS_MODE=vins_odom`) | `F27` | development variant |
Separate line, not F-series: SW / SWI / SWM = our replica of Switch-SLAM (SwitchSLAM_Exact_Replica.md).

## Values on every bag
| Bag | F24 | F25A | F26 | F27 |
|---|---|---|---|---|
| Multi Floor | 0.45 / 0.92, 1.01 / 1.73, 0.69 / 1.24 (n=3, mean 0.72 / 1.30) | not run | 0.54 / 1.01 (n=1) | not run |
| Long Corridor | 2.12 / 5.31, 2.15 / 5.57, 1.75 / 3.53 (n=3, mean 2.01) | not run | 2.10 / 3.73 (n=1) | not run |
| Farm L route, sideways RGB 60 Hz camera (3 Nov) | 0.657 / 0.897 (n=1) | not run | not run | not run |
| Farm L route, forward RGB 60 Hz camera (paper sensors, 7 Nov) | 0.472 / 1.068 (n=1; VINS alone 14.47) | not run | 0.290 / 0.562 (n=1; VINS alone 4.31, no VO_FAIL) | not run |
| Farm L route, forward grey 20 Hz camera (not the paper's sensors) | 0.255 / 0.568 (n=1) | not run | not run | not run |
| Corridor02 | 1.47 / 2.51 (n=1) | not run | 1.93 / 3.46 (n=1; worse than F24, F16, F20; guess LiDAR 98 %) | not run |
| Cave02 | 7.55 / 12.63 (n=1) | not run | 6.23 / 10.56 (n=1) | 6.62 / 11.21 (n=1) |
| GEODE stairs alpha | 6.15 / 14.00, 9.15 / 25.44 (0.5x), 9.09 / 19.42 (0.25x) (n=3) | 6.58 / 15.80, 8.80 / 19.67 (n=2) | 6.36 / 14.07 (n=1) | 6.97 / 16.40 (n=1) |

Offline, not a version: loop-closure back end on the saved keyframes: Corridor02 F24 1.471 -> **1.110 / 2.15** (22 loops), F26 1.931 -> 2.006 / 3.53 (13 loops); Cave02 F24 7.352 / 12.33 (96 loops, all in the first 100 s); GEODE F24 6.152 / 14.00 (0 loops). One recording each.

## Reading
- F25A, F26 and F27 do not beat F24 beyond its run-to-run spread on any bag where they were run (GEODE spread 6.15 to 9.15).
- Cave02: F26 and F27 are 0.9 to 1.3 m below the single F24 run, every 120 s block lower; one run each, a hint only. All are above the old F8 / F16 runs (4.0 to 5.1).
- Multi Floor F26 0.54 (n=1) is inside the F24 spread of 0.45 to 1.01; no difference shown. Long Corridor 2.10 is inside the F24 spread.
- Never run: F25A on anything but GEODE; F27 on Farm, Corridor02, Multi Floor and Long Corridor. F26 on Farm: one live run only, inside F24's own spread on the forward rigs (0.255 to 0.472), not a result. Cave02 and GEODE are development data for F25 to F27.
