# Switch-SLAM as published: our implementation, what it is, what it is not (4 Nov 2026)

Files: `fusion_v4/switch_slam_core.py` (Algorithm 1 and Eqs. 11-16), `fusion_v4/switch_slam_node.py` (ROS node, drop-in for
`fusion_node_v2.py`), `fusion_v4/test_switch_slam.py` and `test_switch_slam_node.py` (12 tests), configs `SW`, `SWM`, `SW1` in
`run_fusion_study.sh`, batch `fusion_v4/batches/switchslam_exact_batch.sh`. Section 8 adds the generation-1 node (`V7`).

**Status.** Written from the paper (Lee et al., RA-L 9(8), 2024, doi:10.1109/LRA.2024.3421792); the authors released no code. Verified
so far by unit tests on synthetic data and by a ROS-free plumbing test of the node. **No live run has been made.** Whether it
reproduces the published numbers is the reproduction check in section 5, to be run on the laptop.

## 1. Why F12 was not this

F12 (`WEIGHT_MODE=switch_ss`) used only the detection rule, inside our VINS-primary fusion. Checking its logged Corridor02 run: the rule
fired on 2.5 % of FUSED rows, so LiDAR translation was used in 97.5 % of them. F12 therefore behaved as "LiDAR translation, VINS
rotation" (F14 with a rare fall-back), which is why it scored close to F14 (1.87 against 1.74). The "47 %" in the Corridor02 notes is the
share of rows with the kappa(S_RR) gate open, a column that `switch_ss` does not use. F12 is a weighting ablation, not a baseline, and
should not be called Switch-SLAM.

## 2. Equation by equation

| Paper | What it says | Implemented in | Note |
|---|---|---|---|
| Eq. 11-12, Sec. III-C | 3 smallest eigenvalues of H_l, normalised to unit norm; degenerate if any is below [0.12, 0.27, 0.48] | `eig_degeneracy`, `LT_PUBLISHED` | Eq. 12 evaluated gives [0.116, 0.271, 0.471]; the printed 0.48 is used (`LT_MODE=formula` for the other). |
| Status buffer, Fig. 4 | queue Q_s of size n; Normal / Start-End / Fully | `status_of` | n is not given (A2). |
| Eq. 13 | T_k = T_{k-1} (+) sqrt(3) lam1 dT_l (+) (1 - sqrt(3) lam1) dT_v | `blend` on SO(3) x R^3 | lam1 = smallest normalised eigenvalue, weight <= 1. |
| Algorithm 1, lines 2-8 | LO guess if VO failed or all lam >= lam_t; interpolation if queue is Start/End; else VO guess | `SwitchSlamCore.decide` | `decide` changes no state. |
| Sec. III-D | S_vo = fail on VINS-Mono's failure tests; LiDAR only until re-initialised | `vo_fail` | A7. |
| Eq. 14, 16 line 1-2 | well-conditioned: -H^-1 J^T d; degenerate and VO failed: (U Lambda_p U^-1)^-1 J^T d | `finish`, cases 1 and 2 | Lambda_p drops the flagged eigenpairs; applied as a projection of the converged displacement on the kept eigenvectors (D2). |
| Eq. 15, 16 line 3 | argmin ||dx + Hv^-1 Jv dv||^2 + ||dx + (U Lambda_p U^-1)^-1 Jl dl||^2 | `finish`, case 3 | Two plain norms: the minimiser is the mean of the two steps (A4). |
| Algorithm 1 line 10 | push the current status | `buf.append` in `finish` | |
| Sec. III-F | iSAM2 + Scan Context back end | not used | Table II used no loop closure or GNSS, so the front end is what is compared. |

## 3. Where the paper is silent (choices made, all in the code as parameters)

