# Cave02 and GEODE: where the F24 error comes from (9 Nov 2026, read from the saved switching logs)

Method: the fused, A-LOAM-only and VINS-only trajectories in each run's switching log were aligned to the ground truth (Umeyama SE(3), no scale) over the full span, then split into segments, each aligned on its own. Runs: Cave02 F24 runs 1 to 3 (plus F26 and F27 run 1), GEODE stairs alpha F24 runs 1 to 4 (plus F26). No new run. Ground truth: cave02_gt.txt, gt_stairs_alpha.txt.

## Full-span RMSE by source (m)
| Run set | Fused (F24) | A-LOAM alone | VINS alone |
|---|---|---|---|
| Cave02 F24 (3 runs) | 7.55, 7.08, 7.11 | 11.09, 9.63, 10.45 | 10.80, 13.18, 10.87 |
| GEODE F24 (4 runs, 0.5x) | 6.15, 9.15, 7.05, 6.56 | 6.07, 9.11, 7.01, 6.35 | 186.6, 153.1, 270.8, 163.7 |

## Cave02
- Local accuracy is good: with each segment aligned on its own, fused is 0.67 to 0.70 m on t >= 300 s and 2.2 to 2.4 m on t < 300 s (three runs, same pattern; A-LOAM alone 0.65 to 0.76 and 1.96 to 2.18). The 7 m full-span error comes from the offset between segments, not from steady drift.
- Aligned on t > 300 s, the first 210 s sit about 17 m off (A-LOAM about 25 to 28 m), and the offset closes between 210 and 300 s.
- Worst 10 s windows in all three runs: 285 to 305 s, where the ground truth moves 6.0 to 6.1 m and the estimate moves 1.5 to 1.6 m (a stall).
- In 250 to 310 s the translation-block ratio lambda_min / trace(H_tt) falls to 0.11 to 0.12 (about 0.20 elsewhere), and the VIO consistency value (vio_gamma) is 0 from about 250 s to the end. So the weakest LiDAR stretch coincides with VINS being unusable.
- VINS alone is 8 to 11 m in every segment (scale about 0.78 against the ground truth). With a scale fit to the ground truth it would be 2.7 m (runs 1 and 3), which is an oracle, not a usable number.
- Start: VINS lost at 84 to 108 s (VO_FAIL flickers), WARMUP until about 120 s.
- Ground-truth z falls from 0 to about -24 m between 120 and 360 s (descent).

## GEODE stairs alpha
- Fused equals A-LOAM in every run (6.15 against 6.07, 9.15 against 9.11, 7.05 against 7.01, 6.56 against 6.35). VINS has failed completely (scale 0.02 to 0.07, 150 to 270 m RMSE), so the fusion adds nothing here.
- The error is mostly vertical: z RMSE 5.4 to 7.3 m against xy 2.8 to 5.5 m.
- Per 30 to 60 s segment the error is only 0.2 to 3.7 m; the full-span 6 to 9 m comes from offsets between segments (stairs descent z -23 m, and the return).

## What this does and does not show
- Both bags are development data. A change made to improve them counts as evidence only if it is tested on bags it was not tuned on, with the reading rule written first.
- Published context (different metrics and sensors, not comparable): Cave02 iG-LIO 0.43, GenZ-LIO 0.44, DLIO 0.57, Faster-LIO 0.81, FAST-LIO2 4.49, Point-LIO 6.57; GEODE alpha RELEAD 0.57, FAST-LIO2 4.69, DLIO 4.89, R3LIVE 4.54, LIO-SAM 6.30.
- Not found: the cause of the Cave02 stall (A-LOAM or its map) and why VINS fails on both bags (configuration, darkness, scale initialisation). Neither was tested.
