# Validation Methodology for SLAM Degeneracy Detectors, Thresholds, and LiDAR-Visual-Inertial Odometry Evaluation

Scope note: these notes target a thesis that (a) validated degeneracy detectors with synthetic random 6x6 SPD Hessians (3000 trials, one seed) and an eigenvalue-ratio ground truth that equals the detector threshold (circular), (b) analyzed one Gazebo run (4017 frames) by comparing mean pose error per mode, (c) used arbitrary trial counts (400, 800), and (d) borrowed thresholds from other papers. Numbers marked "[computed]" were calculated by the researcher with scipy from the cited formulas; they are not quoted from a source.

## Q1. How do X-ICP (Tuna et al.), Tuna et al. 2025 and DCReg define ground-truth degeneracy, and what detector-independent ground truth is accepted?

### Takeaway
None of X-ICP, the Tuna et al. field analysis, or DCReg reports a per-frame precision/recall against labelled ground truth; they ground degeneracy in (i) synthetic environments whose degenerate directions follow from geometry (symmetric cylinder, corridors) with known transforms, and (ii) real deployments in known-degenerate environments (tunnels, mines, open fields) judged by trajectory/map error against an independent reference (laser scanner map, GNSS/RTK-INS). A 2026 paper ("Degenerate in Whose Frame?") gives the most directly reusable detector-independent protocol: synthetic corridors whose degenerate-direction count is fixed by geometry, swept over noise/voxel settings and 8 seeds, and a threshold is accepted only if it reproduces the known counts in all configurations.

