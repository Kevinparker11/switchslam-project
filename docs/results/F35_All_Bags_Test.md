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
