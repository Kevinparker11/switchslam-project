# How published papers evaluate LiDAR degeneracy DETECTION in isolation: labels, metrics, datasets, simulators

Access notes: arxiv.org/html/2509.06285 (DCReg) and arxiv.org/html/2608.19522 (LF-GICP) were refused by the fetch proxy (HTTP 429). For DCReg, the project copy of the PDF (2509.06285v3, IJRR-format preprint) was used instead. LF-GICP was seen only as a search-result title. Direct curl to arXiv was blocked (403). Most per-paper details below come from WebFetch summaries of the arXiv HTML or ar5iv pages, not from a full manual read, so check exact numbers against the PDFs before quoting them in the thesis.

## Q1. Which papers report detection metrics against labels, and how were the labels made?

### Takeaway
Only one verified paper scores a degeneracy detector against per-direction ground-truth labels with classification metrics: Nubert et al. (L3E, arXiv 2203.05698). Its labels come from Gazebo simulation, by Monte-Carlo perturbing poses and thresholding the resulting registration error. Every other verified paper evaluates detection indirectly. They use one of three things: downstream ATE/RPE/map error; a "degeneracy ratio" (the share of frames flagged); or qualitative per-direction timelines in environments whose degenerate directions are known by construction (a tunnel or cylinder).

### Cited Findings
**L3E: Nubert, Walther, Khattak, Hutter, "Learning-based Localizability Estimation for Robust LiDAR Localization", arXiv 2203.05698 (ICRA 2022; venue from memory, not confirmed on the fetched page)**
- Trained only on simulated data. Labels were generated in Gazebo with a simulated Velodyne VLP-16. Parent clouds were sampled along hand-drawn paths through 15 environments: tunnels, cylinders, planes, and meshed caves from CAD or downsampled real cave scans. — [ar5iv 2203.05698](https://ar5iv.labs.arxiv.org/html/2203.05698)
- Labelling procedure:
  - Child scans were made by Monte-Carlo sampling 6 per-direction perturbations from zero-mean Gaussians (about 0.1 m translation, 5–10° rotation), with a fresh ray-cast for each child pose.
  - Each child was registered against its parent.
  - A direction was labelled localizable when the expected registration error stayed below 0.1 m in translation or 2° in rotation (a binary label per DoF). — [ar5iv 2203.05698](https://ar5iv.labs.arxiv.org/html/2203.05698)
- Detection metrics on the held-out test set (a tunnel mesh), averaged over the 6 DoF: accuracy 0.854, F1 0.517, precision 0.398, recall 0.752. Per-direction results were better for x, y and yaw than for z, roll and pitch, which the authors attribute to class imbalance. — [ar5iv 2203.05698](https://ar5iv.labs.arxiv.org/html/2203.05698)
- Baseline: the Zhang & Singh eigenvalue thresholds {30, 90, 110} inside CompSLAM. The paper says detection is "on par with state-of-the-art methods after environment-specific threshold tuning". — [arXiv abs](https://arxiv.org/abs/2203.05698); [ar5iv](https://ar5iv.labs.arxiv.org/html/2203.05698)
- Real-world tests ran on ANYmal with a VLP-16 in a mine tunnel, a paved worksite and urban corridors. The page documents no IMU use in detection. — [ar5iv 2203.05698](https://ar5iv.labs.arxiv.org/html/2203.05698)

**X-ICP: Tuna, Nubert, Nava, Khattak, Hutter, arXiv 2211.16335 (T-RO 2024; venue from memory)**
- Detection outputs one of three categories (none / partial / full localizability) per eigen-direction and per DoF. It is evaluated qualitatively, through over-time localizability plots (Figs. 8–14). — [arXiv html 2211.16335](https://arxiv.org/html/2211.16335)
- Simulation cases with degenerate directions known by construction: a semi-circular tunnel (translational degeneracy along its axis), a cylindrical room (rotational degeneracy about the vertical axis), and a 246 m corridor → open space → corridor path. — [arXiv html 2211.16335](https://arxiv.org/html/2211.16335)
- Real data: the Seemühle mine (521.8 m), the Rümlang construction site (153 m) and Opfikon City Park (235 m). Reference maps came from a Leica RTC360 scanner. Metrics were APE, RPE per 10 m, map error and end-position error. The paper does not report precision or recall for detection. — [arXiv html 2211.16335](https://arxiv.org/html/2211.16335)

**Tuna et al., "Informed, Constrained, Aligned: A Field Analysis on Degeneracy-aware Point Cloud Registration in the Wild", arXiv 2408.11809 (ETH Research Collection record)**
- All mitigation methods share one detector: X-ICP simplified to binary localizable / non-localizable. Thresholds were κ1=300, κ2=150, κ3=45 and κf=80 (60 in one experiment). Detection is not evaluated on its own: there are no ground-truth labels and no precision, recall or F1. — [arXiv pdf 2408.11809](https://arxiv.org/pdf/2408.11809); [ETH record](https://www.research-collection.ethz.ch/handle/20.500.11850/744619)
- Platforms: ANYmal with a VLP-16, the HEAP excavator with an Ouster OS0-128, and a handheld Ouster OS1-128. The fetched summary says IMU is not used for detection. — [arXiv pdf 2408.11809](https://arxiv.org/pdf/2408.11809)

**DCReg: Hu, Chen, Jia, Wu, Tan, Waslander, arXiv 2509.06285 (IJRR-format preprint; project copy v3)**
- Baseline detection methods: ME (minimum eigenvalue, Zhang 2016), FCN (full condition number, Hinduja 2019) and CN (relative condition number, Hu 2024b). Complete-solution baselines include X-ICP, ME-TSVD/TReg (Tuna 2025), FCN-SR and O3D. — project file 2509.06285v3.pdf, §7.1.2 ([arXiv abs](https://arxiv.org/abs/2509.06285))
- Detection metric: the **Degeneracy Ratio (DR)**, the percentage of frames flagged. The authors state that DR "serves as an indicator of detection sensitivity rather than an error metric." The paper has no labelled precision or recall. — 2509.06285v3 §7.1.2
- Detection analysis (§7.4.1) has three parts: a timeline of which eigen-directions are flagged per frame (Fig. 12, parking lot); Schur versus diagonal condition numbers with threshold 10 (Fig. 13), showing rotational degeneracy that diagonal methods mask; and per-direction and overall DR across methods (Fig. 14). — 2509.06285v3
- Example DRs from Table 5:
  - Cave02: Ours 32.90%, FCN-SR 58.89%, ME-SR 6.47%.
  - Parking lot: Ours 86.74%, FCN-SR 98.15%.
  - Corridor ablation: DR 58.04%.
  Correctness is argued from ATE and map accuracy (AC, Chamfer distance), not from labels. — 2509.06285v3 Tables 5 and 9
- Simulation protocol, "following Tuna et al. (2025)": a symmetric cylinder scene with controlled perturbations. The perturbed cloud is registered to the original, which gives ground-truth transforms. — 2509.06285v3 §7.1.1
- Degeneracy is induced deliberately by artificially limiting LiDAR range to 10 m in the parking lot and corridor sequences. — 2509.06285v3 §7.1.1
- Registration-level evaluation is LiDAR-only point-to-plane ICP. System-level evaluation uses a 5 s sliding-window fixed-lag smoother. The authors list prior coupling with IMU or Kalman-filter/factor-graph systems as future work, noting that "Strong priors from IMU ... can also redistribute or mask degeneracy patterns." — 2509.06285v3 §7.1.3, §9

**Hatleskog & Alexis, "Probabilistic Degeneracy Detection for Point-to-Plane Error Minimization", arXiv 2410.10784**
- No standalone detection metrics or ground-truth labels. Evaluation is end-to-end on four real datasets from legged and aerial robots: Rümlang, Seemühle, Trondheim and Fyllingsdalen. Baselines include Deschaud 2018 and Lin et al. 2022. — [arXiv html 2410.10784v2](https://arxiv.org/html/2410.10784v2)

**LP-ICP: "General Localizability-Aware Point Cloud Registration for Robust Localization in Extreme Unstructured Environments", arXiv 2501.02580**
- Classifies each DoF into three levels (fully / partially / non-localizable) from point-to-line and point-to-plane Jacobian projections onto eigenvectors. Compared against Zhang's degeneracy factor and X-ICP on a simulated lunar-like environment (10 sequences, 10 km) and on CERBERUS DARPA SubT data. The fetched content shows no detection precision or recall. — [ar5iv 2501.02580](https://ar5iv.labs.arxiv.org/html/2501.02580); [arXiv abs](https://arxiv.org/abs/2501.02580)

**SuperLoc: Zhao et al., arXiv 2412.02901**
- Alignment-risk prediction is shown qualitatively, with per-axis confidence histograms and observability-colored scans. It is assessed indirectly through outlier percentage against FARO ground truth (10 cm), ATE and robustness metrics. The paper reports no precision, recall or AUC for the predictor. It uses an IMU preintegration factor. Data: 8 SubT-MRS sequences plus Laurel Caverns. — [arXiv html 2412.02901v1](https://arxiv.org/html/2412.02901v1/)

**LiLi: "Lie Theory Based 3D LiDAR Scan Alignment Degeneracy Detection", arXiv 2609.17145 (2026)**
- Not evaluated as classification. It uses an alignment-quality metric (the median NN distance of the scan extended along detected twists) on 5 synthetic shapes: a plane, closed and open cylinders, a sinusoidal cylinder and a rotating tunnel. It also reports ATE and RPE inside LIO-SAM on a custom tunnel with total-station ground truth. The only detection baseline is Zhang's Hessian method. — [arXiv html 2609.17145v2](https://arxiv.org/html/2609.17145v2)

**Switch-SLAM: Lee et al., RA-L 9(8), Aug 2024, pp. 7270–7277**
- The detector uses the 3 smallest eigenvalues of H_l, L2-normalized and tested against semicircle-distribution expectations with a χ² (2 DoF, 0.103) threshold, giving λt=[0.12, 0.27, 0.48]. Evaluation runs on simulated Plane, Fast Rotate and Farm datasets (ROS/Gazebo), where the degenerate regions are marked by construction (Fig. 5), plus real data. The paper is LiDAR-inertial-visual. — project file SwitchSLAM.pdf

### Inferences
- The only published, reproducible protocol for scoring detection directly is L3E's perturbation-at-known-pose labelling in simulation. Combined with DCReg's and Tuna's "register a perturbed copy against the original" cylinder protocol, it gives a defensible ground-truth generator that does not depend on the detector. The thesis could apply the L3E-style rule (Monte-Carlo perturb the true pose per direction, run ICP against the ground-truth map, label a direction degenerate if the error exceeds 0.1 m or 2°) to Gazebo and to real datasets with ground-truth maps, then report per-DoF precision, recall, F1 and AUC.
- DCReg's DR is a sensitivity indicator only. A thesis claiming detection correctness needs labels, not DR alone.
- Most papers evaluate the registration in a LiDAR-only way, sometimes with an IMU in the full system. To isolate the detector, use scan-to-map ICP at the ground-truth pose with no IMU prior.

### Gaps
- No verified 2024–2026 paper was found that reports detection precision and recall against geometric labels on public real-world data. L3E's metrics are simulation-only.
- Zhang & Singh 2016 (ICRA, "On degeneracy of optimization-based state estimation problems"), Hinduja et al. 2019 (IROS, degeneracy-aware factors for underwater SLAM), Ebadi DARE-SLAM, GenZ-ICP, RELEAD ([arXiv 2402.18934](https://arxiv.org/html/2402.18934v2), cited in DCReg as ICRA 2024, DOI 10.1109/ICRA57147.2024.10611074), and COIN-LIO's own degeneracy analysis were not fetched in this session. Treat their evaluation protocols as unverified. From memory (unverified), none of them reports labelled detection precision or recall.
- The fetched pages did not confirm the exact L3E venue or the X-ICP T-RO volume.

## Q2. Which public datasets (LiDAR + IMU + ground truth) were used for degeneracy evaluation?

### Takeaway
Public datasets with LiDAR, IMU, accurate ground truth and deliberate degeneracy include:
- **GEODE** (64 sequences, 7 degenerate scenario types, three LiDAR types, ground-truth maps for stairs)
- **ENWIDE** (Ouster OS0-128, built-in IMU, Leica MS60 total station)
- **SubT-MRS**
- **FusionPortable**
- **CERBERUS / DARPA SubT** data

DCReg used FP, GEODE and SubT-MRS. Simulated environments are Gazebo tunnels, cylinders and planes (L3E, X-ICP, Switch-SLAM) and a lunar-like simulation (LP-ICP).

### Cited Findings
- **GEODE** (Chen, Qi, Feng, Zhuang, Chen, Hu, Wu, Peng, Lu): published in IJRR (2026) with DOI 10.1177/02783649251344967, and on arXiv as 2409.04961.
  - Sensors: Velodyne VLP-16, Ouster OS1-64, Livox AVIA, an Xsens MTi-30 IMU at 100 Hz, and stereo cameras.
  - Ground truth: GNSS-RTK/INS, a Leica MS60 laser tracker (metro tunnels), Vicon (flat surfaces), and Leica RTC360 scanner maps (stairs).
  - 64 sequences over 7 scenario types: flat surfaces (2), stairs (3), metro tunnels (23), off-road (21), inland waterways (9), urban tunnels (3), bridges (3).
  - Degeneracy is characterized per scenario as translational, rotational or combined. These are scenario-level descriptions, not per-frame labels.
  - Website: https://geode.github.io
  — [arXiv html 2409.04961v1](https://arxiv.org/html/2409.04961v1); [SAGE](https://journals.sagepub.com/doi/10.1177/02783649251344967); [GitHub](https://github.com/PengYu-Team/GEODE_dataset)
- **ENWIDE** (ETH ASL, associated with COIN-LIO, ICRA 2024):
  - Sensors: Ouster OS0-128 at 10 Hz and its internal IMU at 100 Hz.
  - Ground truth: Leica MS60 total station tracking a prism on the LiDAR, in TUM-format CSV.
  - Environments: Intersection, Runway, Field, Tunnel and Katzensee, each with smooth and dynamic sequences, targeting "large sections of degenerate geometry".
  - DOI 10.3929/ethz-c-000787551.
  — [ENWIDE page](https://projects.asl.ethz.ch/datasets/enwide/); [COIN-LIO arXiv 2310.01235](https://arxiv.org/html/2310.01235v3)
- DCReg's real-world data: FusionPortable (Jiao 2022; Wei 2024), GEODE, SubT-MRS (Zhao 2024), and self-collected MS sequences (Pandar XT-32 with RTK-INS ground truth). The Cave02 and parking lot scenes have ground-truth maps of 53M and 218M points. — 2509.06285v3 §7.1.1 and Table 5
- SuperLoc used 8 SubT-MRS sequences plus Laurel Caverns, with FARO ground-truth maps. — [arXiv 2412.02901](https://arxiv.org/html/2412.02901v1/)
- LP-ICP used CERBERUS DARPA SubT data and a simulated lunar environment (PLAM, 10 sequences). — [ar5iv 2501.02580](https://ar5iv.labs.arxiv.org/html/2501.02580)
- The X-ICP field sites (Seemühle mine, Rümlang, Opfikon) have Leica RTC360 ground-truth maps. Their public availability was not verified. — [arXiv 2211.16335](https://arxiv.org/html/2211.16335)

### Inferences
- For L3E-style perturbation labelling on real data, the thesis needs dense ground-truth maps, not just trajectories. Candidates are GEODE's stairs (RTC360 maps), DCReg's Cave02 and parking lot maps (via FP or SubT-MRS), and SubT-MRS FARO maps. ENWIDE has a total-station trajectory but no confirmed ground-truth map. It suits trajectory-consistency checks: label a frame degenerate if LiDAR-only ICP drifts along a direction relative to the total-station pose.
- Range-limiting (DCReg's 10 m crop) is a published, controllable way to induce degeneracy on otherwise well-constrained data.

### Gaps
- It was not verified which GEODE, FP or SubT-MRS sequences ship dense ground-truth maps under licenses that allow redistribution.
- No public dataset found provides per-frame, per-direction degeneracy labels.

## Q3. Has any paper evaluated a normal-distribution / orientation-tensor measure? With what results?

### Takeaway
No verified paper evaluated a surface-normal distribution or orientation-tensor degeneracy measure against labels. LP-ICP uses normals only through point-to-plane Jacobians. A 2026 arXiv paper, LF-GICP (2608.19522, "voxel-normal localizability field"), is the closest match by title, but its content could not be read.

### Cited Findings
- LP-ICP incorporates normal-vector information through point-to-plane and point-to-line correspondences when computing per-direction localizability contributions. These contributions are Jacobian projections, not a normal-covariance or orientation-tensor statistic. — [ar5iv 2501.02580](https://ar5iv.labs.arxiv.org/html/2501.02580)
- LF-GICP, "Parameter-Free Degeneracy-Aware LiDAR Odometry via a Voxel-Normal Localizability Field", appears as arXiv 2608.19522. Its HTML was refused (HTTP 429), so its method, metrics and results are unverified. — [arXiv html 2608.19522](https://arxiv.org/html/2608.19522); [Pith listing](https://pith.science/paper/2608.19522)
- LiLi does not analyze normals; it works on raw points. — [arXiv 2609.17145v2](https://arxiv.org/html/2609.17145v2)
- Point-to-plane Hessians are built from normals. The translational block H_tt is the sum of n·nᵀ over correspondences, so a normal scatter or orientation tensor is (up to weighting) the translational information block. This project's own notes (claude/SLAM_Degeneracy_Final_Methods_With_Proofs.md) already record "Channel T ... is exactly H_tt/N". That is a project derivation, not a published result.

### Inferences
- Because the normal orientation tensor (1/N)Σ n nᵀ equals S_tt-like information before the Schur correction, a thesis "Channel T" based on it is mostly redundant with DCReg's translational block. It would need to show added value on labelled data, for example on rotation-coupled cases, or by being robust to correspondence-weighting effects. No published result supports or refutes such a channel.

### Gaps
- GenZ-ICP (planarity-based adaptive weighting; arXiv 2411.06766 from memory) and RELEAD (arXiv 2402.18934) may use normal or planarity statistics. They were not verified here.
- No published detection precision or recall was found for any normal-distribution measure.
