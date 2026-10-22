# Reviewer report v2: Introduction draft `intro_v2.md` (LiDAR degeneracy detection)

Review date: 2026-10-11. Reviewer did not write the draft.

Files reviewed:
- Draft: `scratchpad/intro_v2.md` (10 paragraphs, 3 contributions, roadmap; about 1,360 words before the contributions).
- Reference list: `scratchpad/refs_v2.md` ([1]–[29]).

Evidence used:
- `fact_bank.md` (all sections, including Section 0), `verified_refs.md`, `review.md` (v1 review).
- Project files, read in full this session:
  - `2509.06285v3.pdf` (DCReg [9]): Abstract, §1.1, §2.1, §3.3, §4.2–4.4, §7.1, §7.3–7.5, §9, §10, Tables 2, 4, 5, 9.
  - `SwitchSLAM.pdf` (Switch-SLAM [23]): Abstract, §II, §III-C to III-E (Eqs. 14–16, Alg. 1), §IV-C.
- Fetched this session (WebFetch; quotes are ≤125 characters and exact as returned):
  - SuperLoc arXiv 2412.02901 (abstract and HTML v2).
  - Nobili et al., ORI PDF.
  - SubT-MRS, CVF PDF.
  - LVI-SAM, ar5iv 2104.10831, Sec. II-C2.
  - GEODE, arXiv HTML 2409.04961v2, including §4.4 (ground truth).
  - Nubert et al., ar5iv 2203.05698, Sec. VI.
  - Gelfand et al., Stanford PDF.
  - Hinduja et al., CMU PDF.
  - LP-ICP, arXiv HTML 2501.02580v3.
- Code: local clone of A-LOAM (`scratchpad/repos/A-LOAM`): `laserOdometry.cpp`, `laserMapping.cpp`, `lidarFactor.hpp`. Also the project patch `/mnt/attach/outputs/patch_hessian.py`, which shows the Hessian is extracted in `laserOdometry.cpp`, the scan-to-scan stage.
- Overlap check: a script compared all word 4- to 7-grams of the draft against every quoted string in `fact_bank.md`. The DCReg and Switch-SLAM full texts and the fetched abstracts were compared by hand.

Verdict legend:
- **S**: supported.
- **P**: partly supported.
- **N**: not supported.

---

## A. Must-fix items, ranked

1. **P9: the A-LOAM description is technically wrong, and it does not match the labels.**
   - The draft says the channels are computed on A-LOAM's *scan-to-scan* problem. That is correct for the project code: `patch_hessian.py` patches `laserOdometry.cpp`.
   - In `laserOdometry.cpp`, however, each plane residual (`LidarPlaneFactor`) uses the normal of the plane through **three points of the previous sweep** (j, l, m). The 5-point map-plane fit belongs to `laserMapping.cpp` (`LidarPlaneNormFactor`), the scan-to-map stage. So "normals of planes fitted to the map" is wrong.
   - In P10, the labels come from registering each scan "back to the map", which is scan-to-map registration. The detector and the labels therefore describe two different registration problems, and the draft never says so.
2. **P9: "it carries no rotational information [10]" overstates the case and is technically false.**
   - A rank-deficient **T** does reveal some rotational freedoms. If every normal is parallel to n, as on a single ground plane, rotation about n is unconstrained.
   - What **T** cannot do is certify that rotation *is* constrained. That depends on the lever arms p × n, which **T** discards.
   - Gelfand supports the scoped version: "rotations are dependent on distance of the point", and normal-space sampling "is aimed at constraining translational sliding".
3. **P9: the N**T** identity contradicts the next sentence.**
   - H_tt = N**T** holds only for the point-to-plane part of the Hessian, with the same N unit normals and unit weights.
   - The next sentence says the Hessian also contains edge residuals, and those add to H_tt.
   - Contribution 1 says "Schur complement of the point-to-plane Hessian", while P9 says the Hessian includes edges. Pick one and use it in both places.
4. **P10: the reference-trajectory caveat leaves out GEODE [8].**
   - GEODE §4.4: for the stair sequence, "the ground truth trajectory is generated using the PALoc SLAM method", "which estimates LiDAR poses within a pre-constructed map by the Leica RTC360 laser scanner".
   - That is the same LiDAR-to-map dependence as [7] and [29], so cite [7], [8], [29].
   - GEODE also admits that on one stair device "the PALoc algorithm could not generate an accurate ground truth trajectory". This supports the per-scan check.
   - Also: [8] and [29] release maps only for some sequences, so "datasets that release survey-grade maps" needs scoping.
5. **P5 S6: a seven-word verbatim run from the DCReg abstract.**
   - The run is "long-duration localization accuracy and typical speedups of".
   - The draft also drops "at least" from "at least 20%–50%", which changes the claim.
6. **P6 S3: close paraphrase of the LF-GICP abstract, and GICP is undefined.**
   - The draft's "covariance regularization can keep the translational block well conditioned" is the source's "covariance regularization keeps the translation block artificially well-conditioned" with only the inflections changed.
   - "In a degenerate tunnel" combines two separate abstract statements.
