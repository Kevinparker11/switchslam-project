# F24 against F26, every bag (6 Nov 2026)

F26 = F24 with the scan-to-map guess chosen by Switch-SLAM's degeneracy rule; the fusion is F24's. ATE RMSE / max in m, Umeyama SE(3), no scale, full span, front end only unless stated. n = live runs. Sources: F24_to_F27_All_Bags.md, F26_Status_Guess.md, Farm_Forward_Camera_Test.md.

## 1. Result per bag
| Bag | F24 | F26 | F26 - F24 (RMSE) | Spread of F24 on this bag | Reading |
|---|---|---|---|---|---|
| Multi Floor | 0.45 / 0.92 (n=1) | 0.54 / 1.01 (n=1) | +0.09 | about 0.1 (F8, F16 sd 0.11) | slightly worse, at the edge of the spread |
| Long Corridor | 2.12, 2.15, 1.75 (mean 2.01; max 5.31, 5.57, 3.53) | 2.10 / 3.73 (n=1) | +0.09 vs the mean | 1.75 to 2.15 | inside the spread, tie |
| Corridor02 | 1.47, 1.29 (n=2 good runs) and 104.00 (one failed run) | 1.93 / 3.46 (n=1) | **+0.46** | F24 family 1.47 to 1.84 (F16 x6, F20 x3, F24) | worse |
| Cave02 | 7.55, 7.08, 7.11 (n=3) | 6.23 / 10.56 (n=1) | **-0.85 to -1.32** | F24 spread 7.08 to 7.55 | outside the F24 spread; one F26 run, hint only |
| GEODE stairs alpha | 6.15, 9.15, 7.05, 6.56 (0.5x, n=4) | 6.36 / 14.07 (n=1) | -0.2 to -2.8 | 6.15 to 9.15 | inside the spread, tie |
| Farm L route, forward RGB 60 Hz | 0.472 / 1.068 (n=1) | 0.290 / 0.562 (n=1) | -0.18 | 0.255 to 0.472 over the two forward rigs | inside the spread (VINS draw differs) |
Count: F26 lower on Cave02 (now just outside the three-run F24 spread of 7.08 to 7.55, one F26 run) and Farm (inside or at the edge of a spread), higher than the good F24 runs on Corridor02 (outside the F24-family spread of 1.29 to 1.84; F26 has not seen the failure F24 run 2 had), tie on Long Corridor and GEODE, and on Multi Floor F26 0.54 sits inside the F24 spread of 0.45 to 1.01. All n = 1 for F26; no bag gives a result.

## 2. Why: what each version puts into A-LOAM's starting guess
| Bag | F24 guess | F26 guess (kinds used) | Paper rule fires (Hessian degenerate) |
|---|---|---|---|
| Cave02 | VINS motion 86.7 % of scans, "no motion" 13.3 % (warm-up) | LiDAR 100 % | 0 % |
| GEODE | VINS motion 55.1 %, "no motion" 44.9 % | LiDAR 93.7 %, interpolation 3.4 %, VINS 2.9 % | about 6 to 10 % |
| Multi Floor | VINS motion except a few percent | LiDAR 98.5 % | 1.5 % |
| Long Corridor | VINS motion except a few percent | LiDAR 95.5 % | 4.5 % |
| Corridor02 | VINS motion except WARMUP (951 of 8297 rows, 11 %) | LiDAR 98.0 %, interpolation 1.4 %, VINS 0.8 % | about 2 % |
| Farm (forward RGB) | VINS motion whenever it passes the guard (VINS erratic: 11 VO_FAIL rows) | LiDAR 67 %, VINS 32 %, interpolation 0.6 % | 32 % (last 25 m of the L and the standing end) |
So F26 is "F24 with A-LOAM's own guess" on every bag except Farm. Where it differs from F24 in effect: it drops the VINS motion from the guess (helps when VINS is erratic or A-LOAM starts badly: Cave02 warm-up, Farm run 2; costs when VINS is healthy and the LiDAR is not flagged: Corridor02).

