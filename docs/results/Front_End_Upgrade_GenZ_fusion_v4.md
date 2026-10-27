# fusion_v4: the master system with GenZ-LIO in place of A-LOAM (21 Oct 2026)

The master (`fusion_v3`, config F16 on A-LOAM) is unchanged and stays the reference. This folder is a separate
copy. The fusion node, the fusion rules (Schur R monitored, Schur T soft translation weight, SAH as the additional T),
the keyframe recorder and the back end are byte-identical to the master (`fusion_core.py`, `fusion_node_v2.py`,
`structure_heading.py`, `keyframe_recorder.py`, `v2_tools.py`). Only the LiDAR front end changes.

## Why GenZ-LIO (comparison of options)

What our fusion needs from the LiDAR front end: (1) a scan-to-map pose per scan; (2) the 6x6 information (Hessian)
of that registration, for the Schur R / T channels; (3) the registered scan, for SAH and keyframes; (4) ROS 1 Noetic,
VLP-16 PointCloud2, real time on the laptop; (5) no tuning on our test sequences.

| Option | Multi Floor | Long Corridor | Cave02 | Divergence (GenZ-LIO Table 4) | Information available | ROS 1 | Verdict |
|---|---|---|---|---|---|---|---|
| A-LOAM (master) | 26.4 (ours) | 15.8 (ours) | – | – | yes (patched Ceres Hessian) | yes | current |
| **GenZ-LIO** (T-FR 2026) | 0.26 | 1.90 | 0.44 | 0 % / 0 % | yes: J^T R⁻¹ J of its ESIKF update (5-line patch) | yes, Noetic | **chosen** |
| iG-LIO (RA-L 2024) | 0.25 | 1.55 | 0.43 | 30.8 % / 40.0 % | yes (GICP IESKF), needs patch | yes | runner-up: as accurate here, diverges on other data |
| FAST-LIO2 | diverged | 1.77 | 4.49 | 23.1 % / 0 % | yes | yes | diverges on Multi Floor |
| DLIO | 3.47 | 2.29 | 0.57 | 53.9 % / 26.7 % | not exposed | yes | unstable |
| Point-LIO / Faster-LIO | 1.71 / 2.84 | 29.1 / 9.76 | 6.57 / 0.81 | – | yes | yes | weak on the corridor |

GenZ-LIO has the accuracy of the best option on our sequences, never diverged in its 42-sequence benchmark, ships
SubT-MRS VLP-16 configurations, runs on ROS 1 Noetic, and its update already computes the information we need.
Caveat: GenZ-LIO's Table 4 used a separate configuration per sequence. We use ONE frozen configuration, their Multi
Floor file (our tuning sequence), with our own extrinsic (`genz/make_genz_config.py`). Expect our GenZ-only numbers
to be somewhat worse than their table on Long Corridor and the caves.

## What was added
| File | Purpose |
|---|---|
| `genz/patch_genz_information.py` | Exports the LiDAR-only information J^T R⁻¹ J (6x6, [dp_W, dθ_I]) in `/Odometry` pose.covariance. Verified: compiles, all 17 GenZ core tests pass, and on GenZ's floor test scene the exported matrix equals J^T R J (z ≈ 8.9e6, x/y ≈ 0.5–0.7). |
| `lio_bridge.py` | Republishes GenZ output as A-LOAM topics: `/aft_mapped_to_init` (LiDAR pose), `/laser_hessian` (information moved to the LiDAR body frame [dθ_L, dt_L] and A-LOAM units), `/velodyne_cloud_registered`. The frame change is checked against a numerical Jacobian (`tests_v4/test_lio_bridge.py`, error < 1e-10). |
| `genz/make_genz_config.py` | Writes the single frozen GenZ configuration. |
| `genz/install_genz.sh` | Builds GenZ-LIO (pinned commit bf444f7) with the patch in `/root/genz_ws` inside the ROS container. A-LOAM's workspace is not touched. |
| `genz/check_bag_fields.sh` | Checks that the bags' LiDAR clouds carry per-point time or ring. |
| `genz/calibrate_genz_c.py` | Chooses GENZ_C_T on Multi Floor only (same rule as C_T = 0.03). |
| `run_fusion_study.sh` | FRONT=genz (default): starts GenZ-LIO + bridge instead of A-LOAM; results go to `<OUT_DIR>_genz`. Configs G0 (GenZ alone), GV (VINS-Mono control), G8 (F8 rule), G16 (F16 rule). |

## Information scale
GenZ's information is weighted by inverse variances, so it is about 10^5–10^7 times larger than A-LOAM's Hessian.
C_T = 0.03 does not carry over; GENZ_C_T is chosen on Multi Floor only and frozen. Because GenZ-LIO takes no
feedback from the fusion node, replaying a G0 log with any GENZ_C_T is exact, so one recorded G0 run per sequence
gives exact G8 results and (with its keyframes) G16 results offline.

## Run order (on the laptop)
1. `cp -r fusion_v4 ~/switchslam_channelT/` (next to fusion_v3; do not overwrite it).
2. `bash ~/switchslam_channelT/fusion_v4/genz/install_genz.sh 2>&1 | tee ~/install_genz.log` (once, 10–20 min).
3. `bash ~/switchslam_channelT/fusion_v4/genz/check_bag_fields.sh "<Corridor02 bag folder>" "<Cave02 bag folder>"`
4. Smoke test on Multi Floor: `cd ~/switchslam_channelT/fusion_v4 && SMOKE=1 SMOKE_SECS=120 ./run_fusion_study.sh G0`
5. Multi Floor: `REPEAT=3 RECORD_KF=1 ./run_fusion_study.sh G0` then upload `~/runs_v2_genz` logs; GENZ_C_T is
   chosen with `genz/calibrate_genz_c.py` and frozen.
6. Other sequences, frozen: `SEQ_ENV=~/runs_corridor/seq.env PLAY_RATE=0.5 REPEAT=3 RECORD_KF=1 ./run_fusion_study.sh G0`
   (same for Corridor02 and Cave02), then live `GENZ_C_T=<frozen> ... ./run_fusion_study.sh G16` for confirmation.
