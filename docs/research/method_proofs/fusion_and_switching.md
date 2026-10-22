# Information-weighted LiDAR/VIO fusion, degeneracy in fusion, and principled mode switching

Context: the thesis code fuses δ = (H_l + H_v)^-1 (H_l d_l + H_v d_v), with no weights. H_l = J_l^T J_l comes from A-LOAM with unit residual weights and Huber loss. H_v comes from VINS-Mono. A heuristic scalar `conf` is computed but not used, and a bilateral form (conf_L H_l + conf_V H_v)^-1(...) is proposed with no proof. Switch-SLAM Eq. 15/16 and Algorithm 1 come from the project copy of the paper (SwitchSLAM.pdf, IEEE RA-L vol. 9 no. 8, Aug 2024, p. 7274). Book-level derivations that I wrote out myself, without fetching the book page this session, are marked **[derivation]**. Inferences are marked **[inference]**.

---

## Q1. Is the information-weighted fusion the minimum-variance (BLUE) estimate, and under what assumptions?

### Takeaway
x̂ = (P1^-1 + P2^-1)^-1 (P1^-1 x1 + P2^-1 x2) is the minimum-variance unbiased linear combination (BLUE) of two estimates only if all of these hold:
- both estimates are unbiased;
- they are uncorrelated (P12 = 0);
- P1 and P2 are the true covariances;
- both are expressed in the same linearized tangent space.

Under Gaussian errors it is also the ML/MAP estimate. The code's version with raw H_l and H_v breaks the third condition, because the Hessians are not covariance-normalized (see Q3). It very likely breaks the second as well (see Q2).

