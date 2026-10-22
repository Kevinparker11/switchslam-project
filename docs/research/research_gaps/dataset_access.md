# Dataset access sheets: GEODE, FusionPortable v1/V2, SubT-MRS SuperLoc, MS parking lot

Method note: GitHub READMEs and config files were read directly (raw.githubusercontent.com and shallow git clones of PengYu-Team/GEODE_dataset, thisparticle/geode (the GEODE homepage source), JokerJohn/PALoc, JokerJohn/DCReg, fusionportable/fusionportable.github.io (the FusionPortable website source) and superxslam/SuperOdom). superodometry.com and arXiv pages were read only through the WebFetch summariser. Those facts are marked "(via fetch summary)" and should be checked against the page before quoting. The arXiv HTML for GEODE v3 was refused (HTTP 429), so GEODE paper facts come from ar5iv, which may show an older arXiv version. Google Drive, Crossref and arxiv.org could not be reached directly, so **no GT file was downloaded and no timestamp was checked against the data**.

## 1. GEODE (Chen et al.): stairs and VLP-16 sequences

### Takeaway
GEODE is published in IJRR with DOI 10.1177/02783649251344967. SAGE lists the year as 2026; the README records acceptance on 2025-03-09. The README's topic table gives the Xsens MTi-30 on topic `/imu/data` at **100 Hz** for all three rigs. The stairs sequences are `Stairs_Alpha` (VLP-16, 3.7 GB, 345 s, 301.06 m) and `Stairs_Beta` (OS1-64, 11.0 GB, 331 s, 300.15 m). Their GT comes from PALoc alignment to a Leica RTC360 map, and the map is downloadable from gofile links in the PALoc README. GEODE publishes no per-sequence degenerate-direction table, only per-scenario labels.

