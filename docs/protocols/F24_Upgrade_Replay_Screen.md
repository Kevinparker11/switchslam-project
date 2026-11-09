# F24 upgrade screen: offline replay of F24 variants on saved logs (rules written 9 Nov 2026, before any variant was replayed)

Aim: lower error on Cave02 (and GEODE) while keeping every F24 addition. Diagnosis (`Cave02_GEODE_Error_Diagnosis.md`, `fusion_core.py` VioConsistency): F24's VIO check compares the VINS displacement scale with the LiDAR displacement scale (r = sqrt(mean ln(|dv|/|da|)^2) over 10 s windows, gate ref 0.157). On Cave02 VINS-Mono is about 22 to 28 % too long (Umeyama scale 0.76 to 0.78), so r > ref and VINS is distrusted (vio_gamma = 0) from about 250 s to the end, including the stretch where the LiDAR stalls. The same check also judges VINS against a stalled LiDAR.

Method: `fusion_v4/ot_study/node_harness.py` drives the real fusion node with the logged run (open loop: A-LOAM's output is the logged one, so the effect of a changed guess is not tested). The base replay reproduces the live Cave02 run 1 exactly (7.55 / 12.63). Logs: the saved F24 runs (Cave02 x3, GEODE x4, Corridor02 x3 including the failed run 2, Long Corridor x3). Multi Floor is not screened (ground truth not at hand).

Variants (existing node options only, each added to F24):
- A: VIO_SCALE_T=10 (VINS translation rescaled by the LiDAR / VINS path-length ratio)
- B: VIO_CHECK_PROJ=1 (VINS judged only along directions the LiDAR supports)
- C: A + B
- D: VIO_CHECK_REF=0.35 (looser consistency gate, covers about 40 % scale error)
- E: A + D

Rules:
1. A variant goes forward to a live test only if (a) Cave02 median RMSE is more than 1.0 m below the F24 replay median (spread of F24 on Cave02 is 0.5 m), and (b) Corridor02 runs 1 and 3 and Long Corridor means are not worse than F24 by more than 0.05 m (the no-regression bound used in F24_Predict_Guard.md), and (c) GEODE median is not worse than F24's by more than 1.0 m.
2. Replay is a screen, not a result. A passing variant needs live runs (Cave02 x3, then the other bags) and then bags it has not seen, because Cave02 and GEODE are the bags it was chosen on.
3. Known from F24_Predict_Guard.md section 6: VIO_SCALE_T (variant A and its relatives) improved the Farm log but violated bound (b) on Corridor02 (1.569 to 2.154). That result stands unless this screen differs; it is reported next to the new numbers.
4. The failed Corridor02 run 2 is reported separately (whether any variant changes it), not mixed into the means.
5. All variants are reported, passing or not.

## Results (9 Nov 2026, replay; RMSE in m per saved F24 run; median in brackets)
| Variant | Cave02 x3 | GEODE x4 | Corridor02 x3 (run 2 = the failed run) | Long Corridor x3 |
|---|---|---|---|---|
| base (F24) | 7.55 7.08 7.11 (7.11) | 6.16 9.15 7.06 6.56 (6.81) | 1.48 104.00 1.29 | 2.13 2.16 1.76 (2.13) |
| A: VIO_SCALE_T=10 | 7.57 7.11 7.13 (7.13) | 6.15 9.09 7.10 6.55 (6.83) | 1.93 104.92 1.99 | 2.00 1.95 1.79 (1.95) |
| B: VIO_CHECK_PROJ=1 | 7.56 7.09 7.12 (7.12) | 6.15 9.15 7.05 6.55 (6.80) | 1.46 104.02 1.31 | 2.13 2.16 1.76 (2.13) |
| C: A + B | 7.66 7.18 7.21 (7.21) | 6.18 9.11 7.07 6.57 (6.82) | 1.20 105.60 1.22 | 1.72 1.76 1.12 (1.72) |
| D: VIO_CHECK_REF=0.35 | 6.78 6.28 6.32 (6.32) | 6.16 9.15 7.06 6.55 (6.80) | 1.48 104.00 1.29 | 2.13 2.16 1.76 (2.13) |
| E: A + D | 7.15 6.65 6.70 (6.70) | 6.15 9.09 7.11 6.54 (6.82) | 1.93 104.92 1.99 | 2.00 1.95 1.79 (1.95) |
The base replay reproduces all 13 live runs to within 0.01 m.

Reading against rules 1 to 5:
- **No variant passes rule 1.** Closest is D: Cave02 median 6.32, which is 0.79 m below the base (needs more than 1.0 m), with no change on GEODE, Corridor02 or Long Corridor (identical to the base to 0.01 m). Fails (a) by 0.2 m.
- A fails (a) and (b): Cave02 unchanged, Corridor02 good runs worse by 0.45 and 0.70 m, consistent with F24_Predict_Guard.md section 6. B changes nothing. E fails (b).
- C does not help Cave02 (7.21, slightly worse) but is lower on the corridors: Corridor02 good runs 1.20 and 1.22 against 1.48 and 1.29, Long Corridor mean 1.53 against 2.02. Those are design bags, the replay is open loop, and C was not chosen in advance for them, so this is a note, not a result.
- The failed Corridor02 run 2 stays at 104 to 106 m under every variant (the wrong turn is in A-LOAM's own output, which the replay cannot change).
- Why the gain on Cave02 is small: even with VINS trusted (D), most of the error sits in the first 300 s and in the A-LOAM stall, which is the logged A-LOAM output and not changed by any of these options.
- Conclusion: no existing F24 option takes Cave02 to 1 to 2 m. Reaching it would need a new mechanism for the A-LOAM stall and for the VINS scale, not a flag change. D is the only option with a visible, side-effect-free gain (about 0.8 m), but its value 0.35 was set from Cave02's VINS scale error (ln(1/0.78) = 0.25), so it is tuned on the bag it improves.