- **A1 Hessian.** The paper says H_l "in (8)" (scan-to-map). Default here: the scan-to-scan Hessian of the patched laserOdometry (`/laser_hessian`, in every container, used by all F-configs), rotated into the map frame for the projection. `SWM` uses the scan-to-map Hessian (`patch_mapping_hessian.py` must be applied to A-LOAM).
- **A2 Queue length** n = 5 (`N_BUF`).
- **A3 Thresholds**: the printed ones.
- **A4 Eq. 15 weighting.** Literal reading, LiDAR weight 0.5 (`EQ15_W`). `SW1` (weight 1) is a documented variant. Since the VO step is zero when the guess is the VO pose, the literal reading halves the LiDAR correction in the observable directions.
- **A5 Units.** Eigenvalues of the 6x6 matrix with the rotation block in radians (`D_RAD`), as F12 did.
- **A6 Degenerate set** = flagged entries among the three smallest eigenvalues.
- **A7 VO failure** = no VINS-Mono pose for 1 s (lost or still initialising), or a jump above VINS-Mono's own reset thresholds (5 m, 50 deg) between consecutive poses (restart). No warm-up: the paper has none.
- **A8 check(Q_s)** reads the past statuses only. So the first degenerate scan after a clean queue goes to the VO guess, the next n-1 scans are interpolated, then VO; the end of a degenerate stretch returns to the LiDAR guess at once. (Verified in `test_corridor_modes_and_drift`.)

## 4. Where this stack differs from the authors' (cannot be removed without their code)

- **D1 No IMU preintegration.** The paper's LiDAR-IMU propagation is replaced by A-LOAM's scan-to-scan odometry increment.
- **D2 Solver.** A-LOAM uses Ceres, not the paper's LM with an explicit H. The remap is applied to the converged displacement (exact for a quadratic cost). A-LOAM's own map is built from its un-remapped solution; only the output trajectory and the next initial guess use the remapped pose. The published pose is chosen so that the guess A-LOAM actually uses equals Algorithm 1's T_init (`pose_to_publish`, tested against laserMapping's T_w_odom bookkeeping).
- **D3 VINS-Mono is a black box.** Hv and Jv are not available, so Eq. 15 is applied to the steps (A4).
- **D4 Platform.** Replay at 0.33-0.5x on a Ryzen 5 5600H, against real time on an i7-1165G7; some scans are dropped and the race with the mapping thread is logged (`sw_race`).
- **D5 Averaging.** The paper reports the mean of three runs.

## 5. Reproduction check (fixed before the first run)

Run `SW` three times on Multi Floor and Long Corridor and compare with Switch-SLAM Table II: Multi Floor 1.61 / 3.63, Long Corridor 2.42 / 5.09 (RMSE / max, m). (The farm, 0.38 / 1.10, needs the Gazebo launcher with `SW` and is a separate step.)
- **Reproduces the published level**: the mean RMSE of SW is within +-50 % of the published value on both sequences. Then SW is reported as "Switch-SLAM as published (our implementation)" next to the published number.
- **Does not**: SW is reported on every sequence as "our implementation of Switch-SLAM", the published numbers stay in their own column, and no claim is made about the published system.
- `SWM` and `SW1` are sensitivity runs, declared here, reported whatever they give, never used to choose a setting.
- Nothing is tuned on any sequence. All runs are reported.

## 6. Evidence available now

- 12 tests pass (thresholds, normalisation, Algorithm 1 branches, status queue, interpolation weight, VINS jump, Eq. 14 projection, Eq. 15 mean, body-to-map rotation of the eigenvectors, the T_w_odom bookkeeping, a corridor simulation, node plumbing).
- Detection rule on logged F24 scan-to-scan Hessians: it fires on 1.5 % of scans on Multi Floor, 4.5 % on Long Corridor and 2.1 % on Corridor02 (median normalised eigenvalues 0.25/0.52/0.80, 0.30/0.46/0.83 and 0.29/0.47/0.83). So SW is expected to run as LiDAR-only A-LOAM with a scan-to-scan guess in over 95 % of scans on these three sequences, and the switching to VINS-Mono matters only in the short stretches where the rule fires. Open loop, a prediction, not a result.

## 7. Run

```
cd fusion_v4 && python3 test_switch_slam.py && python3 test_switch_slam_node.py
REPEAT=1 ONLY="C02 CAVE GEODE MF LC" CFGS="F24 SW" setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_exact_batch.sh > ~/sw_batch.log 2>&1 < /dev/null & disown
# reproduction check, three runs:  REPEAT=3 ONLY="MF LC" CFGS="SW" bash batches/switchslam_exact_batch.sh
# single config by hand:           FRONT=aloam RECORD_KF=1 PLAY_RATE=0.5 ./run_fusion_study.sh SW
```
The log is `switching_log_v2_SW_*.csv` (same columns as the F-configs plus `sw_case`, `sw_status`, `sw_vo_fail`, `sw_lam1-3`, `sw_w`, `sw_degen`, `sw_race`), scored by the same `score_run.py`.

