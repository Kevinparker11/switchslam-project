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
