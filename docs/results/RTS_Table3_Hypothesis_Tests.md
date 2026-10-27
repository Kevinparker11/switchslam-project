# Table 3 of the Hybrid-RRT* paper, for this project (27 Oct 2026)

Format source: S. Ganesan, B. Ramalingam, R. E. Mohan, ESWA 258 (2024) 125206, Table 3 (hypothesis test of the proposed algorithm against each baseline, per environment and parameter, H0: M(ALGM1) = M(ALGM2), H1: M(ALGM1) > M(ALGM2), 95 %). Companion: `RRT_Style_Statistical_Tests.md` (Tables 1-2 style: min / median / max / mean, improvement, success rate).

## Names used from here on
| Internal name | Name in the thesis tables | What it is |
|---|---|---|
| G20 | **RTS-Fusion** | Channels R and T (Schur weights) + structure channel T+ (SAH), consistency gate (slow and fast check), VIO scale correction, LiDAR blow-up guard; GenZ-LIO + VINS-Mono. "RTS" = rotation, translation, structure, as in the thesis title. |
| G23 | **RTS-Fusion + gap rule** | RTS-Fusion with the LiDAR-gap rule (gap_T = 1 s); the outage configuration. |
| G17 | **RTS-core** | The same channels without the consistency gate, scale correction and guard. |
| F12 (re-run on the GenZ stack) | **Switch-SLAM rule (re-run)** | The detection rule of Switch-SLAM (RA-L 2024) as an all-or-nothing switch of the translation, rotation always from VINS-Mono. |

## Metrics (the paper's four parameters replaced by ours)
ATE RMSE (m), full span, Umeyama SE(3); max error (m); RPE over 10 s (m); rotation drift over 10 s (deg): RMS angle of the relative-rotation error over 10 s windows, with the constant sensor-to-ground-truth frame offset estimated by Kabsch on the relative rotation vectors (needs no extrinsic calibration). Time, nodes visited and convergence rate have no counterpart here.

## Test
Paired by recording (the same recording is scored by every method; GenZ-LIO and VINS-Mono take no feedback from the fusion, so each replay equals a live run, shown on 10 live recordings in `GenZ_fusion_v4_G20_Universal_Fix.md`). Decision: exact one-sided Wilcoxon signed-rank test (errors are heavy-tailed: one GenZ-LIO run of 5092 m); the paired t-test, which the paper most likely used, is given beside it. Reject H0 when p < 0.05. Where the proposed method is significantly worse (reverse test) it is written in the Reject column.

H0: M(ALGM1) = M(ALGM2), H1: M(ALGM1) > M(ALGM2); ALGM1 = baseline, ALGM2 = RTS-Fusion (= G20); 95 % confidence (reject when p < 0.05). Paired by recording; "RTS better in k of n" counts the recordings where the baseline's value is larger. Recordings: Multi Floor 14; Long Corridor 10; Cave02 4; GEODE stairs (PC) 14; Gazebo office 4.

### Real recordings and the Gazebo office

