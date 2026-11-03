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
