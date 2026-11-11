# -*- coding: utf-8 -*-
"""Text of the thesis report, F26 version (Nov 2026). Markup: **bold**, *italic*, _{sub}, ^{sup}, [[highlight]], {@key} citation.
Reference entries come from content.py (REFDB); two are added here."""
import re

_src = open("/home/claude/switchslam-project/docs/thesis/scripts/content.py").read()
exec(_src[:_src.index('T = "\\t"')])

FIG = R + "/rep/fig/"
F3 = R + "/rep/fig3/"
KEEP = R + "/rep/un/word/media/"      # figures taken unchanged from the submitted draft

REFDB["superloc"] = ('S. Zhao, H. Zhu, Y. Gao, B. Kim, Y. Qiu, A. M. Johnson, and S. Scherer, "SuperLoc: The key to robust LiDAR-inertial '
                     'localization lies in predicting alignment risks," in *Proc. IEEE Int. Conf. Robot. Autom. (ICRA)*, 2025, pp. 14080-14086.')
REFDB["otsu"] = ('N. Otsu, "A threshold selection method from gray-level histograms," *IEEE Trans. Syst., Man, Cybern.*, vol. 9, no. 1, '
                 'pp. 62-66, Jan. 1979, doi: 10.1109/TSMC.1979.4310076.')
REFDB["ganesan"] = ('S. Ganesan, B. Ramalingam, and R. E. Mohan, "A hybrid sampling-based RRT* path planning algorithm for autonomous mobile '
                    'robot navigation," *Expert Syst. Appl.*, vol. 258, Art. no. 125206, Dec. 2024, doi: 10.1016/j.eswa.2024.125206.')

