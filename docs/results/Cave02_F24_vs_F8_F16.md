# Cave02: where F24 (7.55) differs from the earlier F8 / F16 runs (4.3 to 5.1), from the logged runs (6 Nov 2026)

Offline, no new run. ATE RMSE per 120 s block of the same bag after one global Umeyama alignment per run; F8 / F16 = the nine-run control of 19 Oct (`Cave02_Control_Results.md`), F24 = run 1 of 4 Nov. All seven runs: VINS-Mono first pose at 71 s (F16 runs 1 and 3: 98 s), WARMUP 1174 to 1670 rows.

| Run | RMSE | 0-120 s | 120-240 | 240-360 | 360-480 | 480-600 | 600-720 | 720-840 | 840-960 |
|---|---|---|---|---|---|---|---|---|---|
| F8 run 1 / 2 / 3 | 4.71 / 4.31 / 4.40 | 6.9 / 5.5 / 6.3 | 6.4 / 5.6 / 5.5 | 4.6 / 4.1 / 4.2 | 2.2 / 1.8 / 2.2 | 3.0 / 3.3 / 3.0 | 4.5 / 4.8 / 4.5 | 4.8 / 4.8 / 4.7 | 3.3 / 3.2 / 3.3 |
| F16 run 1 / 2 / 3 | 3.97 / 5.10 / 4.11 | 4.1 / 8.7 / 4.4 | 5.3 / 6.3 / 5.6 | 4.0 / 4.5 / 4.2 | 1.9 / 2.2 / 1.9 | 3.1 / 3.1 / 3.2 | 4.7 / 4.6 / 4.8 | 4.4 / 5.0 / 4.5 | 3.1 / 3.5 / 3.2 |
| **F24 run 1** | **7.55** | **12.0** | **12.1** | 5.9 | 5.1 | 5.0 | 4.9 | 5.3 | 5.1 |

- **The gap is in the first 240 s**: F24 12.0 and 12.1 against 4.1 to 8.7 and 5.3 to 6.4 in the six earlier runs. From 240 s on F24 is 5.0 to 5.9, the earlier runs 1.8 to 4.8; the shape over time is the same.
- **That stretch is LiDAR-only in every run** (VINS first pose at 71 s, warm-up to about 130 s or more, W = I), so the fusion additions of F20 to F24 do not act there. The difference is in A-LOAM's first minutes (run-to-run, or a change in the stack since 19 Oct); six earlier runs are all below F24's 12.0, which a single draw does not explain well.
- **During those minutes F24, F8 and F16 all hand A-LOAM a no-motion guess** when VINS is absent (the fault behind F26 / F27).
- **Next, not run:** one F16 run and one F23 run on Cave02 with the current code (about 72 min) separates "F24 regressed" from "the stack or the draw changed since 19 Oct". Command: `ONLY=CAVE CFGS="F16 F23" REPEAT=1 bash batches/switchslam_exact_batch.sh`.
