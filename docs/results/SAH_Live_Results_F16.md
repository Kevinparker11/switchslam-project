# SAH live results (config F16), all three sequences (17-19 October 2026)

Follows `Structure_Heading_Development_Results.md` (replay development of SAH v7). F16 = F8 (`FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9`) + SAH, live in fusion_node_v2, with keyframe recording, then the back end (iso loop weights, 1 search round, odometry noise 1.46 deg / 0.054 m, all frozen from Multi Floor). Replay rates: Long Corridor and Multi Floor 0.5x, Corridor02 0.33x. Metric: ATE RMSE, Umeyama SE(3), no scale, full span. Full record with parameters and timing: https://claude.ai/code/artifact/3b5f9cdd-de1d-428b-a5c4-07bde3af30cc (Phases 15-18).

## Results (ATE RMSE, m, mean +- sd; F16 now 6 runs per sequence, updated 19 Oct after `run_longer_batch.sh`)
| Sequence | F8 front end | F16 front end (6 runs) | replay prediction | F16 + iso loops (6 recordings) | F8 + iso loops |
|---|---|---|---|---|---|
| Long Corridor | 4.53 +- 0.49 | 2.27 +- 0.45 (1.99, 2.16, 3.17, 2.13, 2.00, 2.19) | 1.94 | 1.538 +- 0.304 | 2.67 +- 0.73 (3) |
| Multi Floor | 0.617 +- 0.107 (9 runs, 1.0x); 0.603 +- 0.112 (runs 7-9, 0.5x, matched) | 0.640 +- 0.115 (0.56, 0.80, 0.53, 0.58, 0.77, 0.60; 0.5x) | 0.562 | 0.523 +- 0.224 | 0.347 +- 0.036 (6, 1.0x, not matched) |
| Corridor02 | 2.12 +- 0.06 | 1.708 +- 0.069 (1.69, 1.72, 1.68, 1.68, 1.64, 1.84) | 1.749 | 1.250 +- 0.435 | 2.10 +- 0.10 (3) |

Earlier three-run values (superseded): Long Corridor 2.44 +- 0.64 / 1.673 +- 0.414; Multi Floor 0.63 +- 0.15 / 0.454 +- 0.102; Corridor02 1.695 +- 0.026 / 1.161 +- 0.496.

- Long Corridor: front end level with Switch-SLAM RA-L (2.42); the three new runs (2.13, 2.00, 2.19) are all better than the old run 3 (3.17). With loops 1.54 is below Switch-SLAM but above the challenge best (1.254), LODESTAR (1.386) and SuperLoc (0.817).
- Multi Floor: matched control done. F16 0.640 vs F8 0.603 at 0.5x (Mann-Whitney p = 0.44, 6 vs 3 runs): SAH is neutral on Multi Floor. The gain with loops is a loop-closure gain. Loops were run on F16 only, so there is no matched F8 + loops at 0.5x (the 0.347 was at 1.0x); in F16 run 5 loops made it worse (0.767 to 0.955, max 2.81). SuperLoc's 0.315 (Floor01) is below our best 0.347.
- Corridor02: the SAH gain holds (1.708 vs 2.12). Loop closure gain depends on one long start-end loop: runs 1, 3, 4, 5 accepted it (loops such as 158-692 s or 0-749 s) and went from about 1.7 to 0.81, 0.95, 1.15, 1.01; runs 2 and 6 found only short-span loops (16 and 17) and stayed at 1.73 and 1.85. The revisit was not further apart in those runs (estimated minimum distance between the 155-170 s and 685-705 s parts of the path: 0.78 and 0.80 m vs 0.48-0.70 m; ground truth 0.78 m), so drift distance is not the cause. Why the back end rejected that loop is not established (keyframe files are on the laptop).

## Published numbers verified (19 Oct)
SuperLoc (arXiv 2412.02901) Table III, "ATE Performance on SubT-MRS", asterisk = loop closure; SuperLoc's row has none and the text says its 0.271 average is without loop closure. Corridor01 0.817, Floor01 0.315; its own odometry system; ATE not defined, no units or alignment stated. Earlier notes called this prior-map localisation: wrong (that is Table II, outlier percentages). It is the strongest published no-loop figure on both sequences. "Multi Floor beats every published result" is withdrawn.

