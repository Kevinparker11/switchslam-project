# Configurations explained, and all results to date (21 Oct 2026)

Metric everywhere: ATE RMSE in metres, Umeyama SE(3) alignment, no scale, full span, mean ± sd over live runs (n = 3 unless stated). Differences under about 0.1-0.3 m are ties. Sources: Complete Test Record master tables, Published_Comparison_All_Datasets.md, Cave02_Control_Results.md, Improvement_Replay_Tests.md, GenZ_fusion_v4_MultiFloor_Results.md.

## 1. How to read a configuration name

- **F** = a live configuration of `fusion_node_v2` on the A-LOAM stack (master system, `fusion_v3`). **G** = the same node on the GenZ-LIO stack (`fusion_v4`, 21 Oct). **M** = variants that use A-LOAM's scan-to-map Hessian (`/mapping_hessian`) instead of the scan-to-scan one (defined, not used for results).
- The number is only a label in the order the configuration was added. It does not mean "version 8"; F8 is simply the eighth configuration defined.
- "**+ loops**" = the same run followed by the offline loop-closure back end (LoopCloser, iso loop weights, 1 round). "Front end" or no suffix = no loops.
- A configuration is a set of environment variables for the node, written in `run_fusion_study.sh`.

Terms used below:
- **VINS-Mono**: the camera-IMU estimator (the primary pose in the fused system). **A-LOAM**: the LiDAR scan-to-map matcher (older front end). **GenZ-LIO**: the newer LiDAR-inertial front end (fusion_v4).
- **Schur blocks of the registration Hessian**: S_RR (rotation, "R channel") and S_tt (translation, "T channel"), each after removing the other with a Schur complement.
- **C_T / C_R**: scale of the LiDAR information for translation / rotation in the weight W = (c·S + I)^-1 c·S. Larger c = trust LiDAR more. c = 0 means LiDAR is ignored.
- **κ gate**: LiDAR is used only while the condition number κ(S_RR) is below a threshold (15.7 = Switch-SLAM-style rule; 1e9 = gate off, so the weight alone decides).
- **SAH** (structure-anchored heading): the additional T channel. Wall normals, levelled by VINS gravity, are histogrammed in horizontal direction and compared with a learned world reference; it nudges heading by at most 0.25° per scan.
- **WARMUP / FUSED**: the first 20 s after VINS-Mono starts the output is LiDAR only (W = I); after that the fused rule applies.

## 2. The F configurations (A-LOAM stack, master)

| Config | Settings | What it denotes | Status |
|---|---|---|---|
| F0 | FUSION_MODE=vins | VINS-Mono alone, run inside the node. The control. | live |
| F1 | fused, C_T = LASER_C_T, κ gate 15.7 fixed | First method: soft translation correction from LiDAR, switched off while κ(S_RR) is above 15.7. (The record lists C_T 0.003; the script default is 1e-3.) | live |
| F2 | as F1, κ threshold from online Otsu | Same, but the threshold is learned online with no labels. | live |
| F3 | fused, C_T = LASER_C_T, no gate | Ablation: remove the κ gate, keep the soft weight. | live |
| F4 | FUSION_MODE=lidar, A-LOAM seeded by VINS prediction | LiDAR only, but its initial guess comes from VINS-Mono. | live |
| F5 | FUSION_MODE=lidar, no VINS prediction | Pure A-LOAM, the plain LiDAR baseline. | live |
| F6 | F1 + C_R | Adds a LiDAR rotation weight. | dropped: replays showed C_R hurts with A-LOAM (never run live) |
| F7 | fused, C_T = 0.01, no gate | C_T chosen by a 5-second-horizon rule on bag 0. | live |
| F8 | fused, C_T = 0.03, no gate | **The method**: soft Schur translation weight, rotation from VINS-Mono only, R channel monitored not used. C_T frozen here. | live (the A-LOAM master) |
| F9 / F10 | C_T = 0.1 / 0.3, no gate | Sensitivity of F8 to C_T. | live |
| F11 | WEIGHT_MODE=iso | Same weight in every direction (same mean information). Tests whether direction-dependence matters. | replay only |
| F12 | WEIGHT_MODE=switch_ss, κ 15.7 | Hard switch with the Switch-SLAM detection rule: all-or-nothing LiDAR. | live |
| F13 | WEIGHT_MODE=proj | Hard 0/1 per direction (direction dropped if κ_t > 10). | replay only |
| F14 | WEIGHT_MODE=lidar (W = I) | LiDAR translation always, VINS rotation: no weighting at all. | live |
| F15 | WEIGHT_MODE=diag | Diagonal block of H instead of the Schur complement S_tt. | replay only |
| F16 | F8 + SAH=1 | F8 plus the additional T channel (SAH). **The final A-LOAM system.** | live |
| M0 / M1 | F0 / F1 with HESS_TOPIC=/mapping_hessian | Same, using the scan-to-map Hessian. | defined, not used |

