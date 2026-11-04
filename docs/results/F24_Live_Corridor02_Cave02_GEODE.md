# F24, one live run each on Corridor02, Cave02 and GEODE stairs (4 Nov 2026, laptop, front end only, no loop closure)

Config F24 (frozen, commit 3398697 and earlier): `FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1 ROT_CHECK=1 OT_SRC=geom OT_MODE=gmax VIO_CHECK=1 VIO_CHECK_FAST=5 LIDAR_GUARD_T=2 LIDAR_GUARD_EX=4.325 VIO_CHECK_REF=0.157 VIO_CHECK_FAST_REF=0.277 VIO_CHECK_START=1 HANDOVER=anchor PREDICT_GUARD=1`. Replay rates Cave02 0.5x, GEODE 0.5x, Corridor02 0.33x. Full-span ATE RMSE / max (Umeyama SE(3), no scale). Single runs; nothing changed after a score. All three on the laptop (earlier GEODE runs in `claude/GenZ_fusion_v4_RateControl_and_GEODE_Results.md` were on the PC).

| Sequence | Status of the sequence | F24 RMSE / max (m) | GT path | Rows | Reference (earlier, other configs) |
|---|---|---|---|---|---|
| Corridor02 | development data for F22/F23/F24 (handover diagnosis) | **1.47 / 2.51** | 695 m | 8291 | F16 1.71 +- 0.07; F20 live 1.75 (L2 rule: within +0.05 of F20: met) |
| Cave02 | not clean: its logs were used in post-hoc diagnostics of VINS-Mono scale | **7.55 / 12.63** | 475 m | 9462 | F16 4.40 +- 0.61 (rule L3: not above 5.01: **not met**); GenZ-LIO alone 0.28 |
| GEODE stairs alpha | not clean (same reason) | **6.15 / 14.00** | 301 m | 3217 | F16 17.5-19.8; A-LOAM alone 7.98 (PC); GenZ-LIO alone 0.35-0.49 (PC); published alpha: LIO-SAM 6.30, FAST-LIO2 4.69, DLIO 4.89, R3LIVE 4.54, RELEAD 0.57 |

Switch-SLAM publishes no result on any of the three.

## What the logs show (diagnostics after the scores, not tests)
- **Cave02:** modes WARMUP 1269 / FUSED 8189 / VO_FAIL 11 (FUSED from 129 s). Error per 60 s window (after one global alignment): about 12 m in the first four minutes, about 5 m afterwards (about the F16 level). Fused path 552 m against 475 m of ground truth (+16 %). VINS-Mono steps are 1.3 times the LiDAR steps (median 0.077 against 0.058 m). So the excess comes from the early part (LiDAR-only warm-up and its handover), not from the whole run. Cause not isolated by a further run.
- **GEODE:** modes WARMUP 1415 (44 %) / VO_FAIL 1103 (34 %) / FUSED 707 (22 %); the mean handover step is 30.6 deg; VINS-Mono alone is useless here (186 m). F24 therefore ran as LiDAR-only A-LOAM for about 78 % of the scans, and 6.15 m is about the A-LOAM-alone level (7.98 m, another machine). Fused path 371 m against 301 m (+23 %).
- **Corridor02:** FUSED 89 %, VO_FAIL 0; path 738 m against 695 m (+6 %); the trajectory follows the ground truth in the map render.

## What can be claimed
- F24 improves on F16 on Corridor02 (1.47 against 1.71) and on GEODE (6.15 against about 18.7), and is worse than F16 on Cave02 (7.55 against 4.40). One run each.
- On GEODE the result is about LIO-SAM's published level and far from the best published (RELEAD 0.57) and from GenZ-LIO alone (0.35-0.49). F24 on A-LOAM + VINS-Mono does not compete with LiDAR-inertial front ends there.
- No comparison with Switch-SLAM is possible on these sequences (no published number); see `SwitchSLAM_Exact_Replica.md` for the replica runs.
- Cave02 and GEODE are not clean held-out tests; Corridor02 is development data. State this in the report.

Map renders (RViz-style, map from the recorded keyframes at the fused poses): `rviz_CAVE.png`, `rviz_GEODE.png`, `rviz_C02.png`.
