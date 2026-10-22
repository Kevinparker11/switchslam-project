# Reviewer report: draft Introduction (LiDAR degeneracy detection paper)

Reviewed file: `scratchpad/intro_draft.md` (Section I, 7 paragraphs + 3 contributions + roadmap).
Review date: 2026-10-09.

Sources used:
- `Intro references/verified_refs.md`.
- Earlier notes under `research_notes/`: `detection_protocols.md`, `robotics_degeneracy_literature.md`, `degeneracy_labels.md`, `degenerate_datasets.md`, `subt_mrs.md`, `fusion_and_switching.md`.
- Project PDFs read in full or by search:
  - DCReg: `2509.06285v3.pdf`, read in full.
  - Switch-SLAM: `SwitchSLAM.pdf`, Secs. II, III-A, III-E and IV.
- arXiv pages fetched in this session:
  - 2408.11809: abstract and PDF.
  - 2608.19522: abstract.
  - 2405.12563: introduction.
  - 2203.05698: abstract, plus the ar5iv full text.
  - 2104.10831: PDF.
  - 2208.01787: abstract and PDF.

Verification limits:
- LF-GICP was read only through its abstract and a secondary synopsis cited in earlier notes.
- For [17], WebFetch returned part of the PDF, and the conclusion section was not visible.
- NV-LIOM was checked against the arXiv NV-LIO text, not the RA-L version.
- WebFetch output is a model summary, so quotes taken from it are paraphrases unless they are marked as quotes.

---

## A. Must-fix items (ranked)

1. **Paragraph 4 states the scale-disparity consequence backwards.**
   - The draft says: "rotational eigenvalues are usually much larger than translational ones, and a single threshold on the full Hessian tends to overlook **translational** degeneracy".
   - DCReg [18] says the opposite. The large rotational eigenvalues make full-Hessian minimum-eigenvalue tests miss **rotational** degeneracy, and full-Hessian condition-number tests over-flag **translation** (see B.18a).
2. **Paragraph 5 mischaracterizes the labels in [14].**
   - The draft says the labels "came from simulation [14] ... not from the geometry of the scene at the true pose".
   - Nubert's labels *are* geometric labels at a known pose. Each scan is perturbed, a new child scan is ray-cast at the perturbed pose, and the child is registered back. They are simulated, not outcome-based.
   - Only [21]'s labels are outcome-based. They come from GNSS compared with ICP, and they are binary per keyframe, not per direction.
3. **Paragraph 7: the claim that the orientation channel "does not depend on point positions, residual weights, or the current rotation estimate" draws the wrong contrast** (see C.4).
   - For point-to-plane residuals, H_tt does not depend on point positions either. DCReg Eq. (7c): "Htt depends solely on the normal distribution, independent of point distances".
   - In A-LOAM's world-frame parameterization, H_tt does not depend on the rotation estimate except through which correspondences are found.
   - The real differences are four:
     - the correspondence set, which depends on the pose estimate;
     - the robust (Huber) weights;
     - map-plane normals versus scan normals;
     - A-LOAM's feature selection.
   - The channel also sees only translation. It cannot detect roll in a circular tunnel or yaw on open ground, and the Introduction should say so.
4. **Paragraph 5, "...[12], [17], [18], and take good numbers as evidence that the detector worked", is unfair to two of the three sources.**
   - [17] deliberately fixes one simplified X-ICP detector for all methods and evaluates *mitigation*.
   - [18] explicitly says its degeneracy ratio "serves as an indicator of detection sensitivity rather than an error metric".
   - Reword the sentence. DCReg's own ablation is the strongest evidence for the confound, so use it (see B.18e).
5. **Paragraph 3, the [17] sentence, is overstated and slightly off-target.**
   - The paper's stated conclusion is that active mitigation "is necessary and advantageous in the absence of reliable external estimate assistance".
   - Its priors were external odometry: a noisy simulated pose prior and COIN-LIO for the handheld tunnel. They were not specifically "inertial odometry".
   - It compared *mitigation* strategies, not detectors.
