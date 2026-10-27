# fusion_v4 (GenZ-LIO front end): Multi Floor results and frozen weights (21 Oct 2026)

Data: three live G0 runs (GenZ-LIO alone, frozen GenZ config = its own Multi Floor file + our extrinsic, VINS-Mono + bridged information logged, keyframes recorded), plus one live G17 run (complete configuration). Everything below except the live G17 run is an exact offline replay (GenZ-LIO takes no feedback from the fusion node). Metric: full-span ATE RMSE, Umeyama SE(3), no scale (same as all earlier tables). Multi Floor is the tuning sequence, so all weights below are in-sample.

## Results (ATE m, runs 1/2/3, mean, sd)
| Config | run1 | run2 | run3 | mean | sd |
|---|---|---|---|---|---|
| G0: GenZ-LIO alone | 0.876 | 0.525 | 0.307 | 0.569 | 0.287 |
| VINS-Mono alone (same runs, live) | 1.274 | 8.905 | 1.255 | 3.81 | |
| G8: F8 rule (rotation from VINS-Mono), c_T=1e-4 | 0.705 | 9.030 | 0.565 | 3.433 | 4.848 |
| G16: F8 rule + SAH | 1.325 | 9.073 | 0.927 | 3.775 | 4.593 |
| **G9: R and T both Schur-active (c_T 3e-6, c_R 5e-6)** | 0.587 | 0.393 | 0.281 | **0.420** | 0.155 |
| **G17: G9 + SAH (replay)** | 0.551 | 0.359 | 0.256 | **0.388** | 0.150 |

Reference (A-LOAM master): F8 0.617, F16 0.640; Switch-SLAM Table II 1.61; GenZ-LIO paper 0.26 (per-sequence tuned); iG-LIO 0.25.

## Live confirmation (G17_kf_run1, 21 Oct 15:33)
Complete configuration run live (GenZ-LIO + VINS-Mono + Schur R and T + SAH, frozen weights): **0.293 m** full span, max 0.93 m, 4136/4136 scans, FUSED from +40.5 s. A fresh GenZ-LIO run, so not the same data as the G0 runs.

Ablation from this one run's own log (same GenZ and VINS data in every row): GenZ-LIO alone 0.626; VINS-Mono alone 1.251; old rule G8 0.641; G9 0.337; G17 replay 0.287 (live 0.293, replay agrees with live to 0.006 m).

SAH applied -4.44 deg in total (434 of 4136 rows, max step 0.25 deg). Median FUSED weights: translation 0.67 / 0.82 / 0.91, rotation 0.98 / 1.00 / 1.00 (GenZ rotation is trusted almost fully, VINS-Mono translation fills the weakly constrained directions).

## Loop closure on G17 (offline back end, same settings as before)
Multi Floor G17 run: 221 loops accepted. Full-span ATE 0.293 (no loops) -> 0.391 (odometry noise 1.46 deg / 0.054 m, the A-LOAM calibration) and 0.349 (noise measured on the calibration segment, 0.97 deg / 0.042 m). Loop closure makes G17 worse on Multi Floor; the front end is already accurate and the ICP loops add more error than drift they remove (with A-LOAM F8 0.617 -> 0.347). Most accepted loops join keyframes only ~30 s apart (local revisits). No parameter was changed.

## Findings
- With A-LOAM, rotation from VINS-Mono helped (A-LOAM rotation was the weak part). With GenZ-LIO (tightly coupled, IMU rotation), VINS-Mono rotation is the weak link: in run 2 VINS drifted to 8.9 m and the F8/F16 rule inherits it (3.4-3.8 m).
- Making the rotation channel an active Schur weight (S_RR, c_R) fixes it: the information tells the fusion to trust GenZ-LIO rotation. This is exactly the project's R and T structure: R and T from Schur, SAH as additional T.
- Valley is flat: mean 0.42-0.46 for c_T 1e-6..1e-5 and c_R 2e-6..3e-5. Chosen plateau middle: c_T = 3e-6, c_R = 5e-6 (mean 0.420).
- SAH helps in all 3 replay runs (0.587->0.551, 0.393->0.359, 0.281->0.256) and in the live run's ablation (0.337->0.287).
- Loop closure does not help G17 on Multi Floor.

## Frozen for all other sequences
GENZ_C_T = 3e-6, GENZ_C_R = 5e-6 (G9, G17); GENZ_C_T_F8 = 1e-4 (ablation G8, G16). SAH unchanged (StructureHeadingV6, bound_R). Defaults are in run_fusion_study.sh. Do not retune on LC, C02, Cave02, GEODE.

## Caveats
- In-sample on Multi Floor; generalisation to Long Corridor, Corridor02, Cave02 is the real test. **First held-out result: it did not generalise; see GenZ_fusion_v4_HeldOut_Results.md.**
- GenZ-LIO alone varies by 0.3-0.6 m between identical runs (0.31-0.88): GenZ-LIO is multithreaded and replayed at 1x with other nodes running.
- 0.293 is one live run; the replay mean is 0.388.
