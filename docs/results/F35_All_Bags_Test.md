# F35 on all bags: rules written before the runs (10 Nov 2026)

Config F35 (F26 with the starting guess decided by our own channels, see F35_Guess_With_Own_Channels.md). Nothing changed since the Long Corridor run 1 (1.99 / 3.54 m).

## Runs (batches/f35_all.sh, about 3 h on the laptop)
Multi Floor 2 runs, GEODE 3 runs, Long Corridor run 2 (run 1 exists), Cave02 1 run, Corridor02 1 run. Run counts match F26's where the time allows (F26: Multi Floor 1, Long Corridor 1, Corridor02 2, Cave02 1, GEODE 3). Same replay rates, extrinsics and scorer as the F26 runs; front end only, no loop closure.

## Comparison values (F26 live, RMSE / max, m)
Multi Floor 0.54 / 1.01; Long Corridor 2.10 / 3.73; Corridor02 1.93 / 3.46 and 2.04 / 3.46; Cave02 6.23 / 10.56; GEODE 6.36 / 14.07, 3.26 / 7.81, 5.51 / 15.25. Published Switch-SLAM (other setup): Multi Floor 1.61 / 3.63, Long Corridor 2.42 / 5.09.

## Predictions (not results)
- Multi Floor 0.4 to 0.7 m; Long Corridor 1.7 to 2.2 m (run 1 gave 1.99).
- Corridor02, Cave02, GEODE: inside F26's range, because the published rule fires on 0 to 10 % of scans there and our channels differ most on corridors. On Cave02 and GEODE, where VINS-Mono is distrusted, the guess should fall back to A-LOAM's step, so F35 should equal F26 to within run noise.

## Reading rules
1. Per bag, compare the F35 mean (or the single run) with the F26 values above. Tie band max(0.1 m, 10 %) of the F26 mean. Inside the band = no change visible; outside = better or worse.
2. Also report for each run: guess kinds used (LIDAR / INTERP / VO shares), the fused ATE and max, and A-LOAM's own scan-to-map ATE (aft columns).
3. "F35 can replace F26's published thresholds without a measured loss" requires no bag worse than its tie band. One bag worse than the band = "not equivalent on <bag>", reported with the guess shares. "F35 is better" requires at least two bags better beyond the band and none worse. Anything else is "no change shown".
4. n is 1 to 3 per bag and F26 has 1 to 3 runs per bag, so no significance is claimed; run-to-run spread is shown where there are repeats. A failed run counts. If a run's own spread (max - min over repeats) exceeds the band, the comparison on that bag is "inconclusive" instead of better or worse.
5. All bags are development data for F26 / F35 (Multi Floor calibrated the gates; Long Corridor, Corridor02, Cave02, GEODE were used in F24 to F34 work). No held-out claim. A run that fails a precondition (bag missing, node crash) is reported as void, not rerun with changes.

## Result (runs finished 10 Nov 2026, 19:11 to 21:07 IST; scored with the rules above, nothing changed after the runs)

Scored with the same scorer as the batch (SE(3) Umeyama, no scale); the scorer reproduces the batch's ATE files to 0.01 m. Scripts: scratchpad f35all/score_f35.py (not in the repo).

| Bag | F26 live (RMSE / max, m) | F35 runs (RMSE / max, m) | F35 mean | Band | F35 spread | Reading |
|---|---|---|---|---|---|---|
| Multi Floor | 0.54 / 1.01 (n=1) | 0.80 / 1.37, 0.66 / 1.12 | 0.73 | 0.10 | 0.14 | inconclusive (spread above band) |
| Long Corridor | 2.10 / 3.73 (n=1) | 1.99 / 3.54, 2.40 / 4.51 | 2.20 | 0.21 | 0.41 | inconclusive (spread above band); mean inside the band |
| Corridor02 | 1.93 / 3.46, 2.04 / 3.46 (mean 1.99) | 2.82 / 5.19 (n=1) | 2.82 | 0.20 | n/a | worse (+0.84 m, max 5.19 vs 3.46) |
| GEODE | 6.36, 3.26, 5.51 (mean 5.04) | 4.72 / 17.33, 4.39 / 10.65, 6.02 / 20.55 | 5.04 | 0.50 | 1.63 | inconclusive (spread above band); means equal |
| Cave02 | 6.23 / 10.56 | none | n/a | n/a | n/a | void: no F35 run in the results (see below) |

