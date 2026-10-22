# Offline improvement tests (20 October 2026)

Replays of logged runs (fixed A-LOAM poses; replay reproduces live results within about 0.05 m). Metric: ATE RMSE, Umeyama SE(3), no scale, full span. Scripts: `improve/exp1_warmup.py`, `improve/exp2_sah_warm.py`. Nothing here is a live result and nothing was frozen.

## Test 1: warm-up length t_warm (F8, C_T 0.03; live setting 20 s)
| Seq | 0 | 5 | 10 | 20 | 30 | 40 | 60 | live |
|---|---|---|---|---|---|---|---|---|
| MF (9 runs) | 0.537 | 0.538 | 0.509 | 0.618 | 0.496 | 0.793 | 1.049 | 0.618 |
| LC (3) | 4.094 | 4.092 | 4.121 | 4.515 | 3.993 | 3.914 | 5.000 | 4.533 |
| C02 (3) | 2.163 | 2.161 | 2.160 | 2.168 | 2.160 | 2.160 | 2.160 | 2.119 |
| Cave02 (3) | 4.635 | 4.522 | 4.541 | 4.508 | 4.464 | 4.504 | 4.499 | 4.473 |
Result: differences are inside run-to-run spread (MF sd 0.11, LC sd 0.49), non-monotonic; no change justified.

## Test 2: SAH during warm-up and shorter warm-up (F16 replay, same logs and keyframes)
| Config | MF (6) | LC (3) | C02 (3) |
|---|---|---|---|
| F8 | 0.626 +- 0.107 | 4.515 +- 0.495 | 2.168 +- 0.063 |
| F16 (SAH FUSED only, t_warm 20) | 0.562 +- 0.049 | 1.940 +- 0.245 | 1.749 +- 0.060 |
| SAH also in WARMUP, t_warm 20 | 0.569 +- 0.121 | 1.935 +- 0.793 | 1.668 +- 0.054 |
| F16, t_warm 10 | 0.577 +- 0.126 | 1.607 +- 0.222 | 1.730 +- 0.074 |
| F16, t_warm 0 | 0.623 +- 0.116 | 1.587 +- 0.237 | 1.663 +- 0.053 |
(At t_warm 0 there is no WARMUP mode, so "SAH in WARMUP" is identical.)

Reading: t_warm 0 improved all three LC runs (-0.31, -0.43, -0.31 m) and all three C02 runs (about -0.09 m), but made 5 of 6 MF runs worse (+0.06 m mean) and Cave02 slightly worse (4.64 vs 4.47 m, no SAH there). LC and C02 are already SAH development data and MF is the tuning sequence, so this is a hypothesis, not a result. Applying SAH in WARMUP at t_warm 20 does nothing reliable (LC sd rises to 0.79).

## Not tested / blocked
- LiDAR-trust variants (C_T, W = I): already swept earlier (C_T chosen on MF; Cave02 sweep in `Cave02_Control_Results.md`); repeating would add no information.
- Corridor02 loop rejection: needs `keyframes_F16_kf_run1/2/6.npz` from `~/runs_corridor2/` on the laptop.
- Any real confirmation needs an untouched structured sequence run live with the frozen settings.

## Test 3: why Corridor02 runs 2 and 6 reject the long loop (F16 keyframes runs 1, 2, 6; 20 Oct)
Scripts: `improve/c02/diag.py`, `diag2.py`, `whatif.py`. Ground truth used for diagnosis only.
- The revisit exists in all three runs: 109-131 true long pairs (GT distance < 2 m, gap > 300 s); the estimated poses place them 2.1-5.7 m apart, vertical difference < 0.9 m. The 158 s <-> 695 s pair is within the search radius (8 m) in every run, but the candidate list (3 nearest per keyframe) rarely includes it.
- ICP finds the right alignment: for the pairs it accepts the loop error against ground truth falls from 3.8-4.2 m to 1.7-2.0 m.
- It is rejected by the correction gate: the correction needed is 4.04-4.21 m (runs 2 and 6) against a fixed `max_corr_trans` of 4.0 m (chosen on Multi Floor). In run 1 the same pair needed 3.74 m and was accepted. Run 2 also has fitness 0.49-0.52 against a 0.6 gate.
- Pairs with small corrections (0.5-1.6 m, fitness 0.25-0.45) are rejected by the fitness gate and would not help (loop error 3.5 m -> 3.5 m).