Older systems: the **old switching node** (Switch-SLAM-style modes LIDAR_ONLY / TRANSITION / TIGHTLY_COUPLED chosen by semicircle thresholds on Schur blocks plus a Bingham-style Channel T), and the **13 Oct threshold study** (detection rules A1-A8, B1-B5, C1-C2 tried on that node). Both are superseded by fusion_node_v2. The old node lives in `switchslam_v1/`; the threshold study in `threshold_study/`.

## 3. The G configurations (GenZ-LIO stack, fusion_v4)

| Config | Settings | What it denotes |
|---|---|---|
| G0 | FUSION_MODE=lidar | GenZ-LIO alone (LiDAR-inertial baseline). Also the recording from which all other G results are replayed exactly. |
| GV | FUSION_MODE=vins | VINS-Mono control in this stack (same as F0). |
| G8 | C_T = 1e-4, no gate | The F8 rule on GenZ-LIO: rotation from VINS-Mono. Ablation. |
| G16 | G8 + SAH | The F16 rule on GenZ-LIO. Ablation. |
| **G9** | C_T = 3e-6, C_R = 5e-6, no gate | **R and T both from Schur, both active**: S_RR weights rotation, S_tt weights translation. |
| **G17** | G9 + SAH | **G9 plus the additional T (SAH).** The proposed final system on GenZ-LIO. |

Weights were chosen on Multi Floor only and frozen (rule: smallest mean ATE, plateau middle).

## 4. Results to date

### Multi Floor (tuning sequence; wheeled/legged, SubT-MRS)
| Config | ATE (m) | Notes |
|---|---|---|
| F0 VINS-Mono | 1.28 ± 0.02 | |
| F1 / F2 (gated) | 1.05 / 1.05 | |
| F3 | 0.96 | |
| F7 / F9 / F10 | 0.88 / 0.77 / 0.69 | |
| **F8** | **0.617 ± 0.107** | A-LOAM master |
| F16 | 0.640 ± 0.115 | |
| F4 / F5 (LiDAR only) | 25.7 / 26.4 | A-LOAM alone fails |
| Old switching node | 1.39 ± 0.14 | |
| F8 + loops | 0.347 ± 0.036 | |
| F16 + loops | 0.523 ± 0.224 | |
| F7 + loops (1 recording) / F9 + loops | 0.309 / 0.356 ± 0.102 | |
| G0 GenZ-LIO alone | 0.569 ± 0.287 | runs 0.88 / 0.53 / 0.31 |
| GV (VINS in the same 3 runs) | 3.81 | runs 1.27 / 8.91 / 1.26 |
| G8 | 3.43 ± 4.85 | VINS rotation fails in run 2 |
| G16 | 3.78 ± 4.59 | |
| **G9** | **0.420 ± 0.155** | in-sample |
| **G17** | **0.388 ± 0.150** | in-sample; SAH helps all 3 runs |

### Long Corridor (Corridor01; SAH development data)
| Config | ATE (m) |
|---|---|
| F0 VINS-Mono | 5.81 ± 0.27 |
| F8 | 4.53 ± 0.49 |
| F12 hard switch | 5.43 ± 0.71 |
| F14 (W = I) | 13.2 ± 8.7 |
| F5 A-LOAM only | 15.8 ± 6.3 |
| **F16** | **2.27 ± 0.45** |
| F8 + loops | 2.67 ± 0.73 |
| **F16 + loops** | **1.538 ± 0.304** |