## 3. With loop closure (offline back end on the saved keyframes; fixed settings; keyframes cover 0 to 760 s of 893 s on Corridor02)
| Bag | F24 front end | F24 + loops | F26 front end | F26 + loops |
|---|---|---|---|---|
| Corridor02 | 1.471 / 2.51 | **1.110 / 2.15** (22 loops) | 1.931 / 3.46 | 2.006 / 3.53 (13 loops) |
| Cave02 | 7.55 / 12.63 | 7.352 / 12.33 (96 loops, all in the first 100 s) | 6.23 / 10.56 | not run |
| GEODE | 6.152 / 14.00 | 6.152 / 14.00 (0 loops) | 6.36 / 14.07 | not run |

## 4. Same rig, same route: Farm L, forward RGB 60 Hz (the only matched pair of live runs)
| Quantity | F24 (Run 2) | F26 |
|---|---|---|
| Fused ATE / max | 0.472 / 1.068 | 0.290 / 0.562 |
| A-LOAM output ATE / max | 0.616 / 1.254 | 0.312 / 0.627 |
| A-LOAM path against ground truth (80 m) | +10.5 % | +1.8 % |
| VINS-Mono alone ATE; path | 14.47; 151 m (erratic, 11 VO_FAIL rows) | 4.31; 65 m (20 % short, no VO_FAIL) |
| Mean LiDAR weight in the fusion | 0.93 to 0.96 | 0.99 |
The two runs differ in the VINS-Mono behaviour as well as in the guess rule; one run each cannot separate them.

## 5. Cave02, fused RMSE per 120 s block
| Block (s) | 0-120 | 120-240 | 240-360 | 360-480 | 480-600 | 600-720 | 720-840 | 840-960 |
|---|---|---|---|---|---|---|---|---|
| F24 | 12.0 | 12.1 | 5.8 | 5.1 | 5.0 | 4.9 | 5.3 | 5.1 |
| F26 | 9.7 | 10.1 | 5.0 | 4.2 | 4.2 | 4.1 | 4.3 | 4.3 |
F26 is lower in every block (2.0 to 2.3 m early, 0.6 to 0.9 m later); one run each.

## Update 10 Nov 2026: F24-family 4 h queue (read from for_claude_f24_family_4h.zip)
RMSE / max in m, same method. GEODE at 0.5x. No reading rule was written for this queue beforehand, so this is descriptive.

| Bag | F24 | F26 | F27 |
|---|---|---|---|
| GEODE | 6.15/14.00, 9.15/25.44, 7.05/17.09, 6.56/16.46 (n=4, mean 7.23, median 6.80) | 6.36/14.07, 3.26/7.81, 5.51/15.25 (n=3, mean 5.04, median 5.51) | 6.97/16.40, 8.82/20.02, 6.41/13.30 (n=3, mean 7.40, median 6.97) |
| Corridor02 | 1.47/2.51, 104.00/149.20 (failed), 1.29/2.68 (n=3) | 1.93/3.46, 2.04/3.46 (n=2) | not run |
| Cave02 | 7.55, 7.08, 7.11 (n=3) | 6.23/10.56 (n=1, 6 Nov) | 6.62/11.21 (n=1, 6 Nov) |

- Cave02 runs 2 and 3 of F26 and F27 are not in the zip (no log, no ATE file, no index row). The first stage of the queue produced nothing; cause not yet known.
- GEODE F26 is lower than F24 by 2.2 m on the mean. Exact Mann-Whitney on 3 against 4 runs: U = 1, one-sided p = 0.057, two-sided 0.114. The ranges touch (F26 max 6.36, F24 min 6.15). Suggestive, not shown. F24 and F26 runs were not interleaved.
- GEODE F27 is no different from F24 (mean 7.40 against 7.23).
- Corridor02 F26 2.04 and 1.93: no failure in two runs. F24 failed once in three. Two runs cannot give a failure rate.
- Nothing reaches 1 to 2 m on GEODE (best single run 3.26).
