# G20 + OT (orientation-tensor channel on the GenZ-LIO stack): results of the pre-registered replay (2026-10-29)

Thesis: Kavinkumar S, CB.EN.P2MFA25004. Pre-registration: `fusion_v4/ot_study/round3/PREREG3.md` (written before any OT candidate was replayed). Structure kept: Schur R and Schur T separately, plus the OT channel (never discarded, takes part in the decision). Scripts: `gscore.py`, `gselect.py`, `batchg.sh`, `driveG.sh` in `fusion_v4/ot_study/round3/`.

This is the comparison/fallback branch. The main goal stays the A-LOAM stack (F20 / F21); GenZ-LIO (G20) is the stack that already beats Switch-SLAM live on Multi Floor and Long Corridor.

## What was run
47 recorded GenZ-stack runs (MF 13, C02 1, CV 4, LC 10, GEO 14, GZ 4) replayed through the real `fusion_node_v2` callbacks (`SAH_SYNC=1`). GenZ-LIO and VINS-Mono take no feedback from the fusion, so replay equals live except for the asynchronous SAH worker. Baseline G20 = `FUSION_MODE=fused C_T=3e-6 C_R=5e-6 KAPPA_TH=1e9 SAH=1 VIO_CHECK=1 VIO_SCALE_T=10 VIO_CHECK_FAST=5 LIDAR_GUARD_T=2`. Candidates add `OT_SRC=geom OT_MODE=<rule>` (rules: min, smin, gmax, agm); no new constant. Cells: MF, LC, CV x (clean, LiDAR-solver fault FL, VIO-scale fault FV), plus C02, GEO, GZ clean = 12 cells. Score = mean ln(cell median / G20 cell median), negative = better; admissible only if every clean cell median is within +0.05 m of G20.

## Result (median ATE per cell, m)
| cell | G20 | min | smin | **gmax** | agm |
|---|---|---|---|---|---|
| MF clean | 0.350 | 0.350 | 0.351 | 0.347 | 0.342 |
| LC clean | 1.707 | 1.707 | 1.707 | **1.461** | 1.519 |
| CV clean | 0.296 | 0.296 | 0.296 | 0.288 | 0.291 |
| C02 clean | 2.476 | 2.473 | 2.476 | 2.227 | 2.245 |
| GEO clean | 0.474 | 0.473 | 0.474 | 0.379 | 0.403 |
| GZ clean | 0.455 | 0.455 | 0.453 | 0.213 | 0.293 |
| MF FL | 2.497 | 2.490 | 2.476 | 2.559 | 2.519 |
| LC FL | 8.580 | 8.580 | 8.578 | 8.534 | 8.553 |
| CV FL | 3.216 | 3.216 | 3.216 | 3.208 | 3.212 |
| MF FV | 0.633 | 0.633 | 0.639 | **0.439** | 0.505 |
| LC FV | 1.950 | 1.950 | 1.950 | **1.717** | 1.817 |
| CV FV | 0.296 | 0.296 | 0.296 | 0.288 | 0.291 |
| **score vs G20** | 0 | -0.0004 | +0.0000 | **-0.1486** | -0.0969 |
| admissible | | yes | yes | yes | yes |
| recordings better / worse than G20 (>0.05 m and >10 %), of 47 | | 0 / 0 | 0 / 0 | **26 / 1** | 16 / 0 |
| MF-b2 (GenZ-LIO itself diverged) | 1.47 | 1.47 | 1.46 | 1.48 | 1.47 |

Selected by the pre-registered rule: **G20 + OT gmax** (lowest score among the admissible; the tie rule was not needed).

## Against Switch-SLAM (clean recordings, per recording)
* Multi Floor (13 recordings, paper 1.61): G20 0.257-0.647, gmax 0.255-0.703; **0 recordings above the paper value** in both.
* Long Corridor (10 recordings, paper 2.42): G20 1.543-1.807, gmax 1.405-1.510; **0 above the paper value** in both.
* Maximum errors against the paper's 3.63 / 5.09 were not tabulated here.

## Reading
1. **min and smin do nothing on this stack.** Their score is -0.0004 and 0.0000 and no recording changes. The OT as a fail-safe cap is inactive when the LiDAR weight (c_T = 3e-6) is already tiny.
2. **gmax is the only rule that moves the numbers.** Long Corridor 1.707 to 1.461, GZ 0.455 to 0.213, GEO 0.474 to 0.379, C02 2.476 to 2.227; Multi Floor unchanged (0.350 to 0.347). It raises the LiDAR translation information where the scan geometry supports it.
3. **The feared cost of gmax under a LiDAR-solver fault did not appear in the injected fault cells.** MF-FL 2.559 vs 2.497 (+0.06), LC-FL 8.534 vs 8.580, CV-FL 3.208 vs 3.216. G20 itself is poor under FL (LC-FL 8.58) and the fail-safe rules do not help (8.580), so the injected fault is mainly absorbed by the VIO-trust and guard parts of G20, not by the OT.
4. **gmax helps under the VIO-scale fault** (MF-FV 0.633 to 0.439, LC-FV 1.950 to 1.717).

## Limits
* All 47 recordings were used when G20 was designed. This is a replay on development data, not a held-out test; a claim beyond that needs a live run on new recordings.
* The fault cells are injected, not real failures. gmax gives no protection against a confident wrong LiDAR solver in the synthetic corridor (round 2, weight 0.79); the injected FL here does not show that case.
* Whether the gmax gain is the geometry-following weight or just a larger constant weight was not separated here. In the A-LOAM round the constant C_T = 0.056 matched it on the bags.
* G20 fails the farm world (6.46 / 14.49 m: the VINS-trust check assumes the LiDAR is the metric reference and GenZ-LIO failed there). The farm was not rerun with gmax. Loop closure with G20 + OT was not run.
* Replay is not live: the SAH worker is asynchronous in the live node.

## Consequence for the goal
G20 + OT gmax keeps R, T and OT and beats Switch-SLAM on Multi Floor and Long Corridor on every recording (replay). It does not solve the farm, and it is not the A-LOAM front end, which is the stated main goal. It is the comparison to beat or match with F21 live.