6. **Paragraph 5, "a strong inertial prior can hide degeneracy altogether [18]", overstates the source.**
   - In DCReg this is a remark in the future-directions section ("can also redistribute or mask degeneracy patterns"), not a finding.
   - Drop "altogether" and present the point as a remark.
7. **Paragraph 7, the dataset claim ("survey-grade maps together with ground-truth trajectories [7], [8], [27]"), needs scoping and one caveat.**
   - GEODE has a TLS map only for its stair sequences.
   - Whether FusionPortable v1 provides maps is unverified. FusionPortableV2 releases them explicitly.
   - In GEODE-stairs and SubT-MRS, the reference poses themselves come from aligning LiDAR data to the map. Along the very directions being labeled, the reference pose may be weak.
8. **Paragraph 1 has three problems.**
   - (a) [1] does not support "LiDAR has become the main sensor". [2] does ("the go-to approach for virtually all teams").
   - (b) "mostly through point-to-plane distances" is inaccurate. LOAM, LeGO-LOAM, LIO-SAM and A-LOAM all use edge (point-to-line) residuals as well as planar ones; only FAST-LIO2 is plane-only.
   - (c) As a result, Paragraph 7 ("point-to-plane residuals of A-LOAM") must say that edge residuals are excluded and that Huber weights are or are not carried into H.
9. **Several acronyms and symbols are undefined on first use**: GNSS, ICP, GICP, ROC, and the symbol J.
10. **Paragraph 6, "drop only the weak directions ... rather than the whole update [9]", should also cite [21].**
    - Switch-SLAM already projects the LiDAR update onto the well-conditioned DOFs (Eqs. 15–16, Λ_p).
    - LVI-SAM [22] is the example that drops the whole LiDAR factor.

---

## B. Citation accuracy, sentence by sentence

Legend:
- **S** = supported.
- **P** = partly supported.
- **N** = not supported.

### Paragraph 1

**B.1 [1], [2].** Claim: "Three-dimensional LiDAR has become the main sensor for this task because it measures geometry directly and does not need ambient light [1], [2]."
- **Verdict: P.**
- [2] supports the claim for SubT. Its abstract describes "lidar-centric SLAM solutions (the go-to approach for virtually all teams in the competition)".
- [1] (Cadena 2016) is a general SLAM survey and does not make this claim. Its verified summary is in `verified_refs.md` §1.
- Fix: "In GNSS-denied field robotics, LiDAR is now the primary sensor for this task because it measures geometry directly and needs no ambient light; in the DARPA SubT Challenge, lidar-centric SLAM was the approach of almost every team [2]." Then move [1] to the first sentence (onboard state estimation/SLAM).

**B.2 [3]–[6].** Claim: "...registering each new scan to a local map, mostly through point-to-plane distances, ... in real time."
- **Verdict: P.**
- LOAM, LeGO-LOAM and LIO-SAM use both edge (point-to-line) and planar features. LOAM also has a scan-to-scan odometry stage. FAST-LIO2 is point-to-plane on raw points.
- Fix: "...by registering each new scan to a map through point-to-line and point-to-plane distances, in real time."

### Paragraph 2

**B.3 [2].** Claim: "The effect is well known from field campaigns such as the DARPA Subterranean Challenge [2]."
- **Verdict: S.**
- From [2] Sec. I: the lack of features in long corridors "induces failures in LIDAR-odometry approaches based on feature or scan matching".
- From the CompSLAM section: the system identifies DOFs "possibly ill-conditioned due to geometric self-similarity".

**B.4 [7], [8].** Claim: "recent datasets were recorded in such places on purpose".
- **Verdict: S.**
- GEODE was built for degenerate scenarios: 64 sequences in 7 scenario types (`verified_refs.md` §21).
- SubT-MRS targets degraded conditions, including featureless corridors (§20).

### Paragraph 3

**B.5 [9] Zhang et al.** Claim: eigenvalues reveal poorly constrained directions, and solution remapping updates only along well-constrained directions.
- **Verdict: S.**
- `verified_refs.md` §7. DCReg §2.3.1 also says the method restricts "updates to well-constrained subspaces".

