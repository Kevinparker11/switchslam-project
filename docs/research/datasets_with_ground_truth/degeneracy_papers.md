# Degeneracy detection/mitigation papers: datasets, ground truth, key results

Scope note: Tool budget limited this pass to ~18 calls. One fetch failed: the arXiv HTML page for DCReg v3 (https://arxiv.org/html/2509.06285v3) was rate-limited (HTTP 429) and not read; DCReg details below come instead from the DCReg v3 PDF stored in the user's "Switch , QR" project (file `2509.06285v3.pdf`). Switch-SLAM details come from the project's `SwitchSLAM.pdf` (RA-L 2024, DOI 10.1109/LRA.2024.3421792). Papers listed in the brief but NOT verified in this pass are listed under Gaps and should not be cited from these notes.

## Q1. Per-paper catalogue: datasets/sequences, GT source, metric, where the method wins big vs ties

### Takeaway
The verified papers split into two camps: (a) registration-level degeneracy papers (X-ICP, Tuna et al. field study, DCReg, LP-ICP) that evaluate on their own field data or on public sets (SubT-MRS, GEODE, FusionPortable, CERBERUS) with survey-scanner / RTK / GNSS GT and ATE/RPE; (b) LiDAR-visual systems (Switch-SLAM) that use Gazebo sims plus Handheld, CERBERUS and SubT-MRS Multi Floor / Long Corridor. Large margins appear almost only in strongly degenerate segments (caves with aggressive motion, open fields, long corridors, range-limited scans); in well-constrained scenes methods tie.

### Cited Findings

**DCReg: Decoupled Characterization for Efficient Degenerate LiDAR Registration** (Hu, Chen, Jia, Wu, Tan, Waslander; arXiv 2509.06285; v3 formatted for IJRR) — [arXiv](https://arxiv.org/abs/2509.06285)
- Datasets: simulated symmetric cylinder (7600 pts, protocol from Tuna et al. 2025; GT = known perturbation); real: FusionPortable (Corridor, Building; OS128), GEODE (Stairs; OS64), SubT-MRS (Cave01, Cave02, Cave04; VLP16, handheld), and self-collected "MS" Parking Lot (Pandar XT-32) with RTK-INS GT. Range is artificially limited in some sequences (e.g., parking lot, corridor) to induce degeneracy. — project PDF `2509.06285v3.pdf`, Sec. 7.1.1 and Table 2 ([arXiv](https://arxiv.org/abs/2509.06285))
- Baselines: ME (min eigenvalue, Zhang et al. 2016), FCN (full condition number, Hinduja et al. 2019), CN (relative condition number, Hu et al. 2024b), combined with SR / TSVD / TReg mitigation; plus X-ICP, SuperLoc, Open3D ICP. Each is integrated into a 5 s sliding-window fixed-lag smoother with FAST-LIO2-style LIO; scan-to-map registration. Thresholds: κth = 10, min-eigenvalue 120, X-ICP 300/150. — project PDF Sec. 7.1.2
- Metrics: degeneracy ratio (DR, % frames flagged), ATE (cm), map accuracy AC (cm), time (ms). No precision/recall of detection against labels was found in the retrieved text. — project PDF Tables 4–5
- Table 5 (large margins): Cave02 ATE — DCReg 4.57 cm vs ME-SR 565.61, ME-TSVD 497.05, ME-TReg 209.53, FCN-SR 491.29, O3D 16.88, odometry 129.78; text says "cave02 involve aggressive motion patterns where most baseline methods fail entirely". Parking Lot (10 m range limit) ATE — DCReg 29.56 vs ME-TSVD 30.46 (near tie), ME-SR 62.11, FCN-SR 64.50. — project PDF Table 5
- Table 4: Stairs (GEODE) ATE — DCReg 3.96 cm vs ME-TSVD 6.44, ME-TReg 7.16, ME-SR 160.75, FCN-SR 280.07; Corridor (FP) — DCReg 7.44 vs ME-TReg 26.24, ME-TSVD 94.32; Building (FP, well-constrained) — all ≈8.6 cm (tie) except FCN-SR 299.46 (over-detection, DR 99.23%). — project PDF Table 4
- Claims 5–30x (up to 116x) speedup; "ME fail to detect degeneracy" in range-limited parking lot because rotational eigenvalues are larger than translational ones (scale disparity). — project PDF Sec. 7.3

**X-ICP: Localizability-Aware LiDAR Registration for Robust Localization in Extreme Environments** (Tuna, Nubert, Nava, Khattak, Hutter; arXiv 2211.16335; IEEE T-RO 2024, IEEE doc 10328716) — [arXiv](https://arxiv.org/abs/2211.16335v4), [IEEE](https://ieeexplore.ieee.org/document/10328716)
- Datasets: 3 simulated scenes (semi-circular tunnel, cylindrical room, corridor+open space 246 m; known GT); Seemühle underground mine (521.8 m, ANYmal-C, VLP-16 and OS0-128; GT from Leica RTC360 scanner map); Rümlang construction site (153 m; no GT stated, map consistency only); Opfikon city park (235 m; GT Leica RTC360). All self-collected, not a standard public benchmark. — [arXiv HTML](https://arxiv.org/html/2211.16335v4)
- Metrics: APE, RPE per 10 m, point-to-map distance, end-position error. Baselines: Zhang et al. solution remapping; Hinduja et al. relative condition number. — [arXiv HTML](https://arxiv.org/html/2211.16335v4)
- Key numbers (Seemühle VLP-16): APE 2.45 m / 2.50° (X-ICP) vs 3.73 m / 4.11° (Zhang) vs 8.16 m / 8.03° (Hinduja); last-position error 0.27 m vs 6.37 m vs 24.17 m; RPE/10 m 0.17 vs 0.20 vs 0.26 m (smaller gap locally). — [arXiv HTML](https://arxiv.org/html/2211.16335v4)
- Detection not scored against GT labels (no precision/recall); validated qualitatively against geometry and via drift. — [arXiv HTML](https://arxiv.org/html/2211.16335v4)

**Informed, Constrained, Aligned: A Field Analysis on Degeneracy-aware Point Cloud Registration in the Wild** (Tuna, Nubert, Pfreundschuh, Cadena, Khattak, Hutter; arXiv 2408.11809) — [arXiv](https://arxiv.org/abs/2408.11809)
- Datasets: simulated static cylinder mesh (rotation degeneracy) and dynamic ANYmal sim around a pillar (3-axis); real: Ulmberg bicycle tunnel (handheld ENWIDE payload, OS1-128), ANYmal forest/open field (VLP-16), HEAP walking excavator construction site (OS0-128). GT: Leica BLK2GO scanner maps (handheld), GNSS (ANYmal forest), known transforms in sim; satellite imagery used for trajectory checks. — [arXiv HTML](https://arxiv.org/html/2408.11809v1)
- Compared: equality constraints, inequality constraints, TSVD, Tikhonov (linear and non-linear), solution remapping (Zhang 2016); passive: prior-only, Cauchy M-estimator, global registration (Quatro, FGR); baseline point-to-plane ICP. Detection = X-ICP localizability. — [arXiv HTML](https://arxiv.org/html/2408.11809v1)
- Results: Ulmberg best Ineq. Con. RTE 0.033 m; ANYmal forest best NL-Reg RTE 0.039 m, ATE 0.364 m; Eq. Con., TSVD and Ineq. Con. "performed similarly"; global registration fails in symmetric scenes; active methods beat passive; constraint-before/during-optimization beats post-hoc remapping. — [arXiv HTML](https://arxiv.org/html/2408.11809v1) (summary from fetch tool; exact per-method numbers for losers not extracted)
- Labels: degeneracy defined by environment geometry, not manual frame annotation. — [arXiv HTML](https://arxiv.org/html/2408.11809v1)

**LP-ICP: General Localizability-Aware Point Cloud Registration for Robust Localization in Extreme Unstructured Environments** (arXiv 2501.02580) — [arXiv](https://arxiv.org/abs/2501.02580)
- Datasets: PLAM simulated lunar-like set (AirSim/UE4, 10 seqs, 10 km; exact GT); CERBERUS DARPA SubT (Louisville Mega Cavern, ANYmal 1–4); SubT-MRS Long Corridor. — [arXiv HTML v3](https://arxiv.org/html/2501.02580v3)
- Metric: ATE RMSE (evo), completion ratio. Baselines: Zhang et al., X-ICP, plus VINS-Mono, ORB-SLAM3, LIO-SAM, R3LIVE. — [arXiv HTML v3](https://arxiv.org/html/2501.02580v3)
- Results: PLAM a2_traverse 12.31 m vs X-ICP 36.75, Zhang 36.60 (3x); a3_odom 7.44 vs 18.08 / 16.91; but a4_home LP-ICP 5.66 vs X-ICP 3.85 (X-ICP better); CERBERUS ANYmal 2: 0.24 vs 0.32 / 0.44, ANYmal 3: 0.37 vs 0.56 / 0.50; ties on ANYmal 1, 4 and feature-rich PLAM sequences; SubT-MRS Long Corridor 11.92 m vs X-ICP 19.63, Zhang 24.71. No detection precision/recall. — [arXiv HTML v3](https://arxiv.org/html/2501.02580v3)

**Switch-SLAM: Switching-Based LiDAR-Inertial-Visual SLAM for Degenerate Environments** (Lee, Komatsu, Shinozaki, Kitajima, Asama, An, Yamashita; IEEE RA-L 9(8), 2024; DOI 10.1109/LRA.2024.3421792) — [DOI](https://doi.org/10.1109/LRA.2024.3421792), [IEEE](https://ieeexplore.ieee.org/document/10582434)
- Datasets: Gazebo sims (Fast Rotate, Plane, Farm; VLP-16 + camera + IMU, clearpath cpr_gazebo worlds); Handheld dataset (ref [11], open-field LiDAR degeneracy); CERBERUS DARPA SubT ANYmal 1–4 with LiDAR horizontal FOV artificially cut to 180° to induce degeneracy, cam1 only; SubT-MRS Multi Floor and Long Corridor. No GNSS or loop closure; averages over 3 runs. — project PDF `SwitchSLAM.pdf` Sec. IV-A
- Metric: absolute translational error (max, RMSE), Table II. Baselines: LOAM, LIO-SAM, VINS-Mono, R2LIVE, R3LIVE, FAST-LIVO, LVI-SAM. — project PDF
- Wins/ties: best on Multi Floor and Long Corridor ("structure-less and visually challenging" simultaneously), Farm, ANYmal 1–3; competitive with LIO-SAM on Fast Rotate; tie with LVI-SAM on Handheld ("few LiDAR SLAM degeneracy phases"). Numerical Table II values were not extracted in this pass. — project PDF Sec. IV-B
- Detection evaluation: GT labels built "by comparing GNSS data with scan-to-scan matching using ICP at each keyframe" on part of the Handheld dataset; accuracy 0.91 (Zhang-type min-eigenvalue [16], thr 100), 0.96 (condition-number [17], thr 10), 0.96 (Switch-SLAM); recall 0.91 / 0.96 / 0.99. — project PDF Sec. IV-C

**DRPM: Probabilistic Degeneracy Detection for Point-to-Plane Error Minimization** (arXiv 2410.10784; listed as RA-L 2024; code github.com/ntnu-arl/drpm) — [arXiv](https://arxiv.org/abs/2410.10784), [Awesome list](https://github.com/thisparticle/Awesome-Algorithms-Against-Degeneracy)
- Models Hessian noise from point and normal uncertainty (datasheet noise) to give a probability of degeneracy per direction; "four real-world experiments". Datasets, GT and numbers were not retrieved (abstract only). — [arXiv](https://arxiv.org/abs/2410.10784)

**PALoc (Hu et al.)** — verified as "PALoc: Advancing SLAM Benchmarking with Prior-Assisted 6-DoF Trajectory Generation and Uncertainty Estimation" (arXiv 2401.17826; earlier version 2305.13147) — [arXiv](https://arxiv.org/abs/2401.17826), [RAM-LAB PDF](https://ram-lab.com/papers/2024/PALoc.pdf)
- It is a prior-map-based GT trajectory generation method (relevant to how DCReg's author group produces GT), not primarily a degeneracy detector. DCReg cites "Hu et al. (2024b)" both for the CN (relative condition number) baseline and for the fixed-lag smoother; whether 2024b is PALoc was not confirmed. Its own datasets/numbers were not retrieved.

### Inferences
- Large-margin environments across papers: narrow caves with aggressive motion (DCReg Cave02), open/featureless fields (LP-ICP a2_traverse; Switch-SLAM Plane/Farm), long tunnels/corridors (X-ICP Seemühle end-point error; LP-ICP and Switch-SLAM on SubT-MRS Long Corridor), and artificially range- or FOV-limited scans (DCReg parking lot/corridor; Switch-SLAM CERBERUS 180° FOV). Well-constrained buildings and feature-rich sequences show ties.
- Several papers induce degeneracy artificially (range limit, FOV cut), so "degenerate" public sequences are often not degenerate enough unmodified.

### Gaps
- Not verified in this pass (do not cite from these notes): Zhang & Singh 2016 datasets (paper exists, ICRA 2016, [IEEE](https://ieeexplore.ieee.org/document/7487211) per Awesome list, but its experiments were not read); Hinduja et al. 2019 IROS ([IEEE](https://ieeexplore.ieee.org/document/8968577/), experiments not read); DARE-SLAM (Ebadi et al.); SuperOdometry / SuperLoc; LVI-SAM, R2LIVE, R3LIVE, FAST-LIVO2 dataset details; GenZ-ICP (arXiv 2411.06766), Point-to-distribution degeneracy factor (ICRA 2024), COIN-LIO, RELEAD (listed in the Awesome list but not read); Nubert/Khattak normal-based measures.
- "LF-GICP: Parameter-Free Degeneracy-Aware LiDAR Odometry via a Voxel-Normal Localizability Field" (arXiv 2608.19522) appeared in a search result but was not opened; treat as unverified.
- Switch-SLAM Table II RMSE values and DCReg Table 3 (simulation) were not extracted.

## Q2. Which datasets recur?

### Takeaway
Among verified papers, SubT-MRS (3 of 5: DCReg, LP-ICP, Switch-SLAM) and CERBERUS DARPA SubT ANYmal 1–4 (2: LP-ICP, Switch-SLAM) recur most; GEODE and FusionPortable appear in DCReg; ETH papers (X-ICP, Tuna field study) use their own field data (Seemühle mine, ENWIDE/Ulmberg tunnel, forest, HEAP). Hilti and Newer College did not appear in any verified paper's experiments.

### Cited Findings
- SubT-MRS: DCReg (Cave01/02/04), LP-ICP (Long Corridor), Switch-SLAM (Multi Floor, Long Corridor). — project PDFs; [LP-ICP](https://arxiv.org/html/2501.02580v3)
- CERBERUS ANYmal 1–4: LP-ICP, Switch-SLAM. — [LP-ICP](https://arxiv.org/html/2501.02580v3); project `SwitchSLAM.pdf`
- GEODE (arXiv 2409.04961): 8 environment types (flat surfaces, stairs, two metro tunnel types, bridges, urban tunnels, inland waterways, off-road); Velodyne/Ouster/Livox; GT = GNSS/INS-RTK outdoors, Leica MS60 total station indoors, Vicon on flat surfaces, Leica RTC360 for stairway GT maps; difficulty tags (Easy/Medium/Hard) but no per-frame degeneracy labels. — [GEODE site](https://thisparticle.github.io/geode/), [arXiv](https://arxiv.org/abs/2409.04961)
- SubT-MRS GT: "all ground truth models were captured using a FARO scanner, guaranteeing an accuracy within 10 cm"; GT models shown for Long Corridor, Multi Floor, Campus Outdoor, Campus Indoor; sequences tagged by degradation type (low light, textureless, structureless, smoke/snow, aggressive motion, repetitive features). — [CVPR 2024 supplemental](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Zhao_SubT-MRS_Dataset_Pushing_CVPR_2024_supplemental.pdf)
- The Awesome-Algorithms-Against-Degeneracy list (maintained by GEODE authors) lists GEODE and SubT-MRS as the degeneracy datasets. — [GitHub](https://github.com/thisparticle/Awesome-Algorithms-Against-Degeneracy)

### Inferences
- For a method comparable to DCReg/Switch-SLAM, SubT-MRS (Cave, Multi Floor, Long Corridor) plus GEODE (stairs, tunnels) plus CERBERUS gives the most directly comparable numbers.

### Gaps
- Use of Hilti, Newer College, ENWIDE (as a public dataset) and FusionPortable in other degeneracy papers not checked.

## Q3. Papers that score detection accuracy against labels

### Takeaway
Only Switch-SLAM (among verified papers) reports detection accuracy/recall against labels, and its labels come from GNSS vs. ICP scan-to-scan disagreement (outcome-based), on part of one dataset. X-ICP, Tuna et al., LP-ICP and DCReg do not report detection precision/recall against labels; they use geometry-implied degeneracy or downstream ATE.

### Cited Findings
- Switch-SLAM: labels from GNSS vs ICP scan-to-scan per keyframe on Handheld; accuracy 0.91/0.96/0.96, recall 0.91/0.96/0.99 (min-eigenvalue / condition number / proposed), thresholds swept (50/100/200 and 5/10/15). — project `SwitchSLAM.pdf` Sec. IV-C, [DOI](https://doi.org/10.1109/LRA.2024.3421792)
- X-ICP: no GT localizability labels; qualitative. — [arXiv HTML](https://arxiv.org/html/2211.16335v4)
- Tuna et al. field study: degeneracy by environment geometry. — [arXiv HTML](https://arxiv.org/html/2408.11809v1)
- LP-ICP: "no quantitative evaluation of detection accuracy" (qualitative figures only). — [arXiv HTML v3](https://arxiv.org/html/2501.02580v3)
- DCReg: reports degeneracy ratio per method, not precision/recall; argues ME under-detects and FCN over-detects (FCN DR 99.23% on non-degenerate Building). — project `2509.06285v3.pdf` Table 4

### Inferences
- Geometry-based (non-outcome) labels on real data are essentially absent from the verified literature; simulation with known meshes (X-ICP, Tuna, DCReg cylinder) is the only place GT degeneracy is exact.

### Gaps
- DRPM may include a detection-quality evaluation; not checked.

## Q4. SubT-MRS Multi Floor / Cave: what GT did papers use?

### Takeaway
SubT-MRS supplies FARO-scanner GT models (≤10 cm) for Multi Floor and Long Corridor; Switch-SLAM used Multi Floor and Long Corridor and reported ATE against dataset GT; DCReg used Cave01/02/04 but the GT source for caves was not stated in the retrieved text.

### Cited Findings
- SubT-MRS GT: FARO scanner, within 10 cm; GT models shown for Long Corridor and Multi Floor; Cave GT not confirmed in the supplemental. — [CVPR 2024 supplemental](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Zhao_SubT-MRS_Dataset_Pushing_CVPR_2024_supplemental.pdf)
- Switch-SLAM evaluated Multi Floor and Long Corridor with absolute translational error. — project `SwitchSLAM.pdf`
- LP-ICP used SubT-MRS Long Corridor, GT described as from the challenge dataset. — [arXiv HTML v3](https://arxiv.org/html/2501.02580v3)
- DCReg used Cave01/02/04 (handheld, VLP16) for scan-to-map localization with ATE. — project `2509.06285v3.pdf` Table 2/5

### Inferences
- DCReg's scan-to-map setup requires a prior map; the DCReg group (Hu et al.) authored PALoc, a prior-map-based GT generation pipeline, so cave GT may be PALoc-style map-based. This is an inference, not verified.

### Gaps
- Exact GT trajectory pipeline for SubT-MRS (how FARO maps become 6-DoF trajectories) and whether Cave sequences have GT; a "Ground Truth Trajectory Generation For SubT-MRS Dataset" presentation exists ([Symposium](https://symposium.foragerone.com/meeting-of-the-minds-2023/presentations/53492)) but was not read.
