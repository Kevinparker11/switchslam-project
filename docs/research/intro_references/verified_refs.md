# Verified IEEE References: Introduction (LiDAR Degeneracy Detection Paper)

Verification date: 2026-10-09.
Method: each field below was checked against a source that was actually opened in this session: the Crossref metadata API (publisher-deposited records), arXiv abstract or HTML pages, CVF Open Access, RSS Proceedings, CMU RI publication pages, Stanford Graphics, GitHub, a university library catalogue, and the two project PDFs (SwitchSLAM.pdf and 2509.06285v3.pdf).
Anything that could not be confirmed is marked **unverified** and left out of the IEEE string. No field was filled in from memory.

Status legend:
- **VERIFIED**: the paper exists, and every field in the IEEE string was confirmed.
- **PARTIAL**: the paper exists, but at least one field could not be confirmed. The note says which.
- **DROP**: the paper's existence could not be confirmed.

IEEE author rule: when a paper has more than six authors, the IEEE string uses "et al." (IEEE Reference Guide). The full verified author list is still given in the "Authors" field.

---

## Summary table

| # | Short name | Status | Note |
|---|---|---|---|
| 1 | Cadena et al., T-RO 2016 | VERIFIED | |
| 2 | Ebadi et al., DARPA SubT, T-RO | VERIFIED | Vol. 40 is the 2024 volume. Month and issue are unverified, so they are omitted. |
| 3 | LOAM, RSS 2014 | VERIFIED | The RSS proceedings give no page numbers. Cite by DOI. |
| 4 | LeGO-LOAM, IROS 2018 | VERIFIED | |
| 5 | LIO-SAM, IROS 2020 | VERIFIED | |
| 6 | FAST-LIO2, T-RO 2022 | VERIFIED | |
| 7 | Zhang, Kaess, Singh, ICRA 2016 | VERIFIED | |
| 8 | Gelfand et al., 3DIM 2003 | VERIFIED | |
| 9 | Hinduja et al., IROS 2019 | VERIFIED | The correct DOI ends in **8968577**. |
| 10 | X-ICP, T-RO | VERIFIED | Vol. 40, 2024 (arXiv 2022). |
| 11 | Nubert et al., localizability | VERIFIED | Venue is **IROS 2022**, not ICRA. |
| 12 | Tuna et al., "Informed, Constrained, Aligned" | VERIFIED | IEEE Trans. Field Robot., vol. 2, 2025. |
| 13 | DCReg | VERIFIED | Published in IJRR as OnlineFirst on 31 Aug 2026. Volume, issue and pages are not yet assigned. |
| 14 | NV-LIO (arXiv 2405.12563) | PARTIAL | Published as **NV-LIOM** in RA-L 9(11), 2024. The match is inferred from identical authors and a near-identical title, because the arXiv page has no journal-ref. |
| 15 | LF-GICP (arXiv 2608.19522) | VERIFIED | arXiv preprint only. No venue found. |
| 16 | Hatleskog & Alexis | VERIFIED | Venue is RA-L, vol. 9, no. 12, Dec. 2024. |
| 17 | RELEAD | VERIFIED | ICRA 2024. |
| 18 | VINS-Mono | VERIFIED | |
| 19 | Switch-SLAM | VERIFIED | |
| 20 | SubT-MRS, CVPR 2024 | PARTIAL | The DOI is unverified because Crossref rate-limited the lookup. All other fields are verified. |
| 21 | GEODE | VERIFIED | Published title: "Heterogeneous LiDAR dataset for benchmarking robust localization in diverse degenerate scenarios". IJRR 45(1), 2026. |
| 22 | FusionPortable | VERIFIED | |
| 23 | LVI-SAM | VERIFIED | |
| 24 | Bingham 1974 | VERIFIED* | Crossref has no page data. The pages 1201–1225 come from a secondary source (Wikipedia). |
| 25 | Mardia & Jupp, *Directional Statistics* | VERIFIED* | A library catalogue gives 2000. Crossref's print-date field says 1999-01-03, which is an odd date. 2000 is used. |
| 26 | LP-ICP (arXiv 2501.02580) | PARTIAL | Existence, title and authors are verified. No published venue was found, so cite it as an arXiv preprint. |
| 27 | A-LOAM GitHub | VERIFIED | The repository exists. The maintainers listed in the README are Tong Qin and Shaozu Cao. |

