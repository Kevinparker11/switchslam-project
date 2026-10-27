# Statistical tests across multiple runs (21 Oct 2026)

Question: are the differences between configurations, and the run-to-run variation, real or noise? Unit of analysis = one run's full-span ATE (m). Script: `analysis/improve/stats_tests.py` (rerun whenever runs are added). All tests two-sided unless stated. Replays of the GenZ stack use the frozen weights G9 (c_T 3e-6, c_R 5e-6), G17 (+ SAH).

## Data
- A-LOAM stack (live runs): Multi Floor F8 x9 (1.0x) and x3 (0.5x), F16 x6; Long Corridor F8 x3, F16 x6; Corridor02 F8 x3, F16 x6.
- GenZ stack, Multi Floor: 4 independent GenZ-LIO runs (3 G0 runs + the live G17 run). Per run: G0 [0.876 0.525 0.307 0.626], G9 [0.587 0.393 0.281 0.337], G17 [0.551 0.359 0.256 0.287], G8 [0.705 9.03 0.565 0.641]. Weights were tuned on the first 3; run 4 (the live G17 run) was not used for tuning.

## A. Between configurations, independent runs (A-LOAM stack): effect of SAH (F8 -> F16)
| Sequence | F8 mean (n) | F16 mean (n) | Difference, 95 % bootstrap CI | Welch p | Mann-Whitney exact p | Hedges g |
|---|---|---|---|---|---|---|
| Long Corridor | 4.53 (3) | 2.27 (6) | +2.26 [+1.66, +2.75] | 0.0033 | 0.024 | 4.4 |
| Corridor02 | 2.12 (3) | 1.71 (6) | +0.41 [+0.34, +0.49] | 0.0005 | 0.024 | 5.4 |
| Multi Floor (matched 0.5x) | 0.603 (3) | 0.640 (6) | -0.04 [-0.17, +0.10] | 0.67 | 0.55 | -0.3 |
| Multi Floor (all F8) | 0.617 (9) | 0.640 (6) | -0.02 [-0.14, +0.08] | 0.70 | 0.69 | -0.2 |

Reading: SAH clearly improves Long Corridor and Corridor02 (intervals far from 0, huge effect sizes) and has no effect on Multi Floor, as designed. The exact rank test with 3 vs 6 runs cannot go below p = 0.024, so after a Holm correction over the four comparisons it is 0.095; the effect is not in doubt, the sample is small. Long Corridor and Corridor02 are SAH development data.

## B. GenZ stack, Multi Floor, paired by run (4 runs)
| Comparison | mean diff (m) | paired t p | Wilcoxon exact p (min possible 0.125) | runs lower | mean ratio, 95 % CI |
|---|---|---|---|---|---|
| G9 vs GenZ-LIO alone (G0) | -0.18 | 0.065 | 0.125 | 4/4 | 0.71 [0.50, 1.00] |
| **G17 vs G0** | -0.22 | **0.049** | 0.125 | 4/4 | **0.64 [0.43, 0.94]** |
| G17 vs G9 (SAH on the GenZ stack) | -0.04 | **0.006** | 0.125 | 4/4 | **0.90 [0.84, 0.96]** |
| Old rule (G8) vs G0 | +2.15 | 0.38 | 0.375 | 1/4 | 2.26 [0.25, 20.9] |

Reading: the fused system is lower than GenZ-LIO alone in every run, by about 36 % (95 % CI 6-57 %); SAH adds a consistent 10 % on top. The old rule is not better or worse in a statistically supported way, because one VINS-Mono failure dominates (huge interval). With 4 paired runs an exact rank test cannot reach p < 0.05 (minimum 0.125); 6 paired runs are needed (minimum 0.031).

## C. Fused (GenZ stack) against the A-LOAM master, independent runs
| Comparison | means | diff, 95 % bootstrap CI | Welch p | MWU exact p | Hedges g |
|---|---|---|---|---|---|
| G17 (4) vs F8 (9) | 0.363 vs 0.617 | -0.25 [-0.37, -0.12] | 0.021 | 0.020 | -2.1 |
| G17 (4) vs F16 (6) | 0.363 vs 0.640 | -0.28 [-0.41, -0.13] | 0.015 | 0.019 | -2.1 |
| **G0 (GenZ alone, 4) vs F16 (6)** | 0.583 vs 0.640 | -0.06 [-0.27, +0.16] | 0.68 | 0.76 | -0.3 |

Reading: G17 is significantly better than the master on Multi Floor (p about 0.02), but the weights were tuned on 3 of the 4 runs and the master was replayed at a different rate, so this is in-sample. GenZ-LIO alone is not distinguishable from the master: the improvement comes from the fusion, not from the front end by itself.

## D. Run-to-run variation (chi-square tests on the variance)
- Chi-square test of one variance (H0: sigma = 0.115, the sd of F16's 6 runs): GenZ-LIO alone sd 0.236, chi2 = 12.6, p = 0.006 (one-sided, more variable); 95 % CI for sigma [0.13, 0.88]. G17 sd 0.132, chi2 = 3.97, p = 0.27, no evidence of more variability than F16; CI [0.075, 0.49]. (Treats F16's sd as known; it is itself estimated from 6 runs.)
- Brown-Forsythe equal-variance test, G0 / G17 / F16: p = 0.45. F-test G0/G17 variance ratio 3.2: p = 0.37. Underpowered with 4 runs.
- Do the runs differ inside? Per-30-s-window error, 14 windows per run: Kruskal-Wallis across the 4 runs G0 p = 0.11, G17 p = 0.07; chi-square homogeneity of windows above / below the median G0 p = 0.52, G17 p = 0.41. No significant difference between runs at window level (low power); run-level ATE still ranges 0.31-0.88 (G0) and 0.26-0.55 (G17).
- Within each run, G17 vs G0 on the same windows (Wilcoxon signed-rank): lower in 11/14, 9/14, 12/14, 14/14 windows, p = 0.0017, 0.12, 0.035, 0.0001. Pooled: G17 lower in 46 of 56 windows (82 %), mean change -0.17 m, run-resampled bootstrap 95 % CI [-0.28, -0.07]. Windows are autocorrelated, so the pooled window p-values are descriptive; the bootstrap over runs is the valid interval.

## What is and is not supported
Supported: SAH helps on Long Corridor and Corridor02 and does nothing on Multi Floor; on the GenZ stack the fused system beats GenZ-LIO alone in 4/4 runs (about 36 %, CI 6-57 %), and SAH adds about 10 %; the fused GenZ system beats the A-LOAM master on Multi Floor (p about 0.02, in-sample); fusion reduces the run-to-run spread of GenZ-LIO alone (chi-square p = 0.006 against the master's spread).

Not supported: any claim on Long Corridor, Corridor02, Cave02 with the GenZ stack (the first held-out runs, 22 Oct, were worse than the master: see GenZ_fusion_v4_HeldOut_Results.md); a rank-test p < 0.05 for the paired GenZ comparisons (needs >= 6 runs); independence from the tuning (weights chosen on 3 of 4 runs).

Next: 6+ G17 runs on Multi Floor (REPEAT=6 RECORD_KF=1), the held-out sequences at the master's replay rates, then rerun this script.