## 8. The generation-1 node, ported (config `V7`)

**What it is.** `fusion_v4/switching_node_v7.py` is the first switching node of the project, the one built before the Schur and Bingham channels: `switchslam_v1/nodes/switching_node_v7.py` (Gazebo form) as used on the Multi Floor bag in `switchslam_v1/multifloor/switching_node_multifloor.py`, which also publishes the fused chain as `/switch_fused_pose`. Chain of versions: `v3` (translation only, speed test) > `v4` (6-DoF) > `v6` (feature-count and jump test, safe LiDAR mode) > `v7` (5-frame status queue, interpolation weight sqrt(3 lam1)). `v5` is an empty file; the repository holds only the import commit, so earlier edits are not recoverable.

**Rule, unchanged.** Detection from the three smallest eigenvalues of `/laser_hessian`, normalised, thresholds from the formula (0.116, 0.271, 0.471). VO failure when fewer than 20 features are tracked or a VINS-Mono step exceeds 1.5 m or 0.8 rad. Status queue of 5 including the current frame: Normal = LiDAR increment; Transition = blend with weight sqrt(3 lam1) on VINS-Mono; Fully = information-weighted 6x6 sum of the two increments with `/vins_mono_hessian` (fall back to LiDAR if the step exceeds 2 m); VO failure = LiDAR increment with the degenerate eigen-directions of the translation block removed (pinv, 2 m guard). The output is the chain of increments, published as `/switch_fused_pose` and logged.

**Changes made for this stack (each marked `# PORT` in the file).** P1 log name `switching_log_v2_<RUN_TAG>.csv`. P2 log time is the scan stamp (bag clock) instead of `time.time()`, which could not be aligned with ground truth. P3 the log carries the A-LOAM scan-to-map pose, the VINS-Mono pose and the Hessian, so `score_run.py` and `fusion_summary.py` read it; the original `feat_count` column is kept. P4 prints the `FUSION_MODE=` line the runner waits for, plus a warning if no synchronised input arrives in 60 s. P5 Hessian messages are cut to 36 entries (the live `/laser_hessian` also carries cost and residual count; the original reshape would fail on 38). No decision line was touched: `test_switching_node_v7.py` loads the original and the port with stubbed ROS, feeds both 299 synthetic scans covering all four modes (a VINS jump and a feature drop included) and requires identical modes, fused poses and published odometry. It passes.

**Not fixed on purpose (properties of the original, they stay):** the LiDAR-IMU extrinsics are ignored and A-LOAM and VINS-Mono world-frame position differences are mixed directly (harmless for Multi Floor and the Cave02 and SubT corridor extrinsics, which are near identity; GEODE has a 2.5 deg yaw offset, so the VINS-driven stretches there carry a small frame error); VO-failure limits are its own, not VINS-Mono's; the final pose is the increment chain, not the scan-to-map result; the queue includes the current frame. Differences from the paper are the five listed in the reply of 4 Nov 2026 and are what `SW` corrects.

**Needs** `/vins_mono_hessian` (`patches/aloam_vins/patch_vinsmono_hessian.py` in the VINS-Mono container; the captured diff of VINS-Mono 90dabb5 contains it). Not run live yet: the unit tests are the only evidence so far.

**Reporting.** Columns: published Switch-SLAM (Table II) | `V7` "generation-1 node, ported" | `SW` "from the paper" | F24. Same bags, replay rates and scorer. Run: `CFGS="F24 SW V7" bash batches/switchslam_exact_batch.sh`, or `FRONT=aloam RECORD_KF=1 PLAY_RATE=0.5 ./run_fusion_study.sh V7`. Check on Multi Floor first: the project's earlier V7-type result was RMSE about 1.39 m; if the port gives a very different number on the same bag, the port (not the rule) is the first suspect.

## 9. One-command reproduction run