No item is marked DROP.

---

## 1. Cadena et al. (2016): **VERIFIED**

**IEEE:**
C. Cadena *et al.*, "Past, present, and future of simultaneous localization and mapping: Toward the robust-perception age," *IEEE Trans. Robot.*, vol. 32, no. 6, pp. 1309–1332, Dec. 2016, doi: 10.1109/TRO.2016.2624754.

- Authors (8): Cesar Cadena, Luca Carlone, Henry Carrillo, Yasir Latif, Davide Scaramuzza, José Neira, Ian Reid, John J. Leonard.
- Summary: A survey and tutorial of SLAM that sets out the standard formulation and reviews open problems: long-term robustness, scalability, metric and semantic map representations, theoretical guarantees, and active SLAM.
- Sources: https://api.crossref.org/works/10.1109/TRO.2016.2624754 ; https://arxiv.org/abs/1606.05830

## 2. Ebadi et al. (DARPA SubT): **VERIFIED**

**IEEE:**
K. Ebadi *et al.*, "Present and future of SLAM in extreme environments: The DARPA SubT challenge," *IEEE Trans. Robot.*, vol. 40, pp. 936–959, 2024, doi: 10.1109/TRO.2023.3323938.

- Authors (31): Kamak Ebadi, Lukas Bernreiter, Harel Biggie, Gavin Catt, Yun Chang, Arghya Chatterjee, Christopher E. Denniston, Simon-Pierre Deschênes, Kyle Harlow, Shehryar Khattak, Lucas Nogueira, Matteo Palieri, Pavel Petráček, Matěj Petrlík, Andrzej Reinke, Vít Krátký, Shibo Zhao, Ali-akbar Agha-mohammadi, Kostas Alexis, Christoffer Heckman, Kasra Khosoussi, Navinda Kottege, Benjamin Morrell, Marco Hutter, Fred Pauling, François Pomerleau, Martin Saska, Sebastian Scherer, Roland Siegwart, Jason L. Williams, Luca Carlone.
- Notes:
  - Crossref gives the year as 2024. The DOI suffix contains "2023" because the paper appeared online in 2023. Use 2024.
  - Month and issue are not in the Crossref record, so they are omitted.
  - The arXiv preprint (2208.01787) has a different title: "Present and Future of SLAM in Extreme Underground Environments".
- Summary: Reviews the localization and mapping systems that six teams built for the multi-year DARPA SubT Challenge, with a focus on lidar-centric and multi-robot SLAM, and assesses how mature the field is, which problems remain open, and which open-source tools and datasets are available.
- Sources: https://api.crossref.org/works?query.bibliographic=Present+and+future+of+SLAM+in+extreme+environments+DARPA+SubT+challenge ; https://arxiv.org/abs/2208.01787

## 3. LOAM (RSS 2014): **VERIFIED**

**IEEE:**
J. Zhang and S. Singh, "LOAM: Lidar odometry and mapping in real-time," in *Proc. Robot.: Sci. Syst.* (RSS), Berkeley, CA, USA, Jul. 2014, doi: 10.15607/RSS.2014.X.007.

- Authors: Ji Zhang, Sanjiv Singh.
- Notes: The proceedings are titled *Robotics: Science and Systems X*. The paper is p07, and the RSS page lists no page numbers.
- Summary: Real-time lidar odometry and mapping that splits the problem into a high-frequency, low-fidelity odometry step and a low-frequency, fine scan-to-map registration step.
- Sources: https://api.crossref.org/works/10.15607/RSS.2014.X.007 ; https://www.roboticsproceedings.org/rss10/p07.html

## 4. LeGO-LOAM (IROS 2018): **VERIFIED**

**IEEE:**
T. Shan and B. Englot, "LeGO-LOAM: Lightweight and ground-optimized lidar odometry and mapping on variable terrain," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst.* (IROS), Madrid, Spain, Oct. 2018, pp. 4758–4765, doi: 10.1109/IROS.2018.8594299.

