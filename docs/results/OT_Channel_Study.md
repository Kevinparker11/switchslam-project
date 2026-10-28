# R + T + OT on the A-LOAM stack: how to use the orientation-tensor channel (study of 28 Oct 2026)

Goal set by the owner: keep the structure fixed (Schur R and Schur T channels judged separately, plus the additional T = orientation tensor of the scan normals, never discarded), find the best way to use the orientation tensor, and reach the F8/F16-with-loops results on the A-LOAM front end, so that GenZ-LIO and iG-LIO are not needed.

Everything below the literature section is an **offline replay**: the real `fusion_node_v2` callbacks are driven by logged F8 runs and their keyframe scans (`fusion_v4/ot_study/node_harness.py`, SAH processed synchronously). The A-LOAM poses are the logged ones (open loop), so only the fusion changes. A replay of a run's own setting reproduces the live result exactly (F8: MF 0.626, LC 4.515, C02 2.168 m against live 0.627, 4.53, 2.12). Other settings are approximations because live runs feed the fused pose back into A-LOAM. All three sequences are development data (MF: C_T calibration; LC and C02: SAH development). The selection rules were written down before each stage was run (`fusion_v4/ot_study/PREREG.md`, first entry 10:20 UTC). Nothing here is a live result.

## Summary
| Config | MF front end (6 logs) | LC (3) | C02 (3) |
|---|---|---|---|
| F8 (T only) | 0.626 | 4.515 | 2.168 |
| F16 (T + SAH) | 0.560 | 1.946 | 1.782 |
| F17 (R + T + SAH) | 0.560 | 1.946 | 1.782 |
| **F20 (R + T + OT: OT fail-safe on the geometric tensor + SAH)** | **0.558** | **1.974** | **1.776** |
| Switch-SLAM, published | 1.61 | 2.42 | none |

With loops: see section 6.
- **R channel:** its rotation check never closed on any of the 12 healthy logs, so F17 equals F16 to the last digit. It costs nothing, but these logs cannot show its value. Its value is only for VIO rotation failures, which these bags do not contain.
- **OT channel in the translation weight:** every rule that uses the plain planar-normal tensor and lowers the LiDAR information made the corridors worse, by 0.27 to 0.75 m. The tensor leaves out edges, so it understates the constraint A-LOAM really has.
- **Geometric tensor:** counting linear features as well (an edge with direction d contributes (I - d dᵀ)/2) removes that loss. The fail-safe cap is then neutral on healthy data: MF -0.002, LC +0.028, C02 -0.006 m.
- **Injected solver fault:** F20 beat F16 on 12 of 12 logs (sign test p = 0.0005). The fault is a confident but wrong LiDAR slide, with the keyframe scans untouched. The gain is small: 2 to 5 % (MF -0.08, LC -0.10, C02 -0.25 m).
- **OT channel for heading:** the heading part is SAH, the alignment of the orientation distribution of the same normals (section 4). It gives the large gains: LC 4.52 to 1.95 m, C02 2.17 to 1.78 m in replay, and 4.53 to 2.27 m live on LC.

## 1. The structure (fixed)
- **R, the Schur rotation block S_RR** (radians, D_RAD), judged on its own. In healthy operation the rotation comes from the VIO (c_R = 0) and R is monitored. When the VIO rotation disagrees with the LiDAR rotation beyond the frozen references, the LiDAR rotation carries the step with W_R = (S_RR + 10⁻³ I)⁻¹ S_RR (ROT_CHECK, design B). The references are 0.402 rad over 2 s and 0.585 rad over 10 s, the largest values on 19 Multi Floor recordings.
- **T, the Schur translation block S_tt**, with the rotation coupling removed. Weight W_t = (c S + I)⁻¹ c S, with c = 0.03 frozen on Multi Floor.
- **OT, the orientation-tensor channel, the "additional T"**, computed per LiDAR keyframe from the raw points only. It uses no correspondences and no solver state.
  - T = (1/n) Σ n nᵀ over the planar normals. T is the sufficient statistic of the Bingham distribution of the normals, so every Bingham parameter is a function of T's eigen-decomposition.
  - The geometric tensor G = (Σ_planar n nᵀ + Σ_linear (I - d dᵀ)/2) / (n_planar + n_linear) also counts edges.
  - Both come from the same k = 12 PCA that SAH already runs (`structure_heading.scan_tensors`). They are rotated into the current LiDAR frame between keyframes.
- Separating R and T by Schur complements is DCReg's, and also Selective KF's and MM-LINS'. Separate rotation and translation weights because of the unit difference are also in D²-LIO. **Neither is claimed.**

## 2. Literature: who already uses an orientation tensor of normals
- **LF-GICP** (arXiv 2608.19522, Aug 2026 preprint, read through a review synopsis).
  - It builds M = Σ ρ_v n_v n_vᵀ from planarity-weighted map normals and uses λ_min/tr and λ_min/|V|, with thresholds and hysteresis.
  - These gate a Fisher-information reweighting of GICP correspondences.
  - It argues that the GN Hessian masks degeneracy.
  - It is LiDAR-only, with no VIO and no heading use.
  - **So the orientation tensor as a solver-independent degeneracy measure is prior art.**
