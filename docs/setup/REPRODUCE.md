# Reproducing the studies

Prerequisites: [INSTALL.md](INSTALL.md) (environment) and [DATASETS.md](DATASETS.md) (bags and ground truth in place). All commands run on the host from `~/switchslam_channelT/fusion_v4/` (a copy of this repository's `fusion_v4/`; the folder is self-contained). Configuration names (F0-F16, G0-G17) are defined in [`docs/results/Configurations_Explained_and_Results_To_Date.md`](../results/Configurations_Explained_and_Results_To_Date.md).

Rules the study follows (do not break them when repeating it): settings are frozen before a sequence is run; Multi Floor is the only tuning sequence for the GenZ weights; held-out sequences are never used to adjust a setting; every result is mean ± sd over repeated live runs with the full-span ATE.

## 0. One-time preparation
```bash
mkdir -p ~/switchslam_channelT && cp -r <repo>/fusion_v4 ~/switchslam_channelT/
cd ~/switchslam_channelT/fusion_v4
bash clean_restart.sh                      # restarts both containers: guarantees no leftover ROS processes
bash genz/install_genz.sh 2>&1 | tee ~/install_genz.log      # only for the GenZ stack
```
`run_fusion_study.sh` restarts the containers itself before every run.

## 1. Run controls (environment variables of `run_fusion_study.sh`)

| Variable | Meaning |
|---|---|
| `FRONT=aloam` / `genz` | master A-LOAM stack (F configs) / GenZ-LIO stack (G configs, default). Results go to `<OUT_DIR>` / `<OUT_DIR>_genz` |
| `SEQ_ENV=~/runs_<name>/seq.env` | a sequence other than Multi Floor |
| `REPEAT=n` | n live repeats per configuration (tags `<cfg>_run<k>`) |
| `RECORD_KF=1` | also save keyframe scans (`keyframes_<cfg>_kf_run<k>.npz`, needed for loop closure and SAH replays; tag becomes `<cfg>_kf_run<k>`) |
| `PLAY_RATE=r` | replay the bag at r x real time (slower = no dropped scans/frames) |
| `SMOKE=1 [SMOKE_SECS=n]` | short run, no scoring, tag `SMOKE_...` |
| `BAGS_ROOT`, `BAG_DIR_OVERRIDE` | where the bags are |
| `GENZ_C_T`, `GENZ_C_R`, `GENZ_C_T_F8` | frozen GenZ weights (defaults 3e-6, 5e-6, 1e-4 — chosen on Multi Floor only) |

The script appends one line per finished run to `results_index.csv` (`tag,config,rows,ate_full_rmse,ate_full_max,finished`) and skips tags already present, so an interrupted batch can simply be restarted. Long batches should be detached from the terminal:
```bash
setsid nohup systemd-inhibit --what=sleep:idle ./run_fusion_study.sh ... > ~/batch.log 2>&1 < /dev/null &
```

## 2. Setting up a sequence
```bash
# SubT-MRS sequences: needs the published Intrinsics/Extrinsics yaml and the ground truth
./setup_sequence.sh cave02 "<bag folder>" <Intrinsics.yaml> <Extrinsics.yaml> <ground truth>
# GEODE stairs (device alpha)
bash geode/setup_geode.sh "<path to GEODE>/stairs_alpha.txt"
```
Both write `~/runs_<name>/seq.env`, copy the generated VINS-Mono config, A-LOAM launch and extrinsics into the containers, and check the ground truth against the bag time span. Then a smoke test: `SEQ_ENV=~/runs_<name>/seq.env SMOKE=1 SMOKE_SECS=160 FRONT=aloam ./run_fusion_study.sh F8`.

## 3. What was run for each result

| Result | Command |
|---|---|
| Multi Floor F0-F5, F8, F16 (A-LOAM) | `REPEAT=3 RECORD_KF=1 FRONT=aloam ./run_fusion_study.sh F0 F5 F8 F16` (1.0x for the nine F8 runs; `PLAY_RATE=0.5` for F16 and the matched F8) |
| Long Corridor F8/F16 | `SEQ_ENV=~/runs_corridor/seq.env REPEAT=3 RECORD_KF=1 PLAY_RATE=0.5 FRONT=aloam ./run_fusion_study.sh F8 F16` |
| Corridor02 F8/F16 | `SEQ_ENV=~/runs_corridor2/seq.env REPEAT=3 RECORD_KF=1 PLAY_RATE=0.33 FRONT=aloam ./run_fusion_study.sh F8 F16` |
| Cave02 F8/F16 | `SEQ_ENV=~/runs_cave02/seq.env REPEAT=3 RECORD_KF=1 PLAY_RATE=0.5 FRONT=aloam ./run_fusion_study.sh F8 F16` |
| GenZ-LIO alone on Multi Floor | `REPEAT=3 RECORD_KF=1 FRONT=genz ./run_fusion_study.sh G0` |
| Weight choice on Multi Floor (replay) | `python3 genz/calibrate_genz_c.py ...` on the G0 logs (see `docs/results/GenZ_fusion_v4_MultiFloor_Results.md`) |
| Full GenZ system live | `FRONT=genz RECORD_KF=1 ./run_fusion_study.sh G17` (add `SEQ_ENV=...` for other sequences) |
| GEODE, master | `SEQ_ENV=~/runs_geode/seq.env REPEAT=3 RECORD_KF=1 PLAY_RATE=0.5 FRONT=aloam ./run_fusion_study.sh F0 F5 F16` |
| GEODE, GenZ | `SEQ_ENV=~/runs_geode/seq.env REPEAT=3 RECORD_KF=1 PLAY_RATE=0.5 FRONT=genz ./run_fusion_study.sh G0 G17` |

(The commands for the master results are reconstructed from the run logs and the script defaults of the time; the replay rates are the ones recorded in the result documents. When in doubt, the `results_index.csv` and `node_*.out` of a run record its exact settings.)

## 4. Scoring and ablations of a finished run
```bash
python3 score_run.py --gt <ground truth> --log ~/runs_<name>/switching_log_v2_<tag>.csv        # full-span ATE
python3 fusion_summary.py --log <log> --gt <gt> --c-t 0.03                                     # paired replays: VINS-only, LiDAR-only, own setting
python3 align_gt_time.py --gt <gt> --seq-env ~/runs_<name>/seq.env --logs <log> [--check-only]   # only if GT and bag clocks disagree
```

## 5. Loop closure (offline back end; needs `pip install gtsam`)
```bash
python3 run_backend.py --log switching_log_v2_F16_kf_run1.csv --kf keyframes_F16_kf_run1.npz --gt <gt> \
        --models iso --odom-sigma auto
```
Settings used in all reported "+ loops" results: LIO-SAM-style isotropic loop weights, one search round, loop radius 8 m, minimum gap 30 s, ICP fitness >= 0.6 and RMSE <= 0.08, maximum correction 15 deg / 4.0 m, odometry noise measured on the calibration segment (`--odom-sigma auto`).

## 6. Statistics and analysis scripts
`analysis/improve/stats_tests.py` reproduces `docs/results/Statistical_Tests_Multiple_Runs.md`. The scripts in `analysis/improve/` and `sah/` are research scripts written in a working directory: they read staged logs from fixed locations (`/tmp/claude-0/...`, `/home/claude/data_in*`) and ground truth from the upload folder. To reuse them, edit the paths at the top of each script to your `~/runs_*` folders. They import the modules of `fusion_v3/` (`v2_tools.py`, `fusion_core.py`, `structure_heading.py`, `backend_*.py`) — run them with that folder on `PYTHONPATH`.

## 7. Unit tests
```bash
cd fusion_v4
python3 -m pytest -q test_fusion_core.py test_recorder.py tests_v4/test_lio_bridge.py     # 8 tests, about 1 s (ROS is stubbed)
python3 -m pytest -q test_backend.py test_backend_cli.py                                   # needs gtsam; takes minutes
```
These check the code, not the evidence.
