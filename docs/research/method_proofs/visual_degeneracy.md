# Visual / VIO Failure and Degeneracy Detection — Choosing a Principled Visual Confidence Channel

Code line numbers below refer to the `master` branch files as fetched on 2026-10-05:
- VINS-Mono: `vins_estimator/src/estimator.cpp` (1147 lines), `feature_manager.cpp`, `factor/marginalization_factor.cpp`, `initial/solve_5pts.cpp`, `config/euroc/euroc_config.yaml`
- LVI-SAM: `src/visual_odometry/visual_estimator/estimator.cpp` (1115 lines), `estimator_node.cpp`, `utility/visualization.cpp`, `src/lidar_odometry/imageProjection.cpp`, `mapOptmization.cpp`, `imuPreintegration.cpp`

## Q1. What exactly are VINS-Mono's built-in failure detection criteria and constants?

### Takeaway
The T-RO paper lists three criteria qualitatively and gives no numbers. In the released code, `failureDetection()` restarts the estimator only on: accelerometer bias norm > 2.5, gyro bias norm > 1.0, position jump > 5 m between consecutive outputs, or z-jump > 1 m. The feature-count check (< 2) and the rotation check (> 50 deg) only log a message; their `return true` is commented out. The thesis's "< 20 features" heuristic does not come from failureDetection. It matches VINS-Mono's **keyframe-selection** rule (`last_track_num < 20`), which is a different check.

