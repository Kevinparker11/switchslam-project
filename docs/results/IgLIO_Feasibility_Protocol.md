# iG-LIO as a third LiDAR front end: desk check, staged feasibility test and the full test (27 Oct 2026)

## Why
The structure (Channels R, T, T+; consistency gate, scale correction, guard) is claimed to work with any LiDAR front end that
gives a pose per scan and the registration information. It has run on two: A-LOAM and GenZ-LIO. iG-LIO (Chen et al., RA-L 2024,
GICP-based iterated error-state Kalman filter) was the runner-up when GenZ-LIO was chosen (`Front_End_Upgrade_GenZ_fusion_v4.md`);
that choice rested on the GenZ-LIO paper's own benchmark (iG-LIO diverged on 30.8 % / 40.0 % of sequences there), and iG-LIO was never run by us.
A third front end of a different design strengthens the generality claim and gives iG-LIO-alone numbers on our recordings
(today the iG-LIO row of Table 7 is "from [5]", the GenZ-LIO authors' re-run; LODESTAR's Table V gives 3.136 m on Long Corridor against 1.55 m there).
Only the LiDAR odometry changes. The fusion core, VINS-Mono, ground truth and metric are untouched; one constant (the information scale) is new.

## Stage 0: desk check of the source (done, 27 Oct, commit 2d79259 of zijiechenrobotics/ig_lio)
| Need | Finding | Verdict |
|---|---|---|
| ROS 1 Noetic, VLP-16 PointCloud2 + IMU | catkin package, Ubuntu 20.04 recommended; `lidar_type: velodyne`; the authors' own `config/bg_velodyne.yaml` is a VLP-16 file (Botanic Garden). Per-point time read from the `time` field (`time_scale` 1000 -> ms); a fallback exists when it is missing. | ok |
| Pose per scan | `/lio_odom` (nav_msgs/Odometry, frame `world`, IMU pose, one message per scan); `current_scan` = the scan in the world frame. | ok |
| Registration information | `LIO::StepOptimize` fills the 15x15 `H` (state [orientation, position, velocity, ba, bg]) first with the LiDAR terms (GICP, or point-to-plane for the first 20 keyframes) and only afterwards with the IMU prior. The LiDAR-only information is `H[0:6,0:6]` right after `ConstructGICPConstraints`, including the Cauchy robust weights and `gicp_constraint_gain`. | ok, 15-line patch |
| Perturbation convention | `dres/dx = [R*hat(mean_A) \| -I]`: right perturbation of rotation in the IMU body frame (cloud is in the IMU frame), position in the world frame. After reordering to [dp_W, dtheta_I] it is exactly the GenZ-LIO convention, so `lio_bridge.py` is reused unchanged apart from two topic names. Verified by numerical differentiation (`tests_v4/test_iglio_convention.py`, max diff 5e-9). | ok |
| Build dependency | CMake and package.xml require `livox_ros_driver` although a Velodyne run never uses it. A message-only stand-in (CustomMsg, CustomPoint) is built in the same workspace (`ig_lio/livox_stub`), no Livox SDK. | workaround, untested until Stage 1 |
| Information scale | gains 100 (GICP) and 1000 (point-to-plane) and robust weights make it differ from GenZ-LIO and A-LOAM: a new c_T, c_R is needed (calibrated on Multi Floor only, as before). | known |
| Frozen configuration | The authors' `bg_velodyne.yaml` unchanged except extrinsic and topics (`ig_lio/make_iglio_config.py`). Their paper states identical parameters across all datasets, so this is their protocol and adds no tuning on our sequences. | ok |

Unknowns that only the laptop can settle: the build (PCL, glog, TBB versions in the container), whether the `time` field is
filled by the converter (same converter as the GenZ runs, model VLP16), the IMU unit (m/s^2 assumed, `enable_acc_correct: false`),
start-up on a bag that begins moving.

## Staged feasibility test (about 1.5-2 h, laptop; each stage has a stop condition)
Nothing here is a result for the thesis. No tuning on test sequences. A failure at any stage is reported as a limit of the approach.

