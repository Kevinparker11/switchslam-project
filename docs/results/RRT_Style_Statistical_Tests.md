# Statistical evaluation in the style of the Hybrid-RRT* paper (27 Oct 2026)

Source of the method: S. Ganesan, B. Ramalingam, R. E. Mohan, "A hybrid sampling-based RRT* path planning algorithm for autonomous mobile robot navigation", Expert Systems with Applications 258 (2024) 125206, Section 4 and Tables 1-3.

## What the paper does
- Every configuration is run 100 times per environment (narrow, cluttered, maze), because the sampler is random.
- **Table 1:** per algorithm and environment, minimum, median, maximum and mean of each metric (path length, time, nodes visited), and the improvement of the proposed method = (baseline mean - proposed mean) / baseline mean, with an up or down arrow. (Checked: RRT* narrow path 680.85 against 668.64 gives the printed 1.79 %.)
- **Table 2:** convergence rate and success rate (share of the 100 runs in which a path is found).
- **Table 3:** hypothesis test for every baseline x environment x metric: H0: M(ALGM1) = M(ALGM2), H1: M(ALGM1) > M(ALGM2), ALGM1 = baseline, ALGM2 = proposed, 95 % confidence, p-value and "Reject Yes/No". The paper does not name the test or say whether M is the mean or the median. p-values down to 3.2e-182 with 100 runs per group can only come from a parametric test such as a t-test (a rank test cannot go below about 1e-34 with 100 against 100); this is an inference, not stated in the paper.

## How it maps onto our project
| Paper | Ours |
|---|---|
| 100 random runs per environment | the repeated recordings of each sequence (4-14), each replayed with every method; the replicates differ through the run-to-run behaviour of VINS-Mono and GenZ-LIO, like the paper's runs differ through the random sampler |
| environments narrow / cluttered / maze | Multi Floor, Long Corridor, Cave02, Corridor02, GEODE stairs (PC), Gazebo office; plus an outage block (gap test) |
| baselines RRT*, Informed RRT*, RRT*-N | GenZ-LIO alone (LiDAR-inertial), VINS-Mono alone (visual-inertial), G17 (our earlier fusion, without the consistency gate, scale correction and guard) |
| proposed Hybrid-RRT* | G20 (outages: G23) |
| path length | full-span ATE RMSE (m), Umeyama SE(3); and the per-run maximum error |
| success rate | share of runs with full-span ATE <= 10 m (no gross divergence; the bound already used in the gap test) |
| time, nodes, convergence rate | not applicable (replay is exact but not timed; no search tree) |
| test, 95 % | one-sided paired test per baseline x environment, alpha 0.05: **Wilcoxon signed-rank (exact) as the decision** (n is 4-14 and the errors are heavy-tailed, for example one GenZ-LIO run of 5092 m), and the paired t-test alongside as the parametric version that the paper most likely used. Also the reverse direction (is G20 worse?) and Holm over the family. |

Pairing: every method is evaluated on the same recording (GenZ-LIO and VINS-Mono take no feedback from the fusion, so the replay equals the live run; shown on 10 live recordings in `GenZ_fusion_v4_G20_Universal_Fix.md`). With n recordings the exact one-sided Wilcoxon p cannot go below 1/2^n: 0.0625 for n = 4, so Cave02 and Gazebo can never reach 0.05 however consistent the result is.