**B.6 [10] Gelfand et al.** Claim: "a similar 6 × 6 constraint matrix to choose ICP samples that stabilize the weak directions".
- **Verdict: S.**
- The matrix is exactly the point-to-plane Hessian, which Gelfand et al. call the "covariance" of constraint forces and torques (`robotics_degeneracy_literature.md` §1).
- Optional precision fix: "the same 6 × 6 matrix".
- Also worth noting: Gelfand normalizes the points to a unit average lever arm to equalize torque and force. This is an early fix for the unit problem raised in Paragraph 4, so [10] could be cited there as well.

**B.7 [11] Hinduja et al.** Claim: "made the eigenvalue cutoff adaptive".
- **Verdict: S.**
- The cutoff is recomputed at every iteration (`verified_refs.md` §9).
- Note that DCReg classifies this method as a full-Hessian condition-number method (FCN).

**B.8 [12], [13].** Claim: "assessed localizability direction by direction".
- **Verdict: S.**
- X-ICP computes per-correspondence alignment onto the eigen-directions, with three categories.
- LP-ICP gives a per-DoF, three-level classification (`detection_protocols.md`).
- [13] is an arXiv preprint only; its venue is unverified.

**B.9 [14] Nubert et al.** Claim: "learned it directly from raw scans".
- **Verdict: S.**
- arXiv abstract: the "network is trained exclusively on simulated data" and predicts localizability from raw scans.

**B.10 [15] Hatleskog & Alexis.** Claim: "derived the probability of degeneracy from a noise model of the inputs".
- **Verdict: S.**
- `verified_refs.md` §16. DCReg §2.1.2 describes it as "probabilistic modeling of measurement noise ... signal strength probability".

**B.11 [16] RELEAD.** Claim: "constrained filter updates in degenerate scenes".
- **Verdict: S.**
- RELEAD uses constrained ESKF updates (`verified_refs.md` §17).
- RELEAD is a mitigation method, so it sits a little oddly in a list of detectors. DCReg also cites it as an example of diagonal-block detection.

**B.12 [17] Tuna et al.** Claim: "A field comparison of several such strategies [17] found that how much they help depends strongly on whether a reliable external prior, such as inertial odometry, is available."
- **Verdict: P.** Evidence:
  - Abstract: "active optimization degeneracy mitigation is necessary and advantageous in the absence of reliable external estimate assistance".
  - Sec. 5.2: "the performance is mainly driven by better usage of the external motion prior".
  - Sec. 5.1.3: the Prior-Only baseline's accuracy "depends on the accuracy of the external pose prior".
- Where the draft goes wrong:
  - The priors were a noisy simulated pose prior and COIN-LIO (LiDAR-inertial) on the handheld tunnel data. They were not specifically "inertial odometry".
  - "depends strongly" is an inference, not a stated result.
  - "such strategies" refers back to a list that is mostly detectors. [17] compares *mitigation* methods (TSVD, inequality constraints, Tikhonov) behind a single shared X-ICP-style detector.
- Fix: "A field comparison of degeneracy-mitigation strategies [17] concluded that active mitigation inside the optimizer is needed mainly when no reliable external odometry estimate is available."

### Paragraph 4

**B.13 Uncited sentence on units and coupling** (DCReg's own claims; the draft's version is checked here as point (a) for [18]).
- Sub-claim: "rotational eigenvalues are usually much larger than translational ones".
  - **Verdict: S** (needs a citation).
  - DCReg §2.1.1: "rotational eigenvalues typically exceed translational ones by orders of magnitude due to lever-arm effects".
  - Caveat from DCReg Fig. 17: "Rotational eigenvalues are not consistently larger than translational ones". So "usually" is the right word.
- Sub-claim: "a single threshold on the full Hessian tends to overlook translational degeneracy".
  - **Verdict: N (reversed).** Evidence from DCReg:
    - §2.1.1: the scale disparity makes "rotational degeneracies particularly elusive to detect".
    - §7.3.1: ME "systematically overlooks rotational degeneracies due to scale disparity, as rotational eigenvalues typically maintain higher magnitudes than translational counterparts".
    - §7.4.1: "ME exhibit insufficient detection ... while FCN demonstrate over-detection by treating all translational dimensions as universally degenerate".
    - §7.2.1: ME leads "to over-detection in translational part".
  - Fix: "...so a minimum-eigenvalue threshold on the full Hessian tends to miss rotational degeneracy, while a full-Hessian condition number flags translation almost everywhere [18]."

