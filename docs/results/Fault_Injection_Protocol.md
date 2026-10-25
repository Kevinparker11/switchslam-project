# Sensor-outage campaign on real recordings: protocol written before any run (25 Oct 2026)

Why this test. The thesis claim is robustness when one sensor degrades or fails. Every real-data result so far (Multi Floor, Long Corridor, Cave02, Corridor02, GEODE) has both sensors present; the cases where one sensor is gone exist only in the synthetic study (`Thesis_Methodology_Action_Plan.md`, scenarios A and D) and in the plan for BlockLiDAR / BlockVisual (`Dataset_Test_Plan.md` T4), which was never run. The G18-G20 mechanisms (consistency gate, scale correction, fast check, blow-up guard) were built from observed failures, and nobody has seen them under an outage of known time and length. A fault injected at a fixed time into a recording we already have gives a paired comparison (same bag with and without the fault) and an exact cause, which the held-out Gazebo world cannot.

## Design
- Faults (all topics of the sensor type are dropped, IMU and everything else untouched, ground truth unchanged): **C10** camera off for 10 s (3 windows), **L10** LiDAR off for 10 s (3 windows), **C30** camera 30 s (2 windows), **L30** LiDAR 30 s (2 windows). Windows start at fixed fractions of the sequence span D: 0.30, 0.55, 0.80 D for 10 s; 0.40 and 0.75 D for 30 s (`fusion_v4/faults/make_fault_bag.py`; tested with a fake bag in `tests_v4/test_make_fault_bag.py`). All start after VINS-Mono has initialised.
- Sequences and replay rate are those of the 24 Oct live G20 runs: Multi Floor 1.0x, Long Corridor 0.5x, Cave02 0.5x (laptop). GEODE needs the PC and is not part of this run.
- References (no new runs): the live G20 runs of 24 Oct on the same sequences (Multi Floor 4, Long Corridor 4, Cave02 2), same code, same machine, same rate. One extra control: Multi Floor rewritten with no fault (`none`), which checks that the rewrite itself changes nothing.
- Each rewritten bag is played once through the live G20 stack (RECORD_KF=1 as in the references). On two Long Corridor runs (C30, L30) G22 is run live too, to check that exact replay still equals live under outages (this was shown only for runs without outages). GenZ-LIO alone (G0), G17, G19, G22 and VINS-Mono alone come from replaying the logs.
- Order (priority; the batch stops starting runs at the cap, MAX_HOURS = 5.75): S control, A core (MF and LC x C10, L10, C30, L30), B replicates of A (replicates differ only through VINS-Mono's non-determinism), C Cave02 C30 and L30.

| Block | Runs | Expected time |
|---|---|---|
| S | MF none | 12 min |
| A | MF x4 (12 min each), LC C10 / L10 (14), LC C30 / L30 with G20 and G22 (25) | 2.1 h |
| B | MF x4, LC x4, G20 only | 1.7 h |
| C | Cave02 C30, L30 (about 41 min each) | 1.4 h |
| Total | 19 runs | about 5.4 h |

## Measures (fixed now)
1. **Survival**: log reaches the end (last row within 5 s of the bag end), no NaN, no single step above 5 m. A crash, a hang or a stuck pose is a result and is reported as such.
2. **dATE** = full-span ATE of the faulted run minus the mean ATE of the references, per configuration (G0, VINS-Mono alone, G17, G19, G20, G22).
3. **Window drift**: translation RPE over each outage window plus 30 s after it, faulted minus reference on the same interval.
4. Expected log rows = reference rows minus the dropped LiDAR scans; fewer rows than that is reported as lost scans (compute starvation), not as a method result.

## Hypotheses and the predictions made before the data (they can be wrong)
- **H0 control**: GenZ-LIO does not use the camera, so G0 under C10 / C30 equals the unfaulted G0 (|dATE| < 0.01 m); the rewritten no-fault Multi Floor run lies inside the spread of the four references (G20 0.26-0.38 m).
- **H1 camera outage**: the fused G20 is at most 0.10 m worse than its own reference (median over runs), i.e. it falls back to something close to LiDAR-inertial. A larger loss would mean the VINS-Mono restart or scale correction corrupts the fusion.
- **H2 LiDAR outage**: the fused G20 has a lower dATE than GenZ-LIO alone by more than 0.10 m (VINS-Mono carries the gap). Predicted for 30 s; open for 10 s.
- **H3 G22 against G20**: G22 (more LiDAR weight) loses less under camera outages and more under LiDAR outages than G20. Both directions are predictions, not findings.
- A difference below 0.10 m is a tie (inside the ground-truth quality). Units for the tests are sequence x fault (8 from blocks A+B means, plus 2 from block C); exact Wilcoxon signed-rank where n >= 6, Holm over H1-H3; every run, including failed ones, goes into the table.

## Limits stated in advance
- Dropping messages is a clean outage of known length; it is not a physically blocked LiDAR or a covered lens (BlockLiDAR / BlockVisual are the real counterparts and need downloads).
- G22 was chosen in-sample on the development data; H3 is a test of a prediction, not a confirmation of G22.
- Exact live-equals-replay has not been shown for outages; the two live G22 runs check it. If they disagree, the replayed numbers for the other configurations are marked as unconfirmed.
- Windows at fixed fractions are the same for every run on a sequence; they are not randomised.

## Running it
`cd ~/switchslam-project/fusion_v4/faults`, then `setsid nohup systemd-inhibit --what=sleep:idle bash fault_batch.sh > ~/faults_batch.log 2>&1 < /dev/null & disown`. Resumable (finished runs have a DONE file); `MAX_HOURS=4` lowers the cap; `bash fault_batch.sh pack` rebuilds `~/faults_results.tgz`, the only file to send back.