- Authors: Tixiao Shan, Brendan Englot.
- Summary: A lightweight lidar odometry and mapping system for ground vehicles that uses ground segmentation and ground-plane constraints to estimate 6-DoF pose in real time on embedded hardware over varied terrain. This summary is based on the project README, because the IEEE Xplore abstract page did not load.
- Sources: https://api.crossref.org/works/10.1109/IROS.2018.8594299 ; https://github.com/RobustFieldAutonomyLab/LeGO-LOAM

## 5. LIO-SAM (IROS 2020): **VERIFIED**

**IEEE:**
T. Shan, B. Englot, D. Meyers, W. Wang, C. Ratti, and D. Rus, "LIO-SAM: Tightly-coupled lidar inertial odometry via smoothing and mapping," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst.* (IROS), Las Vegas, NV, USA, 2020, pp. 5135–5142, doi: 10.1109/IROS45743.2020.9341176.

- Notes: IROS 2020 was held virtually. Crossref lists the event dates as 24 Oct 2020 to 24 Jan 2021.
- Summary: A factor-graph lidar-inertial odometry system. IMU preintegration de-skews the point clouds and gives an initial guess for scan matching, and the system stays real-time by matching against local keyframe submaps instead of a global map.
- Sources: https://api.crossref.org/works/10.1109/IROS45743.2020.9341176 ; https://arxiv.org/abs/2007.00258

## 6. FAST-LIO2 (T-RO 2022): **VERIFIED**

**IEEE:**
W. Xu, Y. Cai, D. He, J. Lin, and F. Zhang, "FAST-LIO2: Fast direct LiDAR-inertial odometry," *IEEE Trans. Robot.*, vol. 38, no. 4, pp. 2053–2073, Aug. 2022, doi: 10.1109/TRO.2022.3141876.

- Summary: A tightly coupled iterated-Kalman-filter LiDAR-inertial odometry that registers raw points directly to the map without feature extraction, and stores the map in an incremental k-d tree (ikd-Tree) that supports efficient insertion, deletion and rebalancing.
- Sources: https://api.crossref.org/works/10.1109/TRO.2022.3141876 ; https://arxiv.org/abs/2107.06829

## 7. Zhang, Kaess, Singh (ICRA 2016): **VERIFIED**

**IEEE:**
J. Zhang, M. Kaess, and S. Singh, "On degeneracy of optimization-based state estimation problems," in *Proc. IEEE Int. Conf. Robot. Autom.* (ICRA), Stockholm, Sweden, May 2016, pp. 809–816, doi: 10.1109/ICRA.2016.7487211.

- Summary: An online method that analyses the geometry of the constraints in an optimization-based estimator, separates the degenerate directions from the well-conditioned ones, and updates the solution only in the well-conditioned directions ("solution remapping"). It is validated on camera and lidar ego-motion estimation.
- Sources: https://api.crossref.org/works/10.1109/ICRA.2016.7487211 ; https://publications.ri.cmu.edu/on-degeneracy-of-optimization-based-state-estimation-problems

## 8. Gelfand et al. (3DIM 2003): **VERIFIED**

**IEEE:**
N. Gelfand, L. Ikemoto, S. Rusinkiewicz, and M. Levoy, "Geometrically stable sampling for the ICP algorithm," in *Proc. 4th Int. Conf. 3-D Digit. Imag. Model.* (3DIM), Banff, AB, Canada, Oct. 2003, pp. 260–267, doi: 10.1109/IM.2003.1240258.

- Notes:
  - Crossref's issued-date field is empty. The October 2003 date (6–10 Oct 2003) comes from the authors' Stanford project page.
  - The Crossref container title is "Fourth International Conference on 3-D Digital Imaging and Modeling, 2003. 3DIM 2003. Proceedings."
- Summary: Shows that the accuracy of ICP depends on which points are sampled, and proposes a sampling strategy that detects pose uncertainty and picks the points that best constrain the otherwise unstable transformation directions.
- Sources: https://api.crossref.org/works/10.1109/IM.2003.1240258 ; https://graphics.stanford.edu/papers/stabicp/

## 9. Hinduja et al. (IROS 2019): **VERIFIED**

**IEEE:**
A. Hinduja, B.-J. Ho, and M. Kaess, "Degeneracy-aware factors with applications to underwater SLAM," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst.* (IROS), Macau, China, Nov. 2019, pp. 1293–1299, doi: 10.1109/IROS40897.2019.8968577.

