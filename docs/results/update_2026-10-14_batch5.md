
## Update, 14 October 2026 (batch 5: F8 recordings 4-6 and LiDAR-only + loops; C_T = 0.03 fixed in advance)

Three new recordings at C_T = 0.03 (F8_kf_run4-6, live full-span ATE RMSE 0.576 / 0.587 / 0.475) and one LiDAR-only recording (F4_kf_run1).
Back end: LIO-SAM-style loop weights (iso), 1 search round (default), odometry noise calibrated on bag 0.

| Recording | front end only | + iso loops, 1 round | loops | bags 1-2 (iso) |
|---|---|---|---|---|
| F8_kf_run4 | 0.576 / 1.24 | 0.360 / 0.96 | 142 | 0.354 |
| F8_kf_run5 | 0.587 / 1.24 | 0.363 / 0.75 | 130 | 0.366 |
| F8_kf_run6 | 0.475 / 1.04 | 0.303 / 0.85 | 139 | 0.296 |

**All six C_T = 0.03 recordings (F8_kf_run1-6), full-span ATE RMSE (m):** front end 0.626 +- 0.107; with loop closure **0.347 +- 0.036** (max 0.395, min 0.303);
6 of 6 improve and 6 of 6 are below the challenge's best Multi Floor value (0.401, FAST-LIO2 + HBA; metric and alignment may differ).
Wilcoxon signed-rank, front end vs loops (n = 6): p = 0.031 (smallest possible for n = 6). Live F8 over all nine live runs (no loops): 0.617 +- 0.107.
Caveat: the one-round setting was chosen after seeing the earlier recordings (post hoc), and C_T = 0.03 came from the full-span sweep on this sequence. The three new recordings
were not used for either choice and land in the same range (0.360 / 0.363 / 0.303 vs earlier F8 0.395 / 0.306 / 0.356), so repeatability holds; Long Corridor is still the unbiased test.

**LiDAR-only (A-LOAM scan-to-map, VINS-predicted) + loop closure: does not rescue it.** F4_kf_run1 live 7.752 / 14.23; with iso loops 8.181 / 15.70
(bag 0 1.255 -> 1.255, bags 1-2 4.234 -> 4.173). Only 2845 scans (< 3000 rule, so excluded from index means). The LiDAR-centred baseline is too far off
for the loop search to find or fix anything; the VIO-primary front end is what makes loop closure work (consistent with VINS-only + loops 1.235 -> 1.382).
(The 7.75 m F4 value is our own A-LOAM, not a published baseline.)

Checks: 1-s RPE (held-out) for the F8 recordings is 0.090 / 0.092 / 0.098 vs VINS 0.066 (worse, as before).
Replay "fused C_T = 0.03" columns (0.76-0.98) are open-loop replays of the logged A-LOAM and are less accurate than the live runs (0.48-0.59), because the live run feeds the fused pose back into A-LOAM.

Next: Long Corridor (fresh sequence; needs bag + GT; see claude/Dataset_Test_Plan.md). C_T = 0.03 and 1 round fixed in advance.
