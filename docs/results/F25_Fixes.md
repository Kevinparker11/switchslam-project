# F25A: one fix to F24 from the Cave02 / GEODE logs, and one idea that failed (4 Nov 2026)

Request: bring F24 (A-LOAM + VINS-Mono) close to 1 to 2 m on Cave02 (7.55 / 12.63) and GEODE stairs alpha (6.15 / 14.00). Everything here is a diagnosis of the logged F24 run 1 of each bag plus open-loop replays of those logs; no new live run exists yet. Cave02 and GEODE become **tuned-on (development) data** for anything reported from F25A.

## 1. GEODE: the anchored handover adopted a distrusted VINS (fixed in F25A)
- Log of F24 run 1, row 2907: the second WARMUP -> FUSED handover moved the fused rotation by **60.2 deg** (first handover 0.9 deg). At that row `vio_gamma = 0` and `rot_gamma = 0`: both consistency checks had already closed on this VINS segment. The anchor (`HANDOVER=anchor`) sets the fused rotation from the VINS orientation without looking at them. Error went from about 4 m to about 12 m in the last 40 s.
- Fix, `HANDOVER_TRUST=1` (`FusionCore(handover_trust=True)`): apply the anchor only if `gamma >= 0.5` and `rot_gamma >= 0.5` at that step; otherwise the handover behaves as `none`. No new constant. Default off: F24 is unchanged bit for bit.
- Open-loop replay of the logged inputs (A-LOAM pose, VINS pose, body Hessian; no SAH, no orientation-tensor cap, no pose feedback into A-LOAM): replay without the fix 6.07 / 13.43 (live F24 6.15 / 14.00, same two handovers, 1.1 and 57.1 deg); **with the fix 5.48 / 11.41**.
- Not a route to 1 to 2 m: the VINS is useless on this bag (186 m alone), F24 is A-LOAM for 78 % of the scans, and A-LOAM alone is about 6 m (7.98 m on the PC).

## 2. Cave02: the standstill-hold idea was wrong (not used)
- Observation: for 60 to 120 s the robot is nearly still (ground truth 0.3 to 0.5 m per 10 s) while A-LOAM travels 2 to 5 m per 10 s. That looked like a wander that a standstill hold could remove.
- Check: over the same 10 s windows the A-LOAM **net displacement is 0.03 to 0.14 m**. The jitter is zero-mean: it adds path length, not position error. Holding the pose cannot remove a 12 m offset that is not made of it.
- Replay with an oracle standstill flag (ground-truth speed under 0.1 m/s over 1 s, 27 % of the scans): rotation and translation hold 13.39 (worse, it discards real rotation); translation-only hold 7.58; with the LiDAR-wander condition removed 7.47; F24 replay 7.50. No gain even with a perfect flag.
- Consequence: the code (`still_detect.py`, `FusionCore(zupt=...)`, `ZUPT*` switches in `fusion_node_v2.py`, `test_f25.py`) stays, default off, with **no configuration that uses it**.
- The fused path being 16 % longer than the ground truth (552 m against 475 m) and the 12 m offset in the first four minutes are therefore not explained. The earlier F8 / F16 runs on this bag scored 4.40 to 4.47 (3 runs each), F24 7.55 in one run, and single runs differ by up to 1.1 m with the VINS start time; whether F24 is worse than F8 here, or the run is an outlier, needs a matched repeat.

## 3. What this says about the target
- With the A-LOAM + VINS-Mono front end, 1 to 2 m on these two bags is not reachable by fusion changes: GEODE is limited by A-LOAM (about 6 m) and Cave02 has never been below 3.65 m on this stack.
- The GenZ-LIO front-end stack of this project already gets there (Project docs `GenZ_fusion_v4_G20_Universal_Fix.md`, `RRT_Style_Statistical_Tests.md`, replays of recorded runs, GenZ-LIO and VINS-Mono take no feedback so replay = live): Cave02 G20 0.296 (median of 4), G22 and GenZ-LIO alone 0.28 to 0.29; GEODE stairs alpha G20 0.475 (median of 14, PC), G22 0.394, GenZ-LIO alone 0.355; with loop closure 0.32. G19/G20 were designed after the Cave02 and GEODE failures were seen: development results, and the same label applies to F25A.

## 4. Tests and run commands
- `python3 test_f25.py` (handover with a distrusted and a trusted VINS, hold on wander, no hold for a constant-speed run, no hold when the IMU is not quiet, detector); `test_fusion_core.py`, `test_handover.py`, `test_predict_guard.py`, `test_gyro_prior.py`, `test_t_cap.py` still pass.
- Live check of the fix (about 6 min at 0.5x), same environment as the F24 GEODE run: `RECORD_KF=1 SEQ_ENV=<GEODE seq.env> bash fusion_v4/run_fusion_study.sh F25A` (config `F25A` in `run_fusion_study.sh`). Expect the second handover row to show `handover_skipped = 1`; expected result about 5.5 m, not 1 to 2 m.
- Regression before F25A replaces F24 anywhere: it must equal F24 on the frozen sequences. The flag acts only when a checked VINS is distrusted at the handover, so Multi Floor, Long Corridor, Farm and Corridor02 should be identical rows unless such a handover occurs; check `handover_skipped` there.
