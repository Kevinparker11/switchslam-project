# F26: does a LiDAR rotation weight (the R channel) change the output? Open-loop replay, rules written before any run (10 Nov 2026)

## Question
In F26 the LiDAR rotation weight constant c_R is 0, so the output rotation is VINS-Mono's and the R Schur channel acts only through the rotation check, which closed on 0.0 % of fused scans on four bags and 3.6 % on GEODE. Would raising c_R, so that the LiDAR contributes rotation in the directions where its Schur information is high, help?
Earlier evidence (Configurations_Explained_and_Results_To_Date.md, 6.3, an older design with the same weight form): an active rotation weight from c_R = 0.003 made Multi Floor (0.62 to 1.3 to 2.0 m), Corridor02 (2.2 to 3.4 to 4.1) and Cave02 (4.5 to 5.7 to 8.8) worse and Long Corridor better (4.5 to 1.9). This test repeats the question on the F26 logs.

## Method
The real `fusion_node_v2` callbacks are driven offline (`ot_study/round3/node_harness.py`, `SAH_SYNC=1`) by the logged F26 runs and their keyframe scans, with F26's settings and one change, `C_R`:
- logs: Multi Floor run 1, Long Corridor run 1, Corridor02 runs 1 and 2, Cave02 run 1, GEODE runs 1 to 3 (all F26, live, 0.5x or 0.33x as recorded);
- grid: C_R in {0 (control), 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3} (the earlier protocol's grid plus 3e-3);
- score: ATE RMSE / max of the fused output against ground truth, Umeyama SE(3), no scale, full span, the same scorer as the live runs.
Limits, stated now: it is open loop. A-LOAM's poses and Hessians are the logged ones, so a changed output cannot change A-LOAM's matching (in the live loop the output seeds the guess). Each log is one trajectory, so a replay difference is one trajectory's difference, not a spread. The keyframe scans in the logs are the ones of the live run.

## Rules
1. Control (C_R = 0) must reproduce the live F26 score of the same log within max(0.05 m, 5 %). If it does not, the replay is not valid for that log and is reported, not adjusted.
2. A difference counts only if it exceeds the project's tie band, max(0.1 m, 10 %) of the control score, on that log.
3. "The R channel adds value" requires one C_R > 0 that improves at least two bags by more than the tie band and worsens none by more than the tie band, on bags that are not the calibration bag. Anything else is reported as "no gain shown" (or "harmful" where a bag worsens beyond the band).
4. A value chosen from this grid is not frozen and not claimed: all bags here are development data for F26 and the live feedback is not captured. Any adoption needs a live test on held-out bags with rules written first.

## Predictions written before the run
- C_R = 0 reproduces the live scores.
- Multi Floor, Corridor02 and Cave02 get worse with larger C_R (A-LOAM's rotation is the weaker one there, as the older replay found); Long Corridor may improve; GEODE unclear.
- No C_R satisfies rule 3.
