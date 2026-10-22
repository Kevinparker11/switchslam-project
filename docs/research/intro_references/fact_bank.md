# Fact Bank: Introduction (LiDAR degeneracy detection paper)

Built: 2026-10-11. Builds on `verified_refs.md` (bibliographic data) and `review.md` (draft check).

Reference numbers: the bracketed numbers in section headings are the `verified_refs.md` numbers. The old draft numbered references differently (for example, DCReg was [18] and Switch-SLAM was [21]), so match on names, not numbers.

## How to read this file

Each fact gives three things: a short exact quote (30 words or fewer), where it appears, and the source.

Source tags:
- **[PF]**: claude.ai Project file, read in full with `project_read`. The text is exact apart from PDF line-break artefacts.
  - `2509.06285v3.pdf` = DCReg, arXiv v3.
  - `SwitchSLAM.pdf` = the RA-L published version.
- **[LP]**: a local copy of the authors' PDF, extracted with `pdftotext`. The text is exact.
- **[WF]**: WebFetch of the named page, asking for verbatim text. WebFetch returns text through an extraction model and caps each quote at 125 characters. These quotes are very likely verbatim, but spot-check them against the PDF before camera-ready.
- **(para)**: a paraphrase, not a quote. Do not put it in quotation marks.

Access limits in this session:
- Shell egress to arxiv.org, crossref, CVF, Stanford and RSS was blocked by policy, so all web reads went through WebFetch.
- Crossref returned HTTP 429 after three queries.
- doi.org returned HTTP 429. The RA-L page for NV-LIOM was **not** read.
- These pages blocked automated access, so the Bingham (1974) and Mardia & Jupp primary pages were **not** read:
  - Project Euclid and JSTOR (bot-protection pages);
  - Wiley (fetch error);
  - Semantic Scholar API (fetch error);
  - dblp search and .bib pages (robots.txt).

---

## 0. Findings that change the draft

1. **Labels are not unique to Nubert et al. (L3E) and Switch-SLAM.** Nobili et al. (ICRA 2018; new reference N1 below) scored a learned alignment-risk predictor against labels:
   - In experiments, each real alignment was "manually labelled as a success or a failure".
   - In a simulated test they report 79.8% accuracy "for degeneracy".
   - These labels are per alignment (success or failure), not per direction.
   - The draft's "only L3E and Switch-SLAM" sentence must therefore become "to our knowledge, no study provides **per-direction** labels on **real** data". Cite N1 as a per-alignment, real-data example.
2. **DCReg Table 9 is the corridor sequence with range limited to 10 m.** §7.5.1 says "corridor dataset with LiDAR range limited to 10 m". Figure 17's corridor frames use a 5 m limit. Say "range-limited corridor" when citing Table 9.
3. **FusionPortable v1 does provide ground-truth maps for its indoor sequences.**
   - Table III marks GT Map "Yes" for the indoor sequences and "No" for campus_road.
   - The maps come from a Leica BLK360.
   - This settles the open item in `review.md` B.27.
4. **SubT-MRS DOI.** The SuperLoc authors' page gives the SubT-MRS BibTeX DOI 10.1109/CVPR52733.2024.02137. This comes from the authors' page, not IEEE, so confirm it on Xplore before use.
5. **The X-ICP thresholds differ between papers.**
   - X-ICP arXiv v4 uses κ₁ = 250, κ₂ = 180, κ₃ = 35, "set based on the basin of convergence".
   - DCReg's X-ICP baseline uses 300 / 150 (§7.1.3).
   - Do not quote one set as "X-ICP's thresholds" without saying which paper it comes from.
6. **Hinduja et al.'s adaptive threshold** is described as being "for the loop closure candidates" (see §9). Keep the draft's wording general: "made the cutoff adaptive (recomputed per iteration)".

---

## 1. Cadena et al., T-RO 2016 [1]

Source: [WF] https://ar5iv.labs.arxiv.org/html/1606.05830 (arXiv v4 = T-RO version)

1. "we are entering in a third era for SLAM, the robust-perception age" (Introduction)
2. Requirement of that era: "the SLAM system operates with low failure rate for an extended period of time in a broad set of environments" (Introduction)
3. "the system needs to be aware of imminent failure (e.g., due to outliers or degeneracies)" (Sec. III, Long-term autonomy I: Robustness)
4. "An ideal SLAM solution should be fail-safe and failure-aware." (Sec. III)

