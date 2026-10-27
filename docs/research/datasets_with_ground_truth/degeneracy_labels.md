# Ground-truth degeneracy labels for evaluating LiDAR degeneracy detectors

## Q1. Which datasets release a GT point-cloud map (TLS) + GT poses, enabling an "oracle" Hessian/observability per frame?

### Takeaway
Newer College, Oxford Spires, FusionPortableV2 (subset of sequences), SubT-MRS, and GEODE (select indoor/stair sequences only) provide or promise a survey-grade GT map plus GT poses, so one can build each frame's point-to-plane Hessian against the GT map at the GT pose. Hilti 2022/2023 do NOT release TLS maps (only sparse ground-control points), so they are unsuitable for oracle-Hessian labelling.

### Cited Findings
- **Newer College**: prior map from a Leica BLK360 TLS, 47 static scans over 8 h, ~290 M points, point accuracy better than 1 cm; GT poses obtained by registering each Ouster scan to the prior map (libpointmatcher ICP, map downsampled to 1 cm) — [NCD Ground Truth page](https://ori-drs.github.io/newer-college-dataset/ground-truth/). Whether the full prior map is downloadable was not stated on that page — [NCD Ground Truth page](https://ori-drs.github.io/newer-college-dataset/ground-truth/) (UNVERIFIED: download availability).
- **Oxford Spires**: Leica RTC360 TLS map (1.9 mm at 10 m, 5.3 mm at 40 m; 3-7 mm cloud-to-cloud error); GT trajectory "computed by ICP registering each undistorted LiDAR point cloud to the merged TLS map", ~1-2 cm accuracy; sensors: 3 global-shutter fisheye cameras (20 Hz), Hesai QT64 LiDAR, 400 Hz IMU; data released at dynamic.robots.ox.ac.uk/datasets/oxford-spires — [Oxford Spires arXiv 2411.10546](https://arxiv.org/html/2411.10546)
- **FusionPortableV2**: GT maps from Leica RTC360 (outdoor) and Leica BLK360 (indoor), ~0.3 km² coverage; not all sequences have a GT map (vehicle sequences lack them; Table 4 "GT Map" column); GT poses from Leica MS60 total station (3-DoF, ~1 mm), 3DM-GQ7 dual-antenna RTK-INS (~1.4 cm), or FAST-LIO2 where INS fails — [FusionPortableV2 arXiv 2404.08563](https://arxiv.org/html/2404.08563v1); dataset site [FusionPortable dashboard](https://fusionportable.github.io/dataset/fusionportable_v2/)
- **SubT-MRS**: GT map built with Leica Viva TS15A total station, Leica 360 mini prism, FARO Focus 3D S120 (79 FARO scans on CMU campus, <2 cm; hospital ~3.4 cm over 350×350 m); paper states "The ground truth maps for all the datasets will be provided to the users"; sensors: 4 RGB cameras, Velodyne VLP-16, Epson M-G365 IMU, FLIR Boson thermal — [SubT-MRS arXiv 2307.07607](https://arxiv.org/html/2307.07607v1)
- **GEODE**: "precise ground-truth poses for each sequence and ground-truth maps for select indoor sequences"; stair sequence has GT map (LAS) and its poses were obtained by aligning sensor data to the GT map with PALoc; other GT: Vicon mocap / Leica laser tracker (indoor), GNSS-RTK/INS (outdoor), Leica MS60 prism tracking for metro tunnels (position only) — [GEODE arXiv 2409.04961](https://arxiv.org/html/2409.04961v2); [GEODE GitHub](https://github.com/PengYu-Team/GEODE_dataset). Sensors: three rigs (VLP-16 / Ouster OS1-64 / Livox AVIA), each with stereo HikRobot cameras + Xsens MTi-30 IMU — [GEODE GitHub](https://github.com/PengYu-Team/GEODE_dataset)
- **Hilti 2022/2023**: GT is "sparse ground truth extracted from a unified terrestrial laser scan", Z+F Imager 5016 (2022) and Trimble X7 (2023), evaluated at surveyed ground-control points; point-cloud maps are not publicly released (per the fetched summary of the paper) — [Hilti 2023 arXiv 2404.09765](https://arxiv.org/html/2404.09765v2); [Hilti 2023 dataset page](https://hilti-challenge.com/dataset-2023)
- **ENWIDE** (degenerate tunnel/field/runway/intersection/Katzensee; Ouster OS0-128 + internal IMU, no camera listed): GT from Leica MS60 total station prism (position only); no GT map mentioned — [ENWIDE page](https://projects.asl.ethz.ch/datasets/enwide/)
- DCReg (IJRR 2026) evaluated on FusionPortable, GEODE, SubT-MRS and self-collected Pandar XT-32 data with RTK-INS, and used GT maps for mapping metrics (AC, Chamfer distance) — [DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285); [DCReg GitHub](https://github.com/JokerJohn/DCReg)

### Inferences
- Best fit for "oracle Hessian at GT pose" with camera+IMU+LiDAR: Oxford Spires and Newer College (GT poses are themselves scan-to-TLS-map ICP, so the oracle Hessian is the very Hessian of the GT-generation registration — consistent but note circularity: frames where that ICP was itself degenerate will have less reliable GT poses). FusionPortableV2 and SubT-MRS are next (map + independent tracker/INS poses). GEODE only for stairs/indoor sequences with maps.
- Hilti and ENWIDE give poses only, so they support drift-based labels but not geometry-based oracle labels (unless one builds a map from GT poses + scans, which is circular).

### Gaps
- Did not verify the actual downloadable status of Newer College and SubT-MRS GT maps (SubT-MRS says "will be provided").
- Did not verify which exact FusionPortableV2 sequences carry GT maps (Table 4 not extracted).

## Q2. Which datasets/papers provide explicit degeneracy annotations?

### Takeaway
No surveyed public dataset provides per-frame / per-time-window degeneracy labels with directions. GEODE gives per-sequence degenerate-direction categories (e.g., "1 Trans.", "2 Trans. + 1 Rot."); FusionPortableV2 and SubT-MRS give sequence-level challenge tags; ENWIDE only describes "large sections of degenerate geometry".

### Cited Findings
- GEODE "does not explicitly annotate" degenerate time intervals; Table 3 lists per-sequence "Degeneracy Direction" (translational / rotational / combined) — [GEODE arXiv 2409.04961](https://arxiv.org/html/2409.04961v2)
- FusionPortableV2 Table 4 "Challenges" column tags sequences as Textureless, Structureless, Dynamic, Scale, Perceptual Aliasing — [FusionPortableV2 arXiv](https://arxiv.org/html/2404.08563v1)
- SubT-MRS categorizes sequences as visually / geometrically / simultaneously degraded, no segment-level labels — [SubT-MRS arXiv](https://arxiv.org/html/2307.07607v1)
- ENWIDE: "environments with large sections of degenerate geometry", smooth and dynamic sequence per site; no per-segment labels on the page — [ENWIDE page](https://projects.asl.ethz.ch/datasets/enwide/)
- Tuna et al. 2025 report the Ulmberg bicycle tunnel has LiDAR degeneracy for "more than 80% of the dataset" (a coarse quantitative statement, not released labels) — [Tuna et al. arXiv 2408.11809](https://arxiv.org/pdf/2408.11809)

### Inferences
- A thesis can claim a contribution by releasing per-frame oracle labels derived from GT maps (e.g., on Oxford Spires / FusionPortableV2 / GEODE-stairs), since none exists publicly per this search.
- GEODE's sequence-level direction tags can serve as a weak sanity check (does the detector's dominant flagged direction match the sequence tag?).

### Gaps
- Did not exhaustively search all 2025-2026 datasets (e.g., the "Degradation-Robust High-Precision Mapping" dataset seen in search results on ResearchGate was not verified).
- The awesome list [Awesome-Algorithms-Against-Degeneracy](https://github.com/thisparticle/Awesome-Algorithms-Against-Degeneracy) was not inspected.

## Q3. How did X-ICP, Tuna et al. 2025, DCReg, L3E, etc. construct degeneracy ground truth?

### Takeaway
Real-world experiments in all these papers validate detection indirectly (trajectory/map error vs TLS/GT), not via labelled precision/recall. Explicit labels come only from (a) designed simulation geometry with analytically known degenerate directions (X-ICP, Tuna 2025 cylinder, DCReg reusing it) and (b) Monte-Carlo perturbation-registration tests in simulation (L3E).

### Cited Findings
- **X-ICP (Tuna et al., T-RO 2023)**: simulation environments with "smooth planar surfaces, self-similar corridors, a cylindrical room, and an open area" where degenerate directions are known from geometry; real-world reference from a Leica RTC360 TLS used "to generate ground truth map and robot trajectory"; no per-direction GT labels, validation via APE/RPE/end-position errors — [X-ICP arXiv 2211.16335](https://arxiv.org/pdf/2211.16335); [X-ICP project](https://sites.google.com/leggedrobotics.com/x-icp)
- **Tuna et al. 2025 ("Informed, Constrained, Aligned", T-RO)**: simulation with "perfectly cylindrical and symmetric mesh" and ANYmal simulated trajectories; real-world: Ulmberg tunnel, ANYmal forest open field (3-axis degeneracy), HEAP construction site; GT maps from TLS; detection deliberately simplified to a binary X-ICP-like eigen-analysis "to prevent giving an unintentional advantage"; no precision/recall for detection reported — [arXiv 2408.11809](https://arxiv.org/pdf/2408.11809); [project page](https://sites.google.com/leggedrobotics.com/perfectlyconstrained)
- **DCReg (Hu et al., IJRR 2026)**: "Following the protocol established in Tuna et al. (2025), we employ a symmetric cylinder scenario with controlled perturbations... The perturbed point cloud is registered with the original to obtain ground truth transformations with absolute accuracy"; real data FP, GEODE, SubT-MRS, self-collected; artificially limits LiDAR range (e.g., 10 m in parking lot/corridor) to induce degeneracy; reports "Degeneracy Ratio (DR)" which "serves as an indicator of detection sensitivity rather than an error metric"; detection quality argued qualitatively (FCN over-detects, ME under-detects) and via case studies (stairs: Z-degenerate going down, roll-pitch going up) — [DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285) (project copy 2509.06285v3)
- **L3E (Nubert, Walther, Khattak, Hutter, ICRA 2022)**: labels via Monte-Carlo: perturb each "parent" scan by 6-DoF Gaussian offsets (0.1 m, 5-10°), register child to parent with point-to-plane ICP, mean absolute error per direction; direction labelled non-localizable if error exceeds 0.1 m / 2°. Gazebo with simulated VLP-16, 15 environments (planes, tunnels, cylinders, meshed real caves); trained only on simulation, tested on ANYmal field data — [arXiv 2203.05698](https://arxiv.org/pdf/2203.05698); [L3E GitHub](https://github.com/leggedrobotics/L3E)

### Inferences
- Credibility ranking for labels: (1) analytic geometry in simulation (exact, but toy); (2) oracle Hessian/perturbation test at GT pose against a TLS map (real data, detector-independent); (3) sequence-level tags (GEODE); (4) drift-based (trajectory error spikes) — weakest because confounded by IMU, mitigation, and the detector itself.
- The L3E perturbation protocol is directly reusable on real datasets with GT maps: perturb GT pose, run scan-to-GT-map ICP, label direction degenerate if convergence error exceeds threshold — independent of the tested detector.

### Gaps
- No paper found that publishes a per-frame real-data degeneracy label set with precision/recall evaluation.

## Q4. Simulation options with exact geometry

### Takeaway
Gazebo with custom meshes (as in L3E/X-ICP) is the proven route; TartanGround (TartanAir family, Unreal/AirSim) now includes simulated LiDAR + IMU + stereo + occupancy maps. Original TartanAir is visual-SLAM focused; LiDAR in it was not verified.

### Cited Findings
- L3E: Gazebo + VLP-16 model, 15 environments incl. tunnels, cylinders, meshed caves — [arXiv 2203.05698](https://arxiv.org/pdf/2203.05698)
- X-ICP: simulated corridors, cylindrical room, open area with known degenerate directions — [arXiv 2211.16335](https://arxiv.org/pdf/2211.16335)
- TartanGround: Unreal Engine 4 + AirSim, 63 environments, 878 trajectories, 6 stereo RGB cameras with depth/semantics, IMU, LiDAR point clouds, semantic occupancy maps (~15 TB); tunnels/corridors not explicitly listed — [TartanGround arXiv 2505.10696](https://arxiv.org/html/2505.10696v2)
- DARPA SubT resources (virtual worlds and datasets listing) — [subt_resources Datasets](https://github.com/subtchallenge/subt_resources/blob/main/3-Datasets.md) (contents not inspected)

### Inferences
- With an occupancy map/mesh one can compute the oracle Hessian exactly per frame (no TLS noise), making simulation the cleanest labelling source; combine with a real TLS-map dataset for credibility.

### Gaps
- CARLA, Isaac Sim, and DARPA SubT virtual world LiDAR+IMU+camera releases were not verified in this pass.
- Whether original TartanAir (v1) has LiDAR was not verified (believed visual-only; UNVERIFIED).

## Q5. Drift-based vs geometry-based labels

### Takeaway
Geometry-based (oracle Hessian or perturbation test at GT pose against GT map/mesh) labels are detector-independent and give directions; drift-based labels are cheap but confounded.

### Cited Findings
- Papers rely on trajectory/map error as indirect validation (X-ICP APE/RPE; DCReg ATE + AC/CD; Tuna 2025 map distances) — [X-ICP](https://arxiv.org/pdf/2211.16335); [DCReg](https://arxiv.org/abs/2509.06285); [Tuna 2025](https://arxiv.org/pdf/2408.11809)
- DCReg explicitly notes IMU/temporal priors "can also redistribute or mask degeneracy patterns" and that degeneracy also stems from "sparse environments and poor initial poses" — [DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285)
- DCReg shows detection rate depends heavily on LiDAR range (DR 86.7% at 10 m vs 31.1% at 60 m in parking lot) — [DCReg arXiv 2509.06285](https://arxiv.org/abs/2509.06285)

### Inferences
- Drift-based pros: needs only GT poses (works on Hilti, ENWIDE); cons: drift lags degeneracy, IMU masks it, gives no direction, and depends on the estimator under test.
- Geometry-based pros: per-direction, per-frame, independent of detector; cons: requires GT map, threshold choice (eigenvalue or perturbation-error) is itself a design choice, and labels depend on scan range/downsampling — should be reported with sensitivity analysis. Range truncation (as in DCReg) is a controllable way to create degenerate variants of the same data.

### Gaps
- No published study comparing agreement between drift-based and geometry-based labels was found.