7. **P5 S4: "this hid degeneracy that was present [9]" asserts ground truth that DCReg does not have, and it undercuts the paper's own thesis.**
   - DCReg's evidence is its own Schur condition number plus a geometric argument:
     - Fig. 13: "rotational degeneracy is masked by diagonal methods".
     - §7.4.1: "the Schur condition number successfully identifies the ill-conditioning, whereas the diagonal condition number incorrectly classifies the configuration as well-constrained".
     - Stairs: "diagonal methods fail to detect these critical degeneracies, misclassify them as well-constrained cases".
   - DCReg has no independent labels. P7 of the draft argues that no such real-data labels exist, so "was present" contradicts the draft.
   - Also, the parking lot is range-limited: "we limit the LiDAR scanning range to 10 m" (§7.3.1).
8. **Undefined acronyms.**
   - GNSS (P1 S1, and again in P7).
   - SLAM (P1 S2). "such a SLAM system" also has no antecedent.
   - ICP (P3 S2).
   - GICP (P6 S3).
   - Optionally LiDAR (P1 S3).
9. **Structure: "Three problems remain open" (P4) is followed by a fourth gap in P7 ("a further gap").**
10. **P7 S5: close paraphrase of DCReg §9, plus a causal link the source does not make.**
    - Source: "can also stabilize weakly constrained local estimation, but they can also redistribute or mask degeneracy patterns". That is two separate effects, presented in a future-directions remark.
    - The draft's "and thereby mask" turns them into cause and effect.
11. **P7 S2: "a measure of sensitivity" will be read as recall** in a paper that is about detection metrics. DCReg's "detection sensitivity" means how often the detector fires.
12. **P3 S4 and P6 S8: [15] and [16] are characterized loosely.**
    - [16] SuperLoc does not predict "failure". It assesses per-direction observability "before the ICP optimization happens", from scan–map point-to-plane correspondences.
    - [15] Nobili does not predict risk from PCA of normals alone: "individually Ω and α cannot predict alignment failure". The risk ρ = f(overlap Ω, alignability α), where α comes from "PCA on the row vectors of N", the normals of matched planar patches in the overlap region.
13. **Close paraphrases of medium severity:**
    - P4 S2: Hatleskog's list, in the same order.
    - P7 S6: Switch-SLAM's label sentence.
    - P5 S3: the DCReg §2.1.1 sentence skeleton.
    - P2 S4: the DCReg §10 "not only … but also" structure.
    Replacements are in Section D.

Exact replacement text for every item is in the final ranked list (Section F).

---

## B. Claim support, sentence by sentence

