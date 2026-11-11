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

## Bag check, owner's printout of 11 Nov 2026 (`handheld.bag`, 10.3 GB, in laptop_bags/handheld on the external drive)
- 1,642.9 s, 1,716,700 messages. Topics: /points_raw 16,289 scans at 9.91 Hz (VLP-16, 16,309 points per scan, fields x y z intensity ring time); /imu_raw and /imu_correct 500 Hz; /camera/image_raw/compressed 49,283 frames at 30 Hz (mono8, 720 x 540); /gps/fix 8,215 fixes at 5 Hz.
- The first /imu_raw sample has gravity on -z (accel -2.46, 0.05, -9.39): the IMU is mounted upside down, consistent with the extrinsic R = diag(-1, 1, -1) in handheld_Extrinsics.yaml.
- GPS: status values 0 and 2, horizontal variance median 0.01 m^2 (90th percentile 0.06, maximum 146.3), vertical variance median 368.6 m^2 (z not usable), no gap above 1 s (maximum 0.3 s), path 2,286 m, extent 410 x 319 m, no jump above 5 m between fixes. Horizontal reference quality looks good apart from a few high-variance fixes.
- Camera: a raw bag would be about 19.2 GB, so the images are republished live. VINS-Mono's `freq: 10` in the config drops the 30 Hz stream to 10 Hz.
- The F20 log of 30 Oct spans 1,642.4 s, i.e. the whole bag.
- Reference script: `make_gps_reference.py`, cleaning rule fixed before any score: drop fixes with status < 0 or horizontal variance above 1.0 m^2; counts printed; no smoothing. `score_run_xy.py` now takes `--src fused|aft|vins`.
