# Stock R2LIVE on our bags

The original [R2LIVE](https://github.com/hku-mars/r2live) (Lin et al., 2021), built from its own repository at one pinned commit (`e719ca266ab53ca8915ca4e1416152993f2a55d7`) in a separate Docker image `r2live_stock`, run on the same bags, ground truth and replay rates as the other stock baselines. It shares nothing with `switchslam_gpu_v2`, `vinsmono_test`, or the other baseline images.

**Status: written and tested offline only** (16 parameter, converter and build tests, 8 runner dry runs). The image has not been built and no bag has been played. Both patches were checked with `git apply` against the pinned commit; the first build on the desktop is the real test.

## What R2LIVE cannot take as it is, and what is done

| Upstream | Our data | Done |
|---|---|---|
| LiDAR: Livox messages or Velodyne/Ouster clouds. The Velodyne and Ouster handlers never set the per-point time (`curvature`), so the scan end time equals the scan start and the LIO deskew and propagation break | Velodyne VLP-16 | `vel_to_r2live.py` writes a cloud with `x y z intensity curvature` (`curvature` = point time in ms from the scan start, points put in ascending time order) on `/os1_cloud_node/points`, the input of the Ouster handler (`lidar_type 3`, `N_SCANS 1`), which copies whole points. No coordinate changes, no point added or dropped |
| Camera: VINS-style camodocal models | MEI (SubT-MRS) and pinhole (GEODE) | Used as they are: camodocal supports both. No rectification. GEODE's compressed images are decompressed to a raw topic |
| LiDAR-IMU offset compiled in for the authors' Avia, `(0.04165, 0.02326, -0.0284)` | Our own extrinsics | `r2live_rig.patch`: the constant becomes the parameter `r2live_lio/lidar_offset_to_imu`, default the upstream value. R2LIVE has no LiDAR-IMU rotation (frames assumed aligned); ours are 0.0 to 3 degrees off identity, printed in `params_changes.txt`, not applied |
| IMU topic `/livox/imu` fixed in the LIO source | Our IMU topic | `<remap>` in the launch file, plus `imu_topic` in the camera yaml for the VIO half |

IMU: acceleration in m/s^2 as it is (`acc_mul_G 0`), no orientation needed.

`r2_params.py` writes `lio_config.yaml` (upstream `config/lio_config.yaml`) changing `lidar_type 3`, `N_SCANS 1` and adding `r2live_lio/lidar_offset_to_imu`; and `cam_config.yaml` (upstream `config/filr_cam.yaml`) changing `imu_topic`, camera model block (`model_type`, size, mirror parameter for MEI, distortion, projection) and `extrinsicRotation/Translation` (camera in the IMU frame). Everything else stays upstream, including `estimate_extrinsic 0`, `estimate_td 1`, feature tracker and filter settings.

Launch: `inside.sh` writes `run.launch` with the nodes and parameters of upstream `demo.launch` (feature_tracker, lio_feat_extract, r2live), without RViz. No display is needed: the only window calls in the source are commented out or in the calibration tool.

Scored output: `/tf` `world` to `/aft_mapped` (the LIO pose, stamped with the scan end time), recorded by `record_tf.py` to `odom.tum`. The VIO half also publishes `world` to `body`; it is not scored.

## Build notes

- `r2live_noetic_build.patch`: the `Calibration` tool of `camera_model` and its two sources are not built (OpenCV 3 constants, unused by the estimator); `CV_GRAY2RGB` becomes `cv::COLOR_GRAY2RGB`; `<opencv/cv.h>` becomes `<opencv2/opencv.hpp>` in three files; `${PCL_LIBRARIES}` is added to the `r2live` link line (the same missing `pcl_filters` symbol as R3LIVE, expected from the source, not yet confirmed by a build).
- `livox_ros_driver`: message definitions only, same commit as for R3LIVE, built in its own workspace (`/root/livox_ws`) first. R2LIVE's package.xml does not declare it as a dependency, so in one workspace catkin configured r2live before the messages existed (first desktop build).
- Ceres is Ubuntu's `libceres-dev` (1.14), the version R2LIVE's own docker file builds. No `-march` flag; `../baselines/check_isa.sh` fails on any AVX-512 instruction. The first three apt steps are the same text as the R3LIVE image, so the layers are shared when both images are on one machine.

## Rule fixed before the first run (per-method failure rule, not yet agreed)

The LIO half updates once per LiDAR scan. Proposal: a run is **failed** if a node died (VIO "reboot" or failure-detection messages in `r2live.log` are R2LIVE's own recovery, counted and reported, not failures by themselves), or fewer than 80% of the LiDAR scans produced a pose, or the maximum error exceeds 100 m. Not applicable if the preflight says so (no per-point time, no camera topic). Three runs per sequence. **Waiting for the owner's OK before the first scored run.**

## Desktop: build and smoke test (never scored)

```
cd ~/switchslam-project && git pull
docker build --network host -t r2live_stock fusion_v4/stock_r2live
docker run --rm -v ~/switchslam-project:/repo:ro r2live_stock bash /repo/fusion_v4/baselines/check_isa.sh /root/r2_ws/devel
SLICE=1 ./fusion_v4/stock_r2live/run_r2live.sh geode
SLICE=1 ./fusion_v4/stock_r2live/run_r2live.sh mf
```

## Laptop (scored runs)

```
cd ~/sw_base && git fetch && git merge --ff-only origin/f22-handover && cd fusion_v4
df -h ~                                                                   # check free space first
./baselines/load_image.sh r2live_stock                                    # or: --from ssh://user@desktop
SMOKE=1 ./stock_r2live/run_r2live.sh geode
for n in lc mf c02 cave02 geode; do REPEAT=3 ./stock_r2live/run_r2live.sh $n; done 2>&1 | tee ~/r2live_run123.log
```

Results go to `~/runs_r2live/<name>/run<k>/`: `odom.tum`, `lio_config.yaml`, `cam_config.yaml`, `params_changes.txt`, `r2live_commit.txt`, `r2live.log`, `crashes.txt`, `preflight.txt`, `adapter_used.txt`, `cloud_fields.txt`.

## Offline tests

`python3 test_stock_r2live.py` and `python3 test_run_r2live.py` (from this folder; numpy and pyyaml only). Set `R2LIVE_UPSTREAM=<clone at the pinned commit>` to also check the patches against the real source.
