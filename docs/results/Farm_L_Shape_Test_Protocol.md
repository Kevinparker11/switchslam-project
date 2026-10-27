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
