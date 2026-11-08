# Prompt: comprehensive theoretical review paper on LiDAR degeneracy (paste everything below into a new chat)

---

## 1. Who I am and what I want

I am Kavinkumar S (CB.EN.P2MFA25004), M.Tech student in Manufacturing and Automation, Department of Mechanical Engineering, Amrita School of Engineering, Coimbatore, Amrita Vishwa Vidyapeetham, India. My advisor is Dr. G. Sivasankar, Department of Mechanical Engineering.

Write a **comprehensive, purely theoretical review paper** on **LiDAR degeneracy in SLAM and LiDAR odometry**. I want to submit it to a Scopus-indexed journal, in IEEE format (IEEEtran, journal mode).

**This is a review paper, not a research paper.**
- It has no experiments, no new results, no case study, no simulations, and no benchmark runs of its own.
- Everything in it comes from the published literature. It explains and organises that literature, compares it and critically analyses it.
- Its value is synthesis: a clear explanation of what LiDAR degeneracy is, how the field understood it over time, what has been identified and used, where the gaps are, which solutions are possible, and where future work should go.

**The goal: one paper that tells the whole story.** A reader who reads only this paper should come away knowing the **past, present and future** of LiDAR degeneracy:
- **Past:** where the problem came from and how it was first understood.
- **Present:** every approach in use today, how they relate, and what each can and cannot do.
- **Future:** what is still open and where the field should go.

That makes **coverage the main requirement**. Source **all available papers** on LiDAR degeneracy, from every database, publisher and preprint server you can reach, plus the related papers needed to understand it. There is **no upper limit** on references: a review of this scope will likely need 150 to 250 or more. The only limits are relevance and verification, so every reference must exist, be checked, and earn its place. Do not pad, and do not leave out a relevant paper to keep the list short.

**"Related papers"** means the work needed to understand the topic fully:
- the origins of scan registration and ICP;
- LiDAR odometry and SLAM system families;
- observability, information and conditioning theory in state estimation;
- degeneracy in other sensors where it affects LiDAR fusion (visual, thermal, radar);
- multi-sensor fusion architectures;
- datasets and benchmarks for degraded environments;
- the earlier SLAM and LiDAR surveys this review builds on.

The paper should take the reader through these questions in order:
1. **What it is:** the fundamentals of LiDAR-based localisation and the theory of degeneracy (observability, information, conditioning).
2. **From the beginning:** how the problem was first recognised (ICP stability and stable sampling, 2001 to 2003) and how it evolved through LOAM-era odometry, solver-level degeneracy analysis, localizability-aware registration, multi-sensor fusion and recent statistical and learning approaches, up to 2026.
3. **What has been identified:** causes, types and environments of degeneracy, and how each manifests in the estimator.
4. **What has been used:** detection methods, mitigation methods, fusion strategies, back-end treatments, datasets and evaluation practice.
5. **Research gaps:** what is missing, inconsistent or unproven in the literature.
6. **Possible solutions:** directions that are grounded in theory and in the existing literature for each gap. Present them as proposals and discussion, not as tested results.
7. **Future work:** a research roadmap.

**Sample format.** I uploaded a sample review only to show what a review paper looks like: Yarovoi and Cho, "Review of simultaneous localization and mapping (SLAM) for construction robotics applications," *Automation in Construction*, vol. 162, 105344, 2024, doi: 10.1016/j.autcon.2024.105344. It has background, limitations, algorithm families, conceptual figures and a narrative style. **Do not copy its structure exactly. Do not include anything like its "Experiments and results" section**, because my paper must be purely theoretical. My paper must be far deeper and more comprehensive. It should be the complete reference work on this one topic, with all available papers rather than the sample's roughly 76.

Working title (improve it if you can):
**"LiDAR Degeneracy in Simultaneous Localization and Mapping: Past, Present and Future: A Comprehensive Review of Theory, Detection, Mitigation, Multi-Sensor Fusion, Research Gaps and Future Directions"**

Target journals: check each one's current scope, Scopus indexing, acceptance of review articles, length limits and fees, then recommend one. The candidates are:
- IEEE Access
- IEEE Sensors Journal
- Sensors or Remote Sensing (MDPI)
- Robotics and Autonomous Systems
- Journal of Field Robotics
- Automation in Construction, if an infrastructure, tunnel or construction angle fits

Write in IEEE format first.

---

## 2. Rules you must follow (non-negotiable)

