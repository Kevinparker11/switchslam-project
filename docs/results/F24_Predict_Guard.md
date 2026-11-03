# F24: no VINS motion in A-LOAM's mapping guess while VINS is failing (3 Nov 2026)

## 1. Finding (Farm F23 live run, 3 Nov 2026; logs in ~/farm_f23)
Farm F23 scored 0.496 / 5.308 m (rule 0.38 / 1.10: not met). All of the excess is in the first 18 s after the reset: from 20 s on the fused output is
0.319 / 0.765 m. In that window:
* VINS-Mono was failing: 97 VO_FAIL rows, VINS steps above 0.5 m on 125 of 269 rows (up to 4 m per scan; the robot moved 2.5 cm per scan).
* A-LOAM's scan-to-map pose made 40 steps above 0.3 m (0.4-2.5 m per scan); 36 of the 40 are on rows where the VINS step is above 0.5 m. In 18-40 s and
  after 40 s there is not a single VINS step above 0.5 m or A-LOAM step above 0.3 m (0 of 4561 rows).
* The LiDAR Hessian was not degenerate on those rows (e_min / e_max of the translation block 0.116 against 0.102 after 25 s), and the rotation tracked
  (A-LOAM yaw -101 deg against ground truth -89 deg over 0-20 s, within 12 deg). The translation was the failure, not the observability.
* The anchored handover is not involved: one handover at 40.0 s after the reset, 0.43 deg.

## 2. Mechanism (read from the code, not yet proven by an intervention)
`fusion_node_v2.laser_odom_cb` publishes, for every scan, the initial guess for A-LOAM's scan-to-map matching on /switch_fused_pose:
`FusionCore.predict` = last fused pose moved by the VINS motion since then, used in every mode (WARMUP, VO_FAIL, FUSED) unless the VINS step is above
3 x jump_max = 3 m. The failure rule of the same node calls a VINS step above jump_max = 1 m (or 0.5 rad) a failure. So a VINS step of 1-3 m was
declared a failure by one rule and used as the mapping guess by the other. A guess off by 1-3 m puts the local scan-to-map optimisation into a wrong
minimum, and the result is fed back as the pose. This explains why the jumps appear only while VINS fails. It is not the only explanation: the
teleport reset (0.88 m, inside the warm-up) and the 80 deg in-place start turn happen in the same window.

