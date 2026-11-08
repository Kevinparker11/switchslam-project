# Prompt: systematic review paper on LiDAR degeneracy (paste everything below into a new chat)

---

## 1. Who I am and what I want

I am Kavinkumar S (CB.EN.P2MFA25004), M.Tech student in Manufacturing and Automation, Department of Mechanical Engineering, Amrita School of Engineering, Coimbatore, Amrita Vishwa Vidyapeetham, India. My advisor is Dr. G. Sivasankar, Department of Mechanical Engineering. My thesis is "Degeneracy Detection and Mitigation in LiDAR-Inertial-Visual SLAM" (November 2026).

Write a **journal review paper** that I can submit to a Scopus-indexed journal. The format is IEEE (IEEEtran, journal mode). The paper must be a real systematic review, publishable on its merits. It should contain about 100 to 130 references. Every reference must exist, be relevant, and be verified by you. Do not pad the list. If only 90 good papers exist, use 90 and tell me.

Working title (you may improve it):
**"LiDAR Degeneracy in SLAM: A Systematic Review of Detection, Mitigation, Multi-Sensor Fusion, and Evaluation Practice"**

Target journals, in order. Check the current scope, Scopus indexing, article type, length limit and fees of each before choosing, and tell me what you found:
1. IEEE Access (survey/review articles accepted; IEEE template).
2. IEEE Sensors Journal (review articles).
3. Robotics and Autonomous Systems (Elsevier) or Journal of Field Robotics (Wiley), if IEEE does not fit.
4. Sensors or Remote Sensing (MDPI), as a fallback.
Write the paper in the IEEE format first. Reformatting for another journal can happen later.

---

## 2. Rules you must follow (non-negotiable)

1. **No invented references.** Before you cite a paper, open a source that confirms it exists: the DOI or Crossref record, the arXiv abstract page, the publisher page, CVF Open Access, RSS proceedings or IEEE Xplore. Record which one you opened.
2. **No invented numbers.** Every number taken from a paper (RMSE, thresholds, dataset sizes) must come from text you actually read. If you only saw an abstract, cite only what the abstract says. Mark anything you could not check as "not verified" and leave it out of the manuscript.
3. **Mark preprints.** arXiv-only papers are cited as "arXiv:xxxx.xxxxx" with the year. Look for a published version first, and cite that if it exists.
4. **IEEE reference style.** Use more than six authors -> first author et al. Give the full venue, volume, issue, pages, month, year and DOI where they exist. Number the references in order of first citation.
5. **Paraphrase, do not copy.** Target under 15% similarity. Do not copy figures from other papers. Redraw every diagram yourself as original vector art.
6. **Be honest about the literature.** Say clearly where the evidence is weak. Examples: thresholds are tuned on the authors' own data; there are few detection labels; methods are run on different sequences; some results were never reproduced.
7. **No em dashes** in the manuscript. Use plain, direct academic English.
8. **AI disclosure.** IEEE requires disclosure of AI-generated text. Draft a short acknowledgment that states AI assistance was used for literature search, drafting and editing, and that the authors verified all content.
9. **Keep a search log.** Record every database, query, date, hit count, and the number screened, excluded and included. The PRISMA diagram must use these real counts, not made-up ones.

---

## 3. Review methodology (write it into the paper as Section II)

Follow **PRISMA 2020** for a systematic review, adapted to robotics.

