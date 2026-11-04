# -*- coding: utf-8 -*-
"""Text of the thesis report. Markup: **bold**, *italic*, _{sub}, ^{sup}, [[highlighted placeholder]], {@key} citation."""
import re

R = "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad"
FIG = R + "/rep/fig/"

TITLE = "DEGENERACY DETECTION AND MITIGATION IN LIDAR-INERTIAL-VISUAL SLAM"
GUIDE = "Dr. G. Sivasankar"

FRONT = dict(
    title=TITLE, name="KAVINKUMAR S", roll="CB.EN.P2MFA25004", month="NOVEMBER 2026", guide=GUIDE,
    designation="[[Designation]]",
    ack=[
        [("I would like to thank our beloved Chancellor ", False), ("AMMA", True), (", Vice-Chancellor, ", False), ("Dr. P. Venkat Rangan", True),
         (" and Dean, Engineering, ", False), ("Dr. Sasagan Ramanathan", True),
         (" for providing me with excellent infrastructure facilities which greatly helped me to carry out my project work.", False)],
        [("I would like to extend my warm thanks to my thesis advisor, ", False), (GUIDE, True), (", ", False), ("[[Designation]]", False),
         (", Department of Mechanical Engineering, Amrita School of Engineering, for guiding me through this project work and for the "
          "support and encouragement throughout it.", False)],
        [("I would like to thank ", False), ("Dr. K. Rameshkumar", True), (", Professor and Chairperson, Department of Mechanical Engineering, and my batch "
          "coordinator ", False), ("Dr. Rammohan S", True), (", Associate Professor, Department of Mechanical Engineering, Amrita School of Engineering, "
          "Amrita Vishwa Vidyapeetham, Coimbatore, for their support.", False)],
        [("I thank my family and friends for their patience and support during the many long test runs of this work.", False)],
    ],
    abstract=[
        "Mobile robots that map tunnels, mines and long corridors lose their LiDAR odometry when the scene stops constraining a "
        "direction of motion. In a corridor with smooth walls the motion along the axis is unobserved, and a camera-based estimator "
        "has to carry that direction. Switching methods such as Switch-SLAM choose between LiDAR and visual odometry with one "
        "eigenvalue test on the whole registration Hessian, in which rotation (radians) and translation (metres) share one scale.",
        "This work builds a LiDAR-visual-inertial odometry front end on A-LOAM and VINS-Mono that judges the two parts separately. "
        "The Schur complements of the A-LOAM Hessian give a rotation block (channel R) and a translation block (channel T); the "
        "translation block sets a per-direction weight between the LiDAR and the VINS-Mono increments. A third channel, the additional T, "
        "is computed from the raw keyframe points instead of the solver: the orientation tensor of the surface normals and edge directions "
        "bounds the translation information direction by direction, and the alignment of the same normals with a learned reference "
        "corrects the heading. Five versions (F20 to F24) were built; the later ones add a VINS-Mono trust check, an anchored hand-over "
        "from the LiDAR-only warm-up and a guard on A-LOAM's initial guess. F24 is the final version.",
        "Without loop closure and with frozen settings, F24 gave an ATE RMSE of 0.45 m on the SubT-MRS Multi Floor sequence (one live run) "
        "and 2.01 m on Long Corridor (mean of three live runs), against 1.61 m and 2.42 m published for Switch-SLAM. On a Gazebo farm route "
        "it gave 0.66 m with a 0.90 m maximum error, against 0.38 m and 1.10 m. Two of the three Long Corridor runs exceeded Switch-SLAM's "
        "5.09 m maximum error because of a heading error in the LiDAR-only warm-up, and the farm RMSE target was missed because the scale "
        "error of VINS-Mono leaks into the fused motion. The final version has not yet been run live on the held-out Cave02 and GEODE sequences.",
    ],
)

REFDB = {
    "cadena": 'C. Cadena *et al.*, "Past, present, and future of simultaneous localization and mapping: Toward the robust-perception age," *IEEE Trans. Robot.*, vol. 32, no. 6, pp. 1309-1332, Dec. 2016, doi: 10.1109/TRO.2016.2624754.',
    "ebadi": 'K. Ebadi *et al.*, "Present and future of SLAM in extreme environments: The DARPA SubT challenge," *IEEE Trans. Robot.*, vol. 40, pp. 936-959, 2024, doi: 10.1109/TRO.2023.3323938.',
    "loam": 'J. Zhang and S. Singh, "LOAM: Lidar odometry and mapping in real-time," in *Proc. Robot.: Sci. Syst. (RSS)*, Berkeley, CA, USA, Jul. 2014, doi: 10.15607/RSS.2014.X.007.',
    "lego": 'T. Shan and B. Englot, "LeGO-LOAM: Lightweight and ground-optimized lidar odometry and mapping on variable terrain," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)*, Madrid, Spain, Oct. 2018, pp. 4758-4765, doi: 10.1109/IROS.2018.8594299.',
    "liosam": 'T. Shan, B. Englot, D. Meyers, W. Wang, C. Ratti, and D. Rus, "LIO-SAM: Tightly-coupled lidar inertial odometry via smoothing and mapping," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)*, Las Vegas, NV, USA, 2020, pp. 5135-5142, doi: 10.1109/IROS45743.2020.9341176.',
    "fastlio2": 'W. Xu, Y. Cai, D. He, J. Lin, and F. Zhang, "FAST-LIO2: Fast direct LiDAR-inertial odometry," *IEEE Trans. Robot.*, vol. 38, no. 4, pp. 2053-2073, Aug. 2022, doi: 10.1109/TRO.2022.3141876.',
    "vinsmono": 'T. Qin, P. Li, and S. Shen, "VINS-Mono: A robust and versatile monocular visual-inertial state estimator," *IEEE Trans. Robot.*, vol. 34, no. 4, pp. 1004-1020, Aug. 2018, doi: 10.1109/TRO.2018.2853729.',
    "orbslam3": 'C. Campos, R. Elvira, J. J. G. Rodriguez, J. M. M. Montiel, and J. D. Tardos, "ORB-SLAM3: An accurate open-source library for visual, visual-inertial, and multimap SLAM," *IEEE Trans. Robot.*, vol. 37, no. 6, pp. 1874-1890, Dec. 2021, doi: 10.1109/TRO.2021.3075644.',
    "zhang2016": 'J. Zhang, M. Kaess, and S. Singh, "On degeneracy of optimization-based state estimation problems," in *Proc. IEEE Int. Conf. Robot. Autom. (ICRA)*, Stockholm, Sweden, May 2016, pp. 809-816, doi: 10.1109/ICRA.2016.7487211.',
    "switchslam": 'J. Lee *et al.*, "Switch-SLAM: Switching-based LiDAR-inertial-visual SLAM for degenerate environments," *IEEE Robot. Autom. Lett.*, vol. 9, no. 8, pp. 7270-7277, Aug. 2024, doi: 10.1109/LRA.2024.3421792.',
    "gelfand": 'N. Gelfand, L. Ikemoto, S. Rusinkiewicz, and M. Levoy, "Geometrically stable sampling for the ICP algorithm," in *Proc. 4th Int. Conf. 3-D Digit. Imag. Model. (3DIM)*, Banff, AB, Canada, Oct. 2003, pp. 260-267, doi: 10.1109/IM.2003.1240258.',
    "hinduja": 'A. Hinduja, B.-J. Ho, and M. Kaess, "Degeneracy-aware factors with applications to underwater SLAM," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)*, Macau, China, Nov. 2019, pp. 1293-1299, doi: 10.1109/IROS40897.2019.8968577.',
    "hatleskog": 'J. Hatleskog and K. Alexis, "Probabilistic degeneracy detection for point-to-plane error minimization," *IEEE Robot. Autom. Lett.*, vol. 9, no. 12, pp. 11234-11241, Dec. 2024, doi: 10.1109/LRA.2024.3484153.',
    "nubert": 'J. Nubert, E. Walther, S. Khattak, and M. Hutter, "Learning-based localizability estimation for robust LiDAR localization," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)*, Kyoto, Japan, Oct. 2022, pp. 17-24, doi: 10.1109/IROS47612.2022.9982257.',
    "xicp": 'T. Tuna, J. Nubert, Y. Nava, S. Khattak, and M. Hutter, "X-ICP: Localizability-aware LiDAR registration for robust localization in extreme environments," *IEEE Trans. Robot.*, vol. 40, pp. 452-471, 2024, doi: 10.1109/TRO.2023.3335691.',
    "tuna2025": 'T. Tuna, J. Nubert, P. Pfreundschuh, C. Cadena, S. Khattak, and M. Hutter, "Informed, constrained, aligned: A field analysis on degeneracy-aware point cloud registration in the wild," *IEEE Trans. Field Robot.*, vol. 2, pp. 485-515, 2025, doi: 10.1109/TFR.2025.3576053.',
    "dcreg": 'X. Hu, X. Chen, M. Jia, J. Wu, P. Tan, and S. L. Waslander, "DCReg: Decoupled characterization for efficient degenerate LiDAR registration," *Int. J. Robot. Res.*, early access, Aug. 2026, doi: 10.1177/02783649261465040.',
    "lpicp": 'H. Yue, Q. Xu, F. Chen, J. Pan, and W. Chen, "LP-ICP: General localizability-aware point cloud registration for robust localization in extreme unstructured environments," 2025, *arXiv:2501.02580*.',
    "lfgicp": 'E. Im, "LF-GICP: Parameter-free degeneracy-aware LiDAR odometry via a voxel-normal localizability field," Aug. 2026, *arXiv:2608.19522*.',
    "bingham": 'C. Bingham, "An antipodally symmetric distribution on the sphere," *Ann. Statist.*, vol. 2, no. 6, pp. 1201-1225, Nov. 1974, doi: 10.1214/aos/1176342874.',
    "mardia": 'K. V. Mardia and P. E. Jupp, *Directional Statistics*. Chichester, U.K.: Wiley, 2000, doi: 10.1002/9780470316979.',
    "advani": 'S. G. Advani and C. L. Tucker III, "The use of tensors to describe and predict fiber orientation in short fiber composites," *J. Rheol.*, vol. 31, no. 8, pp. 751-784, 1987, doi: 10.1122/1.549945.',
    "lvisam": 'T. Shan, B. Englot, C. Ratti, and D. Rus, "LVI-SAM: Tightly-coupled lidar-visual-inertial odometry via smoothing and mapping," in *Proc. IEEE Int. Conf. Robot. Autom. (ICRA)*, Xi\'an, China, May 2021, pp. 5692-5698, doi: 10.1109/ICRA48506.2021.9561996.',
    "relead": 'Z. Chen *et al.*, "RELEAD: Resilient localization with enhanced LiDAR odometry in adverse environments," in *Proc. IEEE Int. Conf. Robot. Autom. (ICRA)*, Yokohama, Japan, May 2024, pp. 3999-4005, doi: 10.1109/ICRA57147.2024.10611074.',
    "subtmrs": 'S. Zhao *et al.*, "SubT-MRS dataset: Pushing SLAM towards all-weather environments," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Seattle, WA, USA, Jun. 2024, pp. 22647-22657.',
    "geode": 'Z. Chen *et al.*, "Heterogeneous LiDAR dataset for benchmarking robust localization in diverse degenerate scenarios," *Int. J. Robot. Res.*, vol. 45, no. 1, pp. 6-22, Jan. 2026, doi: 10.1177/02783649251344967.',
    "aloam": 'T. Qin and S. Cao, "A-LOAM: Advanced implementation of LOAM," GitHub repository, HKUST Aerial Robotics Group. [Online]. Available: https://github.com/HKUST-Aerial-Robotics/A-LOAM',
    "gazebo": 'N. Koenig and A. Howard, "Design and use paradigms for Gazebo, an open-source multi-robot simulator," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)*, Sendai, Japan, Sep. 2004, pp. 2149-2154, doi: 10.1109/IROS.2004.1389727.',
    "umeyama": 'S. Umeyama, "Least-squares estimation of transformation parameters between two point patterns," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 13, no. 4, pp. 376-380, Apr. 1991, doi: 10.1109/34.88573.',
    "sturm": 'J. Sturm, N. Engelhard, F. Endres, W. Burgard, and D. Cremers, "A benchmark for the evaluation of RGB-D SLAM systems," in *Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)*, Vilamoura, Portugal, Oct. 2012, pp. 573-580, doi: 10.1109/IROS.2012.6385773.',
}