| # | Draft claim (abridged) | Verdict | Evidence | Minimal fix |
|---|---|---|---|---|
| P1 S2 | Cadena et al. [1]: a SLAM system must recognize imminent failure, "naming outliers and degeneracies as typical causes" | **S** (wording) | FB §1.3: "the system needs to be aware of imminent failure (e.g., due to outliers or degeneracies)". | "e.g." means examples, not "typical causes". Write "citing outliers and degeneracies as examples". Also define SLAM. "such" has no antecedent. |
| P1 S3 | Nearly every SubT team built around LiDAR, mostly with an IMU [2] | **S** | FB §2.1: "the go-to approach for virtually all teams"; FB §2.2: "Most teams relied on LIDAR and IMU". Both quotes are from the arXiv preprint. | Confirm the wording in the T-RO version. |
| P1 S4 | LOAM and successors use point-to-line/plane on edge/planar features; FAST-LIO2 registers raw points to an incremental map [3]–[6] | **S** | FB §3–§6. | None. |
| P2 S2 | Corridor/tunnel axial slide; "large open spaces and chambers cause similar failures" [2] | **S** | FB §2.3: "(e.g., long corridors, large open spaces, and chambers) … induces failures in LIDAR-odometry approaches based on feature or scan matching". | Optional: for a round tunnel, rotation about the axis is also free. The sentence is 61 words; split it. |
| P2 S3 | Featureless corridors and staircases [7]; seven environments; rotational, translational, or both [8] | **S** | SubT-MRS: "long, featureless corridors … and staircases". GEODE: "seven diverse settings"; "can be categorized into three types: rotational, translational, and a combination of both". | "from stairwells to metro tunnels" is not a range; in GEODE's list the two are adjacent. Use "including stairwells and metro tunnels". |
| P2 S4 | Sparse surroundings and a poor initial pose also under-constrain the problem [9] | **S** (wording) | DCReg §10: "degeneracy stems not only from repetitive geometric features (e.g., tunnels) but also from sparse environments and poor initial poses causing insufficient constraints." | "just as under-constrained" is not in the source. The sentence also mirrors the source's structure; see D. |
| P2 S5 | Along weak directions, the pose reflects noise and the initial guess | uncited; correct | DCReg §1.1: "makes the solution highly sensitive to sensor noise and initial estimates". | Add [9]. |
| P3 S2 | Gelfand [10] used the eigenvalues and condition number of the 6 × 6 matrix to judge ICP stability | **S** | Gelfand: "Our measure of stability, therefore, will be the condition number of the matrix W"; small eigenvalues mean sliding (FB §8.2). | Define ICP. |
| P3 S3 | Zhang [11]: smallest eigenvalue ↔ degeneracy factor; solution remapping updates only well-conditioned directions | **S** | FB §7.2–7.3; DCReg §2.3.1: "restricting updates to well-constrained subspaces". | None. |
| P3 S4a | "recomputed the threshold at every iteration [12]" | **S** | Hinduja abstract: "These directions are selected on the basis of a dynamic threshold, which updates at each iteration." | Context: §III-B applies it "for the loop closure candidates". The general wording is fine. |
| P3 S4b | Three-level localizability per direction [13], [14] | **S** | X-ICP: "localizable, partially-localizable, and non-localizable". LP-ICP: "non-localizable (None), partially localizable (Partial), and fully localizable (Full)". | None. |
| P3 S4c | "predicted alignment failure from the input clouds before registration [15], [16]" | **P** | Nobili: "risk of a failed alignment", "prior to registration" (fits). SuperLoc: "assess constraint observability in each pose direction (X, Y, Z) before the ICP optimization happens", from KD-tree point-to-plane correspondences with map normals. It gives a per-direction confidence (<0.2 means likely degradation), not a failure prediction. | See F-12. |
| P3 S4d | Network trained on simulated data [17] | **S** | "the network is trained exclusively on simulated data". | None. |
| P3 S4e | Probability of degeneracy from a noise model of points and normals [18] | **S** | FB §13.4. | None. |
| P3 S5 | RELEAD constrains filter updates [19]; [20] concluded that active mitigation "matters most" without a reliable external estimate | **S** / **P** | RELEAD: "solving constrained ESIKF updates". [20]: "necessary and advantageous in the absence of reliable external estimate assistance". "matters most" is a comparative the source does not make. | Write "is needed mainly when no reliable external motion estimate is available". |
| P4 S3 | Eigenvalues grow with correspondences and change with weights, scale and noise; tuning does not transfer [18] | **S** | FB §13.1–13.3. | Close paraphrase of the list; see D. |
| P4 S4 | Zhang's threshold came from one sample dataset [11]; [17] needed a cutoff ≥ 110 | **S** | Zhang: "From one sample dataset". Nubert Fig. 4/§VI: thresholds {30, 90, 110}; "an e-value threshold of at least 110 is required to reliably detect degeneracy", tunnel field test. | Move [11] after "Zhang et al.". Structure is close; see D. |
| P5 S3 | Rotational eigenvalues are orders of magnitude larger; minimum eigenvalue misses rotation; the full-Hessian condition number flags translation almost everywhere [9] | **S** | §2.1.1 (lever arm, "making rotational degeneracies particularly elusive"); §7.3.1: ME "systematically overlooks rotational degeneracies"; §7.4.1: FCN treats "all translational dimensions as universally degenerate". FCN-SR flags 99.23% of frames in the well-constrained Building sequence (Table 4). | Close paraphrase of §2.1.1; see D. The 99% figure is strong support and can be cited. |
| P5 S4 | Diagonal blocks remove the scale gap but ignore coupling; "on real stairwell and parking-lot data this hid degeneracy that was present [9]" | **P** | Fig. 13 caption, §7.4.1 and stairs text (quoted in A-7). Both sequences are real. The parking lot is range-limited to 10 m. "Present" rests on DCReg's own Schur test and geometric reasoning, not on labels. | See F-7. |
| P5 S5 | Schur complement = rotation constraint with translation marginalized out, and the reverse | **S**; technically correct | DCReg Eq. 18a/b (S_R and S_t); Thm. 1: "The reduced quadratic after eliminating δt has Hessian S_R"; Prop. 1: "the rotation information that cannot be compensated by translation". | None. |
| P5 S6 | "20–50% better long-duration localization accuracy and typical speedups of 5–30×" | **P** (numbers) / verbatim run | Abstract: "at least 20%–50% improvement in long-duration localization accuracy and typical speedups of 5 − 30× (up to 116× in certain scenarios) over comparable degeneracy-aware baseline methods". | Restore "at least" and reword (F-5). Caution: in the parking lot DCReg is only about 3% better than ME-TSVD (29.56 vs. 30.46 cm), and in Building it is slightly worse than ME-SR (8.65 vs. 8.58 cm). Keep the claim attributed ("reports"), not stated as fact. |
| P6 S3 | Voxelized GICP regularization keeps H_tt well conditioned "in a degenerate tunnel" and hides degeneracy from GN tests [21] | **P** | Abstract: "in voxelized GICP the Gauss--Newton (GN) Hessian masks translational degeneracy, because covariance regularization keeps the translation block artificially well-conditioned"; separately: "straight, uniform tunnels remain unobservable along their axis". | Close paraphrase. The tunnel link is inferred. [21] is a single-author arXiv preprint (Aug. 2026), so do not let a key argument rest on it alone. See F-6. |
| P6 S4a | Point-to-plane H_tt depends only on normals, not on point positions [9] | **S** | DCReg §3.3: "Htt depends solely on the normal distribution, independent of point distances." | None. Mild structural echo of the source. |
| P6 S4b | Gelfand: normal-space sampling constrains only translational sliding [10] | **S** | Gelfand: "normalspace sampling that is aimed at constraining translational sliding"; "Unlike [11], our approach deals with both translational and rotational uncertainties". | Move [10] after "Gelfand et al.". |
| P6 S5 | "Several methods have therefore turned to the normals themselves" | **P** (causal) | LF-GICP's motivation matches ("We bypass this with a regularization-free voxel-normal localizability field"). NV-LIOM and Nobili give other motivations. | Write "Several methods instead work with the normals themselves." |
| P6 S6 | NV-LIOM: smallest eigenvalue of the normal-direction distribution below a threshold [22] | **S** (preprint) | NV-LIO arXiv: "the smallest eigenvalue, λ0, indicates a degenerate case if it falls below a specific threshold". | The RA-L text was not read. Also see E-1 on positioning. |
| P6 S7 | LF-GICP builds a localizability field from voxel normals without regularization [21] | **S** | "regularization-free voxel-normal localizability field". | None. |
| P6 S8 | Nobili: alignment risk from PCA of plane normals [15] | **P** | α from "PCA on the row vectors of N" (normals of matched planar patches in the overlap). Risk from an SVC on (Ω, α). "individually Ω and α cannot predict alignment failure". | See F-13. |
| P7 S2 | Papers report trajectory error or end-point drift [13], [14]; DCReg treats the flagged share as sensitivity, not correctness [9] | **S** | X-ICP: APE, end-position error. LP-ICP: ATE, completion ratio, no labels. DCReg: "DR serves as an indicator of detection sensitivity rather than an error metric." | Terminology clash with recall; see F-11. |
| P7 S4 | Same Schur detector: ATE from 7.44 cm to 164.14 cm depending on mitigation, range-limited corridor [9] | **S** | Table 9 (corridor, range limited to 10 m, DR 58.04%). Schur-based configurations: w/o PCG ("Schur-based detection without mitigation") 164.14; SR 37.75; TReg 22.79; TSVD 17.81; w/o CG 9.22; Full 7.44. "w/o all" (28.54) has no detector and is correctly excluded. | Optional (F-19): 164.14 is *worse* than no degeneracy handling (28.54) even though detections "are not acted upon". A reader of DCReg may flag this anomaly, so the 7.44–37.75 cm span across four mitigations is the safer headline. |
| P7 S5 | Inertial priors stabilize and "thereby mask" degeneracy [9] | **P** | DCReg §9 (future directions): "can also stabilize weakly constrained local estimation, but they can also redistribute or mask degeneracy patterns". A remark; two effects, not cause and effect. | See F-10. |
| P7 S6 | Labels: per direction but simulated [17]; real but per alignment or keyframe [15], [23]; Switch-SLAM: GNSS vs. scan-to-scan ICP per keyframe | **S** | Nubert: "a test set is created in simulation from a ground truth mesh of the tunnel environment"; "the localizability is considered binary". Nobili: "each alignment is manually labelled as a success or a failure". Switch-SLAM §IV-C: "The ground truth is prepared by comparing GNSS data with scan-to-scan matching using ICP [36] at each keyframe". | Close paraphrase of the Switch-SLAM sentence; see F-15. |
| P7 S7 | To our knowledge, no per-direction real-data labels | **S** (hedged) | Also checked: SuperLoc reports no precision or recall; LP-ICP reports no labels; DCReg's degeneracy masks are simulated only (Table 3) or per sequence (Table 2). | Keep the hedge. Unread candidates in `review.md` §D (LiLi 2609.17145) should be checked before submission. |
| P8 S2a | LVI-SAM drops LiDAR odometry constraints when the smallest eigenvalue < threshold [24] | **S** | ar5iv §II-C2: "The LIS reports failure when the smallest eigenvalue of [AᵀA] is smaller than a threshold at the first iteration of optimization." "Lidar odometry constraints are not added to the factor graph when failure happens." | Optional: add "at the first iteration". |
| P8 S2b | Switch-SLAM moves to VO built on VINS-Mono [25] and keeps only the well-conditioned LiDAR directions [23] | **S** | Abstract: "transitions from LiDAR to visual odometry". §III-A: VO uses "the method proposed in [6]" (VINS-Mono). Eq. 15: "Λp denotes the matrix with eigenvalues removed corresponding to degenerate DOFs"; Eq. 16: "executed only along the well-conditioned DOFs". | Precision: what switches is the *initial guess* for scan-to-map matching (Alg. 1). |
| P8 S4 | Camera struggles "under the poor lighting common underground [7]" | **P** | SubT-MRS: "varying lighting conditions"; "limited lighting, such as hospital interiors and caves"; "long, dimly lit corridors"; "poorly illuminated staircases". "Common underground" is a generalization. | Write "for example in the dim caves and corridors of [7]". |
| P9 S2 | A-LOAM is an open implementation of LOAM [26], [3] | **S** | Repository About text: "Advanced implementation of LOAM". | T is computed from the scan, not "on the scan-to-scan problem". Minor wording. |
| P9 S3 | Schur complement on the 6 × 6 Hessian, following [9] | **S** | | |
| P9 S4 | Bingham model for sign-free directional data [27], [28] | **S** (title-level) | Bingham title: "An antipodally symmetric distribution on the sphere". The primary texts were not read (FB §25). | Write "Bingham distribution". Check Mardia & Jupp in a library copy. |
| P9 S5 | H_tt = N**T** with unit weights and identical normals | **technically conditional** | DCReg Eq. 7c: H_tt = Σ nᵢnᵢᵀ for point-to-plane. Correct only for the point-to-plane part with the same normals. Edge residuals add to H_tt. A-LOAM `DISTORTION 0` means s = 1, so there is no hidden weight. | F-3. |
| P9 S6 | Hessian uses "normals of planes fitted to the map" | **N** for scan-to-scan | `lidarFactor.hpp` L57–66: `ljm_norm = (last_point_j - last_point_l).cross(last_point_j - last_point_m)`. Map-plane fitting exists only in `laserMapping.cpp` (`LidarPlaneNormFactor`). | F-1. |
| P9 S7 | "carries no rotational information [10]" | **P / technically false** | Gelfand supports translation-only *targeting* and lever-arm dependence of rotation, not "no information". | F-2. |
| P10 S1 | Public datasets that release survey-grade maps with GT trajectories [7], [8], [29] | **P** | SubT-MRS: FARO maps. GEODE: "ground-truth maps for select indoor sequences" (RTC360, stairs). FusionPortable: BLK360 maps for indoor sequences only. | F-4. |
| P10 S2 | "Following the perturbation idea of [17]" | **P** | Nubert ray-casts a *new* child scan at each perturbed pose and registers it scan-to-scan. The draft rigidly displaces a real scan and registers it to a map. | Say "adapt" (F-21). |
| P10 S3 | Some trajectories were obtained by aligning LiDAR to the map [7], [29] | **S, incomplete** | SubT-MRS §3.2: "point-to-point, point-to-plane, and point-to-line correspondences … between the Ground Truth map and the current LiDAR scan", fused with VO, LO and IMU. FP §IV-B: "the NDT-based 6-DoF localization" against the prior map. GEODE stairs: PALoc in the RTC360 map. | Add [8] (F-4). |