**Use:** cite [1] for "robustness and failure-awareness are open SLAM requirements". Do **not** cite it for "LiDAR is the main sensor".

## 2. Ebadi et al., T-RO 2024, DARPA SubT [2]

Source: [WF] https://ar5iv.labs.arxiv.org/html/2208.01787. This is the arXiv preprint "Present and Future of SLAM in Extreme Underground Environments", and its wording may differ slightly from the T-RO version.

1. "particular emphasis is put on LIDAR-centric SLAM solutions (the go-to approach for virtually all teams in the competition)" (Abstract)
2. "Most teams relied on LIDAR and IMU as the dominant sensing modalities;" (Sec. III-H, Common Themes on the Path to Robustness)
3. "the lack of perceptual features (e.g., long corridors, large open spaces, and chambers) … induces failures in LIDAR-odometry approaches based on feature or scan matching." (Sec. I)
4. "The potential presence of dense obscurants, such as fog, whirling dust clouds, and smoke, challenges the use of LIDARs." (Sec. I)
5. Extra quote from Sec. III-B (CERBERUS): "to identify the degrees of freedom that are possibly ill-conditioned due to geometric self-similarity".

## 3. LOAM, RSS 2014 [3]

Source: [WF] https://www.roboticsproceedings.org/rss10/p07.pdf

- Feature selection: "select feature points that are on sharp edges and planar surface patches" (Sec. V-A).
- Residuals: "the point to line distance" (Eq. 2) and "the point to plane distance" (Eq. 3) are minimized with "the Levenberg-Marquardt method" (Secs. V-B to V-C).

## 4. LeGO-LOAM, IROS 2018 [4]

Source: [LP] the authors' preprint `Shan_Englot_IROS_2018_Preprint.pdf`, from the GitHub repo RobustFieldAutonomyLab/LeGO-LOAM (local copy in scratchpad/repos).

- "A two-step Levenberg-Marquardt optimization method then uses the planar and edge features to solve different components of the six degree-of-freedom transformation" (Abstract)
- "Planar features extracted from the ground are used to obtain [tz, θroll, θpitch] … [tx, ty, θyaw] is obtained by matching edge features" (Sec. I)

## 5. LIO-SAM, IROS 2020 [5]

Source: [WF] https://ar5iv.labs.arxiv.org/html/2007.00258

- "Edge and planar features are extracted by evaluating the roughness of points over a local region." (Sec. III-C)
- Each feature's distance to "its edge or planar patch correspondence" is minimized with Gauss–Newton (Sec. III-C).
- IMU role: "The estimated motion from inertial measurement unit (IMU) pre-integration de-skews point clouds and produces an initial guess for lidar odometry optimization." (Abstract)

## 6. FAST-LIO2, T-RO 2022 [6]

Source: [WF] https://arxiv.org/abs/2107.06829

- "The first one is directly registering raw points to the map" (Abstract). The rest of the sentence was given only as a paraphrase: (para) "without extracting features".
- "maintaining a map by an incremental k-d tree data structure, ikd-Tree" (Abstract)
- Evaluation: "19 sequences from a variety of open LiDAR datasets" (Abstract)
- Point-to-plane on raw points is also stated in DCReg §3.2, which cites FAST-LIO2 [PF]: "The point-to-plane error metric, widely adopted in LiDAR registration for its superior convergence properties".

## 7. Zhang, Kaess, Singh, ICRA 2016 [7]

Source: [WF] https://www.cs.cmu.edu/~kaess/pub/Zhang16icra.pdf

1. "Definition 1: The degeneracy factor D of a system is mathematically defined as D = δd/δx∗c." (Sec. III)
2. "Lemma 2: For the linearized system (3), D = λmin + 1, where λmin is the smallest eigenvalue of A^T A." (Sec. III)
3. Solution remapping: "use xp in the degenerate directions, v1, … vm, and xu in the well-conditioned directions, vm+1,..., vn." (Sec. IV)
4. Threshold: "The threshold is set at the mid-point of the margin between both groups." It is computed "From one sample dataset" (Sec. V).

## 8. Gelfand et al., 3DIM 2003 [8]

Source: [WF] https://graphics.stanford.edu/papers/stabicp/stabicp.pdf