### Corridor02 (held-out for the F8 design; SAH development data)
| Config | ATE (m) |
|---|---|
| F0 VINS-Mono | 4.03 ± 0.01 |
| F5 A-LOAM only | 66 ± 24 |
| F8 | 2.12 ± 0.06 |
| F12 hard switch | 1.87 ± 0.27 |
| F14 (W = I) | 1.74 ± 0.06 |
| **F16** | **1.708 ± 0.069** |
| F8 + loops | 2.10 ± 0.10 |
| **F16 + loops** | **1.250 ± 0.435** |

### Cave02 (clean control, handheld)
| Config | ATE (m) |
|---|---|
| F0 VINS-Mono | 10.25 ± 0.03 |
| F8 | 4.47 ± 0.21 |
| F16 | 4.40 ± 0.61 (SAH applied 0.00°) |

### GenZ stack, held out (frozen Multi Floor weights, 1 live run each at 1.0x replay; see GenZ_fusion_v4_HeldOut_Results.md)
| Sequence | G17 live | GenZ-LIO alone | VINS-Mono in the same run | Master F16 |
|---|---|---|---|---|
| Corridor02 | 5.60 | 3.98 | 336.7 (diverged) | 1.71 |
| Cave02 | 12.66 | 4.61 | 148.8 (diverged) | 4.40 |

The frozen GenZ configuration did **not** generalise in these runs. Long Corridor and GEODE with the GenZ stack have not been scored yet.

## 5. Published numbers for comparison (same sequences)
Multi Floor: Switch-SLAM 1.61; SubT-MRS challenge LiDAR track best 0.401; SuperLoc 0.315; GenZ-LIO 0.26 and iG-LIO 0.25 (per-sequence tuned). Long Corridor: Switch-SLAM 2.42; challenge 1.254-2.990; SuperLoc 0.817; LODESTAR 1.386; GenZ-LIO 1.90. Corridor02 (identity unconfirmed): GenZ-LIO 0.69. Cave02: GenZ-LIO 0.44, iG-LIO 0.43. Full table and sources: Published_Comparison_All_Datasets.md.

## 6. Replay experiments (offline, A-LOAM logs, no new runs)
1. Warm-up length (0-60 s): differences inside the run-to-run spread, non-monotonic; no change justified. A shorter warm-up (0 s) helped all Long Corridor and Corridor02 runs but worsened 5 of 6 Multi Floor runs; it is a hypothesis for an untouched sequence, not adopted. SAH during WARMUP at 20 s does nothing reliable.
2. Corridor02 loop rejection: the true loop needs a ~4.1 m correction, the back end's limit (max_corr_trans) is 4.0 m. At 6 m, two runs improved (Corridor02 F16 run 6 1.85 to 0.88; Long Corridor F8 run 1 2.91 to 1.57), none got worse. Not adopted (needs an untouched sequence; a wider gate can admit false loops).
3. Schur R made active with A-LOAM (c_R from 0.003): Long Corridor improved (4.5 to 1.9) but Multi Floor (0.62 to 1.3-2.0), Corridor02 (2.2 to 3.4-4.1) and Cave02 (4.5 to 5.7-8.8) got worse. With GenZ-LIO the same idea gives the best Multi Floor result (G9, 0.42), because GenZ-LIO's rotation is good and VINS-Mono's is the weak link there. Whether it holds on the other sequences is the pending test.
4. Alternative T channel (orientation tensor of scan normals): same weak directions as Schur (|cos| 0.99-1.00), partial correlation with error given Schur +0.24 (Multi Floor), -0.18 (Long Corridor), +0.02 (Corridor02): no consistent extra information.

## 7. Honest status
- Master (F16, A-LOAM): beats Switch-SLAM on Multi Floor clearly, ties it on Long Corridor, weak on Cave02. Not better than current LiDAR-inertial methods (iG-LIO, GenZ-LIO) published on these sequences.
- fusion_v4 (G9 / G17): 0.39-0.42 on Multi Floor, tuned on those same runs. On the two held-out bags run so far (Corridor02, Cave02) the frozen weights did not hold (table above); the diagnosis is in GenZ_fusion_v4_HeldOut_Results.md.
