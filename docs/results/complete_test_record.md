# SwitchSLAM QR — Complete Test Record

Oct 18, 2026 · @Kevin

## Executive summary

Across about 110 live ROS replays on three SubT-MRS sequences, the method beats Switch-SLAM on Multi Floor by a wide margin, is level with it on Long Corridor without loop closure (2.27 ± 0.45 against 2.42 m) and is below it with loop closure (1.54 m). It does not reach the best published numbers: SuperLoc reports 0.817 m on Long Corridor and 0.315 m on Floor01, both without loop closure. Before the live work there were several synthetic studies (5 seeds each, thousands of Monte Carlo draws) and one Gazebo log. Afterwards came more than 60 offline replay analyses of the logged runs.

| Sequence | Our best front end (no loop closure) | Our best with loop closure | Switch-SLAM RA-L 2024 (no loop closure) | Best other published |
| --- | --- | --- | --- | --- |
| Multi Floor (417 s) | **0.617 ± 0.107 m** (F8, 9 live runs) | **0.347 ± 0.036 m** (F8, 6 recordings; F16 + loops 0.523 ± 0.224 at 0.5×, 6 recordings) | 1.61 m | 0.315 m (SuperLoc, no loop closure); 0.401 m (challenge, FAST-LIO2 + HBA) |
| Long Corridor (279 s, 579 m) | **2.27 m** (F16, 6 live runs; was 4.53 with F8) | 1.54 ± 0.30 m (F16 + loops, 6 recordings; was 2.67 with F8) | 2.42 m | 0.817 m (SuperLoc, no loop closure); 1.254 m (challenge, with back end); 1.386 m (LODESTAR) |
| Corridor02 (893 s, 695 m) | 1.708 ± 0.069 m (F16, 6 live runs; was 2.12 with F8) | 1.25 ± 0.44 m (F16 + loops, 6 recordings; no gain in 2 of 6; was 2.10 with F8) | none published | none published |

All values are ATE RMSE, Umeyama SE(3) alignment without scale, full span, mean of the runs listed.

**What is established.** The main points are:

- Soft Schur-weighted LiDAR translation on top of VINS-Mono roughly halves VINS-Mono's error on all three sequences.
- Loop closure cuts Multi Floor error by 45%, with all 6 recordings improving (Wilcoxon p = 0.031).
- The dominant remaining error everywhere is VINS-Mono heading (yaw) drift of 6–9°. Replacing only the yaw with ground truth would give 0.39 / 1.42 / 0.90 m.
- The new structure-anchored heading correction (SAH, config F16) roughly halved Long Corridor error live, from 4.53 to 2.27 m (6 runs). On Corridor02 it improved the live result from 2.12 to 1.708 m (6 runs). On Multi Floor it left the mean unchanged (0.64 m, against 0.60 m for F8 at the same replay rate).

**What is not yet established.**

- Long Corridor and Corridor02 have been used to develop SAH, so they are development data. The final claim needs a sequence never used before and a non-structured control, such as a cave.
- Long Corridor with F16 has a wide spread (1.99, 2.16 and 3.17 m); run 3 came from the A-LOAM path drifting inside the loop, a cause that is not yet understood.
- The Multi Floor F16 runs were replayed at 0.5× and the F8 runs at 1.0×, so that comparison is not like-for-like (see Comparisons).
- Every published comparison inherits a metric caveat: the alignment and span used by other authors are not always stated.

## System under test

The system went through three generations. The first two were tested only in simulation, Gazebo and one Multi Floor reference. The third, `fusion_node_v2`, produced every real-data result.

| Generation | Code | What it does | Tested on |
| --- | --- | --- | --- |
| Old switching node | `switching_node_schurbingham.py` | Switch-SLAM-style mode switch. The modes are LIDAR\_ONLY, TRANSITION, TIGHTLY\_COUPLED and LIDAR\_ONLY\_SAFE, chosen by a 5-frame status buffer. Detection uses the semicircle thresholds \[0.12, 0.27, 0.48\] on Schur blocks plus Channel T (λ3 < 0.15). Fusion is unweighted (H\_l + H\_v)⁻¹(…). | Gazebo (1 run); Multi Floor (3 reference runs) |
| Proposed redesign D1–D9 | `verify_final_methods.py`, `compare_old_vs_new_pipeline.py` | Noise-floor significance test on Schur eigen-directions, projected covariance intersection, Bernoulli CUSUM switching, VINS-Mono's real failure flags | Synthetic ICP simulation only |
| fusion\_node\_v2 / FusionCore | `fusion_v2.zip` → `fusion_v3` | VIO-primary. VINS-Mono gives the pose and rotation. Each mapped A-LOAM scan corrects the relative translation with W\_t = (c·S\_tt + I)⁻¹ c·S\_tt, the Schur translation block, used as a soft per-direction weight. The fused pose seeds A-LOAM's next scan-to-map match. A 20 s LiDAR-only WARMUP runs before VINS-Mono starts. A keyframe recorder and offline loop-closure back end are optional. | All real-data runs, 13–17 Oct |

The live configurations of fusion\_node\_v2 are below. They are set by environment variables in `run_fusion_study.sh`. C\_T is the LiDAR translation weight, and κ gate means LiDAR is used only when κ(S\_RR) ≤ 15.7 (1e9 = gate off).

| Config | Settings | Role |
| --- | --- | --- |
| F0 | FUSION\_MODE=vins | VINS-Mono alone inside the node (control) |
| F1 | fused, C\_T = 0.003, κ gate 15.7 fixed | First method: gated soft correction |
| F2 | as F1, κ threshold by online Otsu | Label-free threshold variant |
| F3 | fused, C\_T = 0.003, no gate | Gate ablation |
| F4 | lidar, A-LOAM seeded by VINS prediction | LiDAR-only baseline |
| F5 | lidar, no VINS prediction | Pure A-LOAM baseline |
| F6 | F1 + LiDAR rotation weight C\_R | Defined, dropped after replays showed C\_R hurts (never run live) |
| F7 | fused, C\_T = 0.01, no gate | C\_T from the 5-s-horizon bag-0 rule |
| F8 | fused, C\_T = 0.03, no gate | **Current method**, C\_T frozen from here on |
| F9 / F10 | C\_T = 0.1 / 0.3, no gate | C\_T sensitivity |
| F11 | WEIGHT\_MODE=iso | Isotropic weight with the same mean information (replay only) |
| F12 | WEIGHT\_MODE=switch\_ss, κ 15.7 | Hard switch using the Switch-SLAM detection rule |
| F13 | WEIGHT\_MODE=proj | Hard per-direction 0/1 (replay only) |
| F14 | WEIGHT\_MODE=lidar (W = I) | LiDAR translation always, VINS rotation |
| F15 | WEIGHT\_MODE=diag | Diagonal H\_tt instead of Schur S\_tt (replay only) |
| F16 | F8 + SAH=1 | F8 plus structure-anchored heading |

The threshold study of 13 Oct used the old node's switching with 15 detection rules (A1–A8, B1–B5, C1–C2). Those rules are listed in the chronological log.

## Platform and environment

The live runs ran on one laptop in Docker. The scoring, replays and simulations ran in a cloud Python sandbox, and loop closure ran in either place.

| Layer | Detail |
| --- | --- |
| Host | User's laptop, Ryzen 5 5600H (6 cores), Linux with Docker. The mapping node saturates one core at about 93 °C at 1.0× replay. |
| Container `switchslam_gpu_v2` | ROS Noetic, holding roscore (use\_sim\_time), Velodyne packet conversion where needed, A-LOAM (scan registration, odometry, mapping with Hessian export on `/laser_hessian`), `fusion_node_v2.py`, `keyframe_recorder.py` and, from 17 Oct, `structure_heading.py` |
| Container `vinsmono_test` | ROS Kinetic, holding VINS-Mono `feature_tracker` and `vins_estimator`, with configs generated per sequence by `make_vins_config.py`. IMU noise and tracker settings were copied from Multi Floor and never tuned. |
| Bag player | `ros:noetic` container, `rosbag play --clock -r PLAY_RATE`, on the `vins_bridge` Docker network |
| Batch driver | `run_fusion_study.sh` (REPEAT, RECORD\_KF, SEQ\_ENV, BAG\_DIR\_OVERRIDE). A clean stack restart runs before every run. A run is rejected if it has fewer than 3000 log rows (Multi Floor rule). Long batches run under `setsid nohup systemd-inhibit`. |
| Storage | Bags on the laptop (`~/Downloads/RosBag`, Corridor02) and on the external drive "One Touch1" (Long Corridor, Multi Floor copy, used for the 17 Oct batch) |
| Loop-closure back end | `backend_icp.py` + `backend_graph.py` (coarse-to-fine point-to-plane ICP, GTSAM, Huber + χ² pruning), driven by `run_backend.py` / `backend_multi.py`. It ran in `~/venv_backend` on the laptop and in the sandbox. |
| Analysis sandbox | Anthropic cloud Linux with Python 3, numpy, scipy and pandas. It ran the scorer re-implementations, open-loop replays (`fusion_summary.py`, `sah_replay.py`), synthetic Monte Carlo studies and the ROS-stubbed node harness (`node_harness.py`). |

**Replay rate.** It changed during the project, and it matters for comparisons.

| Period | Sequence | Rate | Rows per run (ideal) | Note |
| --- | --- | --- | --- | --- |
| 13–14 Oct | Multi Floor | 1.0× | 3100–3400 (≈ 4170) | About 20–25% of scans skipped. All F0–F10 Multi Floor numbers are at this rate. |
| 15 Oct | Long Corridor | 1.0× | 2758–2774 (≈ 2777) | Essentially complete |
| 16 Oct | Corridor02, attempt 1 | 1.0× | 4628–5554 (≈ 8900) | About 40% skipped. 8 runs discarded before scoring. |
| 16–17 Oct | Corridor02 | 0.33× | 8191–8282 | About 20% skipped in bag minutes 8–11 |
| 17 Oct | Corridor02 sensitivity | 0.2× | 8858 (F8), 8175 (F5) | Essentially complete for F8 |
| 17 Oct | F16 Long Corridor / Multi Floor / Corridor02 | 0.5× / 0.5× / 0.33× | 2775–2776 / 4082–4110 / pending | Chosen so the heading step never skips a keyframe |

**Wall-clock time per run**, taken from the run-finish timestamps:

- Multi Floor at 1.0×: about 7.7 min.
- Long Corridor at 1.0×: about 5.4 min.
- Corridor02 at 0.33×: about 46 min.
- Corridor02 at 0.2×: about 75–80 min.
- Long Corridor at 0.5×: about 10.2 min.
- Multi Floor at 0.5×: about 16.4 min.

The total live machine time is roughly 30 hours.

## Datasets and ground truth

Three real SubT-MRS sequences were used, all from CMU's Hawkins building and all with a VLP-16 LiDAR, a 640×480 camera and a 200 Hz IMU. Before them came one Gazebo log and the synthetic scenes.

| Sequence | Platform | Duration / path | Topics | Ground truth | Clock check | Role now |
| --- | --- | --- | --- | --- | --- | --- |
| SubT-MRS Multi Floor (Floor01) | Legged robot | 3 bags, 417 s span; bag 0 is calibration, bags 1–2 are held out | `/velodyne_packets` (converted), camera, `/imu/data` | `ground_truth_path.csv` (SubT-MRS; same sequence as SuperLoc `floor01_gt.txt`) | On the header clock. `align_gt_time.py` self-test: +4.00 s injected gave +4.00 / +4.02 s; aligned data gave +0.01 s. | Tuning sequence: C\_T, loop rounds and odometry noise were all chosen here |
| SubT-MRS Long Corridor (Corridor01, RC) | Wheeled RC | 279 s, 579 m GT path, loop (start–end 3.3 m) | `/velodyne_packets` (converted), `/camera_1/image_raw` (24 Hz), `/imu/data` | `corridor01_gt.txt` (SuperLoc release, TUM, 1385 poses at 5 Hz) | GT is on the header clock (2018); record times are 2023. Residual offset +0.04 s. | Fresh test for F8 (15 Oct); development data for SAH since 17 Oct |
| SubT-MRS Corridor02 (RC1) | Wheeled RC | 893 s, 695 m GT path, start–end 2.7 m. Stands still for the first ≈ 70 s. | `/velodyne_points` (PointCloud2), `/camera_1/image_raw`, `/imu/data` | `corridor02_gt.txt` | Header clock agrees with GT. Residual +0.03 s. Record times are 2024 and not used. | Held-out test for F8 (protocol written before the runs); development data for SAH |
| Gazebo (old pipeline) | Simulated robot | One run, 4017 frames | Simulated VLP-16, camera, IMU | Simulator pose | — | Old-node diagnostics only |
| Synthetic scenes | Python ICP simulation | 300-frame drive (open area → 100-frame corridor → corridor with doors), plus corridor, corridor\_doors and open\_80\_10\_10 scenes | Simulated points, 0.4 m voxel map | Known geometry | — | Method logic checks only |

**How far to trust the ground truth.** SubT-MRS trajectories are fused from scan-to-map matching against a FARO map and the platform's own odometry. They are therefore not independent of the sensors being tested, and they are weakest where LiDAR degenerates. Differences below about 0.1 m are treated as ties.

- On Corridor02, the GT heading jumps by several degrees between keyframes 0.3 s apart at some times. Only position ATE is reliable there.
- The Corridor02 keyframe files end at 760 s of 893 s, because the recorder saved its last checkpoint before shutdown.

**Candidates not yet used.** These are held back for the untouched test and the controls:

- GEODE Stairs\_Alpha
- SubT-MRS BlockLiDAR and BlockVisual
- SubT-MRS Cave01–04, the planned non-structured control
- FusionPortableV2 `handheld_underground00`

Their links and published baselines are in `claude/Dataset_Test_Plan.md`.

## Evaluation protocol and metrics

Every real-data number in this report is ATE RMSE in metres, with the maximum error beside it where useful. It is computed by our own scorer (`multifloor_ate_eval.py` / `score_run.py`) with rigid Umeyama SE(3) alignment, no scale, over the full logged span.

| Item | Rule |
| --- | --- |
| ATE | RMSE and max of position error after one global SE(3) Umeyama alignment, no scale, full span of the log. Multi Floor is also scored per segment: bag 0 (calibration) and bags 1–2 (held out), each with its own alignment. |
| RPE | 1 s horizon on held-out frames, used to judge short-term smoothness |
| Repeats | 3 live runs per configuration per sequence (6–9 for F8 on Multi Floor). Reported as mean ± sd. Ties are below about 0.1–0.3 m between separate runs. |
| Row rule | A run counts only with at least 3000 log rows on Multi Floor. Shorter runs go to `failed_runs.csv` and are left out of the means. |
| Open-loop replay | The logged scan-to-map poses and Hessians are re-fused offline with a changed rule. A replay of a run's own setting reproduces its live ATE exactly (0.576, 0.475). Replays of other settings are approximations, because live runs feed the fused pose back into A-LOAM. |
| Paired tests | Wilcoxon signed-rank (front end vs loops, replay variants). Sign counts ("better in k of n"). |
| Detection metrics (threshold study) | TPR / FPR on held-out bags 1–2 against A-LOAM drift terciles in 8 s windows; Youden's J = TPR − FPR |
| Synthetic metrics | ATE in cm, mean ± sd over 5 seeds; ANEES against a χ² band; detection rates per scene; CUSUM ARL0 and delay |

**Integrity rules that were kept.**

- Settings are frozen before a sequence is first run: C\_T = 0.03, 1 loop-search round and odometry noise 1.46° / 0.054 m all come from Multi Floor.
- A sequence used to choose or change anything becomes development data. Long Corridor became development data on 15 Oct and Corridor02 on 17 Oct.
- Post-hoc choices are labelled post hoc:
  - the 99th calibration percentile;
  - C\_T = 0.03;
  - one loop-search round.
- Bugs in the pipeline (topic, clock, container, regex) are fixed without touching method settings, and affected runs are repeated.
- Every negative result stays in the record.

## Published baselines

Switch-SLAM is the fair main target: a LiDAR–camera system without loop closure, scored as a 3-run mean. The challenge and LiDAR-odometry entries use stronger front ends or back ends, and their alignment and span are not always stated.

| Method (source) | Multi Floor ATE (m) | Long Corridor ATE (m) | Back end | Fair comparison for us | Verified |
| --- | --- | --- | --- | --- | --- |
| Switch-SLAM, RA-L 2024, Table II | 1.61 (max 3.63) | 2.42 (max 5.09) | No | Yes, front end vs front end | Read from the paper |
| SubT-MRS ICCV'23 challenge, FAST-LIO2 + HBA (Liu et al.) | 0.401 | 1.454 | Yes | Against our + loops numbers only | SubT-MRS paper tables |
| SubT-MRS ICCV'23 challenge, FAST-LIO + pose graph (Weitong et al.) | 0.577 | 1.254 | Yes | As above | SubT-MRS paper tables |
| LODESTAR (Table V) | — | 1.386 (threshold grid-searched on this sequence) | No | Yes, with that caveat | Read from the paper |
| GenZ-ICP / DLIO / LIO-SAM / KISS-ICP / FAST-LIO2 / iG-LIO / AdaLIO (LODESTAR Table V) | — | 1.982 / 2.294 / 2.959 / 3.028 / 3.113 / 3.136 / 3.160 | No | LiDAR-only odometry | Read from LODESTAR |
| D²-LIO paper: FAST-LIO2 / D²-LIO | — | 1.08 / 1.65 | No | Reference only | Earlier notes |
| LIO-SAM + LP-ICP (arXiv 2501.02580) | — | 11.92 | Yes | Reference only | Read from the paper |
| SuperLoc (arXiv 2412.02901, Table III) | 0.315 (Floor01) | 0.817 (Corridor01) | No (odometry) | Closest published match on both sequences; its ATE is not defined in the paper | **Verified**: Table III, its caption and the text read twice on 19 Oct |
| Corridor02 | — | — | — | No published SLAM result found; SuperLoc's "Corridor02" is a different sequence | — |

FAST-LIO2 and LIO-SAM are reported to fail on Multi Floor (NV-LIO, qualitative). The GenZ-LIO (T-FR 2026) table covers both sequences but could not be read.

## Chronological test log

Eighteen test phases ran in order, from synthetic checks of the old detector to live runs, back end and log checks of the heading correction. Each phase below gives its purpose, setup, scale, time, expected versus obtained results, and the conclusion drawn.

| # | Date (2026) | Phase | Kind | Scale |
| --- | --- | --- | --- | --- |
| 1 | before 5 Oct | Old detector checks: Joint vs Decoupled, aliasing, Gazebo log | Synthetic + 1 Gazebo log | 400–800 trials, single seed; 4017 frames |
| 2 | 5 Oct | Final-methods verification S1–S7 | Synthetic ICP Monte Carlo | 5 seeds; 200–4000 runs per check |
| 3 | 5 Oct | Old vs new pipeline, 2×2×2 factorial | Synthetic 30 m drive | 5 scenarios × 5 seeds × 8 pipelines |
| 4 | 6 Oct | Channel T / Bingham statistics checks | Real Multi Floor log + simulation | 3932 frames; 1500–3000 reps |
| 5 | before 13 Oct | Old node reference on Multi Floor | Live ROS | 3 runs |
| 6 | 12–13 Oct | Degeneracy threshold study, 15 rules | Live ROS + offline | 15 runs + offline screen |
| 7 | 13–14 Oct | fusion\_node\_v2: offline evidence, calibration, first batch F0–F5 | Replay + live | 2 replayed logs; 19 live runs |
| 8 | 14 Oct | C\_T sweep F7–F10 and F8 repeats | Live | 21 runs |
| 9 | 14 Oct | Loop-closure back end on Multi Floor | Offline on recordings + synthetic | 1 + 6 + 3 + 1 recordings |
| 10 | 14 Oct | Translation-weighting ablation | Paired replay | 12 logs × 9 rules |
| 11 | 15 Oct | Long Corridor: setup, 15 live runs, back end, diagnosis | Live + replay | 1 smoke + 15 runs |
| 12 | 15–17 Oct | Corridor02 held-out test | Live + replay | 1 smoke + 8 discarded + 15 + 2 runs |
| 13 | 17 Oct | Yaw-drift diagnosis, oracle, Option 2 | Replay with GT | 12 logs, 3 sequences |
| 14 | 17 Oct | SAH development v1–v7, stress, node harness | Replay with keyframes | 12 logs × 7 versions × 7 cases |
| 15 | 17–18 Oct | SAH live (F16) | Live | 9 runs |
| 16 | 18 Oct | F16 batch completed: Corridor02, back end, Long Corridor run 3 check | Live + offline | 3 live runs; 9 back-end recordings; 3 logs checked |
| 17 | 19 Oct | SuperLoc figures verified; near-range filter study | Paper check + replay with keyframes | 12 recordings × 7 radii; 4 object cases × 5 radii |
| 18 | 19 Oct | Six runs per sequence, matched Multi Floor control, Corridor02 loop check | Live + offline | 12 live runs; 18 back-end recordings |

### Phase 1 — Old detector: synthetic checks and the Gazebo log (before 5 Oct)

**Purpose.** To check whether the old pipeline's detection channels separate degenerate from safe scenes. Channel R is the Schur complement with Switch-SLAM's semicircle thresholds; Channel T is the orientation tensor with λ3 < 0.15.

**Setup.** Random 6×6 SPD Hessians, plus synthetic periodic and non-periodic scenes for aliasing. Each used a single fixed seed (42 or 7) and 400, then 800, trials. The Gazebo log is one run of `switching_node_schurbingham.py`, 4017 frames.

| Test | Expected | Obtained | Status |
| --- | --- | --- | --- |
| v1: Joint vs Decoupled, both judged by the semicircle rule | Decoupled detects better | Decoupled recall 1.00, Joint 0.57 | Retired: ground truth was built from the same rule (circular) |
| v2: Joint with its own semicircle rule, Decoupled with DCReg κ(S) > 10, independent ground truth | Fairer gap | Joint recall 0.83, falling from 0.99 at low to 0.68–0.75 at high rotation/translation scale ratio. Decoupled 1.000. | Decoupled's 1.000 is an artefact: the ground-truth cutoff equals κ\_th = 10 |
| Scenario 2 Part A: is the Hessian blind to aliasing? (400 and 800 trials) | Difference ≈ 0 | Relative Hessian difference: mean 0.56%, median 0.31%, max 4.4% | "Approximately blind", not exactly |
| Scenario 2 Part B: Channel T periodicity score | Separates periodic scenes | Recall 1.00, precision 0.995 | Retired: the score is not in the deployed code, and the classes were separable by construction |
| Gazebo log, per-mode error | — | Channel R fires on about 80% of frames. Mean pose error (log units): flagged 29.6 vs not flagged 27.7 (Channel R); 33.7 vs 21.4 (Channel T); LIDAR\_ONLY\_SAFE 0.96 vs TIGHTLY\_COUPLED 30.5. | Correlational, from one run; confounded by which segment each mode ran in |

**Conclusion.** None of the old thresholds had a derivation, and the validation was circular. This led to the full audit (36 items) and the redesign tested in Phases 2–3.

## Master results table (real data)

Every live configuration on every real sequence is listed below, front end first, then with loop closure. All values are ATE RMSE in m, Umeyama SE(3), full span. The threshold-study rules (Phase 6, 1.38–17.67 m, one run each) and the synthetic results are in their phases.

| Sequence | Config | Rate | Runs | Mean ± sd | Min–max of runs | Note |
| --- | --- | --- | --- | --- | --- | --- |
| Multi Floor | Old node | 1.0× | 3 | 1.39 ± 0.14 | — | Max 4.58 ± 0.12 |
| Multi Floor | F0 VINS-Mono | 1.0× | 3 | 1.28 ± 0.02 | 1.25–1.29 | — |
| Multi Floor | F1 gated, C\_T 0.003 | 1.0× | 3 | 1.05 ± 0.05 | 1.00–1.09 | — |
| Multi Floor | F2 gated, Otsu | 1.0× | 3 | 1.05 ± 0.07 | 0.99–1.12 | — |
| Multi Floor | F3 no gate, C\_T 0.003 | 1.0× | 3 | 0.96 ± 0.05 | 0.93–1.02 | — |
| Multi Floor | F7 C\_T 0.01 | 1.0× | 4 | 0.88 ± 0.03 | 0.85–0.91 | — |
| Multi Floor | **F8 C\_T 0.03** | 1.0× | 9 | **0.617 ± 0.107** | 0.47–0.77 | Current method |
| Multi Floor | F8 C\_T 0.03, matched control | 0.5× | 3 | 0.603 ± 0.112 | 0.52–0.73 | Same rate as F16 (Phase 18) |
| Multi Floor | F9 C\_T 0.1 | 1.0× | 3 | 0.77 ± 0.23 | 0.51–0.94 | — |
| Multi Floor | F10 C\_T 0.3 | 1.0× | 3 | 0.69 ± 0.09 | 0.59–0.77 | — |
| Multi Floor | F16 (F8 + SAH) | 0.5× | 6 | 0.640 ± 0.115 | 0.53–0.80 | Matched F8 at 0.5×: 0.603 ± 0.112; no difference |
| Multi Floor | F16 + loops (iso, 1 round) | offline | 6 | 0.523 ± 0.224 | 0.363–0.955 | Run 5 worse with loops (0.767 to 0.955); F8 + loops was at 1.0× |
| Multi Floor | F4 LiDAR, VINS-seeded | 1.0× | 3 + 1 | 25.7 ± 16.7 | 9.56–42.93; kf 7.75 | Below the row rule |
| Multi Floor | F5 A-LOAM only | 1.0× | 3 | 26.4 ± 11.7 | 13.20–35.43 | Below the row rule |
| Multi Floor | F7 + loops (iso, 2 rounds) | offline | 1 | 0.309 | — | — |
| Multi Floor | **F8 + loops (iso, 1 round)** | offline | 6 | **0.347 ± 0.036** | 0.303–0.395 | 6 / 6 improve, p = 0.031 |
| Multi Floor | F9 + loops (1 round) | offline | 3 | 0.356 ± 0.102 | 0.272–0.470 | — |
| Multi Floor | F4 + loops | offline | 1 | 8.18 | — | Worse than without |
| Long Corridor | F0 VINS-Mono | 1.0× | 3 | 5.81 ± 0.27 | 5.65–6.13 | — |
| Long Corridor | F8 | 1.0× | 3 | 4.53 ± 0.49 | 3.97–4.87 | Frozen settings |
| Long Corridor | F12 hard switch | 1.0× | 3 | 5.43 ± 0.71 | 4.65–6.05 | — |
| Long Corridor | F14 LiDAR translation | 1.0× | 3 | 13.2 ± 8.7 | 6.56–23.11 | — |
| Long Corridor | F5 A-LOAM only | 1.0× | 3 | 15.8 ± 6.3 | 11.21–23.01 | — |
| Long Corridor | **F16 (F8 + SAH)** | 0.5× | 6 | **2.27 ± 0.45** | 1.99–3.17 | Rows equal to F8's (complete in both) |
| Long Corridor | F8 + loops | offline | 3 | 2.67 ± 0.73 | 1.85–3.26 | — |
| Long Corridor | F16 + loops (iso, 1 round) | offline | 6 | 1.538 ± 0.304 | 1.312–2.125 | Below Switch-SLAM 2.42; above 1.254 and 1.386 |
| Corridor02 | F0 VINS-Mono | 0.33× | 3 | 4.03 ± 0.01 | 4.02–4.03 | — |
| Corridor02 | F8 | 0.33× | 3 + 1 | 2.12 ± 0.06 | 2.07–2.19; 0.2× 2.11 | — |
| Corridor02 | F12 hard switch | 0.33× | 3 | 1.87 ± 0.27 | 1.65–2.17 | — |
| Corridor02 | F14 LiDAR translation | 0.33× | 3 | 1.74 ± 0.06 | 1.67–1.78 | Second best here |
| Corridor02 | F5 A-LOAM only | 0.33× | 3 + 1 | 66 ± 24 | 46.5–93.0; 0.2× 68.1 | — |
| Corridor02 | F8 + loops | offline | 3 | 2.10 ± 0.10 | 2.01–2.20 | No effect |
| Corridor02 | F16 | 0.33× | 6 | 1.708 ± 0.069 | 1.64–1.84 | Best here; replay predicted 1.749 |
| Corridor02 | F16 + loops (iso, 1 round) | offline | 6 | 1.250 ± 0.435 | 0.807–1.853 | Gain only in the 4 runs that accepted the long start–end loop; runs 2 and 6 unchanged |

