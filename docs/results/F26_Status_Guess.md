# F26 and F27: two changes to the scan-to-map guess of F24 (6 Nov 2026) - built, not yet run live

**Question.** F24 puts the VINS-Mono motion into A-LOAM's scan-to-map guess on every scan while VINS is healthy; Switch-SLAM uses the VIO motion only when the scan Hessian is degenerate. Does the paper's guess rule help A-LOAM on the bags where A-LOAM is the limit (Cave02, GEODE)?

**Change (`GUESS_MODE=status`, `guess_status.py`, config `F26`).** Only the guess changes; the final fused pose is F24's. Guess = last fused pose composed with: A-LOAM's own scan-to-scan increment when the Hessian is not degenerate; the Eq. 13 interpolation when the status queue (size 5) holds both flags; the VINS increment when all are degenerate. Degeneracy = the three smallest eigenvalues of the normalised Hessian below [0.12, 0.27, 0.48]. VINS counts as absent under F24's own guard (after VO_FAIL, step above 1 m, rotation above 0.5 rad). Default `GUESS_MODE=vins` is F24 exactly. Tests: `test_guess_status.py` and all earlier tests pass.

**What the logged F24 runs say before any run:** the paper's rule calls the Hessian degenerate on Cave02 **0.0 %** of scans, GEODE 10.3 %, Multi Floor 1.5 %, Long Corridor 4.5 %. So F26 is almost "F24 with A-LOAM's own guess" on all four, and exactly that on Cave02. This is also why the paper-style SW replica behaves like plain A-LOAM (rule fires on 1.4 to 4.5 % of scans, SW doc section 14).

**Status.** Development variant (Cave02 and GEODE are tuned-on data). One run per sequence planned (`batches/f26_test.sh`, about 1.6 h). Nothing claimed until the runs exist. Not expected to reach 1 to 2 m: it only changes A-LOAM's starting point, not its features.

## Finding in the F24 code that motivates both: "no motion" guess when VINS is unusable
`FusionCore.predict()` returns the last fused pose with NO motion whenever the VINS motion is not usable (VINS absent, still starting, after a VO_FAIL, or a step the guard rejects). A-LOAM then starts scan-to-map from where the robot was one scan ago instead of from its own scan-to-scan increment. In the F24 logs that is the warm-up and VO_FAIL share of the scans: Cave02 13.5 % (first 130 s, where 14 to 36 % of the squared error arises), GEODE 78 %, Multi Floor and Long Corridor a few percent. A Switch-SLAM-style rule never does this (non-degenerate or VINS failed: LiDAR increment).

## The two tests (`batches/both_tests.sh`, one run each, about 2.1 h)
- **Case 1, F26 (follows the paper):** the guess by Switch-SLAM's status rule. GEODE, Cave02, Multi Floor, Long Corridor.
- **Case 2, F27 (our original F24, one change):** the VINS motion stays in the guess while usable; otherwise A-LOAM's increment instead of "no motion". GEODE and Cave02. F27 equals F24 on every scan where VINS is usable.
- Reading rule fixed before the runs: F26 and F27 are compared with the F24 runs of the same bag; on GEODE the F24 spread is 6.15 to 9.15 (three runs), so a difference inside that range is not a result. Multi Floor / Long Corridor under F26 must not be worse than F24 beyond its spread.

## Live results (6 Nov 2026, one run each, laptop, 0.5x; `for_claude_both*.zip`)
ATE RMSE / max in m, Umeyama SE(3), no scale, full span, no loop closure.

| Bag | F24 (earlier runs) | F26 (paper guess rule) | F27 (F24 + A-LOAM increment when VINS unusable) |
|---|---|---|---|
| Cave02 | 7.55 / 12.63 (n=1) | **6.23 / 10.56** | **6.62 / 11.21** |
| GEODE | 6.15 / 14.00, 9.15 / 25.44, 9.09 / 19.42 | 6.36 / 14.07 | 6.97 / 16.40 |
| Multi Floor | 0.45 / 0.92 | 0.54 / 1.01 | not run |
| Long Corridor | 2.12 / 5.31, 2.15 / 5.57, 1.75 / 3.53 | 2.10 / 3.73 | not run |

**Guess kinds actually used (F26 / F27 logs):** F26 LiDAR guess on Cave02 100 %, GEODE 93.7 % (interp 3.4 %, VINS 2.9 %), Multi Floor 98.5 %, Long Corridor 95.5 %. F27 VINS guess on Cave02 86.7 %, GEODE 55.1 %; A-LOAM increment instead of "no motion" 13.3 % and 44.9 %.

**Cave02 per 120 s block, fused RMSE (m):**

| Run | 0-120 | 120-240 | 240-360 | 360-480 | 480-600 | 600-720 | 720-840 | 840-960 |
|---|---|---|---|---|---|---|---|---|
| F24 | 12.0 | 12.1 | 5.8 | 5.1 | 5.0 | 4.9 | 5.3 | 5.1 |
| F26 | 9.7 | 10.1 | 5.0 | 4.2 | 4.2 | 4.1 | 4.3 | 4.3 |
| F27 | 10.3 | 10.7 | 5.2 | 4.4 | 4.3 | 4.2 | 4.7 | 4.9 |

