# Stock R3LIVE on our bags

The original [R3LIVE](https://github.com/hku-mars/r3live) (Lin and Zhang, 2022), built from its own repository at one pinned commit (`6143a38537f28cb36eb24e9bbe2e39c8f7967157`) in a separate Docker image `r3live_stock`, run on the same bags, ground truth and replay rates as the stock A-LOAM, LIO-SAM and LVI-SAM runs. It shares nothing with `switchslam_gpu_v2`, `vinsmono_test`, `liosam_stock` or `lvisam_stock`.

**Status: written and tested offline only** (16 parameter, converter and build tests, 8 runner dry runs, plus `../baselines`). The image has not been built and no bag has been played. The patch was checked with `git apply` against the pinned commit but not compiled; the first build on the desktop is the real test.

## What R3LIVE cannot take as it is, and what is done

R3LIVE was written for a Livox Avia and a pinhole camera. Four inputs differ on our rigs. None of them touches the algorithm.

| Upstream | Our data | Done |
|---|---|---|
| LiDAR: Livox messages, or the Ouster format (`lidar_type 3`). The Velodyne handler is an empty stub | Velodyne VLP-16 clouds | `vel_to_ouster.py` rewrites the cloud into the Ouster field layout (`t` in ns from the scan start, `range` in mm, `ring`, `reflectivity`). No coordinate changes, no point is added or dropped. R3LIVE's Ouster path then does what it does for an Ouster: no feature extraction, all points go on as surface points |
| Camera: pinhole with radial-tangential distortion | The SubT-MRS cameras are MEI (omnidirectional); GEODE's is pinhole | MEI images are rectified to a pinhole image of the same size and principal point by `../baselines/mei_rectify.py` (maths in `mei_model.py`, tested; focal length `mean(gamma)/(1+xi)`, the pixel scale of the image centre). GEODE goes in as it is, with its own intrinsics and k1, k2, p1, p2 |
| LiDAR-IMU offset: compiled constant of the authors' Avia, `(0.04165, 0.02326, -0.0284)` | Our own extrinsics | `r3live_rig.patch`: the constant becomes the parameter `r3live_lio/lidar_offset_to_imu`, default the upstream value. R3LIVE has no LiDAR-IMU rotation (frames are assumed aligned). Ours are 0.0 to 3 degrees off identity; the angle is printed in `params_changes.txt` and the rotation is not applied |
| Needs a display: the VIO thread opens an OpenCV window | Headless | `Xvfb` inside the container. Nothing is shown anywhere |

IMU: acceleration in m/s^2 is used as it is (`m_if_acc_mul_G = 0` upstream). No orientation is needed, so a bag without IMU orientation is applicable here (the shared preflight would flag it for LIO-SAM and LVI-SAM; the runner ignores that part of its verdict).

`r3_params.py` writes `r3live_config.yaml` from the upstream `config/r3live_config.yaml` and changes only:

| Keys | Why |
|---|---|
| `lidar_type: 3` | the Ouster path |
| `record_offline_map: 0` | no map file at the end (output only; the laptop disk is nearly full) |
| `image_width`, `image_height`, `camera_intrinsic`, `camera_dist_coeffs` | the camera R3LIVE sees (rectified pinhole, zero distortion, or GEODE's own) |
| `camera_ext_R`, `camera_ext_t` | camera-IMU extrinsic of the sequence (camera orientation in the IMU frame, same convention as the VINS-Mono extrinsic) |
| `lidar_offset_to_imu` (new key) | t of `laser_to_imu`, read by `r3live_rig.patch` |

Everything else stays at the upstream default, including `estimate_i2c_extrinsic: 1` and `estimate_intrinsic: 1` (R3LIVE refines the camera extrinsic and intrinsics online, so our values are starting values), `maximum_vio_tracked_pts: 600`, `lidar_time_delay` and the filter settings. `Lidar_front_end/N_SCANS` stays 6 (the Livox value); the Ouster path does not read it.

Launch: `inside.sh` writes `run.launch` with the two nodes and the topic parameters of upstream `r3live_bag.launch`, both `required="true"` as upstream. Left out: RViz. GEODE's compressed images are decompressed to a raw topic (same line as for LVI-SAM).

Scored output: the pose R3LIVE sends on `/tf` (`world` to `/aft_mapped`, the IMU pose after every LIO update), recorded by `record_tf.py` to `odom.tum`. It is the same pose as `/aft_mapped_to_init`, but the tf is stamped with the scan end time and the Odometry message with the clock at publication, which lags the scan by the processing time and would put a timing error into the score.

## Build notes

- `livox_ros_driver`: the two `.msg` files of upstream commit `3d240d5666129e1a3052e78ee8487a04b08fdda3` in a message-only package (`livox_msgs_*`), built first. The Livox driver and SDK are not built.
- Built targets: `r3live_LiDAR_front_end` and `r3live_mapping`. Not built: `r3live_meshing` (needs OpenMVS, not used) and the calibration tools. CGAL (`libcgal-dev`) is required by the configure step.
- No `-march` flag. r3live's CMake uses `-O3 -msse2 -msse3`, available on every x86-64 CPU here. `../baselines/check_isa.sh` fails on any AVX-512 instruction. The base is `ros@sha256:72b8bc59...` (the digest of the laptop's `ros:noetic`).
- Upstream warns that OpenCV at build and at run time must be the same version. Both are the image's OpenCV 4.2.

## Rule fixed before the first run (per-method failure rule, not yet agreed)

R3LIVE runs one LIO update per LiDAR scan (no throttle), so the documented rate is the scan rate. Proposal: a run is **failed** if a node died (both nodes are `required`, so one death stops the other), or fewer than 80% of the LiDAR scans produced a pose, or the maximum error exceeds 100 m. Scans are counted as the LiDAR messages of the bag. Not applicable if the preflight says so (no per-point time, no camera topic). Three runs per sequence. **Waiting for the owner's OK before the first scored run.**

## Desktop: build and smoke test (never scored)

```
cd ~/switchslam-project && git pull
docker build --network host -t r3live_stock fusion_v4/stock_r3live        # long, a few GB
docker run --rm -v ~/switchslam-project:/repo:ro r3live_stock bash /repo/fusion_v4/baselines/check_isa.sh /root/r3_ws/devel
SLICE=1 ./fusion_v4/stock_r3live/run_r3live.sh geode                       # 60 s of ~/slices/geode_70s.bag
SLICE=1 ./fusion_v4/stock_r3live/run_r3live.sh mf
```

## Laptop (scored runs)

```
cd ~/sw_new && git pull && cd fusion_v4
df -h ~                                                                   # check free space first
./baselines/load_image.sh r3live_stock                                    # or: --from ssh://user@desktop
SMOKE=1 ./stock_r3live/run_r3live.sh geode                                # 60 s check
for n in lc mf c02 cave02 geode; do REPEAT=3 ./stock_r3live/run_r3live.sh $n; done 2>&1 | tee ~/r3live_run123.log
```

Results go to `~/runs_r3live/<name>/run<k>/`: `odom.tum`, `r3live_config.yaml`, `params_changes.txt`, `r3live_commit.txt`, `r3live.log`, `crashes.txt`, `preflight.txt`, `adapter_used.txt`, `camera_used.txt`, `cloud_fields.txt`.

## Offline tests

`python3 test_stock_r3live.py` and `python3 test_run_r3live.py` (from this folder; numpy and pyyaml only), and `python3 ../baselines/test_rectify.py`. Set `R3LIVE_UPSTREAM=<clone at the pinned commit>` to also check the patch against the real source.
