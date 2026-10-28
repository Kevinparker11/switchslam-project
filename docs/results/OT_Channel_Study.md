# R + T + OT on the A-LOAM stack: how to use the orientation-tensor channel (study of 28 Oct 2026)

The owner fixed the structure. Schur R and Schur T are judged separately, plus the additional T: the orientation tensor of the scan normals, which is never discarded. The tasks were:
- find the best way to use the orientation tensor;
- reach the F8/F16-with-loops results on the A-LOAM front end, so that GenZ-LIO and iG-LIO are not needed.

How the numbers were made:
- **Everything is an offline replay.** The real `fusion_node_v2` callbacks are driven by 12 logged F8 runs (MF 1-6, LC 1-3, C02 1-3) and their keyframe scans. The tool is `fusion_v4/ot_study/node_harness.py`, with SAH processed synchronously and each sequence's own LiDAR-IMU extrinsic.
- **The A-LOAM poses are the logged ones (open loop)**, so only the fusion changes. The F8 setting replays all 12 logged live runs exactly. Other settings are approximations, because live runs feed the fused pose back into A-LOAM.
- **All three sequences are development data.** MF was used for the C_T calibration; LC and C02 for SAH development.
- **Selection rules were written before each stage** (`fusion_v4/ot_study/PREREG.md`).
- **One correction:** a first pass used the MF extrinsic on the corridors. It was noticed, everything on LC and C02 was rerun, and the selections were re-checked with the same rules (they did not change). Only the corrected numbers are reported here.
- **Nothing in this document is a live result.**

## Summary
ATE RMSE (m), full span, Umeyama SE(3), no scale; mean of the logs.

| Config | MF (6) | LC (3) | C02 (3) | MF + loops | LC + loops | C02 + loops |
|---|---|---|---|---|---|---|
| F8 (T only) | 0.626 | 4.533 | 2.119 | 0.347 (live, same 6 logs) | 2.67 (live, 3) | 2.10 (live, 3) |
| F16 (T + SAH) | 0.560 | 1.983 | 1.709 | 0.456 | 1.490 | 1.402 |
| F17 (R + T + SAH) | 0.560 | 1.983 | 1.709 | = F16 | = F16 | = F16 |
| **F20 (R + T + OT)** | **0.558** | **2.010** | **1.710** | **0.469** | **1.455** | **1.481** |
| Switch-SLAM, published | 1.61 | 2.42 | none | | | |

F20 = Schur R with the rotation check + Schur T + the orientation-tensor channel. The OT channel is a fail-safe cap from the geometric tensor of the keyframe scan, plus the heading read-out (SAH) from the same normals. Live F16 + loops for comparison: MF 0.523 ± 0.224, LC 1.538 ± 0.304, C02 1.250 ± 0.435 (6 runs each).

- **Goal check (replay).**
  - F20 matches F16 with and without loops: front end within 0.03 m; with loops MF +0.013, LC -0.035, C02 +0.079 m. The C02 difference is one log, where one loop fewer was accepted.
  - F20 is far below Switch-SLAM on MF (0.47 vs 1.61) and LC (1.46 vs 2.42, and 2.01 without loops).
  - On MF with loops it does not reach F8 + loops (0.469 vs 0.347). The same gap exists for F16, both in replay (0.456) and live (0.523). It comes with SAH and stays unexplained (stage 4).
- **R channel:** its rotation check never closed on any of the 12 logs (F17 = F16 to the last digit). It costs nothing; these bags cannot show its value.
- **OT with the plain planar-normal tensor:** every rule that lowers the LiDAR information made the corridors worse, LC by 0.26-0.59 m and C02 by 0.41-1.00 m. The planar tensor leaves out edges and so understates the constraint A-LOAM really has.
- **OT with the geometric tensor:** counting edges as well, each line with direction d contributing (I - d dᵀ)/2, makes the fail-safe cap neutral: MF -0.002, LC +0.027, C02 +0.001 m.
- **Injected solver fault:** under a confident but wrong LiDAR slide, F20 beats F16 on 12 of 12 logs (sign test p = 0.0005). The gain is small, 2-5 %.
- **Heading:** the read-out of the same normals' orientation distribution (SAH, section 4) is where the large gains come from: LC 4.53 to 1.98 m and C02 2.12 to 1.71 m in replay; LC 4.53 to 2.27 m live.

## 1. The structure (fixed)
- **R: the Schur rotation block S_RR** (radians, D_RAD), judged on its own.
  - In healthy operation the rotation comes from the VIO (c_R = 0) and R is monitored.
  - When the VIO rotation disagrees with the LiDAR rotation beyond the frozen references, the LiDAR rotation carries the step with W_R = (S_RR + 10⁻³ I)⁻¹ S_RR. This is ROT_CHECK, design B.
  - The references are 0.402 rad over 2 s and 0.585 rad over 10 s, the largest values on 19 MF recordings.