**B.14 Uncited sentence on diagonal blocks** (point (b) for [18]). Claim: "Checking the rotational and translational diagonal blocks separately removes the scale problem but ignores the coupling, and it can report a well-constrained problem when the joint problem is not."
- **Verdict: S** (needs a citation). Evidence from DCReg:
  - §4.2: "Even when both κ(HRR) and κ(Htt) appear well-conditioned, the overall system can exhibit severe ill-conditioning due to strong rotation-translation coupling."
  - §2.1.1: diagonal-block analysis "provides more reliable detection without frequent retuning, [but] overlooks the coupling effects ... leading to both false positives and false negatives".
  - Figs. 13 and 15: the parking-lot and stair cases where diagonal analysis misses rotational degeneracy.
- Add [18]. Optionally add [12], [16], which DCReg names as diagonal-block examples.
- Optionally add "(or the reverse)", because Remark 1 notes that κ(S_R) can also be *smaller* than κ(H_RR).

**B.15 [18], Schur complement and reported gains** (point (c)). Claim: "...combined with a targeted solver, it reports clear gains over eigenvalue-based baselines in caves, stairwells, and corridors."
- **Verdict: S, but quantify.** ATE results from DCReg Tables 4 and 5:

  | Scene | DCReg | ME-/FCN- baselines | Other |
  |---|---|---|---|
  | Cave02 | 4.57 cm | 209.53–565.61 cm | O3D 16.88 cm |
  | Stairs | 3.96 cm | 6.44–280.07 cm | |
  | Corridor | 7.44 cm | 26.24–231.40 cm | |

- Caveats worth one clause:
  - The corridor and parking-lot sequences were range-limited on purpose to induce degeneracy (§7.1.1).
  - The system-level runs sit inside "a 5 s sliding-window fixed-lag smoother ... coupled with LiDAR-inertial odometry" (§7.1.3). That clause helps the argument in Paragraph 5.
- Fix: "...reports lower trajectory error than minimum-eigenvalue and condition-number baselines on cave, stair, and range-limited corridor sequences [18]."

**B.16 Uncited sentence: "It changes with the current correspondences and residual weights".**
- **Verdict: S** (needs a citation).
- Hatleskog & Alexis [15]: Hessian eigenvalues "depend on the number of measurements, weights, the scale of the environment and sensor noise" (`robotics_degeneracy_literature.md` §5).
- DCReg §10: "pose estimation depends entirely on correspondence pairs that evolve with initial poses during iteration".
- Fix: add [15], [18].

**B.17 [19] LF-GICP** (point 3 in the brief). Claim: "covariance regularization can keep the translational block well conditioned even when the geometry is not [19]".
- **Verdict: S.**
- arXiv abstract: "covariance regularization keeps the translation block artificially well-conditioned". Its statistics come from a "regularization-free voxel-normal localizability field".
- The secondary synopsis gives M = Σ ρ_v n_v n_vᵀ over map voxel normals, with the statistic λ_min/tr. This is unverified from the full text.

**B.18 [19], [20], normal-distribution detectors.** Claim: "For point-to-plane residuals, the translational block is built from the surface normals, which has led to detectors that inspect the distribution of normals directly [19], [20]."
- **Verdict: P.**
- The fact is right: DCReg Eq. (7c) gives H_tt = Σ n nᵀ, so cite [18] here.
- [20] (NV-LIO arXiv intro): "the distribution of the normal vector directions is analyzed to assess the occurrence of degeneracy" and used for "adjusting the matching uncertainty".
- [19] reads voxel normals.
- The causal link "which has led to" is not stated by either paper. Also, [19] is GICP (plane-to-plane), not point-to-plane.
- Fix: "For point-to-plane residuals, the translational block is the sum of nnᵀ over the matched normals [18]; some detectors therefore read the distribution of normals directly [19], [20]."

