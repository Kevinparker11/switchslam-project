# Novelty, research gap and evidence

*14 October 2026. Every prior-work statement below was read from the paper or its official page on this date, unless marked otherwise. Our numbers come from the user's runs on SubT-MRS Multi Floor.*

## 0. Direct answer first

**No search can prove that an idea has "never been used in any form".**
- What can be shown is that the closest published systems, read in full text where possible, do not do what we do.
- What we do is also measurably better on the same data than the alternatives they use.

**Each building block of our method exists somewhere in the literature:**
- Schur-complement decoupling: DCReg; the Selective Kalman Filter.
- Soft eigen-direction weights: SA-LIVO.
- VIO as the motion prior for LiDAR: VIL-SLAM, LVI-SAM, CompSLAM.
- Loop closure: VIL-SLAM, LVI-SAM.

Claiming any one of them as new would be wrong, and an examiner would catch it.

**What is new, as far as the search found, is the combination and the controlled evidence for it.** Four things together:
1. A VIO-primary estimator.
2. LiDAR enters only as a **continuous** correction of the **translation**, weighted by the LiDAR's **marginal (Schur-complement) translational information**, scaled by one calibrated factor.
3. No degeneracy threshold.
4. Rotation always from VIO.

We also show, on paired data, that this beats the hard alternatives used in the literature: whole-pose switching and per-direction 0/1 selection.

Those are the claims to make. Section 4 gives the wording, and Section 5 lists what must still be run before they are safe.

## 1. Our method in one paragraph

At every mapped LiDAR scan, the relative motion over the last scan is formed in the LiDAR body frame from two sources: VINS-Mono (VIO) and A-LOAM scan-to-map. The fused increment is:

- rotation: dR = dR_VIO
- translation: dt = W dt_LiDAR + (I − W) dt_VIO, with W = (c S_tt + I)⁻¹ c S_tt

Here S_tt = H_tt − H_tR H_RR⁻¹ H_Rt is the Schur complement of the scan-matching Hessian, which is the inverse of the LiDAR's marginal translational covariance. W is the standard information-form weight of a LiDAR measurement with information c·S_tt against a unit VIO step. Directions the LiDAR cannot see get weight near 0, and well-seen directions get weight near 1. There is no switch and no threshold.

The fused pose seeds A-LOAM's next scan-to-map match. A LiDAR-keyframe pose graph adds loop closures afterwards. The only parameter, c, was fixed at 0.03 on Multi Floor and is frozen for every other sequence.

## 2. Closest prior work (what each one does)

