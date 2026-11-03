# F22 / F23: anchored WARMUP -> FUSED handover (3 Nov 2026)

Goal set by the owner: the R + T + OT structure (F20 / F21) must beat Switch-SLAM (RA-L 2024, Table II, front end, no loop
closure) without loop closure and without per-bag tuning, and hold on sequences it was never developed on.

## 1. Diagnosis (existing logs, nothing re-run)
* Long Corridor, all 9 F16 / F20 live runs: the maximum error of the fused output is in the first 1-9 s of the run
  (4.9-8.4 m, mode WARMUP), while the A-LOAM map pose of the same run is 0.4-2.4 m at those times. Under the full-span
  alignment, a heading break later in the run rotates the start of the path away.
* The break is at the first FUSED scan. F20 LC run 1 (scan by scan, yaw change since 2 s before the switch): at 21.28 s the
  fused (= LiDAR) yaw is -10.65 deg, VINS -6.40, ground truth -11.90; at 21.48 s (first FUSED scan) the fused yaw jumps to
  -17.21 (ground truth -12.15). VINS was ~5 deg behind in a fast turn (about 38 deg/s) and caught up one scan later. The warm-up
  had already integrated the turn with the LiDAR rotation, and the first FUSED step added VINS's catch-up of the same turn:
  about 5 deg counted twice, kept for the rest of the run. This is the "yaw step at the switch" of F20_Live_Results.md.
* It is a transient, not a clock offset: angular-rate cross-correlation against the ground truth gives VINS -0.02..+0.01 s and
  A-LOAM -0.07..+0.01 s on Multi Floor, Long Corridor, Corridor02 and Cave02 (r = 0.88-0.97).
* Two other ideas were tested on the way and rejected: (a) output the A-LOAM map pose instead of the fused pose: better on
  Long Corridor (0.7-2.6 m vs 2.0-4.9) but worse on Multi Floor (1.8-2.4 vs 0.5-0.8), Corridor02 and Cave02; A-LOAM's tilt is
  wrong by 11-13 deg RMS on Multi Floor. (b) yaw-only LiDAR rotation increments with a tilt-agreement gate: worse everywhere
  (LC 4.5 -> 4.3-13.6, MF 0.63 -> 0.59-9.9), because gating increments biases the integrated heading.

## 2. Change (fusion_core.FusionCore(handover="anchor"), env HANDOVER=anchor; default "none" = F0-F21 bit for bit)
At every entry into FUSED (after the warm-up, or after a VINS loss and its re-warm-up) the fused rotation is set to
R_off * R_vL(t): R_vL = VINS IMU rotation x R_IL (LiDAR orientation in the VINS world), R_off = robust chordal mean of
R_aft(s) R_vL(s)^T over every warm-up scan of the current VINS segment (outliers beyond 3 x the median distance, at least
0.5 deg, are dropped). The VINS then continues from a reference consistent with itself, so its own catch-up corrects the
transient instead of adding it, and the roll / pitch at the switch come from the gravity-observable VINS attitude. No new
constant: the window is the existing warm-up (T_WARM = 20 s). The step taken is logged (column handover_deg).
* Configs: `[F22]` = F20 + HANDOVER=anchor; `[F23]` = F21 + HANDOVER=anchor (run_fusion_study.sh).
* Tests: test_handover.py (a 5 deg VINS transient at the switch: old handover 5.000 deg mean heading error afterwards, anchored
  0.000; no transient: both exact; robust mean ignores 5 % outliers). test_fusion_core, test_rot_check, test_t_cap,
  test_ot_round2 unchanged and passing.

## 3. Replay through the real node (ot_study/round3/node_harness.py, the 12 development logs MF F8 kf 1-6, LC F8 kf 1-3,
C02 F8 kf 1-3 with their keyframe scans and extrinsics; open loop, so A-LOAM is not re-seeded by the new poses)
The harness reproduces the documented F20 replay exactly (MF 0.558, LC 2.010, C02 1.710).