### Paragraph 5

**B.19 [12], [17], [18], evaluation practice** (points (e) and [12]/[17] in the brief).
- Sub-claim: "Most studies report trajectory error, end-point drift, or the share of frames flagged as degenerate".
  - **Verdict: S.**
  - X-ICP reports APE, RPE, map error and end-position error, with no detection precision or recall (`detection_protocols.md`).
  - [17] reports APE/RPE (EVO) and map error against TLS, uses a shared simplified X-ICP detector, and reports no detection labels.
  - DCReg reports ATE, AC, CD and the degeneracy ratio (DR), which is the share of frames flagged (§7.1.2).
- Sub-claim: "...and take good numbers as evidence that the detector worked".
  - **Verdict: P/N.**
  - It is wrong for [17], which evaluates mitigation behind a fixed detector, chosen "to prevent giving an unintentional advantage".
  - DCReg explicitly says "DR serves as an indicator of detection sensitivity rather than an error metric". It *does* argue detection quality from DR and hybrid ATE:
    - "DCReg achieves balanced detection rates that better reflect actual degeneracy conditions" (§7.4.1);
    - "our detection method combined with SR significantly outperformed the baseline ME-SR approach ..., validating the effectiveness of our balanced detection strategy" (§7.5.2).
  - So the criticism holds for [12] and [18], phrased neutrally.
- Fix: "Most studies report trajectory error, end-point drift, or the share of frames flagged as degenerate [12], [17], [18], and argue for detection quality from these numbers without labels [12], [18]."

**B.20 Uncited claim: "Trajectory error ... mixes the quality of the detector with that of the mitigation or fusion step".**
- **Verdict: S. Cite [18]'s own ablation** (Table 9, corridor). With the same Schur detector, the choice of mitigation changes ATE as follows:

  | Configuration | ATE |
  |---|---|
  | Detection without mitigation | 164.14 cm |
  | No degeneracy handling | 28.54 cm |
  | DCReg + SR | 37.75 cm |
  | DCReg + TReg | 22.79 cm |
  | DCReg + TSVD | 17.81 cm |
  | DCReg (full) | 7.44 cm |

- This is strong, citable support for the paper's central argument. Use it.

**B.21 [18] on inertial priors** (point (d)). Claim: "a strong inertial prior can hide degeneracy altogether [18]".
- **Verdict: P.**
- DCReg §9 (Future Directions): "Strong priors from IMU or other sensors can also stabilize weakly constrained local estimation, but they can also redistribute or mask degeneracy patterns."
- It is a remark, not an experimental result, and it says "mask", not "altogether".
- [17] supports the related point that with a good prior, accuracy is driven by the prior.
- Fix: "...and a strong inertial prior can stabilize the estimate while masking the degeneracy beneath it [17], [18]."

**B.22 [14], [21], labels** (points 5 and [14]/[21] in the brief). Claim: "Where detection accuracy has been measured against labels, the labels came from simulation [14] or from disagreement between scan matching and a GNSS reference [21], not from the geometry of the scene at the true pose."
- **Verdict: P.**
- [21] is S. Switch-SLAM §IV-C: "The ground truth is prepared by comparing GNSS data with scan-to-scan matching using ICP [36] at each keyframe". The labels cover part of the Handheld (open-field) dataset and are binary per keyframe. Results: accuracy 0.91, 0.96 and 0.96, and recall 0.91, 0.96 and 0.99, for [16], [17] and the proposed method respectively.
- [14] is S for "simulation" but N for the contrast. From the ar5iv full text:
  - child scans are ray-cast at perturbed poses and registered to the parent with point-to-plane ICP;
  - each of the 6 DoF is labeled binary with thresholds of 0.1 m and 2°;
  - the test set is simulated from a real tunnel mesh (RTC360/BLK2GO).
  These are geometry-at-known-pose labels, which is the same principle the draft proposes.
