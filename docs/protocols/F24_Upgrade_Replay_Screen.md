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