- **LiLi** (arXiv 2609.17145): independent of the Hessian, but it works by re-optimising from perturbed starts, not from normals.
- **D²-LIO** (arXiv 2508.14355): separate W_r and W_t because of the rotation/translation scale difference.
- **Other normal-based work:** Hatleskog & Alexis (arXiv 2410.10784) on normal-noise-aware point-to-plane degeneracy; Straub et al. (arXiv 1709.05774) on Bingham/vMF mixtures of surfel normals; X-ICP and LP-ICP on localizability from per-point normal contributions.
- **Information-aware odometry** (arXiv 2607.13516): a sampled Hessian, no normals.
- **Heading from walls:** Manhattan LiDAR SLAM (Remote Sens. 15(1):15) and visual Manhattan systems. Histogram-of-normals alignment is used for loop closure (Lin & Zhang, arXiv 1909.11811).
- **Orientation tensors of order 2 and 4:** standard in fibre-orientation statistics (Advani & Tucker, J. Rheology 31, 1987).
- **What was not found:**
  - the orientation tensor as a direction-by-direction, threshold-free cap on the Schur translation information inside a VIO-primary weight;
  - the edge-aware geometric tensor used for that;
  - one orientation-distribution channel that gives both the translation check and the heading anchor.

  These are the candidate contributions. This is a negative search over the papers read, not a proof that nobody has done it.

## 3. Every way to use the orientation tensor, and the results
Each Schur eigen-direction v_i has two numbers:
- the solver's information λ_i;
- the raw-geometry support τ_i = N v_iᵀ T v_i, with N = tr(H_tt). Using the same total mass means there is no free scale. If the Hessian were N·T exactly, τ_i ≥ λ_i would hold and a cap could never bind.

| # | Use | Rule | Free constants | Result (replay, F16 + rule, mean m: MF / LC / C02) |
|---|---|---|---|---|
| A1 | fail-safe cap | min(λ, τ) | none | 0.563 / 2.487 / 2.381 |
| A2 | harmonic mean | 2λτ/(λ+τ) | none | 0.569 / 2.322 / 2.252 |
| A3 | geometric mean | √(λτ) | none | 0.570 / 2.213 / 2.097 |
| A4 | tensor alone | τ | none | 0.583 / 2.486 / 2.394 |
| A5 | solver unless they disagree by more than 2× | λ or τ | factor 2 (a priori) | 0.567 / 2.480 / 2.387 |
| A6 | hybrid Schur | N T - H_tR H_RR⁻¹ H_Rt | none | 0.572 / 2.544 / 2.536 |
| A7 | optimistic | max(λ, τ) | none | 0.580 / 1.947 / 1.795 |
| A1-G | **fail-safe cap on the geometric tensor G (chosen)** | min(λ, τ_G) | none | **0.558 / 1.974 / 1.776** |
| A7-G | optimistic on G | max(λ, τ_G) | none | 0.584 / 1.914 / 1.784 |
| B | hard gate on λ_min(T)/tr (LF-GICP style) | threshold | 1-2 | not run: needs thresholds; A1-A4 are its soft forms |
| C | inside A-LOAM's solver (reweight or remap along the tensor's weak axis) | C++ change | weights | not run: cannot be replayed from logs |
| D | heading from the orientation distribution (SAH) | section 4 | frozen SAH design | F8 → F16: 0.626 → 0.560 / 4.515 → 1.946 / 2.168 → 1.782 |
| E | loop factors shaped by the tensor of the matched normals, Λ_t = 3T/msd (same trace as the standard isotropic factor) | none | — | section 6 |

Baseline F16: 0.560 / 1.946 / 1.782.

**Stage 1 (planar tensor):**
- Only A7 met the pre-written no-harm rule: within 0.05 m of F16 on LC and C02.
- Every rule that lowers LiDAR information lost 0.27-0.75 m on the corridors.
- Reading: the planar-only tensor understates the translational support of A-LOAM's own solution. A-LOAM's Hessian also uses edge features (door frames, pipes, corners), and those are exactly what constrains a corridor axis.

**Stage 2 (geometric tensor, written before it was run):**
- With edges counted, the principled fail-safe A1 became admissible and was chosen by the pre-written rule.
- On healthy data it binds in 90-99 % of fused scans, but mildly: the median ratio λ'/λ is 0.81 (MF), 0.89 (LC), 0.85 (C02), and fewer than 0.2 % of scans fall below 0.5.
- Because W = cλ/(cλ+1) with c·N ≫ 1, the weight changes only where the raw geometry has almost no support (c·N·vᵀGv ≲ 1). That is the intended behaviour of a threshold-free fail-safe.

