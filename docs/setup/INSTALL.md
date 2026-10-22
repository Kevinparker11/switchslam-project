# Installing the environment on a new PC

The whole study runs on one Linux machine with Docker. Two long-lived containers hold the ROS stacks, a third (stock `ros:noetic`) plays the bags. The fusion node, scoring and back end are plain Python.

> **Status (22 Oct 2026).** The two containers were built interactively on the original laptop and no Dockerfile was kept. The environment was therefore **captured from the working machine** (versions, source revisions, local modifications; see [ENVIRONMENT.md](ENVIRONMENT.md)). Two routes exist: **2A move the containers** (guaranteed identical, large) or **2B rebuild from source** with the pinned revisions and the captured diffs (small, but not yet verified end to end on a clean machine).

## 1. Host requirements

| Item | Needed for | Note |
|---|---|---|
| Linux (Ubuntu), Docker | everything | the original machine: Ubuntu laptop, Docker with the default bridge plus a user bridge `vins_bridge` |
| ~60 GB free disk | runs | one A-LOAM run writes ~3 GB of node output before cleanup; keyframes ~10-20 MB per run; bags are 4-23 GB each |
| Python 3 + `pip install -r requirements.txt` | scoring, replay, back end, stats | numpy, scipy, pandas, matplotlib, scikit-learn, pyyaml, gtsam |
| ~16 GB RAM, 4+ cores | GenZ-LIO + VINS-Mono + A-LOAM at once | the studies replay slowly (0.33x-0.5x) for this reason |
| Bags on an external drive | all sequences | expected at `/media/$USER/One Touch1/laptop_bags/<sequence>/` (override with `BAGS_ROOT=...`) |

Directory layout the scripts assume on the host:

```
~/switchslam_channelT/fusion_v4/      <- copy of this repo's fusion_v4/ (self-contained run folder)
~/runs_*                              <- outputs (logs, keyframes, results_index.csv); created by the scripts
<BAGS_ROOT>/multifloor, Corridor02, Cave, Long_Corridor_Rosbag, GEODE      <- bags + ground truth (see DATASETS.md)
```

## 2. The containers

| Container | Base | Holds | Used for |
|---|---|---|---|
| `switchslam_gpu_v2` | ROS **Noetic** | `/root/catkin_ws` with **A-LOAM** (patched), `velodyne_pointcloud`, `/root/genz_ws` with **GenZ-LIO**, `/root/thr` (working copy of our Python) | roscore, LiDAR front end, `fusion_node_v2`, `keyframe_recorder`, `lio_bridge` |
| `vinsmono_test` | ROS **Kinetic** | `/root/catkin_ws/src/VINS-Mono` (patched) | `feature_tracker`, `vins_estimator` |
| `ros:noetic` (stock, started per run) | ROS Noetic | nothing | `rosbag play --clock` with the bag folder mounted at `/bags` |

