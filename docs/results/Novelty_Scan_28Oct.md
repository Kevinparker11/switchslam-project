# Is F8 / F16 novel? Literature scan of 28 October 2026

Method: about 20 web searches (several in extended mode) over LiDAR-visual-inertial fusion, degeneracy handling, Schur-complement decoupling, Manhattan/structure-based heading, plus the page text of 12 closest papers fetched and summarised on the day (summaries by the fetch tool, not a manual full-text reading). Earlier scan: `Novelty_and_Research_Gap.md` (14 Oct). No search can prove that nothing similar exists; the finding below is "not found in what was read".

## What F8 and F16 are, stated as claims to be checked
- F8: VIO (VINS-Mono) is the primary pose. Per mapped scan, the LiDAR scan-to-map translation increment is blended with the VIO increment by W_t = (c S_tt + I)^-1 c S_tt, with S_tt the Schur complement (marginal translational information) of the registration Hessian; one scale c, no threshold, no gate. Rotation always from VIO.
- F16 = F8 + SAH: heading corrected from the directions of near-vertical planar surfaces of LiDAR keyframes, levelled by the VIO gravity, compared with a reference pattern learned online (any building orientation, not only 90 degrees), ≤ 0.25 degree per scan, self-disabling when there is no clear structure.

## Closest prior work, read on 28 Oct
| Work | What it does (as read) | Overlap with F8/F16 | Difference |
|---|---|---|---|
| V-LOAM, Zhang & Singh, ICRA 2015 | VO at 60 Hz is the primary estimate; LiDAR odometry at 1 Hz refines it and removes distortion. No covariance weighting, no degeneracy fallback; the LiDAR stage solves the full drift vector. | VIO-primary + LiDAR correction | No weighting, no translation-only split, no degeneracy handling |
| Selective Kalman Filter, Xu et al., arXiv 2412.17235 | LiDAR-inertial primary; splits the information matrix into rotation/translation blocks (Schur forms) and eigendecomposes each; binary selection S by fixed thresholds; visual information added only in degenerate directions. | Schur-complement blocks for rotation and translation separately | LiDAR-primary, hard 0/1 per direction, thresholds; rotation also corrected |
| SA-LIVO, Cao et al., arXiv 2606.25699 | Joint LiDAR-visual information Lambda_L + q Lambda_V eigendecomposed (6x6); soft gate g = min(sqrt(lambda)/sigma_min, 1); no rotation/translation split, no Schur in the text read; HILTI22, NCD, Oxford Spires, FAST-LIVO2 data. | Continuous per-direction weight | Joint 6x6, LiDAR-anchored, a threshold sigma_min; no SubT-MRS |
| Super Odometry (SO 2.0 "Resilient Odometry via Hierarchical Adaptation"), arXiv 2608.25427 | IMU-centric factor graph, soft fusion; LiDAR residual weights from PCA linearity/planarity/scatter; per-point observability aggregated into confidences gamma_trans and gamma_rot; modality disabled if its share stays under 10 % for 2-4 s (empirical); explicitly avoids the optimiser's Hessian/Schur. No heading prior. SubT-MRS, no loop closure. | Soft fusion, separate translation and rotation confidences, same benchmark | Not Schur, not VIO-primary, both confidences used; also learned IMU network |
| CompSLAM, Khattak et al., arXiv 2505.06483 | VIO primary, whole-pose fallback by eigenvalue threshold | VIO-primary | Hard, whole pose |
| DCReg, Hu et al., IJRR 2026 | Schur-complement rotation and translation decoupling for detection, preconditioning for mitigation; LiDAR only | Schur decoupling | LiDAR-only, no VIO fusion |
| DAMM-LOAM, arXiv 2510.13287 | LiDAR-only; eigen-analysis of the translation block H_tt only; soft per-point weights; rotation not analysed; no Schur | soft weighting from the translation block | LiDAR-only |
| MM-LINS, arXiv 2503.19506 | LIO; rotation and translation covariance blocks eigendecomposed separately "to stop their different scales from coupling"; thresholds; response is a new map | separate rotation/translation scale handling | detection by covariance thresholds, no fusion weighting |
| ALIVE-LIO, arXiv 2604.02706 | LIO + learned velocity used along degenerate directions; X-ICP style; Kalman gain | per-direction external prior | learned prior, hard degenerate subspace |
| Planar Constraint Assisted LiDAR SLAM (Manhattan), Remote Sensing 15(1):15, 2023 | LIO-SAM; RANSAC ground and vertical planes; vertical-plane angle constrains yaw, x, y; assumes three orthogonal main directions; stops working in non-Manhattan scenes | wall direction to limit heading drift | assumes orthogonal Manhattan, no VIO, no learned reference, no self-disabling gates |
| MSC-VO (arXiv 2111.03408), StructVIO, ManhattanSLAM, Structure-SLAM, PGD-VIO (arXiv 2407.17709) | RGB-D / camera based; Manhattan axes (orthogonal) or plane landmarks to reduce rotation drift | structure-based drift reduction | camera/RGB-D, orthogonal axes or plane landmarks, not a LiDAR wall-normal histogram |
| Yaw aided Radar Inertial Odometry using Manhattan World Assumptions | title read, mechanism not read | wall-based yaw aiding | radar; not read |
| DeCOD, arXiv 2609.36753 | corridor landmarks to correct longitudinal drift; LIO | structure used for drift | different quantity |