Rule 2, guess kinds used and A-LOAM's own scan-to-map ATE (RMSE / max, m):

| Run | LiDAR step | VINS-Mono step (VO) | Blend (INTERP) | A-LOAM own pose | Fused |
|---|---|---|---|---|---|
| MF run 1 | 67.3 % | 22.6 % | 10.0 % | 1.78 / 6.50 | 0.80 / 1.37 |
| MF run 2 | 67.2 % | 22.7 % | 10.0 % | 2.29 / 5.90 | 0.66 / 1.12 |
| LC run 1 | 18.2 % | 72.9 % | 8.8 % | 1.13 / 2.84 | 1.99 / 3.54 |
| LC run 2 | 18.2 % | 72.9 % | 8.8 % | 0.87 / 1.90 | 2.40 / 4.51 |
| C02 run 1 | 50.3 % | 42.4 % | 7.2 % | 3.17 / 5.64 | 2.82 / 5.19 |
| GEODE run 1 | 63.7 % | 22.4 % | 13.9 % | 4.30 / 15.26 | 4.72 / 17.33 |
| GEODE run 2 | 77.5 % | 13.3 % | 9.2 % | 4.22 / 10.59 | 4.39 / 10.65 |
| GEODE run 3 | 71.5 % | 18.8 % | 9.7 % | 4.83 / 13.87 | 6.02 / 20.55 |

Rule 3 outcome: no bag is better beyond its band, so "F35 is better" is not met. Corridor02 is worse than its band, so "F35 can replace F26's published thresholds without a measured loss" is not met either: not equivalent on Corridor02 (one run). The summary reading is "no change shown", with one bag worse. F26 stays the final version of the report.

What the runs show and do not show:
1. Multi Floor: both F35 runs (0.80, 0.66) are above the F26 value plus the band (0.64). F26 has one live run there, and its replay control (0.76) did not reproduce it (F26_Rotation_Weight_Replay_Test.md), so the F26 value may be a low draw. The rule calls it inconclusive; the direction is against F35.
2. Long Corridor: the mean is inside the band but the two F35 runs differ by 0.41 m, so the rule gives inconclusive. F35 puts VINS-Mono's step into the guess on 73 % of scans there (F26: 4.5 % by the published rule), and that did not lower the error.
3. Corridor02: one run, 2.82 m, against 1.93 and 2.04 for F26. The F24 runs on this bag have a large spread (earlier runs 104 m and 1.29 m), so one run is weak evidence, but the rule counts it as worse.
4. GEODE: the F35 mean equals the F26 mean (5.04 m both); the spread within each configuration (1.63 m and 3.10 m) is larger than any difference between them.
5. Guess shares differ from the prediction on Multi Floor and GEODE: our channels put VINS-Mono's step into the guess on 13 to 23 % of scans there, not close to zero. On GEODE the VINS-Mono step was used although VINS-Mono is distrusted on most scans; the run-to-run error did not change in the mean.
6. A-LOAM's own scan-to-map pose is better than the fused result on Long Corridor in both runs (1.13 and 0.87 against 1.99 and 2.40). This was already the case for F26 and is not changed by F35.

Cave02: no F35 run is in the results index and no Cave02 files are in the zip, although the batch order has it between Long Corridor and Corridor02. Corridor02 finished at 21:07, about 45 min after Long Corridor run 2 (20:17), which fits a skipped Cave02 step (the batch skips a bag when it is not found at the expected path). The cause is not confirmed; the batch log (~/f35all.log) would show it. Reported as void; Cave02 is not rerun here.
