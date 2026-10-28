# Farm L-shape test: the current method on the route used for the Switch-SLAM-style replication (protocol written 27 Oct 2026, before any run)

## What the old test was
Generation 1 (Sep 2026, `switchslam_v1/farm/`): Gazebo farm/panels world (Clearpath `cpr_gazebo`), Husky, VLP-16, monocular camera, 200 Hz IMU. The robot was reset to (0, 0, 0.2) and
driven by `waypoint_driver_v4.py` along (0,0) -> (0,-40) -> (-20,-40) -> (-40,-40): an L of about 80 m, one pass, no revisit. The Switch-SLAM-style switching node
(`switching_node_v9.py`) was run on it three times. Numbers recomputed on 27 Oct from the logs in `switchslam_v1/logs/` (full-span ATE, Umeyama SE(3), no scale; ground truth = the `gt_*` columns):

| Log | duration | GT path | fused output ATE / max (m) | A-LOAM output alone ATE / max (m) |
|---|---|---|---|---|
| switching_log_v9_Lshape | 958 s | 82.0 m | 5.02 / 10.95 | 0.32 / 1.64 |
| switching_log_v9_Lshape_run2 | 404 s | 81.7 m | 5.79 / 9.35 | 0.44 / 0.84 |
| switching_log_v9_Lshape_run3 | 386 s | 82.1 m | 5.18 / 9.92 | 0.48 / 1.93 |

So in that test the switching node was about ten times worse than A-LOAM alone (mode counts: mostly LIDAR_ONLY or TIGHTLY_COUPLED, TRANSITION about 40 frames). The "best Farm result 0.32 m" quoted in the folder README is the A-LOAM column of run 1, not the fused output.

## What is tested now
The same world and the same L route, recorded once as a bag (`./gz_record.sh farm 1`), converted as for the office world (`./gz_prepare.sh farm`, time-ramp variant `gzfarm_nd`, chosen on physical grounds before), then run 3 times each:
- **F5**: A-LOAM alone (the LiDAR-only control; reproduces the old A-LOAM column).
- **F8**: the A-LOAM master method (soft Schur translation weight, C_T = 0.03, no gate), then the loop-closure back end (`run_backend.py`, iso weights, 1 round, settings frozen from Multi Floor).
- **G20**: RTS-Fusion on the GenZ-LIO front end (frozen 24 Oct settings). GenZ-LIO alone, G17 and G19 are obtained by exact replay of the G20 logs.
VINS-Mono alone comes from the same logs. Nothing is tuned for this world.