- The sentence makes a universal claim, so hedge it with "To our knowledge".
- Fix: "To our knowledge, detection has been scored against labels only in simulation, with per-direction labels from perturbation and re-registration at known poses [14], and on real data with per-keyframe labels from disagreement between ICP scan matching and GNSS [21]. No study provides per-direction labels on real data."

### Paragraph 6

**B.23 [21], [22], [23], LVI systems.** Claim: "LVI-SAM [22] and Switch-SLAM [21] rely on visual or visual–inertial odometry [23] when LiDAR becomes unreliable."
- **Verdict: S.**
- LVI-SAM (arXiv PDF): "We adapt the processing pipeline from [8] for our VIS", where [8] is VINS-Mono. Its LIS declares failure when the "smallest eigenvalue of ATA is smaller than a threshold", and "Lidar odometry constraints are not added to the factor graph when failure happens".
- Switch-SLAM §III-A: its VO uses "the method proposed in [6]" (VINS-Mono), "propagated at the frequency of the IMU measurements". It switches the scan-to-map initial guess to VO when degeneracy is flagged (Alg. 1).

**B.24 [9], per-direction removal.** Claim: "...drop only the weak directions of a LiDAR update rather than the whole update [9]."
- **Verdict: S for [9], but incomplete.**
- Switch-SLAM Eqs. 15–16 already do this ("Λp denotes the matrix with eigenvalues removed corresponding to degenerate DOFs").
- LVI-SAM drops the whole factor.
- Fix: "Some systems discard the whole LiDAR update when degeneracy is flagged [22]; others remove only the flagged directions [9], [21], which requires a detector that is accurate per direction, not only per scan."

### Paragraph 7

**B.25 [24] A-LOAM.** Claim: "an open implementation of LOAM".
- **Verdict: S.**
- Note: A-LOAM uses edge and planar residuals with a Huber loss. The Huber parameter is unverified; earlier notes recall `HuberLoss(0.1)`. State which residuals and weights enter H.

**B.26 [18], [25], [26]. Verdict: S.**
- The Schur complement follows DCReg §4.2.
- The scatter or orientation matrix is the sufficient statistic of the Bingham model [25], [26].

**B.27 [7], [8], [27], datasets with maps.**
- **Verdict: P.**
- GEODE has a "GT map for stairs only" (RTC360). Its stair poses come from aligning the data to that map with PALoc (`degenerate_datasets.md`, `degeneracy_labels.md`).
- SubT-MRS: FARO maps. GT trajectories come from the "fusion of various constraints derived from the ground truth map, visual odometry, LiDAR odometry, and IMU" (`subt_mrs.md`).
- FusionPortable v1: map availability is from prior knowledge and is unverified. DCReg cites both FP v1 (Jiao 2022) and FPv2 (Wei 2024). FPv2 states that GT maps are released. Check which version your corridor sequence comes from, and cite FPv2 if needed.
- Add one clause acknowledging that reference poses can be weak along degenerate directions, and handle it in Sec. IV.

**B.28 [14], perturbation labeling.** Claim: "Following the perturbation idea of [14], each scan is displaced along each direction at its ground-truth pose and registered back to the map..."
- **Verdict: P** (it is an adaptation, so say so).
- [14] differs in three ways:
  - it uses joint Gaussian 6-DoF perturbations;
  - it ray-casts a *new* scan at each perturbed pose, which a rigid displacement of a real scan cannot do;
  - it registers scan-to-scan, not scan-to-map.
- DCReg/[17] use a related "register a perturbed copy to the original" protocol in a simulated cylinder.
- Fix: "Adapting the perturbation labeling of [14], which was developed for simulated scan-to-scan registration, to real scan-to-map data, ..."

---

## C. Technical correctness of uncited statements

**C.1 Corridor, tunnel and open ground. Correct.**
- In a rectangular corridor, the cross-section corners constrain roll; only translation along the axis is free. In a circular tunnel, translation along and rotation about the axis are both free.
- Make two things explicit:
  - A single dominant plane leaves **three** weak directions: two in-plane translations and yaw about the normal. DCReg's parking-lot frames show exactly X, Y and yaw.
  - Write "rotation about the tunnel axis" rather than "roll", because "roll" assumes the body x-axis is aligned with the tunnel.
