# Our configurations against published results, all sequences (21 October 2026)

Our numbers: ATE RMSE (m), Umeyama SE(3), no scale, full span, mean ± sd of live runs (source: Complete Test Record master table; `Cave02_Control_Results.md`). Published numbers were read on 21 Oct from the papers listed under Sources. Metrics differ between papers (alignment and span are often not stated; LODESTAR and D²-LIO use evo APE), so differences under about 0.1–0.3 m are ties.

## Multi Floor (SubT-MRS, legged robot)

| Group | Method | RMSE (m) | Max (m) | Loops |
|---|---|---|---|---|
| Ours | F16 + loops | 0.523 ± 0.224 | – | yes |
| Ours | **F8 + loops** | **0.347 ± 0.036** | 0.73–0.96 | yes |
| Ours | F7 + loops (1 recording) | 0.309 | 0.64 | yes |
| Ours | F9 + loops | 0.356 ± 0.102 | – | yes |
| Ours | **F8** (front end) | **0.617 ± 0.107** | 1.04–1.65 | no |
| Ours | F16 | 0.640 ± 0.115 | – | no |
| Ours | F10 / F9 / F7 / F3 | 0.69 / 0.77 / 0.88 / 0.96 | – | no |
| Ours | F1 / F2 (gated) | 1.05 / 1.05 | – | no |
| Ours | F0 VINS-Mono | 1.28 ± 0.02 | 2.47 | no |
| Ours | Old switching node | 1.39 ± 0.14 | 4.58 | no |
| Ours | F4 / F5 LiDAR only | 25.7 / 26.4 | – | no |
| Switch-SLAM Table II | Switch-SLAM | 1.61 | 3.63 | no |
| Switch-SLAM Table II | VINS-Mono / LOAM / R2LIVE / R3LIVE | 6.30 / 10.6 / 18.5 / 19.0 | 12.8 / 17.9 / 35.2 / 32.4 | no |
| Switch-SLAM Table II | LIO-SAM, LVI-SAM, FAST-LIVO | fail | | no |
| Lee et al. (journal extension) | Proposed / R3LIVE / R2LIVE | 2.13 / 3.08 / 14.6 | 5.72 / 5.38 / 27.2 | not stated |
| SubT-MRS ICCV'23 challenge (LiDAR track) | Liu / Weitong / Kim / Yibin | 0.401 / 0.577 / 0.650 / 5.500 | – | Liu, Weitong, Kim: yes |
| SuperLoc Table III (Floor01) | SuperLoc / Zheng [18] | 0.315 / 19.769 | – | no |

Reading: every fused front end from F1 down is below Switch-SLAM (F8 −62 %), and max error is about 2.2–3× lower. With loops (0.347) we are below every challenge entry (Liu 0.401, −13 %) and second only to SuperLoc (0.315, LiDAR-inertial odometry, +10 %). Our VINS-Mono alone (1.28) is far below Switch-SLAM's VINS-Mono (6.30), so part of the gap is setup and evaluation, not method.

## Long Corridor (SubT-MRS Corridor01, wheeled RC)