### Cited Findings
- Switch-SLAM itself states that its fusion "relies on MAP fusion" (Eq. 15). Its fused objective is a sum of two squared residual terms, e_v(δx) = δx + H_v^-1 J_v^T d_v and e_l(δx) = δx + [UΛ_pU^-1]^-1 J_l^T d_l. — [Switch-SLAM, Lee et al., RA-L 2024 (project file SwitchSLAM.pdf, Sec. III-E, Eq. 15–16)](https://ieeexplore.ieee.org/document/10577169) *(the URL is the IEEE landing page as best identified; the content was read from the project PDF)*
- Standard textbook sources for the result:
  - Bar-Shalom, Li & Kirubarajan, *Estimation with Applications to Tracking and Navigation* (Wiley, 2001): static fusion / information form.
  - Kay, *Fundamentals of Statistical Signal Processing, Vol. 1: Estimation Theory* (1993): Ch. 6 (BLUE) and Ch. 4 (Gauss–Markov theorem for the linear model).
  - Maybeck, *Stochastic Models, Estimation and Control Vol. 1* (1979): Ch. 1 gives the scalar two-measurement example x̂ = (σ2² z1 + σ1² z2)/(σ1² + σ2²) with 1/σ² = 1/σ1² + 1/σ2².
  — [Bar-Shalom et al., Wiley](https://onlinelibrary.wiley.com/doi/book/10.1002/0471221279); [Kay Vol. 1, Pearson](https://www.pearson.com/en-us/subject-catalog/p/fundamentals-of-statistical-signal-processing-volume-1-estimation-theory/P200000003316) *(I did not fetch the chapter text this session. The chapter pointers are from my own knowledge; verify page numbers before citing.)*

### Proof sketch [derivation]
1. **Unbiasedness constraint.** Consider linear estimators x̂ = W1 x1 + W2 x2 with E[x_i] = x. Then E[x̂] = x for every x if and only if W1 + W2 = I.
2. **Error covariance.** With e_i = x_i − x and E[e1 e2^T] = 0, the fused error covariance is P(W1) = W1 P1 W1^T + (I−W1) P2 (I−W1)^T.
3. **Minimize.** Setting ∂ tr P / ∂W1 = 0 gives W1(P1+P2) = P2, so W1 = P2(P1+P2)^-1 and W2 = P1(P1+P2)^-1.
4. **Rewrite in information form.** Using the matrix identity P2(P1+P2)^-1 = (P1^-1+P2^-1)^-1 P1^-1:
   - x̂ = P_f (P1^-1 x1 + P2^-1 x2)
   - P_f = (P1^-1 + P2^-1)^-1
5. **Stronger result.** P(W) − P_f is positive semidefinite for every admissible W. So the fusion is optimal in the Loewner order, not only in trace. This is the Gauss–Markov / BLUE result: stack z = [x1; x2] = [I; I] x + e, with Cov(e) = blkdiag(P1, P2). The Gauss–Markov estimator (A^T C^-1 A)^-1 A^T C^-1 z is exactly the formula above (Kay Vol. 1, BLUE chapter).
6. **Equivalent least-squares objective.** x̂ = argmin_x ‖x − x1‖²_{P1^-1} + ‖x − x2‖²_{P2^-1}. This is the information-weighted version of Switch-SLAM's Eq. 15.
7. **Hessian as information.** In nonlinear least squares, the Gauss–Newton Hessian H = J^T Σ^-1 J is the inverse covariance of the estimate (Laplace / Cramér–Rao approximation). This only holds when the residuals are whitened by their noise covariance Σ.
8. **Mapping to the thesis.** Take P_l^-1 ≈ H_l and P_v^-1 ≈ H_v, and note H_l d_l = −J_l^T r_l = −g_l. The fused step becomes δ = (H_l+H_v)^-1 (H_l d_l + H_v d_v). This equals one Gauss–Newton step on the joint cost ‖r_l‖² + ‖r_v‖², i.e. joint MAP over the stacked problem, but only if the two costs share a common noise scale.

### Inferences
- **[inference]** The assumptions that matter for the thesis:
  - (a) Unbiasedness. A-LOAM's d_l is biased along degenerate directions; this is Zhang's argument, see Q4.
  - (b) Independence. Both d_l and d_v start from the same prior T_{k−1} and share IMU information. In Switch-SLAM, LO's scan-to-map matching is also *initialized* from the VO increment, so the two are correlated (see Q2).
  - (c) Correct scale of H. Violated, see Q3.
  - (d) Same tangent space and linearization point. d_l and d_v must be expressed in the same frame and the same parameterization (rotation/translation ordering, left- vs right-perturbation) before they are added.
- **[inference]** Using the stacked form avoids computing d_l at all: δ = −(H_l+H_v)^-1 (g_l + g_v). This is numerically safer when H_l is near-singular, because H_l^-1 g_l blows up along degenerate directions while g_l stays bounded.

### Gaps
- If the cross-covariance P12 is known, Bar-Shalom & Campo (1986, IEEE TAES) give the fused mean x̂ = x1 + (P1−P12)(P1+P2−P12−P21)^-1 (x2−x1). I did not fetch the paper this session; this formula is from memory.
- I did not fetch page or equation numbers from Bar-Shalom, Kay or Maybeck.

---

## Q2. What if the cross-correlation between the two estimates is unknown? (Covariance intersection)

### Takeaway
Covariance intersection (CI) fuses two estimates with:
- P_CI^-1 = ω P1^-1 + (1−ω) P2^-1
- x̂ = P_CI (ω P1^-1 x1 + (1−ω) P2^-1 x2), with ω ∈ [0,1]

The result is consistent (P_CI ≥ the true error covariance) for *any* cross-correlation. For two estimates it is the provably tightest such linear bound. This is the only rigorous justification found here for a **scalar-weighted** form like the proposed bilateral (conf_L H_l + conf_V H_v) fusion. It requires that the weights sum to one (or are normalized to) and that ω is chosen by optimizing a cost on P_CI, not by a heuristic.

### Cited Findings
- CI was introduced in Julier, S. J. & Uhlmann, J. K., "A Non-divergent Estimation Algorithm in the Presence of Unknown Correlations," *Proc. American Control Conference 1997*, vol. 4, pp. 2369–2373. — [Semantic Scholar entry](https://www.semanticscholar.org/paper/A-non-divergent-estimation-algorithm-in-the-of-Julier-Uhlmann/0ff82aaa06e578968e35da6700d24096ec49953b); citation as given in [Reinhardt et al.](https://isas.iar.kit.edu/pdf/SPL15_Reinhardt.pdf)
- Optimality result (Reinhardt, Noack, Arambel & Hanebeck, "Minimum Covariance Bounds for the Fusion under Unknown Correlations"; the file name indicates IEEE Signal Processing Letters 2015):
  - The bound is (B*_c)^-1 = ω P1^-1 + (1−ω) P2^-1, with gains K1* = ω B*_c P1^-1 and K2* = (1−ω) B*_c P2^-1.
  - Their Theorem 6 proves that these CI gains minimize J(B_c) over all consistent linear fusions for any strictly monotonically increasing cost (e.g. trace, determinant), when the cross-covariance is completely unknown and the two estimates are unbiased.
  - The optimality does **not** extend to three or more estimates; they give a counterexample.
  — [Reinhardt et al., KIT ISAS PDF](https://isas.iar.kit.edu/pdf/SPL15_Reinhardt.pdf)
- Related: inverse covariance intersection (Noack et al., Automatica 2017) gives tighter bounds when the estimates share a *common* piece of information. That is the situation here: a common prior and IMU. — [Noack et al. 2017, Automatica](https://isas.iar.kit.edu/pdf/Automatica17_Noack.pdf)
- CI was applied to SLAM early on: Uhlmann, Julier et al., "Nondivergent simultaneous map building and localization using covariance intersection." — [Semantic Scholar](https://www.semanticscholar.org/paper/Nondivergent-simultaneous-map-building-and-using-Uhlmann-Julier/5b56155902b1443fb0d0a165c10f2ed834d73b10)
- A recent review: Forsling, Noack, Hendeby, "A Quarter Century of Covariance Intersection: Correlations Still Unknown?" (IEEE Control Systems lecture notes). — [Semantic Scholar](https://www.semanticscholar.org/paper/A-Quarter-Century-of-Covariance-Intersection:-Still-Forsling-Noack/532aa992c7e26d388e617eb353019ec03cc0e221/figure/0)

### Inferences
- **[inference] Key link to the thesis.** The proposed bilateral estimate δ = (c_L H_l + c_V H_v)^-1 (c_L H_l d_l + c_V H_v d_v) is invariant to multiplying c_L and c_V by a common factor. So the mean depends only on ω = c_L/(c_L+c_V), and the form is algebraically the **CI mean** with that ω. It can be defended as "conservative fusion under unknown LiDAR–VIO correlation" if three things hold:
  - (i) H_l and H_v are first put on a true information scale (Q3);
  - (ii) the weights are normalized so that c_L + c_V = 1;
  - (iii) ω is chosen as argmin det or trace of (ω H_l + (1−ω) H_v)^-1, a 1-D convex search.

  As currently defined, `conf` (a clipped average of channel ratios) has none of these properties and does not count as a proof.
- **[inference]** CI is reasonable here because the two increments are correlated in practice:
  - shared T_{k−1};
  - shared IMU preintegration;
  - Switch-SLAM's Algorithm 1 seeds LO scan-to-map matching with the VO (or interpolated) initial guess.

  Plain information fusion with P12 assumed zero would be over-confident: it double-counts the shared prior.
- **[inference]** CI works with singular information matrices, because it is defined in information form. A degenerate H_l (rank < 6) is allowed as long as ωH_l + (1−ω)H_v is full rank.
- **[inference]** CI still applies a single scalar ω to the whole 6×6 H_l. It therefore cannot express direction-specific degeneracy by itself. Combine it with the projection in Q4: use H_l^p = U Λ_p U^T inside CI.

### Gaps
- I could not verify the fast-CI closed form of Niehsen (2002, Proc. FUSION, "Information fusion based on fast covariance intersection filtering"). I recall a trace-ratio formula, but did not confirm the exact expression, so it is not given here. The safe recommendation is a numeric 1-D minimization of det(P_CI(ω)).
- The ResearchGate page "Estimation Under Unknown Correlation: Covariance Intersection Revisited" returned HTTP 429 and was not read.

---

## Q3. How do you put two Hessians on a common information scale?

### Takeaway
A Hessian is only an information matrix when each residual is whitened: H = J^T Σ^-1 J, i.e. r̃ = Σ^{-1/2} r.
- VINS-Mono already whitens: the visual reprojection residual is multiplied by sqrt_info = FOCAL_LENGTH/1.5·I (about 1.5 px std), and the IMU factors use the preintegration covariance.
- A-LOAM uses unit weights, so H_l is in m² of point-to-plane/edge distance, not in information units.

The scale fix is H_l,info = H_l / σ_l², where σ_l is the point-to-feature distance noise. Robust losses (Huber in A-LOAM, Cauchy in VINS-Mono) change the effective weights through IRLS, and this must be reflected in the Hessian.

### Cited Findings
- VINS-Mono `estimator.cpp` (setParameter) sets `ProjectionFactor::sqrt_info = FOCAL_LENGTH / 1.5 * Matrix2d::Identity();`, and the same for `ProjectionTdFactor`. `projection_factor.cpp` applies `residual = sqrt_info * residual;` and scales the Jacobian the same way. — [VINS-Mono estimator.cpp](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/VINS-Mono/master/vins_estimator/src/estimator.cpp); [projection_factor.cpp](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/VINS-Mono/master/vins_estimator/src/factor/projection_factor.cpp)
- VINS-Mono's sliding-window optimization uses `loss_function = new ceres::CauchyLoss(1.0);`. — [VINS-Mono estimator.cpp](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/VINS-Mono/master/vins_estimator/src/estimator.cpp)
- VINS-Mono failure-detection thresholds in code:
  - ‖b_a‖ > 2.5
  - ‖b_g‖ > 1.0
  - translation jump > 5 m
  - |Δz| > 1 m
  - rotation > 50° (commented as non-terminal)
  — [VINS-Mono estimator.cpp](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/VINS-Mono/master/vins_estimator/src/estimator.cpp)
- Super Odometry weights LiDAR constraints by a per-feature quality weight w = σ_3D/σ_3Dmax, computed from local geometry eigenvalues. "Unreliable LiDAR constraints will be rejected or have low weight." — [Super Odometry, arXiv 2104.14938](https://arxiv.org/pdf/2104.14938)

### Inferences
- **[inference / derivation] Scale.**
  - With unit weights, H_l = J_l^T J_l = σ_l² · (J_l^T Σ_l^-1 J_l) when Σ_l = σ_l² I.
  - So the correct information matrix is H_l/σ_l².
  - With σ_l ≈ a few cm, H_l/σ_l² is about 10³ times larger than raw H_l.
  - Not normalizing therefore causes a large, arbitrary relative weighting between LiDAR and VIO. That arbitrary weighting is effectively what the unweighted code currently does.
- **[inference] Practical estimate of σ_l².**
  - Use the residual variance at convergence: σ̂_l² = r^T r / (m − 6), with m the number of inlier correspondences (the standard regression estimator).
  - Or use a sensor/feature model, as in FAST-LIVO2's beam-divergence noise model for LiDAR points (see Q5).
- **[inference] Robust losses.**
  - Ceres applies robust losses via IRLS-like scaling of residual and Jacobian.
  - For Huber with threshold δ: inliers (|r| ≤ δ) get weight 1; outliers get weight δ/|r|.
  - The Gauss–Newton H_l should be J^T W J, with W the final IRLS weights. Count the down-weighted outliers when estimating σ_l.
  - I did not verify A-LOAM's exact Huber parameter this session. From memory it is `ceres::HuberLoss(0.1)` in laserMapping; treat this as unverified.
- **[inference] Which H_v to use.**
  - Use the *marginal* information of the current pose from VINS's sliding window: the Schur complement of the full window Hessian onto the latest pose.
  - Do not use the diagonal block. The diagonal block over-states information because it ignores correlation with landmarks, velocity and bias.
  - Monocular VINS also has 4 unobservable directions in a global frame (x, y, z, yaw). For a *relative* pose increment the information is well defined, but this is worth stating.
- **[inference] Units.** A 6×6 information matrix mixes rad and m. It is consistent as long as both H_l and H_v use the same ordering and units. No extra scalar weighting is justified.

### Gaps
- I did not verify FOCAL_LENGTH = 460 in VINS-Mono parameters.h this session (from memory).
- I did not fetch the Ceres robust-loss documentation.

---

## Q4. How should degeneracy modify the fusion? Projection / solution remapping versus scalar down-weighting

### Takeaway
Degeneracy is a *subspace* property: the eigenvectors of H_l with small eigenvalues. A scalar weight c·H_l = U(cΛ)U^T has the same eigenvectors and the same condition number. It cannot suppress a degenerate direction without suppressing all well-constrained directions by the same factor, so **a scalar cannot represent direction-specific degeneracy**.

The principled options are:
- (a) Zhang's solution remapping or projection: take the LiDAR update only in the well-conditioned subspace and the prior/other estimate elsewhere.
- (b) Information-form fusion with the truncated Hessian U Λ_p U^T.

Switch-SLAM's [UΛ_pU^-1]^-1 J_l^T d_l is the same projection as Zhang's (interpreting the inverse as a pseudo-inverse).

### Cited Findings
- Zhang, Kaess & Singh, "On Degeneracy of Optimization-based State Estimation Problems," ICRA 2016, pp. 809–816:
  - The degeneracy factor is D = λ_min + 1 (Lemma 2, Eq. 14), where λ_min is the smallest eigenvalue of A^T A.
  - The threshold is set at the midpoint between the well-conditioned and degenerate distributions on a test set.
  - Three matrices are defined from the eigenvectors (Eqs. 15–17):
    - V_f = [v_1 … v_n]^T (all directions)
    - V_p = [v_1 … v_m, 0 … 0]^T (degenerate directions)
    - V_u = [0 … 0, v_{m+1} … v_n]^T (well-conditioned directions)
  - Final solution (Eq. 18): x_f = x'_p + x'_u, with x'_p = V_f^-1 V_p x_p (prediction in the degenerate space) and x'_u = V_f^-1 V_u x_u (optimization update in the well-conditioned space).
  - In Algorithm 1 (LM loop) the remapping is applied at every iteration.
  - The method is a plug-in for frame-to-frame VO, sweep-to-sweep and sweep-to-map LiDAR. The prediction x_p comes from a motion model or the previous module.
  — [Zhang et al., ICRA 2016 PDF](https://frc.ri.cmu.edu/~zhangji/publications/ICRA_2016.pdf); [CMU RI page](https://www.ri.cmu.edu/publications/on-degeneracy-of-optimization-based-state-estimation-problems)
  *(Caveat: the fetched text rendered Algorithm 1's update as "x_f ← x_f + V_f^-1 V_p Δx_u", which looks like an extraction error, since the paper's Eq. 18 pairs V_u with x_u. Check against the PDF.)*
- LeGO-LOAM's `mapOptmization.cpp` (LMOptimization) is a reference implementation of the remapping:
  - `cv::eigen(matAtA, matE, matV);` with thresholds `eignThre[6] = {100,…,100}`.
  - Rows of `matV2` whose eigenvalues fall below threshold are zeroed and `isDegenerate` is set.
  - `matP = matV.inv() * matV2;` and, when degenerate, `matX = matP * matX2;`.
  — [LeGO-LOAM mapOptmization.cpp](https://raw.githubusercontent.com/RobustFieldAutonomyLab/LeGO-LOAM/master/LeGO-LOAM/src/mapOptmization.cpp)
- Switch-SLAM:
  - Eq. 15 fuses e_v = δx + H_v^-1 J_v^T d_v and e_l = δx + [UΛ_pU^-1]^-1 J_l^T d_l, "where Λ_p denotes the matrix with eigenvalues removed corresponding to degenerate DOFs from Λ."
  - Eq. 16: if all λ(i) ≥ λ_t(i), δx = −H_l^-1 J_l^T d_l; if VO fails, δx = −(UΛ_pU^-1)^-1 J_l^T d_l; otherwise the Eq. 15 fusion.
  - λ_t = [0.12, 0.27, 0.48] from its Eq. 12.
  — project file SwitchSLAM.pdf, Sec. III-C/E ([IEEE](https://ieeexplore.ieee.org/document/10577169))
- A field study compares degeneracy-aware registration strategies: projection/remapping, constrained and regularized solutions. — [Tuna et al., "Informed, Constrained, Aligned," arXiv 2408.11809](https://arxiv.org/html/2408.11809v1) *(seen in search results only; not read in detail)*

### Inferences
- **[derivation] Remapping is an orthogonal projector.**
  - V is orthonormal, so V_f^-1 = V_f^T.
  - Then V_f^-1 V_u = Σ_{i∈well} v_i v_i^T = P_u, the orthogonal projector onto the well-conditioned subspace. Likewise V_f^-1 V_p = P_p = I − P_u.
  - So Zhang's Eq. 18 is x_f = P_p x_p + P_u x_u, which matches LeGO-LOAM's matP.
- **[derivation] Switch-SLAM ≡ Zhang.** For a symmetric H_l = UΛU^T, U^-1 = U^T. Reading [UΛ_pU^T]^-1 as the pseudo-inverse U Λ_p^† U^T:
  - −(UΛ_pU^T)^† g_l = −Σ_{i∈well} λ_i^-1 v_i v_i^T g_l = P_u (−H_l^-1 g_l) = P_u d_l.
  - So Switch-SLAM's LiDAR term is exactly Zhang's remapped update with x_p = 0, i.e. keep the initial guess in degenerate directions.
  - Λ_p has zero entries, so the literal inverse in Eq. 15 does not exist. The pseudo-inverse reading is required.
- **[inference] Eq. 15 as printed is not information-weighted.** Both terms use identity norms. Minimizing ‖δx − a‖² + ‖δx − b‖² gives δx = (a+b)/2, a plain average of the VO increment and the *projected* LO increment.
  - In degenerate directions, this averages the VO value with zero, which halves the VO step.
  - The consistent information-weighted version is δ = (H_v + H_l^p)^-1 (H_v d_v + H_l^p d_l), with H_l^p = UΛ_pU^T. Note that H_l^p d_l = −P_u g_l.
  - In degenerate directions H_l^p adds no information, so VO alone determines δ there. In well-conditioned directions both sources are combined by their (normalized) information.
  - Whether the authors' code uses information weights cannot be decided from the printed equation; this is a possible reading issue to raise carefully.
- **[inference] Plain information fusion is "soft" degeneracy handling.** Since H_l d_l = −g_l, a small eigenvalue λ_i gives the LiDAR term little weight along v_i automatically, provided H_l is correctly scaled. The truncation (Λ_p) is the hard-thresholded limit. It is still justified (Zhang) because:
  - in degenerate directions, the linearization, data association and noise model are unreliable;
  - so the small-but-nonzero λ_i may not reflect true uncertainty, and the estimate may be biased (which violates Q1's unbiasedness assumption).
- **[inference] Answer to "can a scalar weight represent directional degeneracy?"** No.
  - The scalar-weighted bilateral form changes only the *relative* trust in H_l versus H_v uniformly in all 6 DOF.
  - If LiDAR is degenerate only in, say, x-translation, any c_L < 1 also discards valid LiDAR information in the other 5 DOF.
  - The only scalar-weighted form with a justification is CI (Q2). Even then, direction-specific handling must come from the projection H_l^p.
  - Recommended structure: projection for directionality, plus (optionally) CI ω for unknown correlation.
- **[inference] What the code does today.** The TIGHTLY_COUPLED branch uses raw H_l6, not the projection. Per the project methodology doc, the projection exists only in the LIDAR_ONLY_SAFE branch (`zero_degenerate()`). So the deployed fusion does not implement Switch-SLAM Eq. 15's degeneracy handling.

### Gaps
- I could not confirm whether the Switch-SLAM authors' code implements Eq. 15 with identity weights or with information weights.
- Soft alternatives (Tikhonov regularization or partial/scaled constraints, e.g. Hinduja et al. 2019 "Degeneracy-aware factors"; X-ICP by Tuna et al.) were not fetched.

---

## Q5. How do real LiDAR–visual–inertial systems fuse or switch?

### Takeaway
None of the systems surveyed uses a heuristic *sensor-level* scalar confidence to blend LiDAR and visual poses. They fall into three patterns:
- **(i) Failure-gated switching plus factor-graph fusion with fixed or modeled noise:** LVI-SAM, Switch-SLAM.
- **(ii) Covariance-weighted constraints into an IMU-centric graph, with feature-level quality weights and rejection:** Super Odometry.
- **(iii) Tightly coupled Kalman updates of one shared state:** R3LIVE, FAST-LIVO/FAST-LIVO2. Sequential updates there are equivalent to information-weighted fusion.

### Cited Findings
- **LVI-SAM** (Shan et al., ICRA 2021):
  - "The LIS utilizes VIS estimation for initial guesses to support scan-matching."
  - VIS failure is declared when "the number of tracked features is below a threshold, or when the estimated IMU bias exceeds a threshold"; the VIS then re-initializes and informs the LIS.
  - "If the VIS reports failure, we then switch to IMU measurements for the initial guess."
  - LIS failure is adapted from Zhang 2016: "The LIS reports failure when the smallest eigenvalue of A^T A is smaller than a threshold," and "Lidar odometry constraints are not added to the factor graph when failure happens."
  — [LVI-SAM, arXiv 2104.10831](https://arxiv.org/html/2104.10831v1)
- **Super Odometry** (Zhao et al., IROS 2021):
  - IMU-centric: "IMU odometry makes use of observations provided by visual odometry and LiDAR odometry to constrain the IMU bias."
  - VIO and LIO provide pose constraints to the IMU factor graph.
  - In visually or geometrically degraded environments, the IMU-odometry prior term "will be dominant."
  - LiDAR features carry quality weights w = σ_3D/σ_3Dmax; low-quality features are "regarded as noise, and not be used."
  - Loose coupling "distribute[s] the sensor failure risks between several estimation engines."
  — [Super Odometry, arXiv 2104.14938](https://arxiv.org/pdf/2104.14938); [project page](https://superodometry.com/)
- **R3LIVE** (Lin & Zhang, 2021): LIO (FAST-LIO) and VIO subsystems; the VIO "fuses the visual data directly and effectively by minimizing the frame-to-map photometric error." The abstract only was read; the ESIKF details were not extracted. — [R3LIVE, arXiv 2109.07982](https://arxiv.org/abs/2109.07982)
- **FAST-LIVO2** (Zheng et al., 2024):
  - "To address the dimension mismatch between the heterogeneous LiDAR and image measurements, we use a sequential update strategy in the Kalman filter."
  - The LiDAR update runs first, then the visual update uses the posterior covariance P̂ = (I − KH)P̂.
  - LiDAR noise is modeled per point, including beam divergence.
  — [FAST-LIVO2, arXiv 2408.14035](https://arxiv.org/html/2408.14035v2)
- **Switch-SLAM** (Lee et al., RA-L 2024), Algorithm 1:
  - Select the LO initial guess if VO failed or all λ(i) ≥ λ_t(i).
  - Use an interpolated guess T_k = T_{k−1} ⊞ √(3λ1)·δT^l ⊞ (1−√(3λ1))·δT^v (Eq. 13) when the status buffer says "Start/End to degenerate."
  - Otherwise use the VO guess.
  - Then scan-to-map per Eq. 16, then update the status queue.
  - VO failure follows [6] (feature count, bias change, position/rotation jumps), because "the minimum eigenvalue of the Hessian matrix of visual odometry is unstable and remains large after failure."
  — project file SwitchSLAM.pdf, Sec. III-C/D/E

### Inferences
- **[inference]** Sequential Kalman updates with independent measurement noise give the same posterior as a single batch update with stacked measurements. Hence FAST-LIVO2/R3LIVE's fusion is the information-weighted (Q1) fusion done at the measurement level, with properly modeled noise. They do not need a scalar confidence.
- **[inference]** Switch-SLAM's √(3λ1) blend weight is also a scalar applied uniformly across all 6 DOF, used only for the *initial guess*. It is a smoothing device, not an estimator. A thesis can reasonably replace it with the information-weighted / projected fusion (Q4), which transitions smoothly by construction as λ crosses the threshold if a soft projection is used.
- **[inference]** LVI-SAM's "drop the LiDAR factor when λ_min < threshold" is the hard, all-DOF version of degeneracy handling. Zhang/Switch-SLAM's projection is the per-direction refinement.

### Gaps
- I did not extract R3LIVE's exact ESIKF update equations or any degeneracy handling.
- I did not extract FAST-LIVO (v1) details or LIO-SAM/LVI-SAM noise-model constants.

---

## Q6. Principled hysteresis and debouncing for mode switching

### Takeaway
The 5-frame majority buffer is a k-of-n window test with no stated false-alarm or delay guarantees. Principled replacements:
- **(a) Schmitt-trigger dual thresholds** on the degeneracy statistic: enter degenerate mode at λ < λ_in, exit at λ > λ_out, with λ_out > λ_in. Optionally add a minimum dwell time.
- **(b) Page's CUSUM:** g_k = max(0, g_{k−1} + s_k), alarm at g_k ≥ h. It is a repeated SPRT with lower threshold 0, and it is minimax-optimal (Lorden 1971, Moustakides 1986) in worst-case detection delay for a given false-alarm rate.
- **(c) Wald's SPRT** for a one-shot decision between Normal and Degenerate.

Run one CUSUM per direction of change (into and out of degeneracy). This gives hysteresis with tunable average run length (ARL) to false alarm.

### Cited Findings
- Basseville & Nikiforov, *Detection of Abrupt Changes: Theory and Application* (Prentice Hall, 1993):
  - Log-likelihood ratio s_i = ln p_1(y_i)/p_0(y_i), with E_0(s) < 0 and E_1(s) > 0 (Eq. 2.1.2, 2.0.2).
  - CUSUM recursion g_k = (g_{k−1} + s_k)^+, g_0 = 0 (Eq. 2.2.9); alarm time t_a = min{k : g_k ≥ h} (Eq. 2.2.10).
  - CUSUM is "the repeated SPRT algorithm as long as the previously taken decision is d = 0."
  - "The optimal value of the lower threshold … should be zero," which was formally proven later (Shiryaev, Lorden, Moustakides).
  - For a Gaussian mean change, the statistic is weighted by (μ1−μ0)/σ² (Example 2.2.1; g_k = max_j S_j^k, Eq. 2.2.21).
  — [Basseville & Nikiforov, Ch. 2 PDF (LiU course copy)](https://isy.gitlab-pages.liu.se/fs/en/courses/TSFS06/PDFs/Basseville.pdf); [book entry](https://dl.acm.org/doi/abs/10.5555/151741)
- Switch-SLAM motivates its buffer as follows: states "close to the defined threshold … can rapidly change the value of the initial guess and result in non-smooth outcomes." The status buffer "prevents the status from changing radically" and classifies Normal / Start-End to degenerate / Fully degenerate from a queue Q_s of predefined size (Fig. 4). — project file SwitchSLAM.pdf, Sec. III-C
- CUSUM overview, including the Page (1954) origin. — [Wikipedia: CUSUM](https://en.wikipedia.org/wiki/CUSUM) *(secondary; primary is E. S. Page, "Continuous Inspection Schemes," Biometrika 41(1/2):100–115, 1954. I did not fetch it.)*

### Inferences / design recipe
- **[inference] Schmitt trigger.** For each DOF i, with normalized eigenvalue λ_i and Switch-SLAM threshold λ_t(i):
  - enter "degenerate" when λ_i < (1−h_i)·λ_t(i);
  - exit when λ_i > (1+h_i)·λ_t(i).
  - Choose the band h_i from the empirical spread (std) of λ_i in well-conditioned data (e.g. 2σ).
  - This gives a provably chatter-free switch whenever noise amplitude is below the band. A majority buffer does not guarantee this (alternating D/L patterns can still toggle the status).
- **[inference] CUSUM on degeneracy.** Model y_k = λ_min,k (or log λ) as Gaussian, with mean μ0 under Normal and μ1 under Degenerate (estimated from labelled data, as Switch-SLAM already does for λ_t).
  - s_k = ((μ1−μ0)/σ²)·(y_k − (μ0+μ1)/2).
  - Run g⁺ for Normal→Degenerate and a mirrored g⁻ for Degenerate→Normal. Each switch resets the other detector. This is a two-sided, hysteretic switch.
  - The threshold h trades ARL to false alarm against detection delay. This is a stated, tunable guarantee, replacing "5 frames."
- **[inference] SPRT.** For a fixed decision, Wald's SPRT stops when the cumulative LLR S_k leaves (ln B, ln A). Wald's approximations are A ≈ (1−β)/α and B ≈ β/(1−α), for target error rates α and β. These are from Wald 1945/1947 and were not fetched this session; cite the primary source.
- **[inference] Transition blend.** Instead of a discrete "Start/End" status with the √(3λ1) blend, the information-weighted fusion of Q4 with a *soft* projection makes the LiDAR contribution in each direction vary continuously with λ_i. For example, weight each eigen-direction by a smooth ramp between λ_in and λ_out. This removes the need for a separate transition mode while keeping hysteresis on the discrete VO-fail / LiDAR-only decisions.

### Gaps
- I did not fetch primary Schmitt (1938) or Wald (1945) sources, nor Lorden (1971, Ann. Math. Statist.) or Moustakides (1986, Ann. Statist.). The optimality attributions come from Basseville & Nikiforov's Ch. 2 text.
- I found no published LiDAR-degeneracy work that applies CUSUM or SPRT specifically to mode switching. This appears to be an open, defensible design contribution, but I did not search exhaustively.
