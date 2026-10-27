# Open-source code for degeneracy-detection baselines and geometry-based degeneracy labels

Verification method (Oct 6, 2026): each GitHub repo was checked with `git ls-remote` and, for the key repos, a shallow clone so the source tree, LICENSE file and latest commit date could be read directly. "Last commit" is the date of the HEAD commit on the default branch. Repos that returned "could not read Username" from git are treated as **not existing / private** (GitHub returns an auth prompt for missing repos). The GitHub REST API was not reachable from this session, so star counts and the GitHub-detected language are not reported. Language is taken from the source files.

## Q1. Which baselines can be reproduced exactly from public code?

### Takeaway
Only DCReg (its own detector, plus its in-house ME-SR / ME-TSVD / ME-TReg / FCN-SR / O3D / XICP / SuperLoc baselines on the `baseline` branch), Zhang-Singh eigenvalue thresholding (LOAM / LeGO-LOAM / LIO-SAM), DRPM (Hatleskog & Alexis), and SuperLoc (inside SuperOdom, ROS 2) have public code. X-ICP has **no official public code**. The only public X-ICP is DCReg's re-implementation. L3E and LP-ICP repos exist but contain **no code**: L3E is a placeholder and LP-ICP was explicitly withdrawn. A-LOAM itself has **no degeneracy check**.

### Cited Findings