| Stage | What | Gate (go if) |
|---|---|---|
| 0 | desk check (above) | done |
| 1 | `ig_lio/install_iglio.sh`: separate workspace `/root/iglio_ws`, A-LOAM and GenZ-LIO untouched | clean compile, `IGLIO_INSTALL_DONE` |
| 2 | `SMOKE=1 SMOKE_SECS=120 FRONT=iglio ./run_fusion_study.sh I0` (Multi Floor, iG-LIO alone, 120 s) | rows in the log (several hundred), pose moves, no NaN, VINS-Mono present, Hessian present in the rows after the map is built, first-120 s error of the same order as GenZ-LIO on the same stretch |
| 3 | information check from the smoke log, in the cloud (no new run): eigenvalue spectra of S_tt and S_RR, direction of the weak axes, against the GenZ-LIO logs of the same stretch | same qualitative pattern (floor-normal direction strong, weak axes consistent), scales differing by a constant factor |
| 4 | one fused smoke run, 5 min of Multi Floor, `I20` with provisional constants from Stage 3 (scale matching, smoke only) | runs end to end, fused trajectory close to iG-LIO alone, mode counts plausible |

Commands (laptop; repository folder `~/switchslam-project`, branch `fusion-v4-final`):
```
cd ~/switchslam-project && git pull && cd fusion_v4
bash ig_lio/install_iglio.sh 2>&1 | tee ~/install_iglio.log                       # Stage 1
SMOKE=1 SMOKE_SECS=120 FRONT=iglio ./run_fusion_study.sh I0                       # Stage 2 (output: ~/runs_v2_iglio)
```
Stage 4 (after Stage 3): `SMOKE=1 SMOKE_SECS=300 FRONT=iglio IGLIO_C_T=<x> IGLIO_C_R=<y> ./run_fusion_study.sh I20` with the provisional values I send.

## The full test (specified now in outline; the predictions are fixed after Stage 3 and before any other sequence is run)
- Configurations: I0 = iG-LIO alone; I20 = the G20 settings (consistency gate, scale correction, fast check, guard, Channel T+) with the new c_T, c_R. Nothing else differs from G20.
- Calibration of c_T, c_R: Multi Floor only, 3 I0 recordings, offline replay (exact, iG-LIO takes no fusion feedback), same rule as for GenZ-LIO (smallest mean ATE, plateau middle), then frozen. The consistency thresholds (0.156, 0.278) and the guard margin (2.16 m) stay at their G20 values.
- Sequences: Multi Floor (calibration), Long Corridor (0.5x), Cave02 (0.5x); GEODE needs the PC and is not part of this run. I0 x3 on Multi Floor, x2 on Long Corridor and Cave02; I20 live once per sequence to confirm that live equals replay.
- Draft predictions (to be confirmed or changed before the first non-smoke sequence): (I1) I20 is lower than I0 on Multi Floor and Long Corridor by more than 0.05 m and 10 %, and within 0.1 m on Cave02; (I2) I20 is never worse than VINS-Mono alone on any recording; (I3) our I0 numbers are within a factor 2 of the values quoted from the GenZ-LIO paper (0.25 / 1.55 / 0.43), a check of our setup and not of the method. Ties below 0.1 m. All results are reported, including failures.
- If the structure helps less on iG-LIO than on GenZ-LIO, that is reported as a limit of generality.

## Limits stated in advance
One frozen configuration per front end (the papers used per-sequence tuning, so our iG-LIO-alone numbers may be worse than theirs); one LiDAR model; same bags as the rest of the study; the information scale is calibrated on the same sequence as for the other front ends, so Multi Floor is development data for iG-LIO as well.

## Outcome of Stages 1-3 (27 Oct 2026, laptop; smoke data, not thesis results)
- **Stage 1 passed.** Clean build of pinned commit 2d79259 with the Livox message stand-in; the information patch applied (`IGLIO_INSTALL_DONE`).
- **Stage 2 passed.** Multi Floor, first 120 s at 1.0x, `FRONT=iglio`, I0: 1186 rows, no NaN, path 97.9 m against 95.0 m of ground truth, largest step 0.20 m, VINS-Mono in 983 rows (first pose at 20.5 s), Hessian in 1185 of 1186 rows (the first 11 poses carry none, by design). Error over the window (re-aligned on each window, one run, one sequence): iG-LIO 0.037 / 0.189 / 0.735 m at 30 / 70 / 120 s against GenZ-LIO (G0 run 1) 0.025 / 0.131 / 0.286 m; the two agree to 0.03 m up to 50 s, and iG-LIO's error grows faster between 70 and 120 s (about 2.6x GenZ-LIO at 120 s). Same order of magnitude, so the gate is met, but the 120 s gap is a warning that iG-LIO alone may be worse than GenZ-LIO on our recording with the authors' frozen configuration (the GenZ-LIO paper quotes 0.25 / 0.26 for the two on the full sequence, with per-sequence tuning).
- **Stage 3 passed.** Information (first 120 s, median over scans; iG-LIO / GenZ-LIO): trace S_tt 6.6e8 / 8.3e8, trace S_RR 3.8e6 / 3.65e6, eigenvalues of S_tt (min, mid, max) 1.7e7, 2.2e8, 4.5e8 / 3.4e7, 1.9e8, 5.8e8, S_RR 6.6e5, 1.2e6, 1.8e6 / 4.5e5, 1.1e6, 2.0e6; condition number of S_tt 24 / 13.5 (iG-LIO weaker on its weakest axis, and 10x lower in the 10th percentile of the minimum eigenvalue), of S_RR 4.2 / 4.2. Same qualitative pattern and the scales agree within 1.3x, so the GenZ-LIO constants are the right order. Provisional constants for the Stage 4 smoke run only: c_T = 4e-6, c_R = 5e-6 (G20 values 3e-6 / 5e-6 scaled by the ratio of the median traces). The real constants are calibrated on Multi Floor I0 recordings as specified above.
- Script: `fusion_v4/ig_lio/score_iglio_smoke.py`. Stage 4 (fused smoke, 300 s) is next.

