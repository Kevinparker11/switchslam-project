# Least-error 4-hour queue on Cave02 and GEODE: rules fixed before the runs (9 Nov 2026)

Why: F24 on Cave02 is 7.08 to 7.55 (n=3) and on GEODE 6.15 to 9.15 (n=4). Offline diagnosis (`Cave02_GEODE_Error_Diagnosis.md`): the Cave02 error sits in the first 300 s (accurate after: 0.7 m per segment), where VINS is absent or distrusted; GEODE fused equals A-LOAM because VINS fails. The earlier F8 / F16 runs on Cave02 (19 Oct) were 3.97 to 5.10.

## Runs (0.5x replay, same bags, same extrinsics, same scorer; front end only)
| Bag | Config | Meaning | Runs | Time |
|---|---|---|---|---|
| Cave02 | F16 | Schur T + SAH, none of the F17 to F24 additions (control for the 19 Oct result) | 1 | about 36 min |
| Cave02 | F23 | F24 without PREDICT_GUARD (matched control for F24) | 1 | about 36 min |
| Cave02 | F28 | F16 + A-LOAM's own guess chosen by Switch-SLAM's rule (`GUESS_MODE=status`) | 1 | about 36 min |
| Cave02 | F29 | F16 + A-LOAM's own increment when the VINS motion is unusable (`GUESS_MODE=vins_odom`) | 1 | about 36 min |
| GEODE | F16, F28, F29 | same three | 2 each | about 13 min each |
Total about 3 h 50 min. F28 and F29 are new combinations of existing code (`run_fusion_study.sh` entries only; no node change).

## Reading rules
1. **Regression question (Cave02).** F16 RMSE <= 5.1 and F23 >= 7.0: the F17 to F23 additions cost about 2 m on Cave02. F16 >= 6.5: the stack or the run draw changed since 19 Oct; the additions are not the cause. Anything between: not decided.
2. **Guess question (Cave02).** F28 or F29 counts as better than F16 only if its RMSE is more than 1.1 m lower (F16's own earlier spread, 3.97 to 5.10). One run each: smaller gaps are noise.
3. **GEODE.** The F24 spread is 3.0 m (6.15 to 9.15), so no difference below 3.0 m between two configurations is claimed. GEODE is read only as a check that F16, F28 and F29 are not worse than the F24 range.
4. **Least error.** The lowest Cave02 RMSE among F16, F23, F28, F29 is reported as the lowest in this queue, with the other values next to it. It is a development result: Cave02 and GEODE are the bags these variants were chosen on.
5. **Adoption.** Nothing here changes the frozen F24 or the Table II comparison. A variant is adopted only after a confirmation on bags it has not seen (SubT-MRS Cave01, 03, 04; other GEODE sequences) with a rule written first.
6. Failed runs count as runs. Settings are not changed between runs.
7. Not expected to reach 1 to 2 m. The target is stated in the diagnosis as plausible on Cave02 and doubtful on GEODE; this queue only finds the best existing configuration.