## Table A - accuracy per environment (full-span ATE RMSE, m; n = recordings)
| Environment | Method | n | Min | Median | Max | Mean | Improvement of G20 (mean) | Improvement of G20 (median) |
|---|---|---|---|---|---|---|---|---|
| Multi Floor | GenZ-LIO alone | 14 | 0.307 | 0.479 | 5092.589 | 364.258 | ↑ 99.9% | ↑ 26.6% |
| Multi Floor | VINS-Mono alone | 14 | 1.270 | 1.333 | 1.351 | 1.326 | ↑ 66.2% | ↑ 73.6% |
| Multi Floor | G17 (fusion, no gate) | 14 | 0.253 | 0.299 | 4.908 | 0.681 | ↑ 34.2% | ↓ 17.7% |
| Multi Floor | G20 (proposed) | 14 | 0.257 | 0.352 | 1.461 | 0.448 | - | - |
| Long Corridor | GenZ-LIO alone | 10 | 1.923 | 1.987 | 2.084 | 2.000 | ↑ 15.0% | ↑ 14.1% |
| Long Corridor | VINS-Mono alone | 10 | 4.905 | 4.913 | 4.919 | 4.913 | ↑ 65.4% | ↑ 65.3% |
| Long Corridor | G17 (fusion, no gate) | 10 | 1.377 | 2.112 | 3.011 | 2.141 | ↑ 20.6% | ↑ 19.2% |
| Long Corridor | G20 (proposed) | 10 | 1.544 | 1.707 | 1.807 | 1.700 | - | - |
| Cave02 | GenZ-LIO alone | 4 | 0.283 | 0.283 | 0.319 | 0.292 | ↓ 2.1% | ↓ 4.4% |
| Cave02 | VINS-Mono alone | 4 | 10.822 | 12.150 | 64.948 | 25.017 | ↑ 98.8% | ↑ 97.6% |
| Cave02 | G17 (fusion, no gate) | 4 | 3.655 | 4.008 | 5.735 | 4.351 | ↑ 93.1% | ↑ 92.6% |
| Cave02 | G20 (proposed) | 4 | 0.284 | 0.296 | 0.318 | 0.298 | - | - |
| Corridor02 | GenZ-LIO alone | 1 | 2.696 | 2.696 | 2.696 | 2.696 | ↑ 8.0% | ↑ 8.0% |
| Corridor02 | VINS-Mono alone | 1 | 3.465 | 3.465 | 3.465 | 3.465 | ↑ 28.4% | ↑ 28.4% |
| Corridor02 | G17 (fusion, no gate) | 1 | 1.881 | 1.881 | 1.881 | 1.881 | ↓ 31.9% | ↓ 31.9% |
| Corridor02 | G20 (proposed) | 1 | 2.481 | 2.481 | 2.481 | 2.481 | - | - |
| GEODE stairs (PC) | GenZ-LIO alone | 14 | 0.302 | 0.355 | 0.489 | 0.395 | ↓ 22.4% | ↓ 33.7% |
| GEODE stairs (PC) | VINS-Mono alone | 14 | 133.382 | 268.555 | 306.561 | 239.551 | ↑ 99.8% | ↑ 99.8% |
| GEODE stairs (PC) | G17 (fusion, no gate) | 14 | 2.235 | 17.557 | 25.601 | 16.585 | ↑ 97.1% | ↑ 97.3% |
| GEODE stairs (PC) | G20 (proposed) | 14 | 0.389 | 0.475 | 0.578 | 0.483 | - | - |
| Gazebo office | GenZ-LIO alone | 4 | 0.141 | 0.317 | 1.015 | 0.447 | ↓ 14.7% | ↓ 44.8% |
| Gazebo office | VINS-Mono alone | 4 | 0.761 | 0.781 | 0.785 | 0.777 | ↑ 34.0% | ↑ 41.3% |
| Gazebo office | G17 (fusion, no gate) | 4 | 0.445 | 0.482 | 0.819 | 0.557 | ↑ 7.9% | ↑ 4.8% |
| Gazebo office | G20 (proposed) | 4 | 0.319 | 0.459 | 0.816 | 0.513 | - | - |