**Numbers checked:**

| Item | Draft | Source | Status |
|---|---|---|---|
| ATE span | 7.44 and 164.14 cm | Table 9 | exact |
| Accuracy gain | 20–50% | "at least 20%–50%" | "at least" dropped; restore it |
| Speedup | 5–30× | "typical 5 − 30× (up to 116×)" | exact |
| Cutoff | ≥ 110 | Nubert §VI | exact |
| Environments | seven | GEODE | exact |
| Degeneracy types | three | GEODE §4.2.2 | exact |

---

## C. Uncited claims and technical statements

**Uncited claims that should carry a citation:**
- P2 S5 (pose along weak directions reflects noise and the initial guess). Add [9] (DCReg §1.1).
- P6 S2 ("assembled only from the correspondences that were found"). Optionally add [9]: DCReg §10, "pose estimation depends entirely on correspondence pairs that evolve with initial poses during iteration".
- P1 S1 (GNSS-denied inspection) and P3 S1 (Hessian-based detection is the usual approach) are acceptable without a citation. [2] and [9] could be added.

**Technical statements:**
- **Schur complement meaning (P5 S5): correct.** In information form, S_R = H_RR − H_Rt H_tt⁻¹ H_tR is the rotation information with translation marginalized. Equivalently, it is the Hessian of the problem reduced over translation (DCReg Thm. 1, Prop. 1).
- **N**T** identity (P9 S5): correct only as a conditional** (see A-3).
- **"Normals of planes fitted to the map" (P9 S6): wrong for scan-to-scan** (see A-1).
- **"No rotational information" (P9 S7): false as worded** (see A-2).
- **Scan-to-scan detector against scan-to-map labels (P9/P10): an unacknowledged mismatch.** Two ways to resolve it:
  - (a) Compute the Hessian channel in A-LOAM's `laserMapping` (scan-to-map), so that it matches the labels.
  - (b) Keep scan-to-scan and say in the Introduction that the labels describe scan-to-map observability.
