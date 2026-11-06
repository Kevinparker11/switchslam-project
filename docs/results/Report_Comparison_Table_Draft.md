# DRAFT: comparison with Switch-SLAM, front end only, A-LOAM + VINS-Mono (6 Nov 2026)

Source data for the report's comparison tables (Tables 5.2 and 5.7 in the numbering of the draft report; check the numbering before pasting). ATE RMSE / max in m, Umeyama SE(3), no scale, full span, no loop closure, laptop, settings frozen. `n` = number of runs. Cells marked **[PENDING]** have no result yet. No F12 anywhere. Every value is copied from a results_index.csv, a printed score or a Project doc named in the last column.

| Sequence | Switch-SLAM published (mean of 3) | Our Switch-SLAM, SW (paper rule) | Our Switch-SLAM + gyro, SWI | F24 (this thesis) | Source |
|---|---|---|---|---|---|
| Multi Floor | 1.61 / 3.63 | 5.03 / 10.22, 5.44 / 10.94 (n=2) | 1.51 / 4.35 (n=1) | 0.45 / 0.92 (n=1) | SwitchSLAM_Exact_Replica s.11, 13, 17; F24 batch 3 Nov |
| Long Corridor | 2.42 / 5.09 | 12.58 / 23.53, 13.12 / 23.46 (n=2) | 13.81 / 24.78, 13.24 / 24.39 (n=2) | 2.12 / 5.31, 2.15 / 5.57, 1.75 / 3.53 (n=3, mean 2.01) | same, s.14, 17 |
| Farm (Gazebo L route) | 0.38 / 1.10 (generation-1 node v9, final A-LOAM-refined output, n=3: 0.32, 0.44, 0.48; mean 0.41 / 1.47; unfed A-LOAM 0.478, see Farm_L_Shape_Test_Protocol correction) | 81.16 (n=1, cause not found) | **[PENDING]** | 0.657 / 0.897 (n=1, sideways-camera rig); 0.472 / 1.068 (n=1, forward RGB 60 Hz camera, paper sensors; VINS alone 14.47, Farm_Forward_Camera_Test.md); 0.255 / 0.568 (n=1, forward grey 20 Hz camera rig, NOT the paper's RGB 60 Hz configuration, Farm_Forward_Camera_Test.md) | Farm docs; F24_Predict_Guard s.5 |
| Corridor02 | no published value | **[PENDING]** | **[PENDING]** | 1.47 / 2.51 (n=1, development data) | F24_Live_Corridor02_Cave02_GEODE |
| Cave02 | no published value | **[PENDING]** | **[PENDING]** | 7.55 / 12.63 (n=1, flagged: earlier F8/F16 4.4); F26 6.23 / 10.56, F27 6.62 / 11.21 (n=1 each, development variants) | same |
| GEODE stairs alpha | no published value | **[PENDING]** | **[PENDING]** | 6.15 / 14.00, 9.15 / 25.44 (0.5x), 9.09 / 19.42 (0.25x) (n=3) | same; F25_Fixes s.5, 6 |

## Reading (what can be said)
1. **Replication.** SW and SWI do not reproduce the published level on Long Corridor (13 m against 2.42, two runs each) or SW on Multi Floor (5.0 to 5.4 against 1.61). SWI on Multi Floor is close in one run, which is not a reproduction claim. Not isolated: stack differences D1 to D5 and unspecified parameters A1 to A8.
2. **F24 against the published numbers.** Better on Multi Floor (0.45 against 1.61) and Long Corridor RMSE (mean 2.01 against 2.42; max 3.53 to 5.57 against 5.09, two of three runs above). Farm: max inside 1.10, RMSE 0.657 above 0.38. F20, F21, F24 were designed on these sequences: they are not held-out.
3. **Where F24 is weak.** Cave02 and GEODE (A-LOAM + VINS-Mono limit). Published methods on GEODE alpha: COIN-LIO not run, FAST-LIO2 4.69, DLIO 4.89, R3LIVE 4.54, LIO-SAM 6.30, RELEAD 0.57; Cave02 (SuperLoc release): iG-LIO 0.43, GenZ-LIO 0.44, DLIO 0.57, Faster-LIO 0.81, FAST-LIO2 4.49, Point-LIO 6.57. Different metrics and sensors; context only.
4. **Tried and not adopted** (F25_Fixes.md): handover trust (no gain), standstill hold (hypothesis wrong), slower replay (no gain), loop closure on these two bags (no gain).
5. **Pending runs** (batches/both_tests.sh): F26 (paper's guess rule) on GEODE, Cave02, Multi Floor, Long Corridor; F27 (A-LOAM increment instead of a no-motion guess) on GEODE and Cave02.
