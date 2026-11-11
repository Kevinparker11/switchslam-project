# Handheld (LVI-SAM dataset): what exists and what is needed before F26 / F35 runs (11 Nov 2026)

## Correction to the record
The F24 coverage list says Handheld "not run", and on 11 Nov I told the owner that no version had been run on it. That was wrong for F20: a replay log of F20 on the real LVI-SAM Handheld bag was uploaded on 30 Oct 2026 (`handheld_F20_small.csv`: 6,884 rows, 1,642 s, modes FUSED 5,605 / WARMUP 1,198 / VO_FAIL 80, fused path 2.6 km). No score of it is recorded in the repo or the project docs, and the GPS reference file it was scored against is not in this workspace, so it cannot be re-scored here. F24, F26 and F35 have not been run on it.

## What exists (now in fusion_v4/handheld/, copied from the 30 Oct scratch work, never committed before)
- `handheld_config.yaml`: VINS-Mono config for this bag (MEI camera model, 720 x 540, imu_topic /imu_raw, image_topic /camera/image_raw).
- `handheld_Extrinsics.yaml`, `handheld_Intrinsics.yaml`: LiDAR-IMU (R = diag(-1, 1, -1), t = 0) and camera-IMU from LVI-SAM's own params files.
- `score_run_xy.py`: horizontal-only ATE against a GPS-derived reference (2-D rigid fit, reference gaps above 1 s left out and counted). Reason: the bag's only reference is /gps/fix, whose vertical variance is about 370 m^2.
- `make_raw_segment.py`: cuts a segment and decodes the JPEG images to raw, because VINS-Mono cannot read /camera/image_raw/compressed.
- `check_handheld_bag.py` (new, compile and synthetic-bag tested only; the LiDAR and GPS parts have not seen a real bag): topics, rates, image format, GPS quality.

## Still needed
1. Run `check_handheld_bag.py` on the owner's bag and read the printout (topics /points_raw, /imu_raw, /camera/image_raw/compressed, /gps/fix; rates; GPS covariance and gaps).
2. A script that turns /gps/fix into the xy reference file (not in the workspace), with its cleaning rule (outliers, gaps) written before any score.
3. Compressed camera to raw: republish live in the VINS container, or write a raw bag (size printed by the checker).
4. A-LOAM launch with the LiDAR topic remapped from /velodyne_points to /points_raw, scan_line 16, and the IMU topic /imu_raw passed to the node (IMU_TOPICS).
5. Rules before the runs: arms (F5 unfed A-LOAM, F26, F35, SW), number of runs (the paper reports a mean of 3), replay rate, scoring window, what counts as failure, and that the score is horizontal only against a GPS reference, so it is not like for like with the published 3.07 / 1.25 (the reference behind the paper's number is not stated).