### Cited Findings
**Access and venue**
- Download: Google Drive folder https://drive.google.com/drive/folders/1hEn3sBAvQhSdUFnGMZCCv-W0Ynj2rWBs?usp=sharing. A Baidu mirror was added on 2025-10-17 (https://pan.baidu.com/s/19t2WhhUvNnNqKX0zLDhRIA?pwd=sysu, code `sysu`). Only ROS1 bags are provided. — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- The README news says "(20250309) Accepted by IJRR!". The README's own Publications entry still says "Under Review", which is stale. — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- SAGE lists "Heterogeneous LiDAR dataset for benchmarking robust localization in diverse degenerate scenarios", Chen, Qi, Feng, Zhuang, Chen, Hu, Wu, Peng, Lu, **2026**, DOI 10.1177/02783649251344967. — [SAGE](https://journals.sagepub.com/doi/10.1177/02783649251344967); [doi.org](https://dx.doi.org/10.1177/02783649251344967)
- Author list (9 authors, same order as SAGE): Zhiqiang Chen, Yuhua Qi, Dapeng Feng, Xuebin Zhuang, Hongbo Chen, Xiangcheng Hu, Jin Wu, Kelin Peng, Peng Lu. — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset); [homepage](https://thisparticle.github.io/geode/)
- An online benchmark (submission via Google Form) is listed. Its leaderboard entries are dated 1/4/2025. — [homepage](https://thisparticle.github.io/geode/)

**Sensors, topics and rates.** Source: the README image "ROS Topic and Explanation of Each Message" ([GEODE README](https://github.com/PengYu-Team/GEODE_dataset)).
- α: `/velodyne_points` (PointCloud2, 10 Hz); IMU `/imu/data` (sensor_msgs/Imu, Xsens MTi-30, **100 Hz**); `/left_camera/compressed` and `/right_camera/compressed` at 10 Hz.
- β: `/ouster/points` (10 Hz); `/ouster/reflec_image` and `/ouster/range_image` (10 Hz); `/ouster/imu` (InvenSense ICM-20948, 100 Hz); `/imu/data` (Xsens MTi-30, 100 Hz); `/left_camera/image/compressed` and `/right_camera/image/compressed`.
- γ: `/livox/lidar` (livox CustomMsg, 10 Hz); `/livox/imu` (BMI088, 200 Hz); `/imu/data` (Xsens, 100 Hz).
- The fetch summary of ar5iv lists the IMUs as α Xsens MTi-30 at 100 Hz, β ICM-20948 at 100 Hz and γ BMI088 at 200 Hz (via fetch summary). Those are the LiDAR-internal IMUs for β and γ. The README table shows that every rig also records the Xsens at 100 Hz on `/imu/data`. — [ar5iv 2409.04961](https://ar5iv.labs.arxiv.org/html/2409.04961)
- PALoc runs GEODE with `lid_topic: "/velodyne_points"` (α) or `"/ouster/points"` (β), and `imu_topic: "/imu/data"`. The α settings are scan_line 16 and timestamp_unit 0 (seconds). The β settings are scan_line 64, lidar_type 8 and timestamp_unit 3 (ns). — [PALoc configs](https://github.com/JokerJohn/PALoc/tree/main/paloc/config/yaml) (`geode_alpha_vlp16.yaml`, `geode_beta_os64.yaml`)

**Calibration files**
- The repo's `cali/` folder holds `alpha_config.yaml`, `beta_config.yaml` and `gamma_config.yaml`. The README text names them `alpha.yaml`, `beta.yaml` and `gamma.yaml`. — [GEODE repo](https://github.com/PengYu-Team/GEODE_dataset)
- α `T_IMU_LiDAR`: R ≈ [[0.9999, 0.0049, 0.0153], [−0.0050, 1.0000, 0.0021], [−0.0153, −0.0022, 0.9999]], t = [0.0961, −0.1338, 0.3032] m.
- β `T_IMU_LiDAR`: R ≈ [[0.998638, 0.052001, −0.004278], [−0.051937, 0.998554, 0.013900], [0.004994, −0.013659, 0.999894]], t = [−0.027172, −0.034873, 0.062643] m.
- Both yaml files also give Xsens noise values. For β: accel_std 1.11e-2, accel_rw 1.60e-4, gyro_std 9.61e-3, gyro rw 8.0e-5. — [cali/](https://github.com/PengYu-Team/GEODE_dataset/tree/main/cali)
- PALoc copies these same extrinsics into its yaml files as `extrinsic_T`/`extrinsic_R`, with the comment "from lidar to imu". — [PALoc configs](https://github.com/JokerJohn/PALoc/tree/main/paloc/config/yaml)
- **Errors in the calibration yaml files.** All fields quoted are as they appear in the repo. — [cali/](https://github.com/PengYu-Team/GEODE_dataset/tree/main/cali)
  - `alpha_config.yaml` says `pointcloud_topic: "/os1_cloud_node1/points"`, `HORZ_RES: 1024` and `imu_topic: "/imu/imu"`. These contradict the README topic table (`/velodyne_points`, `/imu/data`).
  - Both α and β list `VERT_RES: 16`.
  - `beta_config.yaml` defines `T_LiDAR_CamL` twice; the second should presumably be CamR.
- The OS1-64 `metadata.json` is on Google Drive: https://drive.google.com/file/d/1mkB0DFR0Fv3YcI1frnZNxi5AEhObKXbA/view — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)

**File layout and GT format.** Source: the README file-tree image ([GEODE README](https://github.com/PengYu-Team/GEODE_dataset)).
- Layout: `sensor data/<map_env>/<sequence_id>/<sequence_id>.bag` (plus `.zip` raw files), `calibration_files/<device_id>.yaml`, `groundtruth/map/<map_env>.las` and `groundtruth/traj/<sequence_id>.txt`.
- The homepage text gives the GT trajectory folder as `traj/map_env.las`, which looks like a typo. — [homepage](https://thisparticle.github.io/geode/)
- `rmse.py` compares trajectories in TUM format. — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)

**Stairs sequences.** Sizes, durations, distances and difficulty are from the [homepage](https://thisparticle.github.io/geode/).

| Sequence | Rig | Size | Duration | Distance | Difficulty |
|---|---|---|---|---|---|
| Stairs_Alpha | α | 3.7 GB | 345 s | 301.06 m | Medium |
| Stairs_Beta | β | 11.0 GB | 331 s | 300.15 m | Easy |
| Stairs_Gamma | γ | 2.9 GB | 390 s | 300 m | Medium |

- PALoc's quick-run commands use the bag names `stairs_alpha.bag` (VLP-16) and `stairs_bob.bag` (OS-64). Its default sequence name, which is also the prior-map file name, is `stairs_bob`. — [PALoc README](https://github.com/JokerJohn/PALoc)
- Stairs GT method: "we obtain the ground truth pose by using the PALoc algorithm to align the sensor data with the ground truth map." γ has no GT trajectory because its odometry drifts; map-based evaluation (Cloud_Map_Evaluation) is recommended for γ instead. — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- The homepage says the Leica RTC360 is used "for generating ground-truth maps in stairway sequences". — [homepage](https://thisparticle.github.io/geode/)
- The paper says the RTC360 captured "the stairs on both sides of a building and the corridors across multiple floors with millimeter accuracy". Per the fetch summary, the paper says only the Stairs scenario has a GT map (via fetch summary). — [ar5iv](https://ar5iv.labs.arxiv.org/html/2409.04961)
- GT map downloads, from the PALoc README GEODE section:
  - "Prior map without glass noise": http://gofile.me/4jm56/SfohLpthw
  - "Raw prior map": http://gofile.me/4jm56/pK0A9zTJn
  - Sequence links in the same section: "Velodyne16+ xsense IMU" http://gofile.me/4jm56/yCBxjdEXA and "Ouster64 + xsense IMU" http://gofile.me/4jm56/2EoKPDfKi
  - — [PALoc README](https://github.com/JokerJohn/PALoc)
- File size and format of these gofile maps: not stated. PALoc recommends downsampling prior maps below 2 GB and loads `.pcd`. The GEODE layout says GT maps are `.las`. — [PALoc README](https://github.com/JokerJohn/PALoc); [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- Whether stairs α and β were recorded together: the ar5iv summary says the stairs devices were "collected separately (not simultaneously)" (via fetch summary). The README lists only off-road, inland_waterways and Metro_Tunnels_Tunneling as co-captured on the shared rack. The homepage likewise places Tunneling_tunnel, Offroad and Inland_Waterways under "Co-captured Trajectories". — [ar5iv](https://ar5iv.labs.arxiv.org/html/2409.04961); [README](https://github.com/PengYu-Team/GEODE_dataset); [homepage](https://thisparticle.github.io/geode/)

**Degenerate directions.** GEODE labels degeneracy per scenario, not per sequence.

| Scenario | Degenerate directions |
|---|---|
| Flat ground | 2 trans + 1 rot |
| Stairs | 1 trans + 1 rot |
| Metro tunnels | 1 trans + 1 rot |
| Off-road | 2 trans + 1 rot |
| Inland waterways | 1 trans |
| Urban tunnel | 1 trans |
| Bridges | 1 trans |

- Source: Table 3 of the paper (via fetch summary). The README figure shows the same per-scenario arrows. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2409.04961); [README figure](https://github.com/PengYu-Team/GEODE_dataset)
- DCReg Table 2 marks GEODE Stairs (OS64, 331 s, so Stairs_Beta) as degenerate in one translation and one rotation. The DCReg README says stairs weak directions "move between `t2` and `r0-r1`". — [DCReg README](https://github.com/JokerJohn/DCReg)

**Other α (VLP-16) sequences and their GT type**
- α sequences with RTK-INS (GNSS/INS) 6-DoF GT:
  - `Urban_Tunnel01–03` (vehicle; 285, 342 and 334 s) and `Bridge01–03` (vehicle; 382, 472 and 320 s), all α only, with GT from a CHCNAV CG610. — [homepage](https://thisparticle.github.io/geode/); [ar5iv](https://ar5iv.labs.arxiv.org/html/2409.04961) (via fetch summary)
  - `Offroad1–7_alpha` and `Inland_Waterways_{Short,Medium,Long}_Alpha`. The GT is expressed in the β frame, so α outputs must be converted with `alpha2GT_gnss.py`. — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
  - The homepage lists Offroad1_beta's device as "α(UGV)", which is probably a typo. — [homepage](https://thisparticle.github.io/geode/)
- `Tunneling_tunnel2–5_alpha`: GT from a Leica MS60 prism, which gives "only positions, not attitudes", so this is **not 6-DoF**. The GT is aligned to α. — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- `Stairs_Alpha`: 6-DoF via PALoc.

**License**
- None found in the README or on the homepage.

### Inferences
- For a VLP-16 test with full 6-DoF GT and a map, Stairs_Alpha is the only option. Urban_Tunnel and Bridge give 6-DoF RTK-INS GT but no map.
- The usable IMU stream on α and β is `/imu/data` (Xsens, 100 Hz). Ignore the yaml `imu_topic`.

### Gaps
- The arXiv v3 HTML was rate-limited. The ar5iv version shown is unknown, so the IMU table and the "collected separately" claim should be confirmed in the IJRR PDF.
- No sequence-level degenerate-axis table (for example "x" vs "z") was found. The homepage sequence pages and trajectory images were not checked for direction labels.
- GT trajectory frame for Stairs (IMU or LiDAR): unverified.
- Gofile map sizes and formats: unverified, because the gofile links were not opened.
- SAGE volume, issue and pages: not retrieved, because Crossref was blocked.

## 2. FusionPortable v1 and FusionPortableV2

### Takeaway
v1 is IROS 2022 (arXiv 2208.11865). Its site shows "High-Resolution GT Maps" for **Garden, Escalator, Building**, and PALoc additionally hosts a **corridor** GT map. PALoc's repo now ships TUM-format GT for five v1 handheld sequences in `fp_gt/` (added 2026-01-20). V2 is IJRR 2024 (DOI 10.1177/02783649241303525). Its GT devices are 3DM-GQ7 INS, Leica MS60, BLK360 and RTC360. Its site shows GT maps for **UGV Campus (0.36 km²)** and **Underground Parking (0.037 km²)**.

### Cited Findings
**FusionPortable v1: access and sensors**
- Downloads:
  - Google Drive (recommended): https://drive.google.com/drive/folders/17asiPqNyudKR-VCqCnjd0Z0v5sS0f7qI?usp=drive_link
  - Baidu (code `f66z`)
  - HK file server: sensor_data http://filebrowser.ram-lab.com/share/qEhtb7Cl, GT trajectories and maps http://filebrowser.ram-lab.com/share/S-2Th4iV, calibration http://filebrowser.ram-lab.com/share/I67uNo6q (password `fusionportable` for each)
  - — [FusionPortable page](https://fusionportable.github.io/dataset/fusionportable/) (read from the [site repo](https://github.com/fusionportable/fusionportable.github.io))
- Layout: `calibration_files/20220209_calib/<sensor>.yaml`; `groundtruth/map/<date_env>/{scan/<id>.pcd, merged_scan.pcd (1 cm resolution), transformation.yaml}`; `groundtruth/traj/<date_env>.txt`; `sensor_data/<platform>/<date_env>/<date_env>.bag(.7z)`. — [FP v1 page](https://fusionportable.github.io/dataset/fusionportable/)
- Sensors: Ouster OS1-128 (128×2048), FLIR BFS stereo, DAVIS346 stereo, STIM300 IMU, ZED-F9P RTK. — [FP v1 page](https://fusionportable.github.io/dataset/fusionportable/)
- Handheld sequences: 20220216_canteen_night, canteen_day, 20220215_garden_night, 20220216_garden_day, 20220216_corridor_day, 20220216_escalator_day, 20220225_building_day, 20220216_MCR_slow/normal/fast. Quadruped sequences: 20220219_MCR_{slow,normal,fast}_{00,01}. Vehicle sequence: 20220226_campus_road. — [FP v1 page](https://fusionportable.github.io/dataset/fusionportable/)
- The "Some High-Resolution GT Maps" section shows Garden, Escalator and Building. — [FP v1 page](https://fusionportable.github.io/dataset/fusionportable/)
- Topics as used by PALoc: LiDAR `/os_cloud_node/points`, IMU `/stim300/imu/data_raw`.
- LiDAR→IMU extrinsic in PALoc: t = [−0.036897, 0.00787575, −0.0228079], R ≈ I (first row 0.9999765, −0.0023318, −0.0064528). Point time unit is seconds (timestamp_unit 0).
- PALoc plays the bag `20220216_corridor_day_ref.bag`, a refined bag with the `_ref` suffix.
- — [PALoc fp_os128_corridor.yaml](https://github.com/JokerJohn/PALoc/tree/main/paloc/config/yaml); [PALoc README](https://github.com/JokerJohn/PALoc)

**PALoc FusionPortable GT maps.** The PALoc README FusionPortable table gives:
- `20220216_corridor_day`: GT map http://gofile.me/4jm56/mRT2hkB25, described as "corridor with x degeneracy".
- `20220225_building_day`: map folder https://drive.google.com/drive/folders/18b88mLGvx5H84tVBR0ZaaCCKjEY5c8jT, described as "three loops of indoor hallway".
- canteen_day ("prior map only covers a portion"), escalator_day, garden_day and 20220219_MCR_normal_01 link to the same Drive map folder.
- Sequence bags link to Drive folders 1Xc6m3WZrbjdhq9OjfWKDepb9cLKJpety (corridor, canteen, escalator, building), 1epJURj3r29oOyxkTSEUAHE8__tj9vc1h (garden) and 1SvAanjEgiHufMXybupCKZjbIXhMptoj4 (MCR).
- — [PALoc README](https://github.com/JokerJohn/PALoc)

**PALoc `fp_gt` trajectories.** The PALoc news entry for 2026/01/20 reads "Add the generated gt trajectories of FP dataset in `fp_gt` folder". These are PALoc-generated trajectories, not the dataset's own GT. All files are 8-column TUM (`t x y z qx qy qz qw`) at about 10 Hz. Files read directly from [PALoc fp_gt](https://github.com/JokerJohn/PALoc/tree/main/fp_gt):

| File | Poses | Span | Start epoch |
|---|---|---|---|
| `20220216_corridor_day_ref.txt` | 5,724 | 572.3 s | 1645005900.60 |
| `20220225_building_day_ref.txt` | 5,990 | 598.9 s | 1645778924.05 |
| `20220216_canteen_day_ref.txt` | 2,665 | 266.4 s | not recorded |
| `20220216_escalator_day_ref.txt` | 7,135 | 713.4 s | not recorded |
| `20220216_garden_day_ref.txt` | 2,875 | 287.4 s | not recorded |

- DCReg Table 2 lists FP Corridor as OS128, 572 s, degenerate in two translations and one rotation, and FP Building as OS128, 572 s, with no degeneracy marks. — [DCReg README image](https://github.com/JokerJohn/DCReg)

**FusionPortableV2**
- Venue: "The International Journal of Robotics Research (2024)", DOI 10.1177/02783649241303525, arXiv 2404.08563. — [FP V2 page](https://fusionportable.github.io/dataset/fusionportable_v2/)
- Release history: all sequences, GT trajectories and GT maps were released 2024-04-14. Vehicle GT was post-processed on 2024-05-08 to drop high-uncertainty poses. — [FP V2 page](https://fusionportable.github.io/dataset/fusionportable_v2/)
- Download:
  - Google Drive https://drive.google.com/drive/folders/1PYhnf3PlY5r0hbyzWDGTUTPxRMl6SYa-?usp=sharing
  - Baidu https://pan.baidu.com/s/1lZwK-TNrCyoyC9oWEs8jUg?pwd=byj8
  - Calibration on GitHub: https://github.com/fusionportable/calibration_files
  - — [FP V2 data page](https://fusionportable.github.io/dataset/fusionportable_v2_data/)
- Calibration sets by platform: handheld 20230403, UGV 20230426, vehicle 20230618, legged 20230912. — [FP V2 data page](https://fusionportable.github.io/dataset/fusionportable_v2_data/)
- Sensors: OS1-128, FLIR stereo, DAVIS346 stereo, STIM300, 3DM-GQ7 GNSS/INS. Frame IDs include `ouster00`, `ouster00_imu`, `body_imu` (STIM300) and `3dm_imu`. The PointCloud2 timestamp is that of the last point in the scan, and per-point time is in ns. — [FP V2 page](https://fusionportable.github.io/dataset/fusionportable_v2/)
- GT devices (figure caption): "3DM-GQ7, Leica MS60, Leica BLK360, and Leica RTC360". — [FP V2 page figure](https://fusionportable.github.io/dataset/fusionportable_v2/)
- Sequences:
  - Handheld: handheld_grass00, room00/01, escalator00/01, underground00 ("Structureless").
  - Legged: legged_grass00/01, room00, transition00, underground00.
  - UGV: ugv_parking00–03 ("Structureless"), campus00/01, transition00/01.
  - Vehicle: vehicle_campus00/01, street00, tunnel00 ("Low Texture and Structure"), downhill00, highway00/01 ("Structureless"), multilayer00.
  - — [FP V2 data page](https://fusionportable.github.io/dataset/fusionportable_v2_data/)
- "High-Resolution GT Maps" lists UGV Campus (0.36 km²) and Underground Parking (0.037 km²). — [FP V2 data page](https://fusionportable.github.io/dataset/fusionportable_v2_data/)
- Known issue: V2 GT maps contain unremoved dynamic objects, and the site recommends v1 maps for a "clear" map. — [FP V2 page](https://fusionportable.github.io/dataset/fusionportable_v2/)
- V2 does not include corridor_day or building_day; both are v1 sequence names. — [FP v1 page](https://fusionportable.github.io/dataset/fusionportable/); [FP V2 data page](https://fusionportable.github.io/dataset/fusionportable_v2_data/)

### Inferences
- DCReg's "FP" Corridor and Building match FusionPortable **v1** `20220216_corridor_day` and `20220225_building_day`. The 572 s corridor duration matches PALoc's `fp_gt` corridor span of 572.3 s. Building does not match exactly: 572 s in DCReg against 598.9 s in `fp_gt`, which may be a typo in DCReg.
- The v1 GT trajectory device and method (not on the v1 page) is probably MoCap for the MCR sequences and map-based for others, but this is unverified.

### Gaps
- v1 official GT trajectory source and accuracy: not on the website. The arXiv paper was not reachable.
- Frame of the PALoc `fp_gt` poses (LiDAR or IMU): not documented.
- License for v1 and V2: none found on the site pages.
- File sizes: not listed on the v1 or V2 pages.

## 3. SubT-MRS SuperLoc set

### Takeaway
The SuperLoc page lists 8 sequences with Drive links for the bag, extrinsics, intrinsics, GT map and GT trajectory in TUM format (`timestamp x y z q_x q_y q_z q_w`). It documents neither topics, IMU rate, GT frame nor license. The ICCV'23 challenge page lists **Multi_Floor | SP1 | 480 s**, which matches SuperLoc **Floor01 | SP1 | 480 s** with source "SubT-MRS". No source states outright that they are the same recording, and no timestamps could be compared.

### Cited Findings
**SuperLoc sequence table** (via fetch summary). The page groups the sequences by location: Laurel Craven (Cave01–04) and Hawkins (Corridor01–02, Floor01–02). — [SuperLoc page](https://superodometry.com/superloc)

| Sequence | Source column | Robot | Trajectory | Duration |
|---|---|---|---|---|
| Cave01 | SuperLoc | Handheld | 416 m | 838 s |
| Cave02 | SuperLoc | Handheld | 475 m | 986 s |
| Cave03 | SubT-MRS | Handheld | 490 m | 768 s |
| Cave04 | SuperLoc | Handheld | 597 m | 959 s |
| Corridor01 | SubT-MRS | RC2 | 617 m | 279 s |
| Corridor02 | SuperLoc | RC1 | 690 m | 893 s |
| Floor01 | SubT-MRS | SP1 | 270 m | 480 s |
| Floor02 (bonus) | SuperLoc | SP1 | 410 m | 2190 s |

**Floor01 links** (via fetch summary). — [SuperLoc page](https://superodometry.com/superloc)
- Extrinsics: https://drive.google.com/file/d/1FAtf5IkUzNNrwxyqVAV6Vre5Pmvbp8Mj/view
- Intrinsics: https://drive.google.com/file/d/1uH4wFmLeQNrIGlsUsO--PQuyEIOSOGvR/view
- GT map: https://drive.google.com/file/d/1F46g0wnJVSedTJubFD_Ne1IwgZAGYvsU/view
- GT trajectory: https://drive.google.com/file/d/1T-p9TgDwD_9us7U94cT0guwPNTvx3KkI/view
- The rosbag ID was returned as `13QQ8a-dEy56aH8D0RNW0bfywWz6LKn9`, which may be truncated; copy it from the page.
- Floor02 has no GT trajectory link.

**Other SuperLoc links** (via fetch summary). — [SuperLoc page](https://superodometry.com/superloc)
- Cave GT map, shared by all caves: https://drive.google.com/file/d/1JYSVgunLJj6Fj-MsDoNIDHRDx51YWsQP/view
- Cave GT trajectories:

| Sequence | GT trajectory file ID |
|---|---|
| Cave01 | 17JiwUXJ6xZMkL7GSNQg_kV-ZJfKczxak |
| Cave02 | 1_7D70MVcUbaJqlzN_xlDkguF1qiyZCqF |
| Cave03 | 1Rgm5JC4Nq2mm8s6tafY5w-LvxLrt1oPG |
| Cave04 | 11EnNKVYfHJV3P9i0MUrbV4tYqC5z-PSM |

- Corridor01 GT map: 1EH4NzINNLkHrneIxstrzkY9XTZ1JP5bf
- Interactive maps: https://hawkins-gt-map.s3.us-east-2.amazonaws.com/hawkins.html and https://laurel-craven-gt-map.s3.us-east-2.amazonaws.com/laurel_craven.html
- Initial poses: https://drive.google.com/drive/folders/1WZsyEYyU-_8ps1CUqRq3YO7IaARMdGNm

**GT method and sensors**
- The SuperLoc paper (ICRA 2025, arXiv 2412.02901) says GT maps come from a **FARO scanner** with "<2 mm" precision. Floor01 is a legged robot in an abandoned hospital with low confidence in Z. The paper evaluated the ICCV 2023 challenge set (Final01–03, Urban01–02, Cave03, Corridor01, Floor01). It gives no LiDAR or IMU model or rate (via fetch summary). — [arXiv 2412.02901](https://arxiv.org/html/2412.02901); [abs](https://arxiv.org/abs/2412.02901)
- The ICCV'23 LiDAR-inertial challenge page lists:
  - Main track: Final_Challenge_UGV1/2/3, Urban_Challenge_UGV1/2, Laurel_Cavern (Handheld, 960 s).
  - Bonus track: **Long_Corridor (RC2, 332 s)**, **Multi_Floor (SP1, 480 s)**, Block_LiDAR (SP1, 677 s).
  - It also gives no topic names or GT frame (via fetch summary). — [ICCV'23 challenge page](https://superodometry.com/iccv23_challenge_LiI)
- The SubT-MRS datasets page also lists no topics, rates or license. It gives the GT format as `timestamp x y z q_x q_y q_z q_w` (via fetch summary). — [SubT-MRS datasets](https://superodometry.com/datasets)
- Topic names: the team's SuperOdom `vlp_16.yaml` uses `imu_topic: "/imu/data"` and `laser_topic: "/velodyne_points"`, and the README points users to the iccv23 and superloc pages for challenge data. This is a code default, not a documented bag topic list. — [SuperOdom vlp_16.yaml](https://github.com/superxslam/SuperOdom/blob/main/super_odometry/config/vlp_16.yaml); [SuperOdom README](https://github.com/superxslam/SuperOdom)
- DCReg Table 2 lists Cave01 (838 s), Cave02 (986 s) and Cave04 (959 s) as **VLP16** "SubT-MRS". These durations match the SuperLoc cave rows. — [DCReg README](https://github.com/JokerJohn/DCReg)
- The user's local ICCV Multi_Floor extrinsics file (`SubT_MRS_Hawkins_Multi_Floor_LegRobot_Extrinsics.yaml`) has `laser_to_imu` t = [0.080, 0.029, 0.030]. The file name ties Multi_Floor to a legged robot, consistent with SP1. This is a local file, not a public source.

### Inferences
- Floor01 and Multi_Floor are probably the same recording: same site (Hawkins), robot (SP1), duration (480 s), and SuperLoc's "SubT-MRS" source label. This is an **inference**, not a stated fact.
- Corridor01 (279 s) and Long_Corridor (332 s) differ in duration, as do Cave03 (768 s) and Laurel_Cavern (960 s). If they are the same recordings, SuperLoc may have trimmed them.
- The ~417 s Multi Floor span in the user's logs is shorter than 480 s. It may reflect only the processed part of the bag; this cannot be resolved without the files.

### Gaps
- Floor01 bag topics and IMU model/rate: not documented on any page reached.
- GT TUM frame (LiDAR or IMU): **not documented**.
- GT map format and size: not documented.
- Floor01 vs Multi_Floor timestamp overlap: **not checked**, because Google Drive was blocked from this environment. The check is to download the Floor01 GT TUM file (ID 1T-p9TgDwD_9us7U94cT0guwPNTvx3KkI) and compare its first and last stamps with 1660857392–1660857413.
- License: none found.

## 4. DCReg/PALoc "MS" parking lot

### Takeaway
Yes, links are public. The PALoc README links the sequence `parkinglot_01` (gofile), `redbird_02` and `redbird_03` (HKUST SharePoint), a GT map (gofile) and per-sequence GT trajectories (SharePoint). DCReg's Drive provides only demo frames and `prior_map.pcd`. Whether the links still resolve was not tested.

### Cited Findings
- PALoc "Self-collected Dataset" table, sequence links. — [PALoc README](https://github.com/JokerJohn/PALoc)
  - `parkinglot_01`: http://gofile.me/4jm56/t9SM1iPZr
  - `redbird_02`: https://hkustconnect-my.sharepoint.com/:u:/g/personal/xhubd_connect_ust_hk/EXGbd3lDtLNAr6Q_0QPKiH4B1zDYpA2Qr-RTLcKj36KgYw?e=NJ3XxG
  - `redbird_03`: https://hkustconnect-my.sharepoint.com/:u:/g/personal/xhubd_connect_ust_hk/EWW-xzhbmKNDs-Knv23ceB4BeTfVHmVSuI-eQk251StLmA?e=rANaRZ (added 2025-01-22)
- PALoc table, GT links. — [PALoc README](https://github.com/JokerJohn/PALoc)
  - "Ground Truth Map": http://gofile.me/4jm56/C1OOhgG65
  - "Ground Truth Trajectory" links on SharePoint for each of the three sequences.
- The PALoc demo bag name is `Parkinglot-2023-10-28-18-59-01.bag`. — [PALoc README](https://github.com/JokerJohn/PALoc)
- Two MS configs exist in PALoc. — [PALoc configs](https://github.com/JokerJohn/PALoc/tree/main/paloc/config/yaml)
  - `ms_sbg_pandar32.yaml`: LiDAR `/hesai/pandar`, IMU `/imu/data`, extrinsic t = [0.0354, 0.1254, −0.1358].
  - `ms_3dm_pandar32.yaml`: LiDAR `/hesai/pandar`, IMU `/3dm_ins/imu/data_raw`, extrinsic t = [0.1113, −0.0347, −0.0870], with a ~90° rotation (first row 0.0101, −0.0070, −0.9999).
  - Both use 32 lines and default sequence `parkinglot_raw`.
- DCReg's external data link "Cylinder and parking-lot frames" (https://drive.google.com/drive/folders/1TnS7K7q0hr-7SY__mR8pGQX1PJV3Bzfo) provides `prior_map.pcd` and single frames for the `parking_lot_pk01` demo. It is not a full bag. — [DCReg README](https://github.com/JokerJohn/DCReg)
- DCReg Table 2 lists Parking Lot as Pandar32, 502 s, degenerate in two translations and one rotation, dataset "MS". The README describes pk01 as "planar degeneracy with dominant weak directions in X-Y-Yaw". — [DCReg README](https://github.com/JokerJohn/DCReg)
- DCReg news: accepted by IJRR on 2026-05-26. The citation key is `hu2026dcreg`. — [DCReg README](https://github.com/JokerJohn/DCReg)

### Inferences
- The MS bags may carry two IMU streams (SBG on `/imu/data` and 3DM-GQ7 on `/3dm_ins/imu/data_raw`). This is inferred from the two config files and unverified.
- `parkinglot_01` is likely DCReg's pk01, but the README does not state this.

### Gaps
- Whether the gofile and SharePoint links still resolve, and the file sizes: untested.
- MS license and GT method/accuracy: not stated in the README.
