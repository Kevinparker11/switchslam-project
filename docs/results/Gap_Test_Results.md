# Gap rule (G23) against G20: results of the test fixed in `Gap_Rule_Test_Protocol.md` (26 Oct 2026)

Test as pre-registered: 9 rewritten bags (second, disjoint outage-window set `L10B` = 3 x 10 s, `L30B` = 2 x 30 s), G20 and G23 run live one after the other on each, keyframes recorded, 18 live runs, laptop, 28-30 min per bag (Cave02 102 min). Scoring is by `scratchpad/score_gap.py` (full-span ATE, Umeyama SE(3), same ground-truth files as Section 5.4; the numbers equal the batch summary to 0.01 m). G23 was not changed after the first run.

## 1. Live results (full-span ATE, m)

| Run | G20 | G23 | GenZ-LIO alone (G20-run / G23-run log) | VINS-Mono alone | max step G20 / G23 (m) | max step outside the gaps G20 / G23 (m) |
|---|---|---|---|---|---|---|
| MF L10B r1 | 9118.22 | **2.47** | 22612.5 / 21.5 | 1.35 | 5128 / 4.0 | 2102 / 0.2 |
| MF L10B r2 | 2172.16 | **2.93** | 9674.3 / 9674.3 | 1.34 | 2669 / 4.0 | 2161 / 2.2 |
| MF L30B r1 | 88.27 | 3219.90 | 88.2 / 16434.0 | 1.37 | 202 / 3111 | 1.3 / 3111 |
| MF L30B r2 | 1408.37 | 3238.70 | 3840.1 / 16434.0 | 1.39 | 365 / 3209 | 311 / 3209 |
| LC L10B r1 | **4.58** | 5.81 | 6.7 / 7.5 | 5.14 | 30.8 / 31.0 | 0.7 / 0.7 |
| LC L10B r2 | 190.32 | **10.43** | 192.1 / 19.6 | 5.14 | 47.0 / 29.8 | 1.9 / 0.7 |
| LC L30B r1 | 36.19 | **4.64** | 40.1 / 26.4 | 5.40 | 96.8 / 47.7 | 0.7 / 0.8 |
| LC L30B r2 | 41.64 | **4.66** | 46.5 / 26.4 | 5.40 | 104 / 47.7 | 0.7 / 0.7 |
| C02 L30B r1 | 37.39 | **21.70** | 37.4 / 37.4 | 11.2 | 74 / 13.3 | 3.3 / 3.4 |

G23 is lower than G20 by more than 0.10 m and 10 % in 6 of 9 runs, higher in 3 (MF L30B r1 and r2, LC L10B r1). No NaN, every log reaches the end.

## 2. The pre-registered predictions

Units = sequence x outage, mean over replicates (G20 | G23 | 2 x VINS-Mono alone of the same recordings):

| Unit | G20 | G23 | 2 x VINS | P2 (G23 lower by > 0.10 m and 10 %) | P3 (G23 <= 2 x VINS) |
|---|---|---|---|---|---|
| MF L10B | 5645.19 | 2.70 | 2.70 | yes | yes (by 0.001 m; fragile) |
| MF L30B | 748.32 | 3229.30 | 2.78 | **no** | **no** |
| LC L10B | 97.45 | 8.12 | 10.26 | yes | yes (the expected failing unit passed) |
| LC L30B | 38.92 | 4.65 | 10.86 | yes | yes (G23 below VINS-Mono alone) |
| C02 L30B | 37.39 | 21.70 | 22.22 | yes | yes (by 0.5 m) |

- **P1 survival: fails.** Prediction: G23 never makes a step above 5 m (9 of 9) and G20 breaks it in at least 7 of 9. As written, G23 passes 2 of 9 and G20 0 of 9. The rule as written is badly specified for this test: the gap step itself is legitimate motion (VINS-Mono carries 10-30 s, so 4 m to 48 m), which a 5 m step limit counts as a violation. Excluding the steps over a gap, G23 passes 7 of 9 and G20 6 of 9, but that variant hides G20's failure (G20 adopts the LiDAR jump *in* the gap step and then has a small step outside it). Neither version supports P1; the better statement is the ATE: below 10 m in 5 of 9 runs for G23 and 1 of 9 for G20.
- **P2 accuracy: holds, 4 of 5 units.** One-sided exact sign test p = 0.19: a trend, not significant (as stated in advance). The failing unit is Multi Floor 30 s, not Long Corridor 10 s as expected.
- **P3 against VINS-Mono alone: holds, 4 of 5 units**, two of them by very thin margins (MF L10B 0.001 m, C02 0.5 m). On Long Corridor 30 s G23 is below VINS-Mono alone (4.65 vs 5.43).
- **P4 no harm** was a check on logs (no fault: G23 equals G20 to 0.01 m on the 10 camera and no-fault logs of the first campaign), not repeated live.

