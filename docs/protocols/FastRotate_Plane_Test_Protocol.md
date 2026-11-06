# Fast Rotate and Plane (Switch-SLAM's two other Gazebo datasets): test protocol, written 6 Nov 2026, before any run

**Why.** Switch-SLAM Table II has five simulated or real datasets we have not run: Fast Rotate and Plane are the two with published numbers (SwitchSLAM_TableII_Verified.md). They are the two single-failure cases: Fast Rotate = VINS-Mono degenerate, LiDAR fine; Plane = LiDAR degenerate, VINS-Mono fine. Their worlds were not released, so these are our own recreations in the same open-source world (`cpr_gazebo` agriculture, Husky, VLP-16, camera, 200 Hz IMU, as in the generation-1 and Farm sequences). Nothing about the method is changed for these tests. They are held-out for F24 (not used in its design); the routes are fixed before the first scored run.

## What is run (one live Gazebo run each first, three where a result is close; all runs reported, failed starts counted)
Procedure: the five-terminal sequence of `Farm_L_Shape_Test_Protocol.md` Step 2 (world, controller switch, A-LOAM launch, VINS-Mono with `config/farm/farm_mono_config.yaml`, wiggle, `gt_logger.py`, reset to (0, 0, 0.2)). Arms: **F5** A-LOAM unfed (`aloam_standalone.launch`), **F24** (`fusion_node_v2.py`, settings of `run_fusion_study.sh` config F24, frozen), **SW** (exact Switch-SLAM replica, `switch_slam_node.py`, paper rule), VINS-Mono alone from the F24 log. Metric: full-span ATE RMSE and max from the reset, Umeyama SE(3), no scale (`score_fused.py`, `score_standalone.py`).

## Fast Rotate recreation
Route and driver: `fusion_v4/gazebo/live/waypoint_driver_route.py` (generic, untested in ROS when written: the first drive is a dry run). Intent: about 115 m (paper) near the barn, ground-truth check that LiDAR structure is present (barn walls in range), with fast on-the-spot turns: `SPIN_AT=all SPIN_RATE=2.0 SPIN_TURNS=1`, a spin at every waypoint, waypoints spaced 12 to 15 m. The coordinates of the waypoints must be taken from a first dry drive in the laptop world (barn position; the world is not in this container); they are written into this file before the first scored run.
- **FR-P0 (precondition, else the test is void and not adjusted):** VINS-Mono alone fails the turns (ATE > 2.5 m or VO_FAIL during the turns). The Farm spin run of 28 Oct (1.2 rad/s) did not meet this (VINS 1.61 m, no VO_FAIL in the turns), so the rate is raised to 2.0 rad/s; if VINS still survives, the test is declared void for the failure direction and reported as a rotation test only.
- **FR-1:** A-LOAM unfed does not fail (ATE <= 2.5 m, end-point error <= 5 m); the paper's LOAM is 0.44.
- **FR-2 (the question):** F24 ATE <= max(1.0 m, 1.5 x the unfed A-LOAM ATE of the same session): the VINS failure must not drag the fused output. Reported against Switch-SLAM 1.50 / 0.23.
- **FR-3 (reported, not judged):** SW against F5.

## Plane recreation
Route: a 100 to 110 m path in the crop-row field, away from the barn and fences, so the LiDAR sees ground only; speed 0.25 m/s, no turns (`SPIN_AT=none`). Waypoints from the dry drive, written here before the first scored run.
- **PL-P0 (precondition, else void and not adjusted):** unfed A-LOAM fails on it (ATE > 2.5 m or end-point error > 5 m), as the paper's LOAM does. The Hessian rule share on the logged A-LOAM Hessians is also reported (the L route's last 20 m flagged 77 % of scans while A-LOAM stayed at 0.10 m, so a flag is not a failure).
- **PL-1:** VINS-Mono alone does not fail (ATE <= 2.5 m); the paper's VINS-Mono is 1.17 / 0.41.
- **PL-2 (the question):** F24 ATE <= max(1.0 m, 1.5 x the VINS-Mono ATE of the same run).
- **PL-3 (reported, not judged):** SW against F24 and F5, Switch-SLAM published 1.27 / 0.35.

## Rules
Nothing is changed after a score. A route that does not meet its P0 is re-recorded once with the change announced, or the test is reported void; the numbers of a void test are not used for any claim. One run supports no claim; three are run only where a result lies within 50 % of the pass line. The tests are simulation, one world, our own routes: not comparable to the paper's Fast Rotate and Plane beyond the stated failure directions.

## Commands (laptop, after the dry drive fixes the waypoints; `W` and the rate are from this file)
`WAYPOINTS="$W" SPIN_AT=all SPIN_RATE=2.0 python3 waypoint_driver_route.py` (Fast Rotate); `WAYPOINTS="$W" SPIN_AT=none python3 waypoint_driver_route.py` (Plane); the rest as in Farm_L_Shape_Test_Protocol.md Steps 2 and 3.