| Work | Primary estimator | How LiDAR / extra information enters under degeneracy | Detection | Rot/trans separated | Hard or soft | Threshold | Evaluated on SubT-MRS MF/LC |
|---|---|---|---|---|---|---|---|
| Zhang, Kaess, Singh, ICRA 2016 | LiDAR | Solution remapping: update only in well-conditioned eigen-directions | min eigenvalue of H | no | hard per direction | heuristic | no |
| **Switch-SLAM**, Lee et al., RA-L 2024 | LiDAR, VIO when degenerate | Switches the scan-matching initial guess to VIO; remapped LiDAR + VIO in Eq. 15 | 3 smallest normalised eigenvalues of full H vs [0.12, 0.27, 0.48] | no | **hard switch**, plus interpolation buffer | claimed "non-heuristic" (see Section 3, G3) | **yes**: MF 1.61 / LC 2.42 m RMSE |
| Lee et al., same lab, *LiDAR-Visual-Inertial SLAM Robust in Structurally and Visually Degenerate Environments* (manuscript on lab site; venue not stated) | LiDAR when healthy | "Active factor graph" connects or disconnects LiDAR/visual factors by status; removes degenerate eigen-directions | min eigenvalue of scan-to-map H | no | **hard** | predefined | yes: MF 2.13, LC 4.77 m RMSE (table extracted from PDF text; verify column assignment) |
| LVI-SAM, Shan et al., ICRA 2021 | LiDAR factor graph, VIO as initial guess | VIO initial guess for scan matching (per Switch-SLAM's description) | failure checks | no | hard | heuristic | MF fail, LC 8.7 m (Lee et al. table) |
| VIL-SLAM, Shao et al., 2019 | VIO prior, **LiDAR mapping result replaces it** | No weighting; "loosely couples" VIO and LiDAR mapping | none explicit | no | LiDAR overrides | none | no |
| LIC-Fusion, Zuo et al., 2019 | One MSCKF over IMU, camera and LiDAR edge/surf features | Tight coupling: LiDAR information enters the filter as measurements | implicit | no | soft by construction (full 6-DoF) | none | no |
| Super Odometry, Zhao et al., IROS 2021 | IMU-centric | VIO and LIO relative poses as factors weighted by "reliability"; per-feature weights | no explicit detector | no | soft, per factor / per feature | heuristic | (its team's challenge entry) |
| CompSLAM, Khattak et al., arXiv 2025 | VIO (VTIO) primary, leg odometry fallback | VIO pose is the prior for scan-to-scan registration; whole-pose fallback when degenerate | eigenvalues of H vs threshold; trans/rot checked separately | blocks checked separately | **hard, whole pose** | heuristic | no |
| **Selective KF**, Xu et al., arXiv 2412.17235; published as *Fuse only what matters*, ISPRS J. 2026 | **LiDAR-inertial** primary | VIO information added **only** in LiDAR-degenerate directions via a 0/1 selection matrix S | **Schur-complement covariance blocks** Σ_rr, Σ_tt | yes | **hard (binary)** | "based on practical requirements and experience" | no |
| **SA-LIVO**, Cao et al., arXiv 2606.25699 (June 2026) | Joint LiDAR-visual-inertial iterated EKF | Gate g = min(√λ/σ_min, 1) on eigen-directions of the **joint** information Λ_L + qΛ_V | eigen-decomposition of joint 6×6 info | **no** (6×6 joint) | soft | σ_min (setting not stated) | no |
| DCReg, Hu et al., IJRR 2026 | LiDAR only | Preconditioner with clamped eigenvalues in Schur subspaces | Schur complements S_R, S_t, κ_th 10–50 | yes | soft (preconditioning) | κ | caves only (LiDAR) |
| X-ICP 2023 / RELEAD 2024 | LiDAR (RELEAD: LiDAR front end + graph with VIO) | Constrained optimisation in non-localizable directions | H_tt / H_rr blocks | blocks | hard constraints | heuristic | no |
| Liao et al., arXiv 2412.07513 | LiDAR + IMU | IMU estimate projected onto degenerate directions | H_rr / H_tt ratios, **threshold-free via DBSCAN** | blocks (diagonal, not Schur) | weighted, partly specified | none | no |
| LODESTAR, Lee et al., 2025 | LiDAR-inertial | Adaptive Schmidt-Kalman, active vs fixed states | Jacobian condition number | no | hard (state partition) | grid-searched (incl. on Long Corridor) | LC 1.386 m |
| Tuna et al. field study, T-FR 2025 | LiDAR | Compares TSVD, Tikhonov, constraints | several | — | both | — | no. Finding: *active mitigation matters most when no reliable external odometry prior is available* |
| Hinduja et al., IROS 2019; DARE-SLAM, 2021 | — | **Degeneracy-aware loop / registration factors** | ICP Hessian | — | partial constraints | — | no |

Sources: Section 7.

## 3. The research gap, with evidence

**G1. Soft, marginal-information correction inside a VIO-primary system has not been evaluated.**

In the systems above, LiDAR degeneracy in a LiDAR-camera system is handled in one of three ways:
- **(a) Whole-pose switching:** Switch-SLAM, Lee et al., CompSLAM.
- **(b) Hard per-direction selection or projection:** Zhang 2016, Selective KF, X-ICP/RELEAD.
- **(c) Tight coupling with full 6-DoF information:** LIC-Fusion, SA-LIVO's joint gate.

None of the checked papers does all of the following:
1. Keeps VIO primary.
2. Lets the LiDAR scan-to-map result correct only the translation, through its marginal (Schur) information.
3. Uses a continuous weight with no threshold.
4. Compares that against (a) and (b) on the same recorded data.

The closest designs differ as follows:
- **Selective KF:** Schur covariances, but LiDAR-primary, with a binary choice and experience-set thresholds.
- **SA-LIVO:** soft, but on the joint 6×6 information, with no rotation/translation split, LiDAR-anchored, and not tested on SubT-MRS.
- **CompSLAM:** VIO-primary, but hard and whole-pose.

**G2. Whole-pose switching discards valid translation information when only rotation is weak.**

Measured on our 12 logged Multi Floor runs (range across logs):
- κ(S_RR) > 15.7 in **37%** of frames (36.7–37.7%).
- κ(S_tt) > 10 in only **0.2%** of frames (0.16–0.26%).
- Switch-SLAM's own rule fires in **1.3–1.6%** of frames.

A switch driven by rotation-subspace degeneracy therefore turns LiDAR off in over a third of frames in which its translation is fine:
- **Replay:** rotation-triggered switching costs +0.31 m full-span and +0.36 m on the held-out bags. Gating our weight with the same κ costs +0.28 m and +0.33 m. Both hold on 12 of 12 logs.
- **Live:** the gated F1 was worse than the ungated F3 in 3 of 3 runs.

DCReg decouples rotation and translation for **detection**, but in a LiDAR-only solver. The point that the **fusion decision** must also be decoupled (translation information for translation, VIO for rotation) is, as far as the search found, not made in any LiDAR-camera paper.

**G3. Switch-SLAM's "non-heuristic" threshold is derived from the wrong χ² tail.**
- The threshold 0.103 is the **lower** 5% point of χ²(2) (CDF(0.103) = 0.050), not the 95% critical value of 5.991.
- With the correct tail, Eq. 12 gives negative thresholds that can never fire.
- Its Eq. 15 also sums the visual and LiDAR residuals unweighted.

No published critique was found in our searches, though the full list of papers citing it could not be enumerated (about 60). This is an analysis contribution, not a method.

**G4. Loop closure in LVIO depends on the front end: an observation, not a method novelty.**
- With identical loop closure, our corrected front end goes from 0.626 to **0.347 m**.
- VINS-only goes from 1.235 to 1.382 m (worse).
- LiDAR-only goes from 7.75 to 8.18 m (worse).

Loop closure itself is prior art (VIL-SLAM, LVI-SAM). The evidence that it only helps after the soft correction supports the system design.

## 4. Contributions to claim (suggested wording)

**C1 (method).** "A VIO-primary LiDAR-visual-inertial front end in which the LiDAR scan-to-map result corrects only the translation, through a continuous weight built from its Schur-complement (marginal) translational information, with rotation left to the VIO and no degeneracy threshold. A single information scale, frozen across sequences, is the only parameter."

Evidence status (Section 6):
- **Soft beats hard on held-out data:**
  - **Against whole-pose switches:** better held-out ATE than switching by the Switch-SLAM rule, by the κ(S_RR) gate, or always taking the LiDAR translation (12 of 12 replayed logs; Wilcoxon p = 0.0005).
  - **Against per-direction 0/1 selection:** the same holds (12 of 12 logs, p = 0.0005).
  - **Short-horizon accuracy:** 1-s relative error is better too.
- **Direction-aware beats isotropic:** directional weighting beats isotropic or constant blending by 0.03 m (11 to 12 of 12 logs).
- **Schur vs diagonal block: no difference on Multi Floor** (0.004 m, p = 0.05). This is expected: DCReg itself reports that translational Schur and diagonal condition numbers nearly coincide in the R³×SO(3) parameterisation. **Do not claim that the Schur complement improves accuracy unless Long Corridor shows it.** Claim it as the principled choice (it is the marginal information, Proposition 1 of DCReg).

**C2 (empirical finding).** "In a VIO-primary system, decisions taken on the whole pose (switching) discard valid LiDAR translation whenever rotation is weakly constrained; decoupling the fusion decision is what removes this loss." (G2)

**C3 (analysis).** The Switch-SLAM threshold derivation error (G3), stated as analysis with the arithmetic shown.

**C4 (result).**

| Method | Multi Floor ATE RMSE (m) |
|---|---|
| Ours, front end only | 0.626 ± 0.107 (n = 6) |
| Ours, with loop closure | **0.347 ± 0.036** (n = 6; bootstrap 95% CI 0.322–0.372) |
| Switch-SLAM (published) | 1.61 |
| Lee et al. manuscript | 2.13 |
| ICCV'23 challenge best | 0.401 (different stack; metric and alignment may differ) |
| LVI-SAM, FAST-LIVO (per Lee et al.) | fail |
| Our A-LOAM LiDAR-only | 7.8–42.9 (7 live runs) |

**Drop these claims (prior art exists or our data does not support them):**
- **"First use of the Schur complement in LiDAR-camera fusion":** the Selective KF already uses Schur-complement covariances.
- **"Label-free Otsu threshold":** it did not help (F2 ≈ F1), and threshold-free detection exists (Liao et al. 2024, DBSCAN).
- **"Degeneracy-aware loop weights":** prior art exists (Hinduja 2019, DARE-SLAM), and they were not better on Multi Floor.
- **"Non-heuristic":** C_T = 0.03 was chosen on Multi Floor.

## 5. What must still be done before the claims are safe

1. **Live ablation on Multi Floor**, since the replay ranks need live confirmation:
   - Configs: F11 isotropic, F12 Switch-SLAM-rule switch, F13 per-direction 0/1, F14 always-LiDAR translation, F15 diagonal block; each ×3, about 2 h.
   - Open-loop replay re-uses scan-to-map poses that A-LOAM produced while seeded by our soft-fused pose. Hard variants that lean more on LiDAR therefore inherit better LiDAR poses than they would produce live, so the replay gap is probably an *under*-estimate. Live runs settle it.
   - (Check: replaying a run with its own configuration reproduces the live ATE exactly, 0.576 and 0.475, so the replay arithmetic is exact.)
2. **Long Corridor with everything frozen:** C_T = 0.03, 1 loop-search round, odometry noise 1.46°/0.054 m from Multi Floor.
   - Runs: F0, F8, and the ablation configs.
   - This is where the translation is truly degenerate along the corridor, so it is the decisive test of directional and Schur weighting (C1) and of the switch-vs-soft finding.
   - Targets: Switch-SLAM 2.42 m, Lee et al. 4.77 m, LODESTAR 1.386 m, challenge best 1.254 m.
3. **One more fresh sequence** for generality: SubT-MRS Corridor02 or BlockLiDAR (see `claude/Dataset_Test_Plan.md`).
4. **Our own baselines on the same bags:** FAST-LIO2 (and LIO-SAM if feasible) without loop closure. That gives a same-hardware, same-alignment comparison instead of mixing published numbers that use different alignments.
5. **Statistics:** ≥ 3 live runs per configuration; paired Wilcoxon and bootstrap CIs; ties defined in advance (< 0.1 m, inside the ground truth's quoted accuracy).

## 6. Evidence tables

**Weighting ablation: open-loop replay on 12 logged Multi Floor runs**
- Logs: F0, F1, F7, F8 ×6, F9 ×3. Settings: C_T = 0.03, rotation from VIO, same scan-to-map poses and Hessians for every variant.
- The last column (held-out difference) is the paired difference of the variant minus ours.

| Variant | Full ATE (m) | Held-out bags 1–2 (m) | 1-s RPE | Held-out vs ours |
|---|---|---|---|---|
| **ours: Schur S_tt, soft, no gate** | 0.692 ± 0.142 | **0.425 ± 0.059** | 0.0945 | — |
| diagonal block H_tt, soft | 0.690 | 0.429 | 0.0957 | +0.004 (8/12, p = 0.05) |
| isotropic, same mean information | 0.716 | 0.457 | 0.0973 | +0.032 (11/12, p = 0.001) |
| constant blend α = 0.82 | 0.738 | 0.456 | 0.0946 | +0.031 (12/12, p = 0.0005) |
| per-direction 0/1 (κ_t > 10 dropped) | 0.690 | 0.499 | 0.1107 | +0.075 (12/12, p = 0.0005) |
| hard switch, Switch-SLAM rule | 0.692 | 0.501 | 0.1096 | +0.076 (12/12, p = 0.0005) |
| always LiDAR translation (W = I) | 0.688 | 0.495 | 0.1107 | +0.070 (12/12, p = 0.0005) |
| ours + κ(S_RR) ≤ 15.7 gate | 0.975 | 0.751 | 0.0877 | +0.326 (12/12, p = 0.0005) |
| hard switch on κ(S_RR) | 0.998 | 0.788 | 0.1007 | +0.363 (12/12, p = 0.0005) |
| VIO only | 1.297 | 0.780 | 0.0667 | +0.355 |

Reading:
- Hard variants match ours on the full span because the gain there comes from the first segment. On the held-out bags they are worse by 0.07 m and noticeably rougher (1-s RPE 0.110 vs 0.095).
- Rotation-triggered gating or switching is clearly harmful.
- VIO alone has the best 1-s RPE but drifts. Our correction trades some 1-s smoothness for drift, which should be reported.

**Live results, Multi Floor** (full-span ATE RMSE, m; mean ± sd; bootstrap 95% CI):

| Configuration | n | ATE RMSE | Bootstrap 95% CI |
|---|---|---|---|
| F0 VIO-primary, no LiDAR correction | 3 | 1.277 ± 0.023 | — |
| F1 gated, C_T 0.003 | 3 | 1.050 ± 0.046 | — |
| F3 no gate, C_T 0.003 | 3 | 0.963 ± 0.049 | — |
| F7 C_T 0.01 | 4 | 0.883 ± 0.025 | — |
| F8 C_T 0.03 | 9 | 0.617 ± 0.107 | 0.551–0.683 |
| F8 recordings + loop closure | 6 | **0.347 ± 0.036** | 0.322–0.372 |
| LiDAR only (A-LOAM, F4/F5) | 7 | 7.8–42.9 (range) | — |

## 7. Sources

- Switch-SLAM, Lee et al., RA-L 9(8) 2024, [doi:10.1109/LRA.2024.3421792](https://doi.org/10.1109/LRA.2024.3421792) (project PDF)
- Lee et al., [LiDAR-Visual-Inertial SLAM Robust in Structurally and Visually Degenerate Environments (lab manuscript)](https://www.robot.t.u-tokyo.ac.jp/~yamashita/paper/E/E487Final.pdf)
- DCReg, Hu et al., [arXiv 2509.06285](https://arxiv.org/abs/2509.06285) (project PDF)
- Selective Kalman Filter, Xu et al., [arXiv 2412.17235](https://arxiv.org/html/2412.17235v1); *Fuse only what matters*, ISPRS J. Photogramm. Remote Sens. 238 (2026) 508–518, [record](https://hit.globalimpact.cn/en/publications/fuse-only-what-matters-degeneracy-aware-multi-sensor-fusion-for-l/)
- SA-LIVO, Cao et al., [arXiv 2606.25699](https://arxiv.org/html/2606.25699v1)
- CompSLAM, Khattak et al., [arXiv 2505.06483](https://arxiv.org/pdf/2505.06483)
- Super Odometry, Zhao et al., [arXiv 2104.14938](https://ar5iv.labs.arxiv.org/html/2104.14938)
- VIL-SLAM, Shao et al., [arXiv 1902.10741](https://ar5iv.arxiv.org/html/1902.10741)
- LIC-Fusion, Zuo et al., [arXiv 1909.04102](https://arxiv.org/abs/1909.04102)
- RELEAD, Chen et al., [arXiv 2402.18934](https://arxiv.org/pdf/2402.18934v1)
- Liao et al., [arXiv 2412.07513](https://arxiv.org/html/2412.07513v1)
- LODESTAR, Lee, Marsim, Myung, [arXiv 2511.09142](https://arxiv.org/html/2511.09142v1)
- LP-ICP, [arXiv 2501.02580](https://arxiv.org/pdf/2501.02580)
- DARE-SLAM, Ebadi et al., [arXiv 2102.05117](https://arxiv.org/abs/2102.05117); Hinduja et al., IROS 2019 (cited in DCReg)
- Tuna et al. field study, IEEE T-FR 2025 (cited in DCReg; the quoted finding is from our earlier verified-reference notes); SubT-MRS, [arXiv 2307.07607](https://arxiv.org/html/2307.07607v5)

**Not verified:**
- LVIO-Fusion (Zhang et al., RA-L 2024): mechanism not readable.
- The venue of the Lee et al. manuscript.
- Whether any of the ~60 papers citing Switch-SLAM corrects its χ² tail.
