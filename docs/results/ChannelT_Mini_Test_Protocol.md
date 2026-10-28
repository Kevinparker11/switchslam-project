# Additional T (orientation-tensor channel): a very short synthetic test (protocol written 28 Oct 2026, before any run)

## What is tested, and what is not
Question: does the orientation-tensor channel T (computed from the raw scan normals, before any scan matching) detect translation degeneracy better than, or in addition to, the Hessian Schur channel S_tt, and under which conditions?
This is a synthetic mechanism test in numpy, about a minute of compute. It is NOT evidence on real data and does not replace the pre-registered `channelT_test/eval_channelT.py`. It can only show under which assumed conditions T adds value, or that it does not. Nothing below is changed after seeing a score.

## Correction to my statement of 28 Oct
I said T would help on repeated (aliased) structure. That is not supported: a periodic structure has real normals along the axis, so both T and the Hessian report it as constrained; aliasing is a multi-minimum cost problem that neither sees. It is dropped from this test.

## Setup
- Scene: corridor along x (3 m wide, 2.5 m high), scanner at the centre, VLP-16 model (16 rings, -15..+15 deg, 1800 azimuth steps, max range 25 m), range noise sigma_r = 0.02 m along the beam (and 0.04 m as a second level). Axial constraint comes only from K rectangular door-frame faces (0.2 m x 2.1 m, facing the x axis) placed against the side walls at random x between 3 and 22 m on either side; K in {0, 1, 2, 3, 4, 6, 8, 12}, 5 random scenes per K, 2 noise seeds per scene = 80 scans per noise level.
- Normals for all arms: PCA on the 20 nearest neighbours of the noisy points (the production-like estimate). T = mean of n n^T over all points, ascending eigenvalues, smallest = l1.
- Arm H (Hessian Schur channel): point-to-plane Hessian over the same points and normals, J = [(p x n)^T, n^T], blocks H_RR, H_Rt, H_tt in (rad, m); S_tt = H_tt - H_tR H_RR^-1 H_Rt; score = smallest eigenvalue of S_tt / N.
- Arm T: score = l1 of T. (Same unit as arm H.)
- Arm H+T (the proposed fail-safe rule): score = min(score_H, score_T).
- Conditions: C0 clean (the Hessian uses the scan's own normals); C1 and C2: a fraction rho = 0.10 and 0.30 of the correspondences are wrong (their normal replaced by a random direction, weight 1 - the robust weights do not reject them); T is computed from the scan and is unaffected. This is the "solver unreliable" case of the thesis. It is a modelling assumption chosen to be favourable to T; it is stated, not hidden.
- Truth label: degenerate along x if the noise-free axial component T_true[xx] (mean of n_x^2 over the true hit normals) < 0.004. Sensitivity: 0.002 and 0.008.
- Metrics: AUC with "degenerate" as positive; recall at 5 % false-alarm rate with the threshold set on the calibration half of the scenes (even indices) and applied to the held-out half (odd indices); 95 % bootstrap CI over scenes.

## Pre-declared predictions and verdicts
- C0 prediction: arm T is not better than arm H (T ignores the rotation-translation coupling that S_tt removes); H+T is not better than H by 0.03 AUC. So in the clean case T adds nothing.
- C1/C2 prediction: arm H degrades with rho; H+T recovers to about arm T.
- "T adds value" verdict (all must hold): AUC(H+T) - AUC(H) >= 0.03 with the lower CI bound > 0 in both C1 and C2; AUC(H+T) - AUC(H) >= -0.01 in C0; holds for the main label (0.004) and at least one sensitivity label.
- If the main label fails, the result is "no demonstrated value under these conditions". A pass means only: under the stated corruption model, the fail-safe rule helps; real data must confirm.

## Result (28 Oct 2026; full run as specified, 160 scans = 80 per noise level; seed fixed in the script)
Before the full run, the same script was run once with `--quick` (3 scenes per K instead of 5) as a smoke test and its output was seen; the specification and the criteria were not changed afterwards. The full output is below.

```
scans: 160

=== sigma_r 0.02 m: truth T_xx range 0.0000 - 0.0240; scans with K=0: 10
-- label degenerate if T_true_xx < 0.004 : 40 degenerate / 40 constrained scans
   rho 0.0  AUC H 0.993  T 0.993  H+T 0.993 | H+T - H = +0.000 [0.000, 0.000] | recall@5%FPR (held-out) H 0.94 T 0.94 H+T 0.94
   rho 0.1  AUC H 0.959  T 0.993  H+T 0.993 | H+T - H = +0.034 [0.002, 0.075] | recall@5%FPR (held-out) H 0.75 T 0.94 H+T 0.94
   rho 0.3  AUC H 0.954  T 0.993  H+T 0.993 | H+T - H = +0.039 [0.010, 0.080] | recall@5%FPR (held-out) H 0.75 T 0.94 H+T 0.94
-- label degenerate if T_true_xx < 0.002 : 20 degenerate / 60 constrained scans
   rho 0.0  AUC H 0.994  T 0.996  H+T 0.994 | H+T - H = +0.000 [0.000, 0.000] | recall@5%FPR (held-out) H 1.00 T 1.00 H+T 1.00
   rho 0.1  AUC H 0.932  T 0.996  H+T 0.996 | H+T - H = +0.064 [0.018, 0.125] | recall@5%FPR (held-out) H 0.75 T 1.00 H+T 1.00
   rho 0.3  AUC H 0.788  T 0.996  H+T 0.996 | H+T - H = +0.208 [0.109, 0.308] | recall@5%FPR (held-out) H 0.25 T 1.00 H+T 1.00
-- label degenerate if T_true_xx < 0.008 : 52 degenerate / 28 constrained scans
   rho 0.0  AUC H 0.992  T 0.992  H+T 0.992 | H+T - H = +0.000 [0.000, 0.000] | recall@5%FPR (held-out) H 0.91 T 0.91 H+T 0.91
   rho 0.1  AUC H 0.992  T 0.992  H+T 0.992 | H+T - H = +0.000 [-0.014, 0.017] | recall@5%FPR (held-out) H 0.95 T 0.91 H+T 0.91
   rho 0.3  AUC H 0.967  T 0.992  H+T 0.992 | H+T - H = +0.025 [-0.003, 0.074] | recall@5%FPR (held-out) H 0.77 T 0.91 H+T 0.91

=== sigma_r 0.04 m: truth T_xx range 0.0000 - 0.0260; scans with K=0: 10
-- label degenerate if T_true_xx < 0.004 : 36 degenerate / 44 constrained scans
   rho 0.0  AUC H 0.938  T 0.934  H+T 0.938 | H+T - H = +0.000 [0.000, 0.000] | recall@5%FPR (held-out) H 0.67 T 0.67 H+T 0.67
   rho 0.1  AUC H 0.908  T 0.934  H+T 0.934 | H+T - H = +0.027 [-0.003, 0.064] | recall@5%FPR (held-out) H 0.61 T 0.67 H+T 0.67
   rho 0.3  AUC H 0.860  T 0.934  H+T 0.934 | H+T - H = +0.074 [0.023, 0.144] | recall@5%FPR (held-out) H 0.50 T 0.67 H+T 0.67
-- label degenerate if T_true_xx < 0.002 : 28 degenerate / 52 constrained scans
   rho 0.0  AUC H 0.895  T 0.894  H+T 0.895 | H+T - H = +0.000 [0.000, 0.000] | recall@5%FPR (held-out) H 0.38 T 0.38 H+T 0.38
   rho 0.1  AUC H 0.891  T 0.894  H+T 0.894 | H+T - H = +0.003 [-0.038, 0.046] | recall@5%FPR (held-out) H 0.56 T 0.38 H+T 0.38
   rho 0.3  AUC H 0.861  T 0.894  H+T 0.894 | H+T - H = +0.033 [-0.020, 0.089] | recall@5%FPR (held-out) H 0.56 T 0.38 H+T 0.38
-- label degenerate if T_true_xx < 0.008 : 52 degenerate / 28 constrained scans
   rho 0.0  AUC H 0.976  T 0.976  H+T 0.976 | H+T - H = +0.000 [0.000, 0.000] | recall@5%FPR (held-out) H 0.95 T 0.95 H+T 0.95
   rho 0.1  AUC H 0.972  T 0.976  H+T 0.976 | H+T - H = +0.004 [-0.006, 0.017] | recall@5%FPR (held-out) H 0.80 T 0.95 H+T 0.95
   rho 0.3  AUC H 0.946  T 0.976  H+T 0.976 | H+T - H = +0.030 [-0.006, 0.087] | recall@5%FPR (held-out) H 0.80 T 0.95 H+T 0.95

real	0m48.960s
user	0m46.315s
sys	0m1.605s
```

### Against the pre-declared verdict
- **C0 (clean), prediction held:** T is not better than H (AUC equal to three decimals at sigma_r 0.02, 0.993 against 0.993; 0.934 against 0.938 at 0.04) and H+T equals H. In the clean case T adds nothing. The rotation-translation coupling that S_tt removes made no difference in this geometry.
- **C1/C2 prediction held:** H degrades with the fraction of wrong correspondences (main label, sigma_r 0.02: AUC 0.993 -> 0.959 -> 0.954), T does not move, and H+T follows T.
- **Verdict "T adds value" (AUC(H+T) - AUC(H) >= 0.03 with a CI above 0 in both C1 and C2, no loss in C0, main label plus one sensitivity label):** met at sigma_r = 0.02 (main label: +0.034 [0.002, 0.075] in C1, +0.039 [0.010, 0.080] in C2; label 0.002: +0.064 and +0.208). **Not met at sigma_r = 0.04** (main label: C1 +0.027 with a CI including 0, C2 +0.074 [0.023, 0.144]). The criteria were written for both noise levels without saying how to combine them; read strictly, the verdict is mixed: pass at one noise level, fail at the other.
- Recall at 5 % false-alarm rate (held-out half): 0.75 (H) against 0.94 (T and H+T) at sigma_r 0.02 in C1 and C2; at the 0.002 label with rho 0.3 it is 0.25 against 1.00.

### What this does and does not show
- It shows a conditional benefit: if the Hessian is fed wrong correspondences that the robust weights do not reject, T (from the raw scan) is unaffected, and taking the smaller of the two scores protects against the false "constrained". It also shows T adds nothing when the Hessian is clean.
- The benefit is built into the assumption. The corruption model was chosen to be favourable to T; a Hessian whose robust weights reject most wrong matches would remove it. Not tested here.
- Not shown: any benefit on real data, in A-LOAM's actual Hessian (it also has edge terms), under repeated structure (dropped), or in the final trajectory error. The label threshold and the geometry (a corridor with door frames) were set by me. Synthetic, one scene type, 5 scenes per level.
- Next step to turn this into evidence: log T next to the Hessian verdict on real runs and on a Gazebo world with geometry labels, and check whether the Hessian is ever confident when the geometry is degenerate (`channelT_test/eval_channelT.py`, pre-registered).