- **Labels "from the scene rather than from any detector" (P10 S1).** The labels also depend on the re-registration algorithm and its convergence basin (DCReg §8). Say "by re-registration against a survey map", not "from the scene".
- **P2 S2.** For a round tunnel, rotation about the axis is also free. Optional clause.
- **Positive point the draft does not use.** A-LOAM takes no IMU input, so the inertial-masking confound raised in P7 does not apply to the channels as computed. One clause in P9 would turn that confound into a design advantage.

---

## D. Plagiarism and close paraphrase

**Script result (draft against all fact-bank quotes):**
- One run of 7 or more words: "long-duration localization accuracy and typical speedups of" (DCReg abstract).
- No other runs of 6 or more words. The other 4- and 5-grams are technical terms ("edge and planar features", "the smallest eigenvalue of", "of at least 110").
- Several 6- and 7-gram matches against `review.md` come from reviewer-suggested wording, not from sources. They are not a plagiarism concern.

**Manual comparison against source sentences:**

| Severity | Draft | Source | Issue | Replacement |
|---|---|---|---|---|
| High | P5 S6 "…long-duration localization accuracy and typical speedups of 5–30×…" | DCReg abstract | Seven verbatim words, same sentence skeleton | F-5 |
| High | P6 S3 "covariance regularization can keep the translational block well conditioned" | LF-GICP: "covariance regularization keeps the translation block artificially well-conditioned" | Same words; only the inflections change | F-6 |
| Medium | P5 S3 "rotational eigenvalues are typically orders of magnitude larger than translational ones" | DCReg §2.1.1: "rotational eigenvalues typically exceed translational ones by orders of magnitude" | Same lexical skeleton | F-17 |
| Medium | P7 S5 "stabilize a weakly constrained estimate and thereby mask its degeneracy" | DCReg §9: "stabilize weakly constrained local estimation, but … mask degeneracy patterns" | Same words in the same order | F-10 |
| Medium | P7 S6 "comparing GNSS with scan-to-scan ICP at each keyframe" | Switch-SLAM: "comparing GNSS data with scan-to-scan matching using ICP [36] at each keyframe" | Near-verbatim with words deleted | F-15 |
| Medium | P4 S2 "number of correspondences … residual weights, scene scale, and sensor noise" | Hatleskog: "number of measurements, weights, the scale of the environment and sensor noise" | Same list in the same order | F-16 |
| Low–medium | P2 S4 "Repetitive structure is not the only cause, since sparse surroundings and a poor initial pose…" | DCReg §10: "not only from repetitive geometric features … but also from sparse environments and poor initial poses" | Mirrored structure | F-18 |
| Low–medium | P4 S4 "a cutoff of at least 110 before degeneracy was detected reliably" | Nubert: "threshold of at least 110 is required to reliably detect degeneracy" | Mirrored structure | F-19 |
| Low (acceptable) | P6 S4a (H_tt from normals), P6 S6 (NV-LIOM), P7 S2 ("sensitivity rather than"), P8 S2a (LVI-SAM), P2 S2 ("large open spaces and chambers"), P1 S4 (FAST-LIO2) | | Technical vocabulary; short runs | No change needed. |