The offline replay estimates for SAH v7 (not live) were Multi Floor 0.562 ± 0.049 (6 logs), Long Corridor 1.94 ± 0.24 (3) and Corridor02 1.75 ± 0.06 (3). The yaw oracle gave 0.39 / 1.42 / 0.90.

## Comparisons and improvements

&#91;embedded content: Live runs and offline loop closure, 13–17 Oct 2026 · published values from Switch-SLAM (RA-L 2024) and the SubT-MRS ICCV'23 challenge\]

**Gains by stage.**

- **Multi Floor.**
  - The Schur-weighted LiDAR correction removed 52% of VINS-Mono's error.
  - Loop closure removed a further 45%.
  - Overall, the error is 75% below the old switching node.
- **Long Corridor.**
  - F8 removed 22% of VINS-Mono's error.
  - SAH then removed 50% of F8's error (6 runs) and halved the maximum error (11.4–14.1 m down to 5.4–7.9 m).
  - Loop closure on F8 alone gave 41%.
- **Corridor02.** The fused variants removed 47–57% of VINS-Mono's error. Loop closure on F8 had no effect. On F16 it gave 27% (1.708 to 1.250 m), but only in the 4 of 6 runs that accepted one long start–end loop.

**Against published numbers.**

- **Multi Floor.** The front end alone is 62% below Switch-SLAM. With loop closure it is 13% below the challenge's best entry, though that entry's alignment may differ from ours. SuperLoc's 0.315 m on Floor01 (no loop closure) is below our 0.347 m with loops.
- **Long Corridor.** F16's 2.27 ± 0.45 m (6 runs) is level with Switch-SLAM (2.42). Reaching the challenge's 1.254 m needs a further 49% cut. Even a perfect heading (oracle 1.42 m) would not get there without loop closure, F16 plus the back end then gave 1.54 ± 0.30 m on 6 recordings (Phase 18). SuperLoc's 0.817 m and LODESTAR's 1.386 m are both below our numbers.

**Design questions the tests answered.**

| Question | Answer | Evidence |
| --- | --- | --- |
| Gate the LiDAR correction on κ(S\_RR)? | No | Live: F3 beat F1 in 3 / 3 runs. Replay: gate 0.751 vs 0.425 held out. |
| Soft weighting or a hard switch? | Soft, but not on every sequence | Replay 12 / 12 on Multi Floor and live on Long Corridor (4.53 vs 5.43). Hard is better on Corridor02 (1.87 vs 2.12), though this disappears with the correct heading. |
| Schur S\_tt or diagonal H\_tt? | No difference on Multi Floor | 0.425 vs 0.429 (p 0.05) |
| Take rotation from LiDAR (C\_R > 0)? | No | Multi Floor gets worse in every replay (1.07–2.05) |
| How much LiDAR weight (C\_T)? | 0.03 | Plateau from 0.03 to 0.3; spread and 1-s RPE grow with C\_T |
| Degeneracy-aware loop weights? | Not supported | Iso 0.309 vs Schur 0.605 on Multi Floor. Only the synthetic 120 m corridor favoured Schur. |
| Channel T as a second detector? | No | Failed its pre-set test (C1 / C2 below A2); adds 0.000 AUC |
| Primary sensor chosen from VIO health (Option 2)? | No | Yaw drift is invisible to VIO. A-LOAM yaw is worse on Multi Floor (1.58–1.64). |
| Heading from wall structure? | Yes on corridors so far | Replay 3 / 3 better on both corridors; live Long Corridor 4.53 → 2.44 |

## Failures, withdrawn claims and limitations

The record contains these negative results, retracted statements and run failures. Each should stay in the thesis.

**Negative results.**

| Result | Where |
| --- | --- |
| New pipeline worse under a LiDAR bias (14.4 → 42.9 cm, 0 / 5 seeds) | Phase 3 |
| New pipeline only ties the old one with healthy vision (scenario B) | Phase 3 |
| No detection rule beat always-VINS on Multi Floor; ATE tracks handover share, not detection quality | Phase 6 |
| Channel T failed its pre-set test, live and offline | Phases 4 and 6 |
| κ gate made things worse (F3 beat F1 3 / 3); the Otsu front-end claim is not supported | Phase 7 |
| Degeneracy-aware loop weights lose to isotropic on Multi Floor | Phase 9 |
| Long Corridor F8 missed the Switch-SLAM target (4.53 vs 2.42); no remedy was safe on both sequences | Phase 11 |
| On Corridor02, F14 and F12 beat F8 | Phase 12 |
| Loop closure did nothing on Corridor02 | Phase 12 |
| Option 2 (VIO-health primary selection) rejected | Phase 13 |
| SAH v3, v4 and v5 dropped. v7 fails two stress cases on Corridor02 (4.375 and 2.616) and worsens 2 of 6 Multi Floor runs. | Phase 14 |
| F16 left the Multi Floor mean unchanged live; Long Corridor run 3 is 0.5 m worse than replay | Phase 15 |

**Withdrawn or corrected claims.**

| Claim | Correction |
| --- | --- |
| "99.8% corridor detection" | Came from a simulator artefact (a fixed voxel grid with a constant 2.4 mm/frame bias) |
| Raw Hessian "about 6× overconfident in sd" | ANEES 48 implies a factor of 4.0 |
| Bingham statistic 15NΣ(λ − 1/3)² | The correct form is 15N/2 · Σ(λ − 1/3)², and it tests uniformity, not degeneracy |
| Channel T is exactly H\_tt / N on real data | Only with identical normals, weights and correspondences. On the real log the eigenvalue correlation is 0.74–0.80. |
| v1 / v2 Joint vs Decoupled results | Circular ground truth; retired |
| Scenario 2 Part B | Tested a score that is not deployed; retired |
| "The VO-fail constants are VINS-Mono's" | 20 features is VINS-Mono's keyframe rule; 1.5 m and 0.8 rad were project values |
| "Switch-SLAM's 0.103 is the 95% χ² value" | It is the lower 5% point; our own analysis, no published critique found |
| Multi Floor is "an underground mine" (review slides) | It is CMU's Hawkins building |
| Corridor02 F5 failure is "compute-starved" | Withdrawn after the 0.2× run (still 68 m) |
| Replay "fused C\_T = 0.03" rows of 0.76–0.98 | They were replayed with the gate on. Ungated replay reproduces live exactly. |
| "Long Corridor GT has no overlap" | The check used record times; on header stamps it overlaps |

**Run failures.**

- 7 Multi Floor runs fell below the 3000-row rule: F4 × 3, F5 × 3 and one F1. One F8\_kf run (2877 rows) was also short and was rerun.
- 8 Corridor02 runs at 1.0× dropped about 40% of scans and were discarded before scoring.
- Three pipeline bugs were fixed without touching the method: the topic picked in `setup_sequence.sh`, the GT clock check, and the `backend_multi.py` regex.
- The F16 batch first failed to start because the update zip was not in `~/Downloads`.

**Limitations of the evidence.**

- Multi Floor is a tuning sequence (C\_T, loop rounds and odometry noise were chosen there). Long Corridor and Corridor02 are now development data for SAH.
- Three runs per configuration gives a tie band of 0.1–0.3 m.
- The ground truth is map-aided, not independent.
- The F16 vs F8 comparison on Multi Floor mixes replay rates (0.5× vs 1.0×).
- The published numbers may use other alignment or span.
- Every synthetic magnitude (noise, bias, failure windows) is a simulation choice.

## Pending tests and next steps

The Corridor02 F16 runs are the only test currently running. Everything below follows from what the record shows is still missing.

- [x] Corridor02 F16 × 3 at 0.33× and the back end on all F16 recordings. Done 18 Oct (`for_claude10.zip`, Phase 16): Corridor02 1.695 ± 0.026 m.
- [x] Read the SAH log columns for Long Corridor run 3 and Multi Floor run 2. Long Corridor run 3: SAH normal, the A-LOAM path drifted. Multi Floor run 2: half the accepted updates (175 against 360 and 341). Phase 16.
- [x] F16 + loop closure on Long Corridor. The back end gave 1.673 ± 0.414 m, against 2.67 for F8 + loops.
- [x] Matched control: F8 × 3 on Multi Floor at 0.5×, so F16 and F8 are compared at the same replay rate. Done 19 Oct (Phase 18): F8 0.603 ± 0.112 against F16 0.640 ± 0.115, no difference.
- [x] Find why loop closure did nothing on Corridor02 run 2 (1.728 m with loops, 1.724 m without). Done 19 Oct (Phase 18): runs 2 and 6 never accepted the long start–end loop that gave the other four runs their gain; the drift distance was not the cause.
- [x] Per-time error against ground truth for Long Corridor run 3. Done 19 Oct (Phase 17): the maximum error is at the start in every run, and run 3 is worse in the first 60 s and the last third.
- [ ] Test whether the fusion should lean more on the LiDAR path in Long Corridor: the logged A-LOAM path beat the fused output in runs 1–2 (1.35 and 1.02 m). Check on a sequence not used to choose the setting.
- [ ] Untouched test sequence, never used for any decision. GEODE Stairs\_Alpha or another SubT-MRS sequence; run F0, F8 and F16 × 3 with settings frozen.
- [ ] Non-structured control, SubT-MRS Cave01–04. SAH must switch itself off (F16 = F8).
- [ ] Near-range filter for the spurious-plane failure mode (a plane carried with the robot), decided before the untouched test.
- [x] Verify SuperLoc's 0.817 m (Corridor01) against the paper before citing it. Done 19 Oct: confirmed, no loop closure; it and its 0.315 m on Floor01 are the strongest published figures.
- [ ] Live confirmation of the replay-only weight variants F11, F13 and F15, if the thesis needs them.
- [ ] Ground-truth cross-check with `compare_gt.py`: `floor01_gt.txt` against `ground_truth_path.csv`.
- [ ] Update the project docs (Structure\_Heading\_Development\_Results, Plan\_Beating\_Published\_Results) with the F16 live results.
- [ ] Run the back end on the recorded F8 runs 7–9 on Multi Floor, to get a matched F8 + loops figure at 0.5× (the keyframe files are on the laptop).
- [ ] Find why the long start–end loop (about 158↔693 s) is rejected in Corridor02 runs 2 and 6: inspect the matching score for that keyframe pair.

## Appendix: parameters, scripts and files

These are the node settings at their current defaults, with the values used in the frozen method (F8 / F16) where they differ.

| Parameter (env var) | Default | F8 / F16 value | Meaning |
| --- | --- | --- | --- |
| FUSION\_MODE | fused | fused | vins / lidar / fused |
| C\_T | 1e-3 | 3e-2 | LiDAR translation information scale in W\_t = (c·S\_tt + I)⁻¹ c·S\_tt |
| C\_R | 0 | 0 | LiDAR rotation weight (rotation always from VINS-Mono) |
| WEIGHT\_MODE | schur | schur | Ablations: diag, iso, const, proj, switch\_ss, switch\_kR, lidar, vins |
| KAPPA\_MODE / KAPPA\_TH | fixed / 15.7 | — / 1e9 (gate off) | κ(S\_RR) gate; 15.7 is the Otsu cut from the threshold study |
| W\_ALPHA | 0.7 | 0.7 | Weight smoothing |
| T\_WARM | 20 s | 20 s | LiDAR-only warm-up after VINS-Mono (re)starts |
| JUMP\_MAX | 1.0 m | 1.0 m | VINS step rejected above this (VO\_FAIL); rotation 0.5 rad |
| PREDICT\_WITH\_VINS | 1 | 1 | Seed A-LOAM with VINS-Mono motion |
| HESS\_TOPIC | /laser\_hessian | /laser\_hessian | A-LOAM Hessian export |
| SAH | 0 | 0 / 1 | Structure-anchored heading on (F16) |
| KF\_DIST / KF\_ROT | 1.0 m / 0.2 rad | same | SAH keyframe spacing |
| SAH\_RMIN / SAH\_RMAX | 1.0 / 60 m | same | Range window for SAH points |
| SAH\_VOXEL / SAH\_MAXPTS | 0.25 m / 6000 | same | Downsampling before normals |
| SAH\_MAX\_STEP | 0.25° | same | Largest heading change applied per scan |
| SAH\_SYNC | 0 | 0 | 1 = run SAH in the callback (testing only) |

