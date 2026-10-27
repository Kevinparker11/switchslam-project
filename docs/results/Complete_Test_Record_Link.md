# Complete test record (updated 19 Oct 2026)

The full compiled record of every test, from the first synthetic checks to the six-run F16 batch, is the doc "SwitchSLAM QR — Complete Test Record":
https://claude.ai/code/artifact/3b5f9cdd-de1d-428b-a5c4-07bde3af30cc

It covers 18 phases with parameters, platform, replay rate, run counts, time, expected vs obtained results, a master results table, comparisons with published values, withdrawn claims and pending tests. Phase 16 (18 Oct) holds the Corridor02 F16 runs and the Long Corridor run 3 check; Phase 17 (19 Oct) the SuperLoc verification, near-range filter study and per-time error; Phase 18 (19 Oct) the six-run results, the matched Multi Floor control and the Corridor02 loop check.

Headline numbers (ATE RMSE, m):
- Multi Floor: F8 front end 0.617 ± 0.107 (9 runs, 1.0x); matched F8 0.603 ± 0.112 (3, 0.5x); F16 0.640 ± 0.115 (6, 0.5x) = no SAH effect; F8 + loops 0.347 ± 0.036 (6, 1.0x); F16 + loops 0.523 ± 0.224 (6, 0.5x).
- Long Corridor: F8 4.53 ± 0.49; F8 + loops 2.67 ± 0.73; F16 2.27 ± 0.45 (6, 0.5x); F16 + loops 1.538 ± 0.304 (6). Switch-SLAM 2.42, challenge best 1.254, LODESTAR 1.386, SuperLoc 0.817.
- Corridor02: F8 2.12 ± 0.06; F14 1.74; F16 1.708 ± 0.069 (6, 0.33x); F16 + loops 1.250 ± 0.435 (6; the gain appears only in the 4 runs that accepted one long start-end loop).

Details of the F16 live results, the run 3 diagnosis and the Corridor02 loop check: `claude/SAH_Live_Results_F16.md`.