Rule for use (protocol): P2 holds, so G23 is reported as the outage configuration, with the evidence being the second window set on seen bags, and with the Multi Floor 30 s failure stated.

## 3. Why Multi Floor 30 s fails (and what the rule cannot do)

On MF L30B, GenZ-LIO stays wrong for a long time after the gap in both G23 runs (alone: 16434 m in both, bit-identical across the replicates; in the G20 runs 88 m and 3840 m). While the LiDAR path is garbage, the VIO scale correction (LiDAR path / VINS path over 10 s) follows it: s_vio rises from 1 to 12-47 about 15 s after the gap, the consistency gate closes (gamma 0), the blow-up guard is off (it only runs while the VIO is trusted, and its buffers were cleared at the gap), and the fused steps reach 3-5 m per scan and later 3111 m. The gap step itself is handled correctly (32.5 m, VINS-Mono carries it). A diagnostic replay of the live G23 log with the scale correction switched off gives 13.5 m instead of 3258 m (diagnosis only, not a result).

## 4. Paired replay on the same front-end log (post-hoc supplement, not pre-registered)

Live runs confound the rule with GenZ-LIO's behaviour after a gap: GenZ-LIO alone differs between the G20 run and the G23 run of the same bag (for example MF L10B r1: 22612 m vs 21.5 m; the G23 runs reproduce each other exactly, 16434 m twice and 26.37 m twice, the G20 runs do not). It takes no fusion feedback, so the cause lies in the run (order: the G23 run is always the second on a bag, which the protocol did not randomise; not resolved). To separate the rule from the front end, the fusion core (without Channel T+) was replayed with gap_T = 0 and 1 s on all 18 logs, which fixes the front-end output:

| Log (front end of the ...) | G20 core | G23 core |
|---|---|---|
| MF L10B r1 (G20 run / G23 run) | 9167 / 21.1 | 1.21 / 2.40 |
| MF L10B r2 | 2161 / 2162 | 1.83 / 1.82 |
| MF L30B r1 | 88.3 / 3180 | 1.04 / 3258 |
| MF L30B r2 | 1408 / 3192 | 1101 / 3267 |
| LC L10B r1 | 6.80 / 7.30 | 2.91 / 6.68 |
| LC L10B r2 | 188 / 18.2 | 3.27 / 13.4 |
| LC L30B r1 | 40.2 / 26.5 | 7.00 / 6.53 |
| LC L30B r2 | 46.4 / 26.5 | 6.99 / 6.30 |
| C02 L30B r1 | 37.4 / 37.4 | 21.7 / 21.7 |

With the front-end output held fixed, the rule is lower by more than 10 % in 15 of 18 logs. The other three: the two Multi Floor 30 s logs of the G23 runs (3180 vs 3258, 3192 vs 3267; marginally higher) and LC L10B r1 of the G23 run (7.30 vs 6.68, 8 %, a tie). It lowers a 1408 m run only to 1101 m. Where GenZ-LIO recovers within seconds the rule gives 1-7 m; where it stays garbage for tens of seconds, nothing in the fusion helps. Replay omits Channel T+ (Long Corridor replay differs from live by up to 4 m, see the protocol), so this table is an indication, not a score.

## 5. Conclusions

1. The gap rule does what it was built for: it stops the fusion from adopting the LiDAR jump at re-entry. The first-campaign failure (G20 worse than VINS-Mono alone in 9 of 9) is reduced to 5 of 9 runs below 10 m for G23 against 1 of 9 for G20, and to 4 of 5 units within 2 x VINS-Mono alone.
2. It is not a full fix. The front end, not the fusion, produces the large errors after a gap (GenZ-LIO alone 9674-22612 m on MF L10B, 16434 m on MF L30B), and when its output stays wrong for tens of seconds the scale correction follows it. Long outages on Multi Floor are the failing case in both replicates.
3. Candidate for a next configuration (G24, not run, would need its own protocol and a third window set): a probation after a gap in which the scale is frozen at its pre-gap value and the LiDAR is re-admitted only when its path agrees with the VIO path. The 13.5 m diagnostic suggests where it would act; it has been seen on this bag, so it is post-hoc.
4. Limits: same bags and sensors, message deletion, window set 2 after window set 1 was used for development, order of G20 and G23 not randomised (G23 always second), live non-determinism of the front end, a survival rule that mis-handles the gap step.
