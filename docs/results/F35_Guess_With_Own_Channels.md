# F35: F26 with the starting guess decided by our own channels (10 Nov 2026), rules written before any run

## What changes against F26
F26 chooses A-LOAM's scan-to-map starting guess by the published degeneracy rule (three smallest normalised Hessian eigenvalues against 0.12 / 0.27 / 0.48, a five-scan status queue, A-LOAM's own step / blend / VINS-Mono's step). That rule fires on 0 to 10 % of scans (Cave02 0.0 %, Multi Floor 1.5 %, Long Corridor 4.5 %, GEODE 10.3 %), so the guess is almost always A-LOAM's own step, and the system carries two different definitions of "degenerate" (the published one for the guess, our channels for the fusion weights).
F35 removes the published thresholds. The same status rule (queue of 5, same three guess kinds, same blend) is driven by our own detection: R channel (rotation Schur complement, condition number above 15.7), T channel (translation Schur complement, information weight c_T = 0.03, flagged below 0.5) and the additional-T channel (translation information limited by the orientation tensor of the keyframe geometry, minimum rule). A scan is flagged if any channel flags it. The blend weight is the same information weight as in F30 to F34.
Everything else is F26: fusion weights, gates, guards, warm-up, handover, heading anchor, constants. Config `F35` = F26 + `GUESS_MODE=ours DET_CH=R,T,TT DET_CT=0.03 DET_KR=15.7 DET_TT_RULE=min` (the constants are the ones already frozen for our detector; none set for this test).
Implementation: `StatusGuess(detector=...)` in `guess_status.py`; the node rotates the keyframe orientation tensor with the last mapped scan's rotation for the guess (one scan old). Default `GUESS_MODE=status` reproduces F26 (all earlier tests pass; four new guess tests and a node smoke test (`test_fusion_node_ours.py`: the callbacks run on a synthetic room with F35 settings, a weak translation direction turns the guess into the VINS-Mono step): well conditioned gives the LiDAR step, a weak translation direction gives the VINS-Mono step after a full queue, the additional-T channel flags a geometry with no support along x, a VINS-Mono step above 1 m is treated as absent).

## What to expect, from logs of other runs (not from this config)
Our channels flag the scan far more often than the published rule: degenerate share 82.7 % on Long Corridor, 46 % on Multi Floor, 54 % on GEODE (F30 to F34 logs; those runs use the same Hessian). So the guess should be VINS-Mono's step on a large share of corridor scans, close to the earlier design that always puts VINS-Mono's motion into the guess. On bags where VINS-Mono is distrusted (GEODE: 76 % of scans) the rule falls back to A-LOAM's step.

## Predictions written before the run
- Long Corridor: 1.7 to 2.2 m, as the always-VINS-guess design (1.75 to 2.15 over three runs) and F26 (2.10).
- Multi Floor: 0.4 to 0.7 m (0.45 to 1.01 over earlier runs, F26 0.54).
- Not results.

## Reading rules
1. Long Corridor: up to 2.15 m = inside the 1.75 to 2.15 spread; above 2.15 and up to 2.42 = between that spread and the published Switch-SLAM RMSE; above 2.42 = higher than the published value and than F26. Multi Floor: 0.45 to 1.01 = no change visible; above 1.01 = worse than every earlier run.
2. Report the guess kinds actually used (LIDAR / INTERP / VINS, from `guess_kind`), the fused ATE and max, and the scan-to-map ATE of A-LOAM's own pose.
3. n = 1 supports no claim; a failed run counts. Multi Floor is the calibration bag of the gates and Long Corridor was used to build F33 / F34, so both are development data. Adoption needs held-out bags and repeats.
4. What this tests: whether removing the published thresholds from F26 changes anything. If the result is inside F26's spread, the thresholds can be dropped for simplicity without a measured loss, not shown to be better.

## Run (batches/f35_test.sh)
Default one Long Corridor run (about 20 min). `ONLY="MF"` or `ONLY="LC MF"` for others.

## Result: Long Corridor run 1 (10 Nov 2026)
Fused ATE 1.99 m RMSE, 3.54 m max (n = 2769 poses, GT path 579.2 m). Scorer: Umeyama SE(3), no scale, full span.
- Rule 1: 1.99 is up to 2.15, inside the 1.75 to 2.15 spread of the always-VINS-guess design. It is also below F26's 2.10 / 3.73 and below the published Switch-SLAM 2.42 / 5.09 (published numbers are from another setup; not a like-for-like claim).
- Rule 2, guess kinds used (2776 rows): VINS-Mono step ("VO") 2025 (72.9 %), LiDAR step 506 (18.2 %), blend ("INTERP") 243 (8.8 %), 2 rows without one (init). So our channels put VINS-Mono's step into the guess on about three quarters of scans, against F26's published rule which used it on 0 to 10 %.
- Scan-to-map ATE of A-LOAM's own pose (aft columns): 1.13 / 2.84 m, lower than the fused 1.99 / 3.54. VINS-Mono alone from the same log: 4.99 / 10.85 m.
- Rule 4 reading: the result is inside F26's spread, so the thresholds could be dropped for simplicity without a measured loss on this bag. Not shown to be better. n = 1, Long Corridor is development data (used to build F33 / F34). Multi Floor not run.
- Observation, not a finding: A-LOAM's own pose beats the fused output here. The fusion output on Long Corridor is therefore costing accuracy relative to the scan-to-map pose in this run; one run, cause not tested.
