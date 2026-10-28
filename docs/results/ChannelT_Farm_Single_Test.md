# Additional T: one live test in the farm (protocol written 28 Oct 2026, before the run)
Question: in the farm world, where unfed A-LOAM fails on the L route with four 360-degree turns (F5 run 1: scan-to-map ATE 6.57 m, scan-to-scan moved 10.2 m during turn 3 and 42.7 m during turn 4), does the orientation tensor T flag the failing windows, and does the Hessian Schur channel S_tt?
Conditions chosen for that reason: standalone A-LOAM (`aloam_standalone.launch`, nothing feeding it, so the Hessian belongs to the real solver state), the same spin driver and route as F5 run 1, a passive logger writing the 6x6 scan-to-scan Hessian and T of the same scan (`channelT_test/degen_logger.py`), plus the A-LOAM odometry and ground truth loggers. One run.
Analysis (`channelT_test/farm_T_vs_H.py`, fixed now): 2 s windows, 1 s stride, scored from the reset. A window FAILS if the path length of the A-LOAM scan-to-scan odometry differs from the ground-truth path length by more than 0.3 m (phantom or lost motion; independent of frame conventions). An arm FLAGS a window if its median score (S_tt: smallest eigenvalue of the Schur translation block; T: smallest eigenvalue l1) is below the 10 % quantile of the whole run.
Verdicts: INCONCLUSIVE if fewer than 5 failure windows or fewer than 3 episodes (A-LOAM did not fail again, or failed once). "T adds value in this run" if T flags at least 50 % of failure windows, S_tt flags under 25 %, and T flags at most 15 % of the other windows. "S_tt already flags" if S_tt flags at least 50 %. Otherwise "neither flags": the failures are not translation-degeneracy failures (for example caused by the 1.2 rad/s turns), and T is not testable by this run.
Limits stated in advance: one run, one world, simulation; the failure may be caused by fast rotation, not by weak translation constraint, in which case a translation detector cannot be expected to flag it; no geometry labels, so this is an outcome-based label; nothing here tests the fusion.

## Result (run 1, 28 Oct 2026; analysis script and rules unchanged from the protocol above)
The header lines of the script output (scans, windows, episodes, failure-window starts) were not in the text sent back, so only the table and verdict are recorded here.

| arm | flags failure windows | flags other windows | AUC (failure = low score) |
|---|---|---|---|
| S_tt (Hessian Schur channel) | 47.9 % (34/71) | 0.0 % | 0.884 |
| T (orientation tensor, l1) | 9.9 % (7/71) | 7.8 % | 0.766 |

Pre-registered verdict (script): **neither channel flags the failures.** S_tt is 2.1 points under the 50 % bar for "S_tt already flags", so the rule is not met; it is recorded as a miss, not rounded up. T does not meet "T adds value" (it flags 9.9 % of failures, about the 10 % flag rate by construction, with 7.8 % of the other windows flagged).
Ground truth / A-LOAM in the same run: GT reset at t=99.82 s, path after reset 91.9 m. A-LOAM scan-to-map ATE 6.515 m (max 47.49 m, end-point error 8.108 m); scan-to-scan ATE 15.649 m (end-point error 86.89 m). The failure of F5 run 1 (scan-to-map ATE 6.57 m) was reproduced.
Reading: T did not detect the failing windows better than S_tt in this run; S_tt separates them partly (AUC 0.884, no false flags) and T separates them less (AUC 0.766). The 71 failure windows overlap (2 s windows, 1 s stride), so they are not 71 independent observations. One run, one world, simulation. The failures coincide with 1.2 rad/s turns, so they are not clearly translation-degeneracy failures. No threshold was changed after seeing the result.