## 3. Change (FusionCore(predict_guard=True), env PREDICT_GUARD=1; default off = F0-F23 bit for bit)
The VINS motion is used for the guess only while VINS is trusted by the node's own failure rule: not after a VO_FAIL step, and the step within jump_max
and rot_jump_max (the numbers that already define a VINS jump). Otherwise the guess is the last fused pose. No new constant. Configs: `[F24]` = F23 +
PREDICT_GUARD=1. test_predict_guard.py (guard on: small step outside VO_FAIL used; 2 m step, a step after VO_FAIL, a 0.8 rad step not used; guard off: the old
rule); all earlier unit tests pass.
Replay cannot test this change: the harness is open loop (A-LOAM's poses are logged and are not re-seeded by the guess), so it only shows that the node
runs and that the logged output is unchanged. Only live runs can.

## 4. Live test, fixed before any run
Primary: Farm L route, F24, the same five-terminal procedure as Farm_F20_Live_Result.md, with the order changed so the cause can be separated: robot
reset first, then A-LOAM, VINS and the node started, and the driver started only after the node has been in FUSED mode for 20 s. Report from the reset (as
the rule above) and from the first FUSED row. Pass: RMSE <= 0.38 m and max <= 1.10 m from the reset. Also bag sequences live (Multi Floor, Long Corridor,
Corridor02, one run each, `run_f23_batch.sh` with CFG=F24): no regression against F23 live (MF 0.41 / 0.91, LC 1.75 / 3.02) beyond the run-to-run spread seen
so far. Nothing is changed after seeing a number; one Farm run supports no claim.

## 5. Live result: Farm L route, F24 (3 Nov 2026; protocol of section 4: reset first, driver started after the node was FUSED)
Numbers from the owner's `score_fused.py` printout and the attached logs (~/farm_f24). GT path 79.2 m, 4385 log rows from the first ground-truth sample (no reset jump in the file: 18 s before the robot moved, 323 s moving, 98 s standing after arrival), modes FUSED 4185 / WARMUP 199 / INIT 1, **no VO_FAIL row**, no VINS step above 0.5 m, no A-LOAM step above 0.3 m, one handover (1.5 deg at 45.9 s).
| Output | n | ATE / max (m) | end-point error (m) |
|---|---|---|---|
| **F24 fused** | 4385 | **0.657 / 0.897** | 0.673 |
| A-LOAM output (fed by the fused pose) | 4385 | 0.509 / 0.967 | 0.426 |
| VINS-Mono alone | 4385 | 2.067 / 3.306 | 2.445 |
Against the rule: **max 0.897 <= 1.10 met; RMSE 0.657 > 0.38 not met.** The F23 run's start transient (5.3 m) did not occur. Two things changed between the F23 and F24 runs (PREDICT_GUARD and the order of the steps: no teleport during the warm-up, driver started after FUSED), so this run cannot say which of them removed it; the guard stays unproven until a run with the old order and the guard on.
Where the remaining error is (moving rows only: fused 0.612 / 0.970, A-LOAM 0.463 / 0.833; so not the standing time): a steady 0.6-0.8 m offset, the fused path ends 0.65 m short of the ground truth on both legs. The LiDAR carries 73-87 % of the translation weight (mean W_t 0.76 / 0.81 / 0.87), VINS-Mono moves 9.1 % less than A-LOAM (path 72.9 m against 79.0 m ground truth) and the fused steps are 2.1 % shorter than A-LOAM's: the VINS scale error leaks through the remaining weight.

## 6. Replay of the same Farm log with the VINS scale correction (open loop, 3 Nov 2026; SAH / OT off because no keyframes exist for a live run; the bag-rig extrinsic file, not the live one, which was not attached)
VIO_SCALE_T rescales the VINS translation by the LiDAR / VINS path-length ratio over the last T s (existing option, off in F20-F24).
| Setting | Farm log ATE / max | 
|---|---|
| none (replay of the live run) | 0.714 / 0.895 (live 0.657 / 0.897) |
| VIO_SCALE_T=10 | 0.362 / 0.540 |
| VIO_SCALE_T=5 | 0.373 / 0.547 |
| VIO_SCALE_T=10 + VIO_SCALE_PROJ=1 | 0.342 / 0.506 |
| VIO_SCALE_T=10 + VIO_SCALE_ALONG=1 | 0.370 / 0.525 |
| both | 0.349 / 0.493 |
The same options on the 12 development logs (F23 = F21 + anchor, mean ATE): Multi Floor 0.531 -> 0.553 (PROJ 0.562, PROJ+ALONG 0.558); Long Corridor 1.703 -> 1.761 (1.979, 1.896); **Corridor02 1.569 -> 2.154 (2.326, 2.143)**. The no-regression bound L2 (+0.05 m on Corridor02) is violated by every variant, so none is adopted.
Why: path lengths against the ground truth. Farm: A-LOAM 0.999, VINS-Mono 0.909 (VINS is short, the LiDAR is metric: the correction is right). Corridor02: A-LOAM 1.049, VINS 0.997; Long Corridor 1.018 / 1.006; Multi Floor 1.023 / 0.984 (the LiDAR path is 2-5 % long, VINS is right: the correction scales a correct VINS up toward the LiDAR's error; the s estimate on Corridor02 has median 1.21 and 90th percentile 3.9). The premise "the LiDAR is metric" holds in the open farm and not in the corridors. A safe version needs a test of whether the LiDAR path length is trustworthy in the window; none exists yet. The options VIO_SCALE_PROJ and VIO_SCALE_ALONG are now exposed in fusion_node_v2.py (default off, no change to F0-F24).

## 7. Live bag runs of F24 (3-4 Nov 2026, laptop, front end only, one run each; logs attached)
| Sequence | F24 ATE / max (m) | F23 live | Switch-SLAM |
|---|---|---|---|
| Multi Floor | 0.45 / 0.92 | 0.41 / 0.91 | 1.61 / 3.63 |
| Long Corridor | 2.12 / 5.31 | 1.75 / 3.02 | 2.42 / 5.09 |
* The guard did not act in either run: no VO_FAIL row, no VINS step above jump_max = 1 m (largest 0.81 m on Long Corridor, 0.43 m on Multi Floor), no VINS rotation step above 0.5 rad (0.34 / 0.25). So both runs behaved as F23, and the differences from the F23 live numbers are run-to-run variation (live Long Corridor runs of one configuration have spanned 1.96-3.38 m: F20 3.38 / 1.96 / 3.05; F16 1.99-3.17). F24 is therefore not shown to help or to hurt on the bag sequences; it is inactive there.
* Long Corridor, L1 (rule of section 5 of F22_Handover_Anchor.md): RMSE 2.12 < 2.42 met; max 5.31 > 5.09 missed by 0.22 m; one of the three runs the rule needs.
* The Long Corridor maximum is at 9.6 s after the start, in WARMUP (LiDAR only, 211 rows), error mean 3.95 m in the first 30 s, 0.8-2.3 m afterwards. The direction of travel in the first 10 s is 3.4 deg off the ground truth, 1.1 deg at 20 s, 0.9 deg at 40 s, 0.5 deg at 60 s. The start point is 135 m from the centroid of the path, so with the full-span alignment a heading error of about 2 deg at the start is 5 m. One anchored handover, 2.95 deg at 20.6 s. The excess is in the LiDAR-only warm-up heading, not at the handover.