1. **No invented references.** Before you cite any paper, open a source that confirms it exists: the DOI or Crossref record, the arXiv abstract page, IEEE Xplore, the publisher page, CVF Open Access or the RSS proceedings. Record which source you opened.
2. **No invented claims or numbers.** Every statement about a paper must come from text you actually read. If you saw only the abstract, say only what the abstract says. If you quote numbers from a paper (for example, reported thresholds or reported accuracy), give them exactly as written, with the citation, and keep them few. This is a theoretical review, not a results table.
3. **No original experiments or unpublished results.** Do not include results from my thesis or from any unpublished work.
4. **Mark preprints.** Cite arXiv-only papers as arXiv preprints with their ID. Look for a published version first.
5. **IEEE reference style.** Use first author et al. when there are more than six authors. Give the full venue, volume, issue, pages, month, year and DOI where they exist. Number references in order of first citation.
6. **Paraphrase, do not copy.** Aim for under 15% similarity. Do not reuse any figure from another paper. Draw every figure yourself as original, conceptual vector art.
7. **Be balanced and critical.** For each family of methods, give its idea, its strengths, its limitations and its assumptions. Where the literature is weak (thresholds tuned on the authors' own data, few labelled benchmarks, methods tested on different sequences, results not reproduced), say so with citations.
8. **Mark proposals as proposals.** The "possible solutions" must be reasoned from the literature and theory. Mark each one as a proposed direction, and never claim it has been shown to work.
9. **Style.** No em dashes. Plain, precise academic English. Define every symbol and every acronym at first use.
10. **AI disclosure.** IEEE requires disclosure of AI-generated content. Draft an acknowledgment stating that AI tools assisted with literature search, drafting and editing, and that the authors verified all content.
11. **Keep a search log.** Record each database, query, date, hit count, and the number screened, excluded and included. Any PRISMA diagram must use these real counts.

---

## 3. Literature selection (a short method section in the paper)

A comprehensive review still needs a transparent selection method. Reviewers expect one. Keep it to about one page, following PRISMA 2020 in a light form.

- **Databases:** IEEE Xplore, Scopus, Web of Science (if reachable), Google Scholar, arXiv (cs.RO, cs.CV), ACM Digital Library, ScienceDirect, SpringerLink, Wiley, MDPI, and the RSS and CVF proceedings.
- **Snowballing:** check backward and forward citations from the seed papers in Section 6. Also use the GitHub list "Awesome-Algorithms-Against-Degeneracy" (github.com/thisparticle/Awesome-Algorithms-Against-Degeneracy) as a seed source.
- **Example queries** (adapt per database):
  - ("LiDAR" OR "laser scan") AND ("degeneracy" OR "degenerate" OR "localizability" OR "ill-conditioned" OR "observability") AND ("SLAM" OR "odometry" OR "registration" OR "ICP")
  - ("LiDAR-visual-inertial" OR "LiDAR-inertial-visual") AND ("degenerate" OR "failure detection" OR "switching")
  - ("geometrically degenerate" OR "feature-poor" OR "self-similar") AND ("tunnel" OR "corridor" OR "cave" OR "mine" OR "open field")
  - ("degeneracy" OR "localizability") AND ("dataset" OR "benchmark")
- **Time window:** from the origins of scan registration (Besl and McKay 1992; Chen and Medioni 1991/1992) to November 2026. Do not apply a lower date cut-off to degeneracy-specific papers. Older range-sensor and sonar work on localizability also counts.
- **Coverage completeness check:** coverage is the main requirement, so prove it before drafting.
  1. Run "cited by" forward searches (Google Scholar or Semantic Scholar) on the core papers: Gelfand 2003, Zhang et al. 2016, Hinduja 2019, X-ICP, Tuna et al. 2025, Switch-SLAM, DCReg, GEODE and SubT-MRS. Screen every citing paper.
  2. Compare the included set against the Awesome-Algorithms-Against-Degeneracy list and against the reference lists of the three most recent degeneracy papers you find. Report how many of their relevant entries you include, and why any are left out.
  3. Repeat the searches until a new round adds almost no relevant papers. State in the paper that the search reached this saturation point, and give the date.
- **Inclusion:** peer-reviewed papers, or arXiv preprints with clear technical content, that define, analyse, detect or mitigate degeneracy in LiDAR-based estimation; papers that fuse other sensors because of LiDAR degeneracy; datasets for degenerate scenes; and the foundational SLAM and LiDAR odometry papers needed for background.
- **Exclusion:** papers not about LiDAR or range sensing (unless they are essential background), non-English papers, patents, and papers whose existence cannot be confirmed.
- **For each included paper, record:** the problem addressed, the sensors, the core idea, the assumptions, the strengths, the limitations, the datasets used, and the year. Build the comparison tables from this record.

---

## 4. Required structure of the manuscript

Use the IEEEtran journal template, in this order. The section names are a guide; improve them if you can.

- **Title, authors, affiliations.** Authors: Kavinkumar S and Dr. G. Sivasankar. I will confirm the designation and emails.
- **Abstract** (200 to 250 words, no citations) and **Index Terms** (6 to 8).
- **I. Introduction:** why localisation fails in tunnels, corridors, mines, caves, open fields and planetary-like terrain; why LiDAR is preferred and where it breaks down; the scope; how this review differs from existing SLAM surveys (find and compare all of them, for example Cadena 2016 and Ebadi 2024, and any LiDAR or degeneracy surveys); a contributions list; and the paper organisation.
- **II. Review Methodology:** a short version of Section 3 above, with a PRISMA flow figure.
- **III. Fundamentals:**
  - LiDAR sensing and its error sources;
  - the SLAM and odometry pipeline;
  - scan registration (ICP variants; point-to-point, point-to-plane and point-to-line residuals);
  - optimisation (Gauss-Newton, Levenberg-Marquardt);
  - filtering (EKF and iterated EKF) versus factor graphs;
  - the information matrix H = JᵀJ, its rotation and translation blocks, Fisher information and the Cramér-Rao bound, and observability;
  - a formal definition of degeneracy and localizability.
- **IV. Evolution of the Field:** a narrative history from ICP stability and stable sampling, through LOAM and its derivatives, Zhang et al.'s degeneracy factor and solution remapping, localizability-aware registration, LiDAR-visual-inertial fusion and switching, to recent probabilistic, frame-invariant and learning-based approaches. Include a timeline figure.
- **V. What Causes Degeneracy: Identification and Taxonomy:**
  - Geometric causes: corridors and tunnels (one sliding direction), cylinders and pipes (rotation and translation), open planes and fields, self-similar or repetitive structures, and stairs.
  - Sensor causes: field of view, range limits, sparse beams, solid-state scan patterns, and reflective or absorbing surfaces.
  - Motion causes: aggressive rotation and motion distortion.
  - Algorithm-induced causes: feature selection, correspondence rejection, regularisation masking, and scale disparity between rotation and translation.
  - Types: translational, rotational, coupled; partial versus full; transient versus persistent.
  - The effects on the estimator: drift, divergence, map corruption and false loop closures.
- **VI. Degeneracy Detection.** Sub-taxonomy:
  - (A) Hessian eigenvalue and condition-number methods (Zhang et al. 2016; Hinduja et al. 2019; Switch-SLAM; DCReg's Schur-complement analysis);
  - (B) per-correspondence localizability (X-ICP, LP-ICP);
  - (C) pre-solve geometric indicators from scan or map normals (Gelfand covariance; SuperLoc; ICET; LF-GICP; normal-vector methods such as NV-LIOM);
  - (D) probabilistic and noise-aware detection (Hatleskog and Alexis);
  - (E) learning-based localizability (Nubert et al.);
  - (F) perturbation and re-optimisation methods (LiLi);
  - (G) frame and scale invariance of detectors (arXiv 2608.15532).
  - Also include a subsection on **how detection thresholds are set** and why their portability is a problem (eigenvalues depend on point count, weights, scene scale, noise and body frame).
- **VII. Degeneracy Mitigation:** this section must be a **complete catalogue** of every mitigation strategy that has been proposed or used, not only the ones named here. Organise it by where the mitigation acts, and give a table with the idea, the stage, the assumptions and the limitation of each. Cover at least:
  - (A) **Solver-level, on the update step:** solution remapping (Zhang et al. 2016); truncated SVD; Tikhonov and non-linear regularisation; damping of updates along likely-degenerate directions (Hatleskog and Alexis); equality and inequality constraints on degenerate directions (X-ICP, LP-ICP); preconditioned conjugate gradient with eigenvalue clamping in the preconditioner only (DCReg); degeneracy-aware factors with an adaptive eigenvalue cutoff (Hinduja et al. 2019); Schur-complement decoupling of rotation and translation.
  - (B) **Residual and weighting level:** point-to-line plus point-to-plane terms (LP-ICP); adaptive point-to-point and point-to-plane weighting (GenZ-ICP); Fisher-information-based correspondence weighting (LF-GICP); robust kernels and M-estimators (Cauchy, Huber, GNC as in RELEAD); covariance-regularised GICP and the way its isotropic floor can mask translational degeneracy (a limitation as much as a mitigation).
  - (C) **Data and sampling level:** geometrically stable and normal-space sampling (Gelfand et al. 2003; Rusinkiewicz and Levoy 2001); feature and point selection; ground segmentation and ground-plane constraints (LeGO-LOAM); point-cloud densification, voxel map design and keyframe or submap management.
  - (D) **Prior-based:** using an external odometry prior (IMU, wheel, leg or VIO) and "prior-only" fallback in the degenerate directions; the finding of Tuna et al. that active mitigation matters most when no reliable external prior exists.
  - (E) **Global methods:** global or correspondence-free registration (for example Quatro and FGR) and their failure in symmetric scenes, as reported in the literature.
  - (F) **Learning-based:** learned localizability and learned priors (Nubert et al.; ALIVE-LIO's learned velocity).
  - (G) **System, sensor and platform level:** multi-LiDAR and extended field-of-view setups; active perception and planning that avoid or anticipate degenerate places (for example attention and anticipation in visual-inertial navigation, active SLAM); structural priors such as Manhattan-world or plane constraints; and the sensor-fusion mitigations in Section VIII.
  - Include the field comparison of the solver-level strategies by Tuna et al. (T-FR 2025). For every item, say whether it **detects** and mitigates, or only mitigates, and whether it needs a threshold. If you find a mitigation that fits none of these groups, add a group.
- **VIII. Multi-Sensor Fusion as Mitigation:**
  - (A) IMU-aided LiDAR odometry and why the IMU alone is not enough;
  - (B) switching and failure detection (Switch-SLAM, LVI-SAM, VINS-Mono failure handling, Super Odometry, CompSLAM);
  - (C) tightly coupled LiDAR-visual-inertial systems (LIC-Fusion, VIL-SLAM, R2LIVE, R3LIVE, FAST-LIVO and FAST-LIVO2);
  - (D) direction-wise or selective fusion (Selective KF "Fuse only what matters", SA-LIVO, Liao et al., ALIVE-LIO, MM-LINS, D²-LIO, RELEAD);
  - (E) other modalities: radar, thermal, UWB, wheel and leg odometry (search for these);
  - (F) the problem of visual degeneracy occurring at the same time (darkness, texture-less walls, smoke).
- **IX. Back-End and Loop Closure in Degenerate Environments:** degeneracy-aware factors, DARE-SLAM, false loop closures in self-similar places, and pose-graph consequences.
- **X. Datasets and Evaluation Practice:** a table of degeneracy-relevant datasets (platform, sensors, environment, degeneracy type, ground-truth source); the metrics in use (ATE, RPE, detection accuracy); the shortage of per-frame degeneracy labels; artificial induction of degeneracy (range limits, field-of-view cuts); and reproducibility issues.
- **XI. Critical Discussion:** a side-by-side comparison of the method families (assumptions, cost, need for tuning, need for extra sensors, real-time suitability, maturity). State what the field agrees on and where it disagrees. Use a qualitative comparison table, not a new benchmark.
- **XII. Research Gaps:** give each gap its own numbered paragraph, with citations showing why it is a gap. Examples to check and expand:
  - thresholds without a statistical basis;
  - few labelled benchmarks for detection;
  - frame and scale dependence of detectors;
  - detectors not scored against labels;
  - weak cross-paper comparability and reproducibility;
  - joint LiDAR and visual degeneracy;
  - solid-state and low-cost LiDARs;
  - generalisation of learning-based detectors;
  - embedded compute limits;
  - degeneracy-aware loop closure and relocalisation;
  - standard reporting (repeated runs, held-out data).
- **XIII. Possible Solutions:** for every gap, one or more proposed directions grounded in theory or in adjacent literature. Examples: statistically calibrated tests on the smallest eigenvalue; noise-aware or precision-based thresholds (analogous to GNSS dilution of precision); frame-equivariant metrics; geometry-based ground-truth labels from analytic or surveyed scenes; direction-wise information fusion; uncertainty-aware learning; and benchmark and reporting protocols. Label each as proposed.
- **XIV. Future Directions and Roadmap:** short-term, medium-term and long-term items, with a roadmap figure.
- **XV. Conclusion.**
- **Acknowledgment** (with the AI disclosure), **References**, and **author biographies** with photo placeholders if the journal asks for them.

Length: whatever full coverage needs, probably 15,000 to 22,000 words including tables. Check the chosen journal's limit and tell me if it is too short. A long review may need a journal that allows long surveys, such as IEEE Access, or a split into two parts.

---

## 5. Required tables and figures (all original and conceptual)

**Tables:**
1. Comparison with existing surveys (scope, year, number of references, and whether each covers theory, detection, mitigation, fusion, datasets and gaps).
2. Literature-selection counts per database.
3. Causes and types of degeneracy, with example environments and the affected degrees of freedom.
4. Detection methods: statistic, matrix used (full H, blocks, Schur complement, normals), pre-solve or post-solve, how the threshold is set, frame-invariant or not, and whether code is released.
5. Mitigation methods (the complete catalogue from Section VII, one row per method): group, idea, where it acts, whether it needs a detector and a threshold, assumptions, and limitation. Add a check column marking which methods were compared head-to-head in any published study.
6. Fusion strategies: sensors, coupling type, decision variable, strengths and weaknesses.
7. Datasets for degenerate environments.
8. Qualitative comparison of the method families.
9. Research gaps mapped to possible solutions and to the papers that partly address them.

**Figures** (drawn by you as TikZ or SVG, then exported to PDF):
1. The LiDAR SLAM pipeline, showing where degeneracy enters.
2. Degenerate geometries: corridor, tunnel or cylinder, open plane and stairs, with the unconstrained directions marked.
3. A sketch of the information-matrix eigenvalue spectrum in normal versus degenerate scenes.
4. A taxonomy tree of the whole field.
5. A timeline from 2001 to 2026.
6. Where detection sits: pre-solve, in-solve and post-solve.
7. Fusion architectures: switching, tightly coupled and direction-wise.
8. The PRISMA flow, with the real counts.
9. The future-work roadmap.

---

## 6. Seed reference list (start here, then extend to all available papers)

### 6.1 Already verified (IEEE strings checked against Crossref or arXiv on 9 Oct 2026; re-check DOIs)

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

### 6.2 Found in the project but not fully verified (verify each one)

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

### 6.3 Gaps to fill by searching

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

## 7. How to work (phases and checkpoints)

Work in phases and save each phase's output as a file, so nothing is lost if the chat runs long. After each phase, send me a two-line status. Stop and ask me only when a decision is mine.

1. **Search and screening.** Run the queries and keep the log. Check that no existing survey already covers this exact scope. If one does, tell me at once and propose how to differentiate. Output: `search_log.csv` and `selection_counts.md`.
2. **Reference database.** One row per included paper: IEEE string, DOI or arXiv ID, the source you opened to verify it, the category, and the fields listed in Section 3. Output: `references.xlsx` and `refs.bib`. Include every relevant paper the search finds, with no row target, and report the final count.
3. **Outline.** The section and subsection plan, with the references assigned to each section. Show it to me before drafting.
4. **Drafting.** Write section by section in LaTeX (IEEEtran journal). Every factual sentence about a paper carries its citation. Keep a consistent notation table.
5. **Tables and figures.** Build the tables from the reference database. Draw the figures yourself.
6. **Compile and check.** Build the PDF. Check that every \cite resolves, that no bib entry is unused, and that the reference count and word count fit. Check that figures are readable at print size.
7. **Independent verification.** Use a separate agent or pass that has not seen the drafting. It re-opens a random 25% of the references, plus every paper whose numbers are quoted, and confirms each claim. Fix every mismatch.
8. **Submission package:** the manuscript PDF; the LaTeX source with the .bib and figures; a cover letter; 3 to 5 suggested reviewers (verify that they are real, active in the field and free of conflicts of interest); the AI-use disclosure; and highlights, if the journal requires them.

---

## 8. Deliverables I expect at the end

- `review_main.tex`, `refs.bib`, the `figures/` folder, and the compiled `review_main.pdf` (IEEEtran journal).
- `references.xlsx`: the verification table (paper, DOI or arXiv ID, the source used to verify it, category, and the extracted fields).
- `search_log.csv` and the source of the PRISMA figure.
- `cover_letter.docx` or `.tex`.
- A short list of what I must check or decide: author emails, the advisor's designation, and the journal choice.

Start with Phase 1. In your first reply, tell me in one line which journal you recommend after checking, and why.