- Real corridors can also lose roll when the field of view or range is limited. DCReg §7.4.2 reports X *and* roll in a 5 m range-limited corridor. "sometimes ... mixed together" covers this case.

**C.2 Schur complement meaning. Correct.**
- S_R = H_RR − H_Rt H_tt⁻¹ H_tR is the Hessian of the reduced problem after minimizing over translation. In Gaussian terms, it is the information on rotation with translation marginalized (DCReg Thm. 1, Prop. 1).
- Optional precision: "the rotational information that cannot be explained by a compensating translation".

**C.3 "For point-to-plane residuals, the translational block is built from the surface normals". Correct, but say which normals.**
- H_tt = Σ wᵢ nᵢnᵢᵀ over the *matched map-plane normals* of accepted correspondences.
- In A-LOAM the plane is fitted to 5 nearest map points; these are not raw scan normals.

**C.4 Orientation channel: "does not depend on point positions, residual weights, or the current rotation estimate", assuming T = (1/N) Σ n nᵀ from raw scan normals.**
- "Residual weights": **True.** T is unweighted.
- "Point positions": **Misleading.**
  - T does not depend on lever arms or the origin.
  - It does depend on positions in two ways. Normals are estimated from local neighborhoods, and the sampling density, which is range-dependent, sets each surface's weight in the sum.
  - H_tt for point-to-plane also does not depend on lever arms (DCReg: "independent of point distances"). So this is not a difference between the channels.
- "Current rotation estimate": **True but trivial.**
  - The spectrum of H_tt is rotation-invariant (T ↦ RTRᵀ).
  - With A-LOAM's world-frame translation, ∂r/∂t = nᵀ involves no R.
  - What T avoids is dependence on the *correspondences*, which depend on the whole pose estimate, rotation and translation.
- Missing differences that a reviewer will ask about:
  - map versus scan normals;
  - correspondence gating and rejection;
  - A-LOAM's curvature-based feature selection and downsampling;
  - edge residuals, which add information that T cannot see.
- Identity worth stating: with unit weights, the same normals and the same point set, H_tt = N·T exactly. Any disagreement between the channels is therefore attributable to the items above.
- Scope: T is a **translation-only** statistic. It cannot detect the roll freedom of a circular tunnel or the yaw freedom of open ground. Say that the orientation channel complements the translational part of the Schur channel only.
- Suggested wording: "It is computed from the scan alone, before registration. With unit weights and identical normals it equals H_tt/N, but unlike the Hessian it does not depend on correspondences, robust weights, or the pose estimate. It constrains only translation."

**C.5 Paragraph 2: "The optimizer still returns a pose ... set by noise and by the initial guess". Correct.**
- Optionally cite [9] or [18]. DCReg §1.1 says ill-conditioning "makes the solution highly sensitive to sensor noise and initial estimates".

**C.6 Paragraph 4 units sentence.** The mechanism (lever arm, with H_RR ∝ Σ‖p‖² sin²∠(p,n)) is correct. The consequence is reversed; see B.13.