## Outcome of Stage 4 (27 Oct 2026, fused smoke, 300 s, c_T = 4e-6, c_R = 5e-6; smoke data, not thesis results)
- **The pipeline works end to end:** 2970 rows (no NaN), VINS-Mono from 20.4 s, first fused row at 40.4 s, 2569 fused rows, Hessian in every row, scale and gate columns filled.
- **iG-LIO alone diverged in this run and not in the I0 run.** Same bag, same frozen configuration, same extrinsics, iG-LIO takes no feedback from the fusion. The two logs agree to about 0.1 m up to 50 s (position at 50 s (9.32, 6.09, 0.86) in the I0 run and (9.22, 6.06, 1.02) here); at 70 s the I0 run is at (7.7, 5.8, 3.6), as are GenZ-LIO and VINS-Mono, and this run at (-3.0, 1.1, 5.2), about 10 m away (largest single step only 0.34 m: a wrong motion estimate while the carrier changes floor, not a jump). iG-LIO's own error over 0-120 s is 5.3 m in this run against 0.74 m in the I0 run; over 0-300 s 8.2 m (GenZ-LIO 0.33, VINS-Mono 1.0). Every scan was processed in both runs (2959 of 2970 and 1175 of 1186 logged frames). Run-to-run non-determinism of iG-LIO (multi-threaded) is the likely cause; one run each cannot separate it from the extra CPU load of the fused stack. The GenZ-LIO paper reports divergence of iG-LIO on 30.8 % and 40.0 % of sequences, which fits.
- **The structure did not rescue it.** Fused error 5.1 m (0-120 s) and 8.2 m (0-300 s), equal to iG-LIO alone (5.3, 8.2). The consistency gate (slow check) first opened at 51.7 s (warm-up as designed: windows of the VINS segment must reach 200), closed again at 58.3 s when the LiDAR path left the VINS path, and stayed closed for 97.5 % of the fused rows (gamma = 0, LiDAR weight 0.999), so the LiDAR carried the step; the VIO scale correction rose to 3.7 (the failure mechanism of the gap test: scale follows a wrong LiDAR path); the blow-up guard did not act (the error grows by at most 0.34 m per scan, no 2.16 m in 2 s jump).
- Weights while the gate was open (t = 55 s): 0.15 / 0.25 / 0.44 (Channel T), in the range seen with GenZ-LIO (median 0.70-0.91), so the provisional c_T is of the right order.

### Stage 5 (added before any further run): how often does iG-LIO alone diverge on this stretch?
Four repeats of the Stage 2 run (I0, 110 s, Multi Floor, unchanged configuration), error at 110 s against ground truth (window re-aligned) read with `score_iglio_smoke.py`. Rule fixed now: a run counts as diverged if its error over 0-110 s is above 2 m (GenZ-LIO on the same stretch: 0.29 m). Together with the two earlier runs that gives 6 runs of iG-LIO alone.
- 0 or 1 diverged of the 6: go on to the specified full test (3 I0 recordings for the calibration), the divergence rate is reported as a result, and divergent recordings are scored and kept, not discarded.
- 2 or more of 6: iG-LIO with the authors' configuration is not a stable third front end on this sequence. The full test is not run as specified; the finding (rate, and that the structure does not rescue a front end that drifts consistently, like the G23 failure) is reported as a limit, and the report stays on two front ends. Whether to test a rescue rule is a separate decision.
- Scripts: `fusion_v4/ig_lio/score_iglio_fused.py`, `score_iglio_smoke.py`.