- **Databases:** IEEE Xplore, Scopus, Web of Science (if reachable), Google Scholar, arXiv (cs.RO, cs.CV), ACM Digital Library, ScienceDirect, SpringerLink, Wiley, MDPI, plus RSS and CVF proceedings.
- **Snowballing:** check backward and forward citations from the seed papers in Section 7. Also use the GitHub list "Awesome-Algorithms-Against-Degeneracy" (github.com/thisparticle/Awesome-Algorithms-Against-Degeneracy), maintained by the GEODE authors, as a seed source.
- **Example search strings** (adapt them per database):
  - ("LiDAR" OR "laser scan") AND ("degeneracy" OR "degenerate" OR "localizability" OR "ill-conditioned" OR "observability") AND ("SLAM" OR "odometry" OR "registration" OR "ICP")
  - ("LiDAR-visual-inertial" OR "LiDAR-inertial-visual" OR "LVI") AND ("degenerate" OR "failure detection" OR "switching")
  - ("geometrically degenerate" OR "feature-poor" OR "self-similar") AND ("tunnel" OR "corridor" OR "cave" OR "open field")
  - ("degeneracy" OR "localizability") AND ("dataset" OR "benchmark")
- **Time window:** 2001 (Rusinkiewicz and Levoy ICP variants) and 2003 (Gelfand stable sampling) to November 2026. Weight the review toward 2016 to 2026.
- **Inclusion:** peer-reviewed journal and conference papers, or arXiv preprints with clear technical content, that (a) define, detect or mitigate degeneracy in LiDAR-based state estimation, or (b) fuse other sensors because of LiDAR degeneracy, or (c) provide datasets or benchmarks for degenerate scenes. Also include foundational SLAM and LiDAR odometry papers needed for context.
- **Exclusion:** papers that are not about LiDAR or range sensing (unless they are directly needed, for example VINS-Mono as a fusion component), non-English papers, patents, and papers whose existence cannot be confirmed.
- **Data extraction per paper:** the sensor setup; the degeneracy statistic; the threshold and how it was chosen; the mitigation; the fusion strategy; the datasets; the metrics; the main result; whether code is released; and whether detection was scored against labels.
- **Quality appraisal:** a simple checklist per paper. Did it use a public dataset? Report repeated runs? Release code? Compare against prior degeneracy methods? Score detection against labels? Choose thresholds on separate data from evaluation?

---

## 4. Required structure of the manuscript

Use the IEEEtran journal template with this order:

- **Title, authors, affiliations.** Authors: Kavinkumar S and Dr. G. Sivasankar (confirm the advisor's designation and both email addresses with me).
- **Abstract** (200 to 250 words, one paragraph, no citations) and **Index Terms** (6 to 8).
- **I. Introduction:** why degeneracy matters (tunnels, corridors, caves, mines, open fields, planetary analogues; DARPA SubT); the scope; how this review differs from existing surveys (find and compare all prior SLAM and LiDAR surveys, for example Cadena 2016 and Ebadi 2024, and any degeneracy-specific surveys you find); and a contributions list.
- **II. Review Methodology:** PRISMA flow, databases, queries, criteria, and counts.
- **III. Background and Definitions:** the registration problem; point-to-plane and point-to-line residuals; the Gauss-Newton Hessian H = JᵀJ and its rotation and translation blocks; Fisher information and observability; types of degeneracy (translational, rotational, coupled; geometric versus solver-induced; full versus partial); and the scale disparity between rotation and translation.
- **IV. Degeneracy Detection.** Sub-taxonomy:
  - (A) Hessian eigenvalue and condition-number methods: Zhang et al. 2016; Hinduja 2019; Switch-SLAM; DCReg Schur-complement.
  - (B) Per-correspondence localizability: X-ICP, LP-ICP.
  - (C) Pre-solve scan or map geometry: Gelfand covariance; SuperLoc; ICET; LF-GICP; normal-vector methods such as NV-LIO(M).
  - (D) Probabilistic and noise-aware: DRPM by Hatleskog and Alexis.
  - (E) Learning-based: Nubert et al. 2022.
  - (F) Perturbation and re-optimisation: LiLi.
  - (G) Frame and scale invariance: "Degenerate in Whose Frame?", arXiv 2608.15532.
  - Include a subsection on **how thresholds are chosen** (empirical, user-defined, basin of convergence, statistical) and their portability.
- **V. Degeneracy Mitigation in Registration:** solution remapping; truncated SVD; Tikhonov regularisation; equality and inequality constraints; preconditioned conjugate gradient (DCReg); stable sampling; adaptive point-to-point and point-to-plane weighting (GenZ-ICP); point-to-line terms; robust kernels; and the field comparison of these strategies by Tuna et al. (T-FR 2025).
- **VI. Multi-Sensor Fusion Under LiDAR Degeneracy:**
  - (A) Switching and failure detection: Switch-SLAM; LVI-SAM and VINS-Mono failure detection; Super Odometry; CompSLAM.
  - (B) Tightly coupled LiDAR-visual-inertial systems: LIC-Fusion, VIL-SLAM, R2LIVE, R3LIVE, FAST-LIVO, FAST-LIVO2, and others you find.
  - (C) Direction-wise or selective fusion: Selective KF ("Fuse only what matters"), SA-LIVO, Liao et al. arXiv 2412.07513, ALIVE-LIO, MM-LINS, D²-LIO, RELEAD.
  - (D) Other modalities: radar, thermal, UWB, wheel and leg odometry. Search for these; I have few seeds here.
  - (E) Visual degeneracy happening at the same time, which matters for fusion.
- **VII. Back-End and Loop Closure in Degenerate Scenes:** degeneracy-aware factors (Hinduja), DARE-SLAM, pose-graph consequences, and the risk of false loop closures in self-similar corridors.
- **VIII. Datasets, Ground Truth and Evaluation Practice:** a table of every degeneracy-relevant dataset (Section 7.4); how ground truth is produced (FARO or Leica scans, total station, RTK); metrics (ATE RMSE and max, RPE, degeneracy ratio, detection precision and recall); the shortage of per-frame degeneracy labels; and the practice of inducing degeneracy artificially (range limits, FOV cuts).
- **IX. Comparative Analysis:** cross-paper results tables on shared sequences (SubT-MRS Multi Floor, Long Corridor, Cave02, Corridor02; GEODE; CERBERUS). State clearly that numbers from different papers are not directly comparable unless the setup matches.
- **X. Open Challenges and Future Directions:** threshold calibration with a statistical null; labelled benchmarks; frame equivariance; reproducibility; solid-state and low-cost LiDARs; learning-based detectors that generalise; joint LiDAR and visual degeneracy; compute limits on embedded platforms; and standard reporting (repeated runs, held-out data).
- **XI. Conclusion.**
- **Acknowledgment** (including the AI disclosure), **References**, and **author biographies** with photo placeholders (IEEE Access needs them).

Length: about 12,000 to 16,000 words including tables. Check the target journal's limit.

---

## 5. Required tables and figures (all original)

**Tables:**
1. Comparison with existing surveys: scope, year, number of references, and whether each covers detection, mitigation, fusion and datasets.
2. PRISMA counts per database.
3. Detection methods: statistic, matrix used (full H, blocks, Schur, normals), pre- or post-solve, how the threshold is set, frame-invariant or not, code released, scored against labels or not.
4. Mitigation methods: type (hard, soft, regularised, preconditioned, sampling), where it acts in the solver, and the main limitation.
5. Fusion systems: sensors, coupling (loose, tight, switching, direction-wise), decision variable, back end, and datasets.
6. Datasets: platform, LiDAR, camera, IMU, environment, degeneracy type, GT source and accuracy, and availability.
7. Cross-paper results on shared sequences, with a column saying what differs between setups.
8. Quality-appraisal summary across included papers.
9. Open problems mapped to the papers that partly address them.

**Figures:** draw these as vector graphics (TikZ or SVG to PDF):
1. PRISMA 2020 flow diagram with the real counts.
2. Taxonomy tree of the field.
3. Publications per year and per category (from your extraction table).
4. Degenerate geometries: corridor (one sliding direction), tunnel or cylinder (two directions), open plane, and stairs, with the weak directions marked.
5. Detection pipeline positions: pre-solve versus in-solve versus post-solve.
6. Fusion architectures: switching versus tightly coupled versus direction-wise.
7. A timeline of the main milestones, 2003 to 2026.

---

## 6. What my own project found (use it as critical-analysis input, clearly labelled)

These are results from my thesis. They are **not published**. In the review, use them only (a) as a short labelled "reproducibility case study" box or subsection, or (b) in the open-challenges discussion. Write "in the authors' re-implementation" every time. If the target journal does not accept new experimental results in a review, move this material to the discussion and remove the numbers. Ask me before using them.

**System:** A-LOAM (LiDAR) plus VINS-Mono (visual-inertial). The final version is "F24", a VIO-primary fusion. It adds a Schur-complement information-weighted LiDAR translation correction, VIO consistency checks, a LiDAR guard, an anchored handover and a prediction guard. It was compared against my re-implementation of Switch-SLAM's Algorithm 1 ("SW"), with frozen settings. Metric: ATE RMSE and max (m), Umeyama SE(3) alignment, no scale, full trajectory, front end only (no loop closure) unless stated.

**Switch-SLAM published front-end results (Table II, RA-L 2024; mean of 3 runs):** Multi Floor 1.61 / 3.63; Long Corridor 2.42 / 5.09; Farm (Gazebo) 0.38 / 1.10.

**Replication finding:** my SW re-implementation did **not** reproduce the published numbers. Multi Floor gave 5.03 / 10.22 and 5.44 / 10.94 (two runs). On Long Corridor, both SW and the SWI variant gave about 13 m (two runs each). A variant (SWI) reached 1.51 / 4.35 on Multi Floor in one run, which is not a reproduction claim. The causes are not isolated. The candidates are stack differences and parameters the paper does not specify. Use this to support the reproducibility point: published detectors leave key parameters unspecified.

**Threshold critique (my own analysis; I found no published critique).** Switch-SLAM normalises the three smallest Hessian eigenvalues and gives thresholds λ_t = e_m - sqrt(0.103·e_m), with expectations e = [0.289, 0.498, 0.749] and thresholds [0.12, 0.27, 0.48]. It calls 0.103 the chi-square value for 2 DOF at 95%. But the chi-square(2) CDF at 0.103 is 1 - exp(-0.0515) ≈ 0.050. So 0.103 is the **lower** 5% point; the upper 95% critical value is 5.991. Putting 5.991 into the formula gives negative thresholds, so the rule could never fire. In addition, Pearson's statistic needs counts, and the semicircle law does not apply to the positive semidefinite matrix JᵀJ. Present this as "our analysis indicates" and invite verification. Do not overstate it.

**F24 results (development data unless marked; n = number of runs):**
- Multi Floor: 0.45 / 0.92, 1.01 / 1.73, 0.69 / 1.24 (n=3, mean 0.72 / 1.30).
- Long Corridor: 2.12 / 5.31, 2.15 / 5.57, 1.75 / 3.53 (n=3).
- SubT-MRS Corridor02 (the SuperLoc release: Hawkins, RC1, 690 m, 893 s): 1.47 / 2.51 (n=1). With an offline loop-closure back end: 1.11 / 2.15.
- Cave02: 7.55 / 12.63 (n=1). Earlier versions reached about 4.4, so this is a possible regression. More runs are in progress; I will send you the updated numbers.
- GEODE stairs alpha (0.5x replay): 6.15 / 14.00 and 9.15 / 25.44. At 0.25x: 9.09 / 19.42. The results are limited by A-LOAM.
- Gazebo Farm: 0.657 / 0.897 on the original rig. On the forward-camera RGB 60 Hz rig: 0.472 / 1.068 (n=1). The forward rig is not paper-matched.
- Multi Floor, Long Corridor and Farm were used during design, so they are **not held-out**.

**Published results on Corridor02** (from GenZ-LIO Table 4, read on 21 Oct 2026; **re-verify before use**): FAST-LIO2 1.89, Faster-LIO 2.88, AdaLIO 1.98, Point-LIO 1.74, LIO-EKF 65.59, DLIO 1.39, iG-LIO 1.48, PV-LIO 0.73, GenZ-LIO 0.69 (ATE RMSE, m).

**Published Cave02 context (DCReg Table 5, scan-to-map localisation with a prior map, so not comparable to odometry):** DCReg 4.57 cm against minimum-eigenvalue variants of 209 to 566 cm.

**Lessons from the project for the open-challenges section:**
- Detection thresholds are almost always tuned on the authors' own data.
- Only Switch-SLAM scores detection against labels. Its labels come from GNSS-versus-ICP disagreement on part of one dataset.
- Several papers induce degeneracy artificially (DCReg range limits; Switch-SLAM cuts the CERBERUS field of view to 180°).
- Methods are evaluated on different sequences, so cross-paper comparison is weak.
- Results vary run to run. My Multi Floor RMSE ranged from 0.45 to 1.01 across three identical runs. Single-run results support no claim.
- Fixed eigenvalue thresholds depend on point count, weights, scene scale, noise (Hatleskog and Alexis), and the body frame (arXiv 2608.15532).

---

## 7. Seed reference list (start here, then extend to about 100 to 130)

### 7.1 Already verified (IEEE strings checked against Crossref or arXiv on 9 Oct 2026; re-check DOIs)

1. C. Cadena *et al.*, "Past, present, and future of simultaneous localization and mapping: Toward the robust-perception age," *IEEE Trans. Robot.*, vol. 32, no. 6, pp. 1309-1332, Dec. 2016, doi: 10.1109/TRO.2016.2624754.
2. K. Ebadi *et al.*, "Present and future of SLAM in extreme environments: The DARPA SubT challenge," *IEEE Trans. Robot.*, vol. 40, pp. 936-959, 2024, doi: 10.1109/TRO.2023.3323938.
3. J. Zhang and S. Singh, "LOAM: Lidar odometry and mapping in real-time," in *Proc. Robot.: Sci. Syst.*, 2014, doi: 10.15607/RSS.2014.X.007.
4. T. Shan and B. Englot, "LeGO-LOAM: Lightweight and ground-optimized lidar odometry and mapping on variable terrain," in *Proc. IEEE/RSJ IROS*, 2018, pp. 4758-4765, doi: 10.1109/IROS.2018.8594299.
5. T. Shan *et al.*, "LIO-SAM: Tightly-coupled lidar inertial odometry via smoothing and mapping," in *Proc. IEEE/RSJ IROS*, 2020, pp. 5135-5142, doi: 10.1109/IROS45743.2020.9341176.
6. W. Xu, Y. Cai, D. He, J. Lin, and F. Zhang, "FAST-LIO2: Fast direct LiDAR-inertial odometry," *IEEE Trans. Robot.*, vol. 38, no. 4, pp. 2053-2073, Aug. 2022, doi: 10.1109/TRO.2022.3141876.
7. J. Zhang, M. Kaess, and S. Singh, "On degeneracy of optimization-based state estimation problems," in *Proc. IEEE ICRA*, 2016, pp. 809-816, doi: 10.1109/ICRA.2016.7487211.
8. N. Gelfand, L. Ikemoto, S. Rusinkiewicz, and M. Levoy, "Geometrically stable sampling for the ICP algorithm," in *Proc. 3DIM*, 2003, pp. 260-267, doi: 10.1109/IM.2003.1240258.
9. A. Hinduja, B.-J. Ho, and M. Kaess, "Degeneracy-aware factors with applications to underwater SLAM," in *Proc. IEEE/RSJ IROS*, 2019, pp. 1293-1299, doi: 10.1109/IROS40897.2019.8968577.
10. T. Tuna, J. Nubert, Y. Nava, S. Khattak, and M. Hutter, "X-ICP: Localizability-aware LiDAR registration for robust localization in extreme environments," *IEEE Trans. Robot.*, vol. 40, pp. 452-471, 2024, doi: 10.1109/TRO.2023.3335691.
11. J. Nubert, E. Walther, S. Khattak, and M. Hutter, "Learning-based localizability estimation for robust LiDAR localization," in *Proc. IEEE/RSJ IROS*, 2022, pp. 17-24, doi: 10.1109/IROS47612.2022.9982257.
12. T. Tuna *et al.*, "Informed, constrained, aligned: A field analysis on degeneracy-aware point cloud registration in the wild," *IEEE Trans. Field Robot.*, vol. 2, pp. 485-515, 2025, doi: 10.1109/TFR.2025.3576053.
13. X. Hu *et al.*, "DCReg: Decoupled characterization for efficient degenerate LiDAR registration," *Int. J. Robot. Res.*, early access, Aug. 2026, doi: 10.1177/02783649261465040 (arXiv:2509.06285).
14. D. Chung and J. Kim, "NV-LIOM: LiDAR-inertial odometry and mapping using normal vectors towards robust SLAM in multifloor environments," *IEEE Robot. Autom. Lett.*, vol. 9, no. 11, pp. 9375-9382, Nov. 2024, doi: 10.1109/LRA.2024.3457373.
15. E. Im, "LF-GICP: Parameter-free degeneracy-aware LiDAR odometry via a voxel-normal localizability field," arXiv:2608.19522, 2026.
16. J. Hatleskog and K. Alexis, "Probabilistic degeneracy detection for point-to-plane error minimization," *IEEE Robot. Autom. Lett.*, vol. 9, no. 12, pp. 11234-11241, Dec. 2024, doi: 10.1109/LRA.2024.3484153.
17. Z. Chen *et al.*, "RELEAD: Resilient localization with enhanced LiDAR odometry in adverse environments," in *Proc. IEEE ICRA*, 2024, pp. 3999-4005, doi: 10.1109/ICRA57147.2024.10611074.
18. T. Qin, P. Li, and S. Shen, "VINS-Mono: A robust and versatile monocular visual-inertial state estimator," *IEEE Trans. Robot.*, vol. 34, no. 4, pp. 1004-1020, Aug. 2018, doi: 10.1109/TRO.2018.2853729.
19. J. Lee *et al.*, "Switch-SLAM: Switching-based LiDAR-inertial-visual SLAM for degenerate environments," *IEEE Robot. Autom. Lett.*, vol. 9, no. 8, pp. 7270-7277, Aug. 2024, doi: 10.1109/LRA.2024.3421792.
20. S. Zhao *et al.*, "SubT-MRS dataset: Pushing SLAM towards all-weather environments," in *Proc. IEEE/CVF CVPR*, 2024, pp. 22647-22657 (find the DOI).
21. Z. Chen *et al.*, "Heterogeneous LiDAR dataset for benchmarking robust localization in diverse degenerate scenarios," *Int. J. Robot. Res.*, vol. 45, no. 1, pp. 6-22, Jan. 2026, doi: 10.1177/02783649251344967 (GEODE).
22. J. Jiao *et al.*, "FusionPortable: A multi-sensor campus-scene dataset ...," in *Proc. IEEE/RSJ IROS*, 2022, pp. 3851-3856, doi: 10.1109/IROS47612.2022.9982119.
23. T. Shan, B. Englot, C. Ratti, and D. Rus, "LVI-SAM: Tightly-coupled lidar-visual-inertial odometry via smoothing and mapping," in *Proc. IEEE ICRA*, 2021, pp. 5692-5698, doi: 10.1109/ICRA48506.2021.9561996.
24. H. Yue, Q. Xu, F. Chen, J. Pan, and W. Chen, "LP-ICP: General localizability-aware point cloud registration for robust localization in extreme unstructured environments," arXiv:2501.02580, 2025 (look for a published version).
25. T. Qin and S. Cao, "A-LOAM: Advanced implementation of LOAM," GitHub repository. [Online]. Available: https://github.com/HKUST-Aerial-Robotics/A-LOAM

### 7.2 Found in the project but not fully verified (verify each one)

**Detection and registration:**
- SuperLoc (Zhao et al., ICRA 2025, arXiv:2412.02901)
- ICET (McDermott and Rife, NAVIGATION 71(2), 2024, arXiv:2306.08690)
- GenZ-ICP (Lee, Lim, Han, RA-L, arXiv:2411.06766)
- DAMM-LOAM (arXiv:2510.13287)
- D²-LIO (arXiv:2508.14355)
- LiLi (Hulchuk, Bayer, Faigl, arXiv:2609.17145)
- "Degenerate in Whose Frame? An Equivariance Condition for Degeneracy Detection in LiDAR Registration" (arXiv:2608.15532)
- PALoc (Hu et al., arXiv:2401.17826)
- Rusinkiewicz and Levoy, "Efficient variants of the ICP algorithm," 3DIM 2001
- Brossard et al., ICP covariance (arXiv:1909.05722)
- SVN-ICP (arXiv:2509.08069)
- Information-aware odometry (arXiv:2607.13516)
- DeCOD (arXiv:2609.36753)
- KISS-ICP
- GICP and VGICP
- NDT
- Nashed et al., "Curse of degeneracy", cited by Switch-SLAM. I could not locate it; find it or drop it.

**LiDAR-inertial odometry baselines:**
- Faster-LIO
- Point-LIO
- iG-LIO
- DLIO
- DLO
- PV-LIO
- AdaLIO
- LIO-EKF
- GenZ-LIO (arXiv:2603.16273)
- COIN-LIO (Pfreundschuh et al., ICRA 2024, arXiv:2310.01235)
- LODESTAR (arXiv:2511.09142)
- AKF-LIO (arXiv:2503.06891)
- MM-LINS (arXiv:2503.19506)

**Fusion:**
- Super Odometry (Zhao et al., arXiv:2104.14938)
- CompSLAM (Khattak et al., arXiv:2505.06483)
- DARE-SLAM (Ebadi et al., arXiv:2102.05117)
- LIC-Fusion (arXiv:1909.04102)
- VIL-SLAM (arXiv:1902.10741)
- R2LIVE
- R3LIVE (arXiv:2109.07982)
- FAST-LIVO
- FAST-LIVO2 (arXiv:2408.14035)
- Selective KF / "Fuse only what matters" (arXiv:2412.17235, ISPRS J. 2026)
- SA-LIVO (arXiv:2606.25699)
- Liao et al. (arXiv:2412.07513)
- ALIVE-LIO (arXiv:2604.02706)
- FAST-LIVGO (arXiv:2606.19190)
- Ground-Fusion++ (arXiv:2507.08364)
- ORB-SLAM3

**Visual degeneracy and attention:**
- Carlone and Karaman, "Attention and anticipation in fast visual-inertial navigation" (arXiv:1610.03344)
- Zhang and Scaramuzza, Fisher information for active perception (arXiv:2008.03324)
- Structure and Manhattan VIO (MSC-VO arXiv:2111.03408, PGD-VIO arXiv:2407.17709)

**Datasets:**
- SubT-MRS (arXiv:2307.07607)
- GEODE (arXiv:2409.04961)
- CERBERUS DARPA SubT
- ENWIDE (from COIN-LIO)
- NTNU lidar_degeneracy_datasets (Nissov, Khedekar, Alexis, ICRA 2024, arXiv:2403.05332)
- Hilti 2021 (arXiv:2109.11316)
- Hilti-Oxford 2022 (arXiv:2208.09825)
- Hilti 2023 (arXiv:2404.09765)
- Newer College (arXiv:2003.05691) and its multi-camera extension (arXiv:2112.08854)
- FusionPortableV2 (arXiv:2404.08563)
- M2DGR (arXiv:2112.13659)
- M3DGR (arXiv:2507.08364)
- Ground-Challenge (arXiv:2307.03890)
- Botanic Garden (arXiv:2306.14137)
- S3E (arXiv:2210.13723)
- HeLiPR (arXiv:2309.14590)
- MCD (arXiv:2403.11496)
- Oxford Spires (arXiv:2411.10546)
- CAVERS (arXiv:2604.15052)
- DiTer++ (arXiv:2412.05839)
- GrandTour (arXiv:2602.18164)
- TartanGround (arXiv:2505.10696)
- "Large-scale LiDAR-inertial dataset for degradation-robust mapping" (arXiv:2507.20516)
- Solid-state versus spinning LiDAR variability (arXiv:2507.04321)

**Statistics background (use sparingly):**
- Bingham 1974 (Ann. Statist. 2(6), doi: 10.1214/aos/1176342874)
- Mardia and Jupp, *Directional Statistics*, Wiley 2000
- Shi and Tomasi, "Good features to track," CVPR 1994
- The uniformity-tests overview (arXiv:1804.00286)

### 7.3 Gaps to fill by searching

The seed list is thin in these areas. Search for them specifically:
- Radar-LiDAR and thermal-LiDAR fusion in degraded scenes.
- UWB or leg-odometry aiding in tunnels.
- Degeneracy in solid-state LiDARs (Livox).
- Mine and tunnel SLAM papers from field robotics journals.
- Planetary-analogue LiDAR localisation.
- Learning-based degeneracy prediction after 2022.
- Degeneracy in LiDAR-based relocalisation and place recognition.
- Degeneracy-aware loop closure.
- Any earlier survey on LiDAR degeneracy or localizability. If one exists, it changes the contribution statement, so tell me immediately.

---

## 8. How to work (phases and checkpoints)

Work in phases and save each phase's output as a file, so nothing is lost if the chat runs long. After each phase, send me a short status and wait for my "go" only if a decision is mine. Otherwise continue.

1. **Search and screening.** Run the queries, keep the log, build the PRISMA counts, and check that no prior survey makes this one redundant. Output: `search_log.csv` and `prisma_counts.md`.
2. **Reference database.** One row per included paper: IEEE string, DOI or arXiv ID, the source you opened to verify it, category, and the data-extraction fields from Section 3. Output: `references.xlsx` and `refs.bib`. Target 100 to 130 rows.
3. **Outline.** The section and subsection plan with the references assigned to each section. Show it to me before drafting.
4. **Drafting.** Write section by section in LaTeX (IEEEtran journal). Every factual sentence about a paper carries its citation.
5. **Tables and figures.** Build them from the reference database, not from memory.
6. **Compile and check.** Build the PDF. Check that every \cite resolves, that there are no unused bib entries, and that the reference count, page count and word count are as expected. Check the figures at print size.
7. **Independent verification.** Use a separate agent or pass that has not seen the drafting. It re-opens a random 25% of references (and all papers with numbers quoted) and confirms each claim against the source. Fix every mismatch.
8. **Submission package:** the manuscript PDF; the LaTeX source with .bib and figures; a cover letter to the editor; a list of 3 to 5 suggested reviewers with no conflict of interest (verify that they are real and active in the field); the AI-use disclosure; and a highlights list if the journal needs one.

---

## 9. Deliverables I expect at the end

- `review_main.tex`, `refs.bib`, the `figures/` folder, and the compiled `review_main.pdf` (IEEEtran journal).
- `references.xlsx`: the verification table (paper, DOI or arXiv, verified-by source, category, extracted fields).
- `search_log.csv` and the PRISMA diagram source.
- `cover_letter.docx` (or .tex).
- A one-page summary of the contributions, and the list of things I must check or decide (for example author emails, the advisor's designation, whether to include the case-study numbers, and the journal choice).

Start now with Phase 1. Tell me in one line which journal you recommend after checking, and why.
