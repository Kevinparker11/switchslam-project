# Universal-fix study (24 Oct 2026)

Exact offline replays of fusion configurations on every recorded GenZ-stack run (33 recordings, `logs_all.py`; edit the paths
for your machine). Result write-up: `docs/results/GenZ_fusion_v4_G20_Universal_Fix.md`; tables: `results_data/2026-10-24/`.

| Script | Purpose |
|---|---|
| `rep.py <log> <cfg>...` | replay configurations (from `configs.py`) on one recording, write `out/<log>__<cfg>.json` |
| `table.py [cfgs]` | per-recording table and per-sequence medians |
| `configs.py` | G17-G20 and every candidate tried (U0-U3, L10/L30, A*, G19p, F*, K*, G20f) |
| `calib_debias.py`, `calib_recent.py` | Multi Floor calibration of the de-biased and fast check references |
| `diag_scale.py`, `diag_speed.py`, `diag_err.py` | ground-truth diagnosis (scale, speed, heading); not used by any configuration |
| `diag_gate.py`, `diag_guard.py` | gate timeline; LiDAR-minus-VINS excess on healthy runs and on the GenZ divergence |
| `mk_bk.py`, `bk_job.sh` | replayed trajectory -> loop-closure back end (`fusion_v4/run_backend.py`) |

Run everything: `cat names.txt | xargs -P2 -I{} python3 rep.py {} GZ G17 G18 G19 G20` then `python3 table.py GZ,G17,G18,G19,G20`.
