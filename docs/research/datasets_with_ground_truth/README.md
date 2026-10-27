# Cave ground truth exists; test it on caves and stairs

**The claim that the SubT-MRS cave sequences lack public ground truth is false.** Cave01–Cave04 each have a ground-truth (GT) trajectory file in TUM format and share a public Laurel Caverns GT point-cloud map. They are linked from the SuperLoc page, not from the main SubT-MRS datasets page or the ICCV'23 challenge pages, which is why a search of the main pages finds nothing ([SuperLoc page](https://superodometry.com/superloc)). Two caveats matter for the thesis. First, SubT-MRS GT trajectories are **map-aided fusion estimates** built from the GT map plus the platform's own visual, LiDAR and IMU odometry, so they are not independent measurements ([arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)). Second, **Multi Floor was recorded in CMU's Hawkins multi-floor building, not in an underground mine**, so the project slide that says "underground mine" needs correcting ([CVPR 2024 paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.pdf)). Only five degeneracy papers could be verified from primary sources. In all of them, methods separate sharply only in strongly degenerate segments (caves with aggressive motion, stairs, long corridors, range-limited scans) and tie in well-constrained buildings. Only Switch-SLAM scores detection against labels, and those labels are drift- or outcome-based.

For the three test classes, the recommendations are:

- **Class A (coupling-dominated degeneracy):** SubT-MRS Cave02 and GEODE Stairs.
- **Class B (stress cases where Schur may be weak):** range-truncated versions of the same sequences, plus Long Corridor and GEODE tunnels.
- **Class C (VINS-healthy control):** FusionPortableV2 Building, alongside Multi Floor.

The highest-value first step costs no new data. Floor01, the probable Multi Floor recording, has a public Hawkins GT map, so the existing Channel T and Hessian AUC comparison can be re-scored against geometry-based oracle labels instead of drift labels.

## The SubT-MRS cave GT sits on the SuperLoc page, and Floor02 is the only gap

The public SubT-MRS release is split into three groups:

- **ICCV'23 LiDAR-Inertial track:** 6 real sequences (including Laurel_Cavern) plus 3 simulated TartanAir sequences.
- **ICCV'23 Sensor-Fusion track:** 7 sequences, including Multi_Floor and Long_Corridor.
- **SuperLoc localization set (ICRA 2025):** 8 sequences, including Cave01–Cave04, Corridor01/02 and Floor01/02.

