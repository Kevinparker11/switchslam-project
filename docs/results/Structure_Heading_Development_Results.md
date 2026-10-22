# Structure-anchored heading (SAH): development results on all three sequences (17 October 2026)

Follows `Yaw_Drift_Diagnosis_and_Next_Direction.md`. Offline replays of the logged F8 runs with their keyframes (Multi Floor 6 runs, Long Corridor 3, Corridor02 3). Mean ATE RMSE in metres. **All three sequences are development data for this component.** Nothing below was tuned on the corridors: every version was frozen before it was run on them, and each version was run on all three plus the stress cases. Code: `sah/` (`sheading.py` classes StructureHeading, V3-V6, DirectionSLAM; `sah_replay.py`; `sah_stress.py`); the live implementation is `fusion_v3/structure_heading.py`.

## Facts found on the way
- The Hawkins corridors are **not Manhattan**: wall direction in the GT frame, per keyframe, Long Corridor -5.5 deg in one wing and +34.5 deg in the other (stable to +-0.6 deg inside a wing); Corridor02 several directions (-22, +23, and +3 to +10 deg in the middle part). A Manhattan (90 deg) design would mis-measure; the design has to learn arbitrary directions.
- The GT heading on Corridor02 jumps by several degrees between keyframes 0.3 s apart at some times (map-aided GT), so per-keyframe heading truth is noisy there; ATE (position) is the reliable score.
- Corridor02 keyframe files end at 760 s of 893 s (recorder saved its last checkpoint before shutdown); no measurements after that.

## Versions tried (frozen design each time; "stress" = synthetic perturbations of the keyframe normals)
| Version | idea | MF | LC | C02 | verdict |
|---|---|---|---|---|---|
| F8 (current method) | - | 0.626 | 4.515 | 2.168 | baseline |
| v1 | global direction-histogram correlation vs learned reference, null-model structure test, adaptive R | 0.536 | 2.030 | 1.715 | good on real data; strong spurious plane breaks C02 (7.2) |
| v3 | likelihood alignment + mode agreement | - | - | 2.346 | rejects almost everything; dropped |
| v4 | per-direction local alignment, capped prior | 0.544 | 2.030 | 5.208 | snaps walls a few deg off the main axis onto it (C02 590-640 s); dropped |
| v5 | 1-D EKF with wall directions as landmarks | 0.488 | 2.757 | 2.806 | VINS early heading change (5 deg in 60 s on C02) exceeds the physical drift model, so known walls become "new" landmarks; dropped |
| v6 | v1 measurement + per-direction agreement veto + capped prior | 0.558 | 2.030 | 1.715 | good |
| **v7** | v6 + drift gate from measurement noise and physical drift rate only | **0.562** | **1.940** | **1.749** | **current candidate** |

## v7 in detail
Per run: MF 0.543 0.474 0.572 0.617 0.578 0.586 (F8 0.766 0.731 0.619 0.576 0.587 0.475: 4 of 6 better, run 4 and run 6 worse); LC 1.673 1.993 2.153 (F8 4.745 4.853 3.947: 3 of 3 better); C02 1.702 1.729 1.816 (F8 2.121 2.143 2.239: 3 of 3 better).

Stress cases (mean):
| case | MF | LC | C02 |
|---|---|---|---|
| no structure (random normals) | 0.626 (= F8) | 4.515 (= F8) | 2.168 (= F8) |
| structure lost after 40 % | 0.558 | 3.560 | 1.870 |
| structure only after 40 % | 0.628 | 3.955 | **2.616 (worse than F8)** |
| 30 % outlier normals | 0.486 | 1.937 | 1.755 |
| 20 % of points | 0.578 | 2.147 | 1.879 |
| strong spurious plane fixed to the robot (30 % of points, oscillating +-10 deg) | 0.628 | 3.335 | **4.375 (5.6 on 2 of 3 runs)** |

## Known limits (to report, not hide)
1. A large planar object that moves with the robot and fills about a third of the vertical planar points can mislead it in a corridor where only one wall direction is visible (the per-direction veto needs two directions). Practical mitigation: exclude near-range points (self / carried objects) before computing normals.
2. If the reference is first built in a part of a building whose walls differ by a few degrees from those seen later, it can mistake the difference for heading drift (C02 "structure only after 40 %": 2.17 -> 2.62).
3. On Multi Floor two of six runs (the two best F8 runs) get worse by 0.04-0.11 m.

## Next (as of 17 Oct)
Live implementation in fusion_node_v2 (keyframe-rate SAH on A-LOAM registered scans, near-range filter), live runs on all three sequences, then an untouched sequence and a cave run (where SAH must switch itself off). The live results are in `SAH_Live_Results_F16.md`.