`fusion_v4/batches/switchslam_reproduction.sh` runs, in order: the unit tests; a 70 s smoke run of `SW` and `V7` on Multi Floor; `SW` x3 on Multi Floor and Long Corridor (the check of section 5); the A-LOAM scan-to-map Hessian patch followed by `SWM` x3 on the same two; then `repro_summary.py`, which applies the rule of section 5 (mean RMSE within +-50 % of 1.61 and 2.42) and writes `~/sw_repro_summary.txt`. `SWM` is last on purpose: the patch adds an `Evaluate()` per scan to every later run in the container. `SWM`, `SW1`, `V7` and `F24` are listed in the summary and never judged against the rule. Start: `setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_reproduction.sh > ~/sw_repro.log 2>&1 < /dev/null & disown`; smoke only: `STAGES=1`. Duration at 0.5x replay, from the bag lengths (Multi Floor 417 s, Long Corridor 279 s) plus about 2-3 min of restart and shutdown per run (estimate, not measured): one Multi Floor run about 16 min, one Long Corridor run about 12 min, so the six `SW` runs about 1.5 h, the patch and rebuild about 5 min, the six `SWM` runs about 1.5 h, the smoke stage about 6 min: about 3.2 h in total (about 1.6 h for stages 1, 2 and 4 only). Status 4 Nov 2026: written and the verdict tool tested on made-up numbers; not run.

## 10. Short version (one run each on Multi Floor)

`fusion_v4/batches/switchslam_quick.sh`: unit tests; the VINS-Mono and laserOdometry Hessian patches if their markers are missing (idempotent); `SW` and `V7` once on Multi Floor; the scan-to-map patch with a rebuild; `SWM` once. Default: one `SW` run only (about 20 min, estimate); `WITH_V7=1` and `WITH_SWM=1` add one run each (and the patches they need). One run per config is a first look, not the three-run check of section 5: no verdict is claimed from it, and a `SW` value far from 1.61 / 3.63 from a single run is a reason to run the three, not a result. Status: written, syntax-checked, not run.

## 11. First live result (4 Nov 2026, laptop, Multi Floor, 0.5x, one run, commit 3d1014b)

`SW`: ATE RMSE 5.03 m, max 10.22 m (full span). Same session, `F24`: 0.45 / 0.92. Published Switch-SLAM: 1.61 / 3.63. One run, so no verdict under the rule of section 5 (needs three); the single value is 3.1 times the published RMSE.

Log of the run (4126 scans): the rule fired on 1.5 % of scans (62 scans used VINS-Mono: 40 `VO`, 22 `INTERP`); 98.5 % were LiDAR-only scan-to-map with the scan-to-scan initial guess; median normalised eigenvalues 0.25 / 0.52 / 0.80; VINS-Mono counted as failed in 4.9 % of scans (start-up); 9.7 % of scans had an earlier scan still being mapped (`sw_race`). The final pose followed A-LOAM's scan-to-map pose within 0.07 m. The trajectory agreed with `F24`'s A-LOAM trajectory to 0.05 m until about 60 s and left it between 60 s and 120 s (stairs), reaching 7 m at 120 s.

Reading (from the log, not tested by a further run): pure A-LOAM on Multi Floor in this stack scored 26.4 m (F5, earlier study). `SW` at 5.03 m is much better than that because the 62 VINS-Mono scans help, but with the rule firing on 1.5 % of scans `SW` is mostly A-LOAM, and A-LOAM's initial guess here is the scan-to-scan odometry, not the paper's LiDAR-IMU propagation (difference D1, section 4). So the likely cause of the gap is D1 together with a rule that rarely fires on this sequence, not an error in Algorithm 1. This explanation is a hypothesis: no run with an IMU-propagated guess has been made. No setting was changed after seeing this result.

## 12. SWI: gyro prior (variant, declared 4 Nov 2026 after the first live result)

**Why.** Section 11: with the rule firing on 1.5 % of scans, `SW` is mostly A-LOAM, whose guess has no IMU (D1); the paper's LiDAR propagation is IMU-based. **Hypothesis, not a result:** a gyro rotation prior lets A-LOAM survive the stairs and moves `SW` toward the published level.