---

## E. Style and IEEE conventions

**Positioning risk a reviewer will raise:**
- NV-LIOM [22] already thresholds the smallest eigenvalue of the normal-direction distribution, which is essentially **T**. P9 and Contribution 1 should say in one clause what is new: the pairing with the Schur channel, the analysis of when the two disagree, and the Bingham reading.
- If true and verified against the RA-L text, also say whether NV-LIOM uses a mean-subtracted covariance or the second moment.
- Contribution 3's benchmark also leaves out two detectors the Introduction discusses: the full-Hessian condition number [12] and Switch-SLAM's χ²-normalized detector [23]. Either add them or say why they are left out.

**Specific style issues:**
1. **Count mismatch.** "Three problems remain open" is followed by a fourth ("a further gap"). Fix as in F-9.
2. **Acronyms.** Define GNSS, SLAM, ICP and GICP at first use. LiDAR is optional but safer. IMU is already defined.
3. **Citation placement.** IEEE practice puts the number right after the named work:
   - "Zhang et al. [11] set …"
   - "Gelfand et al. [10] observed …"
   - "Nobili et al. [15] …"
   - "NV-LIOM [22] declares …"
   - "LF-GICP [21] builds …"
   - "LVI-SAM [24] leaves …"
   - "Switch-SLAM [23] moves …"
4. **Number format.** Match the source: "20%–50%".
5. **Wording.**
   - Use "Bingham distribution", not "Bingham model".
   - "on purpose" → "deliberately".