## Verdict by component
1. **VIO-primary with LiDAR refinement: not new.** V-LOAM, VIL-SLAM, CompSLAM, Super Odometry all have VIO or IMU as the primary or equal-role estimate with LiDAR refinement.
2. **Schur-complement separation of rotation and translation: not new** (DCReg, Selective KF, MM-LINS for the separation). Do not claim it.
3. **Continuous, threshold-free weight: partly prior** (SA-LIVO soft gate with sigma_min, DAMM-LOAM, Super Odometry). Their weights use a threshold or a different quantity. Ours has one scale c, set on Multi Floor and not retuned.
4. **The combination in F8: not found.** VIO-primary + LiDAR enters only as a translation correction + weight from the marginal (Schur) translational information S_tt + rotation always from VIO + no gate or threshold. No checked paper has all of these. Supporting evidence of our own: soft beats hard and whole-pose switching on held-out bags (12 of 12 logs), and rotation-triggered switching discards valid translation (kappa(S_RR) high in 37 % of frames, kappa(S_tt) in 0.2 %).
5. **SAH (F16): the idea is prior art, the specific design is not found.** Structure-based yaw correction from walls exists (LiDAR Manhattan SLAM, visual Manhattan systems). Not found in what was read: heading from LiDAR wall normals on a VIO-primary estimator, with a reference learned online in arbitrary (non-90-degree) buildings, whole-pattern correlation, and self-disabling gates. Its gains are modest and development data (see `Structure_Heading_Development_Results.md`).
6. **Channel T / Bingham:** the orientation-tensor eigenvalue ratio appears in LF-GICP (arXiv 2608.19522, read earlier through a synopsis; fetch rate-limited today) and the normal sums in SuperLoc and X-ICP; Bingham gives no statistic beyond T's eigenvalues. Not a novelty claim.

## What changed in the comparison with published results (important)
Super Odometry's Table 2 (SubT-MRS, no loop closure) reports Floor01 0.315 m and Corridor01 0.817 m ATE; our `Published_Comparison_All_Datasets.md` already lists 0.315 for SuperLoc on Floor01, so these appear to be the same values. Our F8 front end is 0.617 on Multi Floor (F8 + loops 0.347), and our best Long Corridor front end is 2.27 (F16; F16 + loops 1.54). So:
- we beat Switch-SLAM's published numbers on Multi Floor (1.61), and tie on Long Corridor (2.42) only with F16;
- we do **not** beat the best published SubT-MRS results (0.315, 0.817); with loops we are within 0.03 m on Multi Floor and about two times behind on Long Corridor;
- the setups differ (our VINS-Mono alone is much better than Switch-SLAM's), and Multi Floor is our tuning sequence.

## Suggested wording (what the evidence supports)
"To our knowledge, among the LiDAR-visual-inertial methods we examined, none combines a VIO-primary estimator with a LiDAR correction restricted to translation, weighted continuously by the Schur-complement (marginal) translational information with a single calibrated scale and no degeneracy threshold, and with rotation left to the VIO." Not "first to use the Schur complement", not "first soft fusion", not "non-heuristic" (c was set on Multi Floor), not "beats the state of the art".

## Limits of this scan
No Google Scholar / IEEE Xplore / Semantic Scholar paging; the 60 or so papers citing Switch-SLAM were not enumerated; page texts were read through a summarising fetch tool, several only as abstracts or partial text; two sources were not read (LF-GICP today because of a rate limit; the Yaw-aided Radar-Inertial paper's mechanism); venue status of several 2025-2026 arXiv preprints unconfirmed; workshop and thesis literature only sampled.

## Sources
[V-LOAM (ICRA 2015)](https://frc.ri.cmu.edu/~zhangji/publications/ICRA_2015.pdf), [Selective Kalman Filter](https://arxiv.org/html/2412.17235v1), [SA-LIVO](https://arxiv.org/html/2606.25699v1), [Super Odometry 2.0](https://arxiv.org/pdf/2608.25427), [DAMM-LOAM](https://arxiv.org/abs/2510.13287), [MM-LINS](https://arxiv.org/abs/2503.19506), [ALIVE-LIO](https://arxiv.org/abs/2604.02706), [DCReg](https://arxiv.org/abs/2509.06285), [Planar Constraint Assisted LiDAR SLAM (Manhattan)](https://www.mdpi.com/2072-4292/15/1/15), [MSC-VO](https://arxiv.org/pdf/2111.03408), [PGD-VIO](https://arxiv.org/pdf/2407.17709), [DeCOD](https://arxiv.org/html/2609.36753), [Switch-SLAM](https://doi.org/10.1109/LRA.2024.3421792), [SuperLoc](https://arxiv.org/abs/2412.02901), [LF-GICP](https://arxiv.org/html/2608.19522).

## Addendum (28 Oct, later): the R + T + OT structure
Three more papers bear on the owner's fixed structure (details and links in `OT_Channel_Study.md`):
- LF-GICP (arXiv 2608.19522) already uses the orientation tensor of planarity-weighted map normals as a solver-independent degeneracy measure (threshold-gated, LiDAR-only, no heading use). "Orientation tensor as degeneracy measure" is therefore not new.
- D²-LIO (arXiv 2508.14355) already uses separate rotation and translation weights because of the scale difference. Together with DCReg, the R / T separation is not new.
- LiLi (arXiv 2609.17145) is independent of the Hessian, but through re-optimisation, not normals.
What was not found in the papers read: the tensor (with edges counted) as a direction-by-direction, threshold-free cap on the Schur translation information inside a VIO-primary weight (N = tr(H_tt), no scale), and one orientation-distribution channel giving both that cap and the heading anchor (SAH = alignment of all even-order orientation tensors of the same normals). Claim wording in `OT_Channel_Study.md` section 7.
