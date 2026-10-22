# Datasets, ground truth and where the scripts expect them

All test bags live on one external drive, under a single root: `/media/$USER/One Touch1/laptop_bags/` (note the space in the drive name; every path must be quoted). Change it with `BAGS_ROOT=...`. Bags and ground truth are **not** stored in this repository.

## Folder layout expected under `BAGS_ROOT`

| Sequence | Folder | Bag(s) | Ground truth (TUM `t x y z qx qy qz qw`, or csv for Multi Floor) | Role |
|---|---|---|---|---|
| Multi Floor (SubT-MRS, legged robot, ~270 m) | `multifloor/` (also `RosBag/`) | `multifloor_0.bag`, `multifloor_1.bag`, `multifloor_2.bag` | `SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv` (default `~/Downloads/...`; override `MULTIFLOOR_GT=`) | tuning sequence |
| Long Corridor (SubT-MRS Corridor01, wheeled RC) | `Long_Corridor_Rosbag/` | `raw_data_core_2023-07-25-03-01-44.bag` (6.4 GB) | `corridor01_gt.txt` (from `SubT_MRS_Hawkins_Long_Corridor_RC`) | SAH development |
| Corridor02 (SuperLoc Hawkins, RC, 893 s) | `Corridor02/` | `corridor02.bag` | `corridor02_gt.txt` | SAH development; held-out for F8 |
| Cave02 (SuperLoc Laurel Cavern, handheld, 986 s) | `Cave/cave02_bag/` | `cave02.bag` | `Cave/cave02_gt.txt` | clean control, never used for design |
| GEODE stairs, device alpha | `GEODE/` | `stairs_alpha.bag` (3.8 GB) | `GEODE/stairs_alpha.txt` (TUM, 3447 poses, 344.6 s) | untouched test set |

Sequences with their own `seq.env` (written by `setup_sequence.sh` / `geode/setup_geode.sh`, stored in `~/runs_<name>/`): `BAG_DIR`, `GT`, container paths of the VINS-Mono config and A-LOAM launch, `OUT_DIR`, `MIN_ROWS`, scorer, extrinsics. Examples: `configs/templates/seq.cave02.env.example`.

## Where to download

- **SubT-MRS / SuperLoc sequences (Multi Floor = Floor01, Corridor01, Corridor02, Cave01-04):** the SuperLoc page lists each sequence with Drive links for the bag, extrinsics, intrinsics, GT map and GT trajectory (TUM format): <https://superodometry.com/superloc>. The Multi Floor sequence of the ICCV'23 SubT-MRS challenge matches SuperLoc Floor01 (SP1, 480 s); no source states outright that they are the same recording. Details, sizes, folder IDs and caveats: [`docs/research/research_gaps/dataset_access.md`](../research/research_gaps/dataset_access.md).
- **GEODE** (<https://thisparticle.github.io/geode/>, paper <https://arxiv.org/abs/2409.04961>, repo `PengYu-Team/GEODE_dataset`): Google Drive <https://drive.google.com/drive/folders/1hEn3sBAvQhSdUFnGMZCCv-W0Ynj2rWBs> or Baidu Netdisk <https://pan.baidu.com/s/19t2WhhUvNnNqKX0zLDhRIA> (code `sysu`). ROS 1 bags. Device alpha = Velodyne VLP-16 + HikRobot stereo camera + Xsens MTi-30 IMU; calibration in `alpha_config.yaml`. The stair ground truth was made by map alignment (PALoc).

## Sensor topics

| Sequence | LiDAR | IMU | Camera |
|---|---|---|---|
| Multi Floor | `/cmu_sp1/velodyne_packets`, converted to `/multifloor/velodyne_points` by `configs/multifloor/multifloor_velodyne_convert.launch` | `/cmu_sp1/imu/data` | `/cmu_sp1/camera_1/image_raw` |
| Corridor02, Cave02, Long Corridor | see the generated `seq.env` / `rosbag_info.txt` of each `~/runs_<name>/` (topic names differ per robot) | | |
| GEODE alpha | `/velodyne_points` (PointCloud2 with `ring` and per-point `time`, times negative = relative to scan end) | `/imu/data` (~100 Hz) | `/left_camera/compressed`, `/right_camera/compressed` (JPEG, 1224x1024, 10 Hz; no raw images, so `geode/` republishes) |

GenZ-LIO needs a per-point time field. If a bag only has `velodyne_packets`, the conversion launch must set the `model` parameter (`VLP16`) of `velodyne_pointcloud`; `run_fusion_study.sh` does this for the GenZ stack. Check any new bag with `fusion_v4/genz/check_bag_fields.sh <folder>` (fast, stdlib only).

## Ground-truth clock
The scorers compare on the clock of the messages' header stamps (not the bag record times). `setup_sequence.sh` checks the overlap of ground truth and bag; if there is none, use `align_gt_time.py`. For GEODE the clocks agree (log start 1705542303.3 vs GT start ...304.1).

## Metric
ATE RMSE, Umeyama SE(3) alignment, no scale, full span of the run (`fusion_v4/score_run.py`, `fusion_summary.py`, `multifloor_ate_eval.py` for Multi Floor). Differences under about 0.1-0.3 m are treated as ties.
