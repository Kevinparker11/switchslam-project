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

## Stage 2b (25 Oct 2026): `./gz_prepare.sh office`
Stage 2a recorded 639 s (6391 scans at 10 Hz, 200 Hz IMU, 9645 camera frames, exact pose at 100 Hz). Stage 2b converts it with `gz_convert.py`
(ground truth to TUM text; a second bag whose per-point time is an azimuth ramp over 0.1 ms) and writes `gazebo_intrinsics.yaml` / `gazebo_extrinsics.yaml`
(`make_sim_calib.py`; fx = fy = 381.361 as in the farm study, laser_to_imu = (0, 0, 0.4) with identity rotation because the Husky IMU frame is
base_link) and calls `setup_sequence.sh` for two sequences: `gzoffice` (plugin time as recorded) and `gzoffice_nd` (time ramp).
The plugin writes time = 0 for every point (found in the first conversion). GenZ-LIO reads a varying `time` field as seconds from the scan start;
a constant field makes it rebuild the time from the azimuth (CloudConversion.cpp), i.e. it deskews as if the scan took 0.1 s although Gazebo sampled
all rays at one instant. The nd variant therefore replaces the field by an azimuth ramp over 0.1 ms. Which variant is the physically right input is decided with a GenZ-LIO-alone
(G0) pilot against the exact ground truth, before any fusion configuration is run.

## Stage 3, held-out world: `construction` (written 25 Oct 2026, before the world was recorded)
Purpose: test, on a recording nobody has looked at, whether G22 (G20 with C_T = 1e-5, chosen on development data) is better than G20.
`office_construction` is the same building with other clutter, so it is a new recording and a new route but not a new floor plan; read it that
way. The route (`routes/construction_loop.csv`, 141 m per lap, 0.67 m minimum clearance) was planned from the rasterised mesh only
(`make_office_route.py <dae> <out.csv> construction`), in a different order of the wings than the office route. Commands (laptop):
`./gz_smoke.sh construction` (optional), `./gz_record.sh construction`, `./gz_prepare.sh construction`, `./gz_batch.sh construction`.
Rule written down before the recording exists (nothing is tuned afterwards):
1. Data: sequence `gzconstruction_nd` only (the time-ramp variant, chosen on physical grounds for the office world). 3 runs of G20 live, 1 of G22 live; G0, G17, G19 and G22 (for runs 1-3) by replay of the G20 logs.
2. Metric: full-span ATE (Umeyama SE(3)) of each run, median over the 3 G20 runs against the median of the replayed G22.
3. Verdict: G22 better if its median is lower by more than 0.05 m and 10 %; worse if higher by the same margin; otherwise no difference. All
   outcomes, including a failed run, a stuck robot or G22 worse, are reported, together with GenZ-LIO alone and the live-vs-replay check.
4. A recording that fails (driver stuck, VINS does not initialise) is reported as such, and a re-record is announced, not silent.