| Group | Method | RMSE (m) | Max (m) | Loops |
|---|---|---|---|---|
| Ours | **F16 + loops** | **1.538 ± 0.304** | – | yes |
| Ours | F8 + loops | 2.67 ± 0.73 | 6.0–10.5 | yes |
| Ours | **F16** (front end) | **2.27 ± 0.45** | 5.38–7.85 | no |
| Ours | F8 | 4.53 ± 0.49 | 11.4–14.1 | no |
| Ours | F12 hard switch | 5.43 ± 0.71 | – | no |
| Ours | F0 VINS-Mono | 5.81 ± 0.27 | – | no |
| Ours | F14 always-LiDAR translation / F5 A-LOAM | 13.2 ± 8.7 / 15.8 ± 6.3 | – | no |
| Switch-SLAM Table II | Switch-SLAM | 2.42 | 5.09 | no |
| Switch-SLAM Table II | LVI-SAM / R3LIVE / LIO-SAM / VINS-Mono / LOAM | 4.37 / 7.63 / 7.64 / 11.8 / 12.6 | 8.62 / 14.5 / 17.6 / 23.8 / 25.6 | no |
| Switch-SLAM Table II | R2LIVE, FAST-LIVO | fail | | no |
| Lee et al. (journal extension) | Proposed / LVI-SAM / R3LIVE | 4.77 / 8.7 / 7.87 | 10.5 / 18.4 / 15.5 | not stated |
| SubT-MRS challenge | Weitong / Liu / Kim / Yibin | 1.254 / 1.454 / 2.100 / 2.990 | – | Weitong, Liu, Kim: yes |
| SuperLoc Table III (Corridor01) | SuperLoc / Zheng [18] | 0.817 / 55.205 | – | no |
| LODESTAR Table V (APE) | LODESTAR (threshold grid-searched on this sequence) | 1.386 | – | no |
| LODESTAR Table V (APE) | GenZ-ICP / DLIO / LIO-SAM / KISS-ICP / FAST-LIO2 / iG-LIO / AdaLIO / DLO | 1.982 / 2.294 / 2.959 / 3.028 / 3.113 / 3.136 / 3.160 / 9.416 | – | no |
| D²-LIO Table II (APE, Long_Corridor_1) | FAST-LIO2 / D²-LIO | 1.08 / 1.65 | – | not stated |
| LP-ICP Table IV | LIO-SAM + LP-ICP / + X-ICP / + Zhang | 11.92 / 19.63 / 24.71 | – | disabled |

Reading: front end against front end, F16 (2.27 ± 0.45) ties Switch-SLAM (2.42) on RMSE and is worse on max (5.4–7.9 vs 5.09; the max is the start-up transient). F8 alone loses (4.53). F16 beats every other Switch-SLAM baseline and most LiDAR-inertial odometries in LODESTAR's table, but not GenZ-ICP (1.98), LODESTAR (1.39), D²-LIO's FAST-LIO2 (1.08) or SuperLoc (0.82). With loops (1.538) we are behind the two best challenge entries (1.254, 1.454) and ahead of Kim (2.100) and Yibin (2.990). The same FAST-LIO2 is 1.08 in one paper and 3.11 in another, which shows how much setups differ.

## Corridor02 (SubT-MRS RC1, wheeled RC)

| Method | RMSE (m) | Loops |
|---|---|---|
| **F16 + loops** | **1.250 ± 0.435** | yes |
| F8 + loops | 2.10 ± 0.10 | yes |
| **F16** | **1.708 ± 0.069** | no |
| F14 always-LiDAR translation | 1.74 ± 0.06 | no |
| F12 hard switch | 1.87 ± 0.27 | no |
| F8 | 2.12 ± 0.06 | no |
| F0 VINS-Mono | 4.03 ± 0.01 | no |
| F5 A-LOAM only | 66 ± 24 | no |

No published SLAM or odometry ATE was found for this sequence. Only an internal comparison is possible: F16 −58 % against VINS-Mono, −69 % with loops.

## Cave02 (SubT-MRS Laurel Caverns, handheld)

| Method | RMSE (m) | Note |
|---|---|---|
| F16 | 4.40 ± 0.61 | SAH switched itself off (0.00°) |
| F8 | 4.47 ± 0.21 | |
| F0 VINS-Mono | 10.25 ± 0.03 | |
| DCReg Table 5: Odom / O3D / ME-TReg / FCN-SR / ME-TSVD / ME-SR / DCReg | 1.298 / 0.169 / 2.095 / 4.913 / 4.971 / 5.656 / 0.046 | Localisation in a prior map (53 M points), not SLAM |

No published SLAM result on Cave02 was found. The challenge's "Laurel Caverns" sequence is called Cave03 in SuperLoc (Liu 0.260 in both), so it is a different sequence. Our cave result is weak against DCReg's odometry baseline (1.30 m).

## Conclusion

