# Gazebo tests (simulation, exact ground truth) - plan and stages

Why: every real test so far is a recorded bag. Simulation can create the two failure directions on purpose (LiDAR degenerate,
VINS-Mono degenerate), has exact ground truth, and is the only way to see the G20 guard act live.

Worlds: Clearpath `cpr_gazebo` 0.2.8 (the same checkout as the generation-1 farm study, `~/cpr_gazebo`), Husky, launched headless.
Nothing about the method is tuned for simulation; sensor settings are in `husky_sim_extras.urdf.xacro` and are frozen.

| Stage | What | Status |
|---|---|---|
| 1 | `./gz_smoke.sh <world>`: start the world headless, check LiDAR / camera / IMU rates, point fields, image texture, real-time factor | written, needs a laptop run |
| 2 | drive a fixed route, record the bag and ground truth, add the zero per-point `time` field, write the camera / IMU / LiDAR calibration from tf | after stage 1 passes |
| 3 | `setup_sequence.sh` + `run_fusion_study.sh G18 G19 G20 G21` (and G0), 3 runs per world | after stage 2 |

Stage-1 output is read for: PASS on lidar / camera / imu, `lidar time` normally FAIL (the plugin writes no per-point time; the
converter adds zeros, which is right because Gazebo scans have no motion distortion), IMU rate (the farm study used 200 Hz).

## Stage 2a (written 25 Oct 2026): `./gz_record.sh office [laps]`
Drives `routes/office_loop.csv` (134 m per lap, planned on the office mesh with 0.55 m clearance by `make_office_route.py`: left wing with a
dead-end lobe, centre, a ~10 m hallway about 1.5 m wide, right wing, back) at 0.5 m/s for 2 laps (the second lap revisits places, which gives the
loop-closure back end something to close) and records `/velodyne_points /imu/data /camera/image_raw /camera/camera_info /gt/husky_pose`
(`/gt/husky_pose` = exact base_link pose from Gazebo, 100 Hz). The driver was checked against a simulated unicycle: completes the route, wall clearance
0.54 m at the closest point. The office is a large open floor (44 x 25 m) with thin partition walls, not a long corridor.
Open points before stage 3: how GenZ-LIO uses the per-point `time` field (the plugin synthesises it from the azimuth although Gazebo samples all rays
at one instant, so deskewing with it would add a false correction during turns), and the calibration files (IMU frame = base_link, so
T_imu_lidar = (0, 0, 0.4) with identity rotation).
