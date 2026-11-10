# F30: F26's guess with LiDAR as the primary sensor (10 Nov 2026), rules written before any run

## What it is
- Output pose: A-LOAM's scan-to-map pose (LiDAR primary). No VINS-Mono fusion, no Schur correction, no remap of the output. `FUSION_MODE=lidar` makes every step LiDAR-only.
- Initial guess for the scan-to-map matching: F26's rule (`GUESS_MODE=status`, Switch-SLAM's Algorithm 1 lines 1 to 8). Scan not degenerate: A-LOAM's own scan-to-scan increment. Degenerate: the VINS-Mono increment. Status queue (size 5) holding both: the Eq. 13 interpolation. VINS counts as absent under F24's guard (VO_FAIL, step above 1 m, rotation above 0.5 rad), then the LiDAR increment.
- Detection: Switch-SLAM's own rule on the Hessian (as F26). No R, T or additional-T channels.
- Config `F30` in `run_fusion_study.sh`. No code change: the guess module and the LiDAR-only mode already existed and were unit-tested (`test_guess_status.py` runs the status guess with the same warm-up setting).

## How it differs from the others
| | output pose | guess | remap in degenerate directions |
|---|---|---|---|
| F26 | F24 fusion (VINS-Mono base, LiDAR corrects) | status rule | F24's Schur fusion |
| **F30** | **A-LOAM scan-to-map (LiDAR)** | **status rule** | **none** |
| SW (replica) | A-LOAM + Switch-SLAM remap (Eqs. 15, 16) | status rule | VINS healthy: equal-weight fusion of the LiDAR step (degenerate directions removed) and the VINS step; VINS failed: LiDAR step along the well-conditioned directions only, the rest from the initial guess |
| F4 (old) | A-LOAM | VINS-Mono always | none |
| F5 (old) | A-LOAM | none (own) | none |

## Predictions written before the runs
- GEODE and Cave02: the VINS-Mono is dead or distrusted for most of the run, so F30 should equal F26 within its run-to-run range (F26 GEODE 3.26 to 6.36, Cave02 6.23 n=1). If F30 differs there, the cause is the fusion, not the guess.
- Multi Floor, Long Corridor, Corridor02: F30 may differ from F26, since F26 uses the VINS-Mono in the output there. Corridor02 is the bag where A-LOAM alone failed in all four F5 runs (46.5 to 93.0 m) and F24 failed once in three, so a failure there counts as a run.

## Reading rules
1. F30 against F26 on the same bag (F26: GEODE n=3, Cave02 n=1, Corridor02 n=2, Multi Floor n=1, Long Corridor n=1). "Lower" only if the F30 mean is below the F26 range; "higher" only if above it; otherwise no difference shown.
2. n=1 to 3 supports no significance claim; failed runs count as runs.
3. Cave02 and GEODE are tuned-on data. Nothing is adopted without a held-out bag and a rule written first.
4. F30 is not Switch-SLAM and not our fusion: it isolates what the VINS-Mono guess alone gives A-LOAM.

## Check against the paper (10 Nov 2026, Section III-E, Eqs. 14 to 16, read from SwitchSLAM.pdf)
The remap is not a plain "VINS fills the degenerate directions". Degenerate and VINS healthy (Eq. 15): the LiDAR step with the degenerate directions removed and the whole VINS step are fused with equal weights, so VINS contributes in all six directions and the LiDAR in the well-conditioned ones. Degenerate and VINS failed (Eq. 16 line 2): optimisation along the well-conditioned directions only; the undetermined directions come from the initial guess (the paper's IMU-propagated LiDAR odometry; in our replica A-LOAM's scan-to-scan increment, difference D1). Eq. 14 as printed says "well-conditioned or VO fails" use the full inverse, Eq. 16 uses the degenerate-removed inverse when VO fails; we follow Eq. 16. Our replica applies the remap to A-LOAM's converged displacement (D2), the paper inside its optimiser.
