# Test of the full R + T + T+ structure on the A-LOAM stack: rotation-aware R channel (design B, "F17b")
Written 28 Oct 2026, before any result. Purpose: decide, with rules fixed now, whether the R channel can be claimed as part of the structure on the A-LOAM stack. Background: F8 and F16 have the T channel (Schur weight on translation, C_T 0.03) and, in F16, the additional T (SAH), but rotation comes from VINS-Mono only (C_R = 0). A replay that made the Schur rotation weight active with a fixed c_R (from 0.003) made Multi Floor (0.62 to 1.3-2.0 m), Corridor02 (2.2 to 3.4-4.1 m) and Cave02 (4.5 to 5.7-8.8 m) worse and Long Corridor better (4.5 to 1.9 m) (`Configurations_Explained_and_Results_To_Date.md`, 6.3). The inference (not tested) is that A-LOAM's rotation is the weaker one on those sequences, so a rotation weight that is always on adds error.

## The design (B), fixed now
F17b = F16 plus an R channel whose weight depends on whether VINS-Mono's rotation can be trusted, the rotation analogue of the translation gate of G18/G20:
- R weight W_R = (c_R S_RR + gamma_R I)^-1 c_R S_RR, the same `info_weight` form as the T channel, with a rotation-specific VIO information gamma_R.
- gamma_R = 1 while the rotation check is open (healthy), gamma_R = 0 while it is closed (LiDAR rotation carries the step in every direction with LiDAR information), as in the translation check.
- Rotation check: over windows of 2 s (fast) and 10 s (slow) of FUSED rows, e = || log(dR_lidar^T dR_vins) || (rad), VINS moved to the LiDAR frame with the extrinsic. The check is open if e <= ref for both windows; gamma_R = the smaller of the two. ref = the largest e on the Multi Floor calibration recordings, per window length (same rule as 0.156 / 0.278 / 2.16 m). No other data sets the constants.
- Rotation guard (mirror of the LiDAR blow-up guard): a LiDAR rotation increment above 3 x the largest 2 s LiDAR rotation on the same calibration recordings is treated as a LiDAR failure; the step is carried by VINS-Mono and the check is not fed.
- c_R in the healthy state: the largest value on the grid {0, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3} for which the Multi Floor calibration mean ATE stays within 0.05 m of F16 (the rule used for G22). If only 0 qualifies, the healthy state is exactly F16 and R acts only through the check; that is reported as such, not as an active R in healthy data.
- Everything else (C_T 0.03, no kappa gate, SAH on, warm-up 20 s) is F16. Switch `ROT_CHECK=1`, default off, so F0-F16 stay bit for bit unchanged (unit test).
- Open item to settle in Phase 1, not by looking at scores: in the live loop, A-LOAM scan-to-map is seeded by the fused pose, so its rotation is partly VINS-Mono's own; the scan-to-scan odometry (`/laser_odom_to_init`) is independent of the prediction and is the cleaner reference. Phase 0 can only use the logged scan-to-map output and therefore understates disagreement.

## Phase 0 (offline, read-only, existing logs, no run)
`fusion_v4/rot_consistency_scan.py` reads the F8/F16 logs and prints, per log and window, the percentiles and maximum of e, split into a yaw part (about world-up) and a tilt part. Questions it answers: (a) what ref values the calibration recordings give; (b) how often the check would close on the healthy recordings (Long Corridor, Corridor02, Cave02, GEODE F16, farm live F8). Rule: if the check would close on more than 2 % of FUSED windows of any healthy recording, B is not equal to F16 there; this is reported and the design is not tuned to remove it.

## Phase 1: implementation
`ROT_CHECK` in `fusion_core.py` / `fusion_node_v2.py` with unit tests: off = identical to F16; a synthetic VINS rotation failure closes the check within the fast window; a synthetic LiDAR rotation blow-up is caught by the guard.

## Phase 2: equivalence on healthy data (live, A-LOAM stack)
Multi Floor x3 (1.0x), Long Corridor x3 (0.5x), Corridor02 x2, Cave02 x2, the same procedure as the F16 runs; F16 reference values are its recorded means. Criteria fixed now: (E1) mean ATE of F17b within max(0.1 m, 10 %) of F16's on each sequence; (E2) the check closed on less than 2 % of FUSED windows. Both must hold on all four sequences for "matches F16 on healthy data". Multi Floor is the calibration sequence; Long Corridor, Corridor02 and Cave02 are partly development data for SAH, so they are reported as such.

## Phase 3: rotation-failure test (live Gazebo, same farm world, same Husky)
Route: the L route with in-place turns inserted (4 turns of 360 degrees at 1.5 rad/s, one at each corner and one at mid-leg), 0.25 m/s elsewhere; driver `waypoint_driver_spin.py` (to be written and fixed before any run; parameters above). Preconditions, checked on the first run before F17b is judged: (P0a) VINS-Mono alone fails the turns (ATE > 2.5 m or VO_FAIL episodes during turns); if not, the test does not exercise the case and is declared void, not adjusted. (P0b) A-LOAM unfed does not fail (ATE <= 2.5 m, end-point error <= 5 m), because the LiDAR is the rotation reference. Methods, 3 runs each, each from a full clean restart: F5 (A-LOAM unfed), F16, F17b; VINS-Mono alone comes from the same logs. Criterion R1 ("wins"): F17b ATE lower than F16 by more than 0.1 m and 10 % in 3 of 3 runs. All runs reported, including failed starts.

## What each outcome allows to be claimed
| Outcome | Claim |
|---|---|
| E1, E2 and R1 all hold (P0 holds) | Full R + T + T+ structure on the A-LOAM stack: equal to F16 on healthy data, better when VINS rotation fails. |
| E1, E2 hold, P0a fails (VINS survives the turns) | Structure present, benefit of R not demonstrated; claim T + T+ plus R as an unproven safeguard. |
| E1 or E2 fails | B is not equivalent to F16 on healthy data; reported, redesign is a new, separately declared step. |
| R1 fails with P0 holding | R does not help even where it should; claim T + T+ only on this stack. |
Limits: a design chosen after the replay result was known; constants come only from Multi Floor; one world and one kind of rotation failure in simulation; the check treats the LiDAR as the rotation reference (it cannot tell which sensor is wrong, as for translation).