1. The matrix is the "covariance matrix of the "torque" and "force" components contributed by each point pair" (Sec. 3).
2. "If any of the eigenvalues are small, the corresponding eigenvector defines a transformation that can move two meshes from their optimum alignment with only a small increase in error." (Sec. 3)
3. "Our measure of stability, therefore, will be the condition number of the matrix" (Sec. 3)
4. Normal-space sampling "is aimed at constraining translational sliding of the input meshes", and it amounts to trying "to equalize the eigenvalues of eigenvectors of W that correspond to translations". The paper contrasts: "Unlike [11], our approach deals with both translational and rotational uncertainties." (Sec. 2/4)
5. Units: Gelfand et al. "scale the point set" to equalize displacement due to ""torque" (i.e. rotation)" with that due to ""force" (i.e. translation)" (Sec. 3). This is an early fix for the rotation/translation scale problem.

**Use:** item 4 supports "normal-based statistics constrain translation only". This is the right citation for the scope of Channel T.

## 9. Hinduja et al., IROS 2019 [9]

Source: [WF] https://www.cs.cmu.edu/~kaess/pub/Hinduja19iros.pdf

1. "These directions are selected on the basis of a dynamic threshold, which updates at each iteration." (Abstract)
2. "we use the condition number, i.e. the ratio between the maximum and minimum eigenvalues … for each iteration as our eigenvalue threshold for the loop closure candidates." (Sec. III)
3. On Zhang et al.'s dataset-calibrated threshold: "However this method is not suitable for real-time evaluation." (Related work)

DCReg labels this method "FCN" (full-Hessian condition number) [PF Table 1, §7.1.2].

## 10. X-ICP, T-RO 2024 [10]

Source: [WF] https://arxiv.org/html/2211.16335v4

1. Categories: "localizable, partially-localizable, and non-localizable" directions, assigned by thresholds κ₁, κ₂, κ₃ (Sec. V).
2. Thresholds: "These parameters are set based on the basin of convergence of the employed ICP algorithm."
   - The values are κ₁ = 250, κ₂ = 180, κ₃ = 35, used "for all environments and sensors shown in Section VII".
   - The κ₃ risk "is user-defined" (Sec. V).
3. Key field result, Seemühle mine, 521.8 m:
   - End-position error was 0.27 m for X-ICP, 6.37 m for Zhang et al., and 24.17 m for Hinduja et al.
   - APE was 2.05 m for X-ICP versus 3.36 m and 5.79 m (Table I, VLP-16).
4. On eigenvalue methods: "Being binary in nature, the method depends on the heuristic tuning of thresholds for operation in different environments." (Sec. II)
5. Stated limitation: "Currently, the proposed method is (similar to related methods) sensitive to the quality of the initial guess." (Conclusion)

## 11. LP-ICP, arXiv 2501.02580 [26 in verified_refs]

Source: [WF] https://arxiv.org/abs/2501.02580 (v3, 31 May 2025; no journal-ref)

1. LP-ICP "combines point-to-line and point-to-plane distance metrics in the ICP algorithm" (Abstract).
2. "The optimization module adds additional soft and hard constraints to the optimization equations based on the localizability category." (Abstract)
3. Stated limitation: "Observed variations in partially localizable directions suggest the need for further investigation on robustness and generalizability." (Abstract)

## 12. Nubert et al., IROS 2022 (L3E) [11]

Source: [WF] https://ar5iv.labs.arxiv.org/html/2203.05698

1. "the network is trained exclusively on simulated data" (Abstract)
2. Labels, part 1: child scans "have to be recorded through ray-casting at the sampled sensor location". Each is "registered against the parent point cloud using point-to-plane ICP" (Sec. III / IV-A).
3. Labels, part 2: "the localizability is considered binary; either a certain direction is localizable or not". The thresholds are 0.1 m and 2.0° (Table II).
4. Test metrics, averaged over 6 DoF (Table IV, ResUNet): accuracy 0.854, precision 0.398, recall 0.752, F1 0.517.
   - The test set is "created in simulation from a ground truth mesh of the tunnel environment" (Sec. V-A).
   - The data are "highly imbalanced with regard to positive and negative instances for each of the six directions" (Sec. IV-E1).
5. Useful for motivating thresholds: in the tunnel field test, "an e-value threshold of at least 110 is required to reliably detect degeneracy" (Sec. VI).

## 13. Hatleskog & Alexis, RA-L 2024 [16]