- Notes: Check any existing BibTeX for this entry. A guessed DOI ending in 8968249 is **wrong**. The DOI confirmed by Crossref is 10.1109/IROS40897.2019.8968577.
- Summary: Restricts both scan matching and pose-graph optimization to the directions that are sufficiently observable, using an adaptive cutoff recomputed at every iteration. This keeps sonar-based underwater SLAM accurate in geometrically sparse scenes and lets it reject unreliable loop closures.
- Sources: https://api.crossref.org/works?query.bibliographic=Degeneracy-aware+factors+with+applications+to+underwater+SLAM+Hinduja ; https://publications.ri.cmu.edu/degeneracy-aware-factors-with-applications-to-underwater-slam

## 10. X-ICP (T-RO 2024): **VERIFIED**

**IEEE:**
T. Tuna, J. Nubert, Y. Nava, S. Khattak, and M. Hutter, "X-ICP: Localizability-aware LiDAR registration for robust localization in extreme environments," *IEEE Trans. Robot.*, vol. 40, pp. 452–471, 2024, doi: 10.1109/TRO.2023.3335691.

- Notes: The preprint is arXiv:2211.16335, submitted 29 Nov 2022 (v4: 18 Feb 2024). Month is not in Crossref, so it is omitted.
- Summary: A localizability-aware point-to-plane ICP. It analyses how strongly each correspondence constrains each motion direction, detects which directions are degenerate, and adds optimization constraints that prevent drift along those directions.
- Sources: https://api.crossref.org/works?query.bibliographic=X-ICP+Localizability-Aware+LiDAR+Registration+Tuna ; https://arxiv.org/abs/2211.16335

## 11. Nubert et al. (IROS 2022): **VERIFIED** (the venue is IROS, not ICRA)

**IEEE:**
J. Nubert, E. Walther, S. Khattak, and M. Hutter, "Learning-based localizability estimation for robust LiDAR localization," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst.* (IROS), Kyoto, Japan, Oct. 2022, pp. 17–24, doi: 10.1109/IROS47612.2022.9982257.

- Notes: The preprint is arXiv:2203.05698.
- Summary: A neural network, trained only in simulation, that predicts directly from raw LiDAR scans whether scan-to-scan registration will be localizable. This allows failures to be detected early without solving the registration and without tuning heuristic thresholds.
- Sources: https://api.crossref.org/works?query.bibliographic=Learning-based+localizability+estimation+for+robust+LiDAR+localization+Nubert ; https://arxiv.org/abs/2203.05698

## 12. Tuna et al., "Informed, Constrained, Aligned": **VERIFIED**

**IEEE:**
T. Tuna, J. Nubert, P. Pfreundschuh, C. Cadena, S. Khattak, and M. Hutter, "Informed, constrained, aligned: A field analysis on degeneracy-aware point cloud registration in the wild," *IEEE Trans. Field Robot.*, vol. 2, pp. 485–515, 2025, doi: 10.1109/TFR.2025.3576053.

- Notes: The preprint is arXiv:2408.11809. The venue is confirmed as IEEE Transactions on Field Robotics.
- Summary: A field study that implements and compares degeneracy-aware ICP strategies (soft and hard constraints, regularization, truncated SVD, and others) in geometrically degenerate real-world settings. It finds that active degeneracy mitigation matters most when no reliable external odometry prior is available.
- Sources: https://api.crossref.org/works?query.bibliographic=Informed+constrained+aligned+field+analysis+degeneracy-aware+point+cloud+registration+in+the+wild ; https://arxiv.org/abs/2408.11809

## 13. DCReg (IJRR, OnlineFirst 2026): **VERIFIED**

**IEEE:**
X. Hu, X. Chen, M. Jia, J. Wu, P. Tan, and S. L. Waslander, "DCReg: Decoupled characterization for efficient degenerate LiDAR registration," *Int. J. Robot. Res.*, early access, Aug. 2026, doi: 10.1177/02783649261465040.