**DCReg — https://github.com/JokerJohn/DCReg (VERIFIED, cloned)**
- Paper: arXiv 2509.06285, accepted to IJRR in 2026 (README news: "2026/05/26: Dcreg has been accepted by IJRR"). — [DCReg README](https://github.com/JokerJohn/DCReg)
- Language and build: C++17, CMake. The `main` branch depends only on Eigen3 and PCL, with optional TBB/OpenMP. It does **not** need ROS. Ceres, yaml-cpp and Open3D are listed as "Not required by C++ core". The `baseline` branch's CMakeLists does `find_package` on Open3D, Eigen3, PCL, Ceres, yaml-cpp, TBB and OpenMP, and points `Open3D_DIR` at an `open3d_catkin` path from a catkin (ROS 1) workspace. — [DCReg README](https://github.com/JokerJohn/DCReg)
- **License: no LICENSE file in the repo root on `main` or `baseline`, and the README has no license statement.** By default the code is all-rights-reserved, so research reuse needs permission from the authors or citation-based fair use. Flag this in the thesis. — repo tree inspected
- Status: active. Last commit on `main` was 2026-06-22. The README reports "2026/04/21: released the verified full DCReg implementation on `main`" and "2025/09/23: released baseline codes and data, including ME-SR, ME-TSVD, ME-TReg, FCN-SR, O3D, XICP, and SuperLoc". The README also reports upstream PRs to Open3D (#7482) and PCL (#6432), dated 2026/04/27. — [DCReg README](https://github.com/JokerJohn/DCReg)
- What `main` implements, in `DCReg/include/dcreg.hpp` (1,096 lines):
  - Module 1: the Schur-complement spectra and condition numbers (`cond_full`, `cond_schur_rot`, `cond_schur_trans`).
  - Module 2: alignment of the eigenvectors to the physical axes, with contribution ratios and a 6-bit `degenerate_mask`.
  - Module 3: a PCG solve with clamped eigenvalues and a QR fallback.
  - Defaults in `utils.hpp`: `degeneracy_condition_threshold = 10.0` and `kappa_target = 10.0`. Other defaults are `pcg_tolerance 1e-6`, `pcg_max_iterations 10`, `plane_fit_neighbors 5`, `max_plane_thickness 0.2` and `search_radius 1.0`. — [DCReg repo source](https://github.com/JokerJohn/DCReg)
- **Standalone scan-to-map: yes.** The `dcreg_parking_lot_example` executable runs "a real parking-lot single-frame-to-map registration case". It needs `prior_map.pcd`, which is downloaded from Google Drive. Its log shows `Observability: schur_rot=..., schur_trans=..., mask=000100`. On `main`, `Algorithm` has only `kNone` and `kDCReg`, so the baselines are **not** on `main`. — [DCReg README](https://github.com/JokerJohn/DCReg)
- The **`baseline` branch** contains:
  - `DCReg/src/icp_test_runner.cpp`, `xicp.cpp`, `superloc.cpp`, and the headers `hessian_computer.h` and `dcreg.hpp`.
  - Configs `config/icp.yaml`, `icp_iter.yaml` and `icp_pk01.yaml`.
  - A `results/` tree with per-method TUM trajectories (dcreg, fcn-sr, me-sr, me-treg, me-tsvd, o3d) for building, cave02, corridor, parkinglot and stairs, plus simulation CSVs.
  - Python baselines `baseline/GeoTransformer` and `baseline/SC2-PCR`.
  - `scripts/get_gtpose.py`, which uses evo to fetch a GT pose for a timestamp. — branch tree inspected
- `icp_pk01.yaml` maps each method to a detection and handling pair: "ME-SR" = [FULL_EVD_MIN_EIGENVALUE, SOLUTION_REMAPPING]; "ME-TSVD" = [FULL_EVD_MIN_EIGENVALUE, TRUNCATED_SVD]; "ME-TReg" = [FULL_EVD_MIN_EIGENVALUE, STANDARD_REGULARIZATION]; "FCN-SR" = [FULL_SVD_CONDITION, SOLUTION_REMAPPING]; "XICP" = [XICP_INEQUALITY, XICP_CONSTRAINT]; "SuperLoc" = [SUPERLOC, SUPERLOC]; "Ours" = [SCHUR_CONDITION_NUMBER, PRECONDITIONED_CG].
  - Thresholds: `condition_threshold: 10.0`, `eigenvalue_threshold: 120.0`, Tikhonov `gamma: 100`, `tsvd singular_threshold: 120`, `LOAM eigen_threshold: 120`.
  - X-ICP thresholds: enough-info 300, insufficient-info 150, high-info 1000.
  - The file also contains the scan PCD, the `target_prior_map.pcd`, `gt_pose` and `initial_noise` fields. This is a ready-made **scan + map + GT-pose perturbation harness**. — `baseline:DCReg/config/icp_pk01.yaml`
- The README credits "Mr. Turcan Tuna for his technical assistance with the baseline XICP implementation". So DCReg's XICP is a **re-implementation** (Ceres-based, per `xicp.cpp`), not the original X-ICP code. — [DCReg README](https://github.com/JokerJohn/DCReg)

**Zhang & Singh eigenvalue degeneracy check (VERIFIED by grepping the source)**
- LeGO-LOAM, https://github.com/RobustFieldAutonomyLab/LeGO-LOAM. BSD-3-Clause, C++, ROS 1, last commit 2020-07-02 (unmaintained).
  - `mapOptmization.cpp:1287`: `float eignThre[6] = {100,...}`, followed by `if (matE.at<float>(0,i) < eignThre[i]) ... isDegenerate = true`.
  - `featureAssociation.cpp:1338`: a 3-DoF version with threshold 10. — [LeGO-LOAM](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM)
- LIO-SAM, https://github.com/TixiaoShan/LIO-SAM. BSD-3-Clause, C++, ROS 1 (master; a ROS 2 branch also exists), last commit 2023-04-17. `mapOptmization.cpp:1239` has the same 6-DoF check with threshold 100. — [LIO-SAM](https://github.com/TixiaoShan/LIO-SAM)
- loam_velodyne, https://github.com/laboshinl/loam_velodyne. The LICENSE is a Ji Zhang/CMU and SwRI copyright notice in BSD style. C++, ROS 1, last commit 2019-01-25.
  - `BasicLaserOdometry.cpp:574`: threshold 10.
  - `BasicLaserMapping.cpp:882`: threshold 100. — [loam_velodyne](https://github.com/laboshinl/loam_velodyne)
- A-LOAM, https://github.com/HKUST-Aerial-Robotics/A-LOAM. BSD-3-style license text, C++, ROS 1, last commit 2019-03-28. It uses Ceres, and `grep -i degenera` finds **nothing**, so A-LOAM has no degeneracy check. Any ME or FCN detector must be added by hand, for example by evaluating J^T J from the Ceres problem. — [A-LOAM](https://github.com/HKUST-Aerial-Robotics/A-LOAM)
- PALoc (below) also implements the Zhang-Kaess-Singh check. `paloc.cpp:2075-2099` cites "J. Zhang, M. Kaess and S. Singh, On degeneracy of optimization-based state estimation problems" and uses `condition_number_xyz > DEGENERACY_THRES || min_eigval_xyz < MIN_EIGENVALUE_THRESHOLD`. — [PALoc](https://github.com/JokerJohn/PALoc)

**DRPM (Hatleskog & Alexis), https://github.com/ntnu-arl/drpm (VERIFIED, cloned)**
- MIT license, C++, header-only (`src/degeneracy.h`) with an example and a Dockerfile. No ROS. Last commit 2024-10-15.
- It is "a reference implementation of the method proposed in the paper 'Probabilistic Degeneracy Detection for Point-to-Plane Error Minimization'" (arXiv 2410.10784). It is easy to drop into any point-to-plane solver. — [DRPM README](https://github.com/ntnu-arl/drpm)

**SuperLoc, inside SuperOdom: https://github.com/superxslam/SuperOdom (VERIFIED, cloned)**
- GPL-3.0, C++, **ROS 2 Humble** (default branch `ros2`), last commit 2026-07-23.
- The README news says "2025/08 — Release SuperLoc code to achieve online degeneracy detection". The features listed are "Alignment Risk Prediction" and "6 DOF degeneracy uncertainty detection".
- `LidarSlam.cpp` publishes `uncertainty_X/Y/Z/roll/pitch/yaw` (see `EstimateLidarUncertainty()`). There is no separate SuperLoc repo: `JokerJohn/SuperLoc` and `superxslam/SuperLoc` do not resolve. — [SuperOdom README](https://github.com/superxslam/SuperOdom); [SuperLoc page](https://superodometry.com/superloc)
- Its localization mode takes a GT map (`map_dir`) and an initial pose. The default map extent is ±525 m in x and y. — [SuperOdom LOCALIZATION.md](https://github.com/superxslam/SuperOdom/blob/ros2/doc/LOCALIZATION.md)

**X-ICP (Tuna et al., arXiv 2211.16335): NO official code found**
- The project site lists only the paper, a video and "Additional Data (Will be shared upon acceptance)". It gives no GitHub link. — [X-ICP site](https://sites.google.com/leggedrobotics.com/x-icp)
- Guessed repos `leggedrobotics/x-icp`, `leggedrobotics/perceptive_locomotion_x-icp`, `leggedrobotics/localizability` and `TurcanTuna/X-ICP` do not resolve.
- Related public code from the same lab:
  - https://github.com/leggedrobotics/open3d_slam: BSD-3, C++, ROS 1, last commit verified via clone. Its source has no "localizab" or "degenera" hits on the default branch.
  - https://github.com/leggedrobotics/icp_localization: BSD-3, ROS 1, last commit 2023-01-18. It does map-based ICP localization with libpointmatcher. — [icp_localization](https://github.com/leggedrobotics/icp_localization)

**L3E (Nubert et al., ICRA 2022, arXiv 2203.05698): repo exists, NO code**
- https://github.com/leggedrobotics/L3E. Its last commit is 2022-07-31, and the repo holds only a README and images. The README says "The corresponding code will be published upon publication of the paper", which has not happened four years on. — [L3E README](https://github.com/leggedrobotics/L3E)

**LP-ICP (arXiv 2501.02580): repo exists, code WITHDRAWN**
- The v1 paper says "dataset and code ... will also be open-sourced at https://github.com/xuqingyuan2000/LP-ICP". The authors are Yue, Xu, Chen, Pan and Chen (Beihang, CUHK, HKU). — [arXiv html v1](https://arxiv.org/html/2501.02580v1)
- The README update from May 2025 says "we decided not to release the project". The repo holds only a README, a LICENSE and figures. — [LP-ICP repo](https://github.com/xuqingyuan2000/LP-ICP)

**FAST-LIO forks with per-direction localizability: none verified**
- Upstream https://github.com/hku-mars/FAST_LIO is GPL-2.0, C++, ROS 1 (with ROS 2 branches), last commit 2024-07-23. A search turned up only generic forks and no maintained localizability fork. — [FAST_LIO](https://github.com/hku-mars/FAST_LIO); [search results](https://github.com/topics/lidar-odometry)

### Inferences
- **Exactly reproducible baselines:**
  - DCReg (`main`, with κ=10 for both Schur blocks).
  - ME-SR, ME-TSVD, ME-TReg, FCN-SR and O3D as **DCReg defines them** (`baseline` branch, threshold 120 for ME and 10 for FCN).
  - LOAM-style ME on LeGO-LOAM and LIO-SAM (threshold 100) and loam_velodyne.
  - DRPM.
  - SuperLoc (ROS 2 only; in DCReg's harness only as a re-implementation).
- **Approximate only:** X-ICP, which exists only as DCReg's re-implementation, so call it "XICP (DCReg re-impl.)".
- **Not reproducible:** L3E and LP-ICP.
- The thesis's detector is based on A-LOAM, which uses Ceres and has no degeneracy check. The cleanest route is to build J^T J (6x6) from the A-LOAM residuals at the final iterate and pass the same matrix to every detector in DCReg's `hessian_computer.h`/`icp_test_runner` or the `dcreg.hpp` modules, plus DRPM. That way all the detectors share one Hessian.
- DCReg has no license file, so its code should be cited and used for research comparison only. Its code should not be redistributed in a public thesis repo without the authors' consent.

### Gaps
- The `baseline` branch was inspected only at the file-list and config level. It was not built or run, so whether it compiles cleanly outside the authors' catkin path is unverified. CMake hardcodes `Open3D_DIR` to `/home/xchu/xicp_ws/...`.
- No A-LOAM fork with a degeneracy-aware solver was verified. Web search returned none, and no specific repo could be confirmed.
- How faithful DCReg's XICP and SuperLoc re-implementations are to the originals is not documented.

## Q2. Which label-generation pipeline (perturbation test at the GT pose vs. the GT map) can be built from existing code with the least effort?

### Takeaway
The least effort is a **GT-map, perturbation-at-GT-pose** oracle built from DCReg's `baseline` harness or `dcreg_parking_lot_example`, or from small_gicp/Open3D in Python. Each scan is registered to the GT map from N perturbed starts around the GT pose (from PALoc or the dataset), and an axis is labeled degenerate when the converged error spreads along it. PALoc supplies GT trajectories, GT maps and FusionPortable GT. evo handles trajectory alignment.

### Cited Findings

**PALoc, https://github.com/JokerJohn/PALoc (VERIFIED, cloned)**
- C++, ROS 1 Noetic on Ubuntu 20.04. It needs Open3D ≥0.17, PCL and GTSAM 4.2.0. A Docker image `ulterzlw/paloc` is available. Last commit 2026-01-21.
- **License:** the README shows an MIT badge, but the repo root has **no LICENSE file**, so the license is only declared in the README. — [PALoc README](https://github.com/JokerJohn/PALoc)
- What it does: "generating high-fidelity, dense 6-DoF ground truth (GT) trajectories ... leverages prior maps". It ships launch files for GEODE (VLP16, OS64), FusionPortable OS128 corridor, MS-dataset Pandar32 and Newer College OS128.
- It also has a real-time localization mode (`fp_os128_corridor_loc.launch`), a `/save_map` service and download links for GT maps.
- For the initial pose, the first scan is aligned to the prior map in CloudCompare. — [PALoc README](https://github.com/JokerJohn/PALoc)
- The `fp_gt/` folder (added 2026-01-20) holds generated GT trajectories for FusionPortable: 20220216_canteen_day, corridor_day, escalator_day, garden_day and 20220225_building_day. — PALoc repo tree
- Successor system: LTLoc (https://github.com/JokerJohn/LTLoc), a "real-time map-based localization system". **Unverified**, because it was not cloned. — [PALoc README](https://github.com/JokerJohn/PALoc)

**Map evaluation:** https://github.com/JokerJohn/Cloud_Map_Evaluation (MapEval) exists, with last commit 2026-03-22. Its root tree has no LICENSE file. It is used for map-based accuracy metrics. — [PALoc README](https://github.com/JokerJohn/PALoc); repo tree

**Registration and oracle libraries (VERIFIED LICENSE file and last commit)**

| Repo | License | Lang | ROS | Last commit | Role in benchmark |
|---|---|---|---|---|---|
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | MIT | C++/Python | none | 2026-09-16 | P2Plane ICP oracle. `GetInformationMatrixFromPointClouds` gives a 6x6 Hessian at a given pose (`Registration.h:225`). This is the "O3D" baseline in DCReg. |
| [koide3/small_gicp](https://github.com/koide3/small_gicp) | MIT | C++ with Python bindings (`src/python/align.cpp`) | none | 2026-09-30 | Fast multithreaded GICP/P2Plane for N-perturbation oracles. `RegistrationResult` exposes `H` (6x6 "final information matrix"), `b`, `error` and `num_inliers`. |
| [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) | MIT | C++/Python | ROS 1/2 wrappers | 2026-05-04 | Simple odometry baseline. Point-to-point only, so it is weaker as a P2Plane oracle. |
| [norlab-ulaval/libpointmatcher](https://github.com/norlab-ulaval/libpointmatcher) | BSD-3 | C++ | none (ROS wrappers separate) | 2026-08-27 | Configurable ICP with `PointToPlaneWithCov` minimizer (covariance output) and `force4DOF`. Used by leggedrobotics/icp_localization. |
| [MichaelGrupp/evo](https://github.com/MichaelGrupp/evo) | GPL-3.0 | Python | ROS 1 bag / ROS 2 bag readers | 2026-10-05 | APE/RPE with SE(3) alignment. DCReg's `get_gtpose.py` workflow uses `evo_ape tum ... -va` to get the alignment transform. |

- small_gicp registration result fields: `Eigen::Matrix<double,6,6> H; ///< Final information matrix`. — [small_gicp registration_result.hpp](https://github.com/koide3/small_gicp/blob/master/include/small_gicp/registration/registration_result.hpp)
- The DCReg baseline config has `gt_pose` and `initial_noise` fields and a `target_prior_map.pcd`, so the harness already supports "scan + GT map + GT pose + perturbation". — `JokerJohn/DCReg@baseline:DCReg/config/icp_pk01.yaml`

### Inferences
- **Recommended label pipeline (fewest new components):**
  1. Get GT poses from the dataset GT or from PALoc `fp_gt` (FusionPortable) / PALoc runs on GEODE / MS-dataset / Newer College, and the GT map from the PALoc download links.
  2. For each scan, crop the GT map around the GT pose. Run small_gicp (Python, MIT) or Open3D P2Plane from K perturbed initial poses, for example uniform within ±0.5 m and ±5°.
  3. Label axis i as degenerate when the spread of converged errors projected on that physical axis exceeds a tolerance, which gives an empirical per-axis localizability label.
  4. Also compute the 6x6 H at the GT pose (from small_gicp `H` or Open3D `GetInformationMatrixFromPointClouds`). This gives a "geometry-only" label, which is the same quantity the Schur and orientation-tensor channels see, so the perturbation label and the Hessian label can be cross-validated.
- The perturbation-at-GT-pose method is L3E-style, but L3E's code is unavailable, so it must be re-implemented. That is roughly 100–200 lines of Python on top of small_gicp or Open3D.
- The pure GT-map Hessian label is even cheaper, but it is circular when the detectors are Hessian-based. The perturbation-convergence label is the less biased choice.
- For running the baselines on the same frames, reusing DCReg's `baseline` `icp_test_runner` is the most direct option, because it already computes ME, FCN, XICP, SuperLoc and Schur on one scan/map pair. Expect build-path fixes, and the license is unclear.
- The license mix matters for releasing code: evo (GPL-3) and SuperOdom (GPL-3) are fine as external tools, but GPL code should not be linked into a permissively licensed release.

### Gaps
- LTLoc's contents and license were not verified.
- Whether the PALoc GT-map download links (gofile, SharePoint) are still live was not checked.
- No public tool was found that directly generates per-axis degeneracy labels from a GT map. This has to be written in-house.
- KISS-ICP's ROS wrapper versions and libpointmatcher's `PointToPlaneWithCov` output semantics were not inspected in detail.
