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