- Authors: Xiangcheng Hu, Xieyuanli Chen, Mingkai Jia, Jin Wu, Ping Tan, Steven L. Waslander. Confirmed against both arXiv and the project PDF.
- Notes:
  - Crossref records this as an IJRR article published 31 Aug 2026, with article number 02783649261465040. Volume, issue and pages are **not yet assigned**, so they are omitted.
  - The project PDF (arXiv v3, 10 Sep 2026) uses the SAGE/IJRR template with "DOI: 10.1177/ToBeAssigned".
  - If you prefer to cite the preprint: arXiv:2509.06285, 2025.
- Summary: Uses Schur-complement decoupling of the registration Hessian into rotation and translation subspaces to detect ill-conditioning. It then resolves eigenvector ambiguity so that the weak directions map to physical motion axes, and stabilizes the solve with a preconditioned conjugate gradient whose eigenvalues are clamped only in the preconditioner, which leaves the original least-squares problem unchanged.
- Sources: https://api.crossref.org/works?query.title=DCReg+Decoupled+Characterization+Efficient+Degenerate+LiDAR+Registration ; https://arxiv.org/abs/2509.06285 ; project file `2509.06285v3.pdf`

## 14. NV-LIO / NV-LIOM: **PARTIAL**

**IEEE (published version, recommended):**
D. Chung and J. Kim, "NV-LIOM: LiDAR-inertial odometry and mapping using normal vectors towards robust SLAM in multifloor environments," *IEEE Robot. Autom. Lett.*, vol. 9, no. 11, pp. 9375–9382, Nov. 2024, doi: 10.1109/LRA.2024.3457373.

**IEEE (preprint, if you specifically mean the arXiv version):**
D. Chung and J. Kim, "NV-LIO: LiDAR-inertial odometry using normal vectors towards robust SLAM in multifloor environments," 2024, *arXiv:2405.12563*.

- Authors: Dongha Chung, Jinwhan Kim (KAIST).
- Why PARTIAL:
  - The arXiv page has no journal-ref; it only says "submitted to the IEEE for possible publication".
  - The RA-L paper is renamed **NV-LIOM**. It has the same two authors and nearly the same title, so it is very likely the published version, but no source states the link explicitly.
  - The arXiv submission date could not be read because the abs page redirected to the HTML version. Only the year 2024 is confirmed, from the ID.
- Summary: A tightly coupled LiDAR-inertial odometry for indoor multifloor buildings. It uses normal vectors extracted from range images for registration and for degeneracy detection (adjusting the matching uncertainty), and adds viewpoint-based loop closure.
- Sources: https://api.crossref.org/works?query.title=NV-LIO+LiDAR-Inertial+Odometry+using+Normal+Vectors+Multifloor ; https://arxiv.org/html/2405.12563v2

## 15. LF-GICP (arXiv 2026): **VERIFIED** (preprint)

**IEEE:**
E. Im, "LF-GICP: Parameter-free degeneracy-aware LiDAR odometry via a voxel-normal localizability field," Aug. 2026, *arXiv:2608.19522*.

- Author: Eunsoo Im (single author). Submitted 20 Aug 2026. arXiv DOI: 10.48550/arXiv.2608.19522. No journal-ref or comments field.
- Summary: Proposes a parameter-free way to detect and handle geometric degeneracy in scan-to-map LiDAR odometry. Statistics from a regularization-free voxel-normal localizability field trigger Fisher-information-based correspondence weighting.
- Source: https://arxiv.org/abs/2608.19522

## 16. Hatleskog & Alexis (RA-L 2024): **VERIFIED**

**IEEE:**
J. Hatleskog and K. Alexis, "Probabilistic degeneracy detection for point-to-plane error minimization," *IEEE Robot. Autom. Lett.*, vol. 9, no. 12, pp. 11234–11241, Dec. 2024, doi: 10.1109/LRA.2024.3484153.

- Notes: The preprint is arXiv:2410.10784 (v1 14 Oct 2024, v2 3 Feb 2025). The DCReg reference list gives the same volume, issue and pages.
- Summary: Models the noise in the inputs to point-to-plane minimization to estimate the probability that each direction is degenerate, and uses that estimate in a real-time registration scheme that damps updates along likely-degenerate directions.
- Sources: https://api.crossref.org/works?query.title=Probabilistic+Degeneracy+Detection+for+Point-to-Plane+Error+Minimization ; https://arxiv.org/abs/2410.10784

