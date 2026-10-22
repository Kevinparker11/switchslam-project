# VINS-LiDAR consistency study (22 Oct 2026)

Exact offline replays of recorded GenZ-stack logs for G17 (R/T Schur weights + SAH), G18 (+ VINS scale-consistency gate),
G19 (+ online VINS scale correction) and SAH only. Results: `docs/results/GenZ_fusion_v4_VIO_Consistency_Results.md`,
raw outputs: `results_data/2026-10-22/vio_consistency/`.

| Script | Purpose |
|---|---|
| `logs.py` | the ten recordings (edit paths for your machine) |
| `harness.py` | replay with `fusion_v4/fusion_core.py` + SAH (`sah/sah_replay3.py`, `sah/sheading.py`) |
| `base_configs.py NAME` | live / GenZ alone / VINS alone / G9 / G17 / SAH only |
| `calibrate_reference.py NAME`, `segment_stat.py NAME` | the consistency statistics on each log (threshold = max on Multi Floor) |
| `eval_gates.py`, `eval_two_timescale.py`, `eval_scale_correction.py`, `eval_scale_projected.py` | the variants compared (all reported) |
| `make_backend_log.py NAME CFG`, `backend_job.sh NAME CFG` | write the replayed trajectory into a log copy and run the loop-closure back end on it |
| `make_table.py` | the summary table (run in the folder holding the json outputs) |
| `segment_timeline.py`, `geode_window_diag.py` | GEODE diagnostics (VINS agrees for 30 s, then its scale drifts) |

Run each script as `python3 -I script.py NAME` (NAME from `logs.py`); one process per log, because the extrinsics are read
at import time from `EXTRINSIC_YAML`.
