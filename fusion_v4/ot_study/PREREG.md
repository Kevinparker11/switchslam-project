# OT-channel replay study: selection rule fixed before the OT batch is run (written after only F8-own and F16 were replayed on MF run 1)
Data: open-loop node-harness replays (the real fusion_node_v2 callbacks, SAH_SYNC=1) of logged F8 runs with their keyframe scans:
MF F8 kf runs 1-6, LC F8 kf runs 1-3, C02 F8 kf runs 1-3. All three sequences are development data (MF: C_T calibration; LC, C02: SAH development).
Configs: F8, F16 (SAH), F17 (SAH + ROT_CHECK), and F16 + OT_MODE in {min, gmean, harm, tonly, agree2, hybrid, max}.
Selection of the OT rule:
1. Rank OT modes by mean MF front-end ATE (6 logs), paired against F16 on the same logs.
2. Admissible only if the mean ATE on LC and on C02 is not worse than F16 by more than 0.05 m (corridors used as a no-harm check only).
3. Pick the best admissible MF mean; if two are within 0.01 m, take the more conservative (min, harm, gmean, agree2, hybrid, tonly, max, in that order).
4. If no mode is admissible, the OT channel is kept in its fail-safe form "min" only if it is within 0.05 m of F16 everywhere; otherwise the report says the OT channel costs accuracy on these data.
Then: the chosen structure = F17 + OT(chosen) is replayed, and the loop back end (run_backend.py, iso, 1 round, odom sigma 1.46 deg / 0.054 m as in the recorded back-end runs) is run on it and on F16 for all 12 logs.
Targets reported, not tuned for: replay front end and with loops vs F16 on the same logs (equal within 0.05 m = "same results"); and against Switch-SLAM (MF 1.61, LC 2.42).
Replay numbers are not live results; the chosen structure must be confirmed live.

## Stage 1 outcome (recorded before stage 2 was designed)
Admissible (LC and C02 within +0.05 m of F16): only `max` (MF 0.580 vs 0.560, LC 1.947 vs 1.946, C02 1.795 vs 1.782). By rule 3 the stage-1 choice is `max`.
All rules that lower the LiDAR translation information (min, gmean, harm, tonly, agree2, hybrid) are worse on LC (+0.27 to +0.60 m) and C02 (+0.32 to +0.75 m).
Reading: the planar-normal tensor UNDER-states the translational support that A-LOAM really has (its Hessian also uses edge features), so any cap removes valid LiDAR information in corridors.

## Stage 2 (written before it is run, 28 Oct 2026): a geometric tensor that also counts linear features
Hypothesis: the stage-1 loss comes from leaving out edges. An edge (line) with direction d constrains translation in the plane normal to d; its contribution to the tensor is (I - d d^T)/2 (trace 1, like a plane's n n^T).
G = (sum over planar points of n n^T + sum over linear points of (I - d d^T)/2) / (number of planar + linear points), from the same k = 12 PCA as the planar normals (planar: (l2 - l1)/l3 > 0.5; linear: (l3 - l2)/l3 > 0.5, eigenvalues ascending l1 <= l2 <= l3).
Only the rules `min` (fail-safe) and `max` are run with G. Selection: if `min` with G is admissible (LC and C02 within +0.05 m of F16) and MF within +0.05 m, it is chosen, because it is the only rule that is a fail-safe; otherwise the stage-1 choice `max` (planar tensor) stands. This is a second look at development data and is reported as such.

## Stage 2 outcome
OTG_min (geometric tensor, fail-safe): MF 0.558 (F16 0.560), LC 1.974 (1.946), C02 1.776 (1.782): admissible, so by the stage-2 rule it is chosen.
OTG_max: MF 0.584, LC 1.914, C02 1.784.
Final structure F20 = SAH + ROT_CHECK + OT_SRC=geom OT_MODE=min (F17 + the OT fail-safe). Next: replay F20, then the loop back end (none / iso / ot) on F16 and F20, all 12 logs.

## Stage 3 (written before it is run): when does the OT channel add value? Injected solver fault on the real logs
The OT channel is a fail-safe for the case "the solver is confident but wrong". Healthy logs cannot show its value (stage 2: neutral). Fault model (the "solver unreliable" case of the thesis, the same model as the synthetic test ChannelT_Mini_Test_Protocol.md, now on real logs with real VIO and real keyframe scans):
- three windows per log, starting at 25 %, 50 % and 75 % of the log duration, 20 s each;
- inside a window the LiDAR scan-to-map position slides along the weakest Schur translation direction (taken at the window start, fixed in the world) at 0.2 m/s (4 m per window; the slide stays in the pose afterwards, as a corrupted map would), and the solver claims confidence: H_tt is replaced by tr(H_tt)/3 * I (wrong correspondences that look like constraint);
- the keyframe scans (and so the OT channel) and the VIO are untouched.
Runs: F16 and F20 on all 12 logs with the same faults. Prediction: F20 has lower full-span ATE than F16 on most logs; the difference is the value of the OT channel under this fault model. Reported as a mechanism demonstration under a stated fault model, not as a frequency of such faults in real data.