All real data come from one sensor pack: a **Velodyne puck LiDAR at 10 Hz, four Leopard Imaging RGB fisheye cameras at 24 Hz, an Epson M-G365 IMU at 200 Hz** and a FLIR Boson thermal camera ([superodometry.com/datasets](https://superodometry.com/datasets); [CVPR 2024 paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.pdf)).

The SuperLoc page lists a GT trajectory and a GT map for every sequence except one. **Floor02's GT trajectory is "Not provided"**; its GT map is the shared Hawkins map ([superodometry.com/superloc](https://superodometry.com/superloc)). The challenge GT, which was withheld during the competition (closed 15 Oct 2023), has since been open-sourced for both tracks ([LiDAR-Inertial page](https://superodometry.com/iccv23_challenge_LiI); [Sensor-Fusion page](https://superodometry.com/iccv23_challenge_Mul)). No evidence was found that any cave GT is still held back, or that an evaluation server is still running.

| Sequence | Site | Platform | Length / duration | GT trajectory (Drive ID) | GT map (Drive ID) |
|---|---|---|---|---|---|
| Cave01 | Laurel Caverns | Handheld | 416 m / 838 s | `17JiwUXJ6xZMkL7GSNQg_kV-ZJfKczxak` | `1JYSVgunLJj6Fj-MsDoNIDHRDx51YWsQP` (shared cave map) |
| Cave02 | Laurel Caverns | Handheld | 475 m / 986 s | `1_7D70MVcUbaJqlzN_xlDkguF1qiyZCqF` | shared cave map |
| Cave03 | Laurel Caverns | Handheld | 490 m / 768 s | `1Rgm5JC4Nq2mm8s6tafY5w-LvxLrt1oPG` | shared cave map |
| Cave04 | Laurel Caverns | Handheld | 597 m / 959 s | `11EnNKVYfHJV3P9i0MUrbV4tYqC5z-PSM` | shared cave map |
| Corridor01 | Hawkins | RC2 (wheeled) | 617 m / 279 s | `1QbQamSktPAzJkf0GduAPTqQlxuxM0DBK` | `1EH4NzINNLkHrneIxstrzkY9XTZ1JP5bf` |
| Corridor02 | Hawkins | RC1 (wheeled) | 690 m / 893 s | `1hb3IVu1OqyPZA61kBZG1raGTBcTv_h3H` | `1d5vv4kfrTyntZw-82fGeTyih3H7DWxg5` |
| Floor01 | Hawkins | SP1 (legged) | 270 m / 480 s | `1T-p9TgDwD_9us7U94cT0guwPNTvx3KkI` | `1F46g0wnJVSedTJubFD_Ne1IwgZAGYvsU` |
| Floor02 | Hawkins | SP1 (legged) | 410 m / 2190 s | **Not provided** | `1F46g0wnJVSedTJubFD_Ne1IwgZAGYvsU` |

Source: [superodometry.com/superloc](https://superodometry.com/superloc). Open each ID at `drive.google.com/file/d/<ID>`. The page spells the cave site "Laurel Craven". The Drive files themselves were not opened in this research, so their contents, sizes and timestamps are still unchecked.

The challenge GT folders are a second source: the Sensor-Fusion track GT (Multi_Floor, Long_Corridor) is in Drive folder `1bSGDe1FFQYEjs20P8L15pTx7T0HCn2L0`, and the LiDAR-Inertial track GT is in Drive folder `1KyM_OO14G6z4NeDZdEfa7hntLLhfdAPp` ([Sensor-Fusion page](https://superodometry.com/iccv23_challenge_Mul); [LiDAR-Inertial page](https://superodometry.com/iccv23_challenge_LiI)).

### How SubT-MRS GT was made, and why it is not independent

GT maps come from a **FARO Focus 3D S120** scanner (±2 mm ranging), with scans registered using point, plane and line correspondences plus loop closure. "96% of the scans achieved a position uncertainty of less than 2mm" ([arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)).

GT trajectories come from "comprehensive fusion of various constraints derived from the ground truth map, visual odometry, LiDAR odometry, and IMU measurements" ([arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)). That makes them **map-aided estimates from the same sensors being evaluated**, not motion-capture or total-station references.

The sources disagree on accuracy. The CVPR supplemental says GT models are accurate "within 10 cm" ([CVPR 2024 supplemental](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Zhao_SubT-MRS_Dataset_Pushing_CVPR_2024_supplemental.pdf)). An earlier arXiv version cites under 2 cm for the campus FARO scans and about 3.4 cm for the hospital map ([arXiv 2307.07607v1](https://arxiv.org/html/2307.07607v1)). These probably measure different things (trajectory versus map), but no per-trajectory accuracy figure has been published.

This matters because LiDAR odometry is one of the GT inputs. In exactly the frames where LiDAR is degenerate, the GT pose leans more on the other constraints and is probably less reliable. A thesis that measures degeneracy-driven drift against this GT should say so. No license text was found on any SubT-MRS page, so contact the AirLab before redistributing derived data.

### Can the cave cameras be used?

This is undocumented. The paper lists caves as visually degraded by "limited lighting" ([arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)), and the cave rows list "RGB, LiDAR, IMU" with no thermal camera ([SuperLoc page](https://superodometry.com/superloc)). No document says whether the handheld rig carried its own lights. DCReg used the caves for LiDAR-only registration and localization, with no camera ([DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy). Assume the images are dark until a brightness check on the actual bag shows otherwise.

## Five verified papers: large gaps in caves and stairs, ties in buildings

The verified literature falls into two groups. One group works at the level of point-cloud registration and evaluates trajectory error against survey-scanner, RTK or GNSS GT: X-ICP, the Tuna et al. field study, DCReg and LP-ICP. The other group is full LiDAR–visual systems, represented here by Switch-SLAM. SubT-MRS appears in three of the five verified papers (DCReg, LP-ICP, Switch-SLAM), and the CERBERUS DARPA SubT ANYmal 1–4 sequences appear in two (LP-ICP, Switch-SLAM).

| Paper | Degenerate data used | GT used | Largest margin | Where methods tie |
|---|---|---|---|---|
| **DCReg** (Hu et al., arXiv 2509.06285, formatted for IJRR) | SubT-MRS Cave01/02/04 (VLP-16); GEODE Stairs (OS1-64); FusionPortable Corridor and Building (OS1-128); self-collected "MS" Parking Lot (Pandar XT-32) with RTK-INS; simulated cylinder | Dataset GT plus GT maps for map accuracy; cylinder GT is the known perturbation | **Cave02 ATE 4.57 cm vs ME-SR 565.61, ME-TSVD 497.05, odometry 129.78**; **Stairs 3.96 vs ME-SR 160.75, FCN-SR 280.07**; Corridor 7.44 vs ME-TSVD 94.32 | **Building ≈8.6 cm for all methods** except FCN-SR (299.46 cm; flags 99.23% of frames); Parking Lot at a 10 m range limit is close, **29.56 vs ME-TSVD 30.46** |
| **X-ICP** (Tuna et al., T-RO 2024) | Self-collected Seemühle mine (ANYmal, VLP-16 and OS0-128), construction site, city park; simulated tunnel, cylinder, corridor | Leica RTC360 scanner map | Seemühle end-position error **0.27 m vs 6.37 m (Zhang) vs 24.17 m (Hinduja)** | Local RPE per 10 m is close (0.17 vs 0.20 vs 0.26 m) |
| **Tuna et al. field study** (arXiv 2408.11809) | Ulmberg bicycle tunnel (OS1-128), ANYmal forest and open field (VLP-16), HEAP excavator site | Leica BLK2GO maps, GNSS | Active methods beat passive ones; global registration fails in symmetric scenes | Equality constraints, TSVD and inequality constraints "performed similarly" |
| **LP-ICP** (arXiv 2501.02580) | PLAM simulated lunar set; CERBERUS ANYmal 1–4; **SubT-MRS Long Corridor** | Exact (simulation); challenge GT for Long Corridor | **Long Corridor 11.92 m vs X-ICP 19.63, Zhang 24.71**; a2_traverse 12.31 vs about 36.7 | CERBERUS ANYmal 1 and 4, feature-rich PLAM; X-ICP is better on a4_home |
| **Switch-SLAM** (Lee et al., RA-L 9(8) 2024) | **SubT-MRS Multi Floor and Long Corridor**; CERBERUS ANYmal 1–4 with LiDAR FOV cut to 180°; Gazebo sims; Handheld | Dataset GT, translational ATE, no loop closure, 3-run average | Best on Multi Floor, Long Corridor, Farm, ANYmal 1–3 | Ties with LVI-SAM on Handheld ("few LiDAR SLAM degeneracy phases") |

Sources: DCReg, project PDF `2509.06285v3.pdf`, Tables 2, 4 and 5 ([arXiv](https://arxiv.org/abs/2509.06285)); X-ICP ([arXiv HTML](https://arxiv.org/html/2211.16335v4)); Tuna et al. ([arXiv HTML](https://arxiv.org/html/2408.11809v1)); LP-ICP ([arXiv HTML v3](https://arxiv.org/html/2501.02580v3)); Switch-SLAM, project PDF ([DOI](https://doi.org/10.1109/LRA.2024.3421792)).

Switch-SLAM's Table II RMSE numbers were not extracted, and neither was DCReg's simulation Table 3. The Tuna et al. margins come from a summary produced by a fetch tool, so the exact numbers for the weaker methods are missing.

### What the Cave02 and Stairs results mean for Schur separation

The two biggest DCReg margins are the strongest published evidence for the Schur-separation hypothesis. Minimum-eigenvalue (ME) detection paired with solution remapping or TSVD fails badly on Cave02 ("aggressive motion patterns where most baseline methods fail entirely") and on GEODE Stairs, while the decoupled method stays at a few centimetres.

DCReg gives an explicit mechanism for the 10 m Parking Lot case: **ME fails "to detect degeneracy" because rotational eigenvalues are larger than translational ones**, a scale mismatch that a joint eigen-analysis cannot separate ([DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285), Sec. 7.3, project copy). The full condition number fails in the opposite direction: it over-detects, flagging 99.23% of frames on the well-constrained Building sequence.

### How detection is scored: almost never against labels

Among the verified papers, **only Switch-SLAM reports detection accuracy against labels**. It builds those labels by comparing GNSS with ICP scan-to-scan matching at each keyframe, on part of its own Handheld dataset, so they are outcome-based. It reports accuracy of 0.91, 0.96 and 0.96 and recall of 0.91, 0.96 and 0.99 for min-eigenvalue, condition-number and Switch-SLAM detection respectively ([Switch-SLAM DOI](https://doi.org/10.1109/LRA.2024.3421792), project PDF Sec. IV-C).

The others do not score detection directly:

- **DCReg** reports a degeneracy ratio (the share of frames flagged), which it calls "an indicator of detection sensitivity rather than an error metric".
- **X-ICP, Tuna et al. and LP-ICP** validate detection only through trajectory error, qualitative figures, or the known geometry of the environment ([X-ICP](https://arxiv.org/html/2211.16335v4); [Tuna et al.](https://arxiv.org/html/2408.11809v1); [LP-ICP](https://arxiv.org/html/2501.02580v3)).

Switch-SLAM's detection labels are not from SubT-MRS, and none of these papers reports per-frame detection precision or recall on SubT-MRS. That leaves room for the thesis to contribute.

Two other papers were found but only partly read. DRPM (arXiv 2410.10784) models Hessian noise probabilistically. Only its abstract was read, so its datasets and any detection evaluation are unknown ([arXiv](https://arxiv.org/abs/2410.10784)). PALoc (arXiv 2401.17826) is a GT-generation pipeline from the DCReg author group, not a detector ([arXiv](https://arxiv.org/abs/2401.17826)).

## Geometry-based oracle labels would replace the weakest part of the Multi Floor result

The Multi Floor result (Channel T AUC about 0.57–0.71 against Hessian 0.76–0.83) is scored with drift labels, and those are the weakest labels in the literature. Drift lags behind the onset of degeneracy, and the IMU can hide it. DCReg notes that IMU and temporal priors "can also redistribute or mask degeneracy patterns" ([DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285)). Drift also depends on the estimator under test and gives no direction.

The research supports a credibility ranking for degeneracy labels, from strongest to weakest:

1. Analytic geometry in simulation. Exact, but the scenes are toy-like.
2. An oracle Hessian or perturbation test at the GT pose against a survey map. Uses real data and does not depend on any detector.
3. Sequence-level tags, such as GEODE's degenerate-direction categories.
4. Drift-based labels.

### Two ways to build geometry-based labels

**Oracle Hessian.** Place each scan at its GT pose, build the point-to-plane Hessian against the GT map, and run the eigenvalue or Schur analysis on it.

**L3E perturbation protocol.** L3E (Nubert, Walther, Khattak, Hutter, ICRA 2022) labels each direction by Monte Carlo: perturb a scan with 6-DoF Gaussian offsets (0.1 m, 5–10°), register it back with point-to-plane ICP, and mark a direction non-localizable if the mean error exceeds **0.1 m or 2°** ([arXiv 2203.05698](https://arxiv.org/pdf/2203.05698); [L3E GitHub](https://github.com/leggedrobotics/L3E)). L3E ran this in Gazebo; applying it to real data is our adaptation. Perturb the GT pose, run ICP from the scan to the GT map, and threshold the convergence error per direction. The result does not depend on Channel T or on the Hessian detector being tested, which removes the bias of scoring a detector with labels derived from its own kind of signal.

Both methods need choices: thresholds, scan range and downsampling. Report a sensitivity sweep over them. DCReg shows how much range alone moves detection: **86.7% of frames flagged at a 10 m range versus 31.1% at 60 m** on its parking lot ([DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285)).

### The circularity caveat

The oracle approach has one structural problem that the thesis should state. On Newer College and Oxford Spires, the GT poses themselves come from ICP of each scan to the TLS map ([NCD GT page](https://ori-drs.github.io/newer-college-dataset/ground-truth/); [Oxford Spires arXiv 2411.10546](https://arxiv.org/html/2411.10546)). GEODE Stairs poses come from aligning to the map with PALoc ([GEODE arXiv 2409.04961v2](https://arxiv.org/html/2409.04961v2)), and SubT-MRS fuses LiDAR odometry into its GT. In the frames where the GT-generating registration was itself degenerate, the GT pose is least trustworthy, which is exactly where labels matter most. Report label confidence alongside the labels, or flag those frames.

### Which datasets support oracle labelling

| Dataset | GT map | GT poses | Supports oracle / L3E labels? |
|---|---|---|---|
| SubT-MRS (Hawkins, Laurel Caverns) | FARO map; Drive IDs listed above | Map-aided fusion | **Yes.** Floor01, Corridor01/02 and Cave01–04 all have map and trajectory |
| GEODE | **Stairs only** (Leica RTC360, LAS) | PALoc alignment on stairs; RTK-INS, total station or Vicon elsewhere | Stairs only |
| FusionPortableV2 | Leica RTC360 / BLK360, only for some sequences (vehicle sequences have none) | Total station (3-DoF), RTK-INS, or FAST-LIO2 where the INS fails | Yes, on the sequences with a map |
| Oxford Spires | Leica RTC360 TLS | ICP to the TLS map, about 1–2 cm | Yes |
| Newer College | Leica BLK360, about 290 M points | ICP to the prior map | Yes; whether the full prior map can be downloaded is unverified |
| Hilti 2022/2023 | Sparse ground-control points only | Evaluation server for most sequences | No |
| ENWIDE | None | Total station, position only | No; also has no camera |

Sources: [superodometry.com/superloc](https://superodometry.com/superloc); [GEODE GitHub](https://github.com/PengYu-Team/GEODE_dataset); [FusionPortableV2 arXiv 2404.08563](https://arxiv.org/html/2404.08563v1); [Oxford Spires arXiv 2411.10546](https://arxiv.org/html/2411.10546); [Hilti 2023 arXiv 2404.09765](https://arxiv.org/html/2404.09765v2); [ENWIDE page](https://projects.asl.ethz.ch/datasets/enwide/).

The notes conflict on Hilti 2022: its GitHub page mentions "high-accuracy laserscans for selected datasets" ([Hilti 2022 GitHub](https://github.com/Hilti-Research/hilti-slam-challenge-2022)), while a summary of the Hilti 2023 paper says the maps are not public. Do not rely on Hilti for oracle labels until this is checked by hand.

**No public dataset offers per-frame, per-direction degeneracy labels.** GEODE gives only per-sequence degenerate-direction categories and "does not explicitly annotate" time intervals ([GEODE arXiv 2409.04961v2](https://arxiv.org/html/2409.04961v2)). Releasing oracle labels for SubT-MRS and GEODE Stairs would be a contribution in its own right.

## Ranked datasets for the three test classes

### Class A (coupling-dominated): Cave02 and GEODE Stairs, both with published baselines

**1. SubT-MRS Cave02 (with Cave01 and Cave04 as replicates).** This is the first choice because it carries the single largest published gap between decoupled and eigenvalue methods (4.57 cm vs 565.61 cm for ME-SR). It also has a GT trajectory and the shared Laurel Caverns GT map, so oracle labels can be built. The catch is the camera: lighting is undocumented, so the VINS branch may be unusable. That does not block Class A, which is a test of the LiDAR detector and can run as LiDAR-plus-IMU, matching DCReg's own setup.

**2. GEODE Stairs, OS1-64 rig as DCReg used it.** This is the best camera, IMU and LiDAR combination for Class A:

- Global-shutter HikRobot stereo cameras, synchronized to GNSS PPS in FPGA hardware.
- A GT map (Leica RTC360) with PALoc-aligned poses.
- A documented coupled degeneracy: DCReg's case study finds Z degenerate when walking down the stairs and roll-pitch degenerate when walking up.
- Published numbers: DCReg 3.96 cm against ME-SR 160.75 cm.

Sources: [GEODE arXiv](https://arxiv.org/html/2409.04961v1); [DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285). **The cameras run at only 10 Hz.** VINS-Mono usually expects 20–30 Hz, so first confirm that VINS-Mono initializes and tracks on an easy GEODE sequence.

**3. FusionPortableV2 corridor or escalator sequences**, if they have a GT map. DCReg's "FP" Corridor (7.44 cm vs ME-TSVD 94.32 cm) is very probably this dataset, but that identification is an inference and has not been confirmed.

### Class B (stress cases where Schur may be weak): controlled range cuts and long axes

The verified literature shows where decoupling stops winning. **At a 10 m range limit, DCReg and ME-TSVD are within 1 cm of each other (29.56 vs 30.46 cm).** Several papers create degeneracy artificially by limiting range (DCReg) or cutting the field of view (Switch-SLAM's 180° CERBERUS runs), which suggests that unmodified public sequences are often not degenerate enough ([DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285); [Switch-SLAM DOI](https://doi.org/10.1109/LRA.2024.3421792)).

**1. Range-truncated versions of Floor01 (Multi Floor), Cave02 and GEODE Stairs, at 10, 20, 30 and 60 m.** This is the best Class B design. It holds the scene, GT and cameras fixed and varies only sparsity, so any advantage Channel T has in the range-limited regime can be attributed to sparsity alone. The original DCReg parking-lot data are self-collected. The repository provides only "the large parking-lot prior map", and whether the bags are public was not confirmed ([DCReg GitHub](https://github.com/JokerJohn/DCReg)).

**2. SubT-MRS Long Corridor / Corridor01.** This adds a natural single-axis degeneracy on a sparse VLP-16 LiDAR. It has a GT trajectory and a Hawkins corridor map, and published numbers from both LP-ICP (11.92 m vs X-ICP 19.63 m) and Switch-SLAM ([LP-ICP](https://arxiv.org/html/2501.02580v3)).

**3. GEODE metro tunnels on the VLP-16 rig, for the "IMU-pinned rotation" case.** These are tagged **1 translational + 1 rotational degenerate DOF** ([GEODE arXiv](https://arxiv.org/html/2409.04961v1)). The rotational degeneracy is the kind a gyroscope can hold in place. The limitation is that tunnel GT is **position only** (Leica MS60 prism tracking) and there is no GT map. Rotation error cannot be evaluated, and oracle labels cannot be computed. Treat these tunnels as a drift-only, translation-only stress test.

Channel T has no published precedent: no verified paper evaluates an orientation-tensor or Bingham detector. Its Class B value is therefore a hypothesis to test, not a finding.

### Class C (VINS-healthy control): well-constrained scenes with tight GT

Multi Floor is already done. The cleanest second control is a **FusionPortableV2 building sequence**. In DCReg's FP Building every method ties at about 8.6 cm, while the full condition number flags 99.23% of frames, so this scene directly measures false positives ([DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285)). FusionPortableV2 states that "all sequences, ground-truth trajectories, and ground-truth maps have been publicly released" ([FusionPortableV2](https://fusionportable.github.io/dataset/fusionportable_v2/)).

**Oxford Spires** is a strong alternative: three global-shutter fisheye cameras at **20 Hz**, a Hesai QT64 LiDAR, a 400 Hz IMU, and a millimetre-level TLS map ([Oxford Spires arXiv 2411.10546](https://arxiv.org/html/2411.10546)). The **Newer College multi-camera extension** has an Alphasense rig with 4 cameras at 30 Hz, an OS0-128 LiDAR and a GT point cloud. Its stairs and Maths sequences also make useful hard cases ([Multi-Cam page](https://ori-drs.github.io/newer-college-dataset/multi-cam/)).

### Practical first steps, in order

1. **Re-score the existing Multi Floor result against oracle labels.**
   - Download the Floor01 GT trajectory (`1T-p9TgDwD_9us7U94cT0guwPNTvx3KkI`) and the Hawkins GT map (`1F46g0wnJVSedTJubFD_Ne1IwgZAGYvsU`).
   - Check that Floor01 really is your Multi_Floor bag. They are probably the same recording: same SP1 platform, same 270 m. But the durations differ (480 s vs 417 s), so check timestamp overlap and cross-check against the Sensor-Fusion track GT folder.
   - Compute oracle-Hessian and L3E-perturbation labels.
   - Recompute AUC for Channel T and for the Hessian detector, with and without the IMU.

   If the gap narrows, the original gap came partly from the drift labels. If it holds, that strengthens the case that the Hessian detector is better.
2. **Check whether the Cave02 images are usable.** Download the Cave02 bag, GT trajectory (`1_7D70MVcUbaJqlzN_xlDkguF1qiyZCqF`) and cave map (`1JYSVgunLJj6Fj-MsDoNIDHRDx51YWsQP`). Before running any switching logic, plot image brightness histograms per camera.
3. **Run the Class A LiDAR-only comparison.** Compare Schur separation against ME on Cave02, using DCReg's reported thresholds (κ_th = 10, minimum eigenvalue 120) so the numbers line up with its Table 5.
4. **Bring up GEODE Stairs.** Fetch the Stairs bag, its GT, and the RTC360 LAS map from the Drive or Baidu links in the GEODE GitHub (ROS1 bags only). Set VINS-Mono for 10 Hz images and confirm it tracks before testing switching.
5. **Generate the Class B range sweeps** on the same three sequences.

## Not yet verified: do not cite these as facts

The rows below come from prior knowledge marked [PK], from inferences, or from sources that were not read. They must be checked against the primary source before they appear in the thesis.

| Item | Status |
|---|---|
| SP1 is a Boston Dynamics Spot | Inference; the page says only "legged" |
| Floor01 = Multi_Floor; Corridor01 = Long_Corridor; Cave03 = the challenge's Laurel_Cavern | Inference from matching platform, length and site |
| DCReg's cave GT is the SuperLoc release | Inference from matching names, durations and citations; not stated in the paper |
| Switch-SLAM used the challenge-released GT for Multi Floor and Long Corridor | Inference |
| DCReg's "FP" = FusionPortable / FusionPortableV2 | Inference from shared co-author X. Hu |
| Identity of DCReg's "MS" dataset and whether its parking-lot bags are public | Unverified |
| DCReg's "Hu et al. 2024b" is PALoc; the cave GT is made PALoc-style | Unverified inference |
| Contents of the SubT-MRS Drive files (format, size, timestamps); per-trajectory GT accuracy | Not opened |
| Whether the cave rig had lights; whether cave images are usable | Undocumented |
| Global-shutter cameras and hardware sync in FusionPortable V1/V2 and the Newer College extension | [PK] |
| Details of Newer College 2020, Hilti 2021/2023, NTU VIRAL, M2DGR, MCD, Botanic Garden, S3E, HeLiPR, DiTer/DiTer++ (sensors, GT, held-back splits, degenerate content) | [PK] or unverified |
| Ground-Challenge sensors and degenerate content (only its LiDAR-SLAM GT type was verified) | Partly [PK] |
| Whether the Hilti 2022 TLS maps are public (the sources conflict) | Unverified |
| Whether the full Newer College prior map can be downloaded | Unverified |
| Which FusionPortableV2 sequences carry a GT map (Table 4 not extracted) | Unverified |
| Experiments in Zhang & Singh 2016, Hinduja 2019, DARE-SLAM, SuperOdometry/SuperLoc, LVI-SAM, R2LIVE, R3LIVE, FAST-LIVO2, GenZ-ICP, the point-to-distribution degeneracy factor, RELEAD | Not read |
| LF-GICP (arXiv 2608.19522); the 2025 degradation-robust mapping dataset (arXiv 2507.20516); GrandTour (arXiv 2602.18164); the LiDAR Variability dataset (arXiv 2507.04321); tunnel thermal-LiDAR (arXiv 2505.03565); Hilti-Trimble-Oxford 360 VI | Found in searches, not examined |
| DRPM's datasets and any detection evaluation | Only the abstract was read |
| Switch-SLAM Table II RMSE values; DCReg Table 3 | Not extracted |
| Whether original TartanAir has LiDAR; LiDAR, IMU and camera support in CARLA, Isaac Sim and the SubT virtual worlds | Unverified |
| License terms for every dataset above | None found |

## Conclusion

Of the issues raised, the missing cave GT is the easiest to fix: it is a matter of where the files are linked. The real problem is the labels. The current Channel T versus Hessian comparison is scored with drift labels, which the IMU can hide and which depend on the estimator under test. The verified literature never scores detection against geometry-based labels on SubT-MRS. Floor01 already has a public GT map, so the thesis can run that geometry-based test on the data it already has before adding any new dataset. The outcome of that re-scoring should decide how Channel T is framed. If it still trails the Hessian detector under oracle labels, its contribution narrows to the Class B regimes (range-limited scans and rotation the IMU holds in place). Those are where DCReg's own margin shrinks to about 1 cm, and so the one place left for a complementary channel to help.

The other strategic point is that the published "large win" cases are few and specific: Cave02, GEODE Stairs, a range-limited corridor, Long Corridor. Several of them only became degenerate after the authors limited range or cut the field of view. A thesis that publishes per-frame, per-direction oracle and L3E labels for Floor01, Cave02 and GEODE Stairs, with range sweeps and a stated circularity caveat, would supply a benchmark that does not yet exist. That benchmark would be harder to dispute than any single AUC number.
