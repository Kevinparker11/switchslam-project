# Test datasets: what to run, where to get it, and how far to trust the ground truth

*14 October 2026. Every file name and link below was opened on the source page or Google Drive on this date, unless it is marked "unverified".*

**Bottom line.**
- **`handheld_underground00.bag` is not the Long Corridor bag and is not a DCReg bag.** It is a FusionPortableV2 sequence: handheld, in an underground car park, labelled "Structureless". It can serve as a later extra test.
- **Long Corridor ground truth is available, from two separate places.** The bag is SuperLoc's "Corridor01". Its zip has the same name as your empty folder.
- **Use our method where LiDAR-only and LiDAR-centred LiDAR–camera methods fail**, and keep the honest controls:
  1. SubT-MRS Long Corridor (required).
  2. A second SubT-MRS corridor (Corridor02).
  3. SubT-MRS BlockLiDAR.
  4. GEODE α sequences where every published method fails.
  5. FusionPortableV2 underground (independent ground truth).

---

## 1. Your bag: `handheld_underground00`

| Item | Value | Source |
|---|---|---|
| Dataset | FusionPortableV2 (Wei et al., IJRR 2024) | [FPv2 data page](https://fusionportable.github.io/dataset/fusionportable_v2_data/) |
| Platform / place | Handheld, underground car park, labelled "Structureless" | same |
| Length | 380 s, 403 m, mean/max speed 1.07 / 3.38 m/s | [FPv2 paper, Table 4](https://arxiv.org/html/2404.08563) |
| Sensors | Ouster OS1-128 at 10 Hz; stereo FLIR BFS (global shutter, 1024×768, 20 Hz); stereo DAVIS346; STIM300 IMU at 200 Hz | same |
| Ground-truth pose | **3-DoF position from a Leica MS60 total station** tracking a prism (paper cites 1 mm), resampled to 20 Hz | same |
| Ground-truth map | Yes: Leica RTC360/BLK360, "Underground Parking" | same |
| Published SLAM results on it | **None.** The paper benchmarks 8 other sequences only. | same |
| Download | [FPv2 Google Drive](https://drive.google.com/drive/folders/1PYhnf3PlY5r0hbyzWDGTUTPxRMl6SYa-?usp=sharing) · [calibration](https://github.com/fusionportable/calibration_files) (handheld set 20230403; the site's link points to the 20230426 folder, so check) | same |

DCReg did use FusionPortable, but its "Corridor" and "Building" (OS128, 572 s) match FusionPortable **v1** `20220216_corridor_day` and `20220225_building_day`, not this bag. DCReg's Table 2 lists FP Corridor/Building, GEODE Stairs, its own MS Parking Lot, and SubT-MRS Cave01/02/04.

**Value to us.** Its ground truth is the only independent kind on this list: a total station, not map-aided fusion. It has a good camera for VINS-Mono and a structureless scene.

**Costs.**
- We would have to run every baseline ourselves.
- A-LOAM only supports 16/32/64 rings, so the 128-ring cloud must be thinned to 64.
- Only position error can be scored.

---

## 2. Long Corridor: bag, ground truth, calibration (direct links)

Each Drive file name below was confirmed on this date by opening its link.

| What | File name (confirmed) | Link |
|---|---|---|
| Bag (zip) | `SubT_MRS_Hawkins_Long_Corridor_RC.zip` | https://drive.google.com/file/d/1aIIqPiE10nX3IhidpxKhc4Psq-AMER1X/view |
| Ground truth, SuperLoc release (TUM: `t x y z qx qy qz qw`) | `corridor01_gt.txt` | https://drive.google.com/file/d/1QbQamSktPAzJkf0GduAPTqQlxuxM0DBK/view |
| Ground truth, ICCV'23 challenge release (folder) | folder "Multi-Modal-Sensor-Fusion-Track" | https://drive.google.com/drive/folders/1bSGDe1FFQYEjs20P8L15pTx7T0HCn2L0 |
| Ground truth, challenge page's second link (folder) | folder "Groundtruth_Trajectory" | https://drive.google.com/drive/folders/1el51myR4Zzmxz6Tq2lq660zUVQSH9PoQ |
| Extrinsics | `SubT_MRS_Hawkins_Long_Corridor_RC_Extrinsics.yaml` | https://drive.google.com/file/d/1bB3jfEJeTf_XoLUHKOaxCNF_MCkiQTol/view |
| Intrinsics | `SubT_MRS_Hawkins_Long_Corridor_RC_Intrinsics.yaml` | https://drive.google.com/file/d/10rv5dg5un7kUveTPS3XBx8IuIYGg9r2h/view |
| GT map (FARO, for map-based checks) | not opened | https://drive.google.com/file/d/1EH4NzINNLkHrneIxstrzkY9XTZ1JP5bf/view |

The same check confirmed Multi Floor. SuperLoc "Floor01" is `SubT_MRS_Hawkins_Multi_Floor_LegRobot.zip`, and its GT is `floor01_gt.txt` (https://drive.google.com/file/d/1T-p9TgDwD_9us7U94cT0guwPNTvx3KkI/view).

**Facts.**
- The challenge page states: *"we have open-sourced our Ground Truth Trajectory data"* ([ICCV'23 sensor-fusion track](https://superodometry.com/iccv23_challenge_Mul)).
- That page lists Long_Corridor as RC2, Hawkins, 295 s, 616.45 m. The SuperLoc page lists Corridor01 as RC2, 279 s, 617 m.
- Our earlier bag span (1690254112–1690254392) is 280 s.

**How far to trust the ground truth.**
- SubT-MRS trajectories are made by fusing scan-to-map matching against a FARO-scanned map (±2 mm ranging) with the platform's own visual, LiDAR and IMU odometry ([SubT-MRS paper](https://arxiv.org/html/2307.07607v5)).
- They are therefore **not independent of the sensors we evaluate**, and they are weakest exactly where LiDAR degenerates.
- The CVPR supplemental quotes "within 10 cm".
- SuperLoc notes low Z confidence on Floor01.

**Treat differences under about 0.1 m between methods as ties.**

**Trust check (new script `compare_gt.py`).** It aligns two GT files in time and SE(3) and reports how far apart they are.
- `python3 compare_gt.py ~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv floor01_gt.txt`
- Then the same for `corridor01_gt.txt` against the challenge Long_Corridor file.
- Verdicts: "identical" (the same file re-exported), "cm level", "~decimetre" (quote it as GT uncertainty), or "DISAGREE".

---

## 3. Datasets used in the papers we hold

| Paper | Datasets | Public? | Our use |
|---|---|---|---|
| **Switch-SLAM** (RA-L 2024) | Gazebo Fast Rotate, Plane, Farm (not released); LVI-SAM "Handheld"; CERBERUS ANYmal 1–4 (LiDAR FOV cut to 180°); **SubT-MRS Multi Floor and Long Corridor**. No loop closure, 3-run mean, translational ATE. | SubT-MRS yes. CERBERUS: no download link found (ETH record has none). Gazebo worlds: not released. | Multi Floor done; **Long Corridor next**. Its Table II is an image in our copy; only MF 1.61/3.63 and LC 2.42/5.09 are known. |
| **DCReg** (IJRR 2026) | FusionPortable v1 Corridor/Building (OS128), GEODE Stairs (OS64), MS Parking Lot (Pandar32, self-collected), SubT-MRS Cave01/02/04 (VLP16), simulated cylinder | All public (MS via PALoc links) | LiDAR-registration benchmark (cm-level ATE with range limits). Different task from ours; use only to show the Schur-detection side. |
| **LP-ICP** (arXiv 2501.02580) | CERBERUS ANYmal 1–4; SubT-MRS Long Corridor | as above | Long Corridor ATE RMSE: LIO-SAM+LP-ICP 11.92 m, +Xn-ICP 19.63, +Zhang 24.71 |
| **LiDAR-inertial SLAM with QR codes** (Sci. Rep. 2026) | Own corridor recordings, 2D LiDAR + wheel + AprilTags | No | Not usable |
| **Thesis review slides (CB_EN)** | Multi Floor; Gazebo farm/plane/fast-route | | Slide says Multi Floor is "an underground mine". **It is CMU's Hawkins building**, so correct this. |

---

## 4. Ranked test plan

Our method's strength is that VINS-Mono remains the primary source, with soft, information-weighted LiDAR correction plus LiDAR loop closure. It should therefore stay alive where LiDAR geometry collapses or LiDAR is blocked, while LiDAR-centred methods (A-LOAM, LIO-SAM, FAST-LIO2, LVI-SAM, R3LIVE) drift or break. Its weakness is the mirror image: where vision fails (dark, smoke, blocked camera) it relies on the LiDAR warm-up path. **Report both sides.**

### Tier 1: required (same sensors and pipeline as Multi Floor, published numbers exist)

**T1. SubT-MRS Long Corridor (= Corridor01).** Run F0 and F8 ×3 with keyframes, C_T fixed at 0.03, and 1 loop-search round. Both settings were chosen on Multi Floor and are disclosed.

Numbers to beat (ATE RMSE, m):

| Group | Method | ATE RMSE (m) |
|---|---|---|
| With back end, ICCV'23 challenge | Weitong et al. | 1.254 |
| | Liu et al. | 1.454 |
| | Kim et al. | 2.100 |
| | Yibin et al. | 2.990 |
| LiDAR-camera, no loop closure | Switch-SLAM | 2.42 (max 5.09) |
| LiDAR / LIO odometry | LODESTAR (threshold grid-searched on this sequence) | 1.386 |
| | GenZ-ICP | 1.982 |
| | DLIO | 2.294 |
| | LIO-SAM | 2.959 |
| | KISS-ICP | 3.028 |
| | FAST-LIO2 | 3.113 |
| | iG-LIO | 3.136 |
| | AdaLIO | 3.160 |
| | LIO-SAM + LP-ICP | 11.92 |

Sources: challenge results from the [SubT-MRS paper](https://arxiv.org/html/2307.07607v5); LODESTAR Table V and earlier project notes; LP-ICP from [arXiv 2501.02580](https://arxiv.org/pdf/2501.02580).

Calibration: new VINS config from the RC2 intrinsics/extrinsics yamls, plus the velodyne-conversion and A-LOAM launch files copied with RC topics.

Open risk: 616 m in about 295 s, a mostly one-way run, may have few revisits, so loop closure may add little.

**T2. Multi Floor ground-truth cross-check** (no new runs). Use `compare_gt.py` with `floor01_gt.txt` against our `ground_truth_path.csv`. This turns "GT is trustworthy" from an assumption into a measured number.

### Tier 2: "they fail, we survive" (same sensor class)

**T3. SubT-MRS Corridor02.**
- RC1, Hawkins, 893 s, 690 m.
- Bag `corridor02.zip`: https://drive.google.com/file/d/1fbQIjza6zCVZ719VvXfNhAONDZflqGnf/view
- GT `corridor02_gt.txt`: https://drive.google.com/file/d/1hb3IVu1OqyPZA61kBZG1raGTBcTv_h3H/view
- Calibration: [extrinsics](https://drive.google.com/file/d/1FzepVzxan_9GjS0Rg_3f1LIjjwm2VZrR/view), [intrinsics](https://drive.google.com/file/d/1gCjmOVcwhm55Rwosel79FMxG_WzvnV8g/view).
- This is a second, longer corridor and a true held-out test of the fixed C_T. No published SLAM numbers exist (SuperLoc is localization in a prior map), so run A-LOAM-only, VINS-only and FAST-LIO2 ourselves.

**T4. SubT-MRS BlockLiDAR** (SP1, Mill19, 677 s, 307.6 m; LiDAR deliberately blocked).
- This is where a VIO-primary design should beat every LiDAR-primary one.
- GT should be in the challenge GT folders. **Check that the file is there before downloading the bag.**
- Bag: challenge [ROS-bag folder](https://drive.google.com/drive/folders/1bV5oCLrpVoc6xKcIduUcco47nG0jPH6i). Calibration links are on [superodometry.com/datasets](https://superodometry.com/datasets).
- The CVPR paper's LiDAR table has a Block column (Zhong et al. has no valid result); the other values were not extracted.
- Counterpart for honesty: **BlockVisual** (camera blocked, 359 s). Expect our method to fall back to LiDAR and perform worse. Report it.

**T5. GEODE α rig.**
- Hardware: VLP-16, the same LiDAR as SubT-MRS; Xsens MTi-30 IMU at 100 Hz; stereo HikRobot global shutter, 1224×1024, **10 Hz**, compressed.
- The GEODE benchmark (7 methods incl. LVI-SAM, R3LIVE, FAST-LIO2, LIO-SAM, DLIO, RELEAD) reports ([GEODE arXiv v2](https://arxiv.org/pdf/2409.04961v2); extraction garbled in places, so recheck in the IJRR PDF):

| α sequence | GT | Published result |
|---|---|---|
| Urban_Tunnel01–03 (vehicle) | RTK-INS 6-DoF (**GNSS is lost inside tunnels; GT quality there is unknown**) | **All methods fail** except RELEAD 40.50 m on 01 |
| Bridge01–03 (vehicle) | RTK-INS 6-DoF | **All methods fail** |
| Stairs_Alpha (handheld, 345 s, 301 m) | PALoc alignment to a Leica RTC360 map, 6-DoF | LVI-SAM fails; LIO-SAM 6.30, FAST-LIO2 4.69, DLIO 4.89, R3LIVE 4.54, RELEAD 0.57 (COIN-LIO not run on alpha; its 0.45 is on beta) |
| Inland_Waterways Short/Medium/Long | GNSS/INS (in the β frame; convert with `alpha2GT_gnss.py`) | LIO-SAM and LVI-SAM fail; FAST-LIO2 10.3 / 19.7 / 70.3 m |
| Tunneling2 | Leica MS60, position only | All methods fail |

- Download: [GEODE Drive](https://drive.google.com/drive/folders/1hEn3sBAvQhSdUFnGMZCCv-W0Ynj2rWBs?usp=sharing) or [Baidu](https://pan.baidu.com/s/19t2WhhUvNnNqKX0zLDhRIA?pwd=sysu) (code `sysu`).
- Calibration: `cali/alpha_config.yaml` in the [GEODE repo](https://github.com/PengYu-Team/GEODE_dataset). Its topic names are wrong; use `/velodyne_points` and `/imu/data`.
- Risk: VINS-Mono at a 10 Hz frame rate on a vehicle at road speed may not initialise. **Smoke-test Stairs_Alpha first** (handheld, slow).

### Tier 3: independent ground truth and controls

**T6. FusionPortableV2 `handheld_underground00`** (Section 1). Total-station GT; run our own baselines.

**T7. SubT-MRS Cave01–04** (handheld, Laurel Caverns).
- GT files `cave0X_gt.txt`; Cave02 confirmed at https://drive.google.com/file/d/1_7D70MVcUbaJqlzN_xlDkguF1qiyZCqF/view; bag `cave02.zip` at https://drive.google.com/file/d/1HwUYboHbCh4_GfyvZYQn25KmA12yiuMR/view.
- DCReg Cave02: odometry 129.78 cm, DCReg 4.57 cm, ME-SR 565.61 cm.
- Camera lighting is undocumented. **Check image brightness before investing.**

**T8. FusionPortable v1 `20220216_corridor_day`.**
- DCReg's corridor, x-degenerate.
- DCReg gets 7.44 cm with a range limit, which is not beatable with a VINS-Mono front end. Use it only as a control, not as a "best result" claim.

**Skipped.**
- CERBERUS ANYmal: no download link found, and its GT is described as "ground-truth structure".
- ENWIDE: no camera.
- QR-paper data: not public.
- Hilti 2021/2022: ground truth mostly behind an evaluation server or sparse; unverified.

---

## 5. Download commands

Google Drive, public files: `pip install gdown`, then `gdown <file-id>`. Example: `gdown 1QbQamSktPAzJkf0GduAPTqQlxuxM0DBK` gives `corridor01_gt.txt`.
- For folders: `gdown --folder <folder-url>`.
- If gdown says the file is over quota, download it in the browser instead.

---

## 6. Not verified (do not cite yet)

- The exact contents of the two challenge GT folders. Drive folder listings did not render, so whether Long_Corridor and BlockLiDAR files are inside is unconfirmed (the challenge page says the trajectories were open-sourced).
- File sizes; whether `corridor01_gt.txt` equals the challenge Long_Corridor GT (run `compare_gt.py`).
- GEODE table values (garbled PDF extraction) and the quality of RTK-INS GT inside tunnels.
- Total-station line-of-sight gaps in `handheld_underground00`.
- Switch-SLAM Table II values other than Multi Floor and Long Corridor.

Sources: [superodometry.com/datasets](https://superodometry.com/datasets) · [ICCV'23 sensor-fusion track](https://superodometry.com/iccv23_challenge_Mul) · [SubT-MRS paper](https://arxiv.org/html/2307.07607v5) · [FPv2 data page](https://fusionportable.github.io/dataset/fusionportable_v2_data/) · [FPv2 paper](https://arxiv.org/html/2404.08563) · [GEODE repo](https://github.com/PengYu-Team/GEODE_dataset) · [GEODE paper](https://arxiv.org/pdf/2409.04961v2) · [LP-ICP](https://arxiv.org/pdf/2501.02580) · [DCReg repo](https://github.com/JokerJohn/DCReg) · project PDFs (Switch-SLAM, DCReg, QR SLAM, review slides).