**What.** `fusion_v4/gyro_prior.py` integrates the gyro (zero-order hold) between the last finished scan and the current one, converts it to the LiDAR frame with the extrinsic rotation, and `SwitchSlamCore.decide(..., gyro_dR=...)` replaces the ROTATION of the LiDAR increment with it; the translation stays A-LOAM's scan-to-scan translation. Everything else (rule, queue, interpolation, Eqs. 14-16) is `SW`. No bias estimate, no accelerometer, no position preintegration, no tuning. If the IMU samples do not cover a scan, that scan falls back to the plain `SW` increment. Config `SWI` = `SW` + `GYRO=1`; IMU topics tried: `/imu/data` and `/cmu_sp1/imu/data` (Multi Floor). Log columns added: `sw_gyro` (1 = gyro used), `sw_gyro_deg` (difference between gyro and A-LOAM odometry rotation, degrees).

**Honest status.** Tests: `test_gyro_prior.py` (integration against exact angles, coverage fallback, frame conversion, core use, node plumbing with constant yaw rate); `SW` behaviour unchanged (11 + node + v7 tests still pass). Not run live. Not the paper's system: the paper's propagation is a full LiDAR-IMU one; SWI is the nearest thing this stack allows. Report as "our implementation, gyro-aided variant (SWI)", next to `SW`, whatever it gives. Run: `RUN_CFGS=SWI bash batches/switchslam_quick.sh` (one Multi Floor run, about 20 min); the script prints the share of scans where the gyro was used.

## 13. First live result of SWI (4 Nov 2026, laptop, Multi Floor, 0.5x, one run, commit 1376a25)