## Table B - success rate (run with full-span ATE <= 10 m) and worst-case error (median of the per-run maximum error, m)
| Environment | n | GenZ-LIO alone | VINS-Mono alone | G17 (fusion, no gate) | G20 (proposed) |
|---|---|---|---|---|---|
| Multi Floor | 14 | 93% / 1.05 | 100% / 4.83 | 100% / 0.86 | 100% / 0.80 |
| Long Corridor | 10 | 100% / 4.31 | 100% / 11.65 | 100% / 5.28 | 100% / 3.77 |
| Cave02 | 4 | 100% / 0.81 | 0% / 51.92 | 100% / 10.77 | 100% / 0.81 |
| Corridor02 | 1 | 100% / 4.62 | 100% / 8.56 | 100% / 3.57 | 100% / 4.41 |
| GEODE stairs (PC) | 14 | 100% / 0.91 | 0% / 1036.31 | 21% / 26.58 | 100% / 1.20 |
| Gazebo office | 4 | 100% / 1.08 | 100% / 1.86 | 100% / 0.96 | 100% / 0.84 |

## Table C - hypothesis test, H0: M(baseline) = M(G20), H1: M(baseline) > M(G20) (one-sided, paired by recording, alpha = 0.05)
| Baseline | Environment | n | G20 lower in | p (Wilcoxon, exact) | Reject H0 | p (paired t) | Reject H0 (t) |
|---|---|---|---|---|---|---|---|
| GenZ-LIO alone | Multi Floor | 14 | 13 of 14 | 0.000122 | Yes | 0.168 | No |
| GenZ-LIO alone | Long Corridor | 10 | 10 of 10 | 0.000977 | Yes | 4.7e-06 | Yes |
| GenZ-LIO alone | Cave02 | 4 | 1 of 4 | 0.875 | No | 0.905 | No |
| GenZ-LIO alone | Corridor02 | 1 | 1 of 1 | n too small | - | - | - |
| GenZ-LIO alone | GEODE stairs (PC) | 14 | 3 of 14 | 0.998 | No | 0.999 | No |
| GenZ-LIO alone | Gazebo office | 4 | 1 of 4 | 0.688 | No | 0.594 | No |
| VINS-Mono alone | Multi Floor | 14 | 13 of 14 | 0.000122 | Yes | 3.39e-08 | Yes |
| VINS-Mono alone | Long Corridor | 10 | 10 of 10 | 0.000977 | Yes | 9.41e-16 | Yes |
| VINS-Mono alone | Cave02 | 4 | 4 of 4 | 0.0625 | No | 0.0803 | No |
| VINS-Mono alone | Corridor02 | 1 | 1 of 1 | n too small | - | - | - |
| VINS-Mono alone | GEODE stairs (PC) | 14 | 14 of 14 | 6.1e-05 | Yes | 1.6e-10 | Yes |
| VINS-Mono alone | Gazebo office | 4 | 3 of 4 | 0.125 | No | 0.0426 | Yes |
| G17 (fusion, no gate) | Multi Floor | 14 | 6 of 14 | 0.665 | No | 0.182 | No |
| G17 (fusion, no gate) | Long Corridor | 10 | 5 of 10 | 0.116 | No | 0.038 | Yes |
| G17 (fusion, no gate) | Cave02 | 4 | 4 of 4 | 0.0625 | No | 0.00164 | Yes |
| G17 (fusion, no gate) | Corridor02 | 1 | 0 of 1 | n too small | - | - | - |
| G17 (fusion, no gate) | GEODE stairs (PC) | 14 | 14 of 14 | 6.1e-05 | Yes | 3.15e-07 | Yes |
| G17 (fusion, no gate) | Gazebo office | 4 | 4 of 4 | 0.0625 | No | 0.106 | No |

