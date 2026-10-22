# SubT-MRS dataset: ground-truth availability per sequence (focus: Cave01/02/04, Hawkins Multi Floor)

Research date: 2026-10-06. Web pages were read through a fetch/summarise tool, not as raw HTML. superodometry.com was blocked for direct curl, so per-cell table values are as the fetch tool reported them. Exact Drive file IDs are given so they can be checked by hand. arxiv.org HTML for 2509.06285v3 was rate-limited (HTTP 429), so the DCReg details come from the project's copy of the PDF (`2509.06285v3.pdf`).

## Q1. What sequences exist (environment, platform, sensors, duration)?

### Takeaway
The public SubT-MRS release on superodometry.com is organised in three groups:
- **ICCV'23 LiDAR-Inertial track:** 6 real sequences plus 3 TartanAir simulated sequences.
- **ICCV'23 Sensor-Fusion track:** 7 sequences, including Multi_Floor and Long_Corridor.
- **SuperLoc localization set (ICRA 2025):** 8 sequences. This is where Cave01–Cave04, Corridor01/02 and Floor01/02 live.

All real data come from one sensor pack: Velodyne puck (VLP-16 class), 4 RGB fisheye cameras, a FLIR Boson thermal camera and an Epson IMU.

### Cited Findings
- **Sensor pack:** "4 Leopard Imaging RGB fisheye cameras, 1 Velodyne puck, 1 Epson M-G365 IMU, 1 FLIR Boson thermal camera", with an NVIDIA Jetson AGX Xavier. Rates per the CVPR paper: LiDAR 10 Hz (360°×30°), RGB 24 Hz, thermal 60 Hz, IMU 200 Hz. An Intel L515 depth camera is also listed. — [CVPR 2024 paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.pdf); [arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)
- **Scale:** the paper claims "over 30 diverse scenes" and "over 500 hours and 100 kilometers" collected 2019–2023. Platforms are aerial, legged, wheeled (RC cars) and handheld. The paper has no per-sequence table of durations and lengths. — [arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)
- **LiDAR-Inertial track (real sequences, all LiDAR + IMU):**
  - Final_Challenge_UGV1/2/3: UGV, "geometry degraded"
  - Urban_Challenge_UGV1/2: UGV
  - Laurel_Cavern: handheld, "underground cave"
  - Simulated (TartanAir): Lidar_factory, Lidar_ocean, Lidar_sewerage
  - Bonus sequences: Long_Corridor, Multi_Floor, Block_LiDAR
  - — [superodometry.com/datasets](https://superodometry.com/datasets); [LiDAR-Inertial challenge page](https://superodometry.com/iccv23_challenge_LiI)
- **Sensor-Fusion track:**

  | Sequence | Platform | Sensors | Duration | Length |
  |---|---|---|---|---|
  | Multi_Floor | SP1 (legged) | LiDAR, RGB, IMU | 417 s | 270 m |
  | Long_Corridor | RC2 (wheeled) | LiDAR, RGB, IMU | 295 s | 616.45 m |
  | BlockLiDAR | SP1 | LiDAR, RGB, IMU | 677 s | 307.55 m |
  | BlockVisual | SP1 | RGB, IMU, thermal | 359 s | 186.02 m |
  | SmokeRoom | RC7 | RGB, thermal, IMU | 418 s | 104.84 m |
  | OutdoorNight | SP1 | RGB, thermal, IMU | 484 s | 254.03 m |
  | FlashLight | SP1 | RGB, thermal, IMU | 279 s | 147.75 m |

  — [Sensor-Fusion challenge page](https://superodometry.com/iccv23_challenge_Mul)
- **SuperLoc set** (columns as reported: "Trajectory", which appears to be length in m, and Duration in s):

  | Sequence | Source | Location | Platform | Sensors | Trajectory | Duration |
  |---|---|---|---|---|---|---|
  | Cave01 | SuperLoc | Laurel Craven | Handheld | RGB, LiDAR, IMU | 416 | 838 |
  | Cave02 | SuperLoc | Laurel Craven | Handheld | RGB, LiDAR, IMU | 475 | 986 |
  | Cave03 | SubT-MRS | Laurel Craven | Handheld | RGB, LiDAR, IMU | 490 | 768 |
  | Cave04 | SuperLoc | Laurel Craven | Handheld | RGB, LiDAR, IMU | 597 | 959 |
  | Corridor01 | SubT-MRS | Hawkins | RC2 | RGB, LiDAR, IMU | 617 | 279 |
  | Corridor02 | SuperLoc | Hawkins | RC1 | RGB, LiDAR, IMU | 690 | 893 |
  | Floor01 | SubT-MRS | Hawkins | SP1 | RGB, LiDAR, IMU | 270 | 480 |
  | Floor02 (bonus) | SuperLoc | Hawkins | SP1 | RGB, LiDAR, IMU | 410 | 2190 |

  — [superodometry.com/superloc](https://superodometry.com/superloc)
- **Platform codes:** the CVPR paper names the Multi-Floor environment as the "Hawkins Multi-Floor Building" and lists Laurel Cavern as a cave site. — [CVPR 2024 paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.pdf)

### Inferences
- **"SP1" is probably a Boston Dynamics Spot.** The challenge page calls it a legged robot. The "Spot" model name is my inference and is not stated verbatim in the fetched text.
- **Floor01 is probably the same recording as Multi_Floor**: same platform (SP1), same building, same 270 m length. The durations differ (480 s against 417 s), possibly from different trimming. Unverified.
- **Corridor01 is probably the same recording as Long_Corridor**: RC2, 617 m against 616.45 m, 279 s against 295 s. Unverified.
- **Cave03, the cave sequence marked "SubT-MRS" as its source, is probably the challenge's Laurel_Cavern.** Unverified.
- **Cave01, Cave02 and Cave04 are marked "SuperLoc" as their source.** They were released with the SuperLoc paper (ICRA 2025), not with the original CVPR 2024 / ICCV'23 SubT-MRS release. That would explain why searching the SubT-MRS dataset or challenge pages turns up no GT for them.
- **The project slide describes Multi Floor as "real legged-robot recording in an underground mine".** This appears to be wrong. Sources place Multi_Floor / Floor01 in the Hawkins multi-floor building, not in a mine.

### Gaps
- No official per-sequence table of LiDAR model by sequence. The paper says "Velodyne puck", and DCReg lists the caves as VLP16.
- Durations for the LiDAR-Inertial track sequences (UGV and Laurel_Cavern) were not shown in the fetched page content.

## Q2. Is GT released per sequence, and in what form? How was it produced?

### Takeaway
**Cave01–Cave04 do have public GT.** The SuperLoc page links a separate GT trajectory file (TUM format) for each of the four, plus a shared Laurel Caverns GT point-cloud map. So it is not true that cave GT is unavailable; it is on the SuperLoc page, not on the main datasets page.

The Hawkins legged sequence (Floor01, which is likely Multi_Floor) has both a GT trajectory and a GT map. **Floor02 is the only SuperLoc sequence whose GT trajectory is "Not provided".** Challenge-track GT, originally withheld, has since been open-sourced.

GT comes from FARO Focus 3D S120 survey maps plus multi-constraint fusion.

### Cited Findings

**SuperLoc page (GT Map and GT Traj. columns):**

| Sequence | GT trajectory | GT map |
|---|---|---|
| Cave01 | `17JiwUXJ6xZMkL7GSNQg_kV-ZJfKczxak` | shared cave map `1JYSVgunLJj6Fj-MsDoNIDHRDx51YWsQP` |
| Cave02 | `1_7D70MVcUbaJqlzN_xlDkguF1qiyZCqF` | shared cave map |
| Cave03 | `1Rgm5JC4Nq2mm8s6tafY5w-LvxLrt1oPG` | shared cave map |
| Cave04 | `11EnNKVYfHJV3P9i0MUrbV4tYqC5z-PSM` | shared cave map |
| Corridor01 | `1QbQamSktPAzJkf0GduAPTqQlxuxM0DBK` | `1EH4NzINNLkHrneIxstrzkY9XTZ1JP5bf` |
| Corridor02 | `1hb3IVu1OqyPZA61kBZG1raGTBcTv_h3H` | `1d5vv4kfrTyntZw-82fGeTyih3H7DWxg5` |
| Floor01 | `1T-p9TgDwD_9us7U94cT0guwPNTvx3KkI` | `1F46g0wnJVSedTJubFD_Ne1IwgZAGYvsU` |
| Floor02 | "Not provided" | `1F46g0wnJVSedTJubFD_Ne1IwgZAGYvsU` (map only) |

- All IDs above are Google Drive file IDs, opened at `drive.google.com/file/d/<ID>`. — [superodometry.com/superloc](https://superodometry.com/superloc)
- The page also links rosbags, extrinsic and intrinsic calibration (Google Drive and Baidu), and initialization poses ([Drive folder](https://drive.google.com/drive/folders/1WZsyEYyU-_8ps1CUqRq3YO7IaARMdGNm?usp=sharing)). It states "Ground truth trajectory follows TUM format". — [superodometry.com/superloc](https://superodometry.com/superloc)
- Web viewers for the GT maps: [Hawkins GT map](https://hawkins-gt-map.s3.us-east-2.amazonaws.com/hawkins.html), [Laurel Craven GT map](https://laurel-craven-gt-map.s3.us-east-2.amazonaws.com/laurel_craven.html). — [superodometry.com/superloc](https://superodometry.com/superloc)
- **Datasets page:** "Ground truth trajectories are distributed separately", in the format `timestamp x y z q_x q_y q_z q_w`. — [superodometry.com/datasets](https://superodometry.com/datasets)
- **LiDAR-Inertial track:** GT was withheld during the competition and later "open-sourced" to "facilitate easier evaluation". GT folder: [Drive 1KyM_OO14G6z4NeDZdEfa7hntLLhfdAPp](https://drive.google.com/drive/folders/1KyM_OO14G6z4NeDZdEfa7hntLLhfdAPp). The fetch tool showed only a "LiDAR_Inertial_Track" subfolder, not individual files. — [LiDAR-Inertial challenge page](https://superodometry.com/iccv23_challenge_LiI)
- **Sensor-Fusion track:** GT trajectories open-sourced at [Drive 1bSGDe1FFQYEjs20P8L15pTx7T0HCn2L0](https://drive.google.com/drive/folders/1bSGDe1FFQYEjs20P8L15pTx7T0HCn2L0). This covers Multi_Floor and Long_Corridor. — [Sensor-Fusion challenge page](https://superodometry.com/iccv23_challenge_Mul)
- **How GT was produced:**
  - GT maps come from a "high-precision FARO Focus 3D S120 3D scanner" (range up to 120 m, "±2mm" range error). Scans were registered with "point-to-point, point-to-plane, and point-to-line correspondences" plus loop closure, and "96% of the scans achieved a position uncertainty of less than 2mm".
  - GT trajectories came from "comprehensive fusion of various constraints derived from the ground truth map, visual odometry, LiDAR odometry, and IMU measurements".
  - — [arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5); [CVPR 2024 paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.pdf)
- A student presentation titled "Ground Truth Trajectory Generation For SubT-MRS Dataset" exists (CMU Meeting of the Minds 2023). Its contents were not read. — [Symposium listing](https://symposium.foragerone.com/meeting-of-the-minds-2023/presentations/53492)

### Inferences
- **GT trajectories are not independent of the sensors.** They are map-constrained fusion estimates from the same sensors, not motion-capture or total-station measurements. Accuracy is probably at the cm level along the trajectory, while the map itself is at the mm level. No per-trajectory accuracy figure was found.
- **Practical route for the user:** for Cave01/02/04, download the GT Traj. links on the SuperLoc page (not the datasets page or the challenge pages).

### Gaps
- Could not open the Drive files to confirm what they contain (file format, sizes, timestamps).
- No published per-sequence GT accuracy figure.
- The SuperLoc paper text read via alphaXiv gave no GT-generation details beyond the CVPR method.

## Q3. Is cave GT withheld for challenge evaluation? Is an evaluation server still running?

### Takeaway
**No evidence that any cave GT is currently withheld.** The ICCV'23 challenge (including Laurel_Cavern) closed on 15 Oct 2023, and its GT was later open-sourced. The SuperLoc caves ship with GT links. No evaluation server that is still active was found.

### Cited Findings
- Challenge deadline: 15 Oct 2023. Submissions went through Gradescope (one per day), ranked by length-weighted reciprocal ATE/RPE. Final ATE ranking: HKU-MaRS-Lab first, Weitong Wu et al. second, CILAB@Yonsei third. — [LiDAR-Inertial challenge page](https://superodometry.com/iccv23_challenge_LiI)
- GT for challenge sequences is described as withheld during the challenge and open-sourced afterwards. — [LiDAR-Inertial challenge page](https://superodometry.com/iccv23_challenge_LiI); [Sensor-Fusion challenge page](https://superodometry.com/iccv23_challenge_Mul)
- Challenge GitHub repository (issue tracker; showed 4 open issues): [water-horse/ICCV2023_SLAM_Challenge](https://github.com/water-horse/ICCV2023_SLAM_Challenge)
- The CVPR paper itself has no statement about holding back test-set GT. — [CVPR 2024 paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.pdf)

### Inferences
- The site also links an "imuchallenge" page ([superodometry.com/imuchallenge](https://superodometry.com/imuchallenge)), which was not read. A later challenge could in principle have hidden GT, but no evidence of that was found for the cave sequences.

### Gaps
- Did not check whether the Gradescope submission portal still accepts submissions.

## Q4. Can the cameras be used in the caves?

### Takeaway
The paper calls caves visually degraded through "limited lighting". No document found says whether the handheld rig in Laurel Caverns carried its own illumination. The cave sequences include RGB, but whether that RGB is usable is undocumented, so expect dark images.

### Cited Findings
- The paper lists visual degradation in "environments with limited lighting, such as hospital interiors and caves" and in "extreme darkness and overexposure". — [arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)
- The SuperLoc rows for Cave01–Cave04 list sensors "RGB, LiDAR, IMU". Thermal is not listed for the caves. — [superodometry.com/superloc](https://superodometry.com/superloc)
- A "FlashLight" sequence (SP1; RGB, thermal, IMU) exists specifically for changing illumination. — [Sensor-Fusion challenge page](https://superodometry.com/iccv23_challenge_Mul)
- **DCReg used the caves only for LiDAR registration and localization**, with no camera. — project copy of [DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285)

### Inferences
- Visual or visual-LiDAR switching methods evaluated on Cave01/02/04 should first inspect image brightness. This is not documented, so it should be checked empirically.

### Gaps
- No source on illumination hardware (headlamp or LEDs) or on image exposure in the cave sequences.

## Q5. Which papers used which SubT-MRS sequences, and where did their GT come from?

### Takeaway
- **DCReg (IJRR-style preprint, arXiv 2509.06285)** used Cave01, Cave02 and Cave04, citing both SubT-MRS and SuperLoc. It evaluated map-based localization ATE.
- **Switch-SLAM (RA-L, vol. 9, no. 8, Aug 2024)** used Multi Floor and Long Corridor.
- **SuperLoc (ICRA 2025, arXiv 2412.02901)** introduced the 8-sequence localization set.

### Cited Findings
- **DCReg sequences:** Table 2 lists Cave01 (838 s), Cave02 (986 s) and Cave04 (959 s), all handheld, VLP16, "SubT-MRS", cited as Zhao et al. 2024a (CVPR) and 2024b (SuperLoc, arXiv 2412.02901). The durations match the SuperLoc table exactly. — DCReg PDF in project ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285)); [superodometry.com/superloc](https://superodometry.com/superloc)
- **DCReg results:** Table 5 reports long-duration localization on Cave02 ("aggressive motion patterns where most baseline methods fail"): DCReg ATE 4.57 cm against Odom 129.78 cm and O3D 16.88 cm, on a 53M-point map. The ATE follows Grupp's evo, and map metrics are computed "with the ground-truth map". SuperLoc is used as a baseline backend. — DCReg PDF in project ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285))
- **DCReg GitHub** ships only demo data (cylinder, parking lot) and does not redistribute SubT-MRS. — [JokerJohn/DCReg](https://github.com/JokerJohn/DCReg)
- **Switch-SLAM** used "Multi Floor and Long Corridor dataset (SubT-MRS dataset)", described as containing "structure-less and visually challenging scenes simultaneously". It reported ATE (max and RMSE) against GT without loop closure. Its degeneracy-detection GT was built on its own Handheld dataset from GNSS against ICP, not on SubT-MRS. — Switch-SLAM PDF in project (Lee et al., IEEE RA-L 9(8), 2024, pp. 7275–7276)
- **SuperLoc** reports a "54% increase in accuracy" on SubT-MRS across eight sequences and promised to release "datasets from eight challenging scenarios". — [alphaXiv 2412.02901](https://www.alphaxiv.org/abs/2412.02901); [superodometry.com/superloc](https://superodometry.com/superloc)

### Inferences
- **DCReg's cave GT is most likely the SuperLoc-released GT trajectory and Laurel Caverns map**: the sequence names, durations and dual citation all match. The paper text read here does not say this explicitly.
- **Switch-SLAM most likely used the challenge-released GT** for Multi_Floor and Long_Corridor. Not stated explicitly in the excerpts read.

### Gaps
- Did not find other papers that list specific SubT-MRS sequences, for example the challenge winners' reports.

## Q6. License and download access

### Takeaway
No explicit license (for example CC BY) was found on the dataset pages, in the CVPR paper or in the challenge repository. Data are hosted on Google Drive, with Baidu mirrors for SuperLoc calibration files.

### Cited Findings
- The SuperLoc and datasets pages show no license text. — [superodometry.com/superloc](https://superodometry.com/superloc); [superodometry.com/datasets](https://superodometry.com/datasets)
- The paper has no licensing statement. — [arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)
- Bulk downloads:
  - LiDAR-Inertial track rosbags: [Drive](https://drive.google.com/drive/folders/1hHCsnc-gANmK6Oox-Im3hqRwsGGaJIuJ)
  - Sensor-Fusion track rosbags: [Drive](https://drive.google.com/drive/folders/1bV5oCLrpVoc6xKcIduUcco47nG0jPH6i)
  - — [LiDAR-Inertial challenge page](https://superodometry.com/iccv23_challenge_LiI); [Sensor-Fusion challenge page](https://superodometry.com/iccv23_challenge_Mul)

### Inferences
- Large Drive files can hit Google's download quota. This is a general Drive behaviour, not something verified for these files.

### Gaps
- License terms are unknown. Contact the AirLab before redistributing.
