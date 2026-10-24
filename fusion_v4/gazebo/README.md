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
