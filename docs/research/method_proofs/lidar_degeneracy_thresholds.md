# LiDAR scan-registration degeneracy detection from the Hessian / information matrix: which thresholds are derived and which are empirical

Scope: A-LOAM style 6x6 Gauss-Newton Hessian H_l = J^T J (unit weights), ordered [rot(3), trans(3)], Schur blocks S_RR and S_tt (DCReg idea). Covered elsewhere (cited only): Zhang 2016 remapping, X-ICP kappa values, DCReg kappa_th=10.

## Q1. Is Switch-SLAM's semicircle/Chi-squared threshold (Eq. 11-12) mathematically valid, and does it transfer to Schur blocks?

### Takeaway
No, the derivation does not hold up statistically. The constant 0.103 is the **lower 5% quantile** of chi-squared with 2 DOF, not the 95% critical value (5.991) that the stated hypothesis test needs. The "expectations" e_m are midpoints of hand-picked ranges and do not come from the semicircle law. The test is also not a valid Pearson chi-squared test, because it uses one continuous observation and no counts. The threshold is in effect an empirical constant written in statistical language. Nothing in it is specific to Schur complements, so it gives no derived basis for S_RR or S_tt.

### Cited Findings
- **What Switch-SLAM actually does (verbatim, RA-L 2024, p. 7273):**
  - λ = [λ1, λ2, λ3] are "the three smallest values from the eigenvalues of H_l in ascending order", and λ is then normalized so that ‖λ‖ = 1. The text gives "the norm of λ is 1", meaning L2 normalization over those three values only.
  - The DOF is set to 2 "because λ is normalized to 1 and one value can be determined when the other two are observed."
  - Eq. 11 is (λ − e_m)²/e_m > 0.103, "where 0.103 denotes the Chi-squared value for 2-DOFs at a 95% confidence level."
  - Semicircle step: "According to [26], the eigenvalues distribution of a randomly constructed real symmetric matrix with finite dimensions can be approximated with a semicircle distribution [27]. Therefore … we assume that each distribution of λ follows a symmetric probability distribution."
  - Expectations: e1 = 1/(2√3) ≈ 0.289, the midpoint of [0, 1/√3]. e2 = 0.498, the midpoint of [e1, 1/√2], where e1 is called "the average minimum value". e3 = 0.749, the midpoint of [e2, 1].
  - Eq. 12 is λt = e_m − √(0.103·e_m), giving [0.12, 0.27, 0.48]. Switching to the visual initial guess happens if "any λ value is lower than the corresponding value of λt".
  - The paper calls this "non-heuristic … grounded in physical assumptions and statistical significance."
  - Source: [Lee et al., Switch-SLAM, RA-L 2024 (project file SwitchSLAM.pdf)](https://ieeexplore.ieee.org/document/10577209)
- **Numerical check (computed with scipy):**
  - χ²₂ CDF(0.1026) = 0.05, so 0.103 is the 5th percentile. The upper 95% critical value is χ²₂(0.95) = 5.991.
  - Thresholds with 0.103: [0.116, 0.271, 0.471]. The paper prints 0.48 for the third, which looks like a small rounding/arithmetic slip.
  - Thresholds with the correct 5.991: [−1.03, −1.23, −1.37]. These are all negative, so the rule would **never fire** for nonnegative λ.
  - Source: computation in this research session (inference from the standard χ² distribution; CDF of χ²₂ is 1 − e^(−x/2)), cross-checked against [Wikipedia, Chi-squared distribution](https://en.wikipedia.org/wiki/Chi-squared_distribution)
- DCReg (IJRR) uses a different kind of criterion, the condition number of the Schur blocks. Its Fig. 13 caption reads "detection thresholds set to 10". DCReg also notes that "translational eigenvalues consistently maintain lower magnitudes than rotational counterparts, resulting in persistently large eigenvalue ratios", which is why it rejects raw joint-spectrum thresholds. — [Hu et al., DCReg, arXiv 2509.06285 (project file)](https://arxiv.org/abs/2509.06285)
- The prior-work critique in Hatleskog & Alexis (2024) explains why fixed raw-eigenvalue thresholds cannot be universal: "eigenvalues depend on measurement count, weights, environment scale and sensor noise." — [Hatleskog & Alexis, Probabilistic Degeneracy Detection for Point-to-Plane Error Minimization, arXiv 2410.10784](https://arxiv.org/html/2410.10784v1)

### Inferences
These are my own analysis and are not stated in any paper.
1. **Wrong tail.** The paper says it rejects H0 "at a 5% significance level". That requires the statistic to exceed the **upper** quantile, 5.991. Using 0.103 means rejecting whenever the deviation is larger than what 95% of chi-squared draws would exceed. That rule is very liberal, not a 5% test. The fact that the "correct" threshold gives negative cutoffs shows the construction only produces usable numbers because of the wrong quantile.
2. **Not a Pearson test.** Pearson's χ² = Σ(O−E)²/E needs counts of categorical outcomes with expected counts of about 5 or more, and it sums over categories. Switch-SLAM applies it to a single continuous eigenvalue in [0,1], per component and without summing. Then (λ−e)²/e has no χ² distribution. Its scale is arbitrary: multiplying λ by 10 changes the statistic by 10x.
3. **The semicircle law does not apply.**
   - Wigner's semicircle law is an asymptotic (n→∞) result for symmetric matrices with i.i.d. zero-mean entries, so it allows negative eigenvalues.
   - H = JᵀJ is positive semidefinite and Wishart-like. Its asymptotic spectrum, if anything, would be Marchenko–Pastur, which is not symmetric.
   - The 6x6 size is far from asymptotic.
   - The semicircle is used only to justify "symmetric", which licenses taking midpoints. The midpoints themselves use an ad hoc "average minimum" for e2 and e3.
4. **DOF=2 reasoning does not hold.** The L2-norm constraint removes one degree of freedom from a 3-vector. But the test is applied per eigenvalue, each with its own threshold, not as a joint 3-cell statistic. So "DOF" has no role in a per-component rule.
5. **It does not transfer to Schur blocks.** The e_m were derived for the three smallest of six eigenvalues of the joint H, re-normalized. For S_RR and S_tt, the code uses all three eigenvalues of a 3x3 matrix. Nothing in the derivation depends on the source matrix, so applying it to Schur blocks is neither more nor less justified than the original. In both cases the triple [0.12, 0.27, 0.48] is an empirical shape test on the normalized spectrum.
6. **What the rule actually measures.** It is effectively a test on the *normalized eigenvalue shape*, which is scale-free within a block. Scale-free tests cannot detect uniform weakness. If all three directions are equally weak (for example very few correspondences), the normalized spectrum looks "healthy". This is also a property of condition-number tests such as DCReg's κ>10.

### Gaps
- I did not locate public Switch-SLAM code to confirm whether the implementation uses √(0.103·e_m) or √0.103·e_m. Only √(0.103·e_m) reproduces the printed numbers.
- I found no published critique of Switch-SLAM Eq. 11–12 in the literature. The critique above is original analysis.

## Q2. Physically derived (unit-bearing) thresholds via covariance/CRLB, and confirmation of the Schur/marginal-covariance identity

### Takeaway
The identity (S_tt)⁻¹ = [H⁻¹]_tt is standard. So with Gaussian residual noise σ, the Schur-block eigenvalues λ_i(S) give predicted marginal standard deviations σ/√λ_i, in metres for S_tt and radians for S_RR. These can be compared with a physical tolerance. This is the most defensible derivation available for A-LOAM's setup. Two caveats apply:
- The Hessian/CRLB covariance is known to be overoptimistic for ICP. Brossard et al. report a ~13x trace gap in one example, and Censi's formula is "widely considered as overoptimistic."
- The tolerance itself (for example 5 cm or 1°) is an application requirement, not something derived.

### Cited Findings
- **Block-inverse identity.** The Schur complement "is the inverse of the block entry of the inverse of" M: [M⁻¹]₂₂ = (D − C A⁻¹ B)⁻¹. For a Gaussian, the conditional covariance is a Schur complement of the covariance matrix. The dual statement is that the Schur complement of the *information* matrix is the marginal information. References given: Boyd & Vandenberghe, *Convex Optimization* (2004); von Mises (1964). — [Wikipedia, Schur complement](https://en.wikipedia.org/wiki/Schur_complement)
  - Applied here: with H = [[H_RR, H_Rt],[H_tR, H_tt]], [H⁻¹]_tt = (H_tt − H_tR H_RR⁻¹ H_Rt)⁻¹ = S_tt⁻¹, and likewise for rotation. (Standard result; also in Golub & Van Loan and Barfoot, *State Estimation for Robotics*. I did not fetch page numbers for those books.)
- **DCReg's own propositions:**
  - Theorem 1: κ(S_R) and κ(S_t) bound "relative error amplification". S_R is "precisely the Hessian of the rotation subproblem after optimally accommodating translation".
  - Proposition 1: S_R = J_Rᵀ(I − P_t)J_R, with weighted form S_R = J_RᵀW(I − P_t^(W))J_R.
  - Theorem 2: S_R ⪯ H_RR and λ_i(H_RR) − λ_max(M_R) ≤ λ_i(S_R) ≤ λ_i(H_RR).
  - Theorem 4 interprets clamping as MAP with prior φ ~ N(0, Γ_R⁻¹).
  - Source: [DCReg, arXiv 2509.06285](https://arxiv.org/abs/2509.06285)
- **CRLB form.** Under Gaussian residuals with std σ, the Fisher information is JᵀJ/σ², and the CRLB is cov ⪰ (JᵀJ/σ²)⁻¹. Along an eigenvector v_i of S_tt, the predicted marginal std is σ/√λ_i. — [Wikipedia, Cramér–Rao bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_bound); Censi applied CRLB to range-finder localization in [Censi, "On achievable accuracy for range-finder localization", ICRA 2007](https://ieeexplore.ieee.org/document/4209738/). I did not access its full text, so no equation numbers.
- **Overoptimism of Hessian covariance (Brossard, Bonnabel, Barrau, RA-L 2020):**
  - "closed-form expressions … whose underlying assumption consists in linearizing the objective function used in ICP around the convergence point, ruling out the possibility for wrong convergence"
  - "Censi's pioneering formula [1] is widely considered as overoptimistic"
  - Their model (Eq. 13): Q_icp = (I₆ − J)Q_ini(I₆ − J)ᵀ + G Q_sensor Gᵀ, which adds an initialization/wrong-convergence term.
  - Example: "A⁻¹ has trace 0.2 cm … whereas the covariance w.r.t. the unknown bias has trace 2.6 cm", roughly a 13x underestimate. They add a sensor-bias term A⁻¹B cov(b)Bᵀ A⁻¹ (Eq. 17).
  - Source: [Brossard et al., A New Approach to 3D ICP Covariance Estimation, arXiv 1909.05722](https://arxiv.org/pdf/1909.05722)
- **Noise-model-derived probabilistic detector (Hatleskog & Alexis, 2024):**
  - Point noise p̂_i = p_i + ε_i, ε_i ~ N(0, Σ_p) (Eq. 7). Normal noise n̂_i ≈ n_i + [n_i]×η_i (Eq. 8). Then E[Ĥ] = H + Σ (Eq. 15), and directional variance σ_u² = Σ_i cov(uᵀv̂_i v̂_iᵀu) (Eq. 16).
  - Decision: p_u = P(a_u ≥ s·ξ_u) (Eq. 20), with s = 10 "to target a relative error of at most 10%". σ_p comes from the LiDAR datasheet (e.g., 1 cm).
  - Their parameter is a relative-error target, not a fitted eigenvalue cutoff. This is the closest published "first-principles" detector found.
  - Source: [Hatleskog & Alexis, arXiv 2410.10784](https://arxiv.org/html/2410.10784v1)
- **Gelfand et al. 2003** define the 6x6 "covariance" C = Σ[(p×n);n][(p×n);n]ᵀ. They relate it to error change via ΔE = [Δω Δt] C [Δω Δt]ᵀ and use κ(C) as the stability measure, aiming "to keep κ as close to 1 as possible". No numeric κ threshold is given. — [Gelfand et al., Geometrically Stable Sampling for ICP, 3DIM 2003](https://graphics.stanford.edu/papers/stabicp/)

### Inferences
1. **Recommended derivation for the thesis (inference).** Define σ_t,max = σ/√λ_min(S_tt) [m] and σ_R,max = σ/√λ_min(S_RR) [rad]. Declare a block degenerate if σ_t,max > τ_t or σ_R,max > τ_R, equivalently λ_min(S_tt) < (σ/τ_t)². This rule has three properties:
   - It is derived: CRLB plus the block-inverse identity give an exact marginal std under the linear-Gaussian model.
   - It carries units and is frame-consistent within each block. Rotation can be checked in any rotated basis because the spectrum is invariant under Q ∈ SO(3) (DCReg Prop. 2(ii)).
   - It needs two physically meaningful inputs: residual noise σ (from the datasheet or the empirical residual RMS after convergence) and tolerance τ (from a downstream requirement, for example map resolution or VO-handover accuracy).
2. **Units in A-LOAM.** With unit weights, A-LOAM's residuals are point-to-line and point-to-plane distances in metres. So σ is in metres, S_tt is dimensionless (m/m per m of translation), and S_RR has units of m². Then σ/√λ(S_RR) is in rad (my dimensional analysis).
3. **Correction for overoptimism.** Because the CRLB is overoptimistic, one of these is needed:
   - Inflate σ, for example using the post-convergence residual RMS (which absorbs model error), or a factor justified from Brossard's 13x trace example.
   - State that the test is a *necessary* condition: if even the optimistic bound exceeds the tolerance, the direction is certainly poorly constrained. This conservative direction is defensible.
4. **σ/√λ versus κ(S).** σ/√λ_min catches uniform weakness, which κ(S) misses. κ(S) catches anisotropy regardless of absolute level. A combined rule is possible, but the absolute rule is the one with a derivation.

### Gaps
- No primary source was found that uses exactly "marginal std along a Schur-block eigenvector greater than a metric tolerance" as a LiDAR degeneracy flag. CELLO-3D (Landry 2019), Nubert's learned localizability, and Bonnabel 2016 were not fetched (tool budget), so their specific numbers are not reported.
- The page and equation numbers for Barfoot, Kay, and Golub & Van Loan were not retrieved.

## Q3. The units/scale problem and the frame-dependence problem

### Takeaway
Rotation and translation eigenvalues of the joint 6x6 are incommensurable: the rotational block carries m² relative to the translational block. Papers that state this:
- DCReg, which resolves it with Schur blocks and proves invariance to rescaling the eliminated variable.
- 2608.15532, which says even per-block and characteristic-length fixes are frame-dependent and proposes a generalized eigenproblem H v = λ M v with point-displacement metric M, giving dimensionless λ ∈ [0,1]. Its threshold τ = 10⁻² is still empirical.

Gelfand 2003 handles units by rescaling points to unit mean radius. Hinduja 2019 uses a plain λ_max/λ_min without addressing units.

### Cited Findings
- **DCReg Prop. 2.** (i) If δt′ = s δt, so that H_tt ↦ s²H_tt and H_Rt ↦ sH_Rt, then S′_R = S_R. (ii) Orthogonal basis change gives S_R ↦ QᵀS_RQ, which preserves the spectrum. Also: "Schur complements naturally eliminate sensitivity to unit or scale changes in the eliminated parameters, directly addressing the scale disparity between rotation (radians) and translation (meters)… More general (non-orthogonal) re-parameterizations do not necessarily preserve the condition number." — [DCReg](https://arxiv.org/abs/2509.06285)
- **2608.15532, "Degenerate in Whose Frame? An Equivariance Condition for Degeneracy Detection in LiDAR Registration"** (Zhang, Zhao, Lin, Guo, Jia, Liu, 2026):
  - "The information matrix … has a rotational block with units of m² relative to its translational block. Its six eigenvalues are therefore not commensurable: changing the length unit can reorder them and alter any raw spectral threshold."
  - Under a body-frame change, H′ = AᵀHA (Eq. 6, A the adjoint). This is "not a similarity". "Congruence preserves nullity … the per-axis footprint and a thresholded spectrum need not be invariant."
  - In a circular tunnel, shifting the origin by 1 m changes which DOFs are flagged.
  - A rig-adapted constant metric exists iff eᵀd = 0 (zero screw pitch). This holds in only 1 of 19 surveyed calibrations.
  - The characteristic-length metric M = diag(ℓ²I₃, I₃) fails the equivariance condition.
  - Remapping corrections differ between body frames on 44.5–69.5% of pairs, with median 0.7–4.0 mm and maximum 0.87 m.
  - Recommendation: the point-displacement metric M = Σ J_iᵀJ_i (Eq. 11), where ξᵀMξ = Σ‖δp_i‖². Solve H v = λ M v (Eq. 9) with H = Σ J_iᵀ n_i n_iᵀ J_i. Since ‖n_i‖ = 1, λ ∈ [0,1], read as "the fraction of induced surface displacement that the point-to-plane residual observes".
  - The threshold τ = 10⁻² is **empirical**. It comes from synthetic corridors, where the interval reproducing the expected flag counts was [5.3×10⁻³, 8.3×10⁻²], and 10⁻² was picked as a "round" value.
  - The paper has no CRLB discussion and only cites DCReg.
  - Sources: [arXiv 2608.15532 (abs)](https://arxiv.org/abs/2608.15532); [HTML](https://arxiv.org/html/2608.15532)
- **Gelfand 2003.** Center the points and "scale the point set so that the average distance of points from the origin is 1", so that rotational and translational displacements are comparable. The criterion is κ(C), with no numeric threshold. — [Gelfand et al. 2003](https://graphics.stanford.edu/papers/stabicp/)
- **Hinduja et al. IROS 2019.** "Similar to [13] we use the condition number, i.e. the ratio between the maximum and minimum eigenvalues … as our eigenvalue threshold". It is computed on the full AᵀA, with no documented rotation/translation split and no units discussion. The threshold is environment-dependent: "different types of environments benefit from different threshold values", and automatic selection is left to future work. It builds on Zhang et al.'s remapping. So it is empirical. — [Hinduja et al., Degeneracy-Aware Factors with Applications to Underwater SLAM, IROS 2019](https://www.cs.cmu.edu/~kaess/pub/Hinduja19iros.pdf)

### Inferences
1. Per-block Schur analysis removes the cross-unit problem. Within S_tt everything is in one unit, and S_tt is invariant to rotating the translation basis. But under a change of body origin (lever arm), translation and rotation mix through the adjoint. So S_tt's spectrum can change while S_RR's does not.
   - Reasoning (my inference): translation of the origin by d maps δt′ = δt + d×δφ. This is a non-orthogonal reparameterization. DCReg itself says such reparameterizations "do not necessarily preserve the condition number".
   - Practical consequence: the thesis should fix and report the frame, for example the LiDAR frame as in A-LOAM, and acknowledge 2608.15532's critique.
2. The σ/√λ physical rule from Q2 is subject to the same frame issue for the translation block, since marginal translation std depends on the reference point. It is internally consistent once the frame is fixed. Rotation-block marginal std is frame-invariant under origin shifts (inference: rotation is unchanged by the adjoint's translation part).
3. 2608.15532's metric gives a dimensionless, frame-equivariant λ, but its threshold is still tuned. So it fixes the frame/units problem but not the derivation problem.

### Gaps
- Gelfand's exact equation numbers for the scaling step were not confirmed beyond the summary.
- I did not verify whether Hinduja uses a "relative" condition number distinct from λ_max/λ_min. The fetched text shows only λ_max/λ_min.
- I did not verify the Switch-SLAM public code, or the thresholds in LiLi (arXiv 2609.17145) and LF-GICP (2608.19522), which appeared in search results as possibly related "parameter-free" detectors.