Source: [WF] https://arxiv.org/html/2410.10784

1. "The eigenvalues of the Hessian depend on the number of measurements, weights, the scale of the environment" (Sec. I). `review.md` records the sentence's continuation as "and sensor noise".
2. Earlier methods "require careful fine-tuning tailored to the robot, sensor, environment" (Sec. I).
3. "Consequently, tuning parameters cannot be expected to generalize across heterogeneous scenarios." (Sec. I)
4. Noise model:
   - points "affected by additive Gaussian noise";
   - normals "influenced by a small rotational perturbation";
   - the method computes the probability "that the signal is s times larger than noise in direction u", with s = 10 (Secs. II-C, III-A).
5. "The method's parameters are selected based on the noise characteristics provided in the LiDAR's datasheet." (Abstract)

## 14. RELEAD, ICRA 2024 [17]

Source: [WF] https://arxiv.org/abs/2402.18934

1. "Our method enables degeneracy-free point cloud registration by solving constrained ESIKF updates in the front end" (Abstract)
2. Multi-sensor constraints are incorporated "through graph optimization based on Graduated Non-Convexity (GNC)" (Abstract).
3. Claimed result: RELEAD "has outperformed existing state-of-the-art LiDAR-Inertial odometry and LiDAR-Visual-Inertial odometry methods" (Abstract).

DCReg [PF §2.1.1] lists RELEAD (Chen et al. 2024a) with X-ICP as diagonal-block analysis.

## 15. Tuna et al., T-FR 2025, "Informed, Constrained, Aligned" [12]

Sources: [WF] https://arxiv.org/abs/2408.11809 and https://arxiv.org/pdf/2408.11809v2. Section numbers below are those of arXiv v2 and may differ in T-FR.

1. "active optimization degeneracy mitigation is necessary and advantageous in the absence of reliable external estimate assistance for LiDAR-SLAM" (Abstract)
2. "Current solutions primarily focus on utilizing additional sources of information, such as external odometry," (Abstract)
3. In the Ulmberg tunnel, with degeneracy in more than 80% of the data: "the performance is mainly driven by better usage of the external motion prior" (Sec. 5). For the Prior-Only baseline: "the accuracy of this method depends on the accuracy of the external pose prior" (Sec. 4.1.7).
4. On detection versus mitigation:
   - One X-ICP-based binary detector is used for all methods "to prevent giving an unintentional advantage to more complex methods" (Sec. 4.3).
   - "Often, these methods require accurate information on degeneracy detection to perform optimally." (Sec. 4.1)
   - Research gap: "there remains a fundamental research gap on the efficacy of degeneracy mitigation methods once LiDAR degeneracy is detected" (Sec. 1).

## 16. DCReg, IJRR 2026 [13]

Source: [PF] `2509.06285v3.pdf`

**Scale disparity**
1. "rotational eigenvalues typically exceed translational ones by orders of magnitude due to lever-arm effects … making rotational degeneracies particularly elusive to detect." (§2.1.1)
2. The ME baseline "systematically overlooks rotational degeneracies due to scale disparity, as rotational eigenvalues typically maintain higher magnitudes than translational counterparts" (§7.3.1, parking lot).
3. "ME exhibit insufficient detection by overlooking larger eigenvalue directions, while FCN demonstrate over-detection by treating all translational dimensions as universally degenerate." (§7.4.1, Fig. 12)
4. Caveat: "Rotational eigenvalues are not consistently larger than translational ones" (Fig. 17 caption).

**Point-to-plane Hessian blocks**
5. "Htt depends solely on the normal distribution, independent of point distances." (§3.3, after Eq. 7c, Htt = Σ nᵢnᵢᵀ)

**Diagonal-block masking**
6. "Even when both κ(HRR) and κ(Htt) appear well-conditioned, the overall system can exhibit severe ill-conditioning due to strong rotation-translation coupling." (§4.2)
7. Diagonal-block analysis "overlooks the coupling effects between translation and rotation" and leads "to both false positives and false negatives in degeneracy detection" (§2.1.1).
8. "Regions A and B demonstrate cases where rotational degeneracy is masked by diagonal methods." (Fig. 13 caption, parking lot). On stairs: "diagonal methods fail to detect these critical degeneracies, misclassify them as well-constrained cases" (§7.4.1).