### Reverse direction (H1: M(G20) > M(baseline)), same data
| Baseline | Environment | n | p (Wilcoxon) | G20 significantly worse |
|---|---|---|---|---|
| GenZ-LIO alone | Multi Floor | 14 | 1 | No |
| GenZ-LIO alone | Long Corridor | 10 | 1 | No |
| GenZ-LIO alone | Cave02 | 4 | 0.188 | No |
| GenZ-LIO alone | GEODE stairs (PC) | 14 | 0.00201 | Yes |
| GenZ-LIO alone | Gazebo office | 4 | 0.438 | No |
| VINS-Mono alone | Multi Floor | 14 | 1 | No |
| VINS-Mono alone | Long Corridor | 10 | 1 | No |
| VINS-Mono alone | Cave02 | 4 | 1 | No |
| VINS-Mono alone | GEODE stairs (PC) | 14 | 1 | No |
| VINS-Mono alone | Gazebo office | 4 | 0.938 | No |
| G17 (fusion, no gate) | Multi Floor | 14 | 0.357 | No |
| G17 (fusion, no gate) | Long Corridor | 10 | 0.903 | No |
| G17 (fusion, no gate) | Cave02 | 4 | 1 | No |
| G17 (fusion, no gate) | GEODE stairs (PC) | 14 | 1 | No |
| G17 (fusion, no gate) | Gazebo office | 4 | 1 | No |

Holm over the 15 forward Wilcoxon tests (family-wise 0.05):
rejected after Holm: G17 (fusion, no gate) / GEODE stairs (PC) (p 6.1e-05); VINS-Mono alone / GEODE stairs (PC) (p 6.1e-05); GenZ-LIO alone / Multi Floor (p 0.000122); VINS-Mono alone / Multi Floor (p 0.000122); GenZ-LIO alone / Long Corridor (p 0.000977); VINS-Mono alone / Long Corridor (p 0.000977)

Recordings per environment: Multi Floor: MF-a1, MF-a2, MF-a3, MF-a4, MF-b1, MF-b2, MF-b3, MF-b4, MF-b5, MF-b6, MF-c1, MF-c2, MF-c3, MF-c4; Long Corridor: LC-a1, LC-a2, LC-a3, LC-b1, LC-b2, LC-b3, LC-c1, LC-c2, LC-c3, LC-c4; Cave02: CV-a1, CV-b1, CV-c1, CV-c2; Corridor02: C02-a1; GEODE stairs (PC): GEO-a1, GEO-a2, GEO-a3, GEO-a4, GEO-b1, GEO-b2, GEO-b3, GEO-b4, GEO-b5, GEO-b6, GEO-c1, GEO-c2, GEO-c3, GEO-c4; Gazebo office: GZ-nd1, GZ-nd2, GZ-nd3, GZ-pl1

## Outage block (gap test, 9 rewritten bags with LiDAR outages, live; proposed = G23)
| Method | n | Min | Median | Max | Mean | Success (ATE <= 10 m) | Improvement of G23 (median) |
|---|---|---|---|---|---|---|---|
| GenZ-LIO alone (G23-run log) | 9 | 7.51 | 26.37 | 16433.95 | 4742.32 | 11% | ↑ 77.9% |
| VINS-Mono alone | 9 | 1.35 | 5.09 | 11.02 | 4.17 | 89% | ↓ 14.1% |
| G20 | 9 | 4.58 | 88.27 | 9118.22 | 1455.24 | 11% | ↑ 93.4% |
| G23 (proposed for outages) | 9 | 2.47 | 5.81 | 3238.70 | 723.47 | 56% | - |

| Baseline | n | G23 lower in | p (Wilcoxon, exact) | Reject H0 | p (paired t) | Reject H0 (t) | p reverse (G23 worse) |
|---|---|---|---|---|---|---|---|
| GenZ-LIO alone | 9 | 9 of 9 | 0.00195 | Yes | 0.0416 | Yes | 1 |
| VINS-Mono alone | 9 | 2 of 9 | 0.986 | No | 0.916 | No | 0.0195 |
| G20 | 9 | 6 of 9 | 0.213 | No | 0.272 | No | 0.82 |