## 17. RELEAD (ICRA 2024): **VERIFIED**

**IEEE:**
Z. Chen *et al.*, "RELEAD: Resilient localization with enhanced LiDAR odometry in adverse environments," in *Proc. IEEE Int. Conf. Robot. Autom.* (ICRA), Yokohama, Japan, May 2024, pp. 3999–4005, doi: 10.1109/ICRA57147.2024.10611074.

- Authors (8): Zhiqiang Chen, Hongbo Chen, Yuhua Qi, Shipeng Zhong, Dapeng Feng, Jin Wu, Weisong Wen, Ming Liu.
- Notes: The arXiv listing (2402.18934) prints one author as "Wu Jin". Crossref and IEEE give "Jin Wu", so use J. Wu.
- Summary: A LiDAR-centric localization system that keeps point-cloud registration working in degenerate scenes through constrained error-state Kalman filter updates, and fuses multiple sensors robustly through GNC-based graph optimization with an efficient smoother.
- Sources: https://api.crossref.org/works?query.title=RELEAD+Resilient+Localization+Enhanced+LiDAR+Odometry+Adverse+Environments ; https://arxiv.org/abs/2402.18934

## 18. VINS-Mono (T-RO 2018): **VERIFIED**

**IEEE:**
T. Qin, P. Li, and S. Shen, "VINS-Mono: A robust and versatile monocular visual-inertial state estimator," *IEEE Trans. Robot.*, vol. 34, no. 4, pp. 1004–1020, Aug. 2018, doi: 10.1109/TRO.2018.2853729.

- Summary: A monocular visual-inertial estimator with robust initialization and failure recovery, tightly coupled sliding-window nonlinear optimization, loop detection, and 4-DoF pose-graph optimization for global consistency.
- Sources: https://api.crossref.org/works/10.1109/TRO.2018.2853729 ; https://arxiv.org/abs/1708.03852

## 19. Switch-SLAM (RA-L 2024): **VERIFIED**

**IEEE:**
J. Lee *et al.*, "Switch-SLAM: Switching-based LiDAR-inertial-visual SLAM for degenerate environments," *IEEE Robot. Autom. Lett.*, vol. 9, no. 8, pp. 7270–7277, Aug. 2024, doi: 10.1109/LRA.2024.3421792.

- Authors (7): Junwoon Lee, Ren Komatsu, Mitsuru Shinozaki, Toshihiro Kitajima, Hajime Asama, Qi An, Atsushi Yamashita. Confirmed against both Crossref and the project PDF header.
- Full-author IEEE form, if preferred: J. Lee, R. Komatsu, M. Shinozaki, T. Kitajima, H. Asama, Q. An, and A. Yamashita, ...
- Summary: A LiDAR-inertial-visual SLAM that switches from LiDAR odometry to visual odometry when a non-heuristic, tuning-free detector flags LiDAR degeneracy. The switch stops failed estimates from propagating through the fused system.
- Sources: https://api.crossref.org/works/10.1109/LRA.2024.3421792 ; project file `SwitchSLAM.pdf` (page 7270 header and abstract)

## 20. SubT-MRS (CVPR 2024): **PARTIAL** (DOI unverified)

**IEEE:**
S. Zhao *et al.*, "SubT-MRS dataset: Pushing SLAM towards all-weather environments," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit.* (CVPR), Seattle, WA, USA, Jun. 2024, pp. 22647–22657.

- Authors (21): Shibo Zhao, Yuanjun Gao, Tianhao Wu, Damanpreet Singh, Rushan Jiang, Haoxiang Sun, Mansi Sarawata, Yuheng Qiu, Warren Whittaker, Ian Higgins, Yi Du, Shaoshu Su, Can Xu, John Keller, Jay Karhade, Lucas Nogueira, Sourojit Saha, Ji Zhang, Wenshan Wang, Chen Wang, Sebastian Scherer.
- Notes:
  - Title, authors, pages and year come from the CVF Open Access page.
  - The IEEE DOI is **unverified** because the Crossref lookup was rate-limited, so it is omitted. Add it only after checking IEEE Xplore.
  - The Seattle, June 2024 venue details come from the CVPR 2024 event record in Crossref.
