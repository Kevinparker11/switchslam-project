# Where the error comes from, and what to do next (17 October 2026)

Analysis with the ground truth of all three sequences (Multi Floor `ground_truth_path.csv`, Long Corridor `corridor01_gt.txt`, Corridor02 `corridor02_gt.txt`) and the logged runs (Multi Floor F8_kf_run1-6, Long Corridor F8_kf_run1-3 + F14, Corridor02 F8_kf_run1-3 + F14). Open-loop replays: the logged scan-to-map poses are reused, so they approximate what a live run would give (replay of a run's own setting reproduces its live ATE).

## 1. Clock check
Residual time offset of the GT against the logs, from rotation-speed correlation of VINS and A-LOAM (0.98-0.99): Corridor02 +0.03 s, Long Corridor +0.04 s. Negligible; no shift needed.

## 2. The dominant error is VINS-Mono heading (yaw) drift
Rotation error of each source relative to its start (degrees, at 25/50/75/100 % of the run, F8 run 1):
| Sequence | VINS yaw drift | A-LOAM map-pose yaw error | A-LOAM tilt error |
|---|---|---|---|
| Multi Floor | 5.8 / 4.4 / 3.9 / 6.3 | 12.3 / 12.9 / 4.1 / -15.2 (jumps of 10-27 deg at stairs) | up to 23 |
| Long Corridor | -4.5 / -7.2 / -6.7 / -9.0 | -9.7 / -5.0 / -5.0 / 1.2 | - |
| Corridor02 | -7.1 / -7.4 / -6.8 / -8.1 | -2.0 / -2.3 / -0.4 / -0.1 | roll up to -14 |

VINS roll/pitch stay within 1-3 deg (gravity-observable); its error is almost pure yaw, which VIO cannot observe. Our fused rotation is VINS rotation, so it carries the same yaw drift.

**Oracle test** (replace only the fused yaw with the GT yaw, everything else unchanged; mean ATE RMSE of the logs, m):
| | Multi Floor (6) | Long Corridor (3) | Corridor02 (3) |
|---|---|---|---|
| F8 replay (as run) | 0.63 | 4.51 | 2.17 |
| F8 + GT yaw at every scan | 0.39 | 1.42 | 0.90 |
| F8 + GT yaw with 2 deg noise per scan, gain 0.02 | 0.43 | 1.45 | 0.82 |
| F8 + GT yaw every 10 s, 1 deg noise | 0.70 | 1.88 | 1.15 |

With the yaw fixed, the translation-weight comparison becomes consistent: c = 0.03 (ours) 0.39 / 1.42 / 0.90; W = I (F14) 0.48 / 1.05 / 1.89; c = 0.01 0.37 / 1.97 / 1.10; c = 0.1 0.45 / 1.10 / 1.47; VINS translation only 0.88 / 3.02 / 3.85. The Corridor02 result "F14 beats F8" disappears once the heading is right.

## 3. Option 2 (VIO-health-based primary selection) is not viable as stated
- VINS-Mono's main failure here is slow yaw drift, which is unobservable from inside VIO; VIO health signals cannot see it.
- Taking the yaw from the A-LOAM map pose instead (replays, gain 0.01 to 1): Multi Floor 0.63 -> 1.58-1.64 (A-LOAM yaw jumps on stairs), Long Corridor 4.51 -> 1.96-2.28, Corridor02 2.17 -> 2.63-3.28 (good on one run, 1.26, bad on the other two, because A-LOAM's own map pose is 1.3-4.2 m depending on the run). Rate gating (1-2 deg per 10 s) does not fix it. The LiDAR map is not a reliable heading source either.

## 4. Candidate: structural heading from the LiDAR walls
All three sequences are inside a building. The dominant horizontal wall-normal direction of a single LiDAR keyframe gives an absolute heading that does not drift.
- First version (Manhattan, circular mean of 4*theta): Multi Floor, F8_kf_run1 keyframes (504), measured in the GT frame: deviation from the building axis median 1.6 deg, p90 3.7, p99 6.1, none above 10 deg. Replay: Multi Floor 0.626 -> 0.507-0.526.
- Prior art (the idea itself is not new): StructVIO (Zou et al., T-RO 2019, Atlanta-world headings in VIO); Li et al., RA-L 2020 (visual SLAM, drift-free rotation in Manhattan world); Kim, Li, Joo, RA-L/ICRA 2022 (visual compass, Manhattan); Doer and Trommer, ICINS 2021 (yaw-aided radar-inertial odometry with Manhattan world); Remote Sensing 15(1):15, 2023 (LiDAR SLAM on LIO-SAM with Manhattan planar constraints, yaw from vertical-plane normals). What would be ours: an observability-matched correction inside a VIO-primary LiDAR-visual-inertial system (roll/pitch from VIO via gravity; yaw from LiDAR structure; translation from the Schur-weighted scan-to-map), each weighted by its own information, with the measured evidence (oracle decomposition) that heading is the dominant error on SubT-MRS.

## 5. Integrity
Long Corridor and Corridor02 were used for this diagnosis, so they are development sequences for this change. A sequence not used so far is needed for the final claim (candidates: GEODE Stairs_Alpha, different building and rig, published LiDAR-camera baselines; a SubT-MRS sensor-fusion sequence not yet used; a cave sequence as a non-structured control where the correction should switch itself off).

---

# Update 17 October 2026: general version, designed not to depend on these bags

The requirement: the method must work on any new scene, not only on these bags; no fitting to the test sequences.

## Design (code: `sah/sheading.py`, replay driver `sah/sah_replay.py`; the live version is `fusion_v3/structure_heading.py`)
"Structure-anchored heading" (SAH), keyframe rate:
1. **No Manhattan assumption.** Each keyframe gives an axial histogram (0.5 deg bins over 180 deg) of the horizontal directions of near-vertical planar points, levelled with the VIO gravity direction. A reference histogram of directions is built in the world frame from accepted keyframes; new directions are learned as they appear. The heading error is the shift that best aligns the keyframe histogram with the reference (normalised circular cross-correlation within +-15 deg, sub-bin peak). Works for any set of persistent wall directions (Manhattan, Atlanta, arbitrary).
2. **Self-disabling where there is no structure.** A keyframe is used only if its histogram is more concentrated than 1.5 x the 99.9 % quantile of random directions with the same point count (Monte-Carlo null model; e.g. peak/mean 2.2 at 400 points, real Multi Floor keyframes 7-15). Alignment must also have a clear unique peak (correlation >= 0.5, margin >= 0.15). Reference start needs 5 mutually consistent keyframes (within 3 deg), otherwise it restarts.
3. **Physical process model, no per-dataset noise.** VIO yaw error grows with time (gyro bias residual, (0.05 deg)^2/s) and with the angle turned (scale/misalignment, 2 % of the turned angle). Measurement noise is estimated online from the innovations (robust covariance matching, Huber-clipped). Gates: chi-square 9 on the innovation and a physical drift-rate bound (3 sigma + 0.1 deg/s since the last accepted update).
4. If nothing passes, the estimator is exactly the previous method (F8).

## Results on Multi Floor (6 logs, replay, mean ATE RMSE m; F8 = 0.626)
| Variant | per log | mean |
|---|---|---|
| SAH, physical defaults (nothing tuned) | 0.542 0.403 0.561 0.551 0.540 0.620 | **0.536** |
| Stress: random normals everywhere (cave/open field) | identical to F8 | 0.626 (0 corrections) |
| Stress: structure lost after 40 % of the run | 0.502 0.462 0.545 0.572 0.554 0.536 | 0.528 |
| Stress: structure only after 40 % | 0.697 0.573 0.831 0.456 0.505 0.661 | 0.620 |
| Stress: 30 % outlier normals | 0.602 0.500 0.553 0.526 0.511 0.495 | 0.531 |
| Stress: only 20 % of the points | 0.587 0.452 0.574 0.603 0.522 0.731 | 0.578 |
| Stress: strong spurious moving direction on 30 % of points | 0.517 0.627 0.565 0.640 0.629 0.727 | 0.617 |

Sensitivity (each default changed 3-9x): q_t 1/9 0.554, x9 0.536; turn factor /3 0.532, x3 0.512; initial R 1 deg 0.551, 6 deg 0.595; search 10 / 25 deg 0.533 / 0.536. Always below F8; no knob is critical.

An earlier version with a tuned gain (process noise chosen on bag 0) gave 0.438-0.455 but had its chi-square gate effectively off, and without the null-model test it corrupted the unstructured stress case (6.2 m on one log); it was dropped in favour of the untuned design.

Weak points seen: log 6 (the best F8 run, 0.475) gets worse in every SAH variant (0.50-0.73). The measurement-minus-GT heading error on Multi Floor has a time pattern of +-3 deg shared by all runs (so it is either GT heading error or real non-uniform structure); robust sigma 2.5 deg.

## Next
Corridor keyframes, then the frozen design on both corridors (development data), then the live node, then an untouched sequence plus a non-structured control. Results of the live runs: `SAH_Live_Results_F16.md`.
