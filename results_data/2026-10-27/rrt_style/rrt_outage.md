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