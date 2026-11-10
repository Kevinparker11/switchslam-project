# Switch-SLAM structure with our detection (R, T, additional T): design and test rules, written before any run (10 Nov 2026)

## What this is
The Switch-SLAM structure is not changed: LiDAR (A-LOAM scan-to-map) is the primary pose; when the scan is degenerate, VINS-Mono gives the initial guess for the scan-to-map matching (status queue, Eq. 13 interpolation) and the remap (Eqs. 14 to 16) removes the degenerate directions from the LiDAR step and takes them from VINS-Mono. The only thing changed is how degeneracy is detected. Config `SWD`, code `switch_slam_detect.py`, node switch `DETECT=ours`. Everything else equals config `SW` (same Hessian topic `/laser_hessian`, N_BUF 5, thresholds [0.12, 0.27, 0.48], literal Eq. 15).

This is not F24 to F27. Those use VINS-Mono as the base and LiDAR as a correction.

## Detection
Degenerate = Switch-SLAM's rule (coupled 6x6 Hessian, always on) OR any of:
- **R**: the three eigenvalues of S_RR (rotation Schur complement), normalised to unit norm, any below its threshold.
- **T**: the same on S_tt (translation Schur complement).
- **additional T (TT)**: S_tt first combined with the orientation tensor of the raw scan normals (`/laser_cloud_surf_last`, k=12 PCA, 400-point subsample), rule `min` (information along each direction = min of solver and raw-scan support; the fail-safe of ChannelT_Mini_Test_Protocol.md), then the same test. TT replaces T when both are named; if no tensor is available for a scan, plain T is used for that scan and the scan is counted as missing.
The removed directions in the remap are the flagged eigenvectors of every channel that fired (orthonormalised as a set); the Eq. 13 weight uses the smallest normalised eigenvalue over the channels that are on.

## Choices that are ours (not the paper's), fixed now
- D1 The paper's thresholds are applied to 3x3 blocks. The paper's expectations are for a unit-norm three-vector, which a 3x3 block gives, but the thresholds were not derived for blocks. They are not tuned.
- D2 Rule `min` for the tensor, not `gmax` (F24's rule): `min` is the fail-safe designed for a detector; `gmax` can only raise information. Per-scan tensor from `/laser_cloud_surf_last` (the F18 route), not the F20+ keyframe tensor.
- D3 No SAH, no VIO or rotation consistency checks, no guards, no warm-up: none is part of this test.

## Runs (batches/swd_4h.sh, about 3.6 h)
Interleaved so drift in the machine does not favour one arm: GEODE (0.5x) SW and SWD runs 1 and 2, SWD run 3; Multi Floor SWD run 1; Cave02 SW run 1, SWD runs 1 and 2; Long Corridor SWD run 1. SW references on Multi Floor and Long Corridor already exist (live, same machine, earlier batches). ATE as in all earlier tables (Umeyama SE(3), no scale, full span, front end only, no loop closure).

## Reading rules (fixed before the runs)
1. **Preconditions.** For every SWD run the log line "additional T: tensor found for X scans, missing for Y" must show at least 90 % found. If not, that run's TT result is void as a test of TT and is reported as such, not adjusted.
2. **Comparison.** SWD against SW of the same bag. On GEODE and Cave02 SWD is "lower" only if its mean RMSE is below the SW mean by more than the SW run-to-run range, and by at least 1.0 m. On Multi Floor and Long Corridor SWD must not be above the SW range (not worse). Anything else is "no difference shown".
3. **Counts.** n=2 or 3 per arm supports no significance claim; the table is descriptive. A failed run counts as a run.
4. **Firing.** The share of scans on which each channel fires (det_sw, det_R, det_T, det_TT) is reported per bag. If SWD fires on more than 50 % of the scans of Multi Floor, it is reported as over-detection, not as a gain.
5. **Target.** Reaching 1 to 2 m on Cave02 and GEODE is the goal, not a pass rule. Nothing is declared reached from a single run.
6. **Development data.** Cave02 and GEODE are tuned-on data for F25 to F27 and are not held out. Any adoption needs a held-out bag (Cave01, 03, 04, other GEODE sequences) and a rule written first. No thresholds are changed after seeing these runs and then reported on the same bags as a result.
7. If SWD is worse than SW, that is reported. The ablation `SWDRT` (R and T only) is the next step only if TT fails rule 1.