| Config | ATE RMSE / max (m) | Note |
|---|---|---|
| Switch-SLAM, published (Table II, mean of 3) | 1.61 / 3.63 | |
| SW (paper's rule, A-LOAM guess) | 5.03 / 10.22 | section 11 |
| **SWI** (SW + gyro rotation prior) | **1.51 / 4.35** | gyro used in 100 % of 4131 scans; median gyro-vs-odometry rotation difference 0.70 deg per scan |
| F24 (this thesis) | 0.45 / 0.92 | same session |

One run: no verdict under the three-run rule of section 5, and none is claimed. The hypothesis of section 12 (the missing IMU in the guess is what separates `SW` from the published level) is supported by this one run, not proven.

**Caveats that must stay with the number.** (1) SWI was designed after the `SW` result on this same sequence, so Multi Floor is development data for SWI; no parameter was tuned (the only change is the rotation source), but the choice to try it followed the result. The independent tests are the other sequences: Long Corridor (published 2.42 / 5.09) and the sequences with no published number. (2) RMSE is below the published value, the maximum error is 20 % above it; one run cannot separate this from run-to-run spread. (3) The median 0.7 deg per scan disagreement between gyro and A-LOAM odometry rotation is large for a 0.1 s scan period; cause not examined (candidates: gyro bias, time offset between IMU and LiDAR stamps, A-LOAM odometry error). (4) SWI is "our implementation, gyro-aided variant", not the paper's LiDAR-IMU propagation.

## 14. Long Corridor, SW and SWI (4 Nov 2026, laptop, 0.5x, one run each, commit 1376a25)

| Config | Multi Floor RMSE / max (m) | Long Corridor RMSE / max (m) |
|---|---|---|
| Switch-SLAM published (mean of 3) | 1.61 / 3.63 | 2.42 / 5.09 |
| SW | 5.03 / 10.22 | 12.58 / 23.53 |
| SWI (gyro prior) | 1.51 / 4.35 | 13.81 / 24.78 |
| F24 | 0.45 / 0.92 | 1.75 to 2.15 / 3.53 to 5.57 (three runs, same batch) |

Neither replica reproduces the published level on Long Corridor. The gyro prior, which closed the gap on Multi Floor, did nothing here (13.81 against 12.58; gyro used in 100 % of scans, median gyro-vs-odometry rotation difference 0.65 deg). So the Multi Floor agreement of SWI is not a general reproduction; it is one run on the sequence that SWI was designed after. Under the rule of section 5 (needs three runs): `SW` is outside the +-50 % band on both sequences in its single runs (3.1 times and 5.2 times the published RMSE).

Log of the `SW` run: the rule fired on 4.5 % of scans (78 INTERP, 47 VO of 2776); the trajectory is 14 % shorter than F24's (518 m against 603 m), i.e. the usual slide along a corridor. The scan-to-scan Hessian of this sequence has median eigenvalues (rad, m units) 65 / 85 / 166 / 387 / 2066 / 5162; the weakest direction is mainly translation (tx 0.62, tz 0.46) but only 1.3 times weaker than the second weakest, so the normalised smallest eigenvalue is 0.29, above the 0.12 threshold: the paper's rule, with this Hessian, does not call the corridor degenerate. Whether the paper's scan-to-map Hessian (`SWM`) would is untested; changing thresholds to make the rule fire would be tuning on the target and is not done.

Reading: with the Hessian and guess available in this stack the paper's rule hardly fires on Multi Floor (1.5 %) or Long Corridor (4.5 %), so `SW` and `SWI` behave mostly like A-LOAM with or without a gyro prior. The honest statement for the report: our implementations of Switch-SLAM do not reproduce the published numbers on Long Corridor; the difference is attributed (unproven) to the missing LiDAR-IMU system (D1) and the Hessian used (A1). No claim about the published system.

## 15. The failed SWM attempt on Long Corridor (4 Nov 2026) and what it still shows

The first `SWM` run on Long Corridor (11:40-11:54) is **not an SWM result**: the mapping-Hessian patch did not compile (mixed Eigen 3.3 / 3.4 in the container, `#include <eigen3/Eigen/Dense>`), the old binary ran, `/mapping_hessian` never arrived (Hessian present in 0 % of rows), the rule never fired (0.0 % of scans, all `SW_LIDAR`). It is therefore a run of A-LOAM with the scan-to-scan guess and no switching at all: ATE 13.12 / 24.22 m. Next to `SW` (12.58 / 23.53; the rule fired in 4.5 % of scans) and `SWI` (13.81 / 24.78) this is evidence, from three single runs, that on Long Corridor the switching contributed little in either replica: with or without it the result is the A-LOAM result of about 13 m. Run-to-run spread is unknown (one run each). The script was fixed (Eigen include in `laserMapping.cpp`, build check, check that the binary contains `/mapping_hessian`); the real `SWM` run is still to be made.

## 16. SWM on Long Corridor (4 Nov 2026, laptop, 0.5x, one run, commit 48cbd22; mapping patch compiled after the Eigen include fix)

Valid run: `/mapping_hessian` present in 100 % of 2776 rows. ATE RMSE / max **13.19 / 23.83 m** (published 2.42 / 5.09).

| Long Corridor, one run each | RMSE / max (m) | rule fired |
|---|---|---|
| Switch-SLAM published (mean of 3) | 2.42 / 5.09 | |
| A-LOAM, no Hessian (invalid SWM attempt, section 15) | 13.12 / 24.22 | 0 % |
| SW (scan-to-scan Hessian) | 12.58 / 23.53 | 4.5 % |
| SWI (SW + gyro prior) | 13.81 / 24.78 | 4.5 % |
| SWM (scan-to-map Hessian, as in the paper) | 13.19 / 23.83 | 1.4 % (20 INTERP, 19 VO) |

The hypothesis of section 14 (the paper's scan-to-map Hessian would flag the corridor) is **not supported**: the scan-to-map Hessian looks less degenerate to the rule, not more. Median sorted eigenvalues (rad, m units) 181 / 257 / 319 / 1047 / 45080 / 62813; median normalised smallest three 0.39 / 0.56 / 0.73, against thresholds 0.12 / 0.27 / 0.48. The rule fires on 1.4 % of scans, fewer than with the scan-to-scan Hessian (4.5 %). All four variants give 12.6 to 13.8 m, so on this sequence neither the Hessian choice, nor the gyro prior, nor the switching itself changes the result in this stack; with single runs the spread between them (1.2 m) cannot be separated from run-to-run noise.

Statement for the report: our implementations of Switch-SLAM (SW, SWI, SWM) do not reproduce the published Long Corridor result; on Multi Floor one run of SWI (1.51 / 4.35) was close to the published 1.61 / 3.63, on a sequence on which SWI was designed. The remaining differences to the paper (no LiDAR-IMU system, A-LOAM + VINS-Mono in place of the authors' components, unreleased code and unpublished parameters) are listed in sections 3 and 4; which of them causes the Long Corridor gap was not isolated.