- Summary: A multi-robot, multi-modal real-world SLAM dataset recorded in degraded conditions (smoke, dust, darkness, featureless corridors and the like), released with new accuracy and robustness benchmark tracks and metrics.
- Source: https://openaccess.thecvf.com/content/CVPR2024/html/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.html

## 21. GEODE dataset (IJRR): **VERIFIED**

**IEEE:**
Z. Chen *et al.*, "Heterogeneous LiDAR dataset for benchmarking robust localization in diverse degenerate scenarios," *Int. J. Robot. Res.*, vol. 45, no. 1, pp. 6–22, Jan. 2026, doi: 10.1177/02783649251344967.

- Authors (9): Zhiqiang Chen, Yuhua Qi, Dapeng Feng, Xuebin Zhuang, Hongbo Chen, Xiangcheng Hu, Jin Wu, Kelin Peng, Peng Lu. The user's guessed list was correct.
- Notes:
  - The paper title does **not** contain "GEODE". GEODE is the name of the dataset.
  - Published online 9 Jun 2025, in print Jan 2026. The preprint is arXiv:2409.04961 (2024).
  - If you cite the online-first version instead, use 2025.
- Summary: Presents GEODE, a multi-LiDAR dataset of 64 trajectories (more than 64 km) across seven kinds of real-world environment with varying geometric degeneracy, built to benchmark degeneracy-robust LiDAR localization and SLAM.
- Sources: https://api.crossref.org/works/10.1177/02783649251344967 ; https://arxiv.org/abs/2409.04961

## 22. FusionPortable (IROS 2022): **VERIFIED**

**IEEE:**
J. Jiao *et al.*, "FusionPortable: A multi-sensor campus-scene dataset for evaluation of localization and mapping accuracy on diverse platforms," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst.* (IROS), Kyoto, Japan, Oct. 2022, pp. 3851–3856, doi: 10.1109/IROS47612.2022.9982119.

- Authors (13): Jianhao Jiao, Hexiang Wei, Tianshuai Hu, Xiangcheng Hu, Yilong Zhu, Zhijian He, Jin Wu, Jingwen Yu, Xupeng Xie, Huaiyang Huang, Ruoyu Geng, Lujia Wang, Ming Liu.
- Summary: Presents a portable multi-sensor suite and a campus dataset of 17 sequences recorded on several platforms (handheld, legged robot, UGV, vehicle), with ground truth for evaluating localization and mapping separately, and benchmarks existing SLAM methods on it.
- Sources: https://api.crossref.org/works?query.bibliographic=FusionPortable+multi-sensor+campus-scene+dataset+Jiao ; https://arxiv.org/abs/2208.11865

## 23. LVI-SAM (ICRA 2021): **VERIFIED**

**IEEE:**
T. Shan, B. Englot, C. Ratti, and D. Rus, "LVI-SAM: Tightly-coupled lidar-visual-inertial odometry via smoothing and mapping," in *Proc. IEEE Int. Conf. Robot. Autom.* (ICRA), Xi'an, China, May 2021, pp. 5692–5698, doi: 10.1109/ICRA48506.2021.9561996.

- Summary: A factor-graph lidar-visual-inertial system made of a visual-inertial subsystem and a lidar-inertial subsystem that help each other, and that keeps running when either one fails.
- Sources: https://api.crossref.org/works?query.title=LVI-SAM+Tightly-coupled+Lidar-Visual-Inertial+Odometry&query.author=Shan ; https://arxiv.org/abs/2104.10831

## 24. Bingham (1974): **VERIFIED\*** (pages from a secondary source)

**IEEE:**
C. Bingham, "An antipodally symmetric distribution on the sphere," *Ann. Statist.*, vol. 2, no. 6, pp. 1201–1225, Nov. 1974, doi: 10.1214/aos/1176342874.

- Notes:
  - Title, author, journal, volume, issue, date and DOI come from Crossref.
  - Crossref has no page data. Pages 1201–1225 come from the References section of the Wikipedia "Bingham distribution" article.
  - Project Euclid and JSTOR blocked automated access, so the pages could not be checked against the publisher.