## Rules fixed before the recording exists
1. Metric: full-span ATE RMSE and max error (Umeyama SE(3), no scale), exact ground truth from `/gt/husky_pose`.
2. P1 (replication check): F5 is within 0.2 m of the old A-LOAM values (0.32-0.48 m), else the new recording is not the old test and this is reported first.
3. P2 (the question): F8 and G20 each have ATE below 2.5 m (half the old switching node's 5.0-5.8 m) in 3 of 3 runs.
4. P3 (not predicted to hold, reported either way): F8 / G20 at or below the LiDAR-only controls (F5, GenZ-LIO alone). The office world showed the fusion costing accuracy when the LiDAR alone is excellent; the same is expected here.
5. P4: the loop-closure back end changes the F8 ATE by less than 0.1 m, because the route never revisits a place. A loop that is accepted anyway is a false loop and is reported.
6. A failed recording (robot stuck, VINS-Mono does not initialise, collision with a panel) is reported as such and a re-record is announced, not done silently. All runs are reported.

## Limits written down now
- The route has no revisit, so this test cannot show a loop-closure gain; it checks the front end and the weighting. A loop test needs a second pass (e.g. L out and back), which would be a different test.
- The old world is assumed to be `cpr_agriculture_gazebo/agriculture_world.launch`; confirm with `./gz_smoke.sh agriculture` and the old shell history before recording.
- The old driver had obstacle avoidance; `gz_driver.py` (pure pursuit on the planned line) has none. If the line meets a panel the driver reports STUCK (exit 3).
- One recording, three live runs: replicates of the same trajectory, not independent samples. Simulation results are reported separately from real data.

## Correction and match with the generation-1 test (27 Oct 2026, after the first recording)
Checked against `switchslam_v1/farm/`: the old L-shape runs used `waypoint_driver_v4.py` (nominal 0.25 m/s, 0.05 m/s^2 acceleration limit, LiDAR-based obstacle avoidance), live nodes in a real-time Gazebo session (the logs last 386-958 s for 82 m), the switching node `switching_node_v9.py`, the `husky_200hz_imu.urdf.xacro` robot and `farm_mono_config.yaml` for VINS-Mono. A second generation-1 route, the panel-parallel route (`waypoint_driver_panels.py`, waypoints taken from a manual drive alongside the panels, about 90 m), is not the L-shape and is not part of this test.
What is the same: the L waypoints (0,0)-(0,-40)-(-20,-40)-(-40,-40), the robot reset to (0, 0, 0.2), Husky with VLP-16, a monocular camera and a 200 Hz IMU, exact Gazebo ground truth, an L of about 80 m.
What is not: the new recording is driven by `gz_driver.py` at 0.5 m/s (177 s, 1773 scans, route completed), twice the old nominal speed; the sensor description is `husky_sim_extras.urdf.xacro`, not the old xacro; the methods are replayed from a bag (exact for GenZ-LIO and VINS-Mono, which take no feedback) instead of live in a GUI session; and the world launch (`agriculture_world.launch`) is assumed, not confirmed. So this is the same route and a similar world, not a re-run of the old session.
To remove the speed difference the bag can be re-recorded at the old nominal speed: `GZ_SPEED=0.25 ./gz_record.sh farm 1` (about 6 min of bag). Both recordings would be reported; the choice of which is the main one is made before any score is looked at.

## Results of the first recording (27 Oct 2026, GZ_SPEED=0.25, 340 s, 3401 scans, 80.6 m of ground-truth path; one live run each, nothing changed after seeing a score)
Full-span ATE RMSE / max (m), Umeyama SE(3), exact ground truth:

| Method | ATE / max | How obtained |
|---|---|---|
| F5 A-LOAM alone | **0.10 / 0.19** | live, A-LOAM stack |
| F8 (C_T 0.03, no gate) | **0.99 / 2.71** | live, A-LOAM stack |
| GenZ-LIO alone | 7.34 / 15.73 | replay of the G20 log |
| VINS-Mono alone | 4.14 / 10.53 | replay |
| G8 / G16 | 7.84 / 7.92 | replay |
| G9 / G17 (RTS-core without / with SAH) | 2.49 / 2.51 | replay |
| G18 / G19 | 6.41 / 6.32 | replay |
| **G20 (RTS-Fusion)** | **6.46 / 14.49** | live (replay 6.462 equals the live value) |
| G21 (G20 + VINS information floor 1e-3, defined 24 Oct) | 6.38 / 14.33 | replay |
| G22-type (c_T 3e-5 on the G20 settings) | 6.74 | replay |
| Switch-SLAM rule re-run (SW, SWR) | 4.14 / 10.53 | replay; identical to VINS-Mono alone: the rule never took the LiDAR translation |
Generation-1 switching node on the same L route: 5.02 / 5.79 / 5.18 m (A-LOAM alone 0.32 / 0.44 / 0.48 m).

Rules (fixed before the recording):
- **P1 (replication check) not met as written:** F5 is 0.10 m, 0.22 m below the lowest old value (0.32 m), outside the 0.2 m window. The new A-LOAM-alone run is better than the old live ones; the old runs were live, in real time with a GUI, and could drop scans (different driver and speed too). This recording is therefore not a replica of the old session, and nothing in the old numbers is reproduced exactly.
- **P2:** F8 0.99 m (one run) is below 2.5 m; **G20 6.46 m is not.** G9 passes by 0.007 m, G17 misses by 0.007 m.
- **P3 (fusion at or below the LiDAR alone):** not met, as predicted: F8 is 0.99 against 0.10 for A-LOAM alone; G20 6.46 against 7.34 for GenZ-LIO alone (there the fusion is below the front end, but the front end failed).
- **P4:** the loop-closure back end has not been run; the route never revisits a place.

Why G20 fails (log analysis): on leg 2 (40 m west) GenZ-LIO moved 17.5 m in x (true about 40) and 6.5 m sideways, VINS-Mono moved 49.5 m (scale +24 %, leg 1 +9 %); the Hessian showed two weak translation directions (c_T x eigenvalue 0.24 and 0.38), but the VINS consistency check compared the path lengths, closed the VINS prior (gamma = 0) for 89 % of leg 2 and the LiDAR weight became 1 in every direction. The check cannot tell which sensor is wrong; it assumes the LiDAR is the metric reference. The G17 / G9 structure without the check reaches 2.5 m; the check that was added for GEODE (where VINS-Mono scale fails, G17 17.6 m) costs 4 m here. A-LOAM, by contrast, tracks the route to 0.10 m, so the failing component is our GenZ-LIO configuration on this world, not the world itself.
Limits: one recording, one live run per method (GenZ-LIO alone differed by up to 0.6 m between runs of the same bag on Multi Floor); simulation; the driver and speed differ from the generation-1 session. No setting has been changed. This recording is now held-out data for any later change to G20.

## Decision of 27 Oct 2026: the bag-based farm test is withdrawn; the original live Gazebo run is repeated (written before any new run)
Why: the recorded bag does not exercise the case this test was meant for. Applying the Switch-SLAM degeneracy rule (Eq. 12, [0.12, 0.27, 0.48]) to the logged A-LOAM Hessians (F5 and F8 give identical numbers) flags 19.8 % of scans (0 % on the first 40 m, 0 % on 40-60 m, 77 % on the last 20 m, where only the smallest normalised eigenvalue is just under its threshold, median 0.11), yet A-LOAM alone is at 0.10 m on every leg (0.101 / 0.088 / 0.112 m). The same rule flags 9.7 % of GEODE scans. A flag is therefore not a failure here, and the recording is not a LiDAR-degenerate test. The numbers above stay on record as reported; they are not used to support any claim about degeneracy.
What is run instead: the generation-1 procedure from `~/switchslam_project/farm/FARM WORKING COMMANDS` (23 Sep 2026), unchanged: Gazebo GUI with `cpr_agriculture_gazebo agriculture_world.launch` and `HUSKY_URDF_EXTRAS=/root/catkin_ws/husky_velodyne_extra.urdf.xacro`, controller switch, A-LOAM launch, VINS-Mono (feature_tracker, vins_estimator, `config/farm/farm_mono_config.yaml`), wiggle, `switching_node_v9.py` (BASE), robot reset to (0, 0, 0.2), `waypoint_driver_v4.py` (autonomous L, 0.25 m/s), log pulled from `/switching_log_v9.csv`.
Rules fixed now:
1. Three runs, each from a full clean restart. All are reported, including failed starts (VINS not initialised, robot stuck).
2. Metric as before: full-span ATE RMSE and max, Umeyama SE(3), no scale, ground truth = the `gt_*` columns; the fused output and the A-LOAM output alone (`aft_*`) are both scored.
3. Replication check (P1'): the A-LOAM-alone ATE of each run lies within the old range 0.32-0.48 m by 0.2 m, and the fused ATE within 5.0-5.8 m by 1.0 m. If not, it is reported before anything else.
4. Nothing is changed in the node, driver or configs. Our current method (F8 / G20) is not part of this run: it exists only as a bag-replay pipeline, and putting it into a live session needs a separate, announced step.

## Step 2 (28 Oct 2026, written before any run): the original five terminals with the switching node replaced by F8
Requested by the owner: everything as in the generation-1 sequence (Gazebo GUI with `agriculture_world.launch` and the old `HUSKY_URDF_EXTRAS`, controller switch, `aloam_velodyne_VLP_16.launch` with rviz and the `/switch_fused_pose` remap, VINS-Mono with `config/farm/farm_mono_config.yaml`, wiggle, reset to (0, 0, 0.2), `waypoint_driver_v4.py`), with one change: terminal 5 runs `fusion_node_v2.py` with the F8 settings (`FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9`; all other node settings at their defaults: no gate, no SAH, no consistency check) instead of `switching_node_v9.py`. It publishes to the same `/switch_fused_pose`, so A-LOAM is fed by it exactly as it was by the old node.
Two additions that do not touch the estimate: (1) a passive logger (`gazebo/live/gt_logger.py`) writes the Husky pose from `/gazebo/model_states` (the old node logged gt itself, F8's node does not); (2) the LiDAR-to-IMU extrinsic the F8 node needs is read from tf of the running robot (`gazebo/live/make_live_extrinsics.py`; the IMU is the hector plugin on `base_link`), because the generation-1 rig is not the rig of the bag test.
Rules fixed now: three runs, each from a full clean restart, all reported (a failed start counts as a run). Scoring starts at the reset to (0, 0, 0.2) (the teleport is the jump in the ground-truth file), so the wiggle and the teleport are not scored; full-span ATE RMSE and max, Umeyama SE(3), no scale, for the fused output; the A-LOAM output of the same log is reported beside it. Predictions: (S1) F8 below 2.5 m (half the old node's 5.0-5.8 m) in 3 of 3 runs; (S2) not below A-LOAM alone (old 0.32-0.48 m), as in the office world and the bag test (F8 0.99 m against 0.10 m); (S3) the live F8 is within a factor 2 of the bag-test F8 (0.99 m). Nothing is changed after seeing a score.

### Step 2, run 1 of 3 (28 Oct 2026, live, Gazebo GUI, F8 node in terminal 5; scored from the reset at t = 184.7 s)
GT path 80.9 m, route completed (end (-38.5, -40.0)), 3525 scored poses; modes after the reset FUSED 3394 / WARMUP 221 / VO_FAIL 3 (first FUSED 22.6 s after the reset). Full-span ATE RMSE / max (m), Umeyama SE(3), no scale:

| Output | ATE / max |
|---|---|
| **F8 fused** | **0.490 / 0.750** |
| A-LOAM output of the same run (fed by the F8 predictions, so not an independent A-LOAM-alone run) | 0.385 / 0.905 |
| VINS-Mono alone (same log) | 1.222 / 5.696 |
| Generation-1 switching node, same route, same procedure (3 runs) | 5.02 / 5.79 / 5.18 |
| Generation-1 A-LOAM output (3 runs) | 0.32 / 0.44 / 0.48 |
| Bag test, F8 | 0.99 / 2.71 |

By leg of the GT path (fused error after the global alignment): 0-40 m 0.36 (max 0.62), 40-60 m 0.56, 60-81 m 0.59 (max 0.75); fused path length 83.0 m against 80.8 m.
Predictions: S1 met (0.49 < 2.5 m; 1 of 3 runs so far). S2 met in the weak sense (fused 0.49 is not below the old A-LOAM range 0.32-0.48). S3 narrowly missed: 0.490 is 2.02 times lower than the bag-test F8 (0.99); the factor-2 bound was 0.495. P1' (replication of the old procedure): the A-LOAM output 0.385 is inside the old 0.32-0.48 range. One run; runs 2 and 3 are still to be done. The extrinsic printout of `make_live_extrinsics.py` was not sent for the record.
