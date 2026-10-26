# LiDAR-gap rule (G23): development evidence and the test fixed before it is run (26 Oct 2026)

## Why
The sensor-outage campaign of 26 Oct (`Fault_Injection_Protocol.md`, results in `Outage_Campaign_Results.md`) showed that G20 breaks under a LiDAR outage: at the first scan after a gap the LiDAR-inertial pose jumps (32-348 m) and the fused trajectory follows it; the fused ATE is 5-148 m worse than VINS-Mono alone in 9 of 9 runs.

## Cause (found in the code, not only in GenZ-LIO)
`FusionCore.step` works on increments between consecutive scans. After a gap the VIO increment over the gap (tens of metres) exceeds `jump_max` (1 m per step), so the VINS step is classed as a jump, the mode becomes VO_FAIL / WARMUP and "the LiDAR carries this step" with weight 1: the whole LiDAR jump over the gap is added to the fused pose. The GenZ-LIO jump itself is a front-end property (dead reckoning through the gap), the adoption of it is a fusion property.

## The rule (`FusionCore(gap_T=...)`, environment `GAP_T`, configuration G23 = G20 + `GAP_T=1`)
A scan interval longer than `gap_T` = 1 s (normal interval 0.1-0.2 s; the largest interval in any earlier log is 0.20 s) is a gap. For that one step:
1. the VIO jump limits are scaled by the gap: max(`jump_max`, 5 m/s x gap) and max(`rot_jump_max`, 2 rad/s x gap);
2. the LiDAR increment is ignored (W = 0): the VIO (scale-corrected as before) carries the step, mode `GAP`;
3. no consistency window spans the gap: the stored window poses are dropped, the gate state and statistics earned before the gap are kept; the scale and guard buffers restart (scale value held);
4. if the VIO cannot be used either, the pose is held (mode `GAP_HOLD`).
Off by default (`gap_T = 0` is G20 bit for bit; unit test `test_gap_rule`). No other change to G20.
The constants (1 s, 5 m/s, 2 rad/s) were fixed from physical limits before any replay; they were not tuned. One design choice was changed during development after a replay (rule 3: the first version reset the gate, which handed trust to the LiDAR for 20 s after the gap).

## Development evidence (replay of the core on the 19 logs of the first campaign, without Channel T+, no keyframes in that pack)
Full-span ATE (m). "live" = the live G20 run, "G20 replay" = the core replayed (equals the live run within 0.1 m where Channel T+ matters little: Multi Floor and Cave02; Long Corridor differs by up to 4 m because the heading channel is left out), "G23" = core with the gap rule.

| Run | live G20 | G20 replay | G23 replay |
| --- | --- | --- | --- |
| MF LiDAR 3 x 10 s (r1, r2) | 12.59, 12.59 | 12.51, 12.50 | 0.84, 0.83 |
| MF LiDAR 2 x 30 s (r1, r2) | 149.96, 52.35 | 150.19, 52.26 | 2.17, 3.00 |
| LC LiDAR 3 x 10 s (r1, r2) | 21.90, 9.91 | 21.96, 12.20 | 15.52, 14.16 |
| LC LiDAR 2 x 30 s (r1, r2) | 21.95, 13.67 | 24.37, 15.91 | 3.09, 4.34 |
| C02 LiDAR 2 x 30 s | 32.38 | 32.38 | 3.73 |
| 10 camera / no-fault logs | 0.26-5.69 | | identical to G20 replay (to 0.01 m) |

Reading: the rule removes the jump in 7 of 9 LiDAR-outage logs (to 0.8-4.3 m; VINS-Mono alone is 1.4 m on Multi Floor, 5.1-5.4 m on Long Corridor, 13.9 m on Cave02). It does not fix Long Corridor with 10 s gaps (15.5 and 14.2 m; in one log it is 2 m worse than the G20 replay): the windows fall in the degenerate corridor section where the unfaulted error is already 1-4 m, and no sensor is good there. These 19 logs are development data for the rule.

## The test (not yet run; rules fixed now)
New recordings are not available, so the test uses the same bags with a second, disjoint set of outage windows and a live run of both configurations on every rewritten bag. This tests the rule against windows it has not seen, not against a new environment; it is stated that way in the report.
- Faults: LiDAR only. Codes `L10B` (3 x 10 s at 0.15 D, 0.42 D, 0.68 D) and `L30B` (2 x 30 s at 0.20 D and 0.60 D), D = sequence span (`make_fault_bag.py`, tested). The first-campaign windows were 0.30/0.55/0.80 D and 0.40/0.75 D. Camera outages are not repeated: the rule cannot act without a scan gap, and the maximum scan interval in all 10 camera and no-fault logs is 0.20 s.
- Sequences and rates as before (Multi Floor 1.0x, Long Corridor 0.5x, Cave02 0.5x). Runs: Multi Floor and Long Corridor, L10B and L30B, two replicates; Cave02 L30B, one. G20 and G23 are run live one after the other on the same rewritten bag, with keyframes recorded (so Channel T+ can be replayed). 9 bags, 18 live runs, about 5.6 h.
- Units: sequence x outage = 5 (MF L10B, MF L30B, LC L10B, LC L30B, C02 L30B), mean over replicates where there are two.
- Measures: full-span ATE as in Section 5.4; survival rule (largest single step below 5 m, no NaN, log reaches the end); GenZ-LIO alone and VINS-Mono alone from the same logs.

Predictions (written before the data; they can be wrong):
- **P1 survival.** G23 never makes a step above 5 m in any of its 9 runs. G20 breaks the rule in at least 7 of its 9 runs.
- **P2 accuracy.** G23 is lower than G20 by more than 0.10 m and 10 % in at least 4 of 5 units. One-sided exact sign test over the 5 units: 5 of 5 gives p = 0.031, 4 of 5 gives p = 0.19 and is reported as a trend, not as significant. The expected failing unit is LC L10B.
- **P3 against VINS-Mono alone.** G23 is within 2 x the ATE of VINS-Mono alone on the same recording in at least 4 of 5 units (expected failing unit: LC L10B). This is a statement about whether the fix brings the system back to the level of its better sensor, not about beating it.
- **P4 no harm.** With the LiDAR present the rule never acts (checked on logs, not run live).
Rules for use: if P2 holds (at least 4 of 5) the report presents G23 as the final configuration for outages and says that the evidence is the second window set on seen bags; if P2 fails, G23 is reported as a failed fix and G20 stays. Nothing about G23 is changed after the first run of this test.

## Limits stated in advance
Same bags and sensors; message deletion, not a physically blocked LiDAR; GenZ-LIO's own re-registration after a gap is not changed (the rule bridges the gap, it does not repair the front end); results on Long Corridor depend on whether the window falls in the degenerate section; live runs are not deterministic, so the two replicates are reported separately.

## Running
Laptop, repository folder `fusion_v4/faults`: `PLAN_SET=gap DEADLINE=<clock time> setsid nohup systemd-inhibit --what=sleep:idle bash fault_batch.sh > ~/faults_gap_batch.log 2>&1 < /dev/null & disown`. Resumable; packs `~/faults_gap_results.tgz` (logs and keyframes). Disk as in the first campaign (one rewritten bag at a time on the drive; at least 3 GB free on the SSD).