**Reading (rule fixed before the runs).**
- **GEODE:** 6.36 and 6.97 sit inside the F24 spread (6.15 to 9.15). Not a result, not a gain.
- **Multi Floor:** 0.54 against 0.45, one run each. Slightly worse; one run cannot say if it is outside the spread. Long Corridor 2.10 is inside the F24 spread (1.75 to 2.15): no harm.
- **Cave02:** F26 and F27 are 0.9 to 1.3 m below the single F24 run, and every 120 s block is lower (early 2.0 to 2.3 m, later 0.6 to 0.9 m). That is one run each against one run, so it is a hint, not a result. Note the order: F26 (which here is plain A-LOAM guess, rule never fires) beats F27. Both stay above the old F8 / F16 runs (4.0 to 5.1) and far from 1 to 2 m.
- **The no-motion guess is not the main fault.** It explains at most about 1 m on Cave02 and nothing visible on GEODE. The remaining Cave02 error (the first 240 s at 10 m, later 4 to 5 m) is A-LOAM itself.
- **Not claimed:** no tuned result, no reduction to 1 to 2 m. Cave02 and GEODE remain development data.

**Next (not run):** F16 and F23 on Cave02 with today's code (about 72 min) to see whether F24 regressed or the draw differs from 19 Oct; a second F26 Cave02 run to see if 6.2 repeats.

## Corridor02, F26, one run (planned 6 Nov 2026, written before the run)
`ONLY=C02 CFGS=F26 REPEAT=1` at the replay rate of the F24 run on this bag (0.33x, about 45 min); the rate is not raised, because scan loss would make it not comparable with the F24 reference. Reference: F24 1.47 / 2.51 (n=1), F16 1.71 +- 0.07, F20 live 1.75. Corridor02 is development data. Reading rule fixed now: F26 above 1.75 (the highest value seen on this bag) = worse than the earlier versions; 1.2 to 1.75 = no visible difference at n = 1; below 1.2 = a hint of a gain, not a result. Guess-kind share (LiDAR / interpolated / VINS) is reported from the log, as for the other bags.

## Corridor02, F26, one run: result (6 Nov 2026, 12:45 to 13:35 IST, laptop, 0.33x, `for_claude_f26_c02.zip`)
**F26 1.93 / 3.46** (8412 poses, GT path 695.2 m) against **F24 1.47 / 2.51** (same bag, same rate, n=1). Reading by the rule fixed above: above 1.75 = worse than the earlier versions. **Correction of the rule's premise:** it called 1.75 the highest value seen on this bag; the results_index of the Corridor02 folder shows higher ones: F8 2.07, 2.10, 2.19, 2.11 (n=4), F12 1.65 to 2.17, F14 1.67 to 1.78, F16 1.64 to 1.84 (n=6), F20 1.73 to 1.79 (n=3), F24 1.47; unfed A-LOAM (F5) 46.5 to 93.0 (n=4), VINS-Mono alone (F0) 4.02 to 4.03 (n=3). So 1.93 is above every F16, F20 and F24 run and below the F8 runs: the verdict "worse than F24 and F16/F20, in the F8 range" stands, with the corrected facts, at n = 1.
**Guess kinds used (F26 log):** LiDAR 8232 rows (98.0 %), interpolation 120 (1.4 %), VINS motion 64 (0.8 %). The paper's rule almost never fires on the corridor (the scan Hessian is not flagged degenerate), so F26 is F24 with A-LOAM's own guess on nearly every scan; the WARMUP / FUSED structure is identical (WARMUP 951 rows to 96 s; F24 and F26 mean LiDAR weights 0.78 / 0.84 / 0.90 and vio_gamma 0.98 in both). The only difference is the guess: F24 puts the healthy VINS motion into A-LOAM's scan-to-map start on every scan, F26 does not.
**Where they differ:** the fused paths of the two runs diverge by 0.84 m rms (max 1.71 m) after alignment, most in the first 120 s (1.37 m rms) and the last 240 s (0.9 to 1.1 m); A-LOAM output path 767.6 m (F26) against 757.4 m (F24), GT 695.2 m; fused 742.3 against 737.8 m.
**What this says.** On Corridor02, where VINS-Mono is healthy (89 % FUSED, no VO_FAIL), keeping the VINS motion in the guess (F24) is better by 0.46 m than the paper's rule (F26), and the same pattern as the replica's corridor results (the paper's rule fires on 1.4 to 4.5 % of scans there too). On Farm the rule fired on 32 % of the scans (end of the L) and F26 was not worse (0.29 against F24's 0.47 on the same rig). Not claimed: one run each; the F24 spread on this bag (1.47 to 1.84 over F16/F20/F24) is 0.4 m, so 0.46 m is at the edge of it.