- **T: the Schur translation block S_tt**, with the rotation coupling removed. Weight W_t = (c S + I)⁻¹ c S, c = 0.03, frozen on MF.
- **OT: the orientation-tensor channel (the "additional T")**, computed per LiDAR keyframe from the raw points only. It uses no correspondences and no solver state.
  - T = (1/n) Σ n nᵀ over the planar normals. T is the sufficient statistic of the Bingham distribution of the normals: every Bingham parameter is a function of T's eigen-decomposition.
  - The geometric tensor G = (Σ_planar n nᵀ + Σ_linear (I - d dᵀ)/2) / (n_planar + n_linear) also counts edges.
  - Both come from the same k = 12 PCA that SAH already runs (`structure_heading.scan_tensors`). Planar means (λ2 - λ1)/λ3 > 0.5; linear means (λ3 - λ2)/λ3 > 0.5.
  - Between keyframes the tensor is rotated into the current LiDAR frame.
- **Not claimed:** separating R and T with Schur complements (DCReg, Selective KF, MM-LINS), or separate rotation and translation weights because of the unit difference (D²-LIO).

## 2. Literature: who already uses an orientation tensor of normals
- **LF-GICP** (arXiv 2608.19522, Aug 2026 preprint, read through a review synopsis).
  - Builds M = Σ ρ_v n_v n_vᵀ from planarity-weighted map normals.
  - Uses λ_min/tr and λ_min/|V|, with thresholds and hysteresis, to gate a Fisher-information reweighting of GICP correspondences.
  - Argues that the Gauss-Newton Hessian masks degeneracy.
  - LiDAR-only, no VIO, no heading use.
  - **The orientation tensor as a solver-independent degeneracy measure is prior art.**
- **LiLi** (arXiv 2609.17145): independent of the Hessian, but by re-optimising from perturbed starts, not from normals.
- **D²-LIO** (arXiv 2508.14355): separate rotation and translation weights because of the scale difference.
- **Hatleskog & Alexis** (arXiv 2410.10784): noise-aware point-to-plane degeneracy.
- **Straub et al.** (arXiv 1709.05774): Bingham/vMF mixtures of surfel normals.
- **X-ICP and LP-ICP:** localizability from per-point normal contributions.
- **Information-aware odometry** (arXiv 2607.13516): a sampled Hessian, no normals.
- **Heading from walls:** Manhattan LiDAR SLAM (Remote Sens. 15(1):15), visual Manhattan systems, and histogram-of-normals alignment for loop closure (Lin & Zhang, arXiv 1909.11811).
- **Second- and fourth-order orientation tensors:** standard in fibre-orientation statistics (Advani & Tucker, J. Rheology 31, 1987).

**Not found in the papers read:**
- the tensor (with edges counted) as a direction-by-direction, threshold-free cap on the Schur translation information inside a VIO-primary weight;
- one orientation-distribution channel that gives both that cap and the heading anchor.

This is a negative search, not a proof that nobody has done it.

## 3. Every way to use the orientation tensor, and the results
Along each Schur eigen-direction v_i there are two numbers:
- the solver's information λ_i;
- the raw-geometry support τ_i = N v_iᵀ T v_i, with N = tr(H_tt).

Because both use the same total mass, there is no free scale. If the Hessian were N·T exactly, τ_i ≥ λ_i would hold and a cap could never bind.