T = "\t"
SW = "Switch-SLAM"

BODY = [
    # =========================================================== CHAPTER 1
    ("chapter", "1", "Introduction"),
    ("h2", "1.1 Introduction"),
    ("p", "Autonomous mobile robots now carry material in factories and warehouses, inspect tunnels and mines, and survey places where a "
          "person should not go. Each of these jobs needs the robot to know where it is and what its surroundings look like, which is the "
          "problem of simultaneous localization and mapping (SLAM) {@cadena}. A robot that does SLAM well can plan a path, return to a "
          "charging point and leave behind a map that people can use. A robot that does it badly drifts, and in a long tunnel a few degrees "
          "of heading error become several metres of position error."),
    ("p", "Three sensors are common on such robots. A 3D LiDAR measures the geometry of the scene directly and at metric scale, so LiDAR "
          "odometry such as LOAM {@loam} and its successors {@lego,liosam,fastlio2} is accurate wherever the scene has enough structure. A "
          "camera sees texture, and an inertial measurement unit (IMU) measures angular rate and acceleration; visual-inertial odometry (VIO) "
          "such as VINS-Mono {@vinsmono} combines the two. The sensors fail in different places. The LiDAR fails where the geometry repeats "
          "itself, and the camera fails in the dark, on bare walls and during fast rotation. The DARPA Subterranean Challenge showed how often "
          "both happen underground {@ebadi}."),
    ("h2", "1.2 LiDAR degeneracy"),
    ("p", "A LiDAR odometry estimates the motion between scans by registering the new scan to a map, usually by Gauss-Newton or "
          "Levenberg-Marquardt minimisation of point-to-plane and point-to-line distances. The registration Hessian H (6 x 6, three rotation "
          "and three translation directions) says how strongly the scan constrains each direction. When the walls of a corridor are smooth "
          "and parallel, every plane normal is perpendicular to the corridor axis, so a shift along the axis does not change any residual and "
          "H has a near-zero eigenvalue in that direction. The solver still returns an answer, but along that direction it is determined by "
          "noise and by the initial guess. Zhang, Kaess and Singh called this degeneracy and proposed to detect it from the eigenvalues of H "
          "{@zhang2016}."),
    ("p", "The effect is large on real data. In this work A-LOAM {@aloam}, run on its own, gave an absolute trajectory error (ATE) of "
          "15.8 m on the 579 m SubT-MRS Long Corridor sequence and 66 m on the 695 m Corridor02 sequence, against 0.4 to 2.2 m for the fused "
          "estimates reported later. In the Multi Floor sequence, where a legged robot climbs stairs between floors, A-LOAM alone gave 26.4 m."),
    ("h2", "1.3 Visual-inertial odometry and its failures"),
    ("p", "A monocular VIO such as VINS-Mono {@vinsmono} tracks image features and integrates the IMU between frames. It does not depend on "
          "the geometry of the scene, so it keeps working in a corridor, but its scale is observable only through the accelerometer and it "
          "drifts slowly in heading. It also needs texture and parallax: a pure in-place rotation gives no parallax, and a dark or "
          "featureless wall gives no features. On the sequences of this work VINS-Mono alone gave 1.28 m on Multi Floor, 5.81 m on Long "
          "Corridor, 4.03 m on Corridor02 and 10.25 m on Cave02, and on the GEODE stairs sequence it lost track repeatedly and reached "
          "270 m. The LiDAR is the better sensor where the geometry is rich, and the VIO is the better sensor along a degenerate direction."),
    ("h2", "1.4 Switching-based LiDAR-visual-inertial fusion"),
    ("p", "Switch-SLAM {@switchslam} runs LiDAR-inertial and visual-inertial odometry side by side and switches the initial pose of the "
          "LiDAR odometry to the visual estimate when it detects LiDAR degeneracy. The detector compares the eigenvalues of the registration "
          "Hessian with a threshold derived from the semicircle law of random matrices. Two features of this design leave room for "
          "improvement. First, the test is applied to the whole Hessian, in which rotation is measured in radians and translation in metres, "
          "so a rotation problem can be hidden by the larger translation numbers and the reverse. Second, the decision is all or nothing: "
          "the whole pose comes from one source, although in a corridor only one translation direction is lost and the other five are still "
          "well constrained by the LiDAR. The detector also trusts the solver's own Hessian; a solver that converges to a wrong minimum can "
          "report a confident Hessian."),
    ("h2", "1.5 Problem statement"),
    ("p", "To build a LiDAR-inertial-visual odometry that detects LiDAR degeneracy separately for rotation and translation, using the Schur "
          "complements of the registration Hessian, adds a check computed from the raw scan geometry that does not depend on the solver, "
          "and uses both to weight the LiDAR and VIO motion direction by direction instead of switching between them."),
    ("h2", "1.6 Objectives"),
    ("bul", ["To separate the rotation and translation information of the A-LOAM registration Hessian with Schur complements (channels R "
             "and T) and use the translation block to weight the LiDAR and VINS-Mono increments per direction.",
             "To add an independent channel from the raw keyframe geometry, the orientation tensor of surface normals and edges, that checks "
             "the translation information and corrects the heading (the additional T channel).",
             "To implement the method live in ROS on A-LOAM and VINS-Mono and test it on the SubT-MRS bags and a Gazebo farm simulation.",
             "To compare it with VINS-Mono alone, A-LOAM alone, earlier versions of the method and the published Switch-SLAM front-end "
             "results, with frozen settings and without loop closure.",
             "To report held-out results and failures as well as successes, with pass rules written before each live test."]),

    # =========================================================== CHAPTER 2
    ("chapter", "2", "Literature Review"),
    ("h2", "2.1 Introduction"),
    ("p", "This chapter reviews how degeneracy has been detected from the registration Hessian, how rotation and translation have been "
          "separated, how surface-normal statistics have been used as a geometry-based measure, and how LiDAR, visual and inertial odometry "
          "have been combined in degenerate scenes. It ends with the gap this work addresses."),
    ("h2", "2.2 Degeneracy detection from the registration Hessian"),
    ("p", "Gelfand et al. {@gelfand} analysed the stability of point-to-plane ICP through the eigenvectors of the 6 x 6 covariance of the "
          "constraint and sampled points so that weak directions are covered. Zhang, Kaess and Singh {@zhang2016} defined a degeneracy factor "
          "as the smallest eigenvalue of the Hessian and projected the solution update onto the well-constrained subspace (solution "
          "remapping). Their threshold is a constant chosen per sensor setup. Hinduja et al. {@hinduja} carried the same idea into a factor "
          "graph by adding only the constrained directions of a registration factor, and applied it to underwater SLAM."),
    ("p", "Later work made the test less ad hoc. Hatleskog and Alexis {@hatleskog} propagated the point noise into the eigenvalues and "
          "decided degeneracy with a probabilistic test instead of a fixed threshold. Nubert et al. {@nubert} learned localizability from "
          "simulated data. X-ICP {@xicp} computed localizability per direction from the contribution of each point and constrained the "
          "optimisation in the weak directions, and a field study {@tuna2025} compared detection and mitigation strategies of this kind on real data "
          "from several robots."),
    ("h2", "2.3 Separating rotation and translation"),
    ("p", "The eigenvalues of the full Hessian mix two units. A rotation eigenvalue scales with the square of the range of the points, a "
          "translation eigenvalue does not, so a threshold that suits one is wrong for the other. DCReg {@dcreg} separates the two with Schur "
          "complements: the rotation block is the rotation information left after the translation has been estimated, and the reverse. On "
          "the SubT-MRS Cave02 and GEODE stairs sequences, where rotation and translation are strongly coupled, it reported localisation errors of a few "
          "centimetres where minimum-eigenvalue detection failed. DCReg is a registration method; it does not fuse a second sensor."),
    ("h2", "2.4 Geometry-based measures from surface normals"),
    ("p", "The distribution of the surface normals of a scan describes which directions the scene can constrain, without reference to any "
          "solver. The Bingham distribution {@bingham} is the standard model for axial data such as normals, and its sufficient statistic "
          "is the second-moment orientation tensor T = (1/n) sum n n^{T} {@mardia}. Orientation tensors of second and fourth order are also used to "
          "describe fibre orientation in composites {@advani}. In LiDAR odometry, LF-GICP {@lfgicp} builds a planarity-weighted normal tensor "
          "of the map and uses its smallest eigenvalue to gate a reweighting of the registration, arguing that the Gauss-Newton Hessian can "
          "hide degeneracy. So the orientation tensor as a solver-independent degeneracy measure is prior art; LF-GICP is LiDAR-only and "
          "does not use the tensor to correct heading."),
    ("h2", "2.5 LiDAR-visual-inertial fusion in degenerate scenes"),
    ("p", "Tightly coupled LiDAR-inertial odometries such as LIO-SAM {@liosam} and FAST-LIO2 {@fastlio2} use the IMU to bridge short "
          "degenerate stretches, but do not use a camera. LVI-SAM {@lvisam} couples a visual-inertial and a LiDAR-inertial subsystem; the "
          "visual system gives the initial guess of the LiDAR scan matching, and the LiDAR depth helps the visual features. RELEAD {@relead} "
          "constrains the LiDAR optimisation in non-localizable directions and fuses it with VIO in a graph. ORB-SLAM3 {@orbslam3} is a feature-based "
          "visual-inertial SLAM with maps and relocalisation, but it has no LiDAR. Switch-SLAM {@switchslam}, described in Section 1.4, is "
          "the closest system to this work and its published results (Table II of that paper, without loop closure) are the targets used "
          "in Chapter 5."),
    ("h2", "2.6 Datasets for degenerate environments"),
    ("p", "SubT-MRS {@subtmrs} provides LiDAR, camera and IMU data from legged, wheeled and handheld platforms in tunnels, caves, corridors "
          "and stairwells, with ground-truth trajectories; its Multi Floor and Long Corridor sequences are used by Switch-SLAM. GEODE "
          "{@geode} provides several LiDAR types in degenerate scenes, including a stairwell with a map-based ground truth. Both are used in "
          "this work, together with a Gazebo {@gazebo} farm world; Switch-SLAM also evaluated on simulated Gazebo scenes, including a farm."),
    ("tab", "2.1", "Summary of the literature closest to this work",
     [["Work", "Contribution", "Limitation for this problem"],
      ["Zhang et al., 2016 {@zhang2016}", "Smallest Hessian eigenvalue as degeneracy factor; solution remapping", "Fixed threshold; rotation and translation in one matrix"],
      ["Tuna et al., 2024 {@xicp}", "Per-direction localizability from point contributions (X-ICP)", "LiDAR only; thresholds per platform"],
      ["Hatleskog and Alexis, 2024 {@hatleskog}", "Noise-propagated probabilistic degeneracy test", "LiDAR only; uses the solver's Hessian"],
      ["Hu et al., 2026 {@dcreg}", "Schur-complement separation of rotation and translation (DCReg)", "Registration only; no camera or VIO"],
      ["Im, 2026 {@lfgicp}", "Orientation tensor of map normals as solver-independent measure", "LiDAR only; no heading use; preprint"],
      ["Shan et al., 2021 {@lvisam}", "Visual-inertial guess for LiDAR matching (LVI-SAM)", "No per-direction degeneracy weighting"],
      ["Lee et al., 2024 {@switchslam}", "Switches the LiDAR initial pose to VIO when degenerate (Switch-SLAM)", "Whole-Hessian test; all-or-nothing switch"]],
     [2350, 3000, 2930], dict(align="llr".replace("r", "l"))),
    ("h2", "2.7 Summary"),
    ("p", "Three points come out of the review. Rotation and translation degeneracy have different causes and units and are better judged "
          "separately, and the Schur complement is a clean way to do it {@dcreg}. The methods that separate them work on the LiDAR alone and "
          "rely on the solver's own Hessian. The fusion systems that add a camera {@switchslam,lvisam} switch the whole pose or the initial "
          "guess and do not weight directions. No system found in this review combines Schur-separated channels with an independent check "
          "from the raw geometry inside a LiDAR-visual-inertial fusion. That combination is the subject of this work."),

    # =========================================================== CHAPTER 3
    ("chapter", "3", "Methodology"),
    ("h2", "3.1 Introduction"),
    ("p", "The work was done in the order of Figure 3.1. A pipeline of A-LOAM and VINS-Mono was set up first, then the fusion channels "
          "were designed and their constants frozen on recorded runs. Live runs exposed failures that replays had not shown; each was "
          "diagnosed from the logs and fixed by a small, testable change, which produced the versions F20 to F24. Every live test had a pass "
          "rule written before it was run, and every run is reported, including failed ones."),
    ("fig", FIG + "f3_1_flow.png", 3.3, "3.1", "Flowchart of methodology"),
    ("h2", "3.2 System overview"),
    ("p", "The fusion is VIO-primary (Figure 3.2). For every LiDAR scan the fusion node receives the A-LOAM scan-to-map pose and its "
          "Hessian, and the VINS-Mono pose at the same time. It forms the LiDAR increment (rotation vector φ_{L}, translation Δt_{L}) and the "
          "VINS increment (φ_{V}, Δt_{V}) since the previous scan and blends them with two 3 x 3 weights:"),
    ("eq", "φ = W_{R} φ_{L} + (I - W_{R}) φ_{V}", "3.1"),
    ("eq", "Δt = W_{t} Δt_{L} + (I - W_{t}) Δt_{V}", "3.2"),
    ("p", "The fused pose is the previous fused pose composed with this increment. W = 0 means the VIO carries a direction, W = I means the "
          "LiDAR carries it. For the first 20 s after VINS-Mono starts (T_{warm}) the output is LiDAR only, because a monocular VIO needs "
          "time to settle its scale; the same warm-up is repeated after VINS-Mono is lost (mode VO_FAIL: no message, a jump above 1 m or "
          "0.5 rad, or a restart). The loop is closed: the fused pose, moved forward by the latest VINS motion, is A-LOAM's initial guess "
          "for the next scan."),
    ("fig", FIG + "f3_2_arch.png", 5.6, "3.2", "Structure of the fusion: channels R, T and the additional T"),
    ("h2", "3.3 Schur decomposition of the registration Hessian"),
    ("p", "The A-LOAM Hessian is partitioned into rotation (R) and translation (t) blocks, with rotation in radians and translation in "
          "metres:"),
    ("eq", "H = [ H_{RR}   H_{Rt} ;  H_{tR}   H_{tt} ]", "3.3"),
    ("p", "The Schur complements give the information about one part after the other part has been estimated from the same data:"),
    ("eq", "S_{RR} = H_{RR} - H_{Rt} H_{tt}^{-1} H_{tR}", "3.4"),
    ("eq", "S_{tt} = H_{tt} - H_{tR} H_{RR}^{-1} H_{Rt}", "3.5"),
    ("p", "S_{tt} is the translation information that is left once the scan's rotation is free, and S_{RR} the reverse. Each is a 3 x 3 "
          "matrix in one unit, so its eigenvalues can be compared within the block. In a corridor S_{tt} has one small eigenvalue along the "
          "axis and two large ones across it."),
    ("h2", "3.4 Channel T: per-direction translation weight"),
    ("p", "The translation block is turned into a weight by treating the LiDAR increment as a measurement with information c_{T} S_{tt} "
          "and the VIO increment as a prior with information γ I:"),
    ("eq", "W_{t} = (c_{T} S_{tt} + γ I)^{-1} c_{T} S_{tt}", "3.6"),
    ("p", "Along an eigenvector of S_{tt} with eigenvalue λ the weight is c_{T}λ / (c_{T}λ + γ): close to 1 where the scene constrains the "
          "motion and close to 0 along a degenerate axis. There is no switching threshold; the condition-number gate of earlier versions is "
          "disabled (KAPPA_TH = 10^{9}). The scale c_{T} = 0.03 was chosen once on Multi Floor recordings (smallest mean ATE, middle of the "
          "plateau) and has not been changed since. γ = 1 normally; Section 3.7 describes when it changes."),
    ("h2", "3.5 Channel R: rotation block and rotation check"),
    ("p", "With A-LOAM the VINS-Mono rotation was found to be better than the LiDAR rotation on most sequences: making the "
          "rotation weight active (c_{R} > 0) improved Long Corridor in replay but made Multi Floor, Corridor02 and Cave02 worse. So in "
          "normal operation c_{R} = 0, the rotation comes from the VIO and S_{RR} is monitored. A rotation check compares the VIO and LiDAR "
          "rotations over 2 s and 10 s windows. When they disagree by more than 0.402 rad and 0.585 rad (the largest values seen on 19 Multi "
          "Floor recordings), the LiDAR rotation carries the step with W_{R} = (S_{RR} + 10^{-3} I)^{-1} S_{RR}. The check did not close on "
          "any row of the bag runs, so its value is untested on this data; it is kept as a safeguard for a VIO rotation failure."),
    ("h2", "3.6 Additional T channel: the orientation tensor"),
    ("h3", "3.6.1 Tensor from the keyframe scan"),
    ("p", "For each LiDAR keyframe the 12 nearest neighbours of every point are found and their covariance is decomposed (eigenvalues "
          "λ_{1} ≤ λ_{2} ≤ λ_{3}). A point is planar when (λ_{2} - λ_{1})/λ_{3} > 0.5, with normal n, and linear when (λ_{3} - λ_{2})/λ_{3} > 0.5, "
          "with direction d. A plane constrains translation along its normal; an edge constrains translation in the plane perpendicular to "
          "its direction. The geometric orientation tensor counts both:"),
    ("eq", "G = ( Σ_{planar} n n^{T} + ½ Σ_{linear} (I - d d^{T}) ) / (n_{p} + n_{l})", "3.7"),
    ("p", "G has trace 1 and uses no correspondences, no solver state and no threshold. Between keyframes it is rotated into the current "
          "LiDAR frame. A tensor of planar normals alone was tried first and rejected: it understated the support that A-LOAM really has "
          "from edge features such as door frames and pipes, and every rule built on it made the corridors 0.26 to 1.0 m worse in replay."),
    ("h3", "3.6.2 Combining the tensor with S_{tt}"),
    ("p", "The tensor is scaled to the same total information as the solver, B = tr(H_{tt}) G, and combined with A = S_{tt} by a basis-free "
          "matrix rule. Several rules were compared by replay on clean data and under injected faults (Chapter 5). The final version uses "
          "the generalised maximum:"),
    ("eq", "S'_{tt} = B^{½} max(M, I) B^{½},   M = B^{-½} A B^{-½}", "3.8"),
    ("p", "where max(M, I) raises every generalised eigenvalue below 1 to 1. Along each direction the combined information is the larger "
          "of what the solver and the raw geometry support, and S'_{tt} replaces S_{tt} in Equation 3.6. F20 used the opposite rule (the "
          "minimum, a fail-safe cap). The maximum was chosen in a pre-registered comparison because it scored best over the clean and "
          "fault cells and on a held-out farm bag; it is not a fail-safe, and protection against a confident but wrong solver comes from "
          "the VIO-trust check of Section 3.7."),
    ("h3", "3.6.3 Heading from the same normals"),
    ("p", "The second read-out of the normals corrects heading, which VINS-Mono cannot observe and which dominates the error in long "
          "corridors. The near-vertical planar normals of a keyframe are levelled with the VIO gravity direction and their horizontal "
          "directions form an axial histogram h(θ) (0.5° bins over 180°). The heading error is the shift that best aligns h(θ) with a "
          "reference histogram learned in the world frame, searched over ±15°. The estimate passes through a Kalman update and is applied "
          "at no more than 0.25° per scan. It switches itself off when the structure is not distinct: a null-model test against random "
          "directions, a unique correlation peak, a chi-square gate and a drift gate. This structure-anchored heading (SAH) is a function of "
          "the even-order orientation tensors of the same normals: the k-th circular harmonic of h(θ) is fixed by the horizontal part of "
          "the tensor of order 2k. The fourth order matters, because with two equally strong perpendicular wall families the second-order "
          "tensor is isotropic and carries no heading information."),
    ("h2", "3.7 Safeguards added after the live tests"),
    ("p", "**VIO-trust check (F21).** For every scan the ratio of VINS and LiDAR path lengths over 10 s windows inside one VINS segment is "
          "formed, and r is the RMS of ln(|Δt_{V}|/|Δt_{L}|). While r stays at or below 0.157 (and a fast 5 s version at or below 0.277), γ = 1 "
          "in Equation 3.6; otherwise γ = 0 and the LiDAR carries the step. Both references, and the guard constant below, were set from six Multi Floor "
          "calibration replays. A LiDAR guard works the other way: while the VINS is trusted, a LiDAR path that runs more than 4.325 m "
          "ahead of the VINS path within 2 s marks the LiDAR step as failed."),
    ("p", "**Anchored hand-over (F22, F23).** In the live Long Corridor runs of F20 the fused heading jumped by 6 to 7° at the first fused "
          "scan: the warm-up had already integrated a fast turn with the LiDAR rotation, and VINS-Mono, which lagged by about 5°, added its "
          "catch-up of the same turn. At every entry into the fused mode the rotation is now reset to"),
    ("eq", "R_{f} = R_{off} R_{vL},   R_{off} = mean_{k} ( R_{A,k} R_{vL,k}^{T} )", "3.9"),
    ("p", "where R_{vL} is the LiDAR orientation predicted by VINS-Mono, R_{A,k} the A-LOAM orientation at warm-up scan k, and the mean is a "
          "robust chordal mean over all warm-up scans of the current VINS segment. VINS-Mono then continues from a reference consistent with "
          "itself, so its catch-up removes the transient instead of adding it."),
    ("p", "**Mapping-guess guard (F24).** In a live farm run of F23 the error reached 5.3 m in the first 18 s, while VINS-Mono was failing. "
          "The likely cause, not proven by that single run, is that VINS steps of 1 to 3 m were passed into A-LOAM's initial guess and "
          "A-LOAM's odometry followed them. In F24 the VINS motion is "
          "used in the guess only when the previous mode was not VO_FAIL and the step is within the jump limits (1 m, 0.5 rad); otherwise "
          "the guess is the last fused pose. The fused output itself is unchanged by this rule."),
    ("h2", "3.8 Versions F20 to F24 and the choice of the final version"),
    ("p", "Table 3.1 lists the five versions. All share channels R, T and the additional T; they differ in the tensor rule and in the "
          "safeguards. No constant was fitted to a test sequence after F20; the new constants of F21 come from Multi Floor, and F22 to F24 "
          "add none."),
    ("tab", "3.1", "Versions of the method",
     [["Version", "Settings added", "Reason (observed failure)"],
      ["F20", "Schur R + rotation check, Schur T (c_{T} = 0.03), OT channel: min rule on G, SAH", "Base structure"],
      ["F21", "OT rule gmax; VIO-trust check and LiDAR guard", "VINS-Mono scale failures (GEODE, injected faults)"],
      ["F22", "F20 + anchored hand-over", "Heading step at the warm-up exit (Long Corridor)"],
      ["F23", "F21 + anchored hand-over", "Same, with the VIO-trust check"],
      ["F24", "F23 + mapping-guess guard", "Start transient on the farm (VINS steps fed to A-LOAM)"]],
     [1000, 4083, 3200], dict(align="cll")),
    ("p", "**F24 is chosen as the final version.** It keeps all three channels of F20 and adds one safeguard for each failure seen in live "
          "runs. On the bag sequences the guard of F24 never acted (no VO_FAIL row and no VINS step above 1 m), so there it behaves exactly "
          "like F23, which had the best replay results of all versions on Long Corridor and Corridor02 (Table 5.1). On the farm, F24 is the "
          "only version whose maximum error was within Switch-SLAM's bound. Its constants are listed in Table 3.2."),
    ("tab", "3.2", "Frozen constants of the final version F24",
     [["Constant", "Value", "Source"],
      ["c_{T} (translation information scale)", "0.03", "Multi Floor, once"],
      ["c_{R} (rotation, normal operation)", "0", "Replay: LiDAR rotation worse than VIO with A-LOAM"],
      ["Warm-up T_{warm}", "20 s", "Design value"],
      ["Jump limits", "1 m, 0.5 rad", "Design value"],
      ["Rotation check references", "0.402 rad / 2 s, 0.585 rad / 10 s", "Largest on 19 Multi Floor recordings"],
      ["VIO-trust references", "0.157 (10 s), 0.277 (5 s)", "Largest on six Multi Floor replays"],
      ["LiDAR guard", "4.325 m over 2 s", "Six Multi Floor replays"],
      ["Tensor k-NN, planarity / linearity", "12, 0.5 / 0.5", "Shared with SAH"],
      ["SAH search, step limit", "±15°, 0.25° per scan", "Developed on Long Corridor and Corridor02"]],
     [3000, 2483, 2800], dict(align="llr".replace("r", "l"))),
    ("h2", "3.9 Evaluation metrics and protocol"),
    ("p", "The accuracy measure is the absolute trajectory error {@sturm}. The estimated positions p_{i} are aligned to the ground truth g_{i} "
          "by the rigid transformation (R, t) that minimises the squared error, without scale (Umeyama {@umeyama}), over the full span of "
          "the run, and"),
    ("eq", "ATE = ( (1/N) Σ_{i} || R p_{i} + t - g_{i} ||^{2} )^{½}", "3.10"),
    ("p", "The maximum of ||R p_{i} + t - g_{i}|| is reported beside it, because Switch-SLAM reports both. All results are front end only, "
          "without loop closure, to match the Switch-SLAM table. Two kinds of result are kept apart. A replay feeds the logged A-LOAM and "
          "VINS-Mono poses of a recorded run through the real fusion node; it is exact for the fusion but open loop, because A-LOAM is not "
          "re-seeded by the new poses. A live run executes the whole pipeline on the bag or in Gazebo. Only live runs are compared with "
          "published numbers. Multi Floor, Long Corridor and Corridor02 were used to design and diagnose the method, so they are "
          "development sequences; Cave02, GEODE stairs and the farm route are treated as held out."),

    # =========================================================== CHAPTER 4
    ("chapter", "4", "Test Setup"),
    ("h2", "4.1 Introduction"),
    ("p", "This chapter describes the computing setup, the datasets, the Gazebo farm simulation and the procedure used for every run. The "
          "same scripts were used for all configurations, so a difference between two results comes from the configuration and from "
          "run-to-run variation, not from the procedure."),
    ("h2", "4.2 Computing and software setup"),
    ("p", "All live runs were made on one laptop running Ubuntu with Docker. ROS Noetic runs in separate containers on a Docker network, "
          "with the ROS master in the A-LOAM container (Figure 4.1). A-LOAM and the fusion node share one container, VINS-Mono runs in a "
          "second one, bags are played from a third, throw-away container, and a fourth container with the full ROS desktop shows the run "
          "live in RViz. roscore is restarted for every run so that no state carries over. The laptop specification is [[CPU, RAM and GPU of "
          "the laptop to be added]]."),
    ("fig", FIG + "f4_1_setup.png", 5.6, "4.1", "Layout of the experimental setup"),
    ("tab", "4.1", "Software components",
     [["Component", "Role", "Notes"],
      ["ROS Noetic, Docker", "Middleware, isolation", "One container per subsystem"],
      ["A-LOAM {@aloam}", "LiDAR scan-to-map odometry", "Publishes pose and 6 x 6 Hessian; initial guess from the fusion"],
      ["VINS-Mono {@vinsmono}", "Monocular visual-inertial odometry", "Configuration per sequence, not tuned"],
      ["fusion_node_v2 (this work)", "Channels R, T, additional T; safeguards", "Python; settings by environment variables"],
      ["Gazebo {@gazebo} + Husky model", "Farm simulation", "VLP-16, camera and IMU plugins"],
      ["RViz viewer, scoring scripts", "Live display, ATE and maximum error", "Umeyama SE(3), no scale"]],
     [2600, 2800, 2883], dict(align="lll")),
    ("h2", "4.3 Datasets"),
    ("p", "The SubT-MRS sequences {@subtmrs} were recorded with one sensor pack: a Velodyne VLP-16-class LiDAR at 10 Hz, an Epson IMU at "
          "200 Hz and RGB cameras, of which one is used by VINS-Mono. GEODE {@geode} stairs was recorded with its α sensor set. Table 4.2 "
          "lists the sequences and their role in this work; the durations and path lengths are those of the ground-truth files. Figure 4.2 "
          "shows four of them as RViz-style renders of the maps built in the runs, with the ground truth and the fused path."),
    ("tab", "4.2", "Sequences used",
     [["Sequence", "Platform, scene", "Duration, path", "Role"],
      ["Multi Floor (SubT-MRS)", "Legged robot, building with stairs", "417 s, 273 m", "Development (c_{T} chosen here)"],
      ["Long Corridor (SubT-MRS)", "Wheeled robot, long corridor", "279 s, 579 m", "Development (SAH, hand-over)"],
      ["Corridor02 (SubT-MRS)", "Wheeled robot, corridors", "893 s, 695 m", "Development (SAH)"],
      ["Cave02 (SubT-MRS)", "Handheld, cave", "954 s, 475 m", "Held out"],
      ["GEODE stairs (α set)", "Handheld, stairwell", "345 s, 301 m", "Held out"],
      ["Farm L route (Gazebo)", "Husky, agricultural field", "323 s moving, 79 m", "Held out (route)"]],
     [2300, 2550, 1650, 1783], dict(align="llcl")),
    ("fig", FIG + "f4_3_rviz.png", 5.7, "4.2", "RViz-style views: (top) Multi Floor and Long Corridor, F24 live; (bottom) Corridor02, F24 replay, and Cave02, F16 live"),
    ("h2", "4.4 Gazebo farm simulation"),
    ("p", "The farm test uses the Clearpath agriculture world in Gazebo with a Husky robot carrying a VLP-16 LiDAR, a camera and an IMU "
          "(Figure 4.3). A waypoint driver moves the robot along an L-shaped route, (0, 0) to (0, -40) to (-40, -40), at 0.25 m/s. The driver "
          "stops and turns in place whenever the heading error exceeds 0.4 rad, so the route has two turns of about 90°: one at the start and "
          "one at the corner. The ground truth is the Gazebo model pose, logged at about 20 Hz. Each run follows a fixed five-terminal "
          "sequence: Gazebo, the controller switch, A-LOAM, VINS-Mono (initialised by a short wiggle of the robot), and the fusion node; "
          "the robot is then reset to the origin and the driver started once the node is in the fused mode."),
    ("fig", FIG + "f4_3_gazebo_placeholder.png", 4.6, "4.3", "Gazebo agriculture world with the Husky robot"),
    ("h2", "4.5 Run procedure"),
    ("p", "Bags are played at 0.5x (Multi Floor, Long Corridor) or 0.33x (Corridor02) so that A-LOAM and the fusion node keep up on the "
          "laptop. The fusion node writes one log row per scan (fused pose, A-LOAM pose, VINS-Mono pose, weights, Hessian, tensor and "
          "heading values, mode) and stores the keyframe scans, which are used for replays and for the map renders. A batch script runs the "
          "configured number of runs, scores each against the ground truth and collects the files. Failed starts, such as A-LOAM's odometry "
          "process dying at launch or VINS-Mono not initialising, are recorded and reported, not discarded."),
    ("h2", "4.6 Baselines"),
    ("p", "Four baselines are used. VINS-Mono alone is taken from the same live run (the VINS pose in the log), so it shares the conditions "
          "of the fused result. A-LOAM alone was run separately with no VINS input. F8 is the earlier version of this work with channel T "
          "only, and F16 adds the heading read-out; both have several live runs. Switch-SLAM's published front-end results (Table II of "
          "{@switchslam}: Multi Floor 1.61 / 3.63 m, Long Corridor 2.42 / 5.09 m, Farm 0.38 / 1.10 m, RMSE / maximum) are the external targets."),

    # =========================================================== CHAPTER 5
    ("chapter", "5", "Results and Discussion"),
    ("h2", "5.1 Introduction"),
    ("p", "The results are given in the order the method was built. Section 5.2 isolates the effect of each version by replay, Section 5.3 "
          "shows what the channels do inside a run, Sections 5.4 to 5.6 give the live results on the bags and the farm, Section 5.7 the "
          "fault tests, Section 5.8 the held-out sequences and Section 5.9 the comparison with published results. Errors are in metres."),
    ("h2", "5.2 Effect of each version (replay)"),
    ("p", "Table 5.1 replays the 12 development logs (6 Multi Floor, 3 Long Corridor, 3 Corridor02) through each version. Because the "
          "replay is open loop, F24 equals F23 here. The largest single step is the heading read-out: from F8 to F16 the Long Corridor error "
          "fell from 4.53 to 1.98 m. The tensor cap of F20 is neutral on clean data (within 0.03 m of F16). The gmax rule and the VIO check "
          "of F21 improve Corridor02 by 0.14 m. The anchored hand-over lowers the Long Corridor maximum from 5.48 to 3.57 m (F20 to F22) and "
          "from 5.39 to 3.51 m (F21 to F23), and lowers Multi Floor by about 0.05 m."),
    ("tab", "5.1", "Replay of the 12 development logs, mean ATE RMSE / maximum (m)",
     [["Version", "Multi Floor (6)", "Long Corridor (3)", "Corridor02 (3)"],
      ["F8 (channel T only)", "0.626 / 1.33", "4.533 / 12.89", "2.119 / 3.77"],
      ["F16 (T + heading)", "0.560 / 1.06", "1.983 / 5.42", "1.709 / 2.85"],
      ["F20", "0.558 / 1.06", "2.010 / 5.48", "1.710 / 2.87"],
      ["F21", "0.583 / 1.10", "1.970 / 5.39", "1.571 / 2.65"],
      ["F22", "0.506 / 0.99", "1.743 / 3.57", "1.709 / 2.87"],
      ["F23 = F24 (open loop)", "0.531 / 1.03", "1.703 / 3.51", "1.569 / 2.64"],
      ["Switch-SLAM (published)", "1.61 / 3.63", "2.42 / 5.09", "not reported"]],
     [2483, 1900, 1950, 1950], dict(align="lccc")),
    ("fig", FIG + "f5_2_ablation.png", 5.7, "5.1", "Replay ATE (bars) and maximum error (dashes) of each version"),
    ("h2", "5.3 Behaviour of the channels in a corridor"),
    ("p", "Figure 5.2 shows the channels during the first live Long Corridor run of F24. After the 20 s warm-up the largest eigenvalue of "
          "W_{t} stays near 0.9: across the corridor the LiDAR carries the motion. The smallest eigenvalue, along the corridor axis, varies "
          "between 0.5 and 0.85, so VINS-Mono carries up to half of the motion along the axis. The tensor ratio λ'/λ is mostly 1.00 to 1.02 and reaches 1.15 in short stretches where the raw geometry supports more "
          "than the solver claims. The heading read-out accumulates up to about -7° of correction, in steps where distinct wall "
          "structure is seen and flat where it switches itself off."),
    ("fig", FIG + "f3_3_weights.png", 5.2, "5.2", "Channel T weight, tensor ratio and heading correction, Long Corridor, F24 live run 1"),
    ("h2", "5.4 Live results on Multi Floor and Long Corridor"),
    ("p", "Table 5.2 collects every live front-end result on the development sequences. On Multi Floor every version from F20 to F24 is well inside "
          "Switch-SLAM (0.41 to 0.58 m against 1.61 m; maximum 0.82 to 1.20 m against 3.63 m), with one run each for F20 to F24. On Long "
          "Corridor F20 did not reach Switch-SLAM live (mean 2.80 m, maximum up to 8.44 m), although its replay value was 2.01 m. The anchored "
          "versions did: F23 gave 1.75 / 3.02 m and the three F24 runs 2.12, 2.15 and 1.75 m."),
    ("tab", "5.2", "Live front-end results, ATE RMSE / maximum (m); n = number of live runs",
     [["Method", "Multi Floor", "Long Corridor", "Corridor02"],
      ["VINS-Mono alone (F0)", "1.277 / 2.47 (3)", "5.813 / 15.54 (3)", "4.027 / 6.75 (3)"],
      ["A-LOAM alone (F5)", "26.4", "15.8", "66"],
      ["F8", "0.617 / 1.34 (9)", "4.533 / 12.89 (3)", "2.120 / 3.76 (3)"],
      ["F16", "0.640 (6)", "2.27 / 5.38-7.85 (6)", "1.708 (6)"],
      ["F20", "0.478 / 0.82 (1)", "2.796 / 7.13 (3)", "1.753 / 2.80 (3)"],
      ["F21", "0.58 / 1.20 (1)", "not run", "not run"],
      ["F23", "0.41 / 0.91 (1)", "1.75 / 3.02 (1)", "not run"],
      ["**F24 (final)**", "**0.455 / 0.92 (1)**", "**2.007 / 4.80 (3)**", "[[pending live run]]"],
      ["Switch-SLAM (published)", "1.61 / 3.63", "2.42 / 5.09", "not reported"]],
     [2483, 1900, 1950, 1950], dict(align="lccc")),
    ("tab", "5.3", "Long Corridor, F24, three live runs",
     [["Run", "ATE RMSE (m)", "Maximum (m)", "Below 2.42 m", "Below 5.09 m"],
      ["1", "2.12", "5.31", "yes", "no"],
      ["2", "2.15", "5.57", "yes", "no"],
      ["3", "1.75", "3.53", "yes", "yes"],
      ["Mean", "2.007 (sd 0.223)", "4.80", "yes", "no (2 of 3 above)"]],
     [1300, 1800, 1700, 1700, 1783], dict(align="ccccc")),
    ("p", "The pass rule written before these runs required the mean RMSE below 2.42 m and every run's maximum below 5.09 m. The RMSE part "
          "is met; the maximum part is not, by 0.22 and 0.48 m in runs 1 and 2. Figure 5.3 shows the trajectories of the final version on "
          "the four sequences with ground truth."),
    ("fig", FIG + "f5_1_traj.png", 5.5, "5.3", "Top-down trajectories of F24 against ground truth (RMSE in brackets)"),
    ("h2", "5.5 Long Corridor maximum error and the warm-up"),
    ("p", "The maximum error of the Long Corridor runs is not where the fusion acts. In run 1 it occurs at 9.6 s, inside the LiDAR-only "
          "warm-up (Figure 5.4); after 30 s the error stays between 0.8 and 2.3 m. In the first 10 s the direction of travel of A-LOAM is "
          "3.4° off the ground truth, 1.1° at 20 s and 0.5° at 60 s. The start of the run is 135 m from the centroid of the path, and the "
          "full-span alignment pivots about the centroid, so a 2° heading error at the start becomes about 5 m of position error. The "
          "anchored hand-over at 20.6 s took a step of 2.95° and is not involved."),
    ("fig", FIG + "f5_3_lc_err.png", 5.5, "5.4", "Position error over time, Long Corridor, F24 live run 1 (yellow: warm-up)"),
    ("p", "A shorter warm-up was therefore replayed (Table 5.4). It lowers the Long Corridor maximum by 0.5 to 0.65 m and helps Corridor02, "
          "but raises the Multi Floor error by 0.065 to 0.09 m, because VINS-Mono's scale is poorly observed in its first seconds and "
          "joining earlier brings that error in. The gain is also smaller than the live run-to-run spread of Long Corridor (about 1 m), and "
          "replays of this sequence have been optimistic before. The warm-up was not changed."),
    ("tab", "5.4", "Replay with a shorter warm-up (F23 = F24 open loop), mean ATE RMSE / maximum (m)",
     [["T_{warm}", "Multi Floor", "Long Corridor", "Corridor02"],
      ["20 s (final)", "0.531 / 1.03", "1.703 / 3.51", "1.569 / 2.64"],
      ["10 s", "0.596 / 1.02", "1.604 / 2.97", "1.557 / 2.61"],
      ["5 s", "0.623 / 1.04", "1.591 / 2.85", "1.449 / 2.33"]],
     [1983, 2100, 2100, 2100], dict(align="cccc")),
    ("h2", "5.6 Farm simulation"),
    ("p", "Table 5.5 lists every live farm run in the order they were made, one run per version. The pass rule was RMSE ≤ 0.38 m and "
          "maximum ≤ 1.10 m. F20 gave 2.45 m in a run where VINS-Mono alone was 16.2 m: without a VIO-trust check the fused pose followed "
          "the failing VINS. F21 kept the error at 0.50 m with VINS-Mono alone at 3.45 m. F23 had a 5.3 m excursion in the first 18 s after the "
          "reset (Figure 5.5), all of it in the warm-up and VO_FAIL modes, when A-LOAM's odometry jumped 0.4 to 2.5 m per scan; after 20 s "
          "its error was 0.32 m. F24, with the guard on A-LOAM's initial guess, had no start transient and met the maximum bound (0.897 m). "
          "Two things changed between the F23 and F24 runs, the guard and the order of the start-up steps, so this one run cannot say "
          "which removed the transient."),
    ("tab", "5.5", "Farm L route, live runs (one each), ATE RMSE / maximum (m)",
     [["Version", "Fused output", "VINS-Mono alone (same run)", "Rule met"],
      ["A-LOAM alone", "0.478 / 0.977", "-", "max only"],
      ["F8", "0.490 / 0.750", "1.222 / 5.70", "max only"],
      ["F20", "2.448 / 6.087", "16.17 / 52.5", "no"],
      ["F21", "0.496 / 0.995", "3.453 / 16.99", "max only"],
      ["F23", "0.496 / 5.308", "22.23 / 222.5", "no"],
      ["**F24 (final)**", "**0.657 / 0.897**", "2.067 / 3.31", "max only"],
      ["Switch-SLAM (published)", "0.38 / 1.10", "-", "-"]],
     [2283, 2000, 2400, 1600], dict(align="lccc")),
    ("fig", FIG + "f5_4_farm.png", 5.5, "5.5", "Farm position error over time, F23 against F24"),
    ("p", "The RMSE of F24 (0.657 m) is above that of A-LOAM's own output in the same run (0.509 m). The error is a steady offset of 0.6 to "
          "0.8 m, and the fused path ends 0.65 m short. In this run VINS-Mono's path was 9.1 % shorter than A-LOAM's, and the LiDAR carried "
          "73 to 87 % of the translation weight, so the VINS scale error leaks through the remaining share. Rescaling VINS-Mono to the LiDAR "
          "path length was replayed: it lowered the farm error to 0.34 to 0.37 m but raised Corridor02 by 0.58 m. In the corridors the LiDAR "
          "path is 2 to 5 % too long and VINS-Mono is close to right, so the correction pulls a correct VINS toward the LiDAR's error. It was "
          "not adopted; a test of whether the LiDAR path length can be trusted is needed first."),
    ("h2", "5.7 Tests with injected faults"),
    ("p", "Two faults were injected into the logged runs and replayed. In the LiDAR fault (FL) the LiDAR position slides along the weakest "
          "Schur direction at 0.2 m/s for three 20 s windows, while its Hessian is replaced by an isotropic one, so the solver looks "
          "confident and is wrong. In the VIO fault (FV) VINS-Mono is given a scale error. Table 5.6 gives the means. Against the LiDAR fault "
          "the min-rule tensor cap of F20 helped in 12 of 12 logs (sign test p = 0.0005), by 2 to 5 %. The VIO-trust check of F21 removed "
          "most of the VIO fault (Multi Floor 2.35 to 0.71 m, Long Corridor 4.89 to 2.61 m) and cut the GEODE error from 18.3 to 10.6 m, at a cost of "
          "0.2 to 0.6 m under the LiDAR fault."),
    ("tab", "5.6", "Replays with injected faults, mean ATE RMSE (m)",
     [["Cell", "F16", "F20", "F21"],
      ["Multi Floor, LiDAR fault", "3.81", "3.72", "3.89"],
      ["Multi Floor, VIO fault", "2.11", "2.35", "0.71"],
      ["Long Corridor, LiDAR fault", "3.72", "3.62", "4.24"],
      ["Long Corridor, VIO fault", "4.81", "4.89", "2.61"],
      ["Corridor02, LiDAR fault", "4.81", "4.56", "4.88"],
      ["Corridor02, VIO fault", "4.03", "4.02", "3.58"],
      ["GEODE stairs, no fault (A-LOAM alone 10.3)", "17.8", "18.3", "10.60"]],
     [3683, 1500, 1500, 1600], dict(align="lccc")),
    ("h2", "5.8 Held-out sequences"),
    ("p", "Cave02 and GEODE stairs were not used to design any part of the method. Live runs of the final version on them have not been "
          "made yet; the results available are live runs of earlier versions and replays of their logs with the anchored hand-over "
          "(Table 5.7). No keyframe scans of those runs are available, so the tensor and heading channels cannot be replayed there. The "
          "hand-over did no harm on either sequence. Cave02 stays at about 4 m (0.8 % of the path), and GEODE "
          "stairs is a VINS-Mono failure (four VINS losses per run) that the hand-over cannot fix (Figure 5.6)."),
    ("tab", "5.7", "Held-out sequences, ATE RMSE (m)",
     [["Sequence", "Result", "Value"],
      ["Cave02", "VINS-Mono alone, live (3 runs)", "10.25"],
      ["Cave02", "F8 / F16 live (3 runs each)", "4.47 / 4.40"],
      ["Cave02", "F16 logs, replay without / with anchor", "3.975, 5.099, 4.111 / 3.976, 5.077, 4.112"],
      ["Cave02", "**F24 live**", "[[pending]]"],
      ["GEODE stairs", "F16 logs, replay without / with anchor", "20.61, 17.26 / 20.20, 16.74"],
      ["GEODE stairs", "F21 replay (VIO-trust check)", "10.60"],
      ["GEODE stairs", "**F24 live**", "[[pending]]"]],
     [1700, 3283, 3300], dict(align="llc")),
    ("fig", FIG + "f5_6_heldout.png", 5.5, "5.6", "Held-out sequences, earlier version F16 live: (a) Cave02, (b) GEODE stairs"),
    ("h2", "5.9 Comparison with Switch-SLAM and statistical tests"),
    ("p", "Figure 5.7 compares the final version with Switch-SLAM's published front end and with VINS-Mono alone from the same runs. F24 is "
          "below Switch-SLAM in RMSE on Multi Floor (0.455 against 1.61 m, one run) and Long Corridor (2.007 against 2.42 m, three runs), "
          "and below its maximum on Multi Floor and the farm. It is above Switch-SLAM in farm RMSE (0.657 against 0.38 m) and in the "
          "maximum of two Long Corridor runs. The baselines are not identical: our VINS-Mono alone on Multi Floor (1.28 m) is far better "
          "than the 6.30 m listed for VINS-Mono in Switch-SLAM's table, so part of the margin comes from the setup and the evaluation."),
    ("fig", FIG + "f5_5_switch.png", 5.6, "5.7", "F24 against Switch-SLAM (published) and VINS-Mono alone"),
    ("p", "Table 5.8 tests the Long Corridor results with one-sided tests at 95 %. With three runs per group the exact Mann-Whitney test "
          "cannot go below p = 0.05, so the Welch t-test is shown beside it as indicative. F24 is lower than VINS-Mono alone and F8 in every "
          "pair; against F20 the difference (28 %) is not significant (p = 0.10). Against the single published value of 2.42 m a one-sample "
          "t-test gives p = 0.042 for the RMSE, and p = 0.35 for the maximum against 5.09 m."),
    ("tab", "5.8", "Long Corridor, H0: baseline mean = F24 mean, H1: baseline mean > F24 mean",
     [["Baseline (live runs)", "Baseline mean (m)", "F24 lower by", "Welch t, p", "Mann-Whitney, p"],
      ["VINS-Mono alone (5.65, 5.66, 6.13)", "5.813", "65.5 %", "3.3 x 10^{-5}", "0.05"],
      ["F8 (3.97, 4.76, 4.87)", "4.533", "55.7 %", "0.0025", "0.05"],
      ["F20 (3.38, 1.96, 3.05)", "2.796", "28.2 %", "0.10", "0.20"],
      ["Switch-SLAM, 2.42 (one value)", "2.42", "17.1 %", "0.042 (one-sample)", "-"]],
     [2683, 1500, 1300, 1450, 1350], dict(align="lcccc")),
    ("h2", "5.10 Discussion"),
    ("p", "The contribution of each channel is uneven. Channel T is what makes the fusion work at all: F8, with channel T alone, lowered "
          "the Long Corridor error from 5.81 m (VINS-Mono) and 15.8 m (A-LOAM) to 4.53 m. The heading read-out of the additional T channel "
          "gave the largest single gain (4.53 to about 2.0 m on Long Corridor). The tensor rule on S_{tt} is neutral on clean data and "
          "matters only under faults, where the min rule protects against a wrong LiDAR and the max rule, combined with the VIO-trust check, "
          "against a wrong VINS. Channel R never acted on this data. The safeguards of F21 to F24 each removed one observed failure: a VINS "
          "scale failure, a heading step at the hand-over and a start transient on the farm."),
    ("p", "Three limits remain. The number of live runs is small (one to three per cell), and the Long Corridor runs of one configuration "
          "have spread over 1.4 m. The Long Corridor maximum and the farm RMSE are not within Switch-SLAM's values, and the causes are known "
          "but not fixed. Most important, the final version has not yet been run on the held-out Cave02 and GEODE sequences or live on "
          "Corridor02, so its generalisation is not shown."),

    # =========================================================== CHAPTER 6
    ("chapter", "6", "Conclusions"),
    ("p", "A LiDAR-visual-inertial odometry was built on A-LOAM and VINS-Mono in which LiDAR degeneracy is judged in three separate "
          "channels: the Schur rotation block, the Schur translation block and an orientation-tensor channel computed from the raw keyframe "
          "geometry. The channels set per-direction weights between the LiDAR and VIO motion instead of switching between them. Five "
          "versions were tested live on SubT-MRS bags and a Gazebo farm, and F24 was selected as the final version. The main findings are:"),
    ("bul", ["Weighting translation by the Schur block S_{tt} lets the LiDAR carry the well-constrained directions and VINS-Mono the "
             "degenerate one: on Long Corridor the error fell from 5.81 m (VINS-Mono) and 15.8 m (A-LOAM) to 4.53 m with channel T alone.",
             "The heading read-out of the orientation tensor channel gave the largest gain: Long Corridor 4.53 to 1.98 m and Corridor02 2.12 "
             "to 1.71 m in replay.",
             "The tensor rule on S_{tt} changes little on clean data; under an injected confident-but-wrong LiDAR fault the min rule improved "
             "12 of 12 logs, and with the VIO-trust check the max rule cut a VINS scale fault from 2.35 to 0.71 m on Multi Floor.",
             "The anchored hand-over removed the 6 to 7° heading step at the end of the warm-up and lowered the replayed Long Corridor maximum "
             "from 5.48 to 3.57 m.",
             "Without loop closure, F24 gave 0.455 m on Multi Floor and a mean of 2.007 m over three Long Corridor runs, below Switch-SLAM's "
             "1.61 m and 2.42 m, and a farm maximum of 0.897 m, below 1.10 m.",
             "Two of three Long Corridor maxima (5.31 and 5.57 m) exceeded Switch-SLAM's 5.09 m because of a 3° heading error in the "
             "LiDAR-only warm-up, and the farm RMSE (0.657 m) exceeded 0.38 m because VINS-Mono's scale error leaks into the fused motion.",
             "The method has not yet been shown to generalise: the final version still has to be run on Corridor02 and on the held-out "
             "Cave02 and GEODE sequences."]),
    ("h2", "6.1 Future scope"),
    ("p", "The warm-up heading could be anchored to the structure as soon as the LiDAR sees distinct walls, instead of waiting for "
          "VINS-Mono, which would address the Long Corridor maximum without the Multi Floor cost of a shorter warm-up. A test of when the "
          "LiDAR path length can be trusted would allow VINS-Mono's scale to be corrected on open ground without harming corridors. The "
          "rotation check needs a sequence where the VIO rotation fails, to show its value. Replacing A-LOAM by a LiDAR-inertial front end "
          "and adding a loop-closure back end are the obvious extensions, and more live runs per sequence are needed before any difference "
          "smaller than about 0.3 m can be called significant."),
    ("refs",),
]