### What-if: `max_corr_trans` 4.0 -> 6.0 (iso, 1 round, odometry noise 1.46 deg / 0.054 m; nothing else changed)
| Set | 4.0 m | 6.0 m |
|---|---|---|
| C02 F16 run 1 | 0.808 | 0.808 |
| C02 F16 run 2 | 1.728 | 1.728 (fitness gate still rejects) |
| C02 F16 run 6 | 1.853 | 0.884 |
| LC F8 runs 1/2/3 | 2.907 / 3.249 / 1.831 | 1.569 / 3.249 / 1.756 |
| C02 F8 runs 1/2/3 | 1.155 / 1.277 / 2.198 | unchanged |
| MF F8 runs 1/2/3 | 0.397 / 0.304 / 0.354 | unchanged |
No run got worse. Caveat: Corridor02 and Long Corridor are development data for loops and SAH, 6 m is one untried-elsewhere value, and a wider gate can admit false loops on a sequence with repeated structure (the pose graph keeps a robust loss and chi2 check). Hypothesis only; not adopted.

## Test 4: Schur R (S_RR) as an active rotation channel (21 Oct; `improve/exp4_Rchannel.py`)
Replay of the logged F8 runs with LiDAR rotation weight W_R = (c_R S_RR + I)^-1 c_R S_RR, c_T 0.03, no gate. Mean ATE (m):
| Seq | c_R 0 (F8) | 0.003 | 0.03 | 0.3 | 3 | 30 |
|---|---|---|---|---|---|---|
| MF (9) | 0.618 | 1.337 | 1.793 | 1.968 | 1.993 | 1.995 |
| LC (3) | 4.515 | 2.339 | 1.936 | 1.941 | 1.942 | 1.942 |
| C02 (3) | 2.168 | 4.076 | 3.444 | 3.472 | 3.478 | 3.479 |
| Cave02 (3) | 4.508 | 5.695 | 8.188 | 8.755 | 8.813 | 8.819 |
Reading: S_RR does not discriminate good from bad LiDAR rotation (the weight saturates at the smallest c_R). Active LiDAR rotation helps Long Corridor and hurts Multi Floor, Corridor02 and Cave02 (4.5 to 5.7-8.8 m), as found on 17 Oct.

## Test 5: an alternative T (orientation tensor of scan normals) against Schur T (21 Oct; `improve/exp5_altT.py`)
Per keyframe window (10 s, >= 2 m travelled; MF 2378, LC 1562, C02 1949 windows): weakest eigenvector of Schur S_tt against weakest eigenvector of the normals' orientation tensor, and Spearman correlation of each statistic with the A-LOAM displacement error per metre against ground truth.
- Direction agreement |cos| between the two weakest directions: median 1.00 (MF), 0.99 (LC), 0.99 (C02). The two channels see the same weak direction.
- Error per metre (all directions), Spearman: Schur lambda_min +0.25 / -0.07 / +0.03 (MF / LC / C02); tensor l1 +0.35 / -0.18 / +0.04.
- Partial Spearman of tensor l1 given Schur: +0.24 [0.15, 0.32] (MF), -0.18 [-0.28, -0.06] (LC, wrong sign), +0.02 [-0.08, 0.13] (C02). Block-bootstrap intervals.
Reading: not validated as independent information. Inconsistent in sign across sequences. Windows are noisy labels and all three sequences are development data. Schur T is not beaten by the tensor on any sequence.