**Eigenvector ordering ambiguity**
9. Corridors: "where motion x and roll are similarly constrained, corresponding eigenvalues become nearly identical or the spectral gap is small, making their natural ordering unstable" (§5)
10. "the three smallest eigenvalues in complete Hessian analysis do not necessarily correspond to translational dimensions." (§7.4.2, corridor)

**Thresholds**
11. "κth is a threshold typically set between 10 and 50." (§4.3). The experiments use "κth = 10, minimum eigenvalue threshold of 120" (§7.1.3).

**Evaluation practice**
12. "DR serves as an indicator of detection sensitivity rather than an error metric." (§7.1.2). DR is "the percentage of frames identified as degenerate".
13. Range limits: "we artificially limit the LiDAR sensing range in some sequences (e.g., parking lot and corridor)" (§7.1.1). The system context: "a 5 s sliding-window fixed-lag smoother … coupled with LiDAR-inertial odometry" (§7.1.3).

**Ablation (Table 9; corridor, LiDAR range limited to 10 m, DR 58.04%; §7.5.1)**

ATE for each configuration:

| Configuration | ATE (cm) |
|---|---|
| w/o all (no degeneracy handling) | 28.54 |
| w/o PCG (Schur detection, no mitigation) | 164.14 |
| w/o Precond. | 23.95 |
| w/o CG | 9.22 |
| DCReg + SR | 37.75 |
| DCReg + TSVD | 17.81 |
| DCReg + TReg | 22.79 |
| DCReg (Full) | 7.44 |

Quote for detection without mitigation: "the detected degeneracies are not acted upon and the solver continues to update along ill-conditioned directions" (§7.5.1).

**Headline results**
14. "at least 20%–50% improvement in long-duration localization accuracy and typical speedups of 5 − 30× (up to 116× in certain scenarios)" (Abstract)

**Conclusion and future directions**
15. "degeneracy stems not only from repetitive geometric features (e.g., tunnels) but also from sparse environments and poor initial poses causing insufficient constraints." (§10)
16. "Strong priors from IMU or other sensors can also stabilize weakly constrained local estimation, but they can also redistribute or mask degeneracy patterns." (§9). This is a remark, not an experimental result.
17. Learned detectors: "their generalization across diverse environments remains constrained by training dataset limitations." (§2.1.2)
18. Noise-model detectors "suffer… from significant performance variations based on parameter settings for multiple noise sources" (§2.1.2).
19. Convergence basin: "When initial pose estimates fall outside this basin, optimization becomes trapped in local minima, rendering degeneracy analysis ineffective" (§8)

## 17. LF-GICP, arXiv 2608.19522 [15]

Source: [WF] https://arxiv.org/abs/2608.19522 (submitted 20 Aug 2026; no journal-ref)

1. "We show that in voxelized GICP the Gauss--Newton (GN) Hessian masks translational degeneracy, because covariance regularization keeps the translation block artificially well-conditioned." (Abstract)
2. "We bypass this with a regularization-free voxel-normal localizability field" (Abstract)
3. Existing handling "requires environment-specific parameter tuning" (Abstract)
4. "straight, uniform tunnels remain unobservable along their axis for LiDAR-only registration." (Abstract)

## 18. NV-LIO (arXiv 2405.12563) / NV-LIOM (RA-L 2024) [14]

Source: [WF] https://arxiv.org/abs/2405.12563, which redirected to the HTML of the NV-LIO preprint. The RA-L page was **not** read (doi.org returned 429).

1. "the distribution of the normal vector directions is analyzed to assess the occurrence of degeneracy" (Introduction)
2. "the smallest eigenvalue, $\lambda_0$, indicates a degenerate case if it falls below a specific threshold" (Degeneracy Detection)
3. "we inserted factors using this distribution-based measurement covariance in degenerate cases" (Degeneracy Detection)

## 19. Switch-SLAM, RA-L 2024 [19]

Source: [PF] `SwitchSLAM.pdf`

1. "a switching structure that transitions from LiDAR to visual odometry when degeneration of LiDAR odometry is detected." (Abstract)
2. "a non-heuristic degeneracy detection method that does not require heuristic tuning and demonstrates generalizability across various environments." (Abstract)
3. Labels: "The ground truth is prepared by comparing GNSS data with scan-to-scan matching using ICP [36] at each keyframe." (Sec. IV-C)
   - The labels cover "a part of the Handheld dataset" (Fig. 9 caption), which is LVI-SAM's Handheld set, cited as [11].
