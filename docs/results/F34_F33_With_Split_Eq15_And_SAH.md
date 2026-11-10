# F34: F33 with a split Eq. 15 and the structure-anchored heading (10 Nov 2026), rules written before the run

## Why
F33 (Switch-SLAM structure, our detection, VINS-Mono rotation when trusted) gave 0.83 / 1.74 m on Multi Floor, 9.73 / 22.23 on GEODE and 4.29 / 10.09 on Long Corridor (one run each), against F26 0.54, 3.26 to 6.36 and 2.10. The Long Corridor log showed two things: 82.7 % of scans in the degenerate branch, where Eq. 15 takes the plain mean of the LiDAR step (flagged directions removed) and VINS-Mono's step, and a final heading error of -6.2 deg, about what SAH corrects there (F16 runs: -5.8 deg). F34 changes those two things and nothing else. GEODE stays limited by A-LOAM and VINS-Mono (F25 doc); nothing here is aimed at it.

## What changes against F33
1. **Eq. 15 split** (`EQ15_MODE=split`, our detector only). The printed Eq. 15 is the mean of the two steps, so along a flagged direction the output moves half of VINS-Mono's step, and along the well-conditioned directions half of the LiDAR's correction. F34 takes, per direction, a 0 / 1 information weight: x = x_l + P x_v, with x_l the LiDAR step with the flagged directions removed and P the projector on the flagged directions. Not F24's soft weights; a hard partition by our own detection.
2. **Structure-anchored heading** (`SAH=1`): F24's module and settings (`structure_heading.make_sah()`, KF_DIST 1 m, KF_ROT 0.2 rad, r in [1, 60] m, voxel 0.25, 6000 points, correction applied at most 0.25 deg per scan about the VINS-Mono vertical). Active only on scans where VINS-Mono is trusted (the counterpart of F24's FUSED mode); stale corrections are dropped when it is not. The correction goes into the same rotation chain that VINS-Mono's rotation drives.
Config `F34` = F33 + `EQ15_MODE=split SAH=1`. No new constant. Defaults reproduce F33 (23 detector / core tests, 11 core tests, node plumbing and gyro tests pass). Two new tests: split vs mean at a flagged direction; and a SAH plumbing test with a synthetic room (VINS-Mono yaw drifting 0.04 deg/s: final heading error 4.80 deg without SAH, 1.59 deg with it, no change without drift, no warnings).
Not added: the anchored handover and the VINS-motion guard of F24. F33 has no warm-up mode to anchor, and a distrusted VINS-Mono is already kept out of the guess (F32 checks).

## Run (batches/f34_lc.sh, about 20 min)
Long Corridor F34 run 1.

## Predictions written before the run
- SAH removes most of the -6 deg end heading error and the split removes the halving along the corridor: 2 to 3.5 m. Not a result.
- The two changes are applied together, so a result cannot say which one did it.

## Reading rules
1. Preconditions (else void for the claim, reported, not adjusted): tensor found for at least 95 % of scans; SAH saw at least 50 keyframes and accepted at least 20 (`sah_acc` in the log, node output).
2. Bands (Long Corridor): up to 2.15 m = inside the F24 / F26 spread; above 2.15 and up to 2.42 = between that spread and the published Switch-SLAM RMSE; above 2.42 and below 4.29 = better than F33, above the published value; 4.29 or more = no improvement on F33. A diverged or crashed run counts.
3. Report: ATE RMSE / max, heading error against ground truth at 50 / 100 / 200 s and end, total SAH correction (`sah_total_deg`), degenerate share, case 3 count, `sw_rotv` share, angle between output and A-LOAM rotation.
4. n = 1 supports no claim. Long Corridor was used to choose these two changes (the F33 result motivated them), so it is development data for F34. Adoption needs held-out bags and repeats, and Multi Floor must not get worse (F33 0.83, F24 / F26 0.45 to 1.01).

## Result: Long Corridor run 1 (uploaded f34_lc_small.zip, 10 Nov 2026)
ATE RMSE / max, full span: **3.89 / 6.91 m** (2769 poses, GT path 579.2 m). F33 4.29 / 10.09; published Switch-SLAM 2.42 / 5.09; F24 1.75 to 2.15; F26 2.10 / 3.73; VINS-Mono alone 4.94 / 12.44 in this run.

Preconditions (rule 1): tensor found for 2774 of 2774 scans; SAH saw 522 keyframes, accepted 281 (rejected 184 on structure, 52 on the gate), none dropped. Both met. SAH's net applied correction at the end: -7.09 deg (node output).

Band (rule 2): above 2.42 and below 4.29 m = **better than F33, above the published value**. The prediction (2 to 3.5 m) was too low: the result is above it. The max error fell more (10.09 to 6.91) than the RMSE (4.29 to 3.89, 9 %). One run each, and the spread of this stack on this bag is not known for F33 or F34 (F24 alone spans 0.4 m over three runs), so the 0.4 m difference is not shown to be real.

From the log:
- Same switching as F33: degenerate branch 82.6 % (R 81.8 %, T 0.0 %, TT 47.8 %), 1.30 directions removed per scan on average, case 3 on 2223 scans; VINS-Mono failed 2.9 % (F33 0.5 %), `sw_rotv` 97.1 %.
- Heading error of the output against ground truth: -1.1 / -3.1 / -2.1 deg at 50 / 100 / 200 s, -5.0 at the end (F33 -1.5 / -3.1 / 0.8 / -6.2). VINS-Mono alone drifted to -9.1 deg in this run (F33 run: -6.2), so the anchor worked against a larger error, and the end result is only 1.2 deg better than F33's. Not the dominant error source either way.
- Path length against ground truth: output 1.037 (F33 1.017), VINS-Mono 1.002. The output path is 3.7 % long, so a VINS-Mono scale deficit is not the explanation.
- Error against a whole-run alignment by 40 s window: 5.2 / 2.8 / 2.8 / 2.7 / 3.6 / 5.2 / 3.4 m, a broad level of 3 to 5 m and not a drift curve. I have not found its cause. Output ATE is still close to VINS-Mono alone (3.89 against 4.94).
- Untested ideas, none run: (a) the hard 0 / 1 split removes any LiDAR information along a flagged direction, while F24's soft weights keep a partial share; (b) the R channel fires on 82 % of corridor scans. Either would be a change made after seeing this result and needs new rules and held-out bags.

Logging bug found while reading: the SAH columns of the switching log (`sah_corr_deg`, `sah_total_deg`, `sah_acc`) were left at 0 in this run (my edit to the row writer did not apply); SAH itself ran (node output above). Fixed afterwards, with a test that the column equals the applied correction; the numbers above come from the node output, not the log columns.

Summary, Long Corridor: F33 4.29 / 10.09, F34 3.89 / 6.91, F26 2.10 / 3.73, published 2.42 / 5.09. F34 is not run on any other bag. Multi Floor must be checked for harm before any adoption (rule 4).