Both long-lived containers join the user-defined Docker network **`vins_bridge`** so that ROS 1 can span them (the run script reads each container's IP on that network and sets `ROS_IP` / `ROS_MASTER_URI=http://<gpu-ip>:11311`).

### 2A. Recommended: move the containers from the working laptop
The A-LOAM and VINS-Mono workspaces are **bind mounts from the host** (`~/catkin_ws_rebuild` and `~/catkin_ws_mono`), so an image alone does not contain them. The two helper scripts handle both parts:
```bash
# on the working laptop (stops the containers for a minute; output several GB)
bash tools/export_images.sh ~/switchslam_export
# copy ~/switchslam_export to the new PC, then there:
bash tools/import_images.sh ~/switchslam_export
```
`import_images.sh` loads the images, creates the network `vins_bridge`, unpacks the two workspaces under `$HOME` and starts the containers with the same network, mounts and display settings as the original (reconstructed from `docker inspect`, see ENVIRONMENT.md). The snapshots `*:baseline-2026-10-09` on the laptop pre-date GenZ-LIO and GEODE; do not use them for fusion_v4.

### 2B. Rebuild from source
Revisions and local changes are recorded in [ENVIRONMENT.md](ENVIRONMENT.md). The two diffs were checked to apply cleanly to fresh upstream checkouts at these revisions; the full build and a run on a clean machine have not been repeated. If a step fails, 2A is the fallback.

```bash
docker network create vins_bridge
mkdir -p ~/catkin_ws_rebuild/src ~/catkin_ws_mono/src
```

**Noetic container (`switchslam_gpu_v2`, Ubuntu 20.04)**
1. `docker run -dit --name switchslam_gpu_v2 --network vins_bridge -v ~/catkin_ws_rebuild:/root/catkin_ws osrf/ros:noetic-desktop-full bash`, then inside: `apt-get update && apt-get install -y ros-noetic-velodyne-pointcloud ros-noetic-velodyne ros-noetic-pcl-ros ros-noetic-pcl-conversions ros-noetic-compressed-image-transport ros-noetic-image-transport-plugins libceres-dev python3-numpy python3-scipy python3-pandas python3-yaml python3-matplotlib` (the original also has Ceres 1.14.0 built from source in `/root`; the packaged Ceres is the first thing to try).
2. A-LOAM: `git clone https://github.com/HKUST-Aerial-Robotics/A-LOAM /root/catkin_ws/src/A-LOAM && cd /root/catkin_ws/src/A-LOAM && git checkout e51f88c && git apply /path/to/patches/aloam_vins/captured_diffs/A-LOAM_e51f88c_local_changes.diff`, then `cd /root/catkin_ws && catkin_make`.
3. GenZ-LIO: `bash fusion_v4/genz/install_genz.sh` (section 4).
4. `mkdir -p /root/thr` and copy the sequence files (section 5).

**Kinetic container (`vinsmono_test`, Ubuntu 16.04)**
1. `docker run -dit --name vinsmono_test --network vins_bridge -v ~/catkin_ws_mono:/root/catkin_ws osrf/ros:kinetic-desktop-full bash`; inside: `apt-get install -y ros-kinetic-compressed-image-transport ros-kinetic-image-transport-plugins` and Ceres 1.14.0 built from source (VINS-Mono needs it).
2. VINS-Mono: `git clone https://github.com/HKUST-Aerial-Robotics/VINS-Mono /root/catkin_ws/src/VINS-Mono && cd /root/catkin_ws/src/VINS-Mono && git checkout 90dabb5 && git apply /path/to/patches/aloam_vins/captured_diffs/VINS-Mono_90dabb5_local_changes.diff`, then `cd /root/catkin_ws && catkin_make`.
3. `mkdir -p /root/thr`.

## 3. Patches to third-party code (`patches/aloam_vins/`)

| File | Target | Purpose |
|---|---|---|
| `patch_hessian.py` | A-LOAM `src/laserOdometry.cpp` | extracts the Gauss-Newton Hessian after `ceres::Solve` and publishes it on `/laser_hessian` (`Float64MultiArray`) |
| `patch_odom_buffer.py`, `patch_timestamp_tolerance.py` | A-LOAM `src/laserMapping.cpp` | buffer fix and timestamp tolerance so the feedback loop (fused pose back into A-LOAM) does not stall |
| `laserMapping.cpp` | reference copy | the patched A-LOAM `laserMapping.cpp` kept from generation 1; superseded by the captured diff |
| `patch_vinsmono_hessian.py` | VINS-Mono `vins_estimator/src/estimator.cpp` | publishes the VINS-Mono Hessian (used by the generation-1 switching node) |
| `patch_vins_hessian.py` | VINS-Fusion (noetic, OpenCV4) `estimator.cpp` | the same patch for a VINS-Fusion tree; not used by the fusion_v2/v3/v4 studies |
| `fusion_v3/patch_mapping_hessian.py` | A-LOAM `src/laserMapping.cpp` | optional scan-to-map Hessian on `/mapping_hessian`, used only by the unused M0/M1 configs |

Each script asserts that its anchor text exists and edits the file in place (paths are container paths such as `/root/catkin_ws/src/A-LOAM/src/laserOdometry.cpp`); copy it into the container, run it there with `python3`, then rebuild with `catkin_make`. The **exact state of the original machine** is the pair of diffs in `patches/aloam_vins/captured_diffs/` (A-LOAM at `e51f88c`, VINS-Mono at `90dabb5`), made with `git diff` on the working containers. They are authoritative: `git apply` them on a fresh checkout instead of running the scripts (the scripts are how the changes were first made).

## 4. GenZ-LIO (front end of fusion_v4)

```bash
bash ~/switchslam_channelT/fusion_v4/genz/install_genz.sh 2>&1 | tee ~/install_genz.log     # 10-20 min
```
It clones `cocel-postech/genz-lio` on the host at the pinned commit **bf444f7a747ed3da8548b56b49c14f207e8d49bb**, copies it into the container at `/root/genz_ws/src/genz-lio`, applies `genz/patch_genz_information.py` (exports the LiDAR information matrix; no other change), installs missing dependencies and builds with `catkin_make -j2 -DCMAKE_BUILD_TYPE=Release`. It prints `GENZ_INSTALL_DONE` on success.

Known issue: GenZ-LIO's CMake downloads Eigen 3.4 from gitlab, which is blocked inside the container. Download Eigen 3.4.0 on the host, copy it into the container and install it to `/usr/local` (`cmake .. && make install`) before building.

## 5. Per-sequence files that must exist inside the containers

Everything below is in [`configs/`](../../configs/) (copied from the working containers on 22 Oct 2026). `run_fusion_study.sh` reads `seq.env` (templates in `configs/seq_env_examples/`; the paths inside are those of the original laptop and must be adapted) and expects these inside the containers:

| Sequence | Into `switchslam_gpu_v2:/root/` | Into `vinsmono_test:/root/catkin_ws/src/VINS-Mono/config/` | Into `switchslam_gpu_v2:/root/thr/` |
|---|---|---|---|
| Multi Floor | `multifloor_aloam.launch`, `multifloor_velodyne_convert.launch` | `multifloor_config.yaml` | - |
| Long Corridor | `corridor_aloam.launch`, `corridor_velodyne_convert.launch` | `corridor_config.yaml` | `corridor_extrinsics.yaml` |
| Corridor02 | `corridor2_aloam.launch` | `corridor2_config.yaml` | `corridor2_extrinsics.yaml` |
| Cave02 | `cave02_aloam.launch` | `cave02_config.yaml` | `cave02_extrinsics.yaml` |
| GEODE alpha | `geode_aloam.launch` | `fusion_v4/geode/geode_config.yaml` | `fusion_v4/geode/geode_extrinsics.yaml` |

```bash
# example: Multi Floor
docker cp configs/multifloor/multifloor_aloam.launch            switchslam_gpu_v2:/root/
docker cp configs/multifloor/multifloor_velodyne_convert.launch switchslam_gpu_v2:/root/
docker cp configs/multifloor/multifloor_config.yaml             vinsmono_test:/root/catkin_ws/src/VINS-Mono/config/
```
`fusion_v4/setup_sequence.sh` (SubT-MRS) and `fusion_v4/geode/setup_geode.sh` (GEODE) do this copying and write `seq.env` for you. The frozen GenZ-LIO configuration is generated by `fusion_v4/genz/make_genz_config.py`; the generated file from the working machine is `configs/genz/genz_frozen.yaml`. The Python files in `/root/thr` are copied by `run_fusion_study.sh` itself before each run (they match the repository byte for byte as of 22 Oct 2026, except `threshold_study/switching_node_mf_thr.py`, added from the container).

## 6. Re-capturing the environment (only after changing the setup)

```bash
bash tools/capture_environment.sh            # -> ~/switchslam_environment.txt and ~/switchslam_environment_files.tgz
```
The capture of 22 Oct 2026 is stored as [environment_capture_2026-10-22.txt](environment_capture_2026-10-22.txt) and summarised in [ENVIRONMENT.md](ENVIRONMENT.md).

## 7. Smoke test of a fresh install

```bash
cd ~/switchslam_channelT/fusion_v4
SMOKE=1 FRONT=aloam ./run_fusion_study.sh F8         # 70 s on Multi Floor; expect VINS-Mono from ~20 s and FUSED from ~40 s
SMOKE=1 SMOKE_SECS=120 FRONT=genz ./run_fusion_study.sh G0    # GenZ-LIO + bridge
```
A healthy run writes `~/runs_v2*/switching_log_v2_SMOKE_*.csv` with several hundred rows.