| Algorithm | Environment | Parameter | n | RTS better in | p-value (Wilcoxon) | Reject H0 | p-value (paired t) | Reject H0 (t) |
|---|---|---|---|---|---|---|---|---|
| GenZ-LIO alone | Multi Floor | ATE RMSE (m) | 14 | 13 of 14 | 0.000122 | Yes | 0.168 | No |
|  |  | max error (m) | 14 | 13 of 14 | 0.000305 | Yes | 0.168 | No |
|  |  | RPE 10 s (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 0.168 | No |
|  |  | rotation drift 10 s (deg) | 14 | 6 of 14 | 0.335 | No | 0.168 | No |
| GenZ-LIO alone | Long Corridor | ATE RMSE (m) | 10 | 10 of 10 | 0.000977 | Yes | 4.7e-06 | Yes |
|  |  | max error (m) | 10 | 10 of 10 | 0.000977 | Yes | 2.1e-07 | Yes |
|  |  | RPE 10 s (m) | 10 | 10 of 10 | 0.000977 | Yes | 4.82e-10 | Yes |
|  |  | rotation drift 10 s (deg) | 10 | 10 of 10 | 0.000977 | Yes | 2.37e-07 | Yes |
| GenZ-LIO alone | Cave02 | ATE RMSE (m) | 4 | 1 of 4 | 0.875 | No | 0.905 | No |
|  |  | max error (m) | 4 | 2 of 4 | 0.312 | No | 0.122 | No |
|  |  | RPE 10 s (m) | 4 | 4 of 4 | 0.0625 | No | 0.00158 | Yes |
|  |  | rotation drift 10 s (deg) | 4 | 4 of 4 | 0.0625 | No | 0.0145 | Yes |
| GenZ-LIO alone | GEODE stairs (PC) | ATE RMSE (m) | 14 | 3 of 14 | 0.998 | No (RTS significantly worse, p 0.00201) | 0.999 | No |
|  |  | max error (m) | 14 | 3 of 14 | 0.988 | No (RTS significantly worse, p 0.0148) | 0.984 | No |
|  |  | RPE 10 s (m) | 14 | 3 of 14 | 0.998 | No (RTS significantly worse, p 0.00201) | 1 | No |
|  |  | rotation drift 10 s (deg) | 14 | 4 of 14 | 0.749 | No | 0.772 | No |
| GenZ-LIO alone | Gazebo office | ATE RMSE (m) | 4 | 1 of 4 | 0.688 | No | 0.594 | No |
|  |  | max error (m) | 4 | 1 of 4 | 0.688 | No | 0.438 | No |
|  |  | RPE 10 s (m) | 4 | 1 of 4 | 0.688 | No | 0.227 | No |
|  |  | rotation drift 10 s (deg) | 4 | 3 of 4 | 0.125 | No | 0.113 | No |
| VINS-Mono alone | Multi Floor | ATE RMSE (m) | 14 | 13 of 14 | 0.000122 | Yes | 3.39e-08 | Yes |
|  |  | max error (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 6.72e-10 | Yes |
|  |  | RPE 10 s (m) | 14 | 13 of 14 | 0.00671 | Yes | 3.32e-05 | Yes |
|  |  | rotation drift 10 s (deg) | 14 | 14 of 14 | 6.1e-05 | Yes | 1.8e-11 | Yes |
| VINS-Mono alone | Long Corridor | ATE RMSE (m) | 10 | 10 of 10 | 0.000977 | Yes | 9.41e-16 | Yes |
|  |  | max error (m) | 10 | 10 of 10 | 0.000977 | Yes | 2.51e-10 | Yes |
|  |  | RPE 10 s (m) | 10 | 10 of 10 | 0.000977 | Yes | 2.02e-10 | Yes |
|  |  | rotation drift 10 s (deg) | 10 | 10 of 10 | 0.000977 | Yes | 1.18e-18 | Yes |
| VINS-Mono alone | Cave02 | ATE RMSE (m) | 4 | 4 of 4 | 0.0625 | No | 0.0803 | No |
|  |  | max error (m) | 4 | 4 of 4 | 0.0625 | No | 0.145 | No |
|  |  | RPE 10 s (m) | 4 | 4 of 4 | 0.0625 | No | 0.118 | No |
|  |  | rotation drift 10 s (deg) | 4 | 4 of 4 | 0.0625 | No | 0.0112 | Yes |
| VINS-Mono alone | GEODE stairs (PC) | ATE RMSE (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 1.6e-10 | Yes |
|  |  | max error (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 5.39e-15 | Yes |
|  |  | RPE 10 s (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 8.3e-10 | Yes |
|  |  | rotation drift 10 s (deg) | 14 | 14 of 14 | 6.1e-05 | Yes | 4.08e-12 | Yes |
| VINS-Mono alone | Gazebo office | ATE RMSE (m) | 4 | 3 of 4 | 0.125 | No | 0.0426 | Yes |
|  |  | max error (m) | 4 | 4 of 4 | 0.0625 | No | 0.0263 | Yes |
|  |  | RPE 10 s (m) | 4 | 3 of 4 | 0.125 | No | 0.102 | No |
|  |  | rotation drift 10 s (deg) | 4 | 3 of 4 | 0.438 | No | 0.349 | No |
| Switch-SLAM rule (re-run) | Multi Floor | ATE RMSE (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 0.0256 | Yes |
|  |  | max error (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 0.0156 | Yes |
|  |  | RPE 10 s (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 0.0177 | Yes |
|  |  | rotation drift 10 s (deg) | 14 | 14 of 14 | 6.1e-05 | Yes | 7.12e-08 | Yes |
| Switch-SLAM rule (re-run) | Long Corridor | ATE RMSE (m) | 10 | 10 of 10 | 0.000977 | Yes | 6.64e-16 | Yes |
|  |  | max error (m) | 10 | 10 of 10 | 0.000977 | Yes | 6.9e-11 | Yes |
|  |  | RPE 10 s (m) | 10 | 10 of 10 | 0.000977 | Yes | 7.1e-11 | Yes |
|  |  | rotation drift 10 s (deg) | 10 | 10 of 10 | 0.000977 | Yes | 3.56e-18 | Yes |
| Switch-SLAM rule (re-run) | Cave02 | ATE RMSE (m) | 4 | 4 of 4 | 0.0625 | No | 6.88e-05 | Yes |
|  |  | max error (m) | 4 | 4 of 4 | 0.0625 | No | 0.00746 | Yes |
|  |  | RPE 10 s (m) | 4 | 4 of 4 | 0.0625 | No | 0.0166 | Yes |
|  |  | rotation drift 10 s (deg) | 4 | 4 of 4 | 0.0625 | No | 1.31e-05 | Yes |
| Switch-SLAM rule (re-run) | GEODE stairs (PC) | ATE RMSE (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 8.72e-07 | Yes |
|  |  | max error (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 2.72e-07 | Yes |
|  |  | RPE 10 s (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 6.28e-08 | Yes |
|  |  | rotation drift 10 s (deg) | 14 | 14 of 14 | 6.1e-05 | Yes | 2.04e-09 | Yes |
| Switch-SLAM rule (re-run) | Gazebo office | ATE RMSE (m) | 4 | 3 of 4 | 0.125 | No | 0.155 | No |
|  |  | max error (m) | 4 | 4 of 4 | 0.0625 | No | 0.0307 | Yes |
|  |  | RPE 10 s (m) | 4 | 3 of 4 | 0.312 | No | 0.238 | No |
|  |  | rotation drift 10 s (deg) | 4 | 3 of 4 | 0.438 | No | 0.358 | No |
| Switch-SLAM rule, whole-pose switch (variant) | Multi Floor | ATE RMSE (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 2.68e-09 | Yes |
|  |  | max error (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 1.02e-08 | Yes |
|  |  | RPE 10 s (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 7.97e-07 | Yes |
|  |  | rotation drift 10 s (deg) | 14 | 14 of 14 | 6.1e-05 | Yes | 0.000383 | Yes |
| Switch-SLAM rule, whole-pose switch (variant) | Long Corridor | ATE RMSE (m) | 10 | 10 of 10 | 0.000977 | Yes | 1.76e-06 | Yes |
|  |  | max error (m) | 10 | 10 of 10 | 0.000977 | Yes | 4.32e-06 | Yes |
|  |  | RPE 10 s (m) | 10 | 10 of 10 | 0.000977 | Yes | 2.45e-06 | Yes |
|  |  | rotation drift 10 s (deg) | 10 | 10 of 10 | 0.000977 | Yes | 6.63e-10 | Yes |
| Switch-SLAM rule, whole-pose switch (variant) | Cave02 | ATE RMSE (m) | 4 | 4 of 4 | 0.0625 | No | 0.000724 | Yes |
|  |  | max error (m) | 4 | 4 of 4 | 0.0625 | No | 0.0109 | Yes |
|  |  | RPE 10 s (m) | 4 | 4 of 4 | 0.0625 | No | 0.00391 | Yes |
|  |  | rotation drift 10 s (deg) | 4 | 4 of 4 | 0.0625 | No | 0.000204 | Yes |
| Switch-SLAM rule, whole-pose switch (variant) | GEODE stairs (PC) | ATE RMSE (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 1.16e-06 | Yes |
|  |  | max error (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 2.57e-07 | Yes |
|  |  | RPE 10 s (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 4.73e-08 | Yes |
|  |  | rotation drift 10 s (deg) | 14 | 14 of 14 | 6.1e-05 | Yes | 1.49e-07 | Yes |
| Switch-SLAM rule, whole-pose switch (variant) | Gazebo office | ATE RMSE (m) | 4 | 4 of 4 | 0.0625 | No | 0.019 | Yes |
|  |  | max error (m) | 4 | 4 of 4 | 0.0625 | No | 0.00574 | Yes |
|  |  | RPE 10 s (m) | 4 | 4 of 4 | 0.0625 | No | 0.00421 | Yes |
|  |  | rotation drift 10 s (deg) | 4 | 3 of 4 | 0.125 | No | 0.0376 | Yes |
| RTS-core (G17, no safeguards) | Multi Floor | ATE RMSE (m) | 14 | 6 of 14 | 0.665 | No | 0.182 | No |
|  |  | max error (m) | 14 | 13 of 14 | 0.000305 | Yes | 0.148 | No |
|  |  | RPE 10 s (m) | 14 | 3 of 14 | 0.985 | No (RTS significantly worse, p 0.0176) | 0.177 | No |
|  |  | rotation drift 10 s (deg) | 14 | 13 of 14 | 0.000183 | Yes | 0.167 | No |
| RTS-core (G17, no safeguards) | Long Corridor | ATE RMSE (m) | 10 | 5 of 10 | 0.116 | No | 0.038 | Yes |
|  |  | max error (m) | 10 | 6 of 10 | 0.0801 | No | 0.0104 | Yes |
|  |  | RPE 10 s (m) | 10 | 10 of 10 | 0.000977 | Yes | 7.14e-06 | Yes |
|  |  | rotation drift 10 s (deg) | 10 | 1 of 10 | 0.999 | No (RTS significantly worse, p 0.00195) | 0.967 | No |
| RTS-core (G17, no safeguards) | Cave02 | ATE RMSE (m) | 4 | 4 of 4 | 0.0625 | No | 0.00164 | Yes |
|  |  | max error (m) | 4 | 4 of 4 | 0.0625 | No | 0.00253 | Yes |
|  |  | RPE 10 s (m) | 4 | 4 of 4 | 0.0625 | No | 0.00182 | Yes |
|  |  | rotation drift 10 s (deg) | 4 | 2 of 4 | 0.438 | No | 0.368 | No |
| RTS-core (G17, no safeguards) | GEODE stairs (PC) | ATE RMSE (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 3.15e-07 | Yes |
|  |  | max error (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 5.01e-07 | Yes |
|  |  | RPE 10 s (m) | 14 | 14 of 14 | 6.1e-05 | Yes | 8.89e-08 | Yes |
|  |  | rotation drift 10 s (deg) | 14 | 9 of 14 | 0.476 | No | 0.665 | No |
| RTS-core (G17, no safeguards) | Gazebo office | ATE RMSE (m) | 4 | 4 of 4 | 0.0625 | No | 0.106 | No |
|  |  | max error (m) | 4 | 4 of 4 | 0.0625 | No | 0.0317 | Yes |
|  |  | RPE 10 s (m) | 4 | 3 of 4 | 0.125 | No | 0.0803 | No |
|  |  | rotation drift 10 s (deg) | 4 | 2 of 4 | 0.688 | No | 0.801 | No |

### Switch-SLAM as published (RA-L 2024, Table II; one value per sequence, no per-run data)

Test: one-sample exact Wilcoxon signed-rank of the RTS-Fusion per-recording values against the published value; H1: published > RTS-Fusion. Only the two metrics Switch-SLAM reports. Different setup and single run: indicative only.

| Algorithm | Environment | Parameter | published | n | RTS better in | p-value (Wilcoxon) | Reject H0 |
|---|---|---|---|---|---|---|---|
| Switch-SLAM (published) | Multi Floor | ATE RMSE (m) | 1.61 | 14 | 14 of 14 | 6.1e-05 | Yes |
| Switch-SLAM (published) | Multi Floor | max error (m) | 3.63 | 14 | 13 of 14 | 0.000122 | Yes |
| Switch-SLAM (published) | Long Corridor | ATE RMSE (m) | 2.42 | 10 | 10 of 10 | 0.000977 | Yes |
| Switch-SLAM (published) | Long Corridor | max error (m) | 5.09 | 10 | 10 of 10 | 0.000977 | Yes |

### Outage block: 9 bags with LiDAR outages (live logs); proposed = RTS-Fusion with the gap rule (G23)

| Algorithm | Environment | Parameter | n | RTS better in | p-value (Wilcoxon) | Reject H0 | p-value (paired t) | Reject H0 (t) |
|---|---|---|---|---|---|---|---|---|
| GenZ-LIO alone | LiDAR outages (9 bags) | ATE RMSE (m) | 9 | 9 of 9 | 0.00195 | Yes | 0.0416 | Yes |
|  |  | max error (m) | 9 | 9 of 9 | 0.00195 | Yes | 0.0474 | Yes |
|  |  | RPE 10 s (m) | 9 | 9 of 9 | 0.00195 | Yes | 0.0401 | Yes |
|  |  | rotation drift 10 s (deg) | 9 | 9 of 9 | 0.00195 | Yes | 0.033 | Yes |
| VINS-Mono alone | LiDAR outages (9 bags) | ATE RMSE (m) | 9 | 2 of 9 | 0.986 | No (RTS significantly worse, p 0.0195) | 0.916 | No |
|  |  | max error (m) | 9 | 2 of 9 | 0.918 | No | 0.916 | No |
|  |  | RPE 10 s (m) | 9 | 2 of 9 | 0.973 | No (RTS significantly worse, p 0.0371) | 0.916 | No |
|  |  | rotation drift 10 s (deg) | 9 | 9 of 9 | 0.00195 | Yes | 0.00735 | Yes |
| RTS-Fusion without gap rule (G20) | LiDAR outages (9 bags) | ATE RMSE (m) | 9 | 6 of 9 | 0.213 | No | 0.272 | No |
|  |  | max error (m) | 9 | 6 of 9 | 0.248 | No | 0.417 | No |
|  |  | RPE 10 s (m) | 9 | 6 of 9 | 0.248 | No | 0.491 | No |
|  |  | rotation drift 10 s (deg) | 9 | 8 of 9 | 0.00586 | Yes | 0.021 | Yes |

Holm correction over all 112 Wilcoxon tests above (family-wise 0.05): 31 rejected.

Notes: (1) n = 4 cannot give an exact one-sided Wilcoxon p below 0.0625, so Cave02 and Gazebo cannot reach "Yes"; Corridor02 has one recording and is not tested. (2) "Switch-SLAM rule (re-run)" is our re-implementation of its detection rule (the three smallest normalised eigenvalues of the 6x6 Hessian against 0.12 / 0.27 / 0.48) as an all-or-nothing switch of the translation between GenZ-LIO and VINS-Mono, rotation always from VINS-Mono (the project's F12, defined on 13 Oct, before this test), replayed on the same recordings; the "whole-pose" variant switches the rotation too and is much worse (it mixes LiDAR rotation with VIO translation increments). Neither is the authors' code or pipeline; the rows against the published Switch-SLAM numbers are the fair comparison to the paper. (3) Outage block: GenZ-LIO alone and VINS-Mono alone come from the same live logs as the G23 run, G20 from its own live log; GenZ-LIO differs between the G20 and G23 runs of a bag (see Gap_Test_Results.md). Switch-SLAM is not run on the outage bags (its rule has no behaviour for missing LiDAR data).

## Reading
1. **Against the published Switch-SLAM numbers** RTS-Fusion is significantly better on Multi Floor (ATE 14 of 14 recordings below 1.61 m, p 6.1e-5; max error 13 of 14 below 3.63 m, p 1.2e-4) and Long Corridor (10 of 10 below 2.42 m and below 5.09 m, p 9.8e-4). Single published values, a different setup, and our VINS-Mono alone is far better than theirs (1.33 against 6.30 m), so this is indicative.
2. **Against the Switch-SLAM rule re-run on our recordings** (same recordings, same front end) RTS-Fusion is significantly better on Multi Floor, Long Corridor and GEODE on all four parameters (p 6.1e-5 to 9.8e-4); Cave02 and Gazebo cannot reach significance with n = 4 (all 4 of 4 lower on Cave02, p 0.0625). Median ATE of the re-run rule: Multi Floor 0.90 (RTS-Fusion 0.35), Long Corridor 5.50 (1.71), Cave02 10.9 (0.30), GEODE 20.2 (0.48), Gazebo 0.54 (0.46). The whole-pose variant is worse still.
3. **Against GenZ-LIO alone**: significantly better on Multi Floor (ATE, max error, RPE) and Long Corridor (all four); not on rotation drift on Multi Floor (6 of 14, the rotation comes mostly from GenZ-LIO), not distinguishable on Cave02 and Gazebo, and **significantly worse on GEODE** (ATE, max error, RPE; p 0.002 to 0.015, medians 0.475 against 0.355 m). The Multi Floor t-test p of 0.168 is the same for all four parameters because one GenZ-LIO divergence (5092 m) dominates every mean; the rank test is not affected.
4. **Against VINS-Mono alone**: significantly better on Multi Floor, Long Corridor and GEODE on all four parameters; Cave02 and Gazebo are limited by n = 4.
5. **Against RTS-core**: the safeguards matter on GEODE (all positional parameters) and for the worst case on Multi Floor (max error 13 of 14); the rotation-drift rows are consistent but tiny (medians 2.96 against 2.96 deg on Multi Floor, 1.30 against 1.30 on Long Corridor, so statistically significant and practically nil); they do not help ATE on Multi Floor (RTS-core's median is lower, 0.30 against 0.35; one RTS-core run fails at 4.9 m) and RTS-core is significantly better than RTS-Fusion on rotation drift on Long Corridor (9 of 10 recordings, p 0.002) and on RPE 10 s on Multi Floor (p 0.018).
6. **Outages** (RTS-Fusion + gap rule): significantly better than GenZ-LIO alone on all four parameters (9 of 9, p 0.002); not significantly different from RTS-Fusion without the gap rule on position (6 of 9), significantly better on rotation drift; **significantly worse than VINS-Mono alone on ATE and RPE (reverse p 0.02 and 0.04)**, better on rotation drift (9 of 9).
7. **Holm** over all 112 Wilcoxon tests of this document (family-wise 0.05): 31 rejected.

## Limits
- In-sample: c_T, c_R and the gate thresholds were calibrated on Multi Floor, and G20 was designed after the failures in these logs were seen; the held-out confirmation (Gazebo construction world, any new real bag) is still open.
- The replicates are repeated recordings of the same sequences, not new environments; GenZ-LIO alone is bit-identical on several Multi Floor and GEODE recordings, so those paired differences are partly repeated.
- n = 1 to 14, not 100: Cave02 and Gazebo (n = 4) cannot reach p < 0.0625 and Corridor02 (n = 1) is not tested. GEODE is PC data, the other sequences laptop data; no comparison crosses machines.
- The re-run Switch-SLAM rule is our re-implementation, not the authors' pipeline; its absolute numbers differ from the published ones (published Multi Floor 1.61 against our re-run median 0.90 with a better VINS-Mono; published Long Corridor 2.42 against 5.50).
- The rotation-drift metric needs the relative-rotation frame offset estimated per method and recording; it is a drift measure, not an absolute orientation error.

## Files
Scripts `analysis/rrt_style/` (`rrt_metrics.py`, `rrt_outage_metrics.py`, `table3.py`); per-recording metrics and the table `results_data/2026-10-27/rrt_style/`; configurations `SW` and `SWR` in `analysis/improve/universal/configs.py`; the opt-in `switch_rot` option in `fusion_v4/fusion_core.py` (default off; G20 replays unchanged: Multi Floor run 1 0.25747 before and after).