4. Numbers (Sec. IV-C):
   - "an accuracy of 0.91 for [16], 0.96 for [17], and 0.96 for the proposed method"
   - "The recall is 0.91 for [16], 0.96 for [17], and 0.99 for the proposed method."
   - [16] = Zhang 2016 and [17] = Nashed 2021.
   - The baselines are reported at their best threshold on this data: "the best accuracy and recall are obtained for a threshold of 100 for [16] and of 10 for [17]."
5. What it switches to:
   - The VO uses "the method proposed in [6]" (VINS-Mono, Sec. III-A).
   - Switching happens when "any λ value is lower than the corresponding value of λt", with λt = [0.12, 0.27, 0.48] (Sec. III-C).
   - The LiDAR update then keeps only the well-conditioned DOFs: "Λp denotes the matrix with eigenvalues removed corresponding to degenerate DOFs from Λ." (Eq. 15)
6. Physical assumption: "LiDAR odometry rarely degenerate beyond 3-DOFs" (Sec. III-C). The threshold uses "0.103 … the Chi-squared value for 2-DOFs at a 95% confidence level" (Eq. 11). That is the paper's wording; the earlier project note questioned this arithmetic.

## 20. LVI-SAM, ICRA 2021 [23]

Sources: [WF] https://ar5iv.labs.arxiv.org/html/2104.10831; the eigenvalue quote is from `review.md` (arXiv PDF).

1. "LVI-SAM can also function when one of the two sub-systems fails." (Abstract)
2. VIS → LIS: visual odometry "serves as an initial guess for lidar scan-matching and introduces constraints into the factor graph." (Sec. I)
3. LIS failure test (Sec. II-C2):
   - the "smallest eigenvalue of ATA is smaller than a threshold" (`review.md`);
   - "Lidar odometry constraints are not added to the factor graph when failure happens." ([WF])
4. "We adapt the processing pipeline from [8] for our VIS". Here [8] is VINS-Mono (Sec. II-B).

## 21. VINS-Mono, T-RO 2018 [18]

Source: [WF] https://arxiv.org/abs/1708.03852

- "A tightly-coupled, nonlinear optimization-based method is used to obtain high accuracy visual-inertial odometry by fusing pre-integrated IMU measurements and feature observations." (Abstract)
- "Our approach starts with a robust procedure for estimator initialization and failure recovery." (Abstract)

## 22. SubT-MRS, CVPR 2024 [20]

Sources: [WF] CVF HTML page and CVF PDF: https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.pdf

1. "multi-degraded environments including over 30 diverse scenes … structureless corridors varying lighting conditions and perceptual obscurants like smoke and dust" (Abstract)
2. Geometric degradation includes "long, featureless corridors (Figure 3 E) and staircases" (paper body).
3. Ground truth:
   - The map is from a "high-precision FARO Focus 3D S120 3D scanner", "maintaining a range error within ±2mm", and "96% of the scans achieved a position uncertainty of less than 2mm".
   - The trajectory is "a comprehensive fusion of various constraints derived from the ground truth map", using point-to-point, point-to-plane and point-to-line correspondences.
   - **The paper gives no accuracy figure for the GT trajectory.** Do not write "cm-accurate trajectories".
4. "the first real-world dataset that specifically addresses failure scenarios of SLAM" (paper body)
5. DOI 10.1109/CVPR52733.2024.02137 comes from the BibTeX on the SuperLoc authors' page (https://superodometry.com/superloc). Confirm it on Xplore.

## 23. GEODE, IJRR 2026 [21]

Source: [WF] https://arxiv.org/abs/2409.04961 and https://arxiv.org/html/2409.04961v2

1. "64 trajectories spanning over 64 kilometers" in "seven diverse settings" (Abstract).
2. The settings: "flat ground, stairs, metro tunnels, off-road terrain, inland waterways, urban tunnels, and bridges" (Sec. 1.2). The LiDARs are VLP-16, OS1-64 and Livox AVIA.
3. Degeneracy categories: degradation "can be categorized into three types: rotational, translational, and a combination of both" (Sec. 4.2.2).
4. GT: "precise ground-truth poses for each sequence and ground-truth maps for select indoor sequences" (Sec. 1.2).
   - The GT sources are Mocap, PALoc with a laser tracker, and GNSS-RTK/INS (Table 3).
   - The about 1 cm and 1 mm figures in Table 2 are device specifications, not trajectory accuracy.