FRONT["abstract"] = [
    "Mobile robots that map tunnels, mines and long corridors lose their LiDAR odometry when the scene stops constraining a "
    "direction of motion. In a corridor with smooth walls the motion along the axis is unobserved, and a camera-based estimator "
    "has to carry that direction. Switching methods such as Switch-SLAM choose between LiDAR and visual odometry with one "
    "eigenvalue test on the whole registration Hessian, in which rotation (radians) and translation (metres) share one scale.",
    "This work builds a LiDAR-visual-inertial odometry front end on A-LOAM and VINS-Mono that judges the two parts separately. "
    "The Schur complements of the A-LOAM Hessian give a rotation block (channel R) and a translation block (channel T), and the "
    "translation block sets a per-direction weight between the LiDAR and the VINS-Mono increments. A third channel, the additional T, "
    "is computed from the raw keyframe points: the orientation tensor of the surface normals and edge directions bounds the "
    "translation information direction by direction, and the same normals correct the heading. Versions F20 to F24 added a VINS-Mono "
    "trust check, an anchored hand-over and a guard on A-LOAM's initial guess. The final version, F26, also takes the decision rule of "
    "Switch-SLAM into the LiDAR matching: VINS-Mono's motion seeds A-LOAM's scan-to-map step only when the scan is degenerate.",
    "Without loop closure and with frozen settings, F26 gave an ATE RMSE / maximum error of 0.54 / 1.01 m on the SubT-MRS Multi Floor "
    "sequence and 2.10 / 3.73 m on Long Corridor, against 1.61 / 3.63 m and 2.42 / 5.09 m published for Switch-SLAM, and 0.29 / 0.56 m "
    "on a Gazebo farm route against 0.38 / 1.10 m. On Corridor02 it gave 1.93 and 2.04 m, and on GEODE stairs 3.26 to 6.36 m where "
    "VINS-Mono alone gave 153 to 272 m. On Cave02 it gave 6.23 m, against 4.4 m for an earlier version. With one to three live "
    "runs per sequence, only the GEODE comparison with VINS-Mono alone is significant (p = 0.008), and every sequence was used during "
    "development, so the results are not a held-out test.",
]

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
          "15.8 m on the 579 m SubT-MRS Long Corridor sequence and 66 m on the 695 m Corridor02 sequence, against 0.5 to 2.1 m for the fused "
          "estimates reported later. In the Multi Floor sequence, where a legged robot climbs stairs between floors, A-LOAM alone gave 26.4 m."),
    ("h2", "1.3 Visual-inertial odometry and its failures"),
    ("p", "A monocular VIO such as VINS-Mono {@vinsmono} tracks image features and integrates the IMU between frames. It does not depend on "
          "the geometry of the scene, so it keeps working in a corridor, but its scale is observable only through the accelerometer and it "
          "drifts slowly in heading. It also needs texture and parallax: a pure in-place rotation gives no parallax, and a dark or "
          "featureless wall gives no features. On the sequences of this work VINS-Mono alone gave 1.28 m on Multi Floor, 5.81 m on Long "
          "Corridor, 4.03 m on Corridor02 and 10.25 m on Cave02, and on the GEODE stairs sequence it lost track repeatedly and reached "
          "150 to 270 m. The LiDAR is the better sensor where the geometry is rich, and the VIO is the better sensor along a degenerate direction."),
    ("h2", "1.4 Switching-based LiDAR-visual-inertial fusion"),
    ("p", "Switch-SLAM {@switchslam} runs LiDAR-inertial and visual-inertial odometry side by side and switches the initial pose of the "
          "LiDAR odometry to the visual estimate when it detects LiDAR degeneracy. The detector compares the eigenvalues of the registration "
          "Hessian with a threshold derived from the semicircle law of random matrices. Two features of this design leave room for "
          "improvement. The test is applied to the whole Hessian, in which rotation is measured in radians and translation in metres, "
          "so a rotation problem can be hidden by the larger translation numbers and the reverse. The decision is also all or nothing: "
          "the whole pose comes from one source, although in a corridor only one translation direction is lost and the other five are still "
          "well constrained by the LiDAR. The detector trusts the solver's own Hessian, and a solver that converges to a wrong minimum can "
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
             "To implement the method live in ROS on A-LOAM and VINS-Mono and test it on SubT-MRS and GEODE bags and a Gazebo farm simulation.",
             "To compare it with VINS-Mono alone, A-LOAM alone, earlier versions of the method and the published Switch-SLAM front-end "
             "results, with frozen settings and without loop closure.",
             "To report failures as well as successes, with pass rules written before each live test and every run counted."]),

    # =========================================================== CHAPTER 2
    ("chapter", "2", "Literature Review"),
    ("h2", "2.1 Introduction"),
    ("p", "This chapter reviews how degeneracy has been detected from the registration Hessian, how rotation and translation have been "
          "separated, how surface-normal statistics have been used as a geometry-based measure, and how LiDAR, visual and inertial odometry "
          "have been combined in degenerate scenes."),
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
          "hide degeneracy. The orientation tensor as a solver-independent degeneracy measure is therefore prior art; LF-GICP is LiDAR-only and "
          "does not use the tensor to correct heading."),
    ("h2", "2.5 LiDAR-visual-inertial fusion in degenerate scenes"),
    ("p", "Tightly coupled LiDAR-inertial odometries such as LIO-SAM {@liosam} and FAST-LIO2 {@fastlio2} use the IMU to bridge short "
          "degenerate stretches, but do not use a camera. LVI-SAM {@lvisam} couples a visual-inertial and a LiDAR-inertial subsystem; the "
          "visual system gives the initial guess of the LiDAR scan matching, and the LiDAR depth helps the visual features. RELEAD {@relead} "
          "constrains the LiDAR optimisation in non-localizable directions and fuses it with VIO in a graph. ORB-SLAM3 {@orbslam3} is a feature-based "
          "visual-inertial SLAM with maps and relocalisation, but it has no LiDAR. Switch-SLAM {@switchslam}, described in Section 1.4, is "
          "the closest system to this work. Its status rule (Section 3.8) is reused in the final version, and its published results "
          "(Table II of that paper, without loop closure) are the targets used in Chapter 5."),
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
     [2350, 3000, 2933], dict(align="lll")),
    ("h2", "2.7 Summary"),
    ("p", "Three points come out of the review. Rotation and translation degeneracy have different causes and units and are better judged "
          "separately, and the Schur complement is a clean way to do it {@dcreg}. The methods that separate them work on the LiDAR alone and "
          "rely on the solver's own Hessian. The fusion systems that add a camera {@switchslam,lvisam} switch the whole pose or the initial "
          "guess and do not weight directions. No system found in this review combines Schur-separated channels with an independent check "
          "from the raw geometry inside a LiDAR-visual-inertial fusion. That combination is the subject of this work."),

    # =========================================================== CHAPTER 3
    ("chapter", "3", "Methodology"),
    ("h2", "3.1 Introduction"),
    ("p", "The work was done in the order of Figure 3.1. After a first-generation switching node and a study of 15 detection rules (Section 5.2), the fusion channels were designed and their constants frozen on recorded runs. Live runs then exposed failures that replays had not shown; each was fixed by a small, testable change (F20 to F24), and F26 changed only A-LOAM's initial guess. Every live test had a pass rule written before it was run, and every run is reported."),
    ("fig", F3 + "f3_1_flow.png", 4.0, "3.1", "Flowchart of methodology"),
    ("h2", "3.2 System overview"),
    ("p", "The fusion is VIO-primary (Figure 3.2). For every LiDAR scan the fusion node receives the A-LOAM scan-to-map pose and its "
          "Hessian, and the VINS-Mono pose at the same time. It forms the LiDAR increment (rotation vector φ_{L}, translation Δt_{L}) and the "
          "VINS increment (φ_{V}, Δt_{V}) since the previous scan and blends them with two 3 x 3 weights:"),
    ("eq", "φ = W_{R} φ_{L} + (I - W_{R}) φ_{V}", "3.1"),
    ("eq", "Δt = W_{t} Δt_{L} + (I - W_{t}) Δt_{V}", "3.2"),
    ("p", "The fused pose is the previous fused pose composed with this increment. W = 0 means the VIO carries a direction, W = I means the "
          "LiDAR carries it. For the first 20 s after VINS-Mono starts (T_{warm}) the output is LiDAR only, because a monocular VIO needs "
          "time to settle its scale; the same warm-up is repeated after VINS-Mono is lost (mode VO_FAIL: no message, a jump above 1 m or "
          "0.5 rad, or a restart). The loop is closed: the fused pose, moved forward by a step chosen as in Section 3.8, is A-LOAM's "
          "initial guess for the next scan."),
    ("fig", F3 + "f3_2_arch.png", 5.4, "3.2", "Structure of the fusion: channels R, T, the additional T and the scan-to-map guess"),
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
    ("p", 'With A-LOAM the VINS-Mono rotation was better than the LiDAR rotation on most sequences: an active rotation weight (c_{R} > 0) improved Long Corridor in early replays, while on Multi Floor, Corridor02 and Cave02 the VIO rotation gave the lower error, and an open-loop replay of the F26 logs with c_{R} from 10^{-5} to 3 x 10^{-3} gave Cave02 2.4 m higher at every setting (Table 5.11). In normal operation c_{R} = 0, the rotation comes from the VIO and S_{RR} is monitored. A rotation check compares the VIO and LiDAR rotations over 2 s and 10 s windows; when they disagree by more than 0.402 rad and 0.585 rad (the largest values on 19 Multi Floor recordings), the LiDAR rotation carries the step with W_{R} = (S_{RR} + 10^{-3} I)^{-1} S_{RR}. The check closed on no fused scan of four sequences and on 3.6 % of those of GEODE, so it acts as a safeguard for strong disagreement.'),
    ("h2", "3.6 Additional T channel: the orientation tensor"),
    ("h3", "3.6.1 Tensor from the keyframe scan"),
    ("p", "For each LiDAR keyframe the 12 nearest neighbours of every point are found and their covariance is decomposed (eigenvalues "
          "λ_{1} ≤ λ_{2} ≤ λ_{3}). A point is planar when (λ_{2} - λ_{1})/λ_{3} > 0.5, with normal n, and linear when (λ_{3} - λ_{2})/λ_{3} > 0.5, "
          "with direction d. A plane constrains translation along its normal; an edge constrains translation in the plane perpendicular to "
          "its direction. The geometric orientation tensor counts both:"),
    ("eq", "G = ( Σ_{planar} n n^{T} + ½ Σ_{linear} (I - d d^{T}) ) / (n_{p} + n_{l})", "3.7"),
    ("p", "G has trace 1 and uses no correspondences, no solver state and no threshold. Between keyframes it is rotated into the current "
          "LiDAR frame. Planar normals alone understate the support that A-LOAM has "
          "from edge features such as door frames and pipes, so edge directions are included; rules built on planar normals alone gave corridor errors 0.26 to 1.0 m higher in replay."),
    ("h3", "3.6.2 Combining the tensor with S_{tt}"),
    ("p", "The tensor is scaled to the same total information as the solver, B = tr(H_{tt}) G, and combined with A = S_{tt} by a basis-free "
          "matrix rule. Several rules were compared by replay on clean data and under injected faults (Section 5.9). The final version uses "
          "the generalised maximum:"),
    ("eq", "S'_{tt} = B^{½} max(M, I) B^{½},   M = B^{-½} A B^{-½}", "3.8"),
    ("p", "where max(M, I) raises every generalised eigenvalue below 1 to 1. Along each direction the combined information is the larger "
          "of what the solver and the raw geometry support, and S'_{tt} replaces S_{tt} in Equation 3.6. F20 used the opposite rule (the "
          "minimum, a fail-safe cap). The maximum was chosen in a pre-registered comparison because it scored best over the clean and "
          "fault cells and on a farm bag that the comparison had not used; protection against a solver that is confident but wrong "
          "comes from the VIO-trust check of Section 3.7."),
    ("h3", "3.6.3 Heading from the same normals"),
    ("p", 'The second read-out of the normals corrects heading, which VINS-Mono cannot observe and which dominates the error in long corridors. The near-vertical planar normals of a keyframe are levelled with the VIO gravity direction, and their horizontal directions form an axial histogram h(θ) (0.5° bins over 180°). The heading error is the shift, searched over ±15°, that best aligns h(θ) with a reference histogram learned in the world frame; it passes through a Kalman update and is applied at no more than 0.25° per scan. It switches itself off when the structure is not distinct (a null-model test against random directions, a unique correlation peak, a chi-square gate and a drift gate). This structure-anchored heading (SAH) depends on the even-order orientation tensors of the same normals; the fourth order matters, because with two equally strong perpendicular wall families the second-order tensor is isotropic and carries no heading information.'),
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
          "A-LOAM's odometry followed them. In F24 a VINS step counts as usable for the guess only when the previous mode was not VO_FAIL and "
          "the step is within the jump limits (1 m, 0.5 rad). The fused output itself is unchanged by this rule."),
    ("h2", "3.8 Scan-to-map guess from the degeneracy status (F26)"),
    ("p", "Up to F24 the guess for A-LOAM's scan-to-map matching was the last fused pose moved by the VINS-Mono step wherever that step was usable, and the last fused pose with no motion otherwise. On Cave02 and GEODE the no-motion guess was used on 13.5 % and 78 % of the scans, while VINS-Mono was starting or failing, and where the scan is well constrained the VINS step only adds VINS-Mono's noise to a match that does not need it."),
    ("p", "F26 chooses the guess with the status rule of Switch-SLAM {@switchslam}. The six eigenvalues of H are computed and the three "
          "smallest, scaled to unit length, are compared with the published thresholds [0.12, 0.27, 0.48]; the scan is degenerate if any of "
          "them is below its threshold. The flags of the last five scans form a status queue. With Δ_{L} the A-LOAM scan-to-scan increment "
          "and Δ_{V} the VINS-Mono increment, the step added to the last fused pose is"),
    ("eq", "Δ_{g} = Δ_{L} (none flagged),   w Δ_{L} + (1 - w) Δ_{V} (mixed),   Δ_{V} (all flagged)", "3.10"),
    ("p", "with w = min(1, √3 λ̄_{1}) from the smallest scaled eigenvalue (Eq. 13 of Switch-SLAM). A VINS step that fails the F24 guard counts as absent. Only A-LOAM's starting point changes; the output is still the fusion of Equations 3.1 and 3.2. The output is not switched or remapped as in Switch-SLAM: that structure, with A-LOAM's pose as the output and our channels as the detector, was tested as F30 to F34; the weighted fusion was lower on every sequence they were run on (Table 5.11)."),
    ("p", 'A variant, F35, drives the same queue with channels R, T and the additional T instead of the published thresholds. It put the VINS step into the guess on 73 % of the Long Corridor scans (F26: 2 %). On the four sequences with runs the reading rule written beforehand gave no change against F26: Corridor02 was higher (2.82 against 1.99 m) and the others were inconclusive. F26 remains the final version.'),
    ("h2", "3.9 Configurations and the choice of the final version"),
    ("p", 'Each configuration is a set of environment variables passed to the fusion node; Table 3.1 lists those referred to in this report. No constant was fitted to a test sequence after F20; the new constants of F21 come from Multi Floor, F22 to F24 add none, and the thresholds of F26 are the published ones.'),
    ("tab", "3.1", "Configurations used in this work",
     [["Config", "Settings", "Purpose"],
      ["F0", "VINS-Mono only", "Visual-inertial control"],
      ["F1 / F2", "c_{T} 0.003, κ gate 15.7 / Otsu {@otsu}", "First gated method"],
      ["F3", "c_{T} 0.003, no gate", "Gate ablation"],
      ["F4 / F5", "LiDAR only, with / without VINS prediction", "LiDAR baselines"],
      ["F7 to F10", "c_{T} 0.01 / 0.03 / 0.1 / 0.3, no gate", "Weight sweep; F8 = channel T"],
      ["F11 / F13 / F15", "Isotropic / per-direction 0-1 / diagonal H_{tt}", "Weighting ablation"],
      ["F12", "Hard switch with the Switch-SLAM rule", "Switching baseline"],
      ["F14", "W = I (LiDAR translation always)", "LiDAR-translation baseline"],
      ["F16", "F8 + SAH", "Channel T and heading"],
      ["F20", "F16 + Schur R, rotation check, OT min rule", "R, T and additional T"],
      ["F21", "OT gmax rule; VIO-trust check; LiDAR guard", "VINS scale failures"],
      ["F22 / F23", "F20 / F21 + anchored hand-over", "Heading step at hand-over"],
      ["F24", "F23 + mapping-guess guard", "Farm start transient"],
      ["F25A", "F24, no hand-over while VINS is distrusted", "Not adopted"],
      ["**F26**", "**F24 + guess from the degeneracy status**", "**Final configuration**"],
      ["F27", "F24 + A-LOAM step instead of no motion", "Not adopted"],
      ["F30 to F34", "Switch-SLAM structure with our channels", "Not adopted"],
      ["F35", "F26 with the status from our channels", "No change shown against F26"],
      ["SW / SWI", "Switch-SLAM in this stack (SWI: gyro prior)", "Reproduction attempt"]],
     [1500, 4283, 2500], dict(align="cll", size=20)),
    ("p", "**F26 is chosen as the final version.** It keeps all three channels and every safeguard of F24 and changes only A-LOAM's starting point. Against F24 it was lower on GEODE, Cave02 and the farm, level on Multi Floor and Long Corridor and higher on Corridor02, each from one to four runs (Section 5.5). Its constants are listed in Table 3.2."),
    ("tab", "3.2", "Frozen constants of the final version F26",
     [["Constant", "Value", "Source"],
      ["c_{T} (translation information scale)", "0.03", "Multi Floor, once"],
      ["c_{R} (rotation, normal operation)", "0", "Replay: the VIO rotation gave the lower error with A-LOAM"],
      ["Warm-up T_{warm}", "20 s", "Design value"],
      ["Jump limits", "1 m, 0.5 rad", "Design value"],
      ["Rotation check references", "0.402 rad / 2 s, 0.585 rad / 10 s", "Largest on 19 Multi Floor recordings"],
      ["VIO-trust references", "0.157 (10 s), 0.277 (5 s)", "Largest on six Multi Floor replays"],
      ["LiDAR guard", "4.325 m over 2 s", "Six Multi Floor replays"],
      ["Tensor k-NN, planarity / linearity", "12, 0.5 / 0.5", "Shared with SAH"],
      ["SAH search, step limit", "±15°, 0.25° per scan", "Developed on Long Corridor and Corridor02"],
      ["Status thresholds, queue", "0.12, 0.27, 0.48; 5 scans", "Published values of Switch-SLAM"],
      ["Guess blend weight w", "min(1, √3 λ̄_{1})", "Switch-SLAM, Eq. 13"]],
     [3000, 2483, 2800], dict(align="lll")),
    ("h2", "3.10 Evaluation metrics and protocol"),
    ("p", "The accuracy measure is the absolute trajectory error {@sturm}. The estimated positions p_{i} are aligned to the ground truth g_{i} "
          "by the rigid transformation (R, t) that minimises the squared error, without scale (Umeyama {@umeyama}), over the full span of "
          "the run, and"),
    ("eq", "ATE = ( (1/N) Σ_{i} || R p_{i} + t - g_{i} ||^{2} )^{½}", "3.11"),
    ("p", 'The maximum of ||R p_{i} + t - g_{i}|| is reported beside it, as in Switch-SLAM, and all results are front end only, without loop closure. A replay feeds the logged A-LOAM and VINS-Mono poses of a run through the real fusion node; it is exact for the fusion but open loop, because A-LOAM is not re-seeded. Only live runs are compared with published numbers, and differences below max(0.1 m, 10 %) are treated as ties.'),
    ("p", 'The statistics follow Ganesan et al. {@ganesan}: minimum, median, maximum and mean per environment, a success rate (here a run with ATE ≤ 10 m), and a one-sided test of H_{0}: M(baseline) = M(proposed) against H_{1}: M(baseline) > M(proposed) at 95 %, here the exact Mann-Whitney U test on separate live runs, with the Welch t-test beside it where both groups have two or more runs. With n_{1} and n_{2} runs the exact test cannot go below p = 1 / C(n_{1} + n_{2}, n_{2}). Cave02 and GEODE were first held out, but the F24 results on them led to F25 to F27, so all six sequences are development data for F26.'),

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
          "live in RViz. roscore is restarted for every run so that no state carries over. The laptop has a Ryzen 5 5600H CPU, an Nvidia "
          "GTX 1650 GPU with 4 GB of video memory and 16 GB of RAM."),
    ("fig", KEEP + "image4.png", 5.2, "4.1", "Layout of the experimental setup"),
    ("tab", "4.1", "Software components",
     [["Component", "Role", "Notes"],
      ["ROS Noetic, Docker", "Middleware, isolation", "One container per subsystem"],
      ["A-LOAM {@aloam}", "LiDAR scan-to-map odometry", "Publishes pose and 6 x 6 Hessian; initial guess from the fusion"],
      ["VINS-Mono {@vinsmono}", "Monocular visual-inertial odometry", "Configuration per sequence, not tuned"],
      ["fusion_node_v2 (this work)", "Channels R, T, additional T; safeguards; status guess", "Python; settings by environment variables"],
      ["Gazebo {@gazebo} + Husky model", "Farm simulation", "VLP-16, camera and IMU plugins"],
      ["RViz viewer, scoring scripts", "Live display, ATE and maximum error", "Umeyama SE(3), no scale"]],
     [2600, 2800, 2883], dict(align="lll")),
    ("h2", "4.3 Datasets"),
    ("p", 'Five real sequences and one simulated route were used (Table 4.2, Figure 4.2): four from SubT-MRS {@subtmrs}, recorded at Carnegie Mellon University and in the Laurel Caverns, and one from GEODE {@geode}, all with a 16-beam Velodyne LiDAR at 10 Hz, a camera and an IMU.'),
    ("tab", "4.2", "Sequences used in this work",
     [["Sequence", "Platform", "Duration / path", "LiDAR, camera, IMU topics", "Ground truth", "Role"],
      ["SubT-MRS Multi Floor (Floor01)", "Legged robot, building with stairs", "3 bags, 417 s, 273 m", "/velodyne_packets (converted), camera, /imu/data",
       "ground_truth_path.csv", "Calibration of c_{T} and the safeguard constants"],
      ["SubT-MRS Long Corridor (Corridor01)", "Wheeled RC car", "279 s, 579 m, loop (start-end 3.3 m)", "/velodyne_packets (converted), /camera_1/image_raw (24 Hz), /imu/data",
       "corridor01_gt.txt, 1,385 poses at 5 Hz", "Development (SAH, hand-over)"],
      ["SubT-MRS Corridor02 (RC1)", "Wheeled RC car", "893 s, 695 m; stationary for 70 s", "/velodyne_points, /camera_1/image_raw, /imu/data",
       "corridor02_gt.txt", "First held out for F8; development for SAH"],
      ["SubT-MRS Cave02 (Laurel Caverns)", "Handheld", "956 s, 475 m; stationary for 45 s", "/velodyne_points (9,471 scans), /camera_1/image_raw, /imu/data",
       "cave02_gt.txt, 4,731 poses at 5 Hz", "Control for SAH; development for F25 to F27"],
      ["GEODE stairs, device α", "Handheld, stairwell", "345 s, 301 m; 3,456 scans", "/velodyne_points (VLP-16), /imu/data (100 Hz), stereo images at 10 Hz",
       "stairs_alpha.txt, 3,447 poses", "First test of F24; development for F25 to F27"],
      ["Farm L route (Gazebo)", "Husky robot, field", "323 s moving, 79 to 81 m", "/velodyne_points (VLP-16), RGB 640 x 480 at 60 Hz, /imu/data (200 Hz)",
       "Gazebo model pose, 20 Hz", "Development (F24 guard); F26 run"]],
     [1300, 1050, 1250, 1983, 1300, 1400], dict(align="llllll", size=19)),
    ("fig", F3 + "f4_gt.png", 4.3, "4.2", "Ground-truth trajectories of the five real sequences (top view)"),
    ("p", 'The SubT-MRS ground truth was obtained by registering the LiDAR against a survey map together with the platform odometry, so it is not fully independent of the sensors being tested and is weakest where the LiDAR degenerates; on Corridor02 its heading jumps by several degrees at some times, so only the position error is reliable there. The GEODE ground truth was obtained against a terrestrial laser scan. The residual time offsets between bag and ground truth were 0.03 s (Corridor02) and 0.04 s (Long Corridor). Figure 4.3 shows four sequences as RViz-style renders of the maps built in the runs.'),
    ("fig", KEEP + "image5.png", 4.5, "4.3", "RViz-style views: (top) Multi Floor and Long Corridor, F24 live; (bottom) Corridor02, F24 replay, and Cave02, F16 live"),
    ("h2", "4.4 Gazebo farm simulation"),
    ("p", "The farm test uses the Clearpath agriculture world in Gazebo with a Husky robot carrying a VLP-16 LiDAR (10 Hz), an RGB camera (640 x 480, 60 Hz) and an IMU (200 Hz), the sensor set given for the simulated robot of Switch-SLAM (Figure 4.4). A waypoint driver moves the robot along an L-shaped route, (0, 0) to (0, -40) to (-40, -40), at 0.25 m/s, turning in place at the start and at the corner. The ground truth is the Gazebo model pose. After Gazebo, A-LOAM, VINS-Mono (initialised by a short wiggle) and the fusion node are started, the robot is reset to the origin and the driver starts once the node is fused. The early runs used a camera looking to the robot's right; the F24 and F26 runs of Section 5.8 used the same camera facing forward."),
    ("fig", KEEP + "image6.png", 3.0, "4.4", "Gazebo agriculture world with the Husky robot"),
    ("h2", "4.5 Replay rate and acceptance of runs"),
    ("p", 'A replay can lose scans if the computer cannot process them in real time, so the replay rate was lowered where needed, chosen from the row counts alone before any error was seen, and runs were accepted only if they contained enough scans (Table 4.3). The fusion node writes one log row per scan (fused, A-LOAM and VINS-Mono poses, weights, Hessian, tensor and heading values, guess kind, mode) and stores the keyframe scans for replays and map renders. Failed starts and diverged runs are reported, not discarded.'),
    ("tab", "4.3", "Replay rates and scans logged per run",
     [["Period", "Sequence", "Rate", "Scans per run (ideal)", "Note"],
      ["13-14 Oct", "Multi Floor", "1.0x", "3,100-3,400 (about 4,170)", "About 20-25 % of scans skipped; all F0-F10 results at this rate"],
      ["15 Oct", "Long Corridor", "1.0x", "2,758-2,774 (about 2,777)", "Complete"],
      ["16 Oct", "Corridor02, attempt 1", "1.0x", "4,628-5,554 (about 8,900)", "About 40 % skipped; all 8 runs discarded before scoring"],
      ["16-17 Oct", "Corridor02", "0.33x", "8,191-8,282", "Used for all later Corridor02 results"],
      ["17-19 Oct", "F16 on Long Corridor / Multi Floor / Corridor02", "0.5x / 0.5x / 0.33x", "2,775 / 4,082-4,110 / 8,265-8,355", "Heading worker never skips a keyframe"],
      ["19-20 Oct", "Cave02", "0.5x", "9,441-9,454", "Complete"],
      ["29 Oct-10 Nov", "F20 to F35 on Multi Floor / Long Corridor / Corridor02", "0.5x / 0.5x / 0.33x", "4,086 / 2,776 / 8,391-8,418", "Complete (F26 counts)"],
      ["4-10 Nov", "F24 to F27 on Cave02 / GEODE", "0.5x / 0.5x", "9,452 / 3,307-3,353", "Complete; GEODE at 0.25x gave no gain"]],
     [1100, 2283, 1250, 1750, 1900], dict(align="lllll", size=19)),
    ("h2", "4.6 Baselines"),
    ("p", "The baselines are VINS-Mono alone (F0 runs; on GEODE and the farm, the VINS-Mono output logged in the fused runs, which is valid because VINS-Mono takes no input from the fusion), A-LOAM alone (F5), F8 (channel T only) and F24. Switch-SLAM's published front-end results {@switchslam} (Multi Floor 1.61 / 3.63 m, Long Corridor 2.42 / 5.09 m, Farm 0.38 / 1.10 m, RMSE / maximum) are the external targets; an implementation of Switch-SLAM in this stack did not reproduce them (Table 5.11)."),

    # =========================================================== CHAPTER 5
    ("chapter", "5", "Results and Discussion"),
    ("h2", "5.1 Introduction"),
    ("p", "This chapter reports the tests in the order they were made, followed by the final results and the comparison with published "
          "work. Table 5.1 gives an overview. Section 5.2 covers the first-generation switching node, Sections 5.3 to 5.5 the effect of each "
          "version and what the channels and the guess rule do inside a run, Sections 5.6 to 5.10 the live results of the final version, "
          "Section 5.11 the statistical tests, Section 5.12 the comparison with published values and the other tests, and Section "
          "5.13 the discussion. "
          "Unless stated otherwise, every value is the full-span ATE RMSE in metres with rigid SE(3) alignment and no scale."),
    ("tab", "5.1", "Overview of the test phases",
     [["Phase", "Date (2026)", "Test", "Kind", "Scale"],
      ["1", "before 5 Oct", "Old detector checks, Gazebo log", "Synthetic + simulation", "400-800 trials; 4,017 frames"],
      ["2", "5 Oct", "Verification of the redesign (S1-S7)", "Synthetic ICP Monte Carlo", "5 seeds, 200-4,000 runs per check"],
      ["3", "5 Oct", "Old vs new pipeline, 2 x 2 x 2 factorial", "Synthetic 30 m drive", "5 scenarios x 5 seeds x 8 pipelines"],
      ["4", "6 Oct", "Channel T statistics", "Real log + simulation", "3,932 frames; 1,500-3,000 repetitions"],
      ["5-6", "12-13 Oct", "Old node reference; 15 detection rules", "Live ROS", "3 + 15 runs"],
      ["7-8", "13-14 Oct", "Fusion node: offline evidence, F0-F5, c_{T} sweep", "Replay + live", "40 runs"],
      ["9-10", "14 Oct", "Loop closure; weighting ablation", "Offline", "11 recordings; 12 logs x 9 rules"],
      ["11", "15 Oct", "Long Corridor", "Live + replay", "15 runs"],
      ["12", "15-17 Oct", "Corridor02 test", "Live + replay", "17 scored runs"],
      ["13-14", "17 Oct", "Yaw-drift diagnosis; SAH development", "Replay with ground truth", "12 logs x 7 versions"],
      ["15-18", "17-19 Oct", "SAH live (F16), six runs per sequence, back end", "Live + offline", "21 runs; 18 back-end runs"],
      ["19", "19-20 Oct", "Cave02 control", "Live", "9 runs"],
      ["20-21", "20-21 Oct", "Improvement replays; statistical tests", "Offline", "Replays of the F8 and F16 logs"],
      ["22", "25-29 Oct", "Orientation-tensor channel; injected faults; F20", "Replay + live", "12 logs per rule; F20 live on four sequences"],
      ["23", "29 Oct-3 Nov", "F21 to F24: VIO-trust check, hand-over, guess guard", "Replay + live", "Multi Floor, Long Corridor, farm"],
      ["24", "3-5 Nov", "F24 on all sequences; Switch-SLAM in this stack", "Live", "20 F24 runs (with phase 26)"],
      ["25", "4-7 Nov", "F25 to F27: guess rules; forward-camera farm rig", "Live", "F25A 2, F26 6, F27 2 runs"],
      ["26", "10 Nov", "F26 and F27 repeats; F30 to F35; c_{R} replay", "Live + replay", "F26 3 and F27 2 more; F30 to F35 15 runs; 56 replays"]],
     [800, 1200, 3083, 1500, 1700], dict(align="cclll", size=19)),
    ("h2", "5.2 First-generation switching node and the threshold study"),
    ("p", 'The old switching node gave 1.39 ± 0.14 m on Multi Floor over three runs, against 1.32 m for VINS-Mono alone. Its logs showed three faults: the LiDAR-only mode used scan-to-scan odometry instead of the scan-to-map result, the VINS and LiDAR world frames (8 to 62° apart) were mixed without a rotation, and the largest error came from the VINS start-up transient.'),
    ("p", "Fifteen detection rules were then run live, one run each, with only the rule changed in the node (Table 5.2). The labels were the "
          "A-LOAM drift terciles in 8 s windows on bags 1 and 2 of Multi Floor, which none of the detectors can see, and each rule was scored "
          "by Youden's index J = TPR - FPR. An offline screen had predicted J for every rule beforehand, and 13 of the 15 predictions were "
          "within 0.05."),
    ("tab", "5.2", "Threshold study on Multi Floor (one live run per rule)",
     [["Rule", "Description", "ATE (m)", "Flagged", "TPR", "FPR", "J"],
      ["A1", "Switch-SLAM semicircle", "3.05", "0.891", "0.907", "0.884", "0.023"],
      ["A2", "κ(S) > 10 (DCReg)", "12.49", "0.551", "0.742", "0.495", "0.247"],
      ["A3", "κ(S) > 50", "15.98", "0.029", "0.061", "0.019", "0.042"],
      ["A4", "Diagonal κ > 10", "13.70", "0.559", "0.734", "0.479", "0.255"],
      ["A5", "λ_{min}(S) < 100", "10.88", "0.741", "0.969", "0.803", "0.166"],
      ["A6", "Never flag", "17.67", "0.000", "0.000", "0.000", "0.000"],
      ["A7", "κ(H) > 10", "1.38", "0.979", "0.970", "0.992", "-0.022"],
      ["A8", "κ(S_{RR}) > 15.7 (Otsu)", "16.27", "0.334", "0.584", "0.105", "0.479"],
      ["B1", "λ_{min}(T) < 0.15 (old channel T)", "7.50", "0.838", "0.973", "0.858", "0.115"],
      ["B2", "κ(T) > 10", "14.66", "0.575", "0.717", "0.562", "0.155"],
      ["B3", "λ_{min}(T) ≤ 0.045", "16.12", "0.245", "0.293", "0.307", "-0.014"],
      ["B4", "Woodcock K < 1", "3.26", "0.823", "0.803", "0.885", "-0.082"],
      ["B5", "Demantke class", "11.97", "0.725", "0.894", "0.630", "0.264"],
      ["C1", "A2 or B3", "10.80", "0.658", "0.751", "0.599", "0.152"],
      ["C2", "A2 or B2", "8.39", "0.739", "0.847", "0.735", "0.112"]],
     [700, 2783, 900, 1000, 950, 950, 1000], dict(align="clccccc", size=20)),
    ("p", "The best detector was A8, the condition number of the rotational Schur block with a threshold found by Otsu's method {@otsu} "
          "(J = 0.479, precision 0.817). The old channel T was checked against a rule set before the runs, which required it to add at least 0.05 to J: "
          "combined with the Schur test it gave J of 0.152 (C1) and 0.112 (C2) against 0.247 for A2. The more important finding is shown in "
          "Figure 5.1. The ATE did not follow the detection quality; it followed the share of time in which control was handed to "
          "VINS-Mono (Spearman correlation -0.95). Rules that flag almost everything (A7) give a low error because they use VINS-Mono most "
          "of the time, and the lowest error on this sequence came from VINS-Mono alone. On this sequence a switching system cannot be judged by how well it detects "
          "degeneracy, and switching throws away LiDAR translation that is still good. This result led directly to the per-direction "
          "weighting of Chapter 3."),
    ("fig", F3 + "f5_rules.png", 4.2, "5.1", "Detection quality against trajectory error for the 15 rules"),
    ("h2", "5.3 Effect of each version (replay)"),
    ("p", "Table 5.3 replays the 12 development logs (6 Multi Floor, 3 Long Corridor, 3 Corridor02) through each version. Because the "
          "replay is open loop, F24 equals F23 here, and F26, which changes only A-LOAM's starting point, cannot be replayed at all. The "
          "largest single step is the heading read-out: from F8 to F16 the Long Corridor error fell from 4.53 to 1.98 m. The tensor cap of "
          "F20 is neutral on clean data (within 0.03 m of F16). The gmax rule and the VIO check of F21 improve Corridor02 by 0.14 m. The "
          "anchored hand-over lowers the Long Corridor maximum from 5.48 to 3.57 m (F20 to F22) and from 5.39 to 3.51 m (F21 to F23), and "
          "lowers Multi Floor by about 0.05 m."),
    ("tab", "5.3", "Replay of the 12 development logs, mean ATE RMSE / maximum (m)",
     [["Version", "Multi Floor (6)", "Long Corridor (3)", "Corridor02 (3)"],
      ["F8 (channel T only)", "0.626 / 1.33", "4.533 / 12.89", "2.119 / 3.77"],
      ["F16 (T + heading)", "0.560 / 1.06", "1.983 / 5.42", "1.709 / 2.85"],
      ["F20", "0.558 / 1.06", "2.010 / 5.48", "1.710 / 2.87"],
      ["F21", "0.583 / 1.10", "1.970 / 5.39", "1.571 / 2.65"],
      ["F22", "0.506 / 0.99", "1.743 / 3.57", "1.709 / 2.87"],
      ["F23 = F24 (open loop)", "0.531 / 1.03", "1.703 / 3.51", "1.569 / 2.64"],
      ["Switch-SLAM (published)", "1.61 / 3.63", "2.42 / 5.09", "not reported"]],
     [2483, 1900, 1950, 1950], dict(align="lccc")),
    ("h2", "5.4 Behaviour of the channels in a corridor"),
    ("p", "Figure 5.2 shows the channels during the live Long Corridor run of F26. After the 20 s warm-up the largest eigenvalue of W_{t} "
          "stays near 0.9 (median 0.91): across the corridor the LiDAR carries the motion. The smallest eigenvalue, along the corridor axis, "
          "has a median of 0.69, so VINS-Mono carries about a third of the motion along the axis and more in the weakest stretches. The "
          "tensor ratio λ'/λ has a median of 1.003 and a 95th percentile of 1.07, so the raw geometry rarely claims more than the solver. "
          "The heading read-out accumulates up to -4.7° of correction, in steps where distinct wall structure is seen and flat where it "
          "switches itself off."),
    ("fig", F3 + "f5_weights.png", 4.2, "5.2", "Channel T weight, tensor ratio and heading correction, Long Corridor, F26 live run"),
    ("h2", "5.5 What the status rule puts into the guess"),
    ("p", "Table 5.4 counts the guess kinds in the F26 logs. On the five real sequences the published thresholds flag few scans, so the guess "
          "is A-LOAM's own scan-to-scan step on 94 to 100 % of them, and on Cave02 on every scan. F26 is therefore close to F24 with A-LOAM's "
          "usual guess. The farm route is the exception: the rule flagged the last 25 m of the L and the standing time at the end, and the "
          "VINS step was used on 32 % of the scans. In F24 the VINS step was used on every scan where it passed the guard, and the no-motion "
          "guess on the rest (13.5 % of the Cave02 scans and 78 % of the GEODE scans)."),
    ("tab", "5.4", "Guess kinds in the F26 live runs (share of scans) and the effect against F24",
     [["Sequence", "A-LOAM step", "Blend", "VINS step", "F26 against F24, ATE (m)"],
      ["Multi Floor", "98.5 %", "0.5 %", "1.0 %", "0.54 against 0.45 to 1.01 (tie)"],
      ["Long Corridor", "95.4 %", "2.8 %", "1.7 %", "2.10 against 1.75 to 2.15 (tie)"],
      ["Corridor02 (2 runs)", "97.7 to 97.8 %", "1.4 to 1.5 %", "0.8 %", "1.93, 2.04 against 1.29, 1.47 (higher)"],
      ["Cave02", "100 %", "0 %", "0 %", "6.23 against 7.08 to 7.55 (lower)"],
      ["GEODE stairs (3 runs)", "93.6 to 95.3 %", "2.3 to 3.4 %", "2.3 to 2.9 %", "mean 5.04 against 7.23 (lower)"],
      ["Farm L route", "67 %", "0.6 %", "32 %", "0.29 against 0.47 (lower)"]],
     [1900, 1400, 1250, 1250, 2483], dict(align="lcccl", size=20)),
    ("p", 'The effect follows the health of VINS-Mono. Where it starts late or fails (Cave02, GEODE), dropping its motion from the guess helped: every 120 s block of the Cave02 run of F26 was lower than in the F24 run, by 2.0 to 2.3 m in the first 240 s and 0.6 to 0.9 m later. Where it is healthy and the scan is not flagged (Corridor02, no VO_FAIL), keeping its motion in the guess was better by about 0.5 m. Both comparisons rest on one to four runs per version.'),
    ("h2", "5.6 Live results of the final version"),
    ("p", "Table 5.5 gives every live front-end result of F26 with the baselines in the format of Table 1 of {@ganesan}: minimum, median, "
          "maximum and mean ATE over the live runs, the mean of the per-run maximum error, and the improvement of F26, (baseline mean - F26 "
          "mean) / baseline mean. An upward arrow means F26 has the lower error. F26 is lower than VINS-Mono alone and A-LOAM alone on every "
          "sequence, by 39 to 98 %. Against F8 it is lower on Multi Floor (12 %), Long Corridor (54 %) and Corridor02 (6 %) and higher on "
          "Cave02 (39 %). Against F24 the mean is lower on Multi Floor, Cave02, GEODE and the farm and about equal on Long Corridor, but on Multi Floor "
          "the F26 run lies inside the F24 spread (0.45 to 1.01 m). On Corridor02 the F24 mean includes its run of 104 m, while its "
          "median (1.47 m) is lower than that of F26 (1.99 m)."),
    ("tab", "5.5", "Live front-end results of F26 and the baselines, ATE RMSE (m) and improvement of F26",
     [["Sequence", "Method", "n", "Min", "Median", "Max", "Mean", "Impr.", "Max err., mean", "Impr."],
      ["Multi Floor", "VINS-Mono alone", "3", "1.25", "1.29", "1.29", "1.277", "↑ 57.7 %", "2.47", "↑ 59.1 %"],
      ["", "A-LOAM alone", "3", "13.20", "30.69", "35.43", "26.44", "↑ 98.0 %", "49.38", "↑ 98.0 %"],
      ["", "F8", "9", "0.47", "0.59", "0.77", "0.617", "↑ 12.4 %", "1.34", "↑ 24.8 %"],
      ["", "F24", "3", "0.45", "0.69", "1.01", "0.717", "↑ 24.7 %", "1.30", "↑ 22.1 %"],
      ["", "**F26**", "1", "0.54", "0.54", "0.54", "**0.540**", "-", "1.01", "-"],
      ["Long Corridor", "VINS-Mono alone", "3", "5.65", "5.66", "6.13", "5.813", "↑ 63.9 %", "15.54", "↑ 76.0 %"],
      ["", "A-LOAM alone", "3", "11.21", "13.21", "23.01", "15.81", "↑ 86.7 %", "-", "-"],
      ["", "F8", "3", "3.97", "4.76", "4.87", "4.533", "↑ 53.7 %", "12.89", "↑ 71.1 %"],
      ["", "F24", "3", "1.75", "2.12", "2.15", "2.007", "↓ 4.6 %", "4.80", "↑ 22.3 %"],
      ["", "**F26**", "1", "2.10", "2.10", "2.10", "**2.100**", "-", "3.73", "-"],
      ["Corridor02", "VINS-Mono alone", "3", "4.02", "4.03", "4.03", "4.027", "↑ 50.7 %", "6.75", "↑ 48.7 %"],
      ["", "A-LOAM alone", "3", "46.53", "58.57", "92.95", "66.02", "↑ 97.0 %", "-", "-"],
      ["", "F8", "3", "2.07", "2.10", "2.19", "2.120", "↑ 6.4 %", "3.76", "↑ 8.1 %"],
      ["", "F24", "3", "1.29", "1.47", "104.00", "35.59", "↑ 94.4 %", "51.46", "↑ 93.3 %"],
      ["", "**F26**", "2", "1.93", "1.99", "2.04", "**1.985**", "-", "3.46", "-"],
      ["Cave02", "VINS-Mono alone", "3", "10.21", "10.26", "10.26", "10.243", "↑ 39.2 %", "-", "-"],
      ["", "F8", "3", "4.31", "4.40", "4.71", "4.473", "↓ 39.3 %", "6.75 to 7.74", "↓"],
      ["", "F24", "3", "7.08", "7.11", "7.55", "7.247", "↑ 14.0 %", "12.06", "↑ 12.4 %"],
      ["", "**F26**", "1", "6.23", "6.23", "6.23", "**6.230**", "-", "10.56", "-"],
      ["GEODE stairs", "VINS-Mono alone", "7", "153.1", "186.6", "271.6", "204.6", "↑ 97.5 %", "808.7", "↑ 98.5 %"],
      ["", "F24", "4", "6.15", "6.81", "9.15", "7.228", "↑ 30.2 %", "18.25", "↑ 32.2 %"],
      ["", "**F26**", "3", "3.26", "5.51", "6.36", "**5.043**", "-", "12.38", "-"],
      ["Farm L route", "VINS-Mono alone", "2", "4.31", "9.39", "14.47", "9.390", "↑ 96.9 %", "16.76", "↑ 96.6 %"],
      ["", "A-LOAM alone", "1", "0.478", "0.478", "0.478", "0.478", "↑ 39.3 %", "0.98", "↑ 42.5 %"],
      ["", "F8 (sideways camera)", "1", "0.490", "0.490", "0.490", "0.490", "↑ 40.8 %", "0.75", "↑ 25.1 %"],
      ["", "F24 (same rig)", "1", "0.472", "0.472", "0.472", "0.472", "↑ 38.6 %", "1.07", "↑ 47.4 %"],
      ["", "**F26**", "1", "0.290", "0.290", "0.290", "**0.290**", "-", "0.56", "-"]],
     [1050, 1500, 330, 620, 700, 700, 800, 900, 853, 830], dict(align="llcccccccc", size=17)),
    ("p", "Figure 5.3 shows the F26 trajectories on the four sequences with the clearest structure; the fused paths follow the ground truth where VINS-Mono alone drifts in heading (Long Corridor) or in scale (farm). A-LOAM's own mapped pose, seeded by the fusion, scored lower than the fused output on Long Corridor (1.00 against 2.10 m) and Corridor02 run 1 (1.17 against 1.93 m), and higher on Multi Floor (1.92 against 0.54 m) and Corridor02 run 2 (2.52 against 2.04 m), so a rule for choosing between the two is open."),
    ("fig", F3 + "f5_traj.png", 4.8, "5.3", "Top-down trajectories of F26 against ground truth (RMSE in brackets)"),
    ("h2", "5.7 Long Corridor maximum error"),
    ("p", "In two of the three Long Corridor runs of F24 the maximum error (5.31 and 5.57 m) exceeded Switch-SLAM's 5.09 m. In run 1 it occurred at 9.6 s, inside the LiDAR-only warm-up, when A-LOAM's direction of travel was 3.4° off the ground truth; the start is 135 m from the centroid of the path, about which the full-span alignment pivots, so a 2° heading error there becomes about 5 m. After 30 s the error stayed between 0.8 and 2.3 m. The F26 run stayed within the bound (3.73 m), as did the two F35 runs (3.54 and 4.51 m). A shorter warm-up of 10 or 5 s was replayed: it lowered the replayed Long Corridor maximum from 3.51 to 2.97 and 2.85 m but raised Multi Floor from 0.531 to 0.596 and 0.623 m, because VINS-Mono's scale is poorly observed in its first seconds, so the warm-up was not changed."),
    ("h2", "5.8 Farm simulation"),
    ("p", "Table 5.6 lists every live farm run in the order they were made, one run per version. The pass rule was RMSE ≤ 0.38 m and "
          "maximum ≤ 1.10 m. F20 gave 2.45 m in a run where VINS-Mono alone was 16.2 m: without a VIO-trust check the fused pose followed "
          "the failing VINS. F21 kept the error at 0.50 m with VINS-Mono alone at 3.45 m. F23 had a 5.3 m excursion in the first 18 s after "
          "the reset, all of it in the warm-up and VO_FAIL modes; F24, with the guard on A-LOAM's initial guess, had none. With the camera "
          "facing forward, F24 gave 0.472 / 1.068 m in a run where VINS-Mono alone drifted to 14.5 m, and F26 gave 0.290 / 0.562 m, inside "
          "both parts of the rule."),
    ("tab", "5.6", "Farm L route, live runs (one each), ATE RMSE / maximum (m)",
     [["Version", "Camera", "Fused output", "VINS-Mono alone (same run)", "Rule met"],
      ["A-LOAM alone", "-", "0.478 / 0.977", "-", "max only"],
      ["F8", "sideways", "0.490 / 0.750", "1.222 / 5.70", "max only"],
      ["F20", "sideways", "2.448 / 6.087", "16.17 / 52.5", "no"],
      ["F21", "sideways", "0.496 / 0.995", "3.453 / 16.99", "max only"],
      ["F23", "sideways", "0.496 / 5.308", "22.23 / 222.5", "no"],
      ["F24", "sideways", "0.657 / 0.897", "2.067 / 3.31", "max only"],
      ["F24", "forward", "0.472 / 1.068", "14.47 / 26.57", "max only"],
      ["**F26 (final)**", "forward", "**0.290 / 0.562**", "4.31 / 6.95", "**yes**"],
      ["Switch-SLAM (published)", "not stated", "0.38 / 1.10", "-", "-"]],
     [2083, 1200, 1800, 2000, 1200], dict(align="lcccc")),
    ("p", "The two forward-camera runs are not a clean pair: VINS-Mono takes no input from the fusion, yet it gave 14.5 m in the F24 run and 4.3 m in the F26 run on the same rig. In the F26 run the A-LOAM output itself scored 0.312 m, and the LiDAR carried 99 % of the translation weight because the VIO-trust check distrusted a VINS-Mono path that was 20 % short, so the result is essentially A-LOAM's scan-to-map pose with the VINS step in the guess on the degenerate stretch. Rescaling VINS-Mono to the LiDAR path length lowered the sideways-camera farm replay to 0.34 to 0.37 m but raised Corridor02 by 0.58 m, and was not adopted."),
    ("h2", "5.9 Tests with injected faults"),
    ("p", "Two faults were injected into the logged runs and replayed. In the LiDAR fault (FL) the LiDAR position slides along the weakest "
          "Schur direction at 0.2 m/s for three 20 s windows, while its Hessian is replaced by an isotropic one, so the solver looks "
          "confident and is wrong. In the VIO fault (FV) VINS-Mono is given a scale error. Table 5.7 gives the means. Against the LiDAR fault "
          "the min-rule tensor cap of F20 helped in 12 of 12 logs (sign test p = 0.0005), by 2 to 5 %. The VIO-trust check of F21 removed "
          "most of the VIO fault (Multi Floor 2.35 to 0.71 m, Long Corridor 4.89 to 2.61 m) and cut the GEODE error from 18.3 to 10.6 m, at a cost of "
          "0.2 to 0.6 m under the LiDAR fault."),
    ("tab", "5.7", "Replays with injected faults, mean ATE RMSE (m)",
     [["Cell", "F16", "F20", "F21"],
      ["Multi Floor, LiDAR fault", "3.81", "3.72", "3.89"],
      ["Multi Floor, VIO fault", "2.11", "2.35", "0.71"],
      ["Long Corridor, LiDAR fault", "3.72", "3.62", "4.24"],
      ["Long Corridor, VIO fault", "4.81", "4.89", "2.61"],
      ["Corridor02, LiDAR fault", "4.81", "4.56", "4.88"],
      ["Corridor02, VIO fault", "4.03", "4.02", "3.58"],
      ["GEODE stairs, no fault (A-LOAM alone 10.3)", "17.8", "18.3", "10.60"]],
     [3683, 1500, 1500, 1600], dict(align="lccc")),
    ("h2", "5.10 Cave02 and GEODE stairs"),
    ("p", "These two sequences are where A-LOAM and VINS-Mono are both weak (Figure 5.4). On GEODE VINS-Mono lost its scale (0.02 to 0.07 in the F24 runs) and the node was in the warm-up or VO_FAIL mode on 73 to 88 % of the scans, so the fused output is close to A-LOAM's own (6.36 against 6.39 m, 3.26 against 3.31 m, 5.51 against 4.58 m). The error is mostly vertical (the stairwell descends 23 m); with each 30 to 60 s segment aligned on its own it is only 0.2 to 3.7 m."),
    ("p", "On Cave02 F26 is 2.4 m below A-LOAM's own output (6.23 against 8.66 m) but 1.8 m above the F8 and F16 runs of October (4.47 and 4.40 m). In the F24 runs the error with each segment after 300 s aligned on its own was only 0.67 to 0.70 m, and the full-span error came from a stall at 285 to 305 s, where the ground truth moves 6 m and the estimate 1.5 m, while the scan's translation information was about half its usual level and VINS-Mono was distrusted. The reason for this difference from F8 and F16 is not yet identified."),
    ("fig", F3 + "f5_heldout.png", 4.6, "5.4", "Cave02 and GEODE stairs, F26 live, with A-LOAM's output in the same run"),
    ("h2", "5.11 Success rate and hypothesis tests"),
    ("p", "Table 5.8 gives the success rate (share of runs with ATE ≤ 10 m) and the median of the per-run maximum error, in the format of "
          "Table 2 of {@ganesan}. Every F26 run met the bound. VINS-Mono alone did not meet it on Cave02 (10.2 m, just over the bound) or GEODE, "
          "A-LOAM alone did not meet it on the three SubT-MRS sequences where it was run, and one of three F24 Corridor02 runs did not meet it."),
    ("tab", "5.8", "Success rate (ATE ≤ 10 m) / median of the per-run maximum error (m)",
     [["Sequence", "VINS-Mono alone", "A-LOAM alone", "F8", "F24", "F26"],
      ["Multi Floor", "100 % / 2.51", "0 % / 58.50", "100 % / 1.24", "100 % / 1.24", "100 % / 1.01"],
      ["Long Corridor", "100 % / 15.24", "0 % / -", "100 % / 13.15", "100 % / 5.31", "100 % / 3.73"],
      ["Corridor02", "100 % / 6.75", "0 % / -", "100 % / 3.72", "67 % / 2.68", "100 % / 3.46"],
      ["Cave02", "0 % / -", "not run", "100 % / 6.75 to 7.74", "100 % / 11.78", "100 % / 10.56"],
      ["GEODE stairs", "0 % / 730.6", "not run", "not run", "100 % / 16.78", "100 % / 14.07"],
      ["Farm L route", "50 % / 16.76", "100 % / 0.98", "100 % / 0.75", "100 % / 1.07", "100 % / 0.56"]],
     [1500, 1450, 1250, 1450, 1250, 1383], dict(align="lccccc", size=20)),
    ("p", "Table 5.9 gives the one-sided tests in the format of Table 3 of {@ganesan}. With one F26 run against three baseline runs the exact test cannot go below p = 0.25, so only Corridor02 (two F26 runs) and GEODE (three) can reject. F26 is significantly lower than VINS-Mono alone on GEODE (all 21 pairs, p = 0.008, Welch p = 1.7 x 10^{-5}). On Corridor02 it is lower than VINS-Mono alone, A-LOAM alone and F8 in every pair, but the exact test stops at p = 0.10; the Welch test rejects against VINS-Mono alone (p = 0.008) and A-LOAM alone (p = 0.022). Against F24 no test rejects; on GEODE F26 is lower in 11 of 12 pairs (p = 0.057)."),
    ("tab", "5.9", "Hypothesis test at 95 %, H_{0}: M(baseline) = M(F26), H_{1}: M(baseline) > M(F26)",
     [["Baseline", "Sequence", "n (base / F26)", "F26 lower in", "p, ATE", "p, max", "Welch p, ATE", "Reject H_{0}"],
      ["VINS-Mono alone", "Multi Floor", "3 / 1", "3 of 3", "0.25", "0.25", "-", "No"],
      ["", "Long Corridor", "3 / 1", "3 of 3", "0.25", "0.25", "-", "No"],
      ["", "Corridor02", "3 / 2", "6 of 6", "0.10", "0.10", "0.008", "No (Welch yes)"],
      ["", "Cave02", "3 / 1", "3 of 3", "0.25", "-", "-", "No"],
      ["", "GEODE stairs", "7 / 3", "21 of 21", "0.008", "0.008", "1.7 x 10^{-5}", "**Yes**"],
      ["A-LOAM alone", "Multi Floor", "3 / 1", "3 of 3", "0.25", "0.25", "-", "No"],
      ["", "Long Corridor", "3 / 1", "3 of 3", "0.25", "0.25", "-", "No"],
      ["", "Corridor02", "3 / 2", "6 of 6", "0.10", "0.10", "0.022", "No (Welch yes)"],
      ["F8", "Multi Floor", "9 / 1", "6.5 of 9", "0.40", "0.10", "-", "No"],
      ["", "Long Corridor", "3 / 1", "3 of 3", "0.25", "0.25", "-", "No"],
      ["", "Corridor02", "3 / 2", "6 of 6", "0.10", "0.10", "0.093", "No"],
      ["", "Cave02", "3 / 1", "0 of 3", "1.00", "1.00", "-", "No (F26 higher)"],
      ["F24", "Multi Floor", "3 / 1", "2 of 3", "0.50", "0.50", "-", "No"],
      ["", "Long Corridor", "3 / 1", "2 of 3", "0.50", "0.50", "-", "No"],
      ["", "Corridor02", "3 / 2", "2 of 6", "0.80", "0.80", "0.21", "No"],
      ["", "Cave02", "3 / 1", "3 of 3", "0.25", "0.25", "-", "No"],
      ["", "GEODE stairs", "4 / 3", "11 of 12", "0.057", "0.114", "0.065", "No"]],
     [1500, 1350, 950, 950, 800, 800, 1033, 900], dict(align="llcccccc", size=19)),
    ("p", 'The farm has one run per method, so no test is possible there, and the published Switch-SLAM values are single numbers that can be compared but not tested. The tests show that F26 is reliably better than VINS-Mono alone where VINS-Mono fails; against F24 they show no significant difference. Ganesan et al. used 100 runs per environment, and one to nine runs per cell sets the statistical scope of this work.'),
    ("h2", "5.12 Comparison with published results and other tests"),
    ("p", "Table 5.10 collects the results of this work on each sequence with the published values. The published numbers were read from "
          "the papers; their alignment and span are not always stated, so differences below about 0.1 m are treated as ties. Against "
          "Switch-SLAM, the closest published LiDAR-visual-inertial system, F26 is lower on Multi Floor (0.54 against 1.61 m; maximum "
          "1.01 against 3.63 m), on Long Corridor (2.10 against 2.42 m; 3.73 against 5.09 m) and on the farm (0.29 against 0.38 m; 0.56 against "
          "1.10 m), each from one run. The baselines are not identical: our VINS-Mono alone on Multi Floor (1.28 m) is far better than the "
          "6.30 m listed for VINS-Mono in Switch-SLAM's table, so part of the margin comes from the setup and the evaluation (Figure 5.5)."),
    ("tab", "5.10", "Results of this work against published values (ATE RMSE, m)",
     [["Sequence", "This work, F26", "Earlier versions of this work", "Switch-SLAM [published]; in this stack", "Other published values"],
      ["Multi Floor", "0.54 (n = 1)", "F24 0.45 to 1.01; F8 0.617; F8 + loops 0.347", "1.61; SW 5.03, 5.44", "SuperLoc 0.315 {@superloc}; challenge 0.401 / 0.577 {@subtmrs}"],
      ["Long Corridor", "2.10 (n = 1)", "F24 1.75 to 2.15; F16 2.27; F16 + loops 1.54", "2.42; SW 12.58, 13.12", "SuperLoc 0.817 {@superloc}; challenge 1.254 {@subtmrs}"],
      ["Corridor02", "1.93, 2.04", "F24 1.29, 1.47 (one run 104); F24 + loops 1.11", "not reported", "none confirmed for this sequence"],
      ["Cave02", "6.23 (n = 1)", "F8 4.47; F16 4.40; F24 7.08 to 7.55", "not reported", "none used (different metrics)"],
      ["GEODE stairs α", "3.26 to 6.36 (n = 3)", "F24 6.15 to 9.15; F16 17.5 to 19.8", "not reported", "RELEAD 0.57; R3LIVE 4.54; FAST-LIO2 4.69; DLIO 4.89; LIO-SAM 6.30 {@geode}"],
      ["Farm L route", "0.29 (n = 1)", "F24 0.47 (same rig), 0.66 (sideways camera)", "0.38", "-"]],
     [1150, 1250, 2100, 1700, 2083], dict(align="lllll", size=19)),
    ("fig", F3 + "f5_switch.png", 5.0, "5.5", "F26 against Switch-SLAM (published) and VINS-Mono alone from the same run"),
    ("p", 'The best published front ends on Multi Floor and Long Corridor are LiDAR-inertial (SuperLoc 0.315 and 0.817 m), well below F26, and on GEODE RELEAD (0.57 m) is far below it while the other published systems are at the level of F26. The other tests and corrected claims are kept in Table 5.11 because they explain the design.'),
    ("tab", "5.11", "Other tests and corrected claims",
     [["Item", "Outcome"],
      ["Weighted fusion with a biased LiDAR (synthetic)", "42.9 cm against 14.4 cm for the old pipeline"],
      ["Detection rules on Multi Floor", "VINS-Mono alone lowest"],
      ["Old channel T as a second detector", "Did not meet its pre-set test live and offline"],
      ["κ gate on the LiDAR correction", "F3 below F1 in 3 of 3 runs"],
      ["Degeneracy-aware loop weights", "Isotropic weights gave the lower error (0.605 against 0.309 m)"],
      ["F8 on Long Corridor", "4.53 m against the Switch-SLAM 2.42 m"],
      ["F8 on Corridor02", "F14 and F12 lower; loop closure made no difference"],
      ["Heading from the LiDAR map", "Not used (Multi Floor 1.58 to 1.64 m)"],
      ["SAH v3, v4, v5", "Superseded by v7; v7 does not pass two Corridor02 stress cases"],
      ["Shorter warm-up; VINS scale correction", "Each helped one sequence and raised the error on another"],
      ["Active LiDAR rotation weight (F26 replay)", "No gain shown; Cave02 2.4 m higher at every c_{R} > 0"],
      ["F25A hand-over trust; standstill hold", "No gain on GEODE"],
      ["Switch-SLAM in this stack (SW, SWI)", "Long Corridor 12.6 to 13.8 m against 2.42 m published"],
      ["Switch-SLAM structure, our channels (F30 to F34)", "GEODE 9.7 to 195.6 m; Long Corridor 3.89 to 4.29 m"],
      ["F24 on Corridor02, run 2", "104 m; cause not yet identified"],
      ["F24 family on Cave02", "6.2 to 7.6 m against 4.4 m for F16; cause not yet identified"],
      ["\"99.8 % corridor detection\"", "Withdrawn: a simulator artefact (fixed voxel grid)"],
      ["Raw Hessian \"6 times over-confident\"", "Corrected to 4.0 in standard deviation (ANEES 48)"],
      ["Switch-SLAM's 0.103 as a 95 % χ² value", "It is the lower 5 % point of χ² with 2 d.o.f."],
      ["Multi Floor described as an underground mine", "It is a multi-floor building at CMU"],
      ["A-LOAM alone on Corridor02 short of computing time", "Withdrawn after the 0.2x run (still 68 m)"],
      ["Cave02 and GEODE as held-out sequences for F26", "Withdrawn: both were used to design F25 to F27"],
      ["COIN-LIO 0.45 m quoted for GEODE α", "It is on device β; best on α is RELEAD 0.57 m"]],
     [3800, 4483], dict(align="ll", size=19)),
    ("h2", "5.13 Discussion"),
    ("p", 'Channel T is what makes the fusion work at all (Long Corridor 15.8 m for A-LOAM and 5.81 m for VINS-Mono, 4.53 m with channel T alone), and the heading read-out gave the largest single gain (4.53 to about 2.0 m). The tensor rule on S_{tt} comes into play under faults, channel R watches the rotation information (its check engaged on 3.6 % of the GEODE scans), and the safeguards of F21 to F24 each removed one observed failure. The status guess of F26 replaced the no-motion guess used on Cave02 and GEODE and lowered the error there; Corridor02 is higher by about 0.5 m.'),
    ("p", 'The threshold study and the F30 to F34 tests agree that a switching system is judged by how much it hands to VINS-Mono; with A-LOAM, the weighted fusion gave a lower error than the switch-and-remap structure on every sequence it was run on.'),
    ("p", 'Scope of the results. F26 has one to three live runs per sequence, and its three GEODE runs spread over 3.1 m. All six sequences were used during development, so the F26 results are development results and a held-out sequence is the next test. On Cave02 the final version gives 6.23 m against 4.4 m for the October versions; the reason for the difference has not yet been identified.'),

    # =========================================================== CHAPTER 6
    ("chapter", "6", "Conclusions"),
    ("p", "A LiDAR-visual-inertial odometry was built on A-LOAM and VINS-Mono in which LiDAR degeneracy is judged in three channels that set per-direction weights between the LiDAR and VIO motion, and F26, which also chooses A-LOAM's initial guess by Switch-SLAM's degeneracy status, was selected as the final version. The main findings are:"),
    ("bul", ['Weighting translation by the Schur block S_{tt} lets the LiDAR carry the well-constrained directions, and the heading read-out of the orientation tensor channel gave the largest single gain (Long Corridor 4.53 to 1.98 m).', 'The error of a switching system follows the share of time handed to VINS-Mono (Spearman -0.95 over 15 detection rules), not the detection quality, which is why the method weights instead of switching.', "Without loop closure, F26 gave 0.54 / 1.01 m on Multi Floor, 2.10 / 3.73 m on Long Corridor and 0.29 / 0.56 m on the farm, below Switch-SLAM's 1.61 / 3.63, 2.42 / 5.09 and 0.38 / 1.10 m, each from one run.", 'On GEODE F26 gave 3.26 to 6.36 m and is significantly better than VINS-Mono alone (153 to 272 m, p = 0.008); against F24 it was lower in 11 of 12 pairs, not significantly (p = 0.057).', 'The status guess lowered the error where VINS-Mono starts late or fails; Corridor02 is higher by about 0.5 m. On Cave02 F26 gives 6.23 m against 4.4 m for the October versions; all results are development results.']),
    ("h2", "6.1 Future scope"),
    ("p", "The next step is a held-out test on a sequence that played no part in the design, with three or more runs each of F26 and F24 and the reading rule written first. A rule for choosing between the fused output and A-LOAM's own mapped pose, which was lower on Long Corridor and Corridor02, and the reason for the Cave02 difference are the open points. A LiDAR-inertial front end and a loop-closure back end are the larger extensions."),
    ("refs",),
]

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
