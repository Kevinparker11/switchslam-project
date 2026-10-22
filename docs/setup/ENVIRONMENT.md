# Environment of the original machine (captured 22 Oct 2026)

Raw output of `tools/capture_environment.sh`: [environment_capture_2026-10-22.txt](environment_capture_2026-10-22.txt). The small files that exist only on that laptop (generated configs, launch files, `seq.env`, local source modifications) are committed under [`configs/`](../../configs/) and [`patches/aloam_vins/captured_diffs/`](../../patches/aloam_vins/captured_diffs/). This page is the summary.

## Host
| Item | Value |
|---|---|
| OS | Ubuntu 22.04.5 LTS, kernel 6.8 |
| Docker | client and server 29.1.3 |
| GPU | NVIDIA GeForce GTX 1650, driver 595.99 (the pipeline itself is CPU-bound; the GPU is only passed through) |
| Python | 3.10.12: numpy 2.2.6, scipy 1.15.3, pandas 2.3.3, scikit-learn 1.7.2, matplotlib 3.10.8, PyYAML 5.4.1, gtsam (version not recorded). The host has no `rosbag` module: bags are read inside containers |

## Containers
Both containers sit on the user-defined bridge `vins_bridge` (created 8 Sep 2026; Docker assigned subnet 172.17.0.0/16, the scripts read the container IPs at run time and never hard-code them).

| | `switchslam_gpu_v2` | `vinsmono_test` |
|---|---|---|
| Image | `switchslam_working_v2` (a hand-modified image; the layer history only shows the stock `ros:noetic` build) | `osrf/ros:kinetic-desktop-full` (unmodified image; all changes are in the container and the bind mount) |
| OS / ROS | Ubuntu 20.04.6, ROS Noetic | Ubuntu 16.04.7, ROS Kinetic |
| Compiler / CMake / Python | gcc 9.4.0, CMake 3.16.3, Python 3.8.10 | gcc 5.4.0, CMake 3.5.1, Python 2.7.12 and 3.5.2 (no OpenCV Python bindings) |
| Bind mount | host `/home/kavinkumar/catkin_ws_rebuild` -> `/root/catkin_ws` | host `/home/kavinkumar/catkin_ws_mono` -> `/root/catkin_ws` |
| Other mounts / env | `/tmp/.X11-unix`, `DISPLAY=:1`, `NVIDIA_VISIBLE_DEVICES=all`, `NVIDIA_DRIVER_CAPABILITIES=all` | `/tmp/.X11-unix`, `DISPLAY=:1` |
| In the container's own filesystem | `/root/genz_ws` (GenZ-LIO), `/root/eigen34` (Eigen 3.4 source, installed to `/usr/local`), `/root/ceres-solver-1.14.0`, `/root/thr` (our Python), `/root/*.launch` | `/root/ceres-solver-1.14.0`, `/root/thr`, `/root/vins_output*` |
| Workspaces (`catkin`) | `/root/catkin_ws` (A-LOAM, `cpr_gazebo`), `/root/genz_ws` | `/root/catkin_ws` (VINS-Mono) |

**Important:** the two `catkin_ws` folders are *bind mounts from the host*, not part of the container image. `docker commit` / `docker save` therefore does **not** contain A-LOAM or VINS-Mono. Either archive those two host folders as well (`tools/export_images.sh` does this) or rebuild them from source with the captured diffs (INSTALL.md, section 2B).

### Third-party sources
| Source | Revision | Local changes |
|---|---|---|
| `HKUST-Aerial-Robotics/A-LOAM` | `e51f88c` | 6 files modified: [`A-LOAM_e51f88c_local_changes.diff`](../../patches/aloam_vins/captured_diffs/A-LOAM_e51f88c_local_changes.diff) (C++14, Hessian publisher `/laser_hessian`, odometry-buffer cap and 20 ms timestamp tolerance in the mapper, mapper reads the fused pose via `/switch_fused_pose`, OpenCV 4 include, `kittiHelper` disabled; the rviz layout change is left out) |
| `HKUST-Aerial-Robotics/VINS-Mono` | `90dabb5` | [`VINS-Mono_90dabb5_local_changes.diff`](../../patches/aloam_vins/captured_diffs/VINS-Mono_90dabb5_local_changes.diff) (visual Hessian published on `/vins_mono_hessian`; a debug `printf` in `feature_tracker_node.cpp`). Generated per-sequence configs are in `configs/` |
| `cocel-postech/genz-lio` | `bf444f7a747ed3da8548b56b49c14f207e8d49bb` | `genz/patch_genz_information.py` (information matrix export), see INSTALL.md section 4 |
| Eigen | 3.4.0 in `/usr/local` (system package stays 3.3.7) | built from the 3.4.0 source for GenZ-LIO |
| Ceres | 1.14.0 built from source (both containers) | none |
| `clearpathrobotics/cpr_gazebo` | `509afbe` | only used by the generation-1 simulation study |

### Libraries (apt)
Noetic container: PCL 1.10.0, OpenCV 4.2.0, Eigen 3.3.7 (system), glog 0.4.0, ROS `velodyne*` 1.7.0, `compressed_image_transport` 1.15.0, `cv_bridge` 1.16.2.
Kinetic container: PCL 1.7.2, OpenCV 2.4.9.1, Eigen 3.3~beta1, glog 0.3.4, `compressed_image_transport` 1.9.5.
Python inside the Noetic container: numpy 1.24.4, scipy 1.10.1, PyYAML 5.3.1, matplotlib 3.1.2 (the fusion node runs here).

## Images present on the laptop on 22 Oct 2026
`switchslam_gpu_v2:baseline-2026-10-09` and `vinsmono_test:baseline-2026-10-09` are snapshots of the master system from **9 Oct, before GenZ-LIO and GEODE were added**; they do not contain the fusion_v4 work. Use a fresh `docker commit` of the current containers (INSTALL.md section 2A) to transport the full state.

## Not recorded
`docker run` flags are reconstructed from `docker inspect` (INSTALL.md, section 2A); the GPU runtime flag was not captured (`NVIDIA_VISIBLE_DEVICES=all` implies `--gpus all`, which the pipeline does not need). The gtsam version and the exact OpenCV/Ceres build options were not recorded.
