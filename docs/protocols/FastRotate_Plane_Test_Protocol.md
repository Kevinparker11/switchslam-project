# Fast Rotate and Plane (Switch-SLAM's two other Gazebo datasets): test protocol, written 6 Nov 2026, before any run

**Why.** Switch-SLAM Table II has five simulated or real datasets we have not run: Fast Rotate and Plane are the two with published numbers (SwitchSLAM_TableII_Verified.md). They are the two single-failure cases: Fast Rotate = VINS-Mono degenerate, LiDAR fine; Plane = LiDAR degenerate, VINS-Mono fine. Their worlds were not released, so these are our own recreations in the same open-source world (`cpr_gazebo` agriculture, Husky, VLP-16, camera, 200 Hz IMU, as in the generation-1 and Farm sequences). Nothing about the method is changed for these tests. They are held-out for F24 (not used in its design); the routes are fixed before the first scored run.

## What is run (one live Gazebo run each first, three where a result is close; all runs reported, failed starts counted)
Procedure: the five-terminal sequence of `Farm_L_Shape_Test_Protocol.md` Step 2 (world, controller switch, A-LOAM launch, VINS-Mono with `config/farm/farm_mono_config.yaml`, wiggle, `gt_logger.py`, reset to (0, 0, 0.2)). Arms: **F5** A-LOAM unfed (`aloam_standalone.launch`), **F24** (`fusion_node_v2.py`, settings of `run_fusion_study.sh` config F24, frozen), **SW** (exact Switch-SLAM replica, `switch_slam_node.py`, paper rule), VINS-Mono alone from the F24 log. Metric: full-span ATE RMSE and max from the reset, Umeyama SE(3), no scale (`score_fused.py`, `score_standalone.py`).

## Fast Rotate recreation
Route (fixed 6 Nov 2026 from the owner's description of the world: the straight first leg of the L route runs along -y past the barn, so barn walls are in LiDAR range): out and back on that leg, 116 m, with an on-the-spot turn at every waypoint, driven by `fusion_v4/gazebo/live/waypoint_driver_route.py` (generic, only compile-checked when written: the first drive is a dry run):
`WAYPOINTS="0,-13;0,-26;0,-40;0,-27;0,-14;0,0;0,-12;0,-24;0,-36" SPIN_AT=all SPIN_RATE=2.0 SPIN_TURNS=1 LINEAR_SPEED=0.25`
(13 + 13 + 14 + 13 + 13 + 14 + 12 + 12 + 12 = 116 m, nine turns, start (0,0) after the reset). The "Spin done" lines of the dry drive show the turn rate actually reached (the Husky controller may clip 2.0 rad/s); the reached rate is reported.
- **FR-P0 (precondition, else the test is void for the failure direction and not adjusted):** VINS-Mono alone fails the turns (ATE > 2.5 m or VO_FAIL during the turns). The Farm spin run of 28 Oct (1.2 rad/s) did not meet this (VINS 1.61 m, no VO_FAIL in the turns), hence 2.0 rad/s here.
- **FR-1:** A-LOAM unfed does not fail (ATE <= 2.5 m, end-point error <= 5 m); the paper's LOAM is 0.44.
- **FR-2 (the question):** F24 ATE <= max(1.0 m, 1.5 x the unfed A-LOAM ATE of the same session): the VINS failure must not drag the fused output. Reported against Switch-SLAM 1.50 / 0.23.
- **FR-3 (reported, not judged):** SW against F5.

## Plane recreation
Route (fixed 6 Nov 2026 from the owner's description: the L route ends near the right edge of the map at (-40,-40) heading -x; a right turn there points along +y and the ground beyond is open): the L route as before, then a right turn and a straight line along +y, no turns anywhere (`SPIN_AT=none`):
`WAYPOINTS="0,-40;-20,-40;-40,-40;-40,-10;-40,25;-40,65" SPIN_AT=none LINEAR_SPEED=0.25`
= 80 m of the known L route + 105 m of open ground (paper: 109 m, ground only). The robot is reset to (0, 0, 0.2) as in every farm run, because the VINS-Mono initialisation wiggle is done at the spawn. The dry drive checks that (-40,65) is inside the map and drivable; if the open stretch ends earlier, the endpoint is shortened to the last open point and the length reported.
- **Scoring (fixed now):** primary = the open-ground leg alone, from the first GT sample past (-40,-40) to the end, each output aligned on that leg only (Umeyama SE(3), no scale), because the paper's Plane is ground only; secondary = the whole route from the reset. Both reported.
- **PL-P0 (precondition, else void and not adjusted):** unfed A-LOAM fails on the open-ground leg (leg ATE > 2.5 m or leg end-point error > 5 m), as the paper's LOAM does. The Hessian rule share on the logged A-LOAM Hessians of the leg is also reported (the last 20 m of the L route flagged 77 % of scans while A-LOAM stayed at 0.10 m, so a flag is not a failure).
- **PL-1:** VINS-Mono alone does not fail on the leg (leg ATE <= 2.5 m); the paper's VINS-Mono is 1.17 / 0.41.
- **PL-2 (the question):** F24 leg ATE <= max(1.0 m, 1.5 x the VINS-Mono leg ATE of the same run).
- **PL-3 (reported, not judged):** SW against F24 and F5; Switch-SLAM published 1.27 / 0.35.

## Rules
Nothing is changed after a score. A route that does not meet its P0 is re-recorded once with the change announced, or the test is reported void; the numbers of a void test are not used for any claim. One run supports no claim; three are run only where a result lies within 50 % of the pass line. The tests are simulation, one world, our own routes: not comparable to the paper's Fast Rotate and Plane beyond the stated failure directions.

## Commands (laptop)
The five-terminal procedure of Farm_L_Shape_Test_Protocol.md Steps 2 and 3, with the driver of terminal 8 replaced:
- Fast Rotate: `WAYPOINTS="0,-13;0,-26;0,-40;0,-27;0,-14;0,0;0,-12;0,-24;0,-36" SPIN_AT=all SPIN_RATE=2.0 python3 waypoint_driver_route.py`
- Plane: `WAYPOINTS="0,-40;-20,-40;-40,-40;-40,-10;-40,25;-40,65" SPIN_AT=none python3 waypoint_driver_route.py`
Order: dry drive of each route with A-LOAM unfed (F5) first (this is also the P0 check), then F24, then SW. Send the GT file, the node logs and the "Spin done" lines; scoring is done offline here.

## Driver fix after the first Plane attempt (7 Nov 2026)
First Plane attempt: the robot reached waypoints 1 to 3 (80.6 m, (-40,-40)) and then got stuck at the fence ("Obstacle at 1.35 to 1.49 m, turning to avoid" repeating). Cause: the avoidance turned in a random direction; with the target on the right (+y) a left turn pointed away from the target and the next goal steering turned back into the fence. Fix to `waypoint_driver_route.py` (driver only; route, speed, sensors, F24 and the scoring rules unchanged): the avoidance turn now goes toward the current waypoint (random only if the target is straight ahead), and after 12 s blocked the robot backs off 3 s. The stuck attempt is not used for any claim; the re-run is the first scored attempt and the change is announced here. If the fence still blocks the turn, the corner waypoint is moved inward and the new coordinates are written here before the run.