**C.7 Labeling procedure: risks a reviewer will raise** (these belong in Sec. IV, but the Introduction's claims depend on them).
- (i) A failure to recover the displacement can come from the convergence basin or local minima, not from degeneracy. DCReg §8 makes the same point.
- (ii) The labels depend on the registration algorithm used. If that is A-LOAM's own solver, the labels are independent of the detectors but share solver-specific behavior with the Hessian channel.
- (iii) Reference-pose error along weak directions; see B.27.

---

## D. Missing citations and related work a reviewer may expect

- Paragraph 4, units sentence and diagonal-block sentence: add [18]. Optionally add [12], [16] for diagonal-block methods.
- Paragraph 4, "changes with the current correspondences and residual weights": add [15], [18].
- Paragraph 4, "translational block is built from the surface normals": add [18] (Eq. 7c).
- Contribution 1 claims thresholds "calibrated on held-out data rather than set by hand", but the Introduction never motivates the problem. Add one sentence on how published thresholds were set:
  - Zhang [9]: mid-margin on one dataset.
  - X-ICP [12]: basin of convergence, partly user-defined.
  - DCReg [18]: κ_th = 10, set equal to a mitigation target in a flat region. DCReg §4.3 says "typically set between 10 and 50".
- Related work worth considering (status as recorded in earlier notes; verify before citing):
  - SuperLoc, Zhao et al., ICRA 2025 (arXiv 2412.02901). Pre-optimization alignment-risk statistic from normals and Jacobians; a DCReg baseline. This is the closest pre-solve competitor to the orientation channel.
  - LiLi, arXiv 2609.17145. A perturbation-and-re-optimization *detector*. Reviewers may ask how the perturbation labels differ from it.
  - "Degenerate in Whose Frame?", arXiv 2608.15532. Shows that Hessian-based verdicts change with the body frame, which bears on the units argument.
  - Nobili et al., ICRA 2018, "Predicting alignment risk". A data-driven detector cited by DCReg. Check whether it reports accuracy against real labels before claiming that only [14] and [21] do.

---

## E. Style (IEEE conventions and phrasing)

IEEE conventions:
- **Citations.** Placement before punctuation, the "[4]–[6]" range form and numbering in order of first appearance are all correct.
- **Hyphens versus en dashes.** "LiDAR–visual–inertial" and "visual–inertial" use en dashes. IEEE editorial style and the cited titles (VINS-Mono, Switch-SLAM, LVI-SAM) use hyphens: "LiDAR-visual-inertial", "visual-inertial". Keep the en dash only for ranges ("[4]–[6]").
- **Acronyms.** Define on first use:
  - "global navigation satellite system (GNSS)";
  - "iterative closest point (ICP)";
  - "generalized ICP (GICP)";
  - "receiver operating characteristic (ROC)".
  - Also define J ("where **J** is the Jacobian of the residuals") and set matrices in bold: **H** = **J**ᵀ**J**.
- **Spelling.** American spelling is consistent ("labeled", "marginalized", "organized"). No issues found.
- **Contributions and roadmap.** The numbered contributions "1)–3)" and the roadmap follow IEEE practice. However, Paragraphs 3–4 are already a related-work survey. Either shorten them or have the roadmap say that Section II covers what the Introduction omits, so the two do not repeat each other.

Phrasing to tighten (exact quote, then a plainer alternative):
1. "How these detectors are evaluated is a further and less discussed issue." → "Evaluation is a third problem."
2. "and take good numbers as evidence that the detector worked" → "and infer detection quality from these numbers" (also a factual fix; see B.19).
3. "These questions have practical weight, because the detector decides what a multi-sensor system does next." → "This matters because the detector decides what a multi-sensor system does next."
4. "we treat LiDAR degeneracy detection as a problem in its own right" → "we evaluate LiDAR degeneracy detection directly, separately from any downstream fusion" (the second half of the sentence then becomes redundant).
5. "The two channels can therefore disagree, and the way they disagree carries information." → state the mechanism: "Where they disagree, the difference comes from the solver (correspondences, weights) rather than from the scene, and we use this in Section III." Otherwise the sentence reads as a teaser.
6. "it reports clear gains over eigenvalue-based baselines" → give the number or say "lower trajectory error than" (see B.15).
7. "It is therefore still hard to say how often a given detector raises a false alarm..." → "As a result, the false-alarm rate, the miss rate, and the accuracy of the reported direction are unknown for existing detectors."
8. Triplet rhythm. "underground, inside large buildings, or on industrial sites", "walls, floor, and ceiling", "Stairwells, narrow cave passages, and open ground", "caves, stairwells, and corridors", "trajectory error, end-point drift, or the share of frames", and "point positions, residual weights, or the current rotation estimate" all appear within six paragraphs. Break up one or two; the last one also has to change for technical reasons (C.4). Separately, "industrial sites" is weak as a GNSS-denied example, since many are outdoors. Use "large indoor industrial facilities".
9. "shifts the load onto a camera that may itself be struggling in dark or textureless spaces" → "...onto a camera that may itself fail in dark or textureless spaces."
