# F30: Switch-SLAM's structure and output, our detection only (10 Nov 2026), rules written before any run

## What it is
- **Output and structure: Switch-SLAM's, as in the paper (Section III-E, Algorithm 1).** A-LOAM's scan-to-map pose is the pose. Scan not degenerate: A-LOAM's own motion is the starting guess and the full LiDAR step is the output (Eq. 16, line 1). Degenerate: the VINS-Mono motion is the guess (status buffer of 5, Eq. 13 blend at the start or end of a degenerate stretch). Degenerate and VINS healthy: the output is the equal-weight fusion of the LiDAR step with the degenerate directions removed and the VINS step (Eq. 15). Degenerate and VINS failed: LiDAR along the well-conditioned directions only (Eq. 16, line 2).
- **Detection: ours only, none of the paper's thresholds** ([0.12, 0.27, 0.48] and the 6x6 eigenvalue rule are not used). R and T are judged separately.
  - **R**: rotation Schur block S_RR. Degenerate where lambda_max / lambda_i > 15.7 (the kappa gate of the fusion, `KAPPA_TH`, frozen since F1). The flagged directions are the weak eigen-directions.
  - **T**: translation Schur block S_tt. Per-direction information weight w_i = c lambda_i / (c lambda_i + 1) with c_T = 0.03 (frozen, F8 to F29) against a unit VINS-Mono information, the same `info_weight` as the fusion. Degenerate where w_i < 0.5, that is where the LiDAR carries less information than the VINS-Mono step.
  - **additional T**: S_tt combined with the orientation tensor of the raw scan normals (`/laser_cloud_surf_last`, k=12, 400 points), rule `min` (information per direction = min of solver and raw-scan support), then the same test. It replaces plain T. If no tensor exists for a scan, plain T is used and the scan is counted as missing.
  - Degenerate = any channel fires. Removed in the remap: the flagged directions of the channels that fired (rotation directions from R, translation directions from T), orthonormalised as a set.
  - Eq. 13 blend weight (ours, since the paper's sqrt(3) lambda_bar_1 belongs to its rule): w = min(1, 2 min_i w_i, 15.7 / kappa_R). It is 1 at either threshold and falls to 0 as the information vanishes.
- Config `F30` (switch_slam_node, `DETECT=ours_only`), code `switch_slam_detect.OwnDetector`, 18 detector tests pass. Same Hessian topic (`/laser_hessian`), same Eq. 15 weighting (0.5), same status buffer (5) as `SW`.

## Choices that are ours
- D1 The R threshold 15.7 and c_T 0.03 are the thesis's frozen constants, not tuned for this test. The binarisation of the T weight at 0.5 is ours (equal information with VINS-Mono).
- D2 Rule `min` for the tensor (the fail-safe), per-scan tensor from `/laser_cloud_surf_last`, not F24's keyframe `gmax`.
- D3 The blend weight above.
- D4 No SAH, no VIO or rotation consistency checks, no guards, no warm-up.

## What the logs say before any run (read-only, no score used)
Share of scans on which R or T would fire, computed from the Hessians logged in the first F24 run of each bag (R and T only; the tensor needs the cloud and is not in the logs). The paper's rule on the same scans, for context.

| Bag | scans | R | T | R or T | paper rule |
|---|---|---|---|---|---|
| Multi Floor | 4070 | 37.1 % | 0.5 % | 37.5 % | 1.5 % |
| Long Corridor | 2774 | 81.8 % | 7.3 % | 81.8 % | 4.5 % |
| Corridor02 | 8296 | 58.0 % | 0.7 % | 58.7 % | 2.3 % |
| Cave02 | 9469 | 4.4 % | 0.0 % | 4.4 % | 0.0 % |
| GEODE | 3225 | 53.7 % | 0.9 % | 54.0 % | 10.3 % |

So with R at 15.7 the scans are called degenerate on a large share of every bag except Cave02, and almost all of it comes from R (T fires on under 8 %). This is consistent with the 13 Oct threshold study (kappa(S_RR) > 15.7 flagged 33 % of Multi Floor frames; the rotation block carried the usable signal and the translation block fired on about 0.2 %). The consequence for F30: on those bags it spends much of the run in the degenerate branch, where the output is the 50/50 fusion with VINS-Mono and the guess is the VINS-Mono motion. It is Switch-SLAM's structure, but it will not behave like a LiDAR-only system there. Not adjusted.

## Reading rules (fixed before the runs)
1. **Precondition.** The additional-T tensor must be found on at least 90 % of scans ("additional T: tensor found for X, missing for Y" in the log), else that run's additional-T result is void.
2. **Fire rates** (det_R, det_T, det_TT per scan in the log) are reported per bag. The share of scans in the degenerate branch is what says how LiDAR-primary the run was. Above 50 % it is reported as "mostly the fusion branch".
3. **Comparison.** F30 against F26 (same guess family, VINS-based output) and against `SW` and `SWD` where they exist (SW has Multi Floor and Long Corridor runs; SW and SWD on GEODE and Cave02 come from the SWD queue). On GEODE and Cave02, F30 is "lower" only if its mean RMSE is below the comparison arm's range and by at least 1.0 m. Otherwise no difference shown. A failed run counts as a run.
4. **Counts.** n = 1 to 3 supports no significance claim.
5. **Development data.** Cave02 and GEODE are tuned-on data. No threshold is changed after seeing these runs and then reported on the same bags. Adoption needs a held-out bag and a rule written first.
6. **Target.** 1 to 2 m on Cave02 and GEODE is the goal, not a pass rule.

## Related configs
`SW` replica of the paper; `SWD` = paper's rule OR our channels with the paper's thresholds (pre-registered, queued); `F31` = F26's guess with A-LOAM as the output and no remap (never run).

## First run (10 Nov 2026, GEODE, run 1): additional T void, fixed afterwards
The log line read "additional T: tensor found for 0 scans, missing for 3455 (plain Schur T used there)". Reading rule 1 applies: run 1 is a run of R and plain T only, void as a test of the additional T, and stays in the record as such (tag `F30_kf_run1`). The run wrote 3104 rows; 1561 of them were scans where an earlier scan was still being mapped when the guess was published (`sw_race`).

Cause (a plumbing error, not a threshold): A-LOAM publishes `/laser_cloud_surf_last` just after the odometry message of the same scan. The switch node looks the tensor up in the odometry callback, where the exact one is never there yet. The fusion node never had this problem because it looks the tensor up in the mapping callback.

Fix (commit after 30fd81d): the lookup takes the exact tensor if present, else the tensor of the newest earlier scan within 0.25 s (`T_LAG_MAX`), and the log line now says how many were the previous scan's. D5: the previous scan's tensor is treated as being in the current frame; the error is the rotation between two scans. Unit test added. The same fix applies to `SWD` (it uses the same node). The fixed run is `F30_kf_run2`; run 1 is not deleted and not replaced.

### Run 1 result (GEODE 0.5x, R and plain T only, additional T void)
ATE RMSE / max = **13.04 / 62.88 m** (3095 of 3104 poses in the GT span). Fire rates from the log: R 54.0 %, T 0.9 %, degenerate branch 54.3 % of scans; the pre-run prediction from the F24 Hessians was R 53.7 %, T 0.9 %, so the detector behaves as predicted. For comparison (same bag, same rate): F24 6.15 to 9.15 (n=4), F26 3.26 to 6.36 (n=3), F27 6.41 to 8.82 (n=3). Reading rule 3: higher than F26's range. n=1, additional T void; no claim beyond that this run is the worst GEODE value in the table.

### Run 1 diagnostics (read from the run's own log)
- Guess kinds: LiDAR 1680 (54 %), VINS-Mono 794 (26 %), interpolation 629 (20 %).
- Output branch (Eq. 16 cases): full LiDAR step 1417 (46 %); degenerate and VINS failed, well-conditioned directions only 263 (8.5 %); degenerate and VINS healthy, Eq. 15 equal-weight fusion with the VINS-Mono step 1423 (46 %).
- VINS-Mono flagged failed (paper-style test: gap above 1 s, step above 5 m or 50 degrees) on 13.0 % of scans.
- Median step per scan: LiDAR 0.110 m, VINS-Mono 0.219 m (about twice). VINS-Mono steps above 1 m: 527 of 2885 (18 %), more than the 13 % flagged failed, so a part of the large steps passes the paper-style test and enters the Eq. 15 fusion.
- Reading (not tested by a further run): with R firing on 54 % of GEODE scans, 46 % of the output is half VINS-Mono, and on this bag the VINS-Mono step is about twice the LiDAR step and often large. That fits the 13.04 m. F24 and F26 reject such steps with a 1 m and 0.5 rad guard and a scale consistency check; the paper-style test has neither. The paper's own rule fires on 10 % of GEODE scans, so the same weakness would be much less exposed under `SW`. The matched `SW` run on GEODE does not exist yet.
