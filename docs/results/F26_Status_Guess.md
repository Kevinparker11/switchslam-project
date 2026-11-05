# F26: F24 with Switch-SLAM's degeneracy rule choosing the scan-to-map guess (6 Nov 2026) - built, not yet run live

**Question.** F24 puts the VINS-Mono motion into A-LOAM's scan-to-map guess on every scan while VINS is healthy; Switch-SLAM uses the VIO motion only when the scan Hessian is degenerate. Does the paper's guess rule help A-LOAM on the bags where A-LOAM is the limit (Cave02, GEODE)?

**Change (`GUESS_MODE=status`, `guess_status.py`, config `F26`).** Only the guess changes; the final fused pose is F24's. Guess = last fused pose composed with: A-LOAM's own scan-to-scan increment when the Hessian is not degenerate; the Eq. 13 interpolation when the status queue (size 5) holds both flags; the VINS increment when all are degenerate. Degeneracy = the three smallest eigenvalues of the normalised Hessian below [0.12, 0.27, 0.48]. VINS counts as absent under F24's own guard (after VO_FAIL, step above 1 m, rotation above 0.5 rad). Default `GUESS_MODE=vins` is F24 exactly. Tests: `test_guess_status.py` and all earlier tests pass.

**What the logged F24 runs say before any run:** the paper's rule calls the Hessian degenerate on Cave02 **0.0 %** of scans, GEODE 10.3 %, Multi Floor 1.5 %, Long Corridor 4.5 %. So F26 is almost "F24 with A-LOAM's own guess" on all four, and exactly that on Cave02. This is also why the paper-style SW replica behaves like plain A-LOAM (rule fires on 1.4 to 4.5 % of scans, SW doc section 14).

**Status.** Development variant (Cave02 and GEODE are tuned-on data). One run per sequence planned (`batches/f26_test.sh`, about 1.6 h). Nothing claimed until the runs exist. Not expected to reach 1 to 2 m: it only changes A-LOAM's starting point, not its features.