| Config | Multi Floor ATE / max | Long Corridor ATE / max | Corridor02 ATE / max |
|---|---|---|---|
| F8 | 0.626 / 1.33 | 4.533 / 12.89 | 2.119 / 3.77 |
| F8 + anchor | 0.518 / 1.13 | 4.182 / 10.74 | 2.119 / 3.76 |
| F16 | 0.560 / 1.06 | 1.983 / 5.42 | 1.709 / 2.85 |
| F16 + anchor | 0.509 / 1.00 | 1.717 / 3.52 | 1.708 / 2.84 |
| F20 | 0.558 / 1.06 | 2.010 / 5.48 | 1.710 / 2.87 |
| **F22 (F20 + anchor)** | **0.506 / 0.99** | **1.743 / 3.57** | 1.709 / 2.87 |
| F21 | 0.583 / 1.10 | 1.970 / 5.39 | 1.571 / 2.65 |
| **F23 (F21 + anchor)** | **0.531 / 1.03** | **1.703 / 3.51** | **1.569 / 2.64** |
| Switch-SLAM (paper) | 1.61 / 3.63 | 2.42 / 5.09 | n/a |

Per run: F22 lower than F20 in 9 of 12 logs (all 3 LC, MF 1/2/5, C02 by < 0.002 m), higher in 3 (MF 3/4/6, by at most
0.014 m); the same 9 / 3 split for F23 against F21 (at most +0.015 m). Long Corridor max per run, F20 -> F22:
4.43 -> 2.77, 5.76 -> 3.29, 6.24 -> 4.66 m. Handover step: Multi Floor 3.1-3.3 deg in every run, Long Corridor 3.8-5.4,
Corridor02 2.1-2.4.

Held out (never used to design anything; only logs without keyframe scans exist, so SAH / OT cannot run there and the check is
the F8 rule and F8 + ROT_CHECK, with and without the anchor):
| Sequence | without | with anchor | handovers per run |
|---|---|---|---|
| Cave02 (F8 logs 1-3) | 4.709 / 4.307 / 4.398 | 4.696 / 4.294 / 4.381 | 1 |
| Cave02 (F16 logs 1-3) | 3.975 / 5.099 / 4.111 | 3.976 / 5.077 / 4.112 | 1 |
| GEODE stairs (F16 logs 1-2) | 20.611 / 17.258 | 20.200 / 16.741 | 4 (VINS losses) |
No harm on either; GEODE stays a VINS-Mono scale failure (that is what the VIO-trust check in F21 / F23 targets).

## 4. Limits
* Open-loop replay. The live LC F20 runs had larger steps (6.1-6.8 deg) than these F8 logs (3.8-5.4), so the live effect may
  be larger, but replays have been optimistic before (F20 LC replay 2.01, live 2.80). Only live runs count.
* Multi Floor, Long Corridor and Corridor02 were used for this diagnosis: they are development data for this change.
* The handover only fixes the switch; the slow VINS yaw drift after it is still corrected only by SAH.

## 5. Live test, fixed before any live run of F22 / F23
Primary configuration: **F23** (keeps R, T, OT and the VIO-trust check that guards against a failing VINS, as on the Farm and
GEODE). F22 is the ablation that shows the anchor on F20 alone. Front end only, no loop closure, full-span ATE RMSE and max,
Umeyama SE(3), no scale. Replay rates as before (MF 0.5x, LC 0.5x, C02 0.33x). Nothing is changed after seeing a live number.
* L1 (development, against Switch-SLAM): F23 mean over 3 live runs below 1.61 m (MF) and 2.42 m (LC), and every run's max
  below 3.63 m (MF) and 5.09 m (LC).
* L2 (no regression): F23 Corridor02 mean within +0.05 m of live F20 (1.753 m).
* L3 (held out, frozen, run only after L1 / L2): Cave02 F23 mean not above the F16 live range (4.40 + 0.61 m); GEODE and the
  farm L route reported against F16 / F21, whatever comes out.
* All runs are reported, including failed starts.

## 6. Live results (3 Nov 2026, laptop, front end only, no loop closure)
Reported in the order they were run; nothing changed between runs.
| Run | Config | Sequence | ATE RMSE / max (m) | Against |
|---|---|---|---|---|
| F21_kf_run1 | F21 | Multi Floor | 0.58 / 1.20 | Switch-SLAM 1.61 / 3.63; live F20 0.48 / 0.82; replay 0.583 / 1.10 |
| F23_kf_run1 | F23 | Long Corridor | 1.75 / 3.02 | Switch-SLAM 2.42 / 5.09; live F20 mean 2.80; replay 1.703 / 3.51 |
* L1 so far (Long Corridor): run 1 is below 2.42 m and its max is below 5.09 m. L1 needs 3 runs and Multi Floor, so it is open.
* Live agrees with replay (1.75 live against 1.70 replay), so the earlier optimism (F20 replay 2.01, live 2.80) did not repeat for this run.
* Single runs on development sequences. Remaining: F23 on Multi Floor and Corridor02 (3 runs each), 2 more Long Corridor runs, then L3.