**Stage 3 (written before it was run): when does it add value?** A solver fault was injected into the real logs, the "solver confident but wrong" case of the thesis:
- three 20 s windows per log, at 25 / 50 / 75 % of the log;
- in each window the LiDAR position slides along the weakest Schur direction at 0.2 m/s, i.e. 4 m per window, and the slide stays in the pose afterwards;
- H_tt is replaced by tr(H_tt)/3·I, the wrong correspondences that look like constraint;
- the keyframe scans and the VIO are untouched.

| | F16 | F20 | F20 better |
|---|---|---|---|
| MF (6) | 3.807 | 3.723 | 6 / 6 (-2.2 %) |
| LC (3) | 3.592 | 3.496 | 3 / 3 (-2.7 %) |
| C02 (3) | 4.852 | 4.602 | 3 / 3 (-5.2 %) |

- F20 is better on 12 of 12 logs (sign test p = 0.0005), but the protection is small. Where the real geometry does support the slide direction, as in most of these buildings, the tensor cannot tell that the solver is wrong.
- It protects only where the scene is truly degenerate along the slide. That is why the gain is largest on Corridor02.
- This demonstrates the mechanism under a stated fault model. It says nothing about how often such faults happen in real data.

## 4. Why SAH is the rotational read-out of the same orientation distribution (an identity, not a relabel)
SAH measures the heading error as the shift that best aligns the axial histogram h(θ) with a reference. h(θ) is the histogram of horizontal directions of the keyframe's near-vertical planar normals.
- Axial data are π-periodic: h(θ) = Σ_k c_k e^{i2kθ}.
- The circular cross-correlation SAH maximises is C(ψ) = Σ_k c_k conj(c_k^ref) e^{-i2kψ}.
- The pair c_k is fixed by the horizontal deviatoric part of the orientation tensor of order 2k: k = 1 is T's horizontal block, k = 2 is the fourth-order tensor, and so on.
- So SAH aligns the whole family of even-order orientation tensors of the same normals, with the histogram smoothing acting as a low-pass weight on the orders.
- **Why T alone is not enough for heading:** with two equally strong orthogonal wall families, T's horizontal block is isotropic and c_1 = 0. The fourth order is the first that sees the walls.
- So the OT channel has two read-outs of one object, the orientation distribution of the scan's planar normals: its second moment (eigenvalues, via G) checks the translation, and its alignment gives the heading.
- The SAH design (gates, Kalman update, 0.25° per scan) is unchanged and frozen. It was developed on LC and C02.

## 5. Final configuration F20 (`run_fusion_study.sh`, FRONT=aloam)
`FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1 ROT_CHECK=1 OT_SRC=geom OT_MODE=min`
- No new tuned constant.
- OT_MODE=off reproduces F16 bit for bit (checked on LC run 1 against the previous node).
- The tensor reuses the SAH k-NN, so the extra cost is negligible.

F18 (TCAP, a per-scan planar tensor from `/laser_cloud_surf_last`) was superseded before its first full run. Only its 70 s smoke run exists. The study showed that the planar-only tensor is the wrong source: it lost 0.5-0.6 m on the corridors as a cap.

## 6. With loops (back end, iso and the tensor-shaped loop factor, replay)
(filled in below)

## 7. What can be claimed, and what cannot
- **Supported:**
  - A VIO-primary fusion with three separately judged channels: Schur R, Schur T, and a solver-independent orientation-tensor channel.
  - In that channel, the edge-aware geometric tensor caps the Schur translation information direction by direction, with no threshold and no scale (N = tr(H_tt)). It is neutral on healthy data and protective under a confident-but-wrong solver fault (12/12, small).
  - The same orientation distribution anchors the heading. That is where the large gains come from.
- **Not supported:**
  - that the tensor improves accuracy on healthy data (it does not);
  - that the R channel improves these results (it never acts on them);
  - "first to use an orientation tensor" (LF-GICP);
  - "first to separate R and T" (DCReg);
  - that a planar Bingham/orientation tensor is a good cap for A-LOAM (it is not; edges are needed).

## 8. Limits
- Open-loop replay on development data, 12 logs. The live runs (`run_f20_batch.sh`) are still to be done.
- The fault model is mine and chosen to be the case the fail-safe is meant for.
- The literature on LF-GICP, LiLi and D²-LIO was read through summaries.
- With SAH_SYNC = 0 the live keyframe tensor arrives one processing delay later than in the replay.

Sources: [LF-GICP](https://pith.science/paper/2608.19522), [LiLi](https://pith.science/paper/2609.17145), [D²-LIO](https://arxiv.org/html/2508.14355), [Hatleskog & Alexis](https://arxiv.org/html/2410.10784v2), [information-aware odometry](https://arxiv.org/pdf/2607.13516), [Lin & Zhang loop closure](https://arxiv.org/pdf/1909.11811), [Advani & Tucker orientation tensors (Tucker keynote)](https://ecm-academics.plymouth.ac.uk/jsummerscales/FPCM/FPCM15/FPCM15_keynote_Tucker_fibre_orientation_descriptors.pdf), [Selective KF](https://arxiv.org/html/2412.17235v1), [DCReg](https://arxiv.org/abs/2509.06285).