# ------------------------------------------------------------------ citations: number by first appearance
ORDER = []


def _cite(m):
    keys = [k.strip() for k in m.group(1).split(",")]
    nums = []
    for k in keys:
        if k not in REFDB:
            raise KeyError(k)
        if k not in ORDER:
            ORDER.append(k)
        nums.append(ORDER.index(k) + 1)
    if len(nums) > 2 and nums == list(range(nums[0], nums[-1] + 1)):
        return "[%d]-[%d]" % (nums[0], nums[-1])
    return ", ".join("[%d]" % n for n in nums)


def _walk(x):
    if isinstance(x, str):
        return re.sub(r"\{@([a-z0-9_,\s]+)\}", _cite, x)
    if isinstance(x, list):
        return [_walk(v) for v in x]
    if isinstance(x, tuple):
        return tuple(_walk(v) for v in x)
    if isinstance(x, dict):
        return x
    return x


BODY = [_walk(b) for b in BODY]
REFS = [REFDB[k] for k in ORDER]
FIGS = [(b[3], re.sub(r"\{@.*?\}", "", b[4])) for b in BODY if b[0] == "fig"]
TABS = [(b[1], b[2]) for b in BODY if b[0] == "tab"]


def strip(s):
    return re.sub(r"_\{(.*?)\}|\^\{(.*?)\}", lambda m: m.group(1) or m.group(2), s).replace("**", "")


def toc_entries():
    out = []
    for b in BODY:
        if b[0] == "chapter":
            out.append((1, b[1], b[2]))
        elif b[0] == "h2":
            num, title = b[1].split(" ", 1)
            out.append((2, num, strip(title)))
        elif b[0] == "refs":
            out.append((0, "", "REFERENCES"))
    return out