5. Motivation: "existing open-source datasets lack representation of geometrically degenerate environments." (Abstract)

## 24. FusionPortable, IROS 2022 [22]

Source: [WF] https://ar5iv.labs.arxiv.org/html/2208.11865

1. "17 sequences that cover a variety of environments on the campus" (Abstract). Platforms: handheld, quadruped, autonomous vehicle (Sec. I-B).
2. GT trajectories (Sec. IV-B):
   - OptiTrack "with millimeter accuracy" in the mocap room;
   - "the NDT-based 6-DoF localization" against a prior map for middle-scale indoor areas;
   - outdoors, "fuse the RTK GPS signal with LiDAR-inertial measurements".
3. GT maps: a Leica BLK360 records a "high-resolution colorized 3D dense map with millimeter accuracy". Table III marks GT Map "Yes" for indoor sequences (Sec. IV-B).
4. Caveat for Paper Sec. IV: for the corridor and other middle-scale indoor sequences, GT poses come from NDT registration to the prior map. They may therefore be weak along the very directions that the corridor degenerates in.

## 25. Bingham 1974 [24] and Mardia & Jupp 2000 [25]

**Primary texts NOT read.** Project Euclid and JSTOR returned bot-protection pages, and Wiley returned a fetch error. Verified so far:
- the Crossref metadata in `verified_refs.md`;
- the title itself: "An antipodally symmetric distribution on the sphere".

Supporting statements from accessible papers, all [WF]:
1. Fallaize & Kypraios, arXiv 1401.2894, "Exact Bayesian inference for the Bingham distribution" (venue not checked):
   - "spherical data which arise as unsigned directions is the Bingham distribution", citing Bingham (1974) and Mardia & Jupp (2000) (Sec. 1);
   - the density is f(x;A) = exp(−xᵀAx)/c(A);
   - the mean squared components τᵢ "are sufficient statistics for" the concentration parameters.
2. Gilitschenski, Kurz, Julier, Hanebeck, arXiv 1311.5796, "Unscented orientation estimation based on the Bingham distribution" (venue not checked):
   - the distribution is antipodally symmetric;
   - fitting is "performed by computing an eigendecomposition of this covariance matrix", where M = the eigenvectors and Z is solved from the eigenvalues.

Safe wording for the Introduction: "The Bingham distribution [24], [25] models axial (sign-free) unit vectors such as surface normals; it is fitted from the eigen-decomposition of the second-moment (scatter) matrix of the samples."

The claim that the scatter matrix is the *sufficient statistic* is standard exponential-family reasoning and is stated in earlier project notes, but it was **not** verified from a primary page here. Read Mardia & Jupp §9.4 / §10.7 in a library copy before you state it as a quoted fact.

---

## 26. Candidate additional references

### N1. Nobili, Tinchev, Fallon, ICRA 2018: **VERIFIED**

**IEEE:** S. Nobili, G. Tinchev, and M. Fallon, "Predicting alignment risk to prevent localization failure," in *Proc. IEEE Int. Conf. Robot. Autom.* (ICRA), Brisbane, QLD, Australia, May 2018, pp. 1003–1010, doi: 10.1109/ICRA.2018.8462890.

Verification:
- Crossref (queried before the rate limit) confirmed the title, the three authors, ICRA 2018 Brisbane (21–25 May), pp. 1003–1010 and the DOI.
- The text was read in the authors' PDF: https://ori.ox.ac.uk/media/5610/2018icra_nobili.pdf [WF].

Facts:
1. "Our solution relies on explicit analysis of the point cloud content prior to registration." (Abstract)
2. "A model predicting the risk of a failed alignment is learned by analysing the degree of spatial overlap between two input point clouds." (Abstract). Alignability is computed by "PCA on the row vectors of N" (the plane normals).
3. Labels: "Each observation is registered using AICP and each alignment is manually labelled as a success or a failure." Failure is defined as an error above 0.02 m or 1°.
4. Results:
   - "The average accuracy of the two parameters was 79.8% for degeneracy and 97.7% for alignability" (simulated test).
   - Online test: "AR captured all 21 alignment failures" (Fig. 10).
   - Accuracy only; no precision or recall.

### N2. Ebadi et al., DARE-SLAM, J. Intell. Robot. Syst. 2021: **VERIFIED**