### Cited Findings
- X-ICP (Tuna, Nubert, Nava, Khattak, Hutter; IEEE T-RO 2023, arXiv 2211.16335) classifies each direction as "localizable, partially-localizable, and non-localizable"; the paper does not report explicit detection metrics (TP/FP/FN, precision, recall) — [X-ICP arXiv PDF](https://arxiv.org/pdf/2211.16335)
- In X-ICP simulation, "the degenerate directions are shown in yellow (translational) and blue (rotational)" — i.e., known from the simulated geometry; in the Seemühle mine, "The environment was scanned using a Leica RTC 360 scanner ... which is used to generate ground truth map and robot trajectory" — [X-ICP arXiv PDF](https://arxiv.org/pdf/2211.16335)
- X-ICP parameters: "κ1 = 250, κ2 = 180, and κ3 = 35 for all environments and sensors"; but κf = cos(80°) ≈ 0.1736 for Velodyne and cos(60°) = 0.5 for Ouster OS0-128 (sensor-dependent). Formal sensitivity analysis of X-ICP's own thresholds is limited; the Seemühle experiment was run "twice" with different sensors, other experiments single-run — [X-ICP arXiv PDF](https://arxiv.org/pdf/2211.16335)
- Tuna et al., "Informed, Constrained, Aligned: A Field Analysis on Degeneracy-aware Point Cloud Registration in the Wild" (arXiv 2408.11809, IEEE T-ASE): static simulation uses "source and reference point clouds ... sampled from a simulated, perfectly cylindrical, and symmetric mesh" with known transformation perturbations; metrics include "Frobenius distance to the true transform", translation errors, and "motion residual along the degenerate direction" — [arXiv 2408.11809](https://arxiv.org/pdf/2408.11809)
- The same paper fixes the detector across mitigation methods for fairness: "all works discussed here use the degeneracy detection method described in X-ICP ... to ensure a fair comparison", with κ1 = 300, κ2 = 150, κ3 = 45 (note: different from X-ICP's 250/180/35); parameter-dependent methods "are tuned based on performance in the Ulmberg bicycle tunnel experiment" — [arXiv 2408.11809](https://arxiv.org/pdf/2408.11809)
- Real-world experiments in Tuna et al.: ANYmal forest (open-field degeneracy, GPS reference), Ulmberg bicycle tunnel ("the LiDAR degeneracy continues for more than 80% of the dataset"), HEAP excavator (short-burst degeneracy) — [arXiv 2408.11809](https://arxiv.org/pdf/2408.11809); project page [Perfectly Constrained](https://sites.google.com/leggedrobotics.com/perfectlyconstrained)
- DCReg (arXiv 2509.06285; IJRR 2026 per repo): "Following the protocol established in Tuna et al. (2025), we employ a symmetric cylinder scenario ... with controlled perturbations"; cylinder of "7600 points" with "a fixed rotation around the Z-axis and a large translation along Z, creating a scenario with multi-DOF degeneracy" — [DCReg arXiv PDF](https://arxiv.org/pdf/2509.06285); [DCReg GitHub](https://github.com/JokerJohn/DCReg)
- DCReg detection reliability: per-dimension detection over time (parking-lot data), Schur-complement vs diagonal condition numbers with "detection thresholds set to 10", and statistical detection rates (balanced vs over/under-detection) across datasets; thresholds "condition number threshold of κth = 10, minimum eigenvalue threshold of 120" — [DCReg arXiv PDF](https://arxiv.org/pdf/2509.06285)
- DCReg real-world evaluation uses ATE, registration accuracy (AC) and Chamfer Distance (CD) on FusionPortable, GEODE, SubT-MRS and self-collected sequences with "RTK-INS ground truth" — [DCReg arXiv PDF](https://arxiv.org/pdf/2509.06285)
- "Degenerate in Whose Frame? An Equivariance Condition for Degeneracy Detection in LiDAR Registration" (Zhang, Zhao, Lin, Guo, Jia, Liu; arXiv 2608.15532): "we use synthetic corridors whose number of degenerate directions follows from geometry" — rectangular corridor = 1 degenerate direction (axial translation), circular corridor = 2 (axial translation + roll about axis), right-angle corner = 0 — [arXiv 2608.15532](https://arxiv.org/html/2608.15532)
- That paper crosses 9 preprocessing configs (3 noise levels × 3 voxel sizes) with 8 random seeds = 216 instances, and for each detector "identif[ies] the threshold interval that reproduces the counts 1, 2 and 0 simultaneously"; only their equivariant point-displacement metric M = Σ J_iᵀJ_i admits a common interval [5.3×10⁻³, 8.3×10⁻²] (1.20 decades); "For every other metric the intersection is empty" — [arXiv 2608.15532](https://arxiv.org/html/2608.15532)

### Inferences
- [Inference] The thesis's circular ground truth (eigenvalue-ratio cutoff = detector threshold) should be replaced by one of three detector-independent references: (a) geometry-defined degeneracy (corridor/cylinder/tunnel in Gazebo or synthetic point clouds, where the null directions are known analytically — the approach of Tuna et al., DCReg, and arXiv 2608.15532); (b) behavioural ground truth: run registration many times from perturbed initial guesses (e.g., random offsets along each eigen-direction) and label a direction degenerate if the converged solution's error/spread along that direction exceeds a tolerance — this is the logic behind "motion residual along the degenerate direction" in Tuna et al., though no reviewed paper reports this as a formal labelling protocol with precision/recall; (c) ground-truth-pose error projected onto the detector's eigen-directions (error vector e = log(T_gt⁻¹ T_est), project onto eigenvectors v_k; label degenerate if |v_kᵀe| exceeds a tolerance) — this is an inference, not a documented protocol in these papers.
- [Inference] Random SPD Hessians do not correspond to any real scene geometry; a stronger synthetic test builds Hessians from sampled point/normal sets of known geometry (corridor, tunnel, plane) plus noise, so the ground truth is geometric, not spectral.
- [Inference] Once the reference is independent, standard binary-classification metrics (per direction per frame: TP/FP/FN/TN, precision, recall, F1) can be reported — something the state-of-the-art papers themselves largely do not do, which the thesis can position as a contribution.
- [Inference] The fact that X-ICP (250/180/35) and Tuna et al. 2025 (300/150/45) use different κ, and κf changes by sensor, is direct evidence that borrowed thresholds are not transferable and must be re-validated on the thesis's own sensor/scene.

### Gaps
- Could not retrieve full experimental sections of X-ICP or DCReg verbatim (fetch tools returned summaries); exact perturbation magnitudes and trial counts in the symmetric-cylinder protocol of Tuna et al. 2025 / DCReg were not extracted.
- No reviewed paper reports precision/recall of degeneracy detection against a per-frame labelled ground truth on real data.

## Q2. Trajectory metrics ATE/RPE and alignment; standard number of runs and variance reporting

### Takeaway
ATE = RMSE of translational residuals after a least-squares alignment (Horn/Umeyama); RPE = error of relative motion over a fixed Δ (time or distance). For visual-inertial (and LiDAR-inertial) systems, align with a 4-DoF (yaw + translation) transform because gravity makes roll/pitch observable; be consistent about which states are aligned. Use evo (evo_ape / evo_rpe) for reproducibility. Report multiple runs (commonly 5 or 10, median or mean ± std) because multithreaded SLAM is nondeterministic.

### Cited Findings
- Sturm et al. 2012 (IROS, TUM RGB-D benchmark), ATE: alignment S via Horn's method, "F_i := Q_i⁻¹ S P_i" (Eq. 4), "RMSE(F_{1:n}) := (1/n Σ ||trans(F_i)||²)^{1/2}" (Eq. 5) — [Sturm et al. 2012 PDF](https://cvg.cit.tum.de/_media/spezial/bib/sturm12iros.pdf)
- Sturm et al. 2012, RPE (Eq. 1) E_i := (Q_i⁻¹ Q_{i+Δ})⁻¹ (P_i⁻¹ P_{i+Δ}) [note: the fetch tool rendered the parentheses incorrectly; this is the standard form in the paper], RMSE over m = n − Δ errors "RMSE(E_{1:n}, Δ) := (1/m Σ ||trans(E_i)||²)^{1/2}" (Eq. 2), and averaged over all Δ "RMSE(E_{1:n}) := 1/n Σ_{Δ=1}^{n} RMSE(E_{1:n}, Δ)" (Eq. 3); translational errors usually suffice because rotation errors show up as translation errors when moving — [Sturm et al. 2012 PDF](https://cvg.cit.tum.de/_media/spezial/bib/sturm12iros.pdf)
- Zhang & Scaramuzza 2018 (IROS, "A Tutorial on Quantitative Trajectory Evaluation for Visual(-Inertial) Odometry"): monocular → sim(3); stereo → SE(3); visual-inertial → "4 DoF yaw-only rigid body transformations (i.e., a rotation around the gravity plus a translation)", because gravity projections "only remain unchanged when the rotation is around the gravity" — [Zhang & Scaramuzza 2018 PDF](https://rpg.ifi.uzh.ch/docs/IROS18_Zhang.pdf)
- Zhang & Scaramuzza: "ATErot = (1/N Σ ‖∠(ΔR_i)‖²)^{1/2}, ATEpos = (1/N Σ ‖Δp_i‖²)^{1/2}"; relative error uses K pairs of states selected "by some criteria (e.g., distance along the trajectory)" and reports "statistics such as the median, average and percentiles" — [Zhang & Scaramuzza 2018 PDF](https://rpg.ifi.uzh.ch/docs/IROS18_Zhang.pdf); toolbox [rpg_trajectory_evaluation](https://github.com/uzh-rpg/rpg_trajectory_evaluation) (which by default uses sub-trajectory lengths as fractions of total length — from the toolbox README, not re-verified here)
- Zhang & Scaramuzza: alignment choice changes results greatly — "the difference of ATEtrans between using the first state and all the states for alignment is quite large (~150%)"; "one needs to be consistent in which states are used for trajectory alignment across different algorithms for a fair comparison" — [Zhang & Scaramuzza 2018 PDF](https://rpg.ifi.uzh.ch/docs/IROS18_Zhang.pdf)
- evo (Grupp 2017): supports TUM, KITTI, EuRoC, ROS/ROS2 bag formats; evo_ape and evo_rpe; `-a` alignment (Umeyama), `-s` scale correction; citation "@misc{grupp2017evo, ... howpublished={\url{https://github.com/MichaelGrupp/evo}}, year={2017}}" — [evo GitHub](https://github.com/MichaelGrupp/evo)
- ORB-SLAM papers report median results over multiple executions to account for nondeterminism (ORB-SLAM: 5 executions; ORB-SLAM3: 10 executions) — search result context only from [ORB-SLAM ar5iv](https://ar5iv.labs.arxiv.org/html/1502.00956) and [ORB-SLAM3 ar5iv](https://ar5iv.labs.arxiv.org/html/2007.11898); the fetch of ORB-SLAM3 did not return the exact sentence, so treat the counts as researcher's recollection needing verification.

### Inferences
- [Inference] For the LiDAR-visual-inertial thesis system: report ATE (translation RMSE, plus rotation) with SE(3) or 4-DoF yaw+translation alignment of the full trajectory, and RPE at fixed distance segments (e.g., 10/20/50 m or fractions of length); state alignment explicitly; produce both with evo so results are reproducible.
- [Inference] Report N ≥ 5 (preferably 10) runs per configuration with median and interquartile range or mean ± std (boxplots), and failure counts separately; in Gazebo, also vary the simulator/sensor-noise seed so runs are not identical.
- [Inference] In Gazebo, ground truth is the simulator's model pose; time-associate with the estimate (evo does timestamp matching with a max-diff tolerance).

### Gaps
- Exact sentence on number of runs in ORB-SLAM3 not retrieved; no survey quantifying the "standard" run count across the SLAM literature was found.

## Q3. Covariance consistency: NEES / NIS chi-square tests (Bar-Shalom) and their use to validate a CRLB-derived threshold

### Takeaway
NEES ε_k = x̃ᵀ P⁻¹ x̃; with N independent Monte Carlo runs, N·ε̄_k ~ χ²(N·n_x), so ε̄_k must lie in [χ²_{α/2}(N n_x)/N, χ²_{1−α/2}(N n_x)/N]. NIS is the same with innovation and its covariance S, and does not need ground truth. Because a CRLB/Hessian-derived threshold assumes the Hessian inverse is the true error covariance, an NEES test on the registration's Hessian-derived covariance is the direct test of that assumption.

### Cited Findings
- NEES: "ε(k) = x̃(k|k)ᵀ P(k|k)⁻¹ x̃(k|k)"; ANEES over N runs "(1/N) Σ ε_i(k)"; "N ANEES is chi-squared distributed with N n_x degrees of freedom"; two-sided bounds r1 = (1/N) F⁻¹(α/2, N n_x), r2 = (1/N) F⁻¹(1 − α/2, N n_x); reference Bar-Shalom, Li, Kirubarajan, *Estimation with Applications to Tracking and Navigation* (Wiley, 2001) — [kalman-filter.com NEES](https://kalman-filter.com/normalized-estimation-error-squared/)
- NIS is recommended "exclusively or additionally to the NEES, because it does not require access to the true state vector" — [kalman-filter.com NEES](https://kalman-filter.com/normalized-estimation-error-squared/)
- Chi-square-distributed normalized errors are used in recent work to auto-tune filter noise (enforcing NEES/NIS distributions with Bayesian optimization), showing the test is a current accepted tuning/validation tool — [arXiv 2306.07225](https://arxiv.org/html/2306.07225)
- [computed] 95% acceptance interval for averaged NEES with n_x = 6 (6-DoF pose): N=1: [1.24, 14.45]; N=10: [4.05, 8.33]; N=25: [4.72, 7.43]; N=50: [5.08, 7.00]; N=100: [5.34, 6.70] (scipy chi2.ppf(0.025/0.975, 6N)/N).

### Inferences
- [Inference] Procedure for the thesis: in Gazebo (ground truth available), for each frame compute e = Log(T_gt⁻¹ T_est) (6-vector) and P = H⁻¹ (scaled by the measurement noise variance σ² if H is unnormalized); compute ε = eᵀP⁻¹e. Over N repeated runs (different noise seeds) or over a time window, check ANEES within the χ² bounds. If ANEES ≫ upper bound the Hessian covariance is overconfident (common for ICP, since point correlations are ignored) and any CRLB-based threshold derived from it is miscalibrated; if consistent, the threshold has empirical support.
- [Inference] Per-direction check: project e onto each eigenvector v_k; (v_kᵀe)² · λ_k / σ² should be ~χ²(1). This tests whether eigenvalue λ_k actually predicts error variance along v_k — a direct, non-circular validation of an eigenvalue/CRLB threshold.
- [Inference] Time-averaged NEES over K frames of one run is only valid if errors are approximately independent across frames, which is false for odometry drift; prefer N independent Monte Carlo runs at the registration level (single scan pair, perturbed initial guess and noise).

### Gaps
- Did not access the Bar-Shalom textbook directly (Sections 5.4 / 11.x on consistency); formula taken from a secondary source that cites it. Did not find a SLAM-degeneracy paper that uses NEES to validate a degeneracy threshold specifically.

## Q4. Monte Carlo sample size: Wilson interval and n for ±0.03 at 95%; multiple seeds

### Takeaway
Use Wilson (or Clopper-Pearson) intervals for recall/accuracy estimates, per Brown, Cai & DasGupta (2001). For a ±0.03 half-width at 95% confidence, worst case (p = 0.5) requires n ≈ 1,064–1,068; if the expected rate is ~0.9, n ≈ 385–388. The thesis's 400 and 800 trials give worst-case half-widths of ≈ ±0.049 and ±0.035. Report results over several independent seeds rather than one.

### Cited Findings
- Wilson score interval: centre (k + z²/2)/(n + z²), a weighted average of p̂ and 1/2 giving p̂ more weight as n grows; Clopper-Pearson uses beta/F quantiles and "never has less than the nominal coverage" but is conservative — [Binomial proportion CI (Wikipedia copy)](https://dornsife.usc.edu/sergey-lototsky/wp-content/uploads/sites/211/2025/06/BinomialCI-Wiki.pdf)
- Brown, Cai & DasGupta (2001), "Interval Estimation for a Binomial Proportion", *Statistical Science* 16(2):101–133: Wald interval coverage is erratic ("chaotic"), recommends Wilson or Jeffreys for small n and Agresti-Coull for larger n — [ResearchGate](https://www.researchgate.net/publication/258237345_Interval_Estimation_for_a_Binomial_Proportion); summary in [tryvantage paper trail](https://tryvantage.co/insights/paper-trail-brown-cai-dasgupta-2001) (secondary)
- Wilson (1927) formula (standard form): p ∈ [ (p̂ + z²/(2n) ± z·sqrt(p̂(1−p̂)/n + z²/(4n²))) / (1 + z²/n) ]; equivalently centre (k + z²/2)/(n + z²), half-width z·sqrt(n p̂(1−p̂) + z²/4)/(n + z²) — [Wilson score interval reference](https://statisticsfundamentals.com/confidence-intervals/wilson-score-interval/) (secondary; consistent with [Binomial CI](https://dornsife.usc.edu/sergey-lototsky/wp-content/uploads/sites/211/2025/06/BinomialCI-Wiki.pdf))
- [computed] Sample size for half-width ≤ 0.03, 95% (z = 1.96): Wald n = z²p(1−p)/E² → p=0.5: 1068; p=0.8: 683; p=0.9: 385; p=0.95: 203. Wilson (exact search): p=0.5: 1064; p=0.8: 682; p=0.9: 388; p=0.95: 215.
- [computed] Wilson 95% half-widths: n=400 → ±0.049 (p=0.5), ±0.030 (p=0.9); n=800 → ±0.035, ±0.021; n=3000 → ±0.018, ±0.011.
- Multiple seeds are used in recent degeneracy-detector validation: 8 random seeds × 9 configurations — [arXiv 2608.15532](https://arxiv.org/html/2608.15532)

### Inferences
- [Inference] Justify n a priori: state the target margin (e.g., ±0.03) and the planning value of p (0.5 worst case), giving n ≈ 1,070 per condition; or justify 400 post hoc only if observed p ≥ 0.9.
- [Inference] Use S ≥ 5–10 independent seeds, report mean ± std (or min–max) of the metric across seeds in addition to the pooled Wilson CI; seed-to-seed variation exposes sensitivity that a single seed hides.
- [Inference] When comparing two detectors on the same trials, use a paired test (McNemar's test) rather than overlapping CIs.

### Gaps
- Did not fetch Wilson 1927 or Brown et al. 2001 full text directly.

## Q5. Threshold selection: ROC / PR curves, sensitivity sweeps, held-out data

### Takeaway
Thresholds should be chosen on a tuning set with an independent ground truth by sweeping the threshold and plotting ROC (TPR vs FPR) or precision-recall (preferred when degenerate frames are rare), then fixed and evaluated on held-out sequences. The degeneracy literature mostly tunes on one experiment and reuses values; the 2026 "Degenerate in Whose Frame?" paper shows threshold intervals often do not transfer across noise/voxel settings.

### Cited Findings
- Tuna et al. 2025 tune parameter-dependent methods "based on performance in the Ulmberg bicycle tunnel experiment" and then apply them to other experiments (implicit train/test split by environment) — [arXiv 2408.11809](https://arxiv.org/pdf/2408.11809)
- X-ICP claims localizability detection "without environment-specific parameter tuning" yet changes κf with LiDAR model — [X-ICP ar5iv](https://ar5iv.labs.arxiv.org/html/2211.16335); [X-ICP arXiv PDF](https://arxiv.org/pdf/2211.16335)
- Robust-threshold criterion: a threshold interval that reproduces known degenerate counts across all 9 noise/voxel configurations; for conventional metrics "the intersection is empty" — [arXiv 2608.15532](https://arxiv.org/html/2608.15532)
- DCReg uses fixed κth = 10, minimum-eigenvalue threshold 120 — [DCReg arXiv PDF](https://arxiv.org/pdf/2509.06285)

### Inferences
- [Inference] Recommended protocol: (1) build labelled data with detector-independent ground truth (Q1); (2) split by sequence/environment into tuning and test sets (never by random frames within one run, because adjacent frames are correlated); (3) sweep threshold over a log grid, plot ROC and PR with AUC/AP and pick the operating point by a stated criterion (max F1, Youden's J, or recall ≥ target); (4) report test-set metrics with Wilson CIs; (5) sensitivity sweep: show ATE/RPE of the full pipeline versus threshold (e.g., ±1 decade) to show a plateau rather than a knife-edge.
- [Inference] If a threshold is CRLB-derived, the sweep should show the analytic value falls within the empirically good range; NEES (Q3) provides the calibration evidence.

### Gaps
- No primary statistics/ML citation was fetched for ROC vs PR (e.g., Saito & Rehmsmeier 2015, Davis & Goadrich 2006); add if needed.

## Q6. Ablation design for multi-component SLAM pipelines; handling confounds on a single run

### Takeaway
Comparing mean error per mode on one run is confounded because the mode is chosen by the detector based on the scene: degenerate segments are intrinsically harder. The accepted alternative is controlled ablation: run the whole trajectory several times with each configuration forced (e.g., LiDAR-only, LiDAR+IMU, LiDAR+visual, full adaptive switching, switching with each component disabled), same input data, multiple seeds, and compare per-segment and whole-trajectory ATE/RPE.

### Cited Findings
- Tuna et al. 2025 isolate the effect of mitigation by holding the detector fixed ("all works ... use the degeneracy detection method described in X-ICP ... to ensure a fair comparison") — a one-factor-at-a-time design — [arXiv 2408.11809](https://arxiv.org/pdf/2408.11809)
- DCReg compares against baselines on identical datasets with ATE, AC and CD, and separately analyses detection (Schur vs diagonal) — [DCReg arXiv PDF](https://arxiv.org/pdf/2509.06285)
- Zhang & Scaramuzza stress identical alignment across compared algorithms for fairness — [Zhang & Scaramuzza 2018 PDF](https://rpg.ifi.uzh.ch/docs/IROS18_Zhang.pdf)

### Inferences
- [Inference] Confound control options, strongest first: (a) Forced-mode ablation: replay the same rosbag/Gazebo run with each mode forced for the entire trajectory and with adaptive switching; compare per-segment errors (segment labelled by the independent ground truth, e.g., corridor vs open) — this is a within-segment, counterfactual comparison. (b) Per-segment stratification: compare modes only within the same segment type and report RPE per segment, not pooled means. (c) Use relative error (RPE over fixed distance) rather than absolute pose error per frame, since ATE at frame k accumulates drift from earlier segments — a mode active late in the run inherits earlier error (temporal confound).
- [Inference] Use paired statistics: per segment, difference in RPE between adaptive and forced modes, with Wilcoxon signed-rank test across segments × runs; report effect sizes.
- [Inference] Ablation table rows: full system; − degeneracy detector (always fuse); − visual; − IMU; detector variant A/B/C; threshold at ±1 decade; each with N runs, median ATE and RPE, failure count.
- [Inference] The 4017-frame log can still be used for detection evaluation if each frame is labelled with an independent degeneracy reference (geometry from the Gazebo world, or GT-error-projected label), but not as causal evidence that switching reduces error.

### Gaps
- No methodological paper on ablation design specifically for SLAM pipelines was found; recommendations are inferred from practice in the cited papers.

## Q7. Public datasets with LiDAR degeneracy and simulated setups

### Takeaway
Suitable LiDAR(-visual)-inertial datasets with geometric degeneracy and independent ground truth: GEODE (64 trajectories, 64 km, tunnels/bridges/stairs etc., 3 LiDAR types + stereo camera), SubT-MRS, ENWIDE (X-ICP lineage), FusionPortable, Ulmberg tunnel / ANYmal forest (Tuna et al.), NTNU lidar_degeneracy_datasets (tunnel + fog corridor, no GT), HK_MEMS, M2TD; plus Hilti, M2DGR, Newer College (named in the brief; not verified in this session). Synthetic corridors/cylinders with analytically known degenerate directions are the standard simulated setup.

### Cited Findings
- GEODE (Heterogeneous LiDAR Dataset for Benchmarking Robust Localization in Diverse Degenerate Scenarios, arXiv 2409.04961): Velodyne VLP-16, Ouster OS1-64, Livox AVIA; IMUs Xsens MTi-30, ICM-20948, BMI088; HikRobot stereo cameras; "seven diverse settings": flat ground, stairs, metro tunnels, off-road, inland waterways, urban tunnels, bridges; GT by GNSS-RTK/INS, Leica MS60 / RTC360 laser tracker/scanner, Vicon, PALoc; "64 trajectories spanning over 64 kilometers"; compared against ENWIDE, CERBERUS, CoSTAR, CTU-CRAS-Norlab, SubT-MRS — [GEODE arXiv](https://arxiv.org/html/2409.04961v1); [GEODE GitHub](https://github.com/PengYu-Team/GEODE_dataset); [GEODE site](https://thisparticle.github.io/geode/)
- DCReg evaluates on FusionPortable, GEODE, SubT-MRS and self-collected sequences with RTK-INS ground truth — [DCReg arXiv PDF](https://arxiv.org/pdf/2509.06285)
- Tuna et al. 2025 field data: ANYmal forest, Ulmberg bicycle tunnel (>80% degenerate), HEAP excavator — [arXiv 2408.11809](https://arxiv.org/pdf/2408.11809)
- X-ICP: simulation with known degenerate directions and Seemühle mine with Leica RTC360 GT map/trajectory — [X-ICP arXiv PDF](https://arxiv.org/pdf/2211.16335)
- NTNU lidar_degeneracy_datasets: Fyllingsdalen tunnel (8 m wide, 500 m straight) and fog-filled NTNU corridor; Ouster OS0-128 (10 Hz), VectorNav VN100 IMU (200 Hz), TI IWR6843AOP radar; no explicit GT; ICRA 2024 "Degradation Resilient LiDAR-Radar-Inertial Odometry" (Nissov, Khedekar, Alexis) — [NTNU GitHub](https://github.com/ntnu-arl/lidar_degeneracy_datasets)
- HK_MEMS multi-LiDAR dataset on degenerate and dynamic urban scenarios — [HK_MEMS GitHub](https://github.com/RuanJY/HK_MEMS_Dataset); M2TD tunnel dataset with LiDAR–IMU–Camera–UWB and low-cost GT — [M2TD GitHub](https://github.com/longlongzxl/M2TD); index of datasets — [Awesome-3D-LiDAR-Datasets](https://github.com/minwoo0611/Awesome-3D-LiDAR-Datasets)
- Synthetic setups: symmetric cylinder (7600 points; Tuna et al. / DCReg) — [DCReg arXiv PDF](https://arxiv.org/pdf/2509.06285); rectangular corridor (1 DOF), circular corridor (2 DOF), right-angle corner (0 DOF) — [arXiv 2608.15532](https://arxiv.org/html/2608.15532)

### Inferences
- [Inference] For a LiDAR-visual-inertial thesis, GEODE is the best fit (camera + IMU + multiple LiDARs, tunnel/bridge degeneracy, independent GT, used by DCReg so results are comparable). SubT-MRS adds multi-modal degraded conditions.
- [Inference] Gazebo: build a long featureless rectangular corridor (known 1-DOF translational degeneracy along the axis), a circular tunnel (adds roll), and a corridor with a junction/corner (non-degenerate control), so each frame's ground-truth degeneracy is known from the world model; add textured vs untextured walls to separately control visual degeneracy.

### Gaps
- Did not verify Hilti, M2DGR, Newer College, ENWIDE or SubT-MRS details (sensors, GT accuracy, degeneracy content) in this session; ENWIDE's exact contents not fetched.
