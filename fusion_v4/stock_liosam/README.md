# Stock LIO-SAM on our bags

The original [LIO-SAM](https://github.com/TixiaoShan/LIO-SAM) (Shan et al., IROS 2020), built from its own repository at one pinned commit (`0be1fbe`, 17 Apr 2023) in a separate Docker image, and run on the same bags, ground truth and replay rates as the stock A-LOAM runs. It shares nothing with the `switchslam_gpu_v2` or `vinsmono_test` containers. It is one of the baselines in the Switch-SLAM table (LIO-SAM, LVI-SAM, R2LIVE, R3LIVE, FAST-LIVO).

**Status: written and tested offline only** (14 unit tests, plus a dry run of the host script with a stand-in `docker`). The image has not been built and no bag has been replayed yet; the first run on the laptop is the real test.

## What is changed from upstream

| What | Change | Why |
|---|---|---|
| `CMakeLists.txt` | `-std=c++11` to `-std=c++14` | PCL 1.10 on Ubuntu 20.04 needs C++14 |
| `include/utility.h` | `<opencv/cv.h>` replaced by `<opencv2/opencv.hpp>`, placed after the PCL includes | the old header does not exist in OpenCV 4; included before PCL's FLANN header it breaks the FLANN build (`unordered_map ... no member named serialize`) |
| `config/params.yaml` | six keys only: `pointCloudTopic`, `imuTopic`, `extrinsicRot`, `extrinsicRPY`, `extrinsicTrans`, `loopClosureEnableFlag: false` | topics and extrinsics of the sequence; no loop closure, as in the Switch-SLAM table |

Everything else in `params.yaml` (IMU noise, voxel sizes, thresholds, `N_SCAN 16`, `Horizon_SCAN 1800`) stays at the upstream default. The first two rows are the file `liosam_noetic_build.patch`, applied by the Dockerfile; no algorithm file is touched. `make_params.py` prints the changed keys of every run into `params_changes.txt`.

The extrinsics come from the `laser_to_imu` matrix of each sequence (the same file the fusion node uses). LIO-SAM's convention is `acc_lidar = extRot * acc_imu` and `q_lidar = q_imu * inverse(extRPY)`, so `extrinsicRot = extrinsicRPY = R^T` and `extrinsicTrans = -R^T t` (the IMU position in the LiDAR frame). A test checks this.

## What stock LIO-SAM needs, and what the preflight does

LIO-SAM only works with a 9-axis IMU (roll, pitch and yaw in `sensor_msgs/Imu.orientation`), needs a `ring` field and a per-point `time` (seconds from the scan start), and shuts down on a cloud with `is_dense == false`. Before any run, `preflight.py` reads the first bag and prints:

| Key | Meaning | If not ok |
|---|---|---|
| `ORIENTATION` | judged on the quaternion itself: unit norm, changing over time, gravity along +z. A driver flag `orientation_covariance[0] = -1` is reported but does not decide (LIO-SAM never reads the covariance), unless the quaternion also fails the gravity check | `missing` or `constant`: **not run**, `NOT_APPLICABLE.txt` says why |
| `RING` | `ring` field, uint16 | missing: not run |
| `TIME` | per-point time, float32, offsets from 0 | `negative` (relative to scan end, as in GEODE): the adapter shifts it; missing: not run |
| `DENSE` | `is_dense` flag and NaN points | `no`: the adapter drops NaN points and sets the flag |
| `ORIENT_GRAVITY_ERR_DEG` | angle between the world-frame acceleration of the first 200 samples and +z | information; above 15 deg prints a note |

`FORCE=1` runs a sequence although the preflight says not applicable; the run is then labelled `FORCED` and is not a stock result. `ADAPT=off` switches the adapter off. The adapter (`cloud_adapter.py`) changes the container of the data only: it removes non-finite points and shifts negative per-point time to start at 0 (moving the header stamp by the same amount). No coordinate changes. Which of the two was used is written to `adapter_used.txt`.

For the two sequences recorded as `velodyne_packets` (Multi Floor, Long Corridor) the packets are converted inside the container with `velodyne_pointcloud` and `model: VLP16`, so `ring` and `time` exist (same ranges 0.4 to 130 m as the rest of the project). The first converted cloud's field list is saved as `cloud_fields.txt` to confirm.

## Run

```
cd ~/switchslam-project/fusion_v4            # a clone of this repository
docker build --network host -t liosam_stock stock_liosam     # first time only, about 20 to 40 min (builds LIO-SAM; GTSAM from the PPA, or from source if the PPA has no package)
REPEAT=1 ./stock_liosam/run_liosam.sh geode   # shortest sequence first
```
Sequences: `mf`, `lc`, `c02`, `cave02`, `geode` (settings in `seq/<name>.env`; bag folders and ground truth default to the paths used by the other runs, override with `BAGS_ROOT=`, `BAG_DIR=`, `GT=`). Replay rates are those of the stock A-LOAM runs (1.0, 1.0, 0.33, 0.5, 0.5); LIO-SAM runs on the bag clock, so a slow replay does not change its input. `REPEAT=3` makes three runs (`RUN_START=2 REPEAT=2` adds runs 2 and 3 later). Results go to `~/runs_liosam/<name>/run<k>/`:

| File | Content |
|---|---|
| `odom.tum` | `/lio_sam/mapping/odometry` (scan-to-map pose, the counterpart of A-LOAM's `aft_`), header stamps |
| `params.yaml`, `params_changes.txt`, `liosam_commit.txt` | the exact parameters and source commit of the run |
| `liosam.log`, `crashes.txt` | node output; number of respawns (a respawn restarts the map, so a run with one is reported as a failure) |
| `preflight.txt`, `adapter_used.txt`, `cloud_fields.txt` | what the bag provides and what was done to it |

Two guards from `../baselines/common.sh` run before anything else. If `BAGS_ROOT` is unset, the runner looks for `laptop_bags` on a mounted drive under `/media/$USER` ("One Touch2", then "One Touch1", then any other), and it refuses to start unless the bag folder sits on a mounted drive (`mountpoint -q` on a parent other than `/`). An unplugged drive would otherwise give the container an empty folder made by `docker -v`. `ALLOW_LOCAL_BAGS=1` accepts bags on the internal disk. The preflight and every run hold `flock ~/.replay.lock` (the same file the F35 runner locks), so a second replay started from another terminal waits and prints that it is waiting.

The score is full-span ATE RMSE and max, Umeyama SE(3) without scale, from the same loader and alignment as the other runs (`score_tum.py`; the host script prints it).

## Rules fixed before the first run (change them before running, not after)

1. Every run is reported with its number; none is dropped or re-run because of its value.
2. A run is labelled **failed** if the node respawned at least once, or fewer than half of the scans produced a pose, or the maximum error exceeds 100 m (the GEODE benchmark's rule; Switch-SLAM gives none).
3. A sequence where the preflight says not applicable is reported as "not applicable, reason", not as a failure score.
4. Three runs per sequence; one run supports no claim.

## Offline tests

`python3 test_stock_liosam.py` (from this folder; numpy and pyyaml only). Covers the extrinsic convention, that untouched keys survive, the cloud report and adapter (coordinates unchanged), the IMU orientation check and the scorer.
