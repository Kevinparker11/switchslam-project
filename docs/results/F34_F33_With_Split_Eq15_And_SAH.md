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