### Cited Findings
- Paper, Sec. VI-G "Failure detection and recovery": failure is declared when "the number of features being tracking in the latest frame is less than a certain threshold", there is a "large discontinuity in position or rotation between last two estimator outputs", or there is a "large change in bias or extrinsic parameters estimation". The paper gives no numbers. — [Qin, Li, Shen, VINS-Mono, T-RO 2018 (arXiv 1708.03852)](https://arxiv.org/pdf/1708.03852)
- Code `Estimator::failureDetection()` (VINS-Mono `estimator.cpp` L621–667) — [estimator.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/estimator.cpp):
  - L623: `if (f_manager.last_track_num < 2)` → only `ROS_INFO`; `//return true;` is **commented out** (not active)
  - L628: `if (Bas[WINDOW_SIZE].norm() > 2.5)` → **return true** (acc bias, m/s²)
  - L633: `if (Bgs[WINDOW_SIZE].norm() > 1.0)` → **return true** (gyro bias, rad/s)
  - L638–644: the extrinsic check `tic(0) > 1` is commented out
  - L646: `if ((tmp_P - last_P).norm() > 5)` → **return true** (translation jump > 5 m between the newest window pose and the previous output)
  - L651: `if (abs(tmp_P.z() - last_P.z()) > 1)` → **return true** (vertical jump > 1 m)
  - L656–665: `delta_angle = acos(delta_Q.w())*2.0/3.14*180.0; if (delta_angle > 50)` → only `ROS_INFO`; `//return true;` commented out (not active)
- On failure (L193–200): `failure_occur = 1; clearState(); setParameter();` and the system goes back to initialization ("system reboot"). — [estimator.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/estimator.cpp)
- **Keyframe rule (the actual source of "20"):** `FeatureManager::addFeatureCheckParallax`: `if (frame_count < 2 || last_track_num < 20) return true;` (make the frame a keyframe). Otherwise the frame is a keyframe when the average compensated parallax `>= MIN_PARALLAX`. — [feature_manager.cpp L74–95](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/feature_manager.cpp)
- `MIN_PARALLAX = keyframe_parallax / FOCAL_LENGTH` (parameters.cpp L56–57). The EuRoC config uses `keyframe_parallax: 10.0` (pixels), `max_cnt: 150` features, `min_dist: 30`, `F_threshold: 1.0` px RANSAC. — [parameters.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/parameters.cpp), [euroc_config.yaml](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/config/euroc/euroc_config.yaml)
- Initialization-time health checks (estimator.cpp):
  - IMU excitation: the std. dev. of `delta_v/dt` over the window must be ≥ 0.25 (L243). This check also only logs; its `//return false` is commented out.
  - Visual SfM start: needs `corres.size() > 20` correspondences and `average_parallax * 460 > 30` px (≈30 px at a nominal 460 px focal length) plus a successful `solveRelativeRT` (L449–462).
  - `solveRelativeRT` needs `inlier_cnt > 12` from `cv::recoverPose` (solve_5pts.cpp L221).
  — [estimator.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/estimator.cpp), [solve_5pts.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/initial/solve_5pts.cpp)

### Inferences
- The current thesis heuristic ("features < 20 OR pos jump > 1.5 m OR rot jump > 0.8 rad") is **not** VINS-Mono's failure detector. In particular:
  - 20 is the keyframe threshold, not a failure threshold.
  - VINS-Mono does not use rotation as an active trigger.
  - VINS-Mono's active triggers are bias norms and a 5 m / 1 m(z) position jump.

  If the thesis wants to say "we adopt [6]'s failure detection as Switch-SLAM does", it should use or cite these actual constants (2.5, 1.0, 5 m, 1 m z), or state that its own constants are custom.
- All of VINS-Mono's thresholds are hand-set constants with no derivation in the paper or the code comments.

### Gaps
- The T-RO paper has no numeric thresholds, so the only authoritative values are in the code. VINS-Fusion's values were not checked; they may differ.

## Q2. How does Switch-SLAM define S_vo (VO failure)?

### Takeaway
Switch-SLAM explicitly chooses **not** to use a Hessian/eigenvalue test for VO. It says the VO Hessian's minimum eigenvalue "is unstable and remains large after failure" (citing Demmel et al. ICCV 2021). Instead it adopts VINS-Mono's heuristic failure detection: tracked feature count, bias changes, and position/rotation changes between consecutive keyframes. S_vo is binary, and on "fail" the system runs pure LiDAR odometry until VO re-initializes. No numeric thresholds are given in the paper.

### Cited Findings
- Sec. III-D "Failure Detection of Visual Odometry": "The minimum eigenvalue of the Hessian matrix of visual odometry is unstable and remains large after failure, as shown in [29]. Therefore, we adapt failure detection of visual odometry as proposed in [6] instead of degeneracy detection in our system. The number of tracked features, bias changes, and positional/rotational changes between consecutive keyframes are used for failure detection. If any of these values exceed the predefined threshold, the system treats the current state as a failure... the state of visual odometry, denoted as Svo, is set to 'fail,' and the system attempts re-initialization. Until successful re-initialization is achieved, the entire system relies on pure LiDAR odometry." — Lee et al., Switch-SLAM, IEEE RA-L 9(8), 2024, doi:10.1109/LRA.2024.3421792 (project file `SwitchSLAM.pdf`, p. 7274) — [DOI](https://doi.org/10.1109/LRA.2024.3421792)
- [6] = Qin et al. VINS-Mono T-RO 2018. [29] = N. Demmel, D. Schubert, C. Sommer, D. Cremers, V. Usenko, "Square root marginalization for sliding-window bundle adjustment," ICCV 2021, pp. 13260–13268. — Switch-SLAM reference list (project `SwitchSLAM.pdf`) — [DOI](https://doi.org/10.1109/LRA.2024.3421792)
- Algorithm 1, line 2: `if S_vo == fail ∨ ∀i λ(i) ≥ λ_t(i)` → use LO propagation as the initial guess.
- Eq. (16): if S_vo = fail and LiDAR is degenerate, optimize only along well-conditioned DOFs, `δx = −(UΛ_pU^{-1})^{-1} J_l^T d_l`.
- H_v is used only as a fusion weight in Eq. (15) and is never eigen-tested.
- The LiDAR thresholds λ_t = [0.12, 0.27, 0.48] come from a chi-square / semicircle-law derivation (Eq. 12).
— project `SwitchSLAM.pdf` pp. 7273–7274 — [DOI](https://doi.org/10.1109/LRA.2024.3421792)

### Inferences
- Switch-SLAM's "non-heuristic" claim applies only to the LiDAR channel. Its visual channel is admittedly heuristic. This makes the thesis's goal of a principled visual channel a genuine extension rather than a reproduction.
- **Directly relevant to the proposed Schur-complement test on H_v:** Switch-SLAM's authors claim that λ_min(H_v) does not drop when VO fails. A plausible mechanism (inference, not verified in Demmel et al.):
  - IMU preintegration factors and the marginalization prior keep H_v well-conditioned even when visual factors vanish or are wrong.
  - A wrong but confident solution still has a large Gauss-Newton Hessian, because H measures curvature at the current estimate, not correctness.

  Any H_v-based channel therefore needs to (a) isolate the **visual** contribution (e.g., the reprojection-factor Hessian only, or H_full − H_IMU-only), and/or (b) be paired with a consistency check such as a residual χ² test or the bias/jump checks.

### Gaps
- I did not verify that Demmel et al. (ICCV 2021) actually show "λ_min remains large after failure". That paper is about square-root marginalization numerics. The Switch-SLAM citation may be loose. This should be checked before the thesis repeats the claim.
- No public Switch-SLAM code was reviewed for the numeric S_vo thresholds.

## Q3. What is LVI-SAM's VIS failure detection, with exact constants?

### Takeaway
- **Paper:** VIS fails when tracked features drop below a threshold or the IMU bias exceeds a threshold. On failure it re-initializes and informs the LIS, which then uses raw IMU instead of VIO for its initial guess.
- **Code:** the feature-count check is disabled (log only). The active triggers are acc-bias norm > 2.5, gyro-bias norm > 1.0, speed > 30 m/s, position jump > 5 m, and z-jump > 1 m.
- **Signalling:** the LIS is "informed" through a reset counter packed into `odometry.pose.covariance[0]`.

### Cited Findings
- Paper Sec. II-B.3: VIS reports failure when "the number of tracked features is below a threshold, or when the estimated IMU bias exceeds a threshold"; "Once a failure is detected, the VIS re-initializes and informs the LIS." — [Shan et al., LVI-SAM, ICRA 2021 (arXiv 2104.10831)](https://arxiv.org/pdf/2104.10831)
- Paper Sec. II-C.1: "We use visual-inertial odometry as an initial guess when it is available. If the VIS reports failure, we then switch to IMU measurements for the initial guess." — [LVI-SAM](https://arxiv.org/pdf/2104.10831)
- Paper Sec. II-C.2: "The LIS reports failure when the smallest eigenvalue of A^TA is smaller than a threshold at the first iteration of optimization" (adapted from Zhang et al. 2016); LiDAR constraints are not added to the graph on failure. — [LVI-SAM](https://arxiv.org/pdf/2104.10831)
- Code `Estimator::failureDetection()` (LVI-SAM visual_estimator/estimator.cpp L653–697) — [estimator.cpp](https://github.com/TixiaoShan/LVI-SAM/blob/master/src/visual_odometry/visual_estimator/estimator.cpp):
  - L655: `last_track_num < 2` → `ROS_ERROR` only; `//return true;` (inactive)
  - L660: `Bas[WINDOW_SIZE].norm() > 2.5` → return true
  - L665: `Bgs[WINDOW_SIZE].norm() > 1.0` → return true
  - L670: `Vs[WINDOW_SIZE].norm() > 30.0` → return true ("big speed"; this check is **added** relative to VINS-Mono)
  - L676: `(tmp_P - last_P).norm() > 5.0` → return true
  - L681: `abs(tmp_P.z() - last_P.z()) > 1` → return true
  - L690–694: `delta_angle > 50` deg → `ROS_ERROR` only; `//return true;` (inactive)
- On failure: `clearState()` increments `failureCount` (estimator.cpp L22–24; init −1 at L5).
- `pubLatestOdometry(..., estimator.failureCount)` writes `odometry.pose.covariance[0] = double(failureId); // notify lidar odometry failure` (visualization.cpp L82; estimator_node.cpp L158).
- The LiDAR side reads `cloudInfo.odomResetId = round(covariance[0])` (imageProjection.cpp L362). It uses the VINS transform as the initial guess only if `odomAvailable && odomResetId == stored id` (mapOptmization.cpp L819–851). Otherwise it falls back to IMU (L855).
— [visualization.cpp](https://github.com/TixiaoShan/LVI-SAM/blob/master/src/visual_odometry/visual_estimator/utility/visualization.cpp), [imageProjection.cpp](https://github.com/TixiaoShan/LVI-SAM/blob/master/src/lidar_odometry/imageProjection.cpp), [mapOptmization.cpp](https://github.com/TixiaoShan/LVI-SAM/blob/master/src/lidar_odometry/mapOptmization.cpp)

### Inferences
- In LVI-SAM's code there is a contradiction between paper and code: the paper names the feature-count criterion, but the code has it disabled. The effective criteria are bias / velocity / position-jump only.
- LVI-SAM, like Switch-SLAM, uses an eigenvalue test for LiDAR but a heuristic for vision. No reviewed system uses a symmetric visual eigen-test.

### Gaps
- The LVI-SAM paper gives no numeric thresholds; the numbers come only from the code.

## Q4. Which Hessian/Fisher-information measures exist for VIO, and which motions are degenerate?

### Takeaway
There is a solid theoretical basis for information-matrix-based visual measures:
- Zhang & Vela's σ_min of the observability matrix
- Carlone & Karaman's λ_min / log-det of the landmark-marginalized information matrix
- Zhang & Scaramuzza's Fisher Information Field (trace/det of the 6×6 pose FIM)

These were developed for feature selection or active perception, **not** for online failure flags. Known degenerate motions for monocular VIO:
- Generic motion: 4 unobservable DOF (3 translation + yaw).
- Constant local acceleration: scale also becomes unobservable.
- No rotation: all of roll/pitch/yaw become unobservable, since gravity and accelerometer bias cannot be separated.

### Cited Findings
- Zhang & Vela (CVPR 2015) score features by "ψ(f, τ) = σ_min(Q_SOM(τ|f))", the minimum singular value of the stripped observability matrix over τ frames. "The value of a feature towards ego-motion estimation is reflected by the conditioning of the SOM". When too few anchors exist, they pick feature subsets by submodular maximization of the minimum singular value. — [Zhang & Vela, Good Features to Track for Visual SLAM, CVPR 2015](https://openaccess.thecvf.com/content_cvpr_2015/papers/Zhang_Good_Features_to_2015_CVPR_paper.pdf)
- Carlone & Karaman ("Attention and Anticipation in Fast Visual-Inertial Navigation", T-RO 2019 / arXiv 1610.03344):
  - They "analytically eliminate the 3D point from the estimation using the Schur complement trick". The per-landmark information is "Δ_l = F_l^T F_l − F_l^T E_l (E_l^T E_l)^{-1} E_l^T F_l" over poses, velocities, and biases.
  - Metrics: the smallest eigenvalue (worst-case error variance = λ_max(P) = 1/λ_min(information)) and the log-determinant (ellipsoid volume).
  — [arXiv 1610.03344](https://arxiv.org/pdf/1610.03344)
- Zhang & Scaramuzza (ICRA 2019) build a 6×6 pose Fisher information "I_T = Σ_k I_T(u^k)" with "I_x(z) = 1/σ² J_x^T J_x" from bearing measurements. Landmarks are treated as **known**, not marginalized. They default to the trace (T-optimality) and also show the determinant. — [Fisher Information Field for Active Visual Localization, ICRA 2019](https://rpg.ifi.uzh.ch/docs/ICRA19_Zhang.pdf); extended version [arXiv 2008.03324](https://arxiv.org/html/2008.03324v1)
- Wu & Roumeliotis (2016 tech report, "Unobservable Directions of VINS Under Special Motions") — [MARS tech report](https://mars.cs.umn.edu/papers/tech_report_unobs_directs.pdf):
  - Generic motion: 4 unobservable DOF, "three for global translation and one for global yaw".
  - Constant local acceleration: scale also becomes unobservable, because "one cannot distinguish the magnitude of the true body acceleration from that of the accelerometer bias".
  - No rotation: global orientation (roll, pitch, yaw) becomes unobservable, because "one cannot distinguish the direction of the local gravitational acceleration from that of the accelerometer bias".
- VINS-Mono itself states that drift "only occurs in 4 DOF, which is the 3D translation, and the rotation around the gravity direction (yaw angle)". — [VINS-Mono arXiv 1708.03852](https://arxiv.org/pdf/1708.03852)
- Yang et al. extend degenerate-motion analysis to aided INS with online calibration. — [Degenerate Motion Analysis for Aided INS, ICRA 2019](https://yangyulin.net/papers/2019_icra_degenerate.pdf); [Online Self-Calibration for VINS, T-RO 2023](https://yangyulin.net/papers/2023_tro_full_calib.pdf)

### Inferences
- Common knowledge, not fetched here: **pure rotation** is degenerate for monocular *vision* because there is zero baseline, so feature depth and translation scale cannot be triangulated. In VIO the IMU still propagates through it, but the visual contribution to translation information collapses. This is exactly the case a visual-only (reprojection-factor) information measure should detect. It can be checked with the parallax statistic VINS-Mono already computes (compensated parallax vs. `MIN_PARALLAX`).
- For a thesis "visual confidence" channel, the literature supports either:
  - λ_min of the landmark-marginalized information (Carlone & Karaman); or
  - per-block λ_min (rotation 3×3 and translation 3×3, after Schur-complementing the other block), in the same way the LiDAR channel normalizes rotation and translation separately.

  Mixing rotation (rad) and translation (m) in one eigenproblem is unit-dependent. This is a known issue for LiDAR degeneracy as well (inference).

### Gaps
- Martinelli's closed-form observability results and Kottas/Hesch consistency papers were not fetched. Their DOF statements are consistent with Wu & Roumeliotis but are not separately cited here.
- I found no paper that uses λ_min of a VIO Hessian as a runtime failure/degeneracy flag with a derived threshold.

## Q5. How do you extract a 6-DOF pose information matrix from VINS-Mono's sliding window, and what does gauge freedom imply?

### Takeaway
Use the Schur complement to marginalize landmarks (inverse depths), velocities, biases, extrinsics, td, and the other poses. This leaves a 6×6 block for the target pose, or a 12×12 block for two keyframes from which relative-pose information is formed. The full VIO Hessian is rank-deficient by 4 (x, y, z, yaw) under free gauge, so the "absolute" pose block is gauge-dependent. Thresholding should use gauge-invariant quantities:
- the relative pose between consecutive keyframes, or
- roll/pitch plus relative terms.

VINS-Mono runs Ceres without fixing the gauge, then removes yaw/position drift afterwards in `double2vector()`.

### Cited Findings
- Zhang, Gallego & Scaramuzza (RA-L 2018) — [RAL18_Zhang.pdf](https://rpg.ifi.uzh.ch/docs/RAL18_Zhang.pdf); covariance transformation code at [rpg_vi_cov_transformation](https://github.com/uzh-rpg/rpg_vi_cov_transformation):
  - VI systems have a 4-DOF gauge freedom: "rotation around gravity and translation".
  - Three handling options: gauge fixation ("fixing the position and yaw angle of the first camera pose"), a gauge prior, and free gauge.
  - Under free gauge the Hessian has "a rank deficiency of four", and covariance is obtained with the Moore–Penrose pseudoinverse. That covariance "is not associated to any particular reference frame".
  - Free-gauge covariance can be transformed to the gauge-fixed form: "Cov(θ_C) ≈ [Q_C ∂θ_C/∂θ] Cov*(θ) [...]^T". The relative difference they report is 0.11%.
- VINS-Mono marginalization (`MarginalizationInfo::marginalize`, marginalization_factor.cpp L267–290):
  - `Amm` is symmetrized and eigen-decomposed, and its pseudo-inverse is formed by thresholding eigenvalues `> eps`.
  - `A = Arr − Arm·Amm_inv·Amr`, `b = brr − Arm·Amm_inv·bmm` (L280–281).
  - `A` is eigen-decomposed again, eigenvalues ≤ eps are zeroed, and the prior is stored as `linearized_jacobians = S_sqrt.asDiagonal() * eigenvectors^T` (L283–290).
  — [marginalization_factor.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/factor/marginalization_factor.cpp)
- VINS-Mono gauge handling, `double2vector()` (estimator.cpp L533–560): after optimization it computes the yaw difference `y_diff` between the pre-optimization `Rs[0]` and the optimized `para_Pose[0]`, then rotates/translates the whole window back so pose 0's yaw and position are unchanged. This means the optimizer runs with a free yaw/position gauge, which is then fixed after the solve. — [estimator.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/estimator.cpp)
- VINS-Mono (paper Sec. VI-D): "The marginalization is carried out using the Schur complement. We construct a new prior based on all marginalized measurements related to the removed state." — [arXiv 1708.03852](https://arxiv.org/pdf/1708.03852)
- Carlone & Karaman use the same Schur-complement elimination of landmarks to get information over poses/velocities/biases. — [arXiv 1610.03344](https://arxiv.org/pdf/1610.03344)

### Inferences (not directly sourced)
- **Recipe for H_v (inference):**
  1. Re-use Ceres' Jacobians at the solution (e.g., `problem.Evaluate` with `jacobians`), or rebuild them the way the `MarginalizationInfo` code does.
  2. Form J^T W J over all factors in the window.
  3. Schur-complement out the inverse depths (block-diagonal, cheap), then velocities/biases/extrinsics/td, then all poses except the newest two keyframes.
  4. From the resulting 12×12 information on (T_{k−1}, T_k), compute the relative-pose information. With ξ = log(T_{k−1}^{-1} T_k) and Jacobian G (12→6), Σ_rel = G Σ_12 G^T, and the information is Σ_rel^{-1}. Equivalently, use a further Schur complement in a reparameterization (T_{k−1}, ξ) and marginalize T_{k−1}.

  The relative quantity is invariant to the 4-DOF gauge. Absolute x, y, z, yaw information in the newest pose mostly reflects the marginalization prior and the arbitrary gauge choice, so thresholds on it would be meaningless.
- **Which factors to include (inference, motivated by Switch-SLAM's warning in Q2):** a "visual confidence" should be computed from **reprojection factors only** (plus, optionally, the visual part of the marginalization prior). If IMU and prior factors are included, information stays high even when the camera is blind, which reproduces the failure mode Switch-SLAM cites.

  An alternative is the information gain the camera adds, e.g. λ_min of the generalized eigenproblem `H_vis+imu x = λ H_imu x`, or the log-det ratio. This would be a principled, unit-free "how much does vision add" score (inference; no source found using it for VIO).
- Pure-rotation and low-parallax cases show up as small eigenvalues of the translational 3×3 block of the relative visual information. Constant-acceleration scale ambiguity is a VIO-level (IMU) observability issue and would not appear in reprojection-only information (inference).

### Gaps
- I found no paper that explicitly argues "relative-pose information between consecutive keyframes is the right object for VIO degeneracy because of the gauge". The argument above is assembled from the gauge-freedom paper and is an inference.
- The `eps` value used in VINS-Mono's marginalization was not confirmed; it is defined in a header not fetched (commonly reported as 1e-8 — unverified).

## Q6. Which feature-count / parallax heuristics exist, and are any derived?

### Takeaway
All feature-count and parallax thresholds found are empirical constants with no derivation:
- VINS-Mono: 20 tracked features for a keyframe, 10 px parallax, 30 px init parallax, >20 correspondences, >12 inliers, bias 2.5/1.0, jump 5 m / 1 m.
- LVI-SAM: the same, plus 30 m/s speed.
- SA-LIVO (2026): a soft multiplicative quality factor (residual RMS, observation count, rejection ratio) with hand-set constants.

The closest "derived" alternatives are information-theoretic (σ_min / λ_min / log-det), and those come from the feature-selection literature.

### Cited Findings
- VINS-Mono constants: see Q1 — [estimator.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/estimator.cpp), [feature_manager.cpp](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/feature_manager.cpp), [euroc_config.yaml](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/config/euroc/euroc_config.yaml)
- SA-LIVO (arXiv 2606.25699):
  - It uses a visual quality factor q = q_rms · q_cnt · q_rej. q_rms penalizes photometric residuals > 12 gray levels; q_cnt ramps with the valid observation count up to a minimum; q_rej decreases with the outlier rejection ratio.
  - Spectral gating runs **only on the joint matrix** Λ_L + qΛ_V, with g(k) = min(√λ_k/σ_min, 1). The visual information is never eigen-decomposed on its own.
  — [SA-LIVO, arXiv 2606.25699](https://arxiv.org/html/2606.25699v1)
- Selective Kalman Filter (Huang et al., 2024): uses **LiDAR** covariance eigen-decomposition to find degenerate directions and fuses vision only along them. The thresholds θ_r, θ_t are "set based on practical requirements and experience", and there is no visual eigenvalue test. — [Pith summary of arXiv 2412.17235](https://pith.science/paper/2412.17235) (secondary summary; primary paper not fetched)
- LVI-SAM and Switch-SLAM: LiDAR uses an eigenvalue test, vision uses heuristics (see Q2, Q3).

### Inferences
- Across the LVIO systems checked (LVI-SAM, Switch-SLAM, SA-LIVO, Selective KF), **none computes a visual degeneracy measure symmetric to the LiDAR one**. Vision is gated by heuristics or scene-level quality factors, or it acts as the "helper" along LiDAR-degenerate directions. A Schur-complemented, reprojection-only, relative-pose information test with a derived threshold would therefore be novel. The thesis should handle Switch-SLAM's stated objection (λ_min stays large after failure) explicitly, e.g. by:
  - excluding IMU/prior factors;
  - combining with a residual χ² consistency test, since VINS-Mono already uses a fixed sqrt_info = FOCAL_LENGTH/1.5 (≈1.5 px σ) for reprojection, which gives a natural χ² normalization;
  - retaining the hard VINS-Mono failure flags (bias/jump) as a separate "failure" condition, distinct from "degeneracy".
- One possible derived threshold (inference): reuse the Switch-SLAM-style normalization on the 3 normalized eigenvalues of each 3×3 block. Alternatively, set the threshold from the expected information of N well-distributed features at the observed parallax with σ = 1.5 px.

### Gaps
- Super Odometry (Zhao et al., IROS 2021), Coco-LIC, SR-LIVO, DV-LIO, R3LIVE and FAST-LIVO2 were not examined in detail within the tool budget, so I cannot confirm whether any of them has a visual Hessian degeneracy test. SA-LIVO cites FAST-LIVO, FAST-LIVO2, R3LIVE, SR-LIVO and LVI-SAM, but does not describe any of them as doing so ([SA-LIVO](https://arxiv.org/html/2606.25699v1)). A CMU thesis on visual-aided LIO in challenging environments (Super Odometry lineage) may be relevant but was not read: [Henry thesis](https://publications.ri.cmu.edu/storage/publications/2021/08/Henry_Thesis_Final.pdf).
- I found no derivation of any feature-count threshold in the literature reviewed.