| # | Use | Rule | Free constants | Replay, F16 + rule, mean m (MF / LC / C02) |
|---|---|---|---|---|
| A1 | fail-safe cap (planar tensor) | min(λ, τ) | none | 0.563 / 2.511 / 2.508 |
| A2 | harmonic mean | 2λτ/(λ+τ) | none | 0.569 / 2.350 / 2.309 |
| A3 | geometric mean | √(λτ) | none | 0.570 / 2.243 / 2.121 |
| A4 | tensor alone | τ | none | 0.583 / 2.510 / 2.505 |
| A5 | solver unless they disagree by more than 2× | λ or τ | factor 2 (a priori) | 0.567 / 2.510 / 2.460 |
| A6 | hybrid Schur | N T - H_tR H_RR⁻¹ H_Rt | none | 0.572 / 2.568 / 2.708 |
| A7 | optimistic | max(λ, τ) | none | 0.580 / 1.983 / 1.696 |
| **A1-G** | **fail-safe cap on the geometric tensor G (chosen, F20)** | min(λ, τ_G) | none | **0.558 / 2.010 / 1.710** |
| A7-G | optimistic on G | max(λ, τ_G) | none | 0.584 / 1.959 / 1.589 |
| B | hard gate on λ_min(T)/tr (LF-GICP style) | threshold | 1-2 | not run: needs thresholds; A1-A4 are its soft forms |
| C | inside A-LOAM's solver (reweight or remap along the tensor's weak axis) | C++ change | weights | not run: cannot be replayed from logs |
| D | heading from the orientation distribution (SAH) | section 4 | frozen SAH design | F8 → F16: 0.626 → 0.560 / 4.533 → 1.983 / 2.119 → 1.709 |
| E | loop factor shaped by the tensor of the matched normals, Λ_t = 3T/msd (same trace as the standard isotropic factor) | | none | with loops, F20 MF / LC / C02: iso 0.469 / 1.455 / 1.481, tensor 0.470 / 1.475 / 1.479: no gain, not adopted |

Baseline F16 (front end): 0.560 / 1.983 / 1.709.

**Stage 1, planar tensor.**
- Only A7 met the pre-written no-harm rule (within 0.05 m of F16 on LC and C02).
- Every rule that lowers the LiDAR information lost 0.26-1.0 m on the corridors.
- Reading: the planar-only tensor understates the translational support of A-LOAM's own solution. A-LOAM's Hessian also uses edge features (door frames, pipes, corners), and those are what constrain a corridor axis.

**Stage 2, geometric tensor (rule written before it was run).**
- With edges counted, the principled fail-safe A1 became admissible and was chosen by the pre-written rule, which prefers the fail-safe.
- The optimistic A7-G was better on C02 (1.589 vs 1.709) but worse on MF (0.584). It was not chosen; that is an observation, not a result.
- On healthy data the cap binds in 90-99 % of fused scans, but mildly. The median λ'/λ is 0.81 (MF), 0.89 (LC) and 0.85 (C02), and at most 0.2 % of scans fall below 0.5.
- Because W = cλ/(cλ+1) with c·N ≫ 1, the weight changes only where the raw geometry has almost no support (c·N·vᵀGv ≲ 1). That is the intended behaviour of a threshold-free fail-safe.

**Stage 3: when does it add value? (written before it was run)** A solver fault was injected into the real logs, the thesis case "solver confident but wrong":
- three 20 s windows per log, at 25 / 50 / 75 % of its length;
- in each window the LiDAR position slides along the weakest Schur direction at 0.2 m/s, i.e. 4 m per window, and the slide stays in the pose afterwards;
- H_tt is replaced by tr(H_tt)/3·I, the wrong correspondences that look like constraint;
- the keyframe scans and the VIO are untouched.

| | F16 | F20 | F20 better |
|---|---|---|---|
| MF (6) | 3.807 | 3.723 | 6 / 6 (-2.2 %) |
| LC (3) | 3.717 | 3.619 | 3 / 3 (-2.7 %) |
| C02 (3) | 4.810 | 4.562 | 3 / 3 (-5.2 %) |

- F20 is better on 12 of 12 logs (sign test p = 0.0005), but the protection is small.
- Where the real geometry does support the slide direction, the tensor cannot tell that the solver is wrong. It protects only where the scene is truly degenerate along the slide, which is why the gain is largest on Corridor02.
- This demonstrates the mechanism under a fault model chosen by me. It says nothing about how often such faults happen in real data.

**Stage 4: the heading read-out in the back end (written before it was run).**
- The idea: tell the pose graph where SAH injected heading, by adding (Σ|corr|)² about the gravity axis to that keyframe step's covariance, so that loops can undo it.
- MF + loops: 0.469 with this change and 0.469 without (model `iso_sah`).
- The corrections inside one keyframe step are small next to the 1.46° per-step odometry sigma already used.
- Not adopted. The MF loop gap stays unexplained.

## 4. Why SAH is the rotational read-out of the same orientation distribution (an identity, not a relabel)
SAH measures the heading error as the shift that best aligns the axial histogram h(θ) with a reference. h(θ) is the histogram of horizontal directions of the keyframe's near-vertical planar normals.
- Axial data are π-periodic: h(θ) = Σ_k c_k e^{i2kθ}.
- The circular cross-correlation SAH maximises is C(ψ) = Σ_k c_k conj(c_k^ref) e^{-i2kψ}.
- The pair c_k is fixed by the horizontal deviatoric part of the orientation tensor of order 2k: k = 1 is T's horizontal block, k = 2 is the fourth-order tensor, and so on.
- So SAH aligns the whole family of even-order orientation tensors of the same normals, and the histogram smoothing acts as a low-pass weight on the orders.
- **Why T alone is not enough for heading:** with two equally strong orthogonal wall families, T's horizontal block is isotropic and c_1 = 0. The fourth order is the first that sees the walls.
- So the OT channel has two read-outs of one object, the orientation distribution of the scan's planar normals: its second moment (eigenvalues, via G) checks the translation, and its alignment gives the heading.
- The SAH design is unchanged and frozen (gates, Kalman update, 0.25° per scan). It was developed on LC and C02.