These are the internal SAH v7 constants (`structure_heading.py`, StructureHeadingV6 with `bound_R=True`):

- 360 bins over 180° and a ±15° search;
- null table N = 50–3200, q99.9 = 5.17–1.37, factor 1.5;
- minimum peak 0.5, margin 0.15, 150 points;
- χ² gate 9, agreement veto 2°, drift rate 0.1°/s;
- q\_t = (0.05°)²/s, turn factor 0.02, R₀ = (3°)², R floor (0.5°)²;
- 5 initial keyframes that must agree within 3°.

These are the back-end settings, frozen from Multi Floor:

- iso loop weights, 1 search round;
- search radius 8 m, ICP acceptance at most 4 m / 15°;
- Huber + χ² pruning;
- odometry noise 1.46° / 0.054 m per step.

**Scripts and where the results live.**

| Purpose | Files |
| --- | --- |
| Live node and core | `fusion_node_v2.py`, `fusion_core.py`, `structure_heading.py`, `keyframe_recorder.py` |
| Batch drivers | `run_fusion_study.sh`, `run_sah_batch.sh`, `run_all_thresholds.sh`, `setup_sequence.sh`, `make_vins_config.py` |
| Scoring and replay | `score_run.py`, `multifloor_ate_eval.py`, `fusion_summary.py`, `offline_evidence.py`, `ablation_weights.py`, `calibrate_c.py`, `align_gt_time.py`, `check_gt.py`, `compare_gt.py` |
| Back end | `backend_icp.py`, `backend_graph.py`, `run_backend.py`, `backend_multi.py`, `backend_synth.py` |
| SAH development (sandbox) | `/home/claude/sah/`: `sheading.py`, `sah_replay.py`, `sah_stress.py`, `sah_sens.py`, `node_harness.py`, `score_harness.py` |
| Synthetic studies | `verify_final_methods.py`, `compare_old_vs_new_pipeline.py`, `threshold_screen.py`, the agents' `sim1-3.py` |
| Result folders (laptop) | `~/runs_v2` (Multi Floor), `~/runs_thr` (threshold study), `~/runs_corridor` (Long Corridor), `~/runs_corridor2` (Corridor02, including `attempt1_rate1.0`) |
| Project notes with the raw numbers | Thesis\_Methodology\_Action\_Plan, SLAM\_Degeneracy\_Final\_Methods\_With\_Proofs, Old\_vs\_New\_Comparison\_Results, Bingham\_Channel\_T\_Valid\_Tests, Multifloor\_Threshold\_Study\_Results, Plan\_Beating\_Published\_Results, Long\_Corridor\_Setup\_Log, Corridor02\_Held\_Out\_Test\_Protocol, Yaw\_Drift\_Diagnosis\_and\_Next\_Direction, Structure\_Heading\_Development\_Results |

## Sources

