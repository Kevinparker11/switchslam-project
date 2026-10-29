# OT channel, round 2: separate third weight, other feasible rules, generality (2026-10-29)

Thesis: Kavinkumar S, CB.EN.P2MFA25004. A-LOAM front end (Option 1). Pre-registration: `fusion_v4/ot_study/round2/PREREG2.md` (written before any candidate was run; three amendments, each written before the scores it affects were read).
Structure kept as agreed: Schur R and Schur T are processed separately, the additional T channel (orientation tensor, OT) is never discarded and takes part in the decision.

## 1. Question
Round 1 (F20) used the OT as a fail-safe cap on the Schur translation information. The request was: test the OT as a separate third weight, find every other feasible way to combine it, aim for the best outcome, and make sure it holds on conditions other than the bags we test on.

## 2. What was tested (open-loop replays through the real fusion_node_v2 callbacks, SAH_SYNC=1)
* **Translation rules** (A = Schur translation information, B = same-mass geometry information from the OT): fail-safe (gmin, smin, min with G3 / GS / ring-filtered tensor, psum, wprod) and rules that can also raise LiDAR information (gmax, agm, ci, wmean).
* **Tensors:** planar T, geometric G, G3 (scattered points as isotropic support), GS (Schur block of the scan's own geometric Hessian), GRF (G without ring "lines").
* **VIO-trust variants:** V0 none, V1 G20 checks, V1b V1 trusted at segment start, V2 V1b judged only along directions the LiDAR supports.
* **Conditions:** Multi Floor (6 logs), Long Corridor (3), Corridor02 (3), each clean + LiDAR-solver fault (FL) + VIO-scale fault (FV) + sparse keyframes (FS); GEODE F16 (3 logs); held-out farm bag (2 logs, scored once). 13 scored cells. Score = mean ln(ATE / ATE_F20) over the cells (negative = better than F20), admissible only if clean MF, LC, C02 each within +0.05 m of F20.
* **Synthetic scenes** (8 types x 3 seeds, VLP-16 ray-cast): corridor, tunnel, room, poles, vegetation, single wall, stairwell, open ground; independent of the bags.

## 3. Results

### Stage A (translation rule, V0)
Scores: gmax -0.029, agm -0.016, wmean -0.016, psum -0.015, ci -0.014, smin -0.014, minS -0.008, min3 -0.004, gmin -0.001, F20 0, F16 -0.007.
Not admissible: wprod +0.122 (LC +0.31 m, C02 +0.35 m clean), minRF +0.014 (LC +0.12 m), sminRF +0.005 (LC +0.13 m, C02 +0.065 m).
No fail-safe cap beats F20 meaningfully on these bags. The rules that raise LiDAR information gain only in cells where the VINS is the weak sensor (FV, GEODE, C02).
Ring-filtered tensors are right on synthetic ground (the ring "lines" are an artefact) but cost LC +0.12 m on real scans, because A-LOAM's own solver uses those ring lines.

### Stage B (VIO-trust variants, scores vs F20 V0)
| arm | score |
|---|---|
| gmax + V2 | -0.179 |
| **gmax + V1b (F21, pre-registered choice)** | **-0.178** |
| agm + V2 / V1 / V1b | -0.175 / -0.170 / -0.173 |
| smin + V1b / V2 (reported, not eligible) | -0.172 |
| F20 + V1b (reported) | -0.166 |
| F20 + V1b, C_T = 0.056 (diagnostic, reported only) | -0.191 |
| gmax V0 | -0.029 |

Every arm with a VIO-trust check lands between -0.164 and -0.179, inside the 0.01 tie band of the best, except the diagnostic. The tie rule picks gmax + V1b.

### Per-cell means (m), replays
| cell | F20 | F16 | F20+V1b | F21 | F20+V1b, C_T 0.056 |
|---|---|---|---|---|---|
| MF clean | 0.56 | 0.56 | 0.56 | 0.58 | 0.58 |
| MF FL | 3.72 | 3.81 | 3.81 | 3.89 | 4.08 |
| MF FV | 2.35 | 2.11 | 0.73 | 0.71 | 0.66 |
| MF FS | 0.64 | 0.62 | 0.64 | 0.65 | 0.63 |
| LC clean | 2.01 | 1.98 | 2.01 | 1.97 | 1.88 |
| LC FL | 3.62 | 3.72 | 4.19 | 4.24 | 4.29 |
| LC FV | 4.89 | 4.81 | 2.71 | 2.61 | 2.48 |
| LC FS | 4.56 | 4.53 | 4.56 | 4.54 | 4.41 |
| C02 clean | 1.71 | 1.71 | 1.71 | 1.57 | 1.57 |
| C02 FL | 4.56 | 4.81 | 4.80 | 4.88 | 4.96 |
| C02 FV | 4.02 | 4.03 | 3.79 | 3.58 | 3.64 |
| C02 FS | 2.20 | 2.22 | 2.20 | 2.12 | 2.09 |
| GEODE clean | 18.3 | 17.8 | 10.59 | 10.60 | 10.58 |

A-LOAM alone on GEODE is 10.3 m. The large effect is the VIO-trust check: GEODE 18 m to 10.6 m and MF-FV 2.35 to 0.71 m. The translation rule is a second-order effect. Paired sign tests over the clean and fault cells find no significant difference between F21, F20 and F16 (p 0.58 to 1).

### With loop closure (iso, 1 round, odometry 1.46 deg / 0.054 m), clean
| | MF | LC | C02 |
|---|---|---|---|
| F20 | 0.469 | 1.455 | 1.481 |
| F20 + V1b | 0.470 | 1.457 | 1.481 |
| **F21** | **0.457** | **1.331** | **1.349** |
| Switch-SLAM published | 1.61 | 2.42 | - |

F20 + V1b equals F20, so the loop-closure gain of F21 comes from the gmax translation weight, not from the VIO check. All three are inside the published Switch-SLAM numbers.

### Held-out farm bag (scored once; replay, not live)
A-LOAM alone 0.106 m; F16 / F20 about 0.99 m; F20 + V1b 0.330 m; **F21 0.280 m**; F20 + V1b with C_T = 0.056: 0.186 m. Fusion is still worse than A-LOAM alone on this bag. Farm fault cells were not run.

### Synthetic scenes (seed 0; seeds 1-2 in `synth_seed*.txt`)
Weight on the weakest direction, honest solver / solver with a confident false slide:
* corridor: honest 0.179 for none/min/smin/gmin, gmax 0.375. Fault: none 0.790, min 0.377, smin 0.208, gmin 0.375, **gmax 0.790** (no protection).
* tunnel: honest 0.180, gmax 0.339. Fault: none 0.783, smin 0.391, **gmax 0.783**.
* single wall: honest 0.215, gmax 0.599; fault: none 0.786, smin 0.484, gmax 0.786.
* room, poles, stairwell, open ground: the solver under-claims what the geometry supports (honest 0.22 / 0.36 / 0.18 / 0.22); gmax raises it to 0.80 / 0.75 / 0.70 / 0.71. Under the fault every rule is close to 0.70 to 0.80 because the geometry really supports the direction.
* The planar T alone mis-states the geometry in several scenes (single wall: T/solver ratio 0.02 vs 0.36 for G; open ground: 0.00 vs 0.59). The geometric tensor G fixes this, which is why F20 and F21 use `OT_SRC=geom`.

## 4. Conclusion
1. **The OT as a separate third weight works only in some forms.** A product-type separate weight (wprod) lowers the LiDAR translation weight too far (LC +0.31 m, C02 +0.35 m clean) and is not admissible. The basis-free matrix rules (gmin, gmax, agm, ci) are admissible.
2. **No translation rule is clearly best on the bags.** Differences between rules are inside the noise (sign tests p 0.58 to 1). gmax scores best (-0.178 in stage B), wins the loop-closure comparison on all three sequences and on the held-out farm bag, and is neutral or slightly positive elsewhere.
3. **gmax is not a fail-safe.** Against a confident wrong solver (synthetic corridor fault) it gives the full false weight 0.79, i.e. no protection, and in honest corridors it roughly doubles the weak-direction weight. The protection against a wrong LiDAR solver now has to come from the VIO-trust check, and that check costs some LiDAR-fault performance (LC-FL +0.4 to +0.6 m, MF-FL +0.1 to +0.2 m versus F20).
4. **The effect that matters is the VIO-trust check.** It is the large, repeatable gain (GEODE, MF-FV, LC-FV, farm).
5. **The gmax gain is not separable from a constant on the bags.** F20 + V1b with C_T = 0.056 (value chosen to match gmax's weak-direction weight on MF after seeing gmax's weights, so it cannot be selected) scores -0.191 vs -0.178 and gets 0.186 m on the farm bag vs 0.280 m, but it is worse on both LiDAR-fault cells (MF-FL 4.08 vs 3.89 m, C02-FL 4.96 vs 4.88 m). What gmax adds over a constant is that its weight follows the scan geometry per keyframe (synthetic scenes), which the bags cannot separate within noise.
6. **Selected configuration: F21 = F20 + gmax + V1b**, the pre-registered stage-B choice (admissible, -0.178 vs F20, best with loop closure). It is a replay result; the live run decides.

## 5. Limits
* Round-2 numbers are open-loop replays; GEODE replays differ from live by -0.06 / +0.11 m because the live SAH worker is asynchronous.
* The VIO references (0.157, 0.277, 4.325) were calibrated on the 6 Multi Floor replays and frozen; C_T is frozen at 0.03.
* Farm bag: one environment, two logs; fusion is still worse than A-LOAM alone (0.28 vs 0.106 m). The R channel's value is still undemonstrated on these bags.
* The multi-floor loop gap for SAH configs (0.47 vs F8 with loops 0.347) is still unexplained.
* Nothing has been run live yet for F21.

## 6. Live test (pre-registered before any live F21 number exists)
Run `fusion_v4/run_f21_batch.sh` (same bags, 3 runs per sequence, loop back end, zip `~/Downloads/for_claude_F21.zip`), compare with the live F20 batch.
* L1: live F21 clean mean ATE on MF, LC and C02 each within +0.05 m of live F20 (admissibility).
* L2: with loops, F21 <= F20 on at least 2 of the 3 sequences (replay: 3 of 3).
Reported whatever comes out; no setting changes after seeing the live numbers.

## 7. Related work used
SA-LIVO (arXiv 2606.25699: per-direction gating of the joint information matrix, no check of which sensor is wrong), equivariant degeneracy criterion (arXiv 2608.15532), LF-GICP (2608.19522), D2-LIO, DCReg, Selective KF, DAMS-LIO, SuperLoc, covariance intersection (Noack et al.). DCReg already separates rotation and translation; the part not covered by them is the orientation tensor used as a basis-free per-direction bound together with its heading read-out (SAH).

## 8. Files
Code: `fusion_v4/fusion_core.py` (`ot_matrix_rule`, `t_weight`, `VioConsistency` proj), `fusion_node_v2.py` (OT_SRC, VIO_CHECK_START, VIO_CHECK_PROJ), `structure_heading.py` (`scan_tensors_ext`), tests `test_ot_round2.py`, `test_t_cap.py`. Study scripts and pre-registration: `fusion_v4/ot_study/round2/`. Config: `[F21]` in `run_fusion_study.sh`; live script `run_f21_batch.sh`.