6. **Generic or informal phrasing to replace.**
   - "Inertial priors add another layer" (stock phrase).
   - "weighted as the solver chose" (informal).
   - "a targeted preconditioned solver" ("targeted" is DCReg's own marketing adjective).
7. **"therefore" appears three times** (P5 S5, P6 S5, P9 S7). The P6 instance asserts a causal link the sources do not support.
8. **Punctuation.** Three colons and one semicolon in about 1,360 words is acceptable. The P2 S1 colon could become a full stop.
9. **Sentence length.** P2 S2 is 61 words chained with "but … and". Split it.
10. **Signposting.** "The first is … The second problem is … The third problem is …" is acceptable once the count is fixed. It does not read as machine-written.

**What the draft does well:**
- No "In recent years", "plays a crucial role", or "Moreover/Furthermore" chains.
- American spelling throughout.
- En dashes in "Gauss–Newton" and in citation ranges.
- Bold matrices.
- Numbered contributions.
- Standard IEEE roadmap.
- Reference numbering in order of first appearance (checked [1]–[29]).

---

## F. Ranked must-fix list with exact replacement text

**F-1 (P9 S6, technical error).** Replace:
> In a working estimator the two differ: the Hessian contains only matched points, robust weights, normals of planes fitted to the map, and edge residuals as well, whereas **T** is computed from the raw scan before any matching.

with:
> In a working estimator the two differ. The Hessian contains only the matched points, carries Huber weights, takes each normal from a plane through three points of the previous sweep, and also includes edge residuals, whereas **T** is computed from the current scan before any matching.

Then add at the end of P10 S2:
> Because the labels describe scan-to-map registration while both channels are computed on A-LOAM's scan-to-scan problem, Section IV also reports how often the two registration problems agree on the weak directions.

Alternative: move the Hessian channel to A-LOAM's scan-to-map stage. Then "normals of planes fitted to the map" becomes correct, and "scan-to-scan" in P9 S2 must change.

**F-2 (P9 S7).** Replace:
> The orientation channel is therefore independent of the registration step, but it carries no rotational information [10], so we test it as a complement to the Schur channel and not as a replacement.

with:
> The orientation channel is therefore independent of the registration step, but it cannot confirm that rotation is constrained, because rotational constraint depends on each point's lever arm, which **T** discards [10]. We test it as a complement to the Schur channel and not as a replacement.

**F-3 (P9 S5).** Replace:
> With unit weights and identical normals, the translational Hessian block equals N**T**, where N is the number of point-to-plane residuals.

with:
> If the Hessian contained only point-to-plane residuals, with unit weights and the same N unit normals as **T**, its translational block would equal N**T**.

Also align Contribution 1 with whatever the Schur channel actually uses. If edges are included, replace "the Schur complement of the point-to-plane Hessian" with "the Schur complement of the registration Hessian".

**F-4 (P10 S1 and S3).** Replace S1:
> To score the channels fairly, degeneracy is labeled from the scene rather than from any detector, using public datasets that release survey-grade maps together with ground-truth trajectories [7], [8], [29].

with:
> To score the channels fairly, degeneracy is labeled by re-registration against a survey map rather than by any detector, using those sequences of three public datasets that come with both a terrestrial laser-scanner map and a reference trajectory [7], [8], [29].

Replace S3:
> Because some of these trajectories were themselves obtained by aligning LiDAR data to the map [7], [29], scans whose ground-truth pose disagrees with the map are excluded, and the sensitivity of the labels to the perturbation size is reported.

with:
> Because these reference trajectories were themselves obtained largely by aligning LiDAR data to the same maps [7], [8], [29], scans whose reference pose disagrees with the map are excluded, and the sensitivity of the labels to the perturbation size is reported.

**F-5 (P5 S6, verbatim run).** Replace:
> Together with a targeted preconditioned solver, it reports 20–50% better long-duration localization accuracy and typical speedups of 5–30× over the baselines it compares against.

with:
> Combined with a preconditioned conjugate-gradient solver that acts only on the flagged directions, DCReg reports localization errors over long runs that are at least 20%–50% lower, and solve times typically 5–30 times shorter, than those of the degeneracy-aware baselines it was tested against [9].

**F-6 (P6 S3, close paraphrase; defines GICP).** Replace:
> In voxelized GICP, covariance regularization can keep the translational block well conditioned in a degenerate tunnel and so hide the degeneracy from Gauss–Newton-based tests [21].

with:
> Im [21] shows that in voxelized generalized ICP (GICP), the regularization applied to local covariances can make the translational block look well conditioned when the scene leaves a translation unconstrained, so Gauss–Newton-based tests miss the degeneracy.

**F-7 (P5 S4, unsupported "was present").** Replace:
> Analyzing the rotational and translational diagonal blocks separately removes the scale gap but ignores their coupling, and on real stairwell and parking-lot data this hid degeneracy that was present [9].

with:
> Analyzing the rotational and translational diagonal blocks separately removes the scale gap but ignores their coupling. On a real stairwell sequence and a range-limited parking-lot sequence, DCReg shows the block-wise test passing frames that its Schur analysis, in line with the scene geometry, marks as degenerate [9].

**F-8 (acronyms and P1 S2 antecedent).**
- P1 S1: replace "without a usable GNSS signal" with:
  > without a usable global navigation satellite system (GNSS) signal
- P1 S2: replace the sentence with:
  > Cadena et al. [1] argued that a simultaneous localization and mapping (SLAM) system meant for long-term operation must also recognize when it is about to fail, citing outliers and degeneracies as examples.
- P3 S2: replace "to judge how stably ICP can align two surfaces" with:
  > to judge how stably the iterative closest point (ICP) algorithm can align two surfaces
- P1 S3 (optional): replace "built its localization around LiDAR" with:
  > built its localization around light detection and ranging (LiDAR)

**F-9 (count mismatch).**
- P4 S1: replace "Three problems remain open." with:
  > Detection itself has three open problems.
- P7 S1: replace "How detectors are evaluated is a further gap." with:
  > Evaluation is a separate weakness.

**F-10 (P7 S5).** Replace:
> Inertial priors add another layer, because they can stabilize a weakly constrained estimate and thereby mask its degeneracy [9].

with:
> Inertial priors confound the picture further, and DCReg notes that a strong IMU prior can steady a poorly constrained estimate while also obscuring which directions were weak [9].

**F-11 (P7 S2, "sensitivity").** Replace:
> and DCReg treats the share of frames it flags as a measure of sensitivity rather than of correctness [9].

with:
> and DCReg uses the share of frames it flags as an indication of how readily a detector fires, explicitly not as an error measure [9].

**F-12 (P3 S4, SuperLoc and Nobili).** Replace:
> predicted alignment failure from the input clouds before registration [15], [16] or with a network trained on simulated data [17],

with:
> estimated, before the solver runs, how likely an alignment is to fail or which directions it will leave weak [15]–[17], in [17] with a network trained on simulated data,

**F-13 (P6 S5–S8).**
- Replace "Several methods have therefore turned to the normals themselves." with:
  > Several methods instead work with the normals themselves.
- Replace "and Nobili et al. predict alignment risk from a principal component analysis of plane normals [15]." with:
  > and Nobili et al. [15] predict alignment risk from the overlap of two clouds together with a principal component analysis of the normals of planar patches in that overlap.

**F-14 (P8 S4).** Replace:
> for example under the poor lighting common underground [7].

with:
> for example in the dim caves and corridors recorded in [7].

**F-15 (P7 S6, close paraphrase).** Replace:
> …[15], [23]; in Switch-SLAM they came from comparing GNSS with scan-to-scan ICP at each keyframe.

with:
> …[15], [23]. Switch-SLAM, for instance, built its keyframe labels by checking scan-to-scan ICP against GNSS.

**F-16 (P4 S2, close paraphrase).** Replace:
> Hessian eigenvalues grow with the number of correspondences and change with residual weights, scene scale, and sensor noise, so a cutoff tuned for one robot and environment is unlikely to carry over to another [18].

with:
> Each correspondence adds to the Hessian, so its eigenvalues scale with the number of points, and they also shift with sensor noise, robust weights, and the size of the scene. A cutoff tuned for one robot and environment is therefore unlikely to carry over to another [18].

**F-17 (P5 S3, close paraphrase).** Replace:
> In LiDAR registration, rotational eigenvalues are typically orders of magnitude larger than translational ones, so a minimum-eigenvalue test tends to overlook rotational degeneracy, whereas a condition number of the full Hessian flags the translational directions almost everywhere [9].

with:
> Because each rotational Jacobian entry is scaled by a point's lever arm, the rotational eigenvalues of a LiDAR registration Hessian are usually far larger than the translational ones, often by orders of magnitude. A minimum-eigenvalue test therefore tends to miss rotational degeneracy, while a full-Hessian condition number flags translation almost everywhere and marked 99% of frames as degenerate even on a well-constrained building sequence [9].

The 99% figure is DCReg's FCN-SR degeneracy ratio on Building (99.23%, Table 4). The per-direction pattern (all three translations flagged) is shown in Fig. 12 for the parking lot.

**F-18 (P2 S4).** Replace:
> Repetitive structure is not the only cause, since sparse surroundings and a poor initial pose can leave a registration problem just as under-constrained [9].

with:
> Self-similar geometry is only one route to an under-constrained problem, and sparse returns or a poor initial guess can lead there too [9].

**F-19 (optional; P4 S4 and P7 S4).**
- P4 S4: replace the sentence with:
  > Zhang et al. [11] set theirs from a single sample dataset, and in the tunnel field test of [17] an eigenvalue detector caught the degeneracy only when its cutoff was raised to 110, the largest of the three values tried.
- P7 S4: replace the sentence with:
  > In DCReg's ablation on a range-limited corridor, the same Schur-based detector gave trajectory errors from 7.44 cm to 37.75 cm depending on which mitigation followed it, and 164.14 cm when its detections were not acted on [9].

**F-20 (P2 S3).** Replace:
> from stairwells to metro tunnels

with:
> including stairwells and metro tunnels

**F-21 (P10 S2).** Replace:
> Following the perturbation idea of [17], each real scan is displaced along a set of directions at its ground-truth pose and registered back to the map, and a direction is labeled degenerate when the displacement is not recovered.

with:
> We adapt the perturbation labeling of [17], which ray-casts simulated scans at perturbed poses, to real data. Each real scan is displaced along a set of directions from its reference pose and registered back to the map, and a direction is labeled degenerate when the displacement is not recovered.

**F-22 (P2 S5, add citation).** Replace:
> that pose reflects noise and the initial guess, and the error is carried into the map.

with:
> that pose reflects noise and the initial guess [9], and the error is carried into the map.