1. **Switch-SLAM.** Beaten clearly on Multi Floor (every fused configuration; F8 0.617 vs 1.61, max 1.04–1.65 vs 3.63). On Long Corridor only F16 reaches it, and only as a tie (2.27 ± 0.45 vs 2.42, worse max); F16 + loops (1.54) is lower but uses a back end Switch-SLAM did not. Switch-SLAM did not run Corridor02 or Cave02.
2. **Against everything published.** Multi Floor: second of all methods found (0.347 with loops, behind SuperLoc 0.315, ahead of all challenge entries). Long Corridor: mid-table (front end beats most LiDAR-inertial and all Switch-SLAM baselines; with loops behind 0.817, 1.08, 1.254, 1.386, 1.454). Corridor02: no published reference. Cave02: weak.
3. **Best configuration.** F16 (+ loops) on the corridors, F8 + loops on Multi Floor; F16 is the one frozen setting that is never clearly worse than F8.
4. **Caveats.** Metrics and alignment differ between papers; our VINS-Mono baseline is much better than Switch-SLAM's, so part of the margin is setup; Multi Floor is our tuning sequence and Long Corridor / Corridor02 are SAH development data; an untouched sequence is still needed for a clean claim.

## Sources
- Switch-SLAM, RA-L 2024, Table II (project PDF, read from the rendered table).
- Lee et al., "LiDAR-Visual-Inertial SLAM Robust in Structurally and Visually Degenerate Environments", https://www.robot.t.u-tokyo.ac.jp/~yamashita/paper/E/E487Final.pdf, Table 1.
- SubT-MRS, CVPR 2024 supplemental, Table 3: https://openaccess.thecvf.com/content/CVPR2024/supplemental/Zhao_SubT-MRS_Dataset_Pushing_CVPR_2024_supplemental.pdf
- SuperLoc, arXiv 2412.02901, Table III: https://arxiv.org/pdf/2412.02901
- LODESTAR, arXiv 2511.09142, Table V: https://arxiv.org/pdf/2511.09142v1
- D²-LIO, arXiv 2508.14355, Table II: https://arxiv.org/pdf/2508.14355v1
- LP-ICP, arXiv 2501.02580, Table IV: https://arxiv.org/pdf/2501.02580
- DCReg, arXiv 2509.06285v3, Table 5 (project PDF).
- GenZ-LIO (arXiv 2603.16273) covers Long Corridor, Multi Floor and Laurel Cavern, but its table values could not be read.

## Update 21 Oct: GenZ-LIO Table 4 (uploaded arXiv 2603.16273v3; IEEE T-FR 2026 per its repository) and publication status

GenZ-LIO Table 4: ATE RMSE (m), LiDAR-inertial odometry, no loop closure, × = divergence (> 200 m).

| Sequence | FAST-LIO2 | Faster-LIO | AdaLIO | Point-LIO | LIO-EKF | DLIO | iG-LIO | PV-LIO | GenZ-LIO | Ours best front end | Ours best with loops |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Multi Floor (SubT-MRS) | × | 2.84 | 0.64 | 1.71 | 13.41 | 3.47 | 0.25 | × | 0.26 | 0.617 (F8) | 0.347 (F8) |
| Long Corridor (SubT-MRS) | 1.77 | 9.76 | 1.74 | 29.10 | 26.52 | 2.29 | 1.55 | 2.01 | 1.90 | 2.27 (F16) | 1.538 (F16) |
| Cave 02 (SuperLoc release) | 4.49 | 0.81 | 3.98 | 6.57 | × | 0.57 | 0.43 | 0.43 | 0.44 | 4.40 (F16) | – |
| Corridor 02 (SuperLoc release; may not be our Corridor02, see earlier note) | 1.89 | 2.88 | 1.98 | 1.74 | 65.59 | 1.39 | 1.48 | 0.73 | 0.69 | 1.708 (F16) | 1.250 (F16) |

Reading: current LiDAR-inertial odometries (iG-LIO, GenZ-LIO) beat all our results on Multi Floor, Long Corridor and Cave02 without loop closure. Our front end beats Switch-SLAM and the LVIO baselines, not the best LIO methods. Cave 02 is very likely our sequence (same name, VLP-16 handheld caves from the SuperLoc release); Corridor 02 identity is unconfirmed.

Publication status of sources (checked 21 Oct): peer reviewed: Switch-SLAM (RA-L 2024), SubT-MRS (CVPR 2024), DCReg (IJRR 2026 per project notes), GenZ-LIO (IEEE T-FR 2026 per repository; uploaded v3 in T-FR template). No peer-reviewed version found: SuperLoc, LODESTAR, D²-LIO, LP-ICP (arXiv preprints). Lee et al. journal extension: venue not stated.
