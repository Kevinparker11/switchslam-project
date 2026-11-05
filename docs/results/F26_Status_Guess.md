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