## Long Corridor run 3 (3.17 m): diagnosis
- Not SAH: end correction -5.83 deg vs -5.86 deg in run 1; structure rejections 191 vs 193. Only a transient differed (+1.97 deg early, about 1.5 deg more negative near 200 s).
- Not replay stress: 0 dropped SAH keyframes, no A-LOAM per-row jump above 0.83 m (limit 1.0), clean restarts, fused path length 597-600 m in all runs. No scale bias: Sim(3) scale 1.003-1.006, same RMSE; the paths are 2.0-2.3% long at GT rate, which is jitter.
- The logged A-LOAM path drifted in run 3: distance to the fused path rose from 7.2 m (220 s) to 31.6 m (275 s) with identical step lengths (heading divergence about 8-10 deg); scored alone it is 5.16 m (max 11.0) vs 1.35 and 1.02 in runs 1-2. The fused result (3.17) was better than A-LOAM alone.
- Error against ground truth by window (RMS, m): the maximum error is at the start in every run (5.38, 5.73, 7.85 m at 8 s, 8 s, 1 s); 0-20 s fused 4.28 / 4.87 / 6.63, A-LOAM alone 1.64 / 1.11 / 10.31. Run 3 is also worse from 180 s on (fused 3.95 and 3.05 in 180-240 and 240-280 s; A-LOAM alone 3.32 and 8.44).
- In runs 1-2 the logged A-LOAM path beat the fused output (1.35 vs 1.99; 1.02 vs 2.16). A-LOAM ran in the loop on fused predictions, so this is not an independent LiDAR-only result. Lead to test, not a finding.
- The 19 Oct runs 4-6 (2.13, 2.00, 2.19) did not repeat run 3's failure, so run 3 looks like an outlier; the cause of its A-LOAM slip is still not established.
- Warm-up (first 20 s, LiDAR-only): 31-37% of the Long Corridor squared error in 7% of the time; RMSE excluding it, re-aligned, 1.56 / 1.68 / 2.52 for runs 1-3. On Corridor02 5-7% and Multi Floor 3-6%: negligible.

## Multi Floor SAH log
Final corrections differed by run: +4.81, +5.60, -0.84 deg. Run 2 (0.80 m) accepted only 175 updates (360 and 341 in runs 1 and 3) and had 307 structure rejections (121 and 115): consistent with a partly inactive correction, not tested as a cause. With six runs the spread stays (0.53-0.80) and F16 equals F8 at the same rate.

## Near-range filter study (19 Oct, replay of SAH v7 on F8 keyframes, GT-scored)
Real data, mean ATE by minimum range r_min (live default 1 m): Long Corridor 1.940 (1 m), 1.929 (2), 1.918 (3), 2.012 (4), 2.091 (5), 2.209 (6), 2.236 (8); Corridor02 1.749, 1.783, 1.771, 1.805, 1.800, 1.802, 1.775; Multi Floor 0.552, 0.615, 0.513, 0.503, 0.485, 0.497, 0.486. Up to 5 m the changes are within run-to-run spread; not claimed.
Synthetic carried plane (body-fixed, 8 m wide, about 25% of points, angle 10-30 deg) at distance d: the filter helps only when r_min removes the whole object (Corridor02, d = 1.5: 2.73 / 3.82 / 3.15 at r_min 1 / 2 / 3, 1.81 at 4; d = 3.0: 3.2-3.3 up to r_min 4, 1.76 at 5). Partial removal gives no protection.
Conclusion: r_min is a platform setting (the farthest extent of anything fixed to the robot), not a general fix; the live default stays at 1.0 m. A motion-based test (points fixed in the body frame across keyframes) was not built: validating it needs real data containing a carried object. Script: `/home/claude/sah/rmin_sweep.py`.

## Batch of 19 Oct (`run_longer_batch.sh`, 01:54-07:13, results in `for_claude11.zip`)
12 live runs: F8 runs 7-9 on Multi Floor (0.5x); F16 runs 4-6 on Long Corridor, Multi Floor and Corridor02. Back end then on all six F16 recordings per sequence with full loop lists (run_backend.py edited in place to print up to 400 loops; original kept as run_backend.py.orig). The first start used an old backup folder (`fusion_v3_backup_1017_1609`) and found no bags; the working folder is `~/switchslam_channelT/fusion_v3`.

## Next
1. Back end on the recorded F8 runs 7-9 (Multi Floor, 0.5x) for a matched F8 + loops figure.
2. Inspect why the long start-end loop (about 158-693 s) is rejected in Corridor02 runs 2 and 6 (matching score for that keyframe pair, keyframes on the laptop).
3. Why A-LOAM is poor in the first 20 s of Long Corridor (warm-up is LiDAR-only).
4. Test leaning more on the LiDAR path in Long Corridor, checked on a sequence not used to choose the setting.
5. Untouched test sequence and a cave control (SAH must switch off).
6. Ground-truth cross-check Floor01 vs Multi Floor (`compare_gt.py`).
