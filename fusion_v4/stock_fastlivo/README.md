# Stock FAST-LIVO on our bags

The original [FAST-LIVO](https://github.com/hku-mars/FAST-LIVO) (Zheng et al., IROS 2022), built from its own repository at one pinned commit (`f7e1af5b10c89ba38c5e2c5e4d458195c58eba6b`) in a separate Docker image `fastlivo_stock`, run on the same bags, ground truth and replay rates as the other stock baselines. It shares nothing with `switchslam_gpu_v2`, `vinsmono_test` or the other baseline images.

**Status: written and tested offline only** (15 parameter and build tests, 8 runner dry runs). The image has not been built and no bag has been played. All four patches were checked with `git apply` against the pinned sources and the Sophus fix was compiled; the first build on the desktop is the real test.

## What FAST-LIVO cannot take as it is, and what is done

| Upstream | Our data | Done |
|---|---|---|
| LiDAR: Livox messages, or Velodyne/Ouster clouds. With `feature_extract_enable 0` the Ouster path takes every point with its time `t` (ns) as the point time; the Velodyne path expects `time` in microseconds and recomputes it from the yaw angle if absent | Velodyne VLP-16 clouds (time in seconds) | The same converter as for R3LIVE, `../stock_r3live/vel_to_ouster.py`: it rewrites the cloud into the Ouster field layout, `t` in ns from the scan start. No coordinate changes, no point added or dropped |
| Camera: vikit models Pinhole, ATAN, Ocam | MEI (SubT-MRS), pinhole (GEODE) | MEI images are rectified to a pinhole image of the same size and principal point by `../baselines/mei_rectify.py` (zero distortion in the config). GEODE goes in as it is with its own k1, k2, p1, p2. GEODE's compressed images are decompressed to a raw topic |
| Config for our rig | Our extrinsics | `fl_params.py` writes the config from the upstream NTU_VIRAL files (below) |
| `/aft_mapped_to_init` is stamped with `ros::Time::now()`, the clock at publication | Scoring by time stamp | `fastlivo_rig.patch`, one line: the stamp is `LidarMeasures.last_update_time`, the time the published state belongs to (scan end after a LIO update, image time after a VIO update). Without it the processing lag would be a timing error in the score. The pose itself is untouched |

Base config: `config/NTU_VIRAL.yaml` and `config/camera_NTU_VIRAL.yaml`, the only upstream pair for a spinning LiDAR (Ouster, 16 lines, like our VLP-16) with a pinhole camera. Changed keys only: `lid_topic`, `imu_topic`, `img_topic`, `extrinsic_T`, `extrinsic_R` (laser_to_imu of the sequence), `Rcl`, `Pcl` (camera from LiDAR, `Rcl = R_ic^T R_il`, `Pcl = R_ic^T (t_il - t_ic)`, checked against the way `lidar_selection.cpp` uses them), and `cam_width/height/fx/fy/cx/cy/d0..d3`. Everything else stays at the upstream NTU_VIRAL value: `point_filter_num 4`, `blind 4`, `filter_size_surf 0.5`, `max_iteration 10`, `img_point_cov 1000`, `laser_point_cov 0.001`, `acc_cov_scale 100`, `gyr_cov_scale 10000`.

Two properties of that upstream choice to know before reading results: `blind 4` drops every point within 4 m of the sensor, which is a lot in a narrow corridor or cave; and the VLP-16 has the same 16 lines as the authors' Ouster, but not their environment. A run with a smaller `blind` would be a tuned variant and goes in as a separate labelled run, not into the stock numbers.

IMU: units do not matter (acceleration is normalised by its mean norm at start), no orientation is needed. As in FAST-LIO, the first IMU samples must be stationary.

The VIO half is skipped while `first_lidar_time < 10` (upstream `continue`): bags with time stamps under 10 s since epoch would run LIO only. Ours are epoch times.

Launch: `inside.sh` writes `run.launch` with the node and the two config files of upstream `mapping_avia_ntu.launch`, `required="true"`. Left out: RViz, the republish node (done separately for compressed bags), the gdb prefix. A virtual display (Xvfb) runs anyway; FAST-LIVO opens no window, only calls `cv::waitKey`.

Scored output: `nav_msgs/Odometry` on `/aft_mapped_to_init` (IMU pose in `camera_init`), recorded by `../stock_liosam/record_odom.py` to `odom.tum`. It carries one state after every LIO update and one after every VIO update, so there are more poses than LiDAR scans.

## Build notes

- `sophus_noetic_build.patch`: `so2.cpp` sets `unit_complex_.real() = 1.` which GCC 9 rejects (the member returns by value); it becomes a complex assignment. `-Werror` is removed from Sophus' CMake. Sophus a621ff is the version the FAST-LIVO README names. Compiled here.
- `vikit_noetic_build.patch`: `CV_INTER_LINEAR`, `CV_RANSAC`, `CV_WINDOW_AUTOSIZE` become the `cv::` constants (OpenCV 4 dropped the C ones). rpg_vikit is pinned at `10871da6d84c8324212053c40f468c6ab4862ee0` (master, last commit 2015).
- `fastlivo_noetic_build.patch`: `CV_INTER_LINEAR` and `CV_BGR2GRAY` in `lidar_selection.cpp`, the same two constants.
- `livox_ros_driver`: message definitions only, same commit as for R3LIVE and R2LIVE.
- Upstream sets `CMAKE_BUILD_TYPE` to Debug in its CMakeLists (flags still contain `-O3`); that stays. CMake sets the OpenMP thread count from the core count of the machine that builds; the image is built once on the desktop and shipped, so the laptop runs the same binary.
- No `-march` flag. `../baselines/check_isa.sh` fails on any AVX-512 instruction. The first three apt steps are the same text as in the R3LIVE and R2LIVE images, so their layers are shared.

## Rule fixed before the first run (per-method failure rule, not yet agreed)

FAST-LIVO publishes a pose after both LIO and VIO updates, so counting poses against LiDAR scans would let a dead LIO hide behind VIO poses. Proposal: a run is **failed** if a node died (the one node is `required`), or the recorded poses cover less than 80% of the time span between the first and last LiDAR scan of the bag, or the maximum error exceeds 100 m. Not applicable if the preflight says so (no per-point time, no camera topic). Three runs per sequence. **Waiting for the owner's OK before the first scored run**; the coverage check is added to the scoring step once the rule is agreed.

## Desktop: build and smoke test (never scored)

```
cd ~/switchslam-project && git pull
docker build --network host -t fastlivo_stock fusion_v4/stock_fastlivo
docker run --rm -v ~/switchslam-project:/repo:ro fastlivo_stock bash /repo/fusion_v4/baselines/check_isa.sh /root/fl_ws/devel
SLICE=1 ./fusion_v4/stock_fastlivo/run_fastlivo.sh geode
SLICE=1 ./fusion_v4/stock_fastlivo/run_fastlivo.sh mf
```

## Laptop (scored runs)

```
cd ~/sw_base && git fetch && git merge --ff-only origin/f22-handover && cd fusion_v4
df -h ~                                                                   # check free space first
./baselines/load_image.sh fastlivo_stock                                  # or: --from ssh://user@desktop
SMOKE=1 ./stock_fastlivo/run_fastlivo.sh geode
for n in lc mf c02 cave02 geode; do REPEAT=3 ./stock_fastlivo/run_fastlivo.sh $n; done 2>&1 | tee ~/fastlivo_run123.log
```

Results go to `~/runs_fastlivo/<name>/run<k>/`: `odom.tum`, `fastlivo_config.yaml`, `fastlivo_camera.yaml`, `params_changes.txt`, `fastlivo_commit.txt`, `fastlivo.log`, `crashes.txt`, `fastlivo_msgs.txt`, `preflight.txt`, `adapter_used.txt`, `camera_used.txt`, `cloud_fields.txt`.

## Offline tests

`python3 test_stock_fastlivo.py` and `python3 test_run_fastlivo.py` (from this folder; numpy and pyyaml only). Set `FASTLIVO_UPSTREAM`, `VIKIT_UPSTREAM`, `SOPHUS_UPSTREAM` to clones at the pinned commits to check the patches against the real sources (defaults `/tmp/fl_up`, `/tmp/vikit_up`, `/tmp/sophus_up`).
