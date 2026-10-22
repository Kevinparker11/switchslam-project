# Cave02 control: SAH must switch itself off (19-20 October 2026)

Follows `SAH_Live_Results_F16.md` (its "Next" item 5, cave control, is now done). Full record: Complete Test Record, Phase 19; Master Project Report, Phase 19 and Section 11.1.

## Question and rule (fixed before any Cave02 run, in `run_cave_batch.sh`)
SAH (config F16 = F8 + structure-anchored heading) should apply almost no correction where the scene has no straight-wall structure. Pass: (1) final total SAH correction under about 2 degrees and few accepted updates; (2) F16 mean ATE within 0.2 m of the F8 mean. No setting was changed after the results.

## Sequence
SubT-MRS Cave02 (Laurel Caverns, handheld). `cave02.bag`, 956 s: `/camera_1/image_raw` 23,473 msgs (bgr8, median brightness 113 of 255, first sampled frame 35), `/imu/data` 190,994, `/velodyne_points` 9,471 (PointCloud2). Ground truth `cave02_gt.txt`: TUM, 4,731 poses at 5 Hz, 954 s, 475 m path, start-end under 0.1 m. The ground truth is on the sensors' header clock: first LiDAR header stamp 1681498133.80, first ground-truth stamp 1681498134.61 (0.81 s); the record times (1686284818) are on another clock. Calibration: one extrinsics and one intrinsics file for all four caves on the SubT-MRS datasets page (saved as `cave03_extrinsics.yaml`, `cave_Intrinsics.yaml`). VINS-Mono config from `make_vins_config.py`, nothing tuned. The platform stands still for about 45 s, then moves 2.5 m and stops again.

## Smoke tests
- 70 s: VINS-Mono never started (not enough excitation); LiDAR path fine.
- 200 s: VINS-Mono from 71.0 s and first fused row at 118.5 s after the first mapped scan; 1972 rows, no scan loss.

## Batch (`run_cave_batch.sh`, 0.5x, F8 and F16 alternating runs 1-3, then F0 runs 1-3; 19 Oct 21:17 to 20 Oct 01:40)
9,441-9,454 rows per run (limit 6,884); none failed. The batch scorer failed on all nine runs (the ground-truth path "One Touch1" contains a space); logs were scored afterwards with `score_run.py` against the ground truth in the zip.

| Config | Runs, ATE RMSE (m) | Mean +- sd | Notes |
|---|---|---|---|
| F0 VINS-Mono | 10.21, 10.26, 10.26 | 10.25 +- 0.03 | control |
| F8 | 4.71, 4.31, 4.40 | 4.47 +- 0.21 | max error 6.75-7.74 m |
| F16 | 3.97, 5.10, 4.11 | 4.40 +- 0.61 | SAH total correction 0.00 deg and acc = 0 in every row of all three runs |

## Findings
1. Null test passed. SAH applied exactly 0.00 degrees in all three F16 runs, so F16 = F8 by construction. F16 - F8 = 0.08 m, inside the 0.2 m rule.
2. The 0.08 m is run noise. Single F16 runs differ by up to 1.1 m. VINS-Mono started at different times between runs: warm-up lasted 1,174 rows in 4 runs, about 1,270 in 3 and about 1,670 in 2, so F8 and F16 were not matched in start time. The effect on the error was not examined.
3. The LiDAR correction cuts the error by 56% against VINS-Mono alone (10.25 to 4.4-4.5 m). VINS-Mono lost tracking (VO_FAIL rows, 4-11 per run) in 5 of 9 runs.
4. Absolute accuracy is poor. DCReg's table lists about 1.30 m (129.78 cm) for LiDAR odometry on Cave02; that is a different method and metric, so it is context only. No cave accuracy claim is made. Cave02 was not used for any decision.

## Why the cave error is large (offline checks on the nine logs, 20 Oct; no new runs)
- The error is spread over the whole run: 60-120 s windows of the fused output score 1.7-9.3 m RMS; the first 120 s (LiDAR-only warm-up) carry 14-36% of the squared error.
- Heading is not the problem here. After the first minute the yaw error against ground truth stays within about +-4 deg (median rotation error 1.9-3.1 deg for F8/F16); early on it is larger (4-23 deg at 60 s). On the corridors VINS-Mono yaw drift dominated.
- Fused paths are 551-584 m long against 475 m of ground truth.
- Replay of the logged F8 data with more LiDAR trust does not help: C_T 0.03 gives 4.75 / 4.33 / 4.44 m (live 4.71 / 4.31 / 4.40); C_T 0.3 4.91 / 4.72 / 4.55; C_T 3 5.04 / 4.87 / 4.67; W = I 5.06 / 4.89 / 4.68.
- Reading: neither SAH nor the translation weights limit the cave result; the logged scan-to-map pose and VINS-Mono themselves are weak there. Diagnostics only. Any change tuned on Cave02 would make it development data.

## Pipeline faults found
- `setup_sequence.sh` writes `BAG_DIR` and `GT` into `seq.env` without quotes: a path with a space ("One Touch1") broke the smoke test. Quoted by hand (`cave_smoke.sh`).
- `run_fusion_study.sh` passes the ground-truth path unquoted to the scorer: the same space produced usage errors in all nine `ate_*.txt`. Not yet fixed in the code.

## Still open
Untouched structured sequence (GEODE Stairs_Alpha or another SubT-MRS sequence), Cave01/03/04 are optional repeats, matched F8 + loops on Multi Floor at 0.5x, Corridor02 loop rejection.