**IEEE:** K. Ebadi, M. Palieri, S. Wood, C. Padgett, and A.-a. Agha-mohammadi, "DARE-SLAM: Degeneracy-aware and resilient loop closing in perceptually-degraded environments," *J. Intell. Robot. Syst.*, vol. 102, no. 1, Art. no. 2, 2021, doi: 10.1007/s10846-021-01362-w.

Verification:
- The Springer article page (https://link.springer.com/article/10.1007/s10846-021-01362-w) gave the title, authors, journal, vol. 102, article 2, the publication date of 9 Apr. 2021, and the DOI.
- dblp gave no. 1.
- The preprint is arXiv:2102.05117.

Facts (Abstract, [WF]):
- The method targets "a degeneracy-aware and drift-resilient loop closing method to improve place recognition" in "lava tubes, caves, and mines".
- "unobservable areas in the environment are determined and excluded from the search for loop closures".

### N3. SuperLoc, Zhao et al., ICRA 2025: **VERIFIED (DOI not found; omit DOI)**

**IEEE:** S. Zhao, H. Zhu, Y. Gao, B. Kim, Y. Qiu, A. M. Johnson, and S. Scherer, "SuperLoc: The key to robust LiDAR-inertial localization lies in predicting alignment risks," in *Proc. IEEE Int. Conf. Robot. Autom.* (ICRA), 2025, pp. 14080–14086.

Verification:
- The venue is confirmed on the authors' page: "2025 IEEE International Conference on Robotics and Automation (ICRA)".
- The pages and author list come from the dblp person page (dblp.dagstuhl.de/pid/262/0103).
- The title and authors match arXiv 2412.02901.
- Neither dblp nor the authors' page gives a DOI. Add it only after checking Xplore.

Facts ([WF], arXiv abs and HTML v2):
1. "Unlike existing degeneracy mitigation algorithms that rely on post-optimization analysis and heuristic thresholds" (Abstract)
2. "eigenvalue analysis occurs too late in the optimization process to provide timely remedy" (Sec. I)
3. "we can quickly assess constraint observability in each pose direction (X, Y, Z) before the ICP optimization happens" (Sec. III)
   - (para) It uses a per-DoF confidence, and values below 0.2 indicate likely degradation.
   - (para) It reports no detection precision or recall against labels.
4. "Our approach achieves a 54% increase in accuracy and exhibits the highest robustness." (Abstract)

### N4. Censi, ICRA 2007: **DROP**

What was confirmed: dblp (https://dblp1.uni-trier.de/rec/conf/icra/Censi07.html) gives the author, the title "An accurate closed-form estimate of ICP's covariance", ICRA 2007 and pp. 3167–3172.

Why it is dropped:
- No DOI could be confirmed. A search for the DOI commonly attributed to it, 10.1109/ROBOT.2007.363961, did not lead to the paper.
- No text of the paper could be opened, so there is no citable fact.
- Re-check on IEEE Xplore if you want it.

### N5. Khattak et al., ICUAS 2020, "Complementary multi-modal sensor fusion for resilient robot pose estimation in subterranean environments": **DROP**

- The only evidence is DCReg's reference list (ICUAS 2020, pp. 1024–1029), which is a secondary source.
- dblp's Khattak page lists no matching ICUAS 2020 entry.
- The NTNU/NVA archive page needs JavaScript.
- Crossref was rate-limited.

---

## 27. Pages that could not be read

| Page | Reason |
|---|---|
| doi.org/10.1109/LRA.2024.3457373 (NV-LIOM, RA-L) | HTTP 429 (rate-limited) |
| api.crossref.org | HTTP 429 after three queries; Censi, Khattak and SuperLoc were not checked there |
| Project Euclid and JSTOR (Bingham 1974) | Bot-protection pages |
| Wiley Online Library (Mardia & Jupp) | Fetch error |
| Semantic Scholar API | Fetch error |
| dblp search and .bib pages | robots.txt |
| purl.org/censi | Server error |
| NVA (NTNU) archive | Needs JavaScript |
| X-ICP arXiv HTML | Read only to 100k characters (the experiments and conclusion were covered) |
| Tuna T-FR arXiv PDF | Truncated in Sec. 5.2 before Secs. 6–7. Its conclusion text was not read; the quotes above come from the abstract and Secs. 1, 4 and 5 |