- [Switch-SLAM, Lee et al., RA-L 2024](https://doi.org/10.1109/LRA.2024.3421792)
- [SubT-MRS dataset paper and ICCV'23 challenge results](https://arxiv.org/html/2307.07607v5)
- [ICCV'23 sensor-fusion track](https://superodometry.com/iccv23_challenge_Mul)
- [SuperLoc, arXiv 2412.02901](https://arxiv.org/abs/2412.02901) (Table III: Corridor01 0.817 m, Floor01 0.315 m; verified 19 Oct)
- [LP-ICP, arXiv 2501.02580](https://arxiv.org/pdf/2501.02580)
- [DCReg, arXiv 2509.06285](https://arxiv.org/abs/2509.06285)
- The LODESTAR Table V and D²-LIO values come from earlier project notes; their papers were not re-opened for this report.

### Phase 2 — Final-methods verification S1–S7 (5 Oct, synthetic)

**Purpose.** To check each proposed replacement (D1–D6) against a derivation, using `verify_final_methods.py`.

**Setup.** The simulation runs real nearest-neighbour point-to-plane ICP on a 0.4 m voxel map (A-LOAM-like, 5-point plane fits), with σ\_p = 0.02 m, N = 1500 points, an initial error of 0.20 m / 1° and 12 iterations. Each scene got 200 runs × 5 seeds, and the fusion tests got 4000 runs × 5 seeds. The tolerances were τ\_t = 0.10 m and τ\_R = 1°.

| Check | Expected | Obtained |
| --- | --- | --- |
| S1 Schur block-inverse identity (5000 random H) | Exact | Max relative difference 1.16e-15 |
| S1 Channel T = H\_tt / N | Exact | max \|H\_tt − N·T\| = 0 |
| S3 λ3 of T in well-constrained scenes | Above 0.15 if the rule worked | 0.104 (corridor\_doors), 0.093 (open\_80\_10\_10), so false alarms |
| S3 Bingham uniformity statistic | Separates scenes | B = 89–3849 in every scene, N = 100–1600, against a critical value of 11.07 |
| S4 detection: proposed D1 (a)+(b) | High on corridor, 0 elsewhere | 0.998 ± 0.002 corridor; 0.000 corridor\_doors; 0.000 open |
| S4 detection: semicircle / DCReg κ > 10 / λ3 < 0.15 | — | 1.000 on all three scenes (no discrimination) |
| S4 detection: CRLB tolerance only | — | 0.000 everywhere: misses the corridor |
| S4 corridor calibration | Consistent covariance | Empirical sd 12.96 cm vs CRLB 2.08 cm; ANEES 48.25 ± 1.79 against \[2.67, 3.35\]. Constrained scenes: ANEES 4.74 / 3.76. |
| S5 fusion, translation RMSE (cm) | Projection helps | Current code 1.189; scalar conf 1.172; information-weighted without projection 3.551; BLUE + projection 0.713; CI + projection 0.713 |
| S5 consistency with correlated errors (ρ = 0.6) | CI consistent, BLUE not | BLUE ANEES 7.03 (above the 6.11 bound); CI 4.47 |
| S6 switching, a = 0.05, b = 0.90 | CUSUM faster, fewer false flags | CUSUM h = 6.00 gives ARL0 3019 frames. 5-frame buffer puts 22.0 ± 1.6% of normal frames in TRANSITION; CUSUM 0.06%. Delay 5.99 vs 2.27 frames. |
| S7 Wilson 95% half-widths | Sample size for later | n = 400: ±0.049; n = 1068: ±0.030; n = 3000: ±0.018 (at p = 0.5) |

**Conclusion.** The derivations hold in simulation. The raw Hessian is badly overconfident in a corridor, because noise-fitted normals manufacture information. The report's "about 6× in standard deviation" was corrected in Phase 4 to a factor of 4.0 for ANEES 48.

### Phase 3 — Old vs new pipeline, factorial comparison (5 Oct, synthetic)

**Purpose.** To measure each change separately: detector, switching and fusion, in a 2×2×2 design.

**Setup.** A 30 m drive of 300 frames at 10 Hz: open area, then a 100-frame corridor (degenerate along x), then a corridor with doorways. Every pipeline saw identical sensor data, over 5 seeds. The new detector was calibrated on held-out maps at the 99th percentile (×3.29); a 95th-percentile variant (×2.48) was run for sensitivity. Scripts: `compare_old_vs_new_pipeline.py`.

| Scenario (ATE cm, mean ± sd of 5 seeds) | Old | Old + new fusion | New | New better in |
| --- | --- | --- | --- | --- |
| A. Vision fails on 40 of 300 frames | 280.0 ± 7.0 | 15.9 ± 3.3 | 14.4 ± 5.1 | 5/5 |
| B. Vision healthy | 14.5 ± 4.5 | 15.2 ± 5.7 | 16.3 ± 6.2 | 2/5 (tie) |
| C. B + 5% random false flags | 14.5 ± 4.5 | 15.2 ± 5.7 | 16.3 ± 6.2 | 2/5 (identical to B) |
| D. LiDAR 2 mm/frame z bias | 14.4 ± 5.2 | 42.3 ± 2.8 | 42.9 ± 0.8 | 0/5 (worse) |
| E. Vision 2% scale bias | 32.7 ± 8.2 | 24.9 ± 9.8 | 17.4 ± 10.1 | 4/5 |

Component results:

- **Detector.** The old detector flagged 100% of frames everywhere. The new one flagged 0% of well-constrained frames and 96% of corridor frames. Uncalibrated, it missed 36.5% of degenerate frames (nominal 5%). At the 95th percentile, corridor detection was 87%, and scenario B became worse than old (25.2 vs 14.5 cm).
- **Open-area per-frame error.** It fell from 9.2 to 5.2 mm with the new fusion.
- **CUSUM with the old fusion (scenario C).** Mode switches fell from 27.4 to 2.0 and false-degenerate frames from 29.2% to 1.1%. ATE fell from 35.4 to 19.7 cm. With the new fusion, ATE was unchanged (15.8 vs 16.3 cm) and switches fell 14×.

**Expected vs obtained.** The large gain in A was expected and found. Most of it comes from one old branch that zeroed real motion: −200 cm in the corridor, exactly 20 frames × 10 cm. B is a tie, not a gain. D is a real loss, because information weighting inherits an unmodelled LiDAR bias.

**Conclusion.** Adopt information-weighted fusion; adopt the detector only with held-out calibration; keep CUSUM for stability only. Do not claim robustness gains with healthy vision. The 99th percentile was chosen after seeing the 95th, so it is labelled post hoc.

### Phase 4 — Channel T and Bingham statistics checks (6 Oct)

**Purpose.** To decide whether Channel T (the orientation tensor of scan normals) can be tested properly, and to verify the research report's statistical claims.

**Setup.** The research agents ran their own synthetic simulations. The coordinator then checked the claims on the real Multi Floor log `switching_log_multifloor_modified_manual_groundfix.csv` (3932 frames at about 10 Hz) and in an independent simulation.

| Check | Expected | Obtained |
| --- | --- | --- |
| Bingham B = 7.5 N Σ(lᵢ − 1/3)² at N = 1000 | Rejects every real scene | diag(0.5, 0.3, 0.2): 350; corridor-like diag(0.02, 0.49, 0.49): 1104; diag(0, 0.5, 0.5): 1250. All far above 11.07. |
| Coverage of a nominal 95% lower bound on λ\_min (K patches of 100 points, 1500 reps) | Naive N anti-conservative | Naive: 0.73 / 0.62 / 0.55 / 0.46. Cluster-robust: 0.99 / 0.99 / 0.98 / 0.95 (K = 10 / 30 / 100 / 300). |
| Agents' simulation of the same (3000 reps) | — | Naive 0.68–0.87; cluster-robust 0.967–0.994 |
| Lag-1 autocorrelation of log l1 on the real log | High | 0.938 (lags 2 / 5 / 10 / 20: 0.93 / 0.88 / 0.82 / 0.71); effective n about 125 of 3932 |
| CUSUM ARL0 under AR(1) input (agents' simulation, 400 runs) | Falls with autocorrelation | 996 (φ = 0), 109 (φ = 0.5), 67 (φ = 0.8), 913 after pre-whitening |
| Noise floor of l1 in a simulated VLP-16 corridor | Above zero | Noisy l1 ≈ 0.019 vs noise-free 0.004–0.009. The physically meaningful threshold is about 5.7e-6. |
| ANEES 48.25 against an expected 3 | — | Covariance factor 16.1, sd factor 4.0. The earlier "6×" needs ANEES ≈ 108, so it is withdrawn. |
| McNemar sample size, 75:25 discordant split | — | 28.9, so about 29 discordant segments |

From the user's own analysis of the real log (not reproduced here), the normalised H\_tt eigenvalues correlate only 0.74–0.80 with T's eigenvalues. Their smallest-eigenvalue medians are 0.134 versus 0.056 for T.

**Conclusion.** The Bingham test asks the wrong question (uniformity). A valid Channel T would need a cluster-robust lower bound on λ\_min, a noise-floor null and a CUSUM calibrated under autocorrelation. Channel T was then tested live in Phase 6.

### Phase 5 — Old node reference on Multi Floor (before 13 Oct)

**Purpose.** To get the real-data starting point for the old switching node.

**Setup.** Multi Floor, 3 bags, 1.0×, the old node with its old rule, 3 runs. Same Docker stack as all later runs.

| Configuration | Runs | ATE RMSE (m) | Max (m) |
| --- | --- | --- | --- |
| Old node, old rule | 3 | 1.39 ± 0.14 | 4.58 ± 0.12 |
| VINS-Mono alone (reference) | — | 1.32 (range 1.02–1.34 across logs) | — |

**Diagnosis from the logs.** The old node was no better than VINS-Mono alone, for three reasons:

1. LIDAR\_ONLY used scan-to-scan odometry (17.6 m alone) instead of scan-to-map (3–4 m).
2. The VINS world frame and the A-LOAM frame were mixed without a rotation; they are 8–62° apart.
3. The maximum error is VINS-Mono's start-up transient: the robot covers about 21 m in the first 20 s.

**Conclusion.** The fixes became fusion\_node\_v2: frame-consistent fusion, a scan-to-map LiDAR source and a LiDAR WARMUP before VINS-Mono starts.

### Phase 6 — Degeneracy threshold study, 15 rules live (12–13 Oct)

**Purpose.** To rank published and project detection rules on real data with labels the detectors cannot see. Channel T had to pass a pre-set test: it must add at least 0.05 to J.

**Setup.** The old switching node ran with the rule swapped per run, on Multi Floor at 1.0×, one run per rule (3870–3933 log rows each; about 2 h in total). The driver was `run_all_thresholds.sh`. Labels were A-LOAM drift terciles in 8 s windows on held-out bags 1–2, scored by J = TPR − FPR. An offline screen (`threshold_screen.py`) predicted every rule's rates beforehand.

| Run | Rule | ATE (m) | Flagged | TPR | FPR | J | Predicted J |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Switch-SLAM semicircle | 3.05 | 0.891 | 0.907 | 0.884 | 0.023 | 0.02 |
| A2 | κ(S) > 10 (DCReg) | 12.49 | 0.551 | 0.742 | 0.495 | 0.247 | 0.25 |
| A3 | κ(S) > 50 | 15.98 | 0.029 | 0.061 | 0.019 | 0.042 | 0.05 |
| A4 | diagonal κ > 10 | 13.70 | 0.559 | 0.734 | 0.479 | 0.255 | 0.25 |
| A5 | λ\_min(S) < 100 | 10.88 | 0.741 | 0.969 | 0.803 | 0.166 | 0.17 |
| A6 | never flag | 17.67 | 0.000 | 0.000 | 0.000 | 0.000 | 0.00 |
| A7 | κ(H) > 10 | 1.38 | 0.979 | 0.970 | 0.992 | −0.022 | −0.01 |
| A8 | κ(S\_RR) > 15.7 (Otsu) | 16.27 | 0.334 | 0.584 | 0.105 | **0.479** | 0.49 |
| B1 | λ\_min(T) < 0.15 (old Channel T) | 7.50 | 0.838 | 0.973 | 0.858 | 0.115 | 0.12 |
| B2 | κ(T) > 10 | 14.66 | 0.575 | 0.717 | 0.562 | 0.155 | 0.15 |
| B3 | λ\_min(T) ≤ 0.045 | 16.12 | 0.245 | 0.293 | 0.307 | −0.014 | −0.01 |
| B4 | Woodcock K < 1 | 3.26 | 0.823 | 0.803 | 0.885 | −0.082 | 0.06 |
| B5 | Demantke class | 11.97 | 0.725 | 0.894 | 0.630 | 0.264 | 0.17 |
| C1 | A2 or B3 | 10.80 | 0.658 | 0.751 | 0.599 | 0.152 | 0.16 |
| C2 | A2 or B2 | 8.39 | 0.739 | 0.847 | 0.735 | 0.112 | 0.10 |

The reference was the old rule over 3 runs: 1.39 ± 0.14 m, J = −0.01.

**Expected vs obtained.**

- The offline predictions held: J was within 0.05 for 13 of 15 rules. B4 and B5 missed, for reasons not yet found.
- Best detector: A8, the rotation Schur block with an Otsu threshold (J 0.479, precision 0.817).
- Channel T failed its pre-set test. Adding it to Schur lowered J (C1 0.152 and C2 0.112, against A2 0.247).
- An offline incremental test added 17 log features to Schur κ (leave-one-block-out). None added meaningful AUC (best +0.016), and T added 0.000. The only lead was the VINS/LiDAR speed ratio (ρ = +0.39, p = 0.009), which does not survive Bonferroni correction.

**Conclusion.** ATE follows how often control passes to VINS-Mono (Spearman −0.95), not detection quality. No rule beat always-VINS (1.32 m). Switching-based evaluation cannot rank detectors when VIO is strong, and that finding motivated the soft-weighting design.

### Phase 7 — fusion\_node\_v2: offline evidence, calibration and first live batch (13–14 Oct)

**Purpose.** To test the new VIO-primary, gated, Schur-weighted correction against pass criteria fixed in advance.

**Offline evidence first.** These are open-loop replays of two old Multi Floor logs, positions only, with the scan-to-scan Hessian. Values are ATE RMSE / max in m.

| Variant | Run A bags 1–2 | Run B bags 1–2 | Run A full | Run B full |
| --- | --- | --- | --- | --- |
| VINS-Mono alone | 0.769 / 1.72 | 0.790 / 1.89 | 1.340 / 4.90 | 1.023 / 3.35 |
| + LiDAR warm-up | 0.769 / 1.72 | 0.790 / 1.89 | 1.264 / 4.08 | 0.953 / 2.45 |
| + gated Schur weights, C\_T = 1e-3 | 0.652 / 1.43 | 0.729 / 1.47 | 1.219 / 4.13 | 0.808 / 1.85 |

The alignment window (0–90 s) moved the full-span max by 1.6–5.3 m, but RMSE stayed at 0.77–1.35 m.

**Calibration.** `calibrate_c.py` ran on bag 0 of the first F0 log, minimising 1-s RPE. It chose C\_T = 0.003, on a flat curve: RPE 0.110 at C\_T = 0 and 0.097 at 0.003.

**Live batch.** F0–F5 × 3, Multi Floor at 1.0×, 13 Oct 23:50 to 14 Oct 02:22, about 7.7 min per run.

| Config | Run 1 | Run 2 | Run 3 | Mean RMSE / max | Bags 1–2 (held out) | Rows |
| --- | --- | --- | --- | --- | --- | --- |
| F0 VINS-Mono in node | 1.29 / 2.51 | 1.29 / 2.54 | 1.25 / 2.35 | 1.275 / 2.47 | 0.751 | 3182–3305 |
| F1 gated, κ ≤ 15.7 | 1.06 / 2.12 | 1.00 / 1.99 | 1.09 / 2.17 | 1.050 / 2.09 | 0.735 | 3282–3382 |
| F2 gated, online Otsu | 0.99 / 1.95 | 1.12 / 2.19 | 1.03 / 2.06 | 1.046 / 2.07 | 0.701 | 3337–3368 |
| F3 no gate | 0.94 / 1.87 | 0.93 / 1.89 | 1.02 / 1.98 | 0.960 / 1.91 | 0.545 | 3324–3351 |
| F4 LiDAR only, VINS-seeded | 9.56 / 15.35 | 24.66 / 36.70 | 42.93 / 62.04 | 25.7 | 2.8–6.9 | 2778–2951 (failed row rule) |
| F5 A-LOAM only | 30.69 / 58.50 | 13.20 / 25.44 | 35.43 / 64.21 | 26.4 | 8.9–11.1 | 2766–2846 (failed row rule) |

One extra F1 run (2727 rows) failed the row rule and was repeated.

**Expected vs obtained (pass criteria set in advance).**

1. F1 and F2 below Switch-SLAM's 1.61 / 3.63: **PASS**.
2. F1 beats its own VINS replay on bags 1–2 in at least 2 of 3 runs: **PASS, but small** (gain 0.03–0.05 m on held-out bags, 0.22–0.27 m on the full span).
3. F3 (no gate) worse than F1: **FAILED**. F3 was better in 3 of 3 runs (held out 0.534 / 0.535 / 0.567 vs 0.758 / 0.693 / 0.753).

Paired replays on the F3 logs agreed (gate on 1.081 / 1.024 / 1.132 vs live ungated 0.936 / 0.927 / 1.018).

**Follow-up replays.**

- LiDAR rotation weight C\_R from 1e-3 to 1e-2 worsened the full span to 1.46–2.4 m. C\_R stays 0, and F6 was dropped.
- Re-calibration without the gate on bag 0: the 1-s RPE horizon picks C\_T = 0.003, and the 5-s horizon picks 0.01. Replay at 0.01 gave 0.798 / 0.761 full span; at 0.03 it gave 0.723 / 0.675.
- The replay of C\_T = 0.003 ungated predicted 0.97 m; live F3 gave 0.960.

**Conclusion.** The κ gate costs accuracy. The Schur information weight alone does the work, so the gate was dropped. The claim that an Otsu threshold helps as a front-end gate is not supported.

### Phase 8 — C\_T sweep without the gate, and F8 repeats (14 Oct)

**Purpose.** To find how much LiDAR translation weight helps once the gate is gone, and to record keyframes for the back end.

**Setup.** Multi Floor, 1.0×, no gate, rotation from VINS-Mono. RECORD\_KF=1 runs also saved keyframe scans (`keyframes_*.npz`, about 505 keyframes and a median of 1766 points each). The runs went in four blocks on 14 Oct, finishing at about 10:42, 11:56, 13:47 and 21:13. There were 21 runs, one of which (2877 rows) failed the row rule.

| Config (C\_T) | Run values, ATE RMSE / max (m) |
| --- | --- |
| F7 (0.01) | kf\_run1 0.85 / 1.66; run1 0.91 / 1.82; run2 0.89 / 1.83; run3 0.88 / 1.79 |
| F8 (0.03) | run1 0.74 / 1.65; run2 0.51 / 1.24; run3 0.54 / 1.20; kf\_run1 0.77 / 1.62; kf\_run2 0.73 / 1.61 (rerun; the first try had 2877 rows); kf\_run3 0.62 / 1.24; kf\_run4 0.58 / 1.24; kf\_run5 0.59 / 1.24; kf\_run6 0.47 / 1.04 |
| F9 (0.1) | kf\_run1 0.51 / 1.24; kf\_run2 0.85 / 1.66; kf\_run3 0.94 / 1.84 |
| F10 (0.3) | run1 0.77 / 1.44; run2 0.59 / 1.25; run3 0.70 / 1.67 |
| F4 recording (LiDAR only) | kf\_run1 7.75 / 14.23 (2845 rows, below the row rule) |

The sweep summary below includes F0 and F3 from Phase 7 as the C\_T = 0 and 0.003 points.

| C\_T | Runs | Full RMSE (m) | Max (m) | Bags 1–2 (m) | 1-s RPE (m) |
| --- | --- | --- | --- | --- | --- |
| 0 (F0) | 3 | 1.28 ± 0.02 | 2.47 | 0.75 | 0.067 |
| 0.003 (F3) | 3 | 0.96 ± 0.05 | 1.91 | 0.55 | 0.065 |
| 0.01 (F7) | 3 | 0.89 ± 0.01 | 1.81 | 0.45 | 0.081 |
| 0.03 (F8) | 6 | 0.65 ± 0.11 | 1.43 | 0.38 | 0.096 |
| 0.1 (F9) | 3 | 0.77 ± 0.23 | 1.58 | 0.45 | 0.111 |
| 0.3 (F10) | 3 | 0.68 ± 0.09 | 1.45 | 0.46 | 0.114 |

All nine F8 live runs together give **0.617 ± 0.107 m**. The six recorded F8 runs give 0.626 ± 0.107 m.

**Expected vs obtained.** The replay at C\_T = 0.01 predicted 0.76–0.80 m, and live F7 gave 0.85–0.91. The gain grows up to C\_T = 0.03 and then plateaus: 0.03, 0.1 and 0.3 cannot be separated. Run-to-run spread and 1-s RPE both grow with C\_T, so more LiDAR weight inherits more of A-LOAM's failure modes.

**Conclusion.** C\_T = 0.03 was fixed for every later sequence. It was picked from the full-span sweep on this sequence (post hoc), so Multi Floor is a tuning sequence.

### Phase 9 — Loop-closure back end on Multi Floor (14 Oct)

**Purpose.** To test whether LiDAR loop closure on the recorded keyframes removes the remaining drift, and whether degeneracy-aware loop weights beat the standard isotropic (LIO-SAM style) weight.

**Setup.** The back end runs offline on the recorded keyframes: coarse-to-fine point-to-plane ICP verification, a GTSAM pose graph, and Huber + χ² pruning. Odometry noise was calibrated on bag 0 with GT (1.45–1.46°, 0.046–0.054 m per step), and loop search uses no GT.

**Synthetic code check first.** This was a room plus a corridor, driven out and back. Values are ATE RMSE in m.

| Scenario | none | iso | hessian | schur | schur\_otsu | schur\_gate |
| --- | --- | --- | --- | --- | --- | --- |
| 50 m corridor | 0.623 | 0.031 | 0.035 | 0.031 | 0.035 | 0.036 |
| 120 m corridor | 1.582 | 0.677 | 0.689 | 0.042 | 0.039 | 0.047 |

The Cauchy kernel discarded true loops far from the drifted estimate. Huber + χ² pruning fixed that.

**Loop-weight ablation on F7\_kf\_run1** (505 keyframes, 2 search rounds). Values are full-span RMSE / max in m.

| Loop information | Loops | Full | Bag 0 | Bags 1–2 |
| --- | --- | --- | --- | --- |
| none (front end) | 0 | 0.854 / 1.66 | 0.303 | 0.441 |
| iso, scale 1 (set before seeing data) | 139 | **0.309 / 0.64** | 0.297 | 0.309 |
| hessian (inflate 10) | 137 | 0.599 / 1.43 | 0.649 | 0.545 |
| schur / schur\_otsu | 137 | 0.605 / 1.44; 0.603 / 1.44 | 0.657; 0.655 | 0.548; 0.547 |
| schur\_gate | 110 | 0.509 / 1.31 | 0.572 | 0.441 |

**Sweeps and checks on the same recording.**

- Iso scale 0.03 / 0.1 / 0.3 / 1 / 3 / 10 gave 0.355 / 0.401 / 0.287 / 0.309 / 0.376 / 1.017.
- Re-optimising a fixed loop set gave 0.298–0.517.
- Hessian inflate 100 / 1000 gave 0.460 / 0.359, never better than iso.
- Blocked 6-fold loop cross-validation (label-free) picked scale 0.1, giving 0.296 against a best of 0.291.
- A VINS-only front end with loops got worse, from 1.235 to 1.382 m.
- A wider search (radius 12 m, gap 15 s) found 156 loops and gave 0.321, so there was no gain.

**Six recordings, 2 rounds vs 1 round** (F8 × 3 at C\_T 0.03 and F9 × 3 at 0.1, iso):

| Recording | Front end | 2 rounds | 1 round |
| --- | --- | --- | --- |
| F8\_kf\_run1 | 0.766 / 1.62 | 0.417 / 0.80 | 0.395 / 0.73 |
| F8\_kf\_run2 | 0.731 / 1.61 | 0.300 / 0.72 | 0.306 / 0.73 |
| F8\_kf\_run3 | 0.619 / 1.24 | 0.846 / 2.56 (worse) | 0.356 / 0.87 |
| F9\_kf\_run1 | 0.512 / 1.24 | 0.271 / 0.56 | 0.272 / 0.56 |
| F9\_kf\_run2 | 0.851 / 1.66 | 0.477 / 0.98 | 0.470 / 0.99 |
| F9\_kf\_run3 | 0.944 / 1.84 | 0.321 / 0.61 | 0.327 / 0.62 |
| Mean ± sd | 0.737 ± 0.156 | 0.439 ± 0.214 (5 of 6 improve) | 0.354 ± 0.071 (6 of 6) |

Of 519 first-round loops, 515 were correct (median error 0.14 m). The 4 false loops were about 3.3 m off and did not change the ATE.

**Fresh recordings at frozen settings** (F8\_kf\_run4–6, iso, 1 round):

- run4: 0.576 → 0.360 m (142 loops)
- run5: 0.587 → 0.363 m (130 loops)
- run6: 0.475 → 0.303 m (139 loops)

All six F8 recordings: front end 0.626 ± 0.107, with loops **0.347 ± 0.036 m** (Wilcoxon p = 0.031).

The LiDAR-only recording F4\_kf\_run1 got worse with loops, from 7.752 to 8.181 m.

**Expected vs obtained.** Schur loop weighting was expected to beat iso. It did in the synthetic 120 m corridor (0.042 vs 0.677), but not on Multi Floor, where only 0–2 of 137 loops had a degenerate translation direction. Loop closure itself gave a 45% gain, and all six recordings fell below the challenge's best value of 0.401 m.

**Conclusion.** Loop closure works only on top of the LiDAR-corrected VIO front end. The degeneracy-aware loop weighting is not supported on Multi Floor. One search round was chosen post hoc.

### Phase 10 — Translation-weighting ablation, paired replay (14 Oct)

**Purpose.** To ask whether soft Schur weighting itself matters, compared with simpler or harder rules, on identical data.

**Setup.** Replay of the same logged scan-to-map poses and Hessians from 12 Multi Floor logs. Only the translation-weight rule changes; C\_T = 0.03 and rotation comes from VIO. The script is `ablation_weights.py`. Values are held-out (bags 1–2) ATE RMSE, mean of 12 logs.

| Rule | Held-out ATE (m) | Ours better in | Note |
| --- | --- | --- | --- |
| Ours: Schur S\_tt, soft, no gate | **0.425** | — | — |
| Diagonal block H\_tt | 0.429 | 8 / 12 (p 0.05) | No real difference on Multi Floor |
| Isotropic, same mean information | 0.457 | 11–12 / 12 | — |
| Constant weight | 0.456 | 11–12 / 12 | — |
| Per-direction 0/1 | 0.499 | 12 / 12 | — |
| Hard switch, Switch-SLAM rule | 0.501 | 12 / 12 (p 0.0005) | 1-s RPE 0.095 vs 0.110 |
| Always LiDAR translation (W = I) | 0.495 | 12 / 12 | — |
| κ(S\_RR) gate | 0.751 | 12 / 12 | — |
| κ(S\_RR) switch | 0.788 | 12 / 12 | — |

On the full span, soft and hard weighting tie at about 0.69. Detector rates over the 12 logs were:

- κ(S\_RR) > 15.7 in 37% of frames;
- κ(S\_tt) > 10 in 0.2%;
- the Switch-SLAM rule in 1.3–1.6%.

**Conclusion.** Soft beats hard on held-out data, and rotation-triggered whole-pose decisions are harmful. On Multi Floor, Schur and diagonal weighting do not differ because translation coupling is weak. Live configs F11–F15 were added to confirm this live; only F12 and F14 have been run so far.

### Phase 11 — Long Corridor: setup, live runs, back end and diagnosis (15 Oct)

**Purpose.** To give F8 a fresh test with every setting frozen from Multi Floor: C\_T = 0.03, 1 loop round, odometry noise 1.46° / 0.054 m, VINS config generated without tuning.

**Setup.** Bag `raw_data_core_2023-07-25-03-01-44.bag` (6.1 GB, 279 s, 65,454 messages), replayed at 1.0×, about 5.4 min per run (11:01–12:17). The 15 runs logged 2758–2774 rows each.

Two bugs were found on first use and fixed without touching the method:

1. `setup_sequence.sh` picked the message type instead of the topic name.
2. The GT check compared against record times instead of header stamps.

A 70 s smoke test of F8 (693 rows; FUSED from 21.4 s) scored 1.07 / 1.70 m on its first 140 m.

| Config | Run 1 | Run 2 | Run 3 | Mean ± sd (m) | Max range (m) |
| --- | --- | --- | --- | --- | --- |
| F8 ours | 4.76 | 4.87 | 3.97 | 4.53 ± 0.49 | 11.4–14.1 |
| F12 hard switch | 6.05 | 4.65 | 5.58 | 5.43 ± 0.71 | 12.2–14.8 |
| F0 VINS-Mono alone | 5.66 | 6.13 | 5.65 | 5.81 ± 0.28 | 15.2–16.2 |
| F14 LiDAR translation always | 9.97 | 23.11 | 6.56 | 13.2 ± 8.7 | 16.8–70.2 |
| F5 A-LOAM alone | 23.01 | 13.21 | 11.21 | 15.8 ± 6.3 | 21.2–56.0 |

**With loop closure** (F8 recordings, frozen back end): 4.76 → 2.91, 4.87 → 3.26, 3.97 → 1.85. The mean fell from 4.53 to **2.67 ± 0.73 m**, with all three improving and maxima of 6.0–10.5 m. All 52–57 loops joined the same place (about 120 s ↔ 155 s). The start–end loop, more than 20 m apart in the estimate, was never considered (search radius 8 m; ICP accepts at most 4 m / 15°).

**Expected vs obtained.** The target was below Switch-SLAM's 2.42 / 5.09 m. **Not met:** the front end gave 4.53 and with loops 2.67.

**Diagnosis from the logs (no GT needed).**

- The route is a loop, with a true start–end distance of 3.3 m. VINS-Mono ends 24–26 m from its start, and F8 ends 21–25 m away. The logged A-LOAM map pose ends only 2.8–4.1 m away.
- The fused path length (597–599 m) matches A-LOAM's (602–605 m), so translation comes from LiDAR and the error comes from VINS-Mono heading. The VINS-vs-LiDAR rotation grows steadily to about 10° by 250 s.
- Replaying the logged A-LOAM pose as a LiDAR-only trajectory gave 2.61 / 1.04 / 1.09 m on the F8 logs and 1.40 / 0.68 / 2.12 m on the F0 logs.

**Remedy replays.** Each remedy was tried on 6 Multi Floor logs with GT and 6 corridor logs, scored for the corridor by the loop gap (true 3.3 m).

| Remedy | Multi Floor ATE (m) | Corridor loop gap (m) |
| --- | --- | --- |
| None (F8) | 0.626 | 23.7 |
| LiDAR rotation weight C\_R = 1e-3 / 1e-2 / 1e-1 | 1.07 / 1.60 / 1.93 | 13.8 / 9.1 / 8.3 |
| Rotation fully from LiDAR | 2.05 | 5.4 |
| Slow drift filter, all axes, τ = 300 s | 0.81 | 14.6 |
| Same, yaw only | 0.71 | 15.0 |
| Yaw only, clipped innovations | 0.625–0.686 | 21–23 |

**Conclusion.** Soft weighting beats the hard switch and always-LiDAR, and is far more stable (sd 0.49 vs 8.7). However, the VIO-primary design inherits VINS-Mono's heading drift on this 580 m low-parallax corridor. No remedy was safe on both sequences, and Long Corridor became a development sequence.

### Phase 12 — Corridor02 held-out test (15–17 Oct)

**Purpose.** A held-out test of the frozen method on a second, longer corridor that had never been used. The protocol (`claude/Corridor02_Held_Out_Test_Protocol.md`) was written before any scored run.

**Setup.** `corridor02.bag`, 893 s, `/velodyne_points`. The platform is still for about 70 s; VINS-Mono initialises at 75.9 s, with the first FUSED row at 96 s. A 190 s smoke test came first.

- **Attempt 1, 1.0×:** 8 runs with 4628–5554 rows (about 40% of scans dropped by the laptop). All 8 were discarded before scoring. The replay rate was then chosen from row rates alone, before any error was seen.
- **Scored batch, 0.33×:** 15 runs, 16 Oct 21:03 to 17 Oct 08:33, about 46 min each, 8191–8282 rows. F5 had 6763–7592 rows.

| Config | Run 1 | Run 2 | Run 3 | Mean ± sd (m) | Max range (m) |
| --- | --- | --- | --- | --- | --- |
| F14 LiDAR translation always | 1.67 | 1.76 | 1.78 | 1.74 ± 0.06 | 2.81–3.18 |
| F12 hard switch | 2.17 | 1.65 | 1.80 | 1.87 ± 0.27 | 2.93–3.78 |
| F8 ours | 2.07 | 2.10 | 2.19 | 2.12 ± 0.06 | 3.69–3.88 |
| F0 VINS-Mono alone | 4.03 | 4.02 | 4.03 | 4.03 ± 0.01 | 6.73–6.76 |
| F5 A-LOAM alone | 58.57 | 46.53 | 92.95 | 66 ± 24 | 79.3–134.5 |

**Expected vs obtained.** All fused variants roughly halved VINS-Mono's error, as expected. Contrary to the hope, F14 beat F8 by about 0.4 m, more than the tie allowance; on Long Corridor the order was the reverse.

Offline replays on the same logs showed the hard switch at 1.75–1.95 m on every log, against 2.07–2.19 for the soft weight. The gap is therefore systematic, not run noise.

**Log analysis** (start–end gap, true 2.77 m):

- VINS-Mono 13.0–13.1 m; F8 4.54–5.04; F12 2.70–4.46; F14 3.27–3.50.
- There is no large heading drift here, unlike Long Corridor.
- F8's LiDAR weight eigenvalues had medians of 0.74 / 0.81 / 0.91, so 9–26% of each step still came from VINS-Mono.
- VINS-Mono is best locally: 1-s RPE 0.107, against 0.171 for LiDAR and 0.140 for F8.

**Loop closure** (F8, frozen back end):

| Run | Front end | After loops | Loops accepted |
| --- | --- | --- | --- |
| run1 | 2.067 / 3.69 | 2.009 / 3.48 | 17 |
| run2 | 2.099 / 3.72 | 2.085 / 3.57 | 21 |
| run3 | 2.192 / 3.88 | 2.198 / 3.90 | 13 |

The mean went from 2.119 to 2.097 m, so there is no measurable effect. The listed loops match the stationary start or local revisits. A regex bug in `backend_multi.py` ("nan" columns) was fixed along the way.

**Replay-rate sensitivity at 0.2×** (run 4 of each, about 75–80 min each):

| Config | Rows | ATE / max (m) | Earlier at 0.33× |
| --- | --- | --- | --- |
| F8 | 8858 (≈ complete) | 2.11 / 4.00 | 2.07–2.19 |
| F5 | 8175 | 68.14 / 105.51 | 46.5–93.0 |

**Conclusion.**

- Missing scans at 0.33× did not change F8, so the comparison holds.
- "F5 is compute-starved" is withdrawn: with more compute it still fails.
- No fixed translation rule wins on both corridors. F8 is the only fused variant that is never the worst.
- No constant was retuned on this sequence.

### Phase 13 — Yaw-drift diagnosis, oracle tests and Option 2 (17 Oct)

**Purpose.** To find where the remaining error comes from on all three sequences once both corridor GT files were available, and to test the proposed "Option 2" (choose the primary sensor from VIO health).

**Setup.** The data were the logged runs: Multi Floor F8\_kf\_run1–6, and Long Corridor and Corridor02 F8\_kf\_run1–3 plus F14. The replays reused the logged scan-to-map poses (open loop). The clock check correlated GT rotation speed with VINS-Mono and A-LOAM (r = 0.98–0.99).

**Clock.** The residual offsets were +0.03 s (Corridor02) and +0.04 s (Long Corridor), so no shift was needed.

**Rotation error of each source** (F8 run 1; degrees at 25 / 50 / 75 / 100% of the run):

| Sequence | VINS-Mono yaw drift | A-LOAM map-pose yaw error | A-LOAM tilt error |
| --- | --- | --- | --- |
| Multi Floor | 5.8 / 4.4 / 3.9 / 6.3 | 12.3 / 12.9 / 4.1 / −15.2 (jumps of 10–27° at stairs) | up to 23 |
| Long Corridor | −4.5 / −7.2 / −6.7 / −9.0 | −9.7 / −5.0 / −5.0 / 1.2 | — |
| Corridor02 | −7.1 / −7.4 / −6.8 / −8.1 | −2.0 / −2.3 / −0.4 / −0.1 | roll up to −14 |

VINS-Mono roll and pitch stay within 1–3°, so its error is almost pure yaw.

**Oracle tests** (mean ATE in m; logs per sequence 6 / 3 / 3):

| Variant | Multi Floor | Long Corridor | Corridor02 |
| --- | --- | --- | --- |
| F8 replay as run | 0.63 | 4.51 | 2.17 |
| F8 + GT yaw at every scan | 0.39 | 1.42 | 0.90 |
| F8 + GT yaw with 2° noise, gain 0.02 | 0.43 | 1.45 | 0.82 |
| F8 + GT yaw every 10 s, 1° noise | 0.70 | 1.88 | 1.15 |

With the yaw fixed, the translation weights rank consistently (MF / LC / C02, m):

- c = 0.03 (ours): 0.39 / 1.42 / 0.90
- W = I (F14): 0.48 / 1.05 / 1.89
- c = 0.01: 0.37 / 1.97 / 1.10
- c = 0.1: 0.45 / 1.10 / 1.47
- VINS-Mono translation only: 0.88 / 3.02 / 3.85

The Corridor02 result "F14 beats F8" disappears once the heading is right.

**Option 2 test.** Yaw was taken from the A-LOAM map pose (gain 0.01 to 1):

- Multi Floor: 0.63 → 1.58–1.64 m
- Long Corridor: 4.51 → 1.96–2.28 m
- Corridor02: 2.17 → 2.63–3.28 m

Rate gating at 1–2° per 10 s did not fix it.

**First structural-heading prototype** (Manhattan, circular mean of 4θ, Multi Floor F8\_kf\_run1, 504 keyframes): deviation from the building axis had a median of 1.6°, p90 3.7° and p99 6.1°. Replay improved Multi Floor from 0.626 to 0.507–0.526 m.

**Conclusion.**

- VINS-Mono yaw drift is the dominant error on every sequence.
- VIO health cannot see it, and the LiDAR map is not a reliable heading source, so Option 2 was rejected.
- Walls give a non-drifting heading. The idea itself is published (StructVIO, Li et al. 2020, Kim/Li/Joo 2022, Doer & Trommer 2021, Remote Sensing 2023); the novelty lies in the observability-matched combination.

### Phase 14 — Structure-anchored heading (SAH) development (17 Oct)

**Purpose.** To build a heading correction that works on any scene and switches itself off where there is no structure, without fitting it to these bags. This was the user's requirement.

**Design (v7, frozen).** At each keyframe, SAH builds an axial histogram (0.5° bins over 180°) of the horizontal directions of near-vertical planar points, levelled with the VIO gravity direction. It learns a world-frame reference of wall directions and measures the heading error by circular correlation within ±15°. A 1-D Kalman filter then applies the correction.

- **Gates:**
  - a null-model structure test (peak/mean at least 1.5× the 99.9% Monte Carlo quantile for random directions);
  - a unique peak (correlation ≥ 0.5, margin ≥ 0.15);
  - a 2° per-direction agreement veto;
  - χ² gate 9;
  - a drift gate of 3σ + 0.1°/s.
- **Process noise** is physical: (0.05°)²/s plus 2% of the angle turned.
- **Measurement noise** R is estimated online, with no per-dataset noise setting.

**Setup.** Replays of the 12 logged F8 runs with their keyframes (Multi Floor 6, Long Corridor 3, Corridor02 3). Each version was frozen before it ran on the corridors and was always run on all three sequences plus the stress cases. Code: `/home/claude/sah/`.

| Version | Idea | MF | LC | C02 | Verdict |
| --- | --- | --- | --- | --- | --- |
| F8 baseline | — | 0.626 | 4.515 | 2.168 | — |
| Tuned prototype | gain chosen on bag 0, no null test | 0.438–0.455 | — | — | Dropped: χ² gate effectively off; 6.2 m on one log of the unstructured stress case |
| v1 | global correlation, null test, adaptive R | 0.536 | 2.030 | 1.715 | A strong spurious plane breaks C02 (7.2) |
| v3 | likelihood alignment + mode agreement | — | — | 2.346 | Rejects almost everything; dropped |
| v4 | per-direction local alignment | 0.544 | 2.030 | 5.208 | Snaps off-axis walls onto the main axis; dropped |
| v5 | 1-D EKF with walls as landmarks | 0.488 | 2.757 | 2.806 | Early VINS heading change exceeds the drift model; dropped |
| v6 | v1 + agreement veto + capped prior | 0.558 | 2.030 | 1.715 | Good |
| **v7** | v6 + physical drift gate | **0.562** | **1.940** | **1.749** | Frozen; became F16 |

**v7 per run (F8 in brackets).**

- Multi Floor: 0.543 (0.766), 0.474 (0.731), 0.572 (0.619), 0.617 (0.576), 0.578 (0.587), 0.586 (0.475). Four of six are better; runs 4 and 6 are worse.
- Long Corridor: 1.673 (4.745), 1.993 (4.853), 2.153 (3.947). Three of three are better.
- Corridor02: 1.702 (2.121), 1.729 (2.143), 1.816 (2.239). Three of three are better.

**Stress cases** (synthetic perturbations of the real keyframe normals; mean ATE in m):

| Case | MF | LC | C02 |
| --- | --- | --- | --- |
| No structure (random normals: cave / open field) | 0.626 (= F8) | 4.515 (= F8) | 2.168 (= F8) |
| Structure lost after 40% | 0.558 | 3.560 | 1.870 |
| Structure only after 40% | 0.628 | 3.955 | **2.616 (worse than F8)** |
| 30% outlier normals | 0.486 | 1.937 | 1.755 |
| Only 20% of points | 0.578 | 2.147 | 1.879 |
| Strong spurious plane fixed to the robot (30% of points, ±10°) | 0.628 | 3.335 | **4.375 (5.6 on 2 of 3 runs)** |

**Sensitivity** (v1 on Multi Floor, each default changed 3–9×):

- q\_t ÷9 / ×9: 0.554 / 0.536
- turn factor ÷3 / ×3: 0.532 / 0.512
- initial R 1° / 6°: 0.551 / 0.595
- search 10° / 25°: 0.533 / 0.536

Every variant stays below F8 (0.626), so no setting is critical.

**Integration check.** SAH was built into `fusion_node_v2.py` (worker thread, gradual application capped at 0.25° per step, exception-safe). The real node callbacks were then driven offline with ROS stubbed (`node_harness.py`):

| Run | Offline replay | Through node code |
| --- | --- | --- |
| LC run 1 | 1.673 | 1.677 |
| LC run 2 | 1.993 | 2.003 |
| C02 run 1 | 1.702 | 1.705 |
| MF run 1 | 0.543 | 0.548 |

With SAH off, the harness reproduces F8 exactly (4.745). It also works without scipy and with either callback order.

**Bugs fixed during development.**

- The Manhattan replay had a sign error that made it worse (about 1.6).
- The first live measurement ignored corrections still being applied; it now accounts for them.
- The harness had path and string-column errors.

**Conclusion.** v7 helped all six corridor runs and four of six Multi Floor runs in replay, and it switches off without structure. It has three disclosed failure modes:

- a large plane moving with the robot in a single-direction corridor;
- a reference first built from walls a few degrees off;
- the two best Multi Floor runs get slightly worse.

### Phase 15 — SAH live, config F16 (17–18 Oct)

**Purpose.** To confirm the replay gains of SAH v7 on the real ROS stack, with nothing else changed (C\_T = 0.03, no gate, WARMUP 20 s).

**Setup.** The batch `run_sah_batch.sh` ran F16 × 3 with keyframes on each sequence, then the frozen back end, then zipped everything to `for_claude10.zip`. Rates were 0.5× for Long Corridor and Multi Floor (bags from the external drive) and 0.33× for Corridor02. These rates were chosen so the heading worker never skips a keyframe.

The first start failed: the update zip had not been saved to `~/Downloads`, so the script was missing. After it was re-sent and unzipped, the batch started at 20:27 local time on 17 Oct.

| Sequence | Run 1 | Run 2 | Run 3 | Mean ± sd (m) | Max (m) | Rows | Time | Replay prediction | F8 live |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Long Corridor (0.5×) | 1.99 | 2.16 | 3.17 | **2.44 ± 0.64** | 5.38 / 5.73 / 7.85 | 2775–2776 | 20:27–20:58 | 1.94 | 4.53 (max 11.4–14.1) |
| Multi Floor (0.5×) | 0.56 | 0.80 | 0.53 | 0.63 ± 0.15 | 1.07 / 1.35 / 1.22 | 4082–4110 | 20:58–21:46 | 0.562 | 0.617 (9 runs, 1.0×) |
| Corridor02 (0.33×) | 1.69 | 1.72 | 1.68 | 1.695 ± 0.026 | 2.69 / 2.64 / 2.88 | 8265–8355 | 21:46–00:04, about 46 min per run | 1.749 | 2.12 |

**Expected vs obtained.**

- **Long Corridor.** All three runs beat F8, the mean almost halved, and the maximum error halved. The result is 0.5 m worse than the replay predicted, and run 3 (3.17) is clearly worse than runs 1–2. At 2.44 m it is level with Switch-SLAM's 2.42 m, but above the challenge best (1.254) and LODESTAR (1.386).
- **Multi Floor.** The mean is unchanged against F8, and run 2 (0.80) is worse than all nine F8 runs (the worst was 0.77). The replay had predicted 0.56.

The Multi Floor comparison is confounded: F16 ran at 0.5× with about 4100 rows, while F8 ran at 1.0× with 3100–3300 rows. A matched F8 run at 0.5× is needed before any claim.

**Batch complete.** Corridor02 F16 × 3, the back end on all F16 recordings and the SAH log columns arrived on 18 Oct and are written up in Phase 16.

### Phase 16 — F16 batch completed: Corridor02, back end, and the Long Corridor run 3 check (18 Oct 2026)

**Purpose.** To finish the F16 batch (Corridor02 live runs and the back end on all three sequences), and to find out why Long Corridor run 3 (3.17 m) was worse than runs 1–2.

**Setup.** The results arrived in `for_claude10.zip`. The configuration is unchanged (F16, 3 runs per sequence; rates 0.5× for Long Corridor and Multi Floor, 0.33× for Corridor02). The run 3 check used the logged SAH columns and statistics, fused and A-LOAM path lengths, per-row A-LOAM steps, rigid-aligned comparisons between the three fused paths, and the replay scores in the summary files. The bundle contained no ground-truth file; the per-time error was computed on 19 Oct from the ground-truth file uploaded earlier (Phase 17).

**Corridor02 live (F16, 0.33×).**

| Run | ATE (m) | Max (m) | Rows | SAH final correction (°) | SAH updates accepted |
| --- | --- | --- | --- | --- | --- |
| 1 | 1.69 | 2.69 | 8342 | −4.06 | 151 |
| 2 | 1.72 | 2.64 | 8355 | −3.85 | 152 |
| 3 | 1.68 | 2.88 | 8265 | −3.76 | 153 |

The mean is **1.695 ± 0.026 m**, against 2.12 (F8), 1.87 (F12), 1.74 (F14) and 4.03 (VINS). The replay had predicted 1.749. The three runs applied almost the same heading correction, which explains the tight spread. The replay failure modes (4.375 m stress case, 2.62 m mis-seeded reference) did not appear. The logged LiDAR path alone scored 3.28, 3.31 and 3.74 m, so the fusion roughly halves it.

**Back end** (iso loop weights, one search round, odometry noise 1.46°/0.054 m, all frozen from Multi Floor).

| Sequence | Run 1 | Run 2 | Run 3 | Mean ± sd (m) | Same runs, no loops | Earlier F8 + loops |
| --- | --- | --- | --- | --- | --- | --- |
| Long Corridor | 1.583 | 1.312 | 2.125 | **1.673 ± 0.414** | 2.440 ± 0.641 | 2.67 ± 0.73 |
| Multi Floor | 0.363 | 0.564 | 0.435 | **0.454 ± 0.102** | 0.629 ± 0.147 | 0.347 ± 0.036 |
| Corridor02 | 0.807 | 1.728 | 0.948 | **1.161 ± 0.496** | 1.695 ± 0.026 | 2.10 |

On Corridor02 run 2, loop closure changed nothing (1.728 m with loops against 1.724 m without). Why was not checked. Multi Floor with loops is still above the F8 + loops mean, but F16 ran at 0.5× and F8 at 1.0×, so the comparison is not matched.

**Long Corridor run 3 check.**

| Run | ATE (m) | SAH final (°) | SAH accepted | Structure rejections | Logged LiDAR path alone (m) | Fused path length (m) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.99 | −5.86 | 254 | 193 | 1.35 (max 2.04) | 597.2 |
| 2 | 2.16 | −3.63 | 280 | 193 | 1.02 (max 2.13) | 598.9 |
| 3 | 3.17 | −5.83 | 278 | 191 | 5.16 (max 11.01) | 599.6 |

- **No replay stress.** All runs reported 0 dropped SAH keyframes, 2769 poses inside the ground-truth span, and clean container restarts. The largest A-LOAM step in any row was 0.83 m, and no row exceeded the 1.0 m jump limit.
- **SAH was not the cause.** Run 3 ended on the same correction as run 1 (−5.83° against −5.86°) with the same structure rejections. The only difference is a transient: run 3 swung to +1.97° early and sat about 1.5° more negative around 200 s.
- **The LiDAR path drifted in run 3.** The distance between the fused and the logged A-LOAM path went from 7.2 m at 220 s to 31.6 m at 275 s, while in runs 1 and 2 it stayed at 5–8 m. Step lengths were identical, so this is a heading divergence of roughly 8–10°, not a speed difference. The logged A-LOAM path alone scored 5.16 m; the fused result (3.17 m) was better than that.
- **The fused paths agree closely.** After rigid alignment the fused paths differ by 1.36 m rms (run 3 against 1), 1.25 m (2 against 1) and 2.26 m (3 against 2). The extra error is a modest drift spread over the run, largest in the first 20–60 s.
- **Fused lost to the logged LiDAR path in runs 1–2** (1.99 against 1.35, and 2.16 against 1.02). The F8 run 1 log shows the same pattern (4.76 fused against 2.61 LiDAR). The A-LOAM here ran inside the loop on fused predictions, so this is not an independent LiDAR-only result.
- **Not established.** Why A-LOAM's scan-to-map slipped in the last minute of run 3. The fused path did lose accuracy there (Phase 17).

**Multi Floor SAH log.** The corrections differed run to run: final +4.81°, +5.60° and −0.84°. Run 2 accepted only 175 updates (runs 1 and 3: 360 and 341) and had 307 structure rejections (runs 1 and 3: 121 and 115). That fits run 2 being the worst of the three (0.80 m), with SAH partly inactive rather than misfired, but this is a coincidence of two logs, not a tested cause.

**Expected against obtained.**

| Sequence | Replay prediction | Live F16, no loops | Gap |
| --- | --- | --- | --- |
| Long Corridor | 1.94 | 2.44 ± 0.64 | +0.50 |
| Multi Floor | 0.562 | 0.63 ± 0.15 | +0.07 |
| Corridor02 | 1.749 | 1.695 ± 0.026 | −0.05 |

**Conclusion.**

- F16 is the best live configuration without loops on Long Corridor (2.44) and Corridor02 (1.695). On Multi Floor it is unchanged, pending a matched control.
- With loops, Long Corridor reaches 1.67 ± 0.41 m. That is below Switch-SLAM's 2.42 m but above the challenge best (1.254) and LODESTAR (1.386).
- Long Corridor run 3 was a drift of the A-LOAM path inside the loop, not a SAH failure or a replay problem. The spread of F16 on Long Corridor (±0.64) is mostly A-LOAM variance.
- Open: why loop closure did nothing on Corridor02 run 2, and whether fused should lean more on the LiDAR path in Long Corridor.

### Phase 17 — Published-number check, near-range filter study and Long Corridor per-time error (19 Oct 2026)

**Purpose.** To verify SuperLoc's figures before citing them, and to test whether a larger minimum range protects SAH against a planar object carried with the robot, the known failure mode.

**SuperLoc check.** The paper (arXiv 2412.02901) was read twice, as a PDF and as HTML v2. Table III is "ATE Performance on SubT-MRS" with the note "\* denotes incorporation of loop closure"; SuperLoc's row carries no asterisk, and the text says its average of 0.271 m was reached without loop closure. It reports **0.817 m on Corridor01** and **0.315 m on Floor01**, measured with its odometry system (Section IV.C). The paper does not define its ATE, give units or state the alignment. The earlier row in this record called it prior-map localisation and "a different task". That was wrong: the map-based localisation table is Table II (outlier percentages), and Table III is odometry.

This changes two statements. SuperLoc's figures are the strongest published results without loop closure on both sequences. Our Multi Floor with loops (0.347 m) is above its 0.315 m, and our Long Corridor front end (2.44 m) and F16 + loops (1.67 m) are above its 0.817 m. The claim that Multi Floor "beats every published result" is withdrawn; the result beats Switch-SLAM and the challenge entries. The match between the Floor01 and Multi Floor sequences is supported by the challenge values in SuperLoc's table (0.401 and 0.577), which equal those cited here; the ground-truth cross-check is still pending.

**Near-range study.** SAH v7 was replayed on the F8 keyframes (Multi Floor 6, Long Corridor 3, Corridor02 3 recordings), scored against ground truth. The only change was the minimum range r\_min applied to the keyframe points before the normals are computed. The live node already uses 1.0 m.

| Mean ATE (m) | r\_min 1 m (live) | 2 m | 3 m | 4 m | 5 m | 6 m | 8 m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Long Corridor | 1.940 | 1.929 | 1.918 | 2.012 | 2.091 | 2.209 | 2.236 |
| Corridor02 | 1.749 | 1.783 | 1.771 | 1.805 | 1.800 | 1.802 | 1.775 |
| Multi Floor | 0.552 | 0.615 | 0.513 | 0.503 | 0.485 | 0.497 | 0.486 |

On real data, up to 5 m changes the mean by at most 0.15 m (Long Corridor) and 0.05 m (Corridor02), and Multi Floor improves from 0.55 to 0.49. All of these are inside the run-to-run spread (about 0.1 m on Multi Floor), so none of it is claimed. At 8 m Long Corridor worsens by 0.30 m.

**Carried-object stress.** A synthetic vertical plane fixed in the body frame, 8 m wide, about 25% of the points, its angle oscillating between 10° and 30°, was added at distance d. Without it the means are 1.940 (Long Corridor) and 1.749 (Corridor02); F8 without SAH gives 4.515 and 2.168.

| Mean ATE (m) | d (m) | r\_min 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- | --- |
| Corridor02 | 1.5 | 2.734 | 3.817 | 3.145 | 1.805 | 1.800 |
| Corridor02 | 3.0 | 3.217 | 3.301 | 2.953 | 3.283 | 1.763 |
| Long Corridor | 1.5 | 2.447 | 2.420 | 2.084 | 2.012 | 2.091 |
| Long Corridor | 3.0 | 2.451 | 2.456 | 2.408 | 2.073 | 2.092 |

The filter protects only when it removes the whole object. The plane reaches out to 4.3 m (d = 1.5) and 5 m (d = 3.0), so r\_min 4 and 5 recover the unperturbed values, while smaller radii leave the outer part in and give no protection (Corridor02 reaches 3.1–3.8 m at d = 1.5, worse than F8 without SAH at 2.17 m).

**Conclusion.**

- The minimum range is a platform setting: it has to exceed the farthest extent of anything fixed to the robot. It is not a general fix, and nothing in the real keyframes shows such an object. The live default stays at 1.0 m.
- The object's geometry here is my own construction, so this shows the mechanism, not how often it occurs.
- A stronger defence would test motion: points fixed in the body frame across keyframes, while wall points slide past. It was not built, because validating it needs real data that contains a carried object; testing it only on this synthetic case would be circular.

**Long Corridor per-time error against ground truth.** The ground-truth file from the earlier upload was in the workspace, so the F16 runs were scored over time (Umeyama alignment per run, 20 s windows, RMS error in metres).

| Window (s) | Fused run 1 | Fused run 2 | Fused run 3 | A-LOAM run 1 | A-LOAM run 2 | A-LOAM run 3 |
| --- | --- | --- | --- | --- | --- | --- |
| 0–20 | 4.28 | 4.87 | 6.63 | 1.64 | 1.11 | 10.31 |
| 20–60 | 1.34 | 2.02 | 2.34 | 1.27 | 0.51 | 6.08 |
| 60–180 | 1.46 | 1.44 | 1.85 | 1.42 | 1.24 | 1.72 |
| 180–240 | 2.24 | 1.72 | 3.95 | 1.29 | 0.80 | 3.32 |
| 240–280 | 1.67 | 2.45 | 3.05 | 1.09 | 0.88 | 8.44 |

- **The maximum error is at the start in every run** (5.38, 5.73 and 7.85 m, at 8 s, 8 s and 1 s). The first 20 s, the LiDAR-only warm-up, carry 4.3–6.6 m RMS. The start is one end of an out-and-back path, so it also shows any global heading error after alignment.
- **Run 3 is worse in two places:** the first 60 s, where its A-LOAM path alone is 10.3 m off in the first 20 s against 1.1–1.6 m in runs 1–2, and from 180 s on, where the A-LOAM path drifts again (3.3 m, then 8.4 m) and the fused path follows it only partly (3.9 m, then 3.1 m).
- **No scale bias.** A Sim(3) alignment gives scales of 1.006, 1.003 and 1.006 and the same RMSE (1.94, 2.15, 3.14 m). The estimated paths are 2.0–2.3% longer than the ground truth when sampled at its rate (Corridor02 +2.9–3.2%), which is jitter, not scale.
- **Corrects Phase 16.** The extra error of run 3 is not only drift spread over the run: its start-up phase was clearly worse, and so was the last third.

### Phase 18 — Six runs per sequence, matched Multi Floor control and Corridor02 loop check (19 Oct 2026)

**Purpose.** To raise F16 from three to six runs on every sequence, to run the matched F8 control on Multi Floor at the same replay rate (0.5×), and to find out why the loop closure did nothing on Corridor02 run 2.

**Setup.** The batch `run_longer_batch.sh` ran 12 live runs (F8 runs 7–9 on Multi Floor; F16 runs 4–6 on Long Corridor, Multi Floor and Corridor02) between 01:54 and 07:13, then the back end on all six F16 runs of each sequence with the frozen settings (iso loop weights, 1 search round, 8 m radius, odometry noise 1.46°/0.054 m). The results arrived as `for_claude11.zip`. The first start used an old backup folder and found no bags; it was restarted from the correct folder, so the 12 runs are the only ones in the index.

**Front end (ATE RMSE, m).**

| Sequence | Config | Runs | Mean ± sd |
| --- | --- | --- | --- |
| Multi Floor, 0.5× | F8 (matched control) | 0.73, 0.52, 0.56 | 0.603 ± 0.112 |
| Multi Floor, 0.5× | F16 | 0.56, 0.80, 0.53, 0.58, 0.77, 0.60 | 0.640 ± 0.115 |
| Long Corridor, 0.5× | F16 | 1.99, 2.16, 3.17, 2.13, 2.00, 2.19 | 2.273 ± 0.447 |
| Corridor02, 0.33× | F16 | 1.69, 1.72, 1.68, 1.68, 1.64, 1.84 | 1.708 ± 0.069 |

**Back end with iso loops (same runs).**

| Sequence | No loops | With loops | Change |
| --- | --- | --- | --- |
| Multi Floor (6 runs) | 0.638 ± 0.115 | 0.523 ± 0.224 | −18% |
| Long Corridor (6 runs) | 2.274 ± 0.449 | 1.538 ± 0.304 | −32% |
| Corridor02 (6 runs) | 1.707 ± 0.070 | 1.250 ± 0.435 | −27% |

**Multi Floor control.** At the same replay rate F16 is 0.640 and F8 is 0.603; the difference is 0.04 m against a spread of 0.11 m (Mann–Whitney p = 0.44, 6 against 3 runs). SAH therefore does nothing on Multi Floor, as designed, and the earlier F8 mean at 1.0× (0.627 ± 0.109, six recorded runs) agrees. The Multi Floor gain with loops is a loop-closure gain. Loop closure was run on the F16 runs only, so a matched F8 + loops figure at 0.5× does not exist yet; the earlier 0.347 ± 0.036 was measured at 1.0× and is not directly comparable with the F16 + loops figure of 0.523. In one run (run 5) loops made the result worse (0.767 to 0.955, max 2.81 m).

**Long Corridor.** The three new runs (2.13, 2.00, 2.19) sit close together and are all better than the earlier run 3 (3.17). The six-run mean 2.273 is 50% below F8 (4.53 ± 0.49) and still level with Switch-SLAM's published 2.42 on the front end. With loops the mean is 1.538 ± 0.304 (earlier three-run value 1.673).

**Corridor02: why the loops did nothing in run 2.** With the full loop lists printed, the gain depends on one loop. Runs 1, 3, 4 and 5 found a long-span loop that joins the start to the end of the traverse (loops such as 158↔692 s or 0↔749 s) and fell from about 1.7 m to 0.81, 0.95, 1.15 and 1.01 m. Runs 2 and 6 found none (16 and 17 loops, all short-span) and stayed at 1.73 and 1.85 m. The start and the end were no further apart in those two runs: the estimated minimum distance between the 155–170 s and 685–705 s parts of the path is 0.78 and 0.80 m, against 0.48–0.70 m in the other four, and the ground truth gives 0.78 m. So the back end failed to accept the loop, and drift did not move the two places out of its 8 m search radius. The cause inside the matching step (ICP acceptance on that pair of keyframes) is not confirmed; the keyframe files are on the laptop and were not part of the upload.

**Expected against obtained.**

| Expectation | Obtained |
| --- | --- |
| SAH is neutral on Multi Floor | Met: 0.640 against 0.603 (matched) |
| The Long Corridor gain holds with more runs | Met: 2.273 ± 0.447 against 4.53 ± 0.49 |
| The Corridor02 gain holds | Met: 1.708 ± 0.069 against 2.12 ± 0.06 |
| Loops help every run | Not met: 2 of 6 Corridor02 runs and 1 of 6 Multi Floor runs gained nothing or lost |

**Conclusion.**

- The SAH gains on Long Corridor and Corridor02 are reproducible at six runs; on Multi Floor SAH makes no difference.
- Loop closure is the largest remaining gain, but on Corridor02 it depends on whether one long-span loop is accepted (4 of 6 runs). That is a back-end reliability problem, not a front-end one.
- The headline numbers with loops are now Long Corridor 1.54 m, Corridor02 1.25 m and Multi Floor 0.52 m (F16), and Multi Floor 0.35 m (F8 at 1.0×, unmatched). SuperLoc's published 0.817 (Corridor01) and 0.315 (Floor01) remain lower than ours, with the caveats in Phase 17.