- Summary: Introduces the Bingham distribution, an antipodally symmetric exponential-family distribution on the sphere whose density is proportional to exp(xᵀAx), for modelling axial data, together with its estimation and inference. This summary comes from secondary descriptions, because the abstract page was blocked.
- Sources: https://api.crossref.org/works/10.1214/aos/1176342874 ; https://en.wikipedia.org/wiki/Bingham_distribution

## 25. Mardia & Jupp, *Directional Statistics*: **VERIFIED\***

**IEEE:**
K. V. Mardia and P. E. Jupp, *Directional Statistics* (Wiley Series in Probability and Statistics). Chichester, U.K.: Wiley, 2000, doi: 10.1002/9780470316979.

- Authors: Kanti V. Mardia, Peter E. Jupp.
- Notes:
  - ISBN 0-471-95333-4 (print) and 9780470316979 (electronic). xxi + 429 pp.
  - The Masaryk University library catalogue gives "Chichester: John Wiley & Sons, [2000]".
  - Crossref's published-print field says 1999-01-03 and published-online says 2008-05-27. The standard citation year, 2000 (the copyright year), is used.
- Summary: A reference monograph on statistics for directions, axes and rotations: the distributions on circles, spheres and manifolds (von Mises–Fisher, Bingham, and others) and inference with them.
- Sources: https://api.crossref.org/works/10.1002/9780470316979 ; https://katalog.muni.cz/Record/MUB01006362989/Description

## 26. LP-ICP: **PARTIAL** (no published venue found)

**IEEE:**
H. Yue, Q. Xu, F. Chen, J. Pan, and W. Chen, "LP-ICP: General localizability-aware point cloud registration for robust localization in extreme unstructured environments," 2025, *arXiv:2501.02580*.

- Authors: Haosong Yue, Qingyuan Xu, Fei Chen, Jia Pan, Weihai Chen.
- Why PARTIAL:
  - The arXiv page (v1 5 Jan 2025, v3 31 May 2025) has no journal-ref, and the v3 HTML has no acceptance notice.
  - Two web searches found no published version. One Crossref search hit the rate limit, so it is still possible that a published version exists.
  - Cite it as an arXiv preprint unless you can confirm a venue.
- Summary: A localizability-aware ICP that combines point-to-line and point-to-plane constraints, evaluates how well each pose direction is constrained, and adds extra constraints along weak directions to keep pose estimation stable in sparse, unstructured environments.
- Sources: https://arxiv.org/abs/2501.02580 ; https://arxiv.org/html/2501.02580v3

## 27. A-LOAM (GitHub software): **VERIFIED**

**IEEE (software / online resource):**
T. Qin and S. Cao, "A-LOAM: Advanced implementation of LOAM," GitHub repository. Accessed: Oct. 9, 2026. [Online]. Available: https://github.com/HKUST-Aerial-Robotics/A-LOAM

- Notes:
  - The repository exists. Its About text reads "Advanced implementation of LOAM".
  - The README names Tong Qin and Shaozu Cao as the people who modified the code, and credits J. Zhang and S. Singh for the original LOAM.
  - No release year is stated, so no year is given. Update the access date to when you finalise the paper.
- Summary: An open-source re-implementation of LOAM that uses Eigen and the Ceres Solver to give a simpler, cleaner code structure, intended as an accessible starting point for SLAM learners.
- Source: https://github.com/HKUST-Aerial-Robotics/A-LOAM

---

## Corrections relative to the draft list

- **#2 Ebadi:** the year is 2024 (T-RO vol. 40), not 2023.
- **#9 Hinduja:** the DOI is 10.1109/IROS40897.2019.8968577.
- **#10 X-ICP:** published in T-RO vol. 40, 2024.
- **#11 Nubert:** the venue is **IROS 2022** (pp. 17–24), not ICRA.
- **#12 Tuna:** IEEE Trans. Field Robot., vol. 2, pp. 485–515, 2025.
- **#13 DCReg:** now published in IJRR (OnlineFirst, Aug. 2026). Cite the journal DOI 10.1177/02783649261465040.
- **#14 NV-LIO:** the journal version is titled **NV-LIOM** (RA-L 2024). Cite it unless you specifically need the preprint.
- **#16 Hatleskog:** RA-L, vol. 9, no. 12, 2024.
- **#21 GEODE:** the formal title has no "GEODE". It is IJRR vol. 45, no. 1, 2026 (online 2025).
