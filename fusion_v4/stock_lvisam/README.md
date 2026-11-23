# Stock LVI-SAM on our bags

The original [LVI-SAM](https://github.com/TixiaoShan/LVI-SAM) (Shan et al., IROS 2021), built from its own repository at one pinned commit (`0d822f6dcac3378312f6703b4f45829e049f221a`, 17 Dec 2022, upstream HEAD) in a separate Docker image `lvisam_stock`, run on the same bags, ground truth and replay rates as the stock A-LOAM and LIO-SAM runs. It shares nothing with `switchslam_gpu_v2`, `vinsmono_test` or `liosam_stock`.

**Status: written and tested offline only** (11 parameter tests, 6 runner dry runs, plus `../baselines`). The image has not been built and no bag has been played. The C++ patches were checked with `git apply` against the pinned commit but not compiled; the first build on the desktop is the real test.

## What is changed from upstream

Two patch files, applied in this order by the Dockerfile. No algorithm is touched.

`lvisam_noetic_build.patch` (needed to build on Noetic: OpenCV 4, PCL 1.10)

| File | Change |
|---|---|
| `CMakeLists.txt` | `-std=c++11` to `-std=c++14` |
| `src/lidar_odometry/utility.h`, `visual_feature/parameters.h`, `visual_loop/parameters.h` | `<opencv/cv.h>` (gone in OpenCV 4) replaced by `<opencv2/opencv.hpp>`, placed after the PCL headers (OpenCV first breaks FLANN serialization) |
| `feature_tracker_node.cpp`, `keyframe.cpp`, `BRIEF.cpp`, `loop_detection.cpp` | `CV_GRAY2RGB`, `CV_RGB2GRAY`, `CV_FONT_HERSHEY_SIMPLEX` replaced by their `cv::` names (debug drawing and a colour conversion only) |

`lvisam_extrinsics.patch` (extrinsics of our rigs instead of the authors' rig)

Upstream hard-codes a 180 degree turn about y at two places. Both are the rotation between frames of the authors' rig, so on another rig they must come from that rig's extrinsics, like the extrinsics of every other method.

| Place | Upstream | Now |
|---|---|---|
| `initial/initial_alignment.h`, `q_lidar_to_cam` (LiDAR pose to IMU pose for the VINS start) | `(0,1,0,0)` | `R_lidar_imu`, key `lidar_imu_rotation` of the VINS config |
| `utility/visualization.cpp`, `q_cam_to_lidar` (IMU pose to the camera frame with ROS axes, used for depth registration) | `(0,1,0,0)` | `R_imu_camros`, key `imu_camros_rotation` of the VINS config |

The 180 degree world yaw (`Rz(pi)`) next to them is left alone: VINS takes the converted LiDAR pose as its start state, so it only has to be one consistent rotation of both position and orientation, and it is.

Why this is correct: the authors' own config gives back their constant. Their camera-IMU rotation `[[0,0,-1],[-1,0,0],[0,1,0]]` times the optical-to-ROS axis change `M` is `diag(-1,1,-1)`, which is 180 degrees about y, and so is their LiDAR extrinsic `extrinsicRot`. `test_stock_lvisam.py` checks both. For our five rigs the two rotations come out 0.0 to 2.95 degrees from identity (measured; the tests bound it at 3.5), so the effect on a run is small; the point is that no constant of someone else's rig is left in.

`lvi_params.py` writes the two config files of a run from the upstream originals and changes only:

| File | Keys | Why |
|---|---|---|
| `params_lidar.yaml` | `pointCloudTopic`, `imuTopic`, `extrinsicTrans`, `extrinsicRot`, `extrinsicRPY`, `loopClosureEnableFlag: false` | topics and extrinsics of the sequence; no loop closure. LVI-SAM's older code applies `extrinsicRPY` without the inverse, so `extrinsicRot = R^T`, `extrinsicRPY = R`, `extrinsicTrans = -R^T t` for `T_imu<-lidar = [R t]` (differs from the LIO-SAM runs, tested) |
| `params_camera.yaml` | `imu_topic`, `image_topic`, camera model block (model, image size, intrinsics), `extrinsicRotation`, `extrinsicTranslation`, `lidar_to_cam_tx..rz`, `loop_closure: 0`, two new keys (`lidar_imu_rotation`, `imu_camros_rotation`) | topics, intrinsics and extrinsics of the sequence; no loop closure |
| `params_camera.yaml` | `fisheye: 0` | the upstream fisheye mask is a 720x540 picture and our images are 640x480 or 1224x1024; a mask of another size makes the feature tracker fail |

Everything else stays at the upstream default, including `useImuHeadingInitialization: true` (LVI-SAM's own default, unlike LIO-SAM), the IMU noise values, the feature tracker settings, `N_SCAN 16` and `Horizon_SCAN 1800`. The MEI cameras of the SubT-MRS bags need no rectification, because LVI-SAM's front end (camodocal) takes the MEI model; GEODE is PINHOLE. `params_changes.txt` of every run lists the keys that changed.

Launch: `inside.sh` writes `run.launch` with the seven nodes of upstream `module_sam.launch`, `respawn` kept, using our two parameter files. Left out: RViz and the robot state publisher (headless). The `image_transport republish` line is kept only for GEODE, whose bag stores `/left_camera/compressed` (`in:=/left_camera`, out `/left_camera/image_raw`); the SubT-MRS bags store raw images and need no republish.

Scored output: `/lvi_sam/lidar/mapping/odometry` (the scan-to-map pose, the counterpart of LIO-SAM's mapping odometry), header stamps, to `odom.tum`.

## Inputs

LiDAR side as for LIO-SAM: ring, per-point `time`, `is_dense`; the same `preflight.py`, `cloud_adapter.py` and packet conversion (`velodyne_pointcloud`, VLP16) are used from `../stock_liosam`. `cam_check.py` adds the camera topic to the preflight (a missing camera is "not applicable"). IMU: 9-axis quaternion, as LIO-SAM.

## Portable build

No `-march` flag anywhere: LVI-SAM's `CMakeLists.txt` has none, Ceres is Ubuntu's `libceres-dev` (1.14), GTSAM is the borglab PPA package or a source build with `GTSAM_BUILD_WITH_MARCH_NATIVE=OFF`. The base is `ros@sha256:72b8bc59...` (the digest of the laptop's `ros:noetic`), so loading the image on the laptop adds only the new layers. Both machines (i7-12700 and Ryzen 5 5600H) have AVX2, FMA and BMI2 and neither has AVX-512; `../baselines/check_isa.sh` fails on any AVX-512 instruction in the built binaries.

## Rule fixed before the first run (per-method failure rule, not yet agreed)

LVI-SAM maps at most every 0.15 s (`mappingProcessInterval`), the same as LIO-SAM, so at 10 Hz about one pose per two scans. Proposal, same as for LIO-SAM: a run is **failed** if a node died or respawned, or fewer than 40% of the LiDAR scans produced a pose (80% of the documented maximum), or the maximum error exceeds 100 m. VINS estimator reboots are counted and reported, not a failure by themselves. Scans are counted as the LiDAR messages of the bag. Not applicable if the preflight says so. Three runs per sequence. **Waiting for the owner's OK before the first scored run.**

## Desktop: build and smoke test (never scored)

```
cd ~/switchslam-project && git pull
docker build --network host -t lvisam_stock fusion_v4/stock_lvisam        # long, a few GB
docker run --rm -v ~/switchslam-project:/repo:ro lvisam_stock bash /repo/fusion_v4/baselines/check_isa.sh /root/lvi_ws/devel
SLICE=1 ./fusion_v4/stock_lvisam/run_lvisam.sh geode                       # 60 s of ~/slices/geode_70s.bag
SLICE=1 ./fusion_v4/stock_lvisam/run_lvisam.sh mf
```

## Laptop (scored runs)

```
cd ~/sw_new && git pull && cd fusion_v4
df -h ~                                                                   # check free space first
./baselines/load_image.sh lvisam_stock                                    # or: --from ssh://user@desktop
SMOKE=1 ./stock_lvisam/run_lvisam.sh geode                                # 60 s check
for n in lc mf c02 cave02 geode; do REPEAT=3 ./stock_lvisam/run_lvisam.sh $n; done 2>&1 | tee ~/lvisam_run123.log
```

Results go to `~/runs_lvisam/<name>/run<k>/`: `odom.tum`, `params_camera.yaml`, `params_lidar.yaml`, `params_changes.txt`, `lvisam_commit.txt`, `lvisam.log`, `crashes.txt`, `vins_reboots.txt`, `preflight.txt`, `adapter_used.txt`, `cloud_fields.txt`.

## Offline tests

`python3 test_stock_lvisam.py` and `python3 test_run_lvisam.py` (from this folder; numpy and pyyaml only). Set `LVISAM_UPSTREAM=<clone at the pinned commit>` to also run the parameter writer on the real upstream config files.