Bags: C02_L30B_r1, LC_L10B_r1, LC_L10B_r2, LC_L30B_r1, LC_L30B_r2, MF_L10B_r1, MF_L10B_r2, MF_L30B_r1, MF_L30B_r2

## Reading
1. **Against VINS-Mono alone** G20 is significantly better on Multi Floor (13 of 14 recordings lower, p 1.2e-4), Long Corridor (10 of 10, p 9.8e-4) and GEODE (14 of 14, p 6.1e-5). On Cave02 it is lower in 4 of 4 (0.30 against 12.2 m median) but n = 4 cannot reach 0.05 (p 0.0625).
2. **Against GenZ-LIO alone** G20 is significantly better on Multi Floor (13 of 14, p 1.2e-4; median 0.352 against 0.479) and Long Corridor (10 of 10, p 9.8e-4; 1.707 against 1.987), tied on Cave02 (0.296 against 0.283) and Gazebo office, and **significantly worse on GEODE** (reverse test p 0.002; median 0.475 against 0.355). The t-test on Multi Floor does not reject (p 0.17) only because of the single 5092 m GenZ-LIO divergence, which is why the rank test is used for the decision.
3. **Against G17** G20 is significantly better only on GEODE (14 of 14, p 6.1e-5, where G17 fails at 17.6 m median). On Multi Floor G17 has the lower median (0.299 against 0.352) but one 4.9 m failure; on Long Corridor the t-test rejects (p 0.038) and the rank test does not (p 0.12). G20 is the stable choice, not the best on every recording.
4. **Holm** (15 forward tests, family-wise 0.05): 6 survive (VINS-Mono alone on Multi Floor, Long Corridor and GEODE; GenZ-LIO alone on Multi Floor and Long Corridor; G17 on GEODE).
5. **Success rate:** G20 100 % on all six environments; GenZ-LIO alone 93 % on Multi Floor (one divergence); VINS-Mono alone 0 % on Cave02 and GEODE; G17 21 % on GEODE.
6. **Outages:** G23 is significantly better than GenZ-LIO alone (9 of 9, p 0.002), not significantly better than G20 (6 of 9, p 0.21), and **significantly worse than VINS-Mono alone** (reverse p 0.02; success 56 % against 89 %), because VINS-Mono is not affected by a LiDAR outage and the fusion still follows a LiDAR that stays wrong after the gap (Gap_Test_Results.md, section 3).

## Limits (to be stated with the tables)
- In-sample: c_T, c_R and the gate thresholds were calibrated on Multi Floor, and G20 was designed after the failures in these logs were seen. The held-out confirmation (Gazebo construction world, any new real bag) is still open. The paper's maps are also the evaluation maps, but its algorithm has no parameters fitted to them.
- Replicates are repeated runs of the same sequences, not new environments: the test is about run-to-run reliability on these sequences, as in the paper.
- Some replicates are not independent in every source (GenZ-LIO alone is bit-identical on several Multi Floor and GEODE recordings), which makes the paired differences for that baseline partly repeated.
- n is 1-14, not 100: p-values cannot be as small as the paper's, and Cave02 (4), Gazebo (4) and Corridor02 (1) cannot reach significance. GEODE is PC data; the others are laptop data; no test crosses machines.
- No time metric (the replay is not timed) and no convergence-rate analogue.

## Files
Scripts `analysis/rrt_style/` (`rrt_tests.py`, `rrt_outage.py`, `vins_one.py` for the VINS-Mono-alone ATE of every recording); tables and the VINS-alone values `results_data/2026-10-27/rrt_style/`. Inputs: the replay JSONs of `analysis/improve/universal/out*` and the gap-test score JSONs.


## Update 27 Oct: see RTS_Table3_Hypothesis_Tests.md
The same test in the exact format of the paper's Table 3 (four parameters, Switch-SLAM added, G20 renamed RTS-Fusion) is in `RTS_Table3_Hypothesis_Tests.md`.
