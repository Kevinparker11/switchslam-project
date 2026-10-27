# Replacing heuristic thresholds with provable degeneracy decisions

**Bottom line.** None of the thesis's current degeneracy components survives scrutiny as written. The final design keeps one borrowed idea, DCReg's Schur decoupling into S_RR and S_tt ([DCReg](https://arxiv.org/abs/2509.06285)), and replaces everything around it with pieces that each have a derivation:

- **D1, detection:** a per-eigen-direction test in two parts. (a) An upper-tail significance test against the information that plane-normal noise manufactures. (b) A precision test in metres and radians that follows from the block-inverse identity and the Cramér–Rao bound.
- **D2, Channel T:** deleted. It is exactly H_tt/N.
- **D3, scalar `conf`:** deleted. A scalar cannot represent directional degeneracy.
- **D4, fusion:** projected, information-scaled covariance intersection.
- **D5, visual channel:** VINS-Mono's real failure criteria, with no invented visual threshold.
- **D6, switching:** a Bernoulli CUSUM replaces the 5-frame buffer.
- **D7, backend:** implemented or explicitly scoped out.
- **D8, DCReg:** described honestly as detection-only.
- **D9, validation:** detector-independent ground truth, NEES calibration and forced-mode ablations.

The strongest evidence comes from a synthetic point-to-plane ICP simulation, not from real sensors. In it, the chosen detector flags 0.998 of truly degenerate corridor frames and 0.000 of well-constrained frames. The Switch-SLAM semicircle rule, DCReg's κ>10 and Channel T's λ3<0.15 each flag 1.000 of all three scenes, so they cannot tell the scenes apart. That matches the real Gazebo log, where Channel R fired on about 80% of frames. The same simulation shows why part (a) is essential: the raw Hessian is roughly 6× overconfident in standard deviation in a corridor (ANEES 48.25 against a consistent band of [2.67, 3.35]), so a CRLB-only threshold misses every degenerate frame. These results support the derivations. They do not replace Gazebo and real-dataset validation, which the D9 protocol specifies.

**Provenance tags used throughout.**
- **[Published]**: stated in a cited paper or in released code.
- **[Project derivation]**: this project's own mathematics, which a reviewer can check step by step.
- **[Synthetic simulation]**: the coordinator's Python Monte Carlo (`/mnt/user-data/outputs/verify_final_methods.py`, output in `verify_final_methods_output.txt`, 5 seeds). It is never a substitute for real-sensor validation.

## One-table summary of all nine decisions

| Component | What the project did | Final method | Proof basis | Evidence | Remaining limitation |
|---|---|---|---|---|---|
| D1 LiDAR detection | Switch-SLAM semicircle thresholds [0.12, 0.27, 0.48] on L2-normalized eigenvalues of both Schur blocks S_RR, S_tt (κ>10 also referenced) | Keep Schur blocks. Per eigen-direction v: (a) upper-tail Satterthwaite χ² test of λ_v against normal-noise information, α = 0.05; (b) precision test σ_r/√(λ_v − μ_v) ≤ τ. Degenerate if (a) OR (b) fails | [Published] block-inverse identity, CRLB, DCReg Prop. 2. [Project derivation] noise-floor null distribution and the critique of Switch-SLAM's χ² tail | [Synthetic] flags 0.998 corridor, 0.000 corridor_doors, 0.000 open_80_10_10. Semicircle, κ>10 and λ3<0.15 flag 1.000 everywhere | Only as good as the noise model; must be NEES-checked on Gazebo/real data. S_tt is frame-dependent. τ is an application requirement |
| D2 Channel T | Orientation tensor T of PCA normals (k=12, ≤400 pts), degenerate if λ3 < 0.15; Bingham test proposed | Remove as an independent channel. If a correspondence-free predictor is wanted, apply the D1 test to the scan's own points and normals | [Published] H_tt = Σ n nᵀ (Gelfand 2003; Low 2004). [Project derivation] the consequences | [Synthetic] max \|H_tt − N·T\| = 0. λ3 = 0.104 and 0.093 in well-constrained scenes. Bingham B = 89–3849 everywhere vs 11.07 | No aliasing detector remains; aliasing is future work |
| D3 Confidence | conf = clip((chanR_r + chanR_t + 2·chanT)/4, 0.3, 1.0), logged and unused; no visual conf exists | Remove. The only defensible scalar is CI's optimized ω inside D4 | [Project derivation] cH has the same eigenvectors and condition number as H | [Synthetic] scalar-conf fusion 1.172 cm RMSE vs 0.713 cm for projected fusion | None beyond D4's |
| D4 Fusion | (H_l + H_v)⁻¹(H_l d_l + H_v d_v), unscaled; called Switch-SLAM Eq. 15 but is not | δ = (ω I_l^p + (1−ω) I_v)⁻¹(ω I_l^p d_l + (1−ω) I_v d_v), with I_l = H_l/σ_l², I_l^p = projection onto D1-passing directions, ω = argmin det P | [Published] Gauss–Markov/BLUE; CI consistency (Julier & Uhlmann 1997); CI optimality (Reinhardt et al. 2015); Zhang 2016 projection | [Synthetic] RMSE 1.189 (code) → 0.713 cm. With correlation 0.6: BLUE ANEES 7.03 (overconfident) vs CI 4.47 (consistent, bound 6.11) | Requires extracting VINS-Mono marginal information; stylized magnitudes |
| D5 Visual | "VO fail" = features < 20 OR jump > 1.5 m OR > 0.8 rad, attributed to VINS-Mono | Hard-failure flag = VINS-Mono's actual criteria (acc-bias > 2.5, gyro-bias > 1.0, jump > 5 m, z-jump > 1 m). No visual threshold; vision enters via I_v. Optional, labelled novel: relative-pose information-gain test | [Published] VINS-Mono code; Switch-SLAM Sec. III-D; Wu & Roumeliotis | Code inspection (no simulation) | VINS-Mono constants are empirical; no derived visual test exists in the literature |
| D6 Switching | 5-frame status buffer: Normal / Transition / Fully, √(3λ1) blend | Two-sided Bernoulli CUSUM on the D1 verdict; threshold h set by in-control ARL0 | [Published] Page 1954; Lorden 1971; Moustakides 1986 (via Basseville & Nikiforov) | [Synthetic] buffer: 22.0% of normal frames in Transition, delay 5.99. CUSUM: 0.06% false flags, delay 2.27, ARL0 3019 | a and b must be measured on labelled data |
| D7 Backend | Not implemented | Implement iSAM2 odometry factors with the D4 pose and P, or scope out explicitly | CI covariance is consistent, so it is safe as a factor | None | Thesis claims must match the scope |
| D8 DCReg mitigation | DCReg cited, but its PCG mitigation is not used | State honestly: DCReg detection math only. Mitigation = D4 projection (Zhang 2016 lineage) | [Published] Zhang 2016; DCReg Thm. 4 for comparison | Covered by D4 | None (documentation) |
| D9 Validation | Random SPD Hessians, one seed, ground truth = detector threshold (circular); one-run per-mode mean error | Geometry-defined Gazebo ground truth, Wilson CIs with n ≥ 1068, NEES calibration, held-out threshold sweeps, forced-mode ablations, GEODE/SubT-MRS | [Published] Sturm 2012; Zhang & Scaramuzza 2018; Bar-Shalom NEES; Brown–Cai–DasGupta; arXiv 2608.15532 protocol | [Synthetic] Wilson half-widths: n=400 → ±0.049, 1068 → ±0.030 | Real experiments not yet run |

## D1: A two-part, unit-bearing test replaces the semicircle threshold

### What was wrong

The switching node L2-normalizes the three eigenvalues of each Schur block and compares them with Switch-SLAM's thresholds [0.12, 0.27, 0.48]. The rule rests on four errors.

**Wrong tail [Project derivation].** Switch-SLAM writes (λ − e_m)²/e_m > 0.103 and calls 0.103 "the Chi-squared value for 2-DOFs at a 95% confidence level" ([Switch-SLAM, Lee et al., RA-L 2024](https://doi.org/10.1109/LRA.2024.3421792)). The χ²₂ CDF is 1 − e^(−x/2), so CDF(0.103) = 0.0502: **0.103 is the lower 5% point**. A test at the 5% significance level needs the upper point, 5.991. Substituting 5.991 into Eq. 12, λt = e_m − √(5.991·e_m), gives thresholds **[−1.026, −1.229, −1.369]**. These are all negative, so the rule could never fire on nonnegative eigenvalues. With 0.103 the exact thresholds are [0.116, 0.271, 0.471]; the paper prints 0.48 for the third. **We found no published critique of Eq. 11–12. This is the project's own analysis and must be presented as such.**

**Not a χ² statistic [Project derivation].** Pearson's statistic needs categorical counts summed over cells. A single continuous eigenvalue in [0, 1] plugged into (λ−e)²/e has no χ² distribution, and the statistic's scale is arbitrary.

**The semicircle law does not apply.** It is an asymptotic result for symmetric matrices with independent zero-mean entries. JᵀJ is positive semidefinite and 6×6. The expectations e_m are hand-picked midpoints, not quantities derived from the law.

**Scale-free tests miss uniform weakness.** A normalized spectrum, like κ, cannot see that all three directions are equally weak.

Borrowed alternatives are equally empirical:
- DCReg's κ>10 and minimum-eigenvalue 120 come from a sweep ([DCReg](https://arxiv.org/abs/2509.06285)).
- X-ICP uses κ = 250/180/35, while Tuna et al. 2025 use 300/150/45 ([X-ICP](https://arxiv.org/pdf/2211.16335); [Tuna et al.](https://arxiv.org/pdf/2408.11809)).
- Zhang 2016 places its threshold "at the mid-point of the margin" between test scenes ([Zhang, Kaess, Singh 2016](https://frc.ri.cmu.edu/~zhangji/publications/ICRA_2016.pdf)).

### Final method (exact equations)

Notation: H_l = JᵀJ, ordered [rotation; translation], blocks H_RR, H_Rt, H_tt.

```
S_RR = H_RR − H_Rt H_tt⁻¹ H_tR          S_tt = H_tt − H_tR H_RR⁻¹ H_Rt
σ_r² = rᵀr / (m − 6)                       (converged residuals, m correspondences)

For every eigenpair (λ_v, v) of S_tt and of S_RR:
  a_i = v               (translation block)
  a_i = v × p_i         (rotation block)
  C_i = Σ_j  s²/(k·l_j,i) · t_j,i t_j,iᵀ   (j over the 2 tangent directions of fit i, k = 5)
  s²  = Σ_i k·l_3,i / Σ_i (k − 3)          (pooled point-noise variance)
  c_i = a_iᵀ C_i a_i
  μ_v = Σ c_i ,  g = Σ c_i² / Σ c_i ,  h = (Σ c_i)² / Σ c_i²

  (a) significance:  constrained only if  λ_v > g · χ²_{h, 1−α},   α = 0.05
  (b) precision:     constrained only if  σ_r / √(λ_v − μ_v) ≤ τ   (τ_t in m, τ_R in rad)

  v is DEGENERATE if (a) fails OR (b) fails.  Report which v.
```

### Derivation, step by step

**Step 1: Schur blocks are marginal information [Published].** For a symmetric positive definite H in 2×2 block form, the block-inverse formula gives [H⁻¹]_tt = (H_tt − H_tR H_RR⁻¹ H_Rt)⁻¹ = S_tt⁻¹, and likewise [H⁻¹]_RR = S_RR⁻¹ ([Schur complement](https://en.wikipedia.org/wiki/Schur_complement)). The simulation confirmed this over 5000 random H to a maximum relative difference of **1.16e-15** (S1).

**Step 2: CRLB along an eigenvector [Published].** With residual noise N(0, σ_r²), the Fisher information is JᵀJ/σ_r² and Cov(x̂) ⪰ σ_r² H⁻¹ ([Cramér–Rao bound](https://en.wikipedia.org/wiki/Cram%C3%A9r%E2%80%93Rao_bound)). By Step 1, the marginal translation covariance is σ_r² S_tt⁻¹. If S_tt = Σ λ_v v vᵀ, the variance along v is σ_r²/λ_v, so the predicted standard deviation is σ_r/√λ_v. The same holds for rotation with S_RR.

**Step 3: units [Project derivation].** A-LOAM residuals are distances in metres.
- S_tt has units of (m/m)², so σ_r/√λ is in metres.
- S_RR has units of m², so σ_r/√λ is in radians.

DCReg Prop. 2 shows that the S spectrum is invariant to rescaling the eliminated block and to orthogonal basis changes. This is why per-block thresholds are unit-consistent ([DCReg](https://arxiv.org/abs/2509.06285)).

**Step 4: why the CRLB alone fails, because noise manufactures information [Project derivation].** Consider a corridor along x. Every true plane normal satisfies n_i·e_x = 0, so the true information along x is zero. A-LOAM, however, uses normals n̂_i = n_i + e_i fitted from k = 5 map points. The Jacobian's translation row along v = e_x becomes n̂_i·v = e_i·v, which is nonzero. So λ_v = Σ (e_i·v)² > 0 even though the geometry provides nothing. For the rotation block, the row is v·(p_i × n̂_i). By the cyclic scalar triple product this equals n̂_i·(v × p_i). Under H0 the true part n_i·(v × p_i) is zero, leaving e_i·(v × p_i). In both cases the spurious row is a_iᵀ e_i, with a_i = v or a_i = v × p_i.

**Step 5: noise covariance of a fitted normal [Project derivation].** A PCA plane fit to k points is a linear regression of the out-of-plane coordinate on the two in-plane coordinates. The slope (normal tilt) toward tangent t_j has variance s²/Σx_j² = s²/(k·l_j), where l_j is the scatter eigenvalue along t_j (scatter normalized by k). The residual sum of squares of the fit is k·l_3 with k − 3 degrees of freedom (three plane parameters). A single 5-point fit therefore estimates s² from only 2 degrees of freedom. Pooling over all correspondences, s² = Σ k·l_3,i / Σ(k − 3), uses thousands. This gives C_i = Σ_j s²/(k l_j,i) t_j t_jᵀ.

**Step 6: null distribution [Project derivation, standard result].** Under H0 ("v carries no true information"), a_iᵀ e_i ~ N(0, c_i) with c_i = a_iᵀ C_i a_i, so λ_v = Σ c_i z_i² with z_i ~ N(0, 1) independent. This is a weighted sum of χ²₁ variables, with mean Σ c_i and variance 2Σ c_i². The Satterthwaite (1946) approximation λ_v ≈ g·χ²_h matches both moments:
- From g·h = Σc and 2g²h = 2Σc², we get g = Σc²/Σc and h = (Σc)²/Σc².

H0 is rejected (the direction is really constrained) only when λ_v exceeds the **upper** α point g·χ²_{h,1−α}. This is the correctly tailed version of the test Switch-SLAM attempted.

**Step 7: bias-corrected precision [Project derivation].** The measured information is λ_v = (true information) + (noise information), and E[noise information] = μ_v = Σ c_i. The unbiased estimate of true information is λ_v − μ_v. Applying Step 2 gives the predicted standard deviation σ_r/√(λ_v − μ_v). Compare it with τ_t (metres) or τ_R (radians). The τ values are application requirements, for example the per-frame error the VO handover can tolerate. They are not tuned constants. The simulation used τ_t = 0.10 m and τ_R = 1°.

**Step 8: combining.** Part (a) asks whether there is any real information. Part (b) asks whether there is enough. A direction failing either is degenerate. Because the test is applied to the minimum eigenvector, which is selected from the same data, the selection bias makes the test conservative: it is more likely to call a direction degenerate.

### Why the alternatives were rejected

- **Semicircle rule:** wrong tail, not a χ² statistic, and an inapplicable law. Each published κ or min-eigenvalue threshold moves between papers and sensors, and κ is blind to uniform weakness.
- **Hatleskog & Alexis (2024, IEEE RA-L 9(12):11234–11241, DOI 10.1109/LRA.2024.3484153):** the closest published first-principles precedent. They propagate datasheet point and normal noise into E[Ĥ] = H + Σ and decide with s = 10 ([arXiv 2410.10784](https://arxiv.org/html/2410.10784v1)). D1 follows the same philosophy but uses a residual-estimated noise level and a stated significance level.
- **Frame-equivariant generalized eigenproblem (arXiv 2608.15532):** fixes the frame and unit problem, but its τ = 10⁻² is still tuned ([Degenerate in Whose Frame?](https://arxiv.org/html/2608.15532)). It is cited as an alternative, not adopted.

### Numerical evidence [Synthetic simulation]

**Setup (S4).** Real nearest-neighbour point-to-plane ICP with correspondences re-associated each iteration:
- a 0.4 m voxel map built like A-LOAM's planar map, with k = 5 plane fits and the 5th neighbour within 1 m;
- σ_p = 0.02 m, N = 1500 points;
- initial-guess error 0.20 m / 1°, 12 iterations;
- 200 runs × 5 seeds per scene.

Three scenes:
- **corridor:** truly degenerate along x;
- **corridor_doors:** 10% of points on cross walls, well constrained;
- **open_80_10_10:** 80% ground, 10% each of two walls, well constrained.

| Detector (fraction of frames flagged) | corridor (degenerate) | corridor_doors (ok) | open_80_10_10 (ok) |
|---|---|---|---|
| **Chosen (a)+(b)** | **0.998 ± 0.002** | **0.000** | **0.000** |
| CRLB tolerance only | 0.000 | 0.000 | 0.000 |
| Switch-SLAM semicircle on S | 1.000 | 1.000 | 1.000 |
| DCReg κ(S) > 10 | 1.000 | 1.000 | 1.000 |
| Channel T λ3 < 0.15 | 1.000 | 1.000 | 1.000 |

**Calibration.**
- **Corridor:** the empirical standard deviation along the weakest direction is **12.96 cm**, while the raw CRLB predicts **2.08 cm**. Translation ANEES is **48.25 ± 1.79** against a consistent band of **[2.67, 3.35]**. The Hessian is about 6× overconfident in standard deviation because normal noise manufactures information, so the CRLB-only test misses every corridor frame.
- **Well-constrained scenes:** the CRLB is only mildly overconfident (ANEES 4.74 and 3.76 against 3). An inflation factor should therefore be calibrated from Gazebo NEES before τ is used.

**Noise-model sensitivity** (recorded in the coordinator's evidence file, not in the output file). A first variant that estimated s² per 5-point fit underestimated the noise information by about 2× and missed the corridor. Pooling fixed it: the corridor's λ_min of 2.5 falls below its threshold of 4.2, while constrained scenes sit near 130 against thresholds of about 7–9.

### Limitations

**The test is only as good as the noise model.** A-LOAM must publish per-correspondence p_i, the fitted normal, and the scatter eigenpairs or C_i, plus final residuals.

**S_tt depends on the frame.** Moving the body origin by d gives δt′ = δt + d × δφ, which changes the S_tt spectrum but not the S_RR spectrum ([arXiv 2608.15532](https://arxiv.org/html/2608.15532)). Fix the A-LOAM LiDAR frame and state this.

**Satterthwaite is a two-moment approximation.** The simulation shows only that it works on three planar scenes. It is not proof on real data.

## D2: Channel T is the Hessian's translation block divided by N

### What was wrong

Channel T computes T = (1/N) Σ n nᵀ from PCA normals (k = 12, ≤ 400 points) and flags degeneracy when λ3 < 0.15. The threshold was labelled "empirical", has no periodicity term, and a Bingham test was proposed to back it.

### Final method

**Remove Channel T as an independent channel.** If a correspondence-free, pre-registration predictor is still wanted, apply the **same D1 test** to the scan's own points and normals (Gelfand stability analysis). This introduces no new constant. Aliasing detection becomes labelled future work.

### Proof

1. **Jacobian [Published].** The point-to-plane residual is r_i = n_iᵀ(R p_i + t − q_i). Linearized in [δφ; δt], its Jacobian row is [(p_i × n_i)ᵀ, n_iᵀ] ([Gelfand et al. 2003](https://graphics.stanford.edu/papers/stabicp/stabicp.pdf); [Low 2004](https://www.comp.nus.edu.sg/~lowkl/publications/lowk_point-to-plane_icp_techrep.pdf)).
2. **Translation block.** With unit weights, H_tt = Σ n_i n_iᵀ = N·T exactly. The simulation gives a maximum |H_tt − N·T| of **0** (S1).
3. **Not independent.** Channel T therefore carries no information that Channel R lacks. It is H_tt without the rotation coupling Σ(p × n)nᵀ, which S_tt includes. Voting "R and T" double-counts one quantity.
4. **Dividing by N discards the amount of information.** λ3(T) = λ_min(H_tt)/N is a fraction. A direction constrained by 10% of 1500 normals is well observed, yet its λ3 ≈ 0.1. In S3 the well-constrained scenes have **λ3 = 0.104** (corridor_doors) and **0.093** (open_80_10_10), so λ3 < 0.15 false-alarms. In S4 it flagged **1.000** of frames in both well-constrained scenes.
5. **Bingham tests the wrong hypothesis [Published + Project derivation].**
   - The Bingham statistic for axial data on S² is B = (n·p(p+2)/2)(tr S² − 1/p). With p = 3 this is (15N/2)(tr T² − 1/3), asymptotically χ²₅ under H0: normals uniform on the sphere ([García-Portugués & Verdebout survey](https://arxiv.org/pdf/1804.00286); [Vollmer 1990](https://www2.newpaltz.edu/~vollmerf/papers/Vollmer_1990_GSAB.pdf)).
   - Because Σλ_i = 1, Σ(λ_i − 1/3)² = Σλ_i² − (2/3)Σλ_i + 1/3 = tr T² − 1/3. So **B = (15N/2) Σ(λ_i − 1/3)²**. The project's earlier "15N" is off by a factor of 2.
   - For any fixed non-uniform population, Σ(λ_i − 1/3)² is a positive constant, so B grows linearly with N and always rejects.
   - S3: **B = 89–3849** across all scenes and N = 100/400/1600, against a critical value of **11.07**. It rejects for degenerate and well-constrained scenes alike.
   - Rejecting uniformity says nothing about whether λ3 ≈ 0.
6. **Aliasing claim unsupported.** Any second-moment tensor is blind to periodicity: a smooth corridor and a periodic-panel corridor can have identical T. Aliasing means a multi-modal cost (discrete ambiguity), not a rank-deficient Hessian. The earlier "Scenario 2 Part B" validated a concentration × periodicity score that is not in the deployed code.

### Alternatives rejected

- **Woodcock or Vollmer fabric indices:** shape descriptors without a noise-aware cutoff ([Vollmer 1990](https://www2.newpaltz.edu/~vollmerf/papers/Vollmer_1990_GSAB.pdf)).
- **LF-GICP's λ_min/tr:** has the same N-normalization problem. It is known only from a third-party summary ([Pith review](https://pith.science/paper/2608.19522)).

### Limitations

No aliasing detector remains. A cost or autocorrelation profile along weak directions is a proposal, and no dedicated LiDAR literature was found for it.

## D3: No scalar can encode directional degeneracy

### What was wrong

conf = clip((chanR_r + chanR_t + 2·chanT)/4, 0.3, 1.0) is logged but not used. The weights (1, 1, 2), the /4 and the [0.3, 1] clip have no derivation. There is no visual confidence anywhere in the code, and the proposed bilateral fusion (c_L H_l + c_V H_v)⁻¹(c_L H_l d_l + c_V H_v d_v) has no proof.

### Final method

**Remove conf, conf_L and conf_V.** Visual trust enters only through the information matrix I_v. The only scalar retained is covariance intersection's ω, chosen by optimization in D4.

### Proof [Project derivation]

1. **Scaling preserves geometry.** Let H = UΛUᵀ. Then cH = U(cΛ)Uᵀ: same eigenvectors, and condition number (cλ_max)/(cλ_min) = κ. A scalar rescales all six DOF equally, so it cannot down-weight a degenerate x-translation without equally discarding valid information in the other five DOF.
2. **The bilateral mean depends only on a ratio.** Multiplying c_L and c_V by a common factor k leaves (kc_L H_l + kc_V H_v)⁻¹(kc_L H_l d_l + kc_V H_v d_v) unchanged. Writing ω = c_L/(c_L + c_V), the bilateral form equals (ωH_l + (1−ω)H_v)⁻¹(ωH_l d_l + (1−ω)H_v d_v). This is exactly the **covariance-intersection mean**.
3. **Conditions for the scalar to be defensible.** The bilateral form is legitimate only if three things hold:
   - H_l and H_v are on a common information scale;
   - ω ∈ [0, 1];
   - ω minimizes det or trace of the fused covariance ([fusion notes; Reinhardt et al.](https://isas.iar.kit.edu/pdf/SPL15_Reinhardt.pdf)).

   A clipped average of channel ratios satisfies none of these.

### Evidence [Synthetic simulation, S5]

With scalar conf, (H_l + 0.65 H_v)⁻¹(…), translation RMSE is **1.172 ± 0.014 cm**, barely different from the current code's 1.189 cm. The projected fusion of D4 reaches **0.713 cm**.

## D4: Projected covariance intersection is the correct fusion

### What was wrong

**The deployed equation is not Switch-SLAM's Eq. 15.** The code computes (H_l + H_v)⁻¹(H_l d_l + H_v d_v):
- H_l is A-LOAM's unit-weight JᵀJ;
- H_v is VINS-Mono's whitened Hessian;
- no projection is applied in TIGHTLY_COUPLED mode (zero_degenerate() runs only in LIDAR_ONLY_SAFE).

Mixing an un-normalized Hessian with a whitened one makes the relative weighting arbitrary (N6).

**Switch-SLAM's Eq. 15 as printed is not information-weighted either.** It fuses e_v = δx + H_v⁻¹J_vᵀd_v and e_l = δx + [UΛ_pU⁻¹]⁻¹J_lᵀd_l, which it describes as MAP fusion ([Switch-SLAM](https://doi.org/10.1109/LRA.2024.3421792)). Both terms carry identity norms, so minimizing ‖δx − a‖² + ‖δx − b‖² gives the plain average (a + b)/2. In degenerate directions this halves the VO step. This may be a typesetting issue; the authors' code was not checked.

### Final method (exact equations)

```
I_l   = H_l / σ_l²            (σ_l² = rᵀr/(m−6); use final IRLS/Huber weights: H_l = JᵀWJ)
I_l^p = U_p Λ_p U_pᵀ / σ_l²   (keep only eigen-directions that PASS D1)
I_v   = Schur-marginal information of the current pose (or relative pose) from VINS-Mono's window
ω*    = argmin_{ω∈[0,1]} det( (ω I_l^p + (1−ω) I_v)⁻¹ )
P     = (ω* I_l^p + (1−ω*) I_v)⁻¹
δ     = P ( ω* I_l^p d_l + (1−ω*) I_v d_v )
      = −P ( ω* P_u g_l / σ_l² + (1−ω*) g_v )     (gradient form; P_u = U_p U_pᵀ; avoids H_l⁻¹)

VO failed:  δ = P_u d_l + (I − P_u) x_IMU          (Zhang 2016 remapping with IMU prediction)
```

### Derivation, step by step

**Step 1: BLUE and when it applies [Published].** Consider linear estimators x̂ = W₁x₁ + W₂x₂ of two unbiased estimates with covariances P₁ and P₂.
1. Unbiasedness for every x requires W₁ + W₂ = I.
2. With E[e₁e₂ᵀ] = 0, the fused error covariance is P(W₁) = W₁P₁W₁ᵀ + (I−W₁)P₂(I−W₁)ᵀ.
3. Setting ∂tr P/∂W₁ = 0 gives W₁ = P₂(P₁+P₂)⁻¹.
4. The identity P₂(P₁+P₂)⁻¹ = (P₁⁻¹+P₂⁻¹)⁻¹P₁⁻¹ turns this into x̂ = (P₁⁻¹+P₂⁻¹)⁻¹(P₁⁻¹x₁ + P₂⁻¹x₂).
5. This is the Gauss–Markov estimator for z = [I; I]x + e and is minimal in the Loewner order.

**BLUE requires four conditions:** unbiased inputs, uncorrelated inputs, correctly scaled covariances, and a shared tangent space ([Bar-Shalom et al.](https://onlinelibrary.wiley.com/doi/book/10.1002/0471221279); [Kay Vol. 1](https://www.pearson.com/en-us/subject-catalog/p/fundamentals-of-statistical-signal-processing-volume-1-estimation-theory/P200000003316)).

**Step 2: information scaling [Project derivation].** With Σ_l = σ_l²I, the information is JᵀΣ_l⁻¹J = H_l/σ_l². VINS-Mono already whitens: `ProjectionFactor::sqrt_info = FOCAL_LENGTH / 1.5 * Identity` ([VINS-Mono estimator.cpp](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/VINS-Mono/master/vins_estimator/src/estimator.cpp)). Adding raw H_l to whitened H_v therefore weights LiDAR by an unlogged factor σ_l⁻².

**Step 3: projection removes bias [Published + Project derivation].**
- Zhang 2016's remapping is x_f = V_f⁻¹V_p x_p + V_f⁻¹V_u x_u ([Zhang et al. 2016](https://frc.ri.cmu.edu/~zhangji/publications/ICRA_2016.pdf); reference code in [LeGO-LOAM](https://raw.githubusercontent.com/RobustFieldAutonomyLab/LeGO-LOAM/master/LeGO-LOAM/src/mapOptmization.cpp)). Since V is orthonormal, V_f⁻¹V_u = Σ_{well} v vᵀ = P_u, an orthogonal projector, and V_f⁻¹V_p = I − P_u.
- Switch-SLAM's [UΛ_pUᵀ]⁻¹ must be read as a pseudo-inverse. Then −(UΛ_pUᵀ)† g_l = P_u d_l, the same projection.
- A-LOAM's d_l is biased along degenerate directions: S4 shows it keeps the initial error. This violates BLUE condition (a), so those directions are removed.
- In information form, I_l^p d_l = −P_u g_l/σ_l², so the near-singular H_l⁻¹ is never formed.

**Step 4: covariance intersection is consistent under unknown correlation [Published; proof written out].** Let the true joint error covariance be Σ = [[P₁, P₁₂], [P₂₁, P₂]] ⪰ 0 with P₁₂ unknown. Fix ω ∈ (0, 1) and set a = (1−ω)/ω.
1. Let D = diag(√a·I, −I/√a). Then DΣD = [[aP₁, −P₁₂], [−P₂₁, P₂/a]] ⪰ 0, because a congruence preserves positive semidefiniteness.
2. Adding the block-diagonal Σ gives diag(P₁/ω, P₂/(1−ω)) − Σ = DΣD ⪰ 0, because (1 + a) = 1/ω and (1 + 1/a) = 1/(1−ω).
3. Take the CI gains K₁ = ωP_CI P₁⁻¹ and K₂ = (1−ω)P_CI P₂⁻¹ with P_CI⁻¹ = ωP₁⁻¹ + (1−ω)P₂⁻¹. Their sum is K₁ + K₂ = I, so the fusion is unbiased.
4. The true fused covariance is [K₁ K₂] Σ [K₁ K₂]ᵀ ⪯ [K₁ K₂] diag(P₁/ω, P₂/(1−ω)) [K₁ K₂]ᵀ = ω P_CI P₁⁻¹ P_CI + (1−ω) P_CI P₂⁻¹ P_CI = P_CI.

Hence **P_CI bounds the true covariance for every cross-correlation** ([Julier & Uhlmann 1997](https://www.semanticscholar.org/paper/A-non-divergent-estimation-algorithm-in-the-of-Julier-Uhlmann/0ff82aaa06e578968e35da6700d24096ec49953b)). Reinhardt et al. prove that for **two** estimates the CI gains minimize any strictly monotone cost (trace, determinant) among all consistent linear fusions under fully unknown correlation ([Reinhardt et al. 2015](https://isas.iar.kit.edu/pdf/SPL15_Reinhardt.pdf)). The result does not extend to three or more estimates. In information form, CI accepts a singular I_l^p as long as ωI_l^p + (1−ω)I_v is full rank.

**Step 5: why the correlation is real.** The LiDAR and VIO increments share three sources:
- the prior T_{k−1};
- IMU preintegration;
- a VO-seeded LiDAR initial guess (Switch-SLAM Algorithm 1; [LVI-SAM](https://arxiv.org/html/2104.10831v1)).

BLUE with P₁₂ = 0 double-counts these. Inverse CI ([Noack et al. 2017](https://isas.iar.kit.edu/pdf/Automatica17_Noack.pdf)) could be tighter for common-information cases and is noted as an alternative.

**Step 6: modes collapse.**
- **VO healthy:** CI with projected LiDAR, continuous across normal and degenerate conditions.
- **VO failed:** the projected LiDAR update, with the IMU prediction filling the projected-out directions (Zhang remapping with x_p = IMU).

### Evidence [Synthetic simulation, S5]

**Setup.** 6-DOF, 4000 runs × 5 seeds, with stylized magnitudes:
- the LiDAR's spurious degenerate eigenvalue is 1.7, a CRLB of about 1.5 cm taken from the S4 corridor;
- the true error along the degenerate axis is 0.2 m;
- σ_l = 0.02 m;
- H_v is diagonal and already whitened.

| Fusion (translation RMSE, cm) | independent | correlated ρ = 0.6 | ANEES (indep / corr), ok if ≤ 6.11 |
|---|---|---|---|
| Code now (H_l+H_v) unscaled | 1.189 ± 0.011 | 1.195 ± 0.014 | — |
| Scalar conf (H_l + 0.65H_v) | 1.172 ± 0.014 | 1.178 ± 0.017 | — |
| Info-weighted, NO projection | 3.551 ± 0.021 | 3.583 ± 0.015 | — |
| BLUE + projection | 0.713 ± 0.008 | 0.718 ± 0.009 | 5.97 / **7.03 overconfident** |
| **CI + projection (ω = 0.83)** | **0.713 ± 0.008** | **0.717 ± 0.009** | **4.27 / 4.47 consistent** |

Correct information scaling without projection is the worst row. This is the empirical form of the bias argument: properly scaled LiDAR information trusts the fake corridor information. BLUE and CI tie on RMSE because, along the degenerate axis, both use vision only. They differ in consistency, which is what the backend (D7) and the thresholds depend on.

### Limitations

- The magnitudes are stylized.
- Extracting I_v from VINS-Mono's window (D5) is real implementation work.
- The robust-loss weights must be carried into H_l.

## D5: Use VINS-Mono's actual failure flags; no visual threshold is invented

### What was wrong

The project's VO-fail rule (features < 20 OR position jump > 1.5 m OR rotation jump > 0.8 rad) was attributed to VINS-Mono, but it is not VINS-Mono's ([VINS-Mono estimator.cpp, failureDetection L621–667](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/estimator.cpp)).

**What VINS-Mono restarts on:**
- accelerometer-bias norm > 2.5;
- gyro-bias norm > 1.0;
- position jump > 5 m;
- z-jump > 1 m.

**What it only logs:** its "features < 2" and "rotation > 50°" checks print a message, with the `return true` commented out.

**Where 20 comes from:** the **keyframe** rule `last_track_num < 20` ([feature_manager.cpp L74](https://github.com/HKUST-Aerial-Robotics/VINS-Mono/blob/master/vins_estimator/src/feature_manager.cpp)), not a failure test.

**Project-chosen values:** 1.5 m and 0.8 rad.

LVI-SAM uses the same criteria plus speed > 30 m/s ([LVI-SAM estimator.cpp](https://github.com/TixiaoShan/LVI-SAM/blob/master/src/visual_odometry/visual_estimator/estimator.cpp)). The "visual confidence" referred to in the thesis does not exist in code.

### Final method

1. **Hard-failure flag = VINS-Mono's own criteria**, stated plainly as the authors' empirical constants. No derived alternative exists in the literature.
2. **No separate visual threshold.** Vision enters fusion through I_v, and CI weights it (D4).
3. **Optional, labelled as a novel extension.** Schur-marginalize VINS-Mono's window onto the relative pose of the two newest keyframes. Test the information that vision adds over the IMU, either with the generalized eigenproblem H_{vis+imu} x = λ H_imu x or with a log-det ratio, using a D1-style significance test.

### Justification

**[Published] Switch-SLAM rejects a visual Hessian test.** It explicitly declines one because "the minimum eigenvalue of the Hessian matrix of visual odometry is unstable and remains large after failure", and adopts VINS-Mono's failure detection as a binary S_vo ([Switch-SLAM Sec. III-D](https://doi.org/10.1109/LRA.2024.3421792)). The supporting citation to Demmel et al. (ICCV 2021, square-root marginalization) looks loose and should not be repeated without checking.

**[Published] Absolute-pose information is meaningless for VIO.** Monocular VIO has **4 unobservable DOF** (3 translation + yaw) ([Wu & Roumeliotis](https://mars.cs.umn.edu/papers/tech_report_unobs_directs.pdf); [VINS-Mono paper](https://arxiv.org/pdf/1708.03852)). Under free gauge the Hessian is rank-deficient by four ([Zhang, Gallego & Scaramuzza 2018](https://rpg.ifi.uzh.ch/docs/RAL18_Zhang.pdf)). Absolute-pose information therefore reflects the gauge, and only relative-pose information is gauge-invariant.

**[Published] Known degenerate motions:**
- constant acceleration makes scale unobservable;
- no rotation makes roll, pitch and yaw unobservable ([Wu & Roumeliotis](https://mars.cs.umn.edu/papers/tech_report_unobs_directs.pdf)).

**[Published] No symmetric visual test exists elsewhere.** Information-matrix visual metrics exist for feature selection, not for online failure flags ([Carlone & Karaman](https://arxiv.org/pdf/1610.03344); [Zhang & Vela](https://openaccess.thecvf.com/content_cvpr_2015/papers/Zhang_Good_Features_to_2015_CVPR_paper.pdf)). None of LVI-SAM, Switch-SLAM or SA-LIVO uses a visual degeneracy test symmetric to the LiDAR one.

**[Project derivation] Why the extension must exclude IMU and prior factors.** Including them keeps information high even when the camera is blind, which reproduces the failure mode Switch-SLAM describes. This is why the extension tests the information vision adds over the IMU.

### Limitations

- The hard-failure constants remain empirical.
- The extension is untested and has no derived threshold beyond the D1 analogy.

## D6: A Bernoulli CUSUM replaces the 5-frame buffer

### What was wrong

The 5-frame status buffer works as follows:
- no flags in the buffer → LIDAR_ONLY;
- all 5 flagged → TIGHTLY_COUPLED;
- mixed → TRANSITION, with the √(3λ1) blend from Switch-SLAM Eq. 13.

This is a k-of-n window with no stated false-alarm or delay guarantee. Any single false flag in 5 frames puts a normal frame into TRANSITION, which happens with probability 1 − (1−a)⁵ for a per-frame false-flag rate a.

### Final method (exact equations)

```
f_k ∈ {0,1}: D1 verdict at frame k;  a = P(f=1 | normal),  b = P(f=1 | degenerate)
Entry CUSUM:  s_k = ln(b/a) if f_k=1,  ln((1−b)/(1−a)) if f_k=0
              g_k = max(0, g_{k−1} + s_k);   switch to DEGENERATE when g_k ≥ h
Exit CUSUM:   s'_k = ln(a/b) if f_k=1,  ln((1−a)/(1−b)) if f_k=0   (roles swapped)
              g'_k = max(0, g'_{k−1} + s'_k); switch back when g'_k ≥ h'; each switch resets the other
h chosen so the in-control average run length ARL0 (frames between false switches) meets a requirement.
```

### Derivation

1. **Log-likelihood ratio.** For independent Bernoulli verdicts, the LLR of "degenerate" against "normal" for one frame is ln P(f | b)/P(f | a), which gives s_k above.
2. **Drift.** Under normal operation E[s] = −KL(a ‖ b) < 0. Under degeneracy E[s] = KL(b ‖ a) > 0. So g drifts toward 0 in normal conditions and climbs at rate KL(b ‖ a) after onset.
3. **CUSUM as repeated SPRT.** The recursion g_k = (g_{k−1} + s_k)⁺ is the repeated SPRT with lower threshold 0. For a given ARL0 it minimizes the worst-case expected detection delay ([Basseville & Nikiforov, Ch. 2](https://isy.gitlab-pages.liu.se/fs/en/courses/TSFS06/PDFs/Basseville.pdf), presenting Page 1954, Lorden 1971 and Moustakides 1986; [CUSUM overview](https://en.wikipedia.org/wiki/CUSUM)).
4. **Hysteresis.** Running a mirrored CUSUM for the exit gives hysteresis with a stated false-switch rate in each direction.
5. **No transition blend.** The √(3λ1) blend becomes unnecessary because D4's CI + projection is continuous. We found no published LiDAR-degeneracy work that applies CUSUM to mode switching, so this is a defensible design contribution.

### Evidence [Synthetic simulation, S6, a = 0.05, b = 0.90, 5 seeds]

- **Threshold:** h = **6.00** gives in-control **ARL0 = 3019 frames**, about 5 min at 10 Hz. The script searched for the smallest h with ARL0 ≥ 1000.
- **Buffer false transitions:** the buffer puts **22.0% ± 1.6%** of non-degenerate frames into Transition and 0.0000 into Fully.
- **CUSUM false alarms:** 0.06% (0.0006) of non-degenerate frames.
- **Detection delay after onset:** buffer → Fully **5.99 frames**; CUSUM **2.27 frames**.

### Limitations

a and b must be measured on labelled data. S4 suggests the chosen test reaches a ≈ 0 and b ≈ 0.998, but only in simulation. Frame-to-frame verdicts are also correlated, while the derivation assumes independence.

## D7 and D8: Scope the backend honestly and credit the right mitigation

**D7 backend.** No backend exists, so no proof is needed. There are two options:
- **Implement it:** an iSAM2 factor graph, LIO-SAM style, adding the D4 fused pose with covariance P as an odometry factor. CI covariance is provably consistent (D4 Step 4), so it is safe to use as a factor.
- **Scope it out:** state explicitly that the thesis evaluates odometry only.

Either is acceptable. What is not acceptable is implying loop closure or global consistency.

**D8 DCReg mitigation.** The thesis borrows DCReg's **detection** mathematics (Schur blocks; Theorem 1 relating κ(S) to error amplification) but not its preconditioned-CG mitigation. DCReg Theorem 4 interprets its clamping as MAP with a prior ([DCReg](https://arxiv.org/abs/2509.06285)). The mitigation actually used is D4's projection, in the Zhang 2016 remapping lineage ([Zhang et al. 2016](https://frc.ri.cmu.edu/~zhangji/publications/ICRA_2016.pdf)). The text must say so. Tuna et al.'s field study compares projection, constrained and regularized mitigations and is the right comparative reference ([Tuna et al.](https://arxiv.org/pdf/2408.11809)).

## D9: Validation must use ground truth the detector cannot see

### What was wrong

- **v1/v2 tests:** random 6×6 SPD Hessians with a single seed, where "ground truth" was an eigenvalue-ratio cutoff equal to the detector's own threshold. This is circular.
- **Trial counts:** 400 and 800 trials, arbitrary.
- **Single-run comparison:** one Gazebo run (4017 frames) compared mean error per mode. LIDAR_ONLY_SAFE 0.96 against TIGHTLY_COUPLED 30.5 is confounded by which segment each mode was active in.
- **Retired scenarios:** Scenario 2 Part A concerns aliasing, a separate problem (D2). Part B tested a score that is not deployed. Both claims are retired.

### Final protocol

**Ground truth from geometry.** Follow the protocol of [arXiv 2608.15532](https://arxiv.org/html/2608.15532) with Gazebo worlds whose degenerate directions are known:
- rectangular corridor: 1 translational degenerate direction;
- circular tunnel: axial translation + roll about the axis;
- corner/room: none.

Add per-direction labels from the ground-truth pose error projected onto the eigen-directions: e = Log(T_gt⁻¹T_est), labelled by |v_kᵀe| against a tolerance. Never define ground truth with the detector's own quantity. X-ICP, Tuna et al. and DCReg also ground degeneracy in geometry rather than per-frame labels ([X-ICP](https://arxiv.org/pdf/2211.16335); [Tuna et al.](https://arxiv.org/pdf/2408.11809)).

**Detection statistics.** Report Wilson 95% intervals ([Brown, Cai & DasGupta 2001](https://www.researchgate.net/publication/258237345_Interval_Estimation_for_a_Binomial_Proportion)). A half-width of ±0.03 at p = 0.5 needs n ≥ 1068 labelled frames per class. From S7:

| n | half-width at p = 0.5 | half-width at p = 0.9 |
|---|---|---|
| 400 | ±0.049 | ±0.030 |
| 800 | ±0.035 | ±0.021 |
| 1068 | ±0.030 | ±0.018 |
| 3000 | ±0.018 | ±0.011 |

Use 5 seeds or runs, and McNemar's test for paired detector comparisons.

**Covariance calibration.** NEES is ε = x̃ᵀP⁻¹x̃. ANEES over N runs must lie in [χ²_{α/2}(N·n_x)/N, χ²_{1−α/2}(N·n_x)/N]; for 6-DOF and N = 50 that is **[5.08, 7.00]** ([NEES reference, citing Bar-Shalom](https://kalman-filter.com/normalized-estimation-error-squared/)). Derive the CRLB inflation factor for D1(b) from this test, because S4 shows the raw CRLB is miscalibrated.

**Threshold sensitivity.** Sweep α and τ on a log grid and report ROC and PR curves. Tune on some worlds and test on others, never on random frames of one run. Show that ATE/RPE plateau as the threshold varies.

**Trajectory evaluation.**
- **Metrics:** ATE and RPE per Sturm et al. ([Sturm 2012](https://cvg.cit.tum.de/_media/spezial/bib/sturm12iros.pdf)), computed with [evo](https://github.com/MichaelGrupp/evo).
- **Alignment:** SE(3) Umeyama for LiDAR-centric runs; 4-DoF for VIO ([Zhang & Scaramuzza 2018](https://rpg.ifi.uzh.ch/docs/IROS18_Zhang.pdf)).
- **Ablations:** forced-mode runs on the same bag (LiDAR-only, VIO-only, current switching, new method).
- **Statistics:** per-segment RPE; Wilcoxon signed-rank tests; 5–10 runs, reporting median and spread.

**Datasets.** GEODE (tunnels, independent ground truth, used by DCReg; [GEODE](https://arxiv.org/html/2409.04961v1)), SubT-MRS, ENWIDE and FusionPortable.

## Eight newly found errors to add to the audit

**N1. Switch-SLAM Eq. 11–12 uses the wrong χ² tail.** It uses the lower 5% point of χ²(2), 0.103 (CDF 0.0502), as if it were the 95% critical value of 5.991. The borrowed threshold inherits a statistical error. This is the project's own analysis; no published critique was found.

**N2. Channel T is not an independent channel.** It is mathematically H_tt/N (S1: max difference 0).

**N3. The project's Bingham statistic is off by a factor of 2, and tests the wrong hypothesis.** It was written as 15N·Σ(λ−1/3)²; the correct form is (15N/2)·Σ(λ−1/3)². It tests uniformity, not degeneracy.

**N4. Scenario 2 Part B validated a score that is not deployed.** The periodicity score it tested is absent from the code.

**N5. The VO-failure constants attributed to VINS-Mono are not VINS-Mono's.** 20 is the keyframe rule. 1.5 m and 0.8 rad are project values.

**N6. The code's fusion weights LiDAR against vision arbitrarily.** It mixes an un-normalized A-LOAM Hessian with a whitened VINS Hessian, so the relative weighting depends on unlogged magnitudes.

**N7. The 5-frame buffer sends about 22% of normal frames to TRANSITION** at a 5% per-frame false-flag rate (S6).

**N8. The raw CRLB/Hessian covariance is overconfident in corridors.** S4 gives ANEES 48.25 against 3, so a CRLB-only threshold misses degeneracy; the noise-floor test is required.

For traceability, the prior 36-item audit maps onto the decisions as follows:
- A1–A6 → D1 (A4–A5 → D2)
- B7–B13 → D3/D4
- C14–C17 → D4
- D18–D19 → D6
- E20–E21 → D5; E22 → D7; E23 → D8; E24 → documentation fix only
- F25–F33 → D9
- G34–G36 → already corrected

## What to implement, in order

1. **A-LOAM patch.** Publish, per planar correspondence:
   - the point p_i and fitted normal;
   - the 5-neighbour scatter eigenvalues and eigenvectors (or C_i directly);
   - the final residual and the final Huber/IRLS weight.

   Also publish H_l = JᵀWJ (already on /laser_hessian) and σ_r² = rᵀr/(m−6).
2. **Switching node, detection.** Delete the semicircle thresholds, the κ test, Channel T, BINGHAM_ISO_THR and conf. Implement D1:
   - Schur blocks and per-eigenvector c_i, μ_v, g, h;
   - test (a) at α = 0.05 and test (b) with stated τ_t and τ_R;
   - a log of which eigenvectors fail, in the LiDAR frame.
3. **Switching node, fusion.** Implement I_l = H_l/σ_l², the projection I_l^p onto D1-passing directions, and a 1-D search for ω minimizing det P. Compute δ in gradient form and publish P.
4. **VINS-Mono side.** Extract the Schur-marginal information of the current (or relative) pose from the sliding window. Replace the VO-fail rule with VINS-Mono's actual criteria (2.5, 1.0, 5 m, 1 m z), cited as empirical. On failure, use the projected LiDAR update with the IMU prediction filling P_p.
5. **Switching logic.** Replace the 5-frame buffer and the √(3λ1) blend with the two-sided Bernoulli CUSUM. Set h from a required ARL0 once a and b are measured.
6. **Experiment 1, calibration.** Build the Gazebo corridor, circular-tunnel and room worlds, with repeated registration runs. Compute ANEES of σ_r²S⁻¹ and derive the CRLB inflation factor and the noise-model check.
7. **Experiment 2, detection.** Collect at least 1068 geometry-labelled frames per class. Report detection rates with Wilson CIs, compare against semicircle/κ/λ3 with McNemar's test, and sweep α and τ with a tune-world/test-world split.
8. **Experiment 3, switching.** Measure a and b, set h, and report false-switch rate and delay against the buffer on the same logs.
9. **Experiment 4, trajectory.** Run forced-mode ablations on identical bags with 5–10 runs, reporting ATE/RPE with evo, per-segment RPE and Wilcoxon tests. Then repeat on GEODE and SubT-MRS sequences.
10. **Backend decision.** Either add iSAM2 odometry factors with P, or write the explicit scope limitation.

## Conclusion

The common failure across the original components was treating a number that *looks* statistical as if it were calibrated: a χ² quantile from the wrong tail, a normalized eigenvalue fraction, a clipped average, a 5-frame majority. The repair is the same each time. Tie the decision to a stated null hypothesis or a physical requirement (noise-floor information, metres and radians, ARL0, consistency under unknown correlation), and then check calibration with NEES rather than trusting the Hessian. The most consequential finding is that the Hessian in a corridor is confidently wrong: noise-fitted normals manufacture about 6× too much precision. This single fact explains why CRLB thresholds miss degeneracy, why unprojected information fusion performs worst, and why BLUE becomes overconfident. Every decision downstream inherits it.

What remains open is empirical, not theoretical. The Satterthwaite noise model, the CUSUM rates and the CI gains are all proven or derived, but the evidence so far is a synthetic planar simulation. The thesis's credibility now depends on running the D9 protocol in Gazebo and on GEODE before claiming the method works on real sensors.
