# Multi Floor threshold study: live results (run 1 of each, 2026-10-13)

SubT-MRS Hawkins Multi Floor, 3 bags at 1.0x, one run per configuration, 3,870-3,933 log rows each. TPR/FPR on held-out bags 1-2 against A-LOAM drift terciles (8 s windows); J = TPR - FPR. ATE = rigid SE(3) Umeyama, no scale. Reference (old rule, 3 runs): ATE 1.39 +/- 0.14 m, J -0.01. VINS alone: 1.32 m.

| Run | Rule | ATE RMSE (m) | Flagged | TC share | TPR | FPR | J | Pred. J |
|---|---|---|---|---|---|---|---|---|
| A1 | semicircle | 3.05 | 0.891 | 0.788 | 0.907 | 0.884 | 0.023 | 0.02 |
| A2 | kappa(S)>10 | 12.49 | 0.551 | 0.408 | 0.742 | 0.495 | 0.247 | 0.25 |
| A3 | kappa(S)>50 | 15.98 | 0.029 | 0.007 | 0.061 | 0.019 | 0.042 | 0.05 |
| A4 | diag kappa>10 | 13.70 | 0.559 | 0.406 | 0.734 | 0.479 | 0.255 | 0.25 |
| A5 | lmin(S)<100 | 10.88 | 0.741 | 0.670 | 0.969 | 0.803 | 0.166 | 0.17 |
| A6 | never | 17.67 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.00 |
| A7 | kappa(H)>10 | 1.38 | 0.979 | 0.942 | 0.970 | 0.992 | -0.022 | -0.01 |
| A8 | kappa(S_RR)>15.7 | 16.27 | 0.334 | 0.234 | 0.584 | 0.105 | 0.479 | 0.49 |
| B1 | lmin(T)<0.15 | 7.50 | 0.838 | 0.778 | 0.973 | 0.858 | 0.115 | 0.12 |
| B2 | kappa(T)>10 | 14.66 | 0.575 | 0.402 | 0.717 | 0.562 | 0.155 | 0.15 |
| B3 | lmin(T)<=0.045 | 16.12 | 0.245 | 0.081 | 0.293 | 0.307 | -0.014 | -0.01 |
| B4 | Woodcock K<1 | 3.26 | 0.823 | 0.719 | 0.803 | 0.885 | -0.082 | 0.06 |
| B5 | Demantke class | 11.97 | 0.725 | 0.683 | 0.894 | 0.630 | 0.264 | 0.17 |
| C1 | A2 or B3 | 10.80 | 0.658 | 0.481 | 0.751 | 0.599 | 0.152 | 0.16 |
| C2 | A2 or B2 | 8.39 | 0.739 | 0.592 | 0.847 | 0.735 | 0.112 | 0.10 |

## Findings
- Detection ranking by J: A8 0.479 > B5 0.264 ~ A4 0.255 ~ A2 0.247 > A5 0.166 ~ B2 0.155 ~ C1 0.152 > B1 0.115 ~ C2 0.112 > A3 0.042 > A1 0.023 > A6 0 > B3 -0.014 > A7 -0.022 > B4 -0.082. Tie band 0.05; roughly 19 held-out windows per J, so differences under ~0.2 are indicative only.
- Offline predictions held: fire rates within 0.9 points, TC share within 1.2 points, J within 0.05 for 13/15. Misses: B4 (pred +0.06, got -0.082), B5 (pred +0.17, got +0.264). Label shift is unlikely to explain them (13 of 15 runs have exactly 635 high-drift held-out frames); cause not yet known. C1/C2 lost 55-63 log rows and have different labelled counts (C1 555/714, C2 635/879); cause not yet checked.
- Derived detection metrics (held-out): A8 precision 0.817, balanced accuracy 0.740; random-firing precision baseline 0.44. Spearman with ATE: LIDAR_ONLY share +0.99, handed-over share -0.99. Head-to-head: only A8 vs A2 (+0.232) and A2 vs A5 (+0.081) are clear detection gains; adding T to Schur lost 0.095 (C1) and 0.135 (C2). Full tables: "Full comparison" tab of the Multi Floor threshold study doc.
- ATE follows handover share (Spearman TC vs ATE -0.95), not detection quality (J vs ATE +0.34, p 0.22). Unflagged frames use raw A-LOAM odometry (17.67 m with no handover, A6). No rule beats always-VINS (1.32 m) on this bag.
- Usable signal is in the rotation Schur block (translation Schur fires on ~0.2% of frames in A2/A4/A8).
- Channel T failed the pre-set test: C1 0.152 and C2 0.112 vs A2 0.247 (needed gain >= 0.05). Adding T raised FPR by 0.10 / 0.24 for TPR +0.01 / +0.11. B5 alone ties A2; no Schur + Demantke pairing was run.
- Offline incremental test (leave-one-block-out, 17 log-derived features added to Schur kappa): none adds meaningful AUC (best +0.016); T adds 0.000. Single lead: VINS/LiDAR speed ratio vs window drift, rho +0.39, p 0.009 (11 tests; does not survive Bonferroni).

## Next
REPEAT=3 for A8, A2, B5, C1 (8 new runs, ~80 min); test A8's 15.7 on a second sequence; add A-LOAM residual/inlier logging and test a LiDAR-vs-VINS motion-consistency channel; re-score with map-based perturbation labels.