## 5. Final configuration F20 (`run_fusion_study.sh`, FRONT=aloam)
`FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1 ROT_CHECK=1 OT_SRC=geom OT_MODE=min`
- No new tuned constant.
- OT_MODE=off reproduces F16 bit for bit (checked on LC run 1 against the previous node).
- The tensor reuses the SAH k-NN, so the extra cost is negligible.
- Back end unchanged: iso, 1 round, odometry sigma 1.46° / 0.054 m.
- The tensor-shaped loop factor (`--models ... ot`) is in the code for the record only.
- F18 (TCAP: a per-scan planar tensor from `/laser_cloud_surf_last`) was superseded before its first full run; only its 70 s smoke run exists.

## 6. Live test of F20 (pre-registered here, before any run): `fusion_v4/run_f20_batch.sh`
- **Runs:** 3 live runs per sequence, at the same rates as F16 (LC 0.5×, MF 0.5×, C02 0.33×), with keyframes recorded.
- **Back end:** none / iso / ot on every run.
- **P1 (structure works live):**
  - the OT tensor is present on ≥ 90 % of fused rows;
  - the rotation check closes on no row, or the closed spans are reported.
- **P2 ("same as F16") — each mean must lie inside the F16 live range:**

  | | MF | LC | C02 |
  |---|---|---|---|
  | Front end | 0.53-0.80 | 1.99-3.17 | 1.64-1.84 |
  | With loops (iso) | 0.363-0.955 | 1.312-2.125 | 0.807-1.853 |

- **P3 (within the published Switch-SLAM numbers):**
  - with loops, every run is below 1.61 (MF) and 2.42 (LC);
  - the LC front-end mean is below 2.42.
- **Not predicted:** matching F8 + loops on MF (0.347). Replay says F20 + loops ≈ 0.47 there.
- All runs are reported, including failed starts.

## 7. What can be claimed, and what cannot
- **Supported (replay, development data; live confirmation pending):**
  - A VIO-primary fusion on A-LOAM with three separately judged channels: Schur R, Schur T, and a solver-independent orientation-tensor channel.
  - In that channel, the edge-aware geometric tensor caps the Schur translation information direction by direction, with no threshold and no scale (N = tr(H_tt)). It is neutral on healthy data and protective (small, 12/12) under a confident-but-wrong solver fault.
  - The same orientation distribution anchors the heading, which is where the large corridor gains come from.
  - F20 matches F16 with and without loops, and is below the Switch-SLAM numbers on MF and LC.
- **Not supported:**
  - that the tensor improves accuracy on healthy data;
  - that the R channel improves these results (it never acts on them);
  - "first to use an orientation tensor" (LF-GICP);
  - "first to separate R and T" (DCReg);
  - that the planar Bingham/orientation tensor is a good cap for A-LOAM (it is not; edges are needed);
  - matching F8 + loops on MF.

## 8. Limits
- Open-loop replay on development data, 12 logs. The live runs (`run_f20_batch.sh`) are still to be done.
- The fault model is mine, chosen to be the case the fail-safe is meant for.
- Literature on LF-GICP, LiLi and D²-LIO was read through summaries.
- With SAH_SYNC = 0 the live keyframe tensor arrives one processing delay later than in the replay.
- The MF loop gap with SAH is unexplained.

Sources: [LF-GICP](https://pith.science/paper/2608.19522), [LiLi](https://pith.science/paper/2609.17145), [D²-LIO](https://arxiv.org/html/2508.14355), [Hatleskog & Alexis](https://arxiv.org/html/2410.10784v2), [information-aware odometry](https://arxiv.org/pdf/2607.13516), [Lin & Zhang loop closure](https://arxiv.org/pdf/1909.11811), [orientation tensors (Tucker keynote)](https://ecm-academics.plymouth.ac.uk/jsummerscales/FPCM/FPCM15/FPCM15_keynote_Tucker_fibre_orientation_descriptors.pdf), [Selective KF](https://arxiv.org/html/2412.17235v1), [DCReg](https://arxiv.org/abs/2509.06285).
