# Handheld (LVI-SAM dataset): F5, F26, F35 and SW replays, rules written before any run (11 Nov 2026)

## What is run
The bag `laptop_bags/handheld/handheld.bag` (1,642.9 s, 10.3 GB; /points_raw 9.9 Hz, /imu_raw 500 Hz, compressed mono camera 30 Hz, /gps/fix 5 Hz). Replay at 0.5x, front end A-LOAM + VINS-Mono (`FRONT=aloam`), config names of `run_fusion_study.sh`: F5 (unfed A-LOAM), F26 (final version), F35, SW (exact Switch-SLAM replica). Setup by `fusion_v4/handheld/setup_handheld.sh` (LVI-SAM's published VINS-Mono config and extrinsics, nothing tuned; the compressed camera is republished to raw in the VINS container; A-LOAM reads /points_raw). F20 was already run on this bag on 30 Oct (19.30 / 70.55 m, Handheld_Readiness.md).

## Scoring (fixed now)
Horizontal ATE only, against the GPS reference of `make_gps_reference.py` (drop fixes with status < 0 or horizontal variance above 1.0 m^2; no smoothing), 2-D rigid fit without scale, full span, log poses inside reference gaps above 1 s left out and counted (`handheld/score_run_xy.py`). Fused output, the A-LOAM output of the same log and VINS-Mono alone are all scored. Not like for like with the paper's 3.07 / 1.25 (max / RMSE): the paper does not state its reference, the part of the bag or the dimension of the error.

## Reading rules
1. **Precondition per run.** At least 5,000 log rows, VINS-Mono poses present, FUSED rows present (smoke run of 160 s first: VINS-Mono from about 20 s, FUSED about 20 s later). Otherwise the run is void, reported, and repeated with the same settings.
2. **Failure label.** A run counts as failed if its fused horizontal RMSE is above 10 m (the 10 m success threshold of the report's success-rate table). The number is always shown next to the label.
3. **Tie band.** max(1.0 m, 10 %) of the reference value. F26 against F20's 19.30 m: lower only if below 17.4 m; higher only if above 21.2 m. F35 against F26: the same band on F26's RMSE. One run each supports no claim; F26 stays the final version whatever F35 does.
4. **Always reported.** Fused, A-LOAM and VINS-Mono RMSE / max; modes (FUSED / WARMUP / VO_FAIL); guess kinds for F26, F35; rule firing share for SW; reference rows dropped and poses left out.
5. **Repeats.** One run each first (about 3.7 h for the four). Two more runs of F26 and F35 each only if their difference lies inside the tie band.
6. **Held out.** F26 and F35 were fixed before this bag was scored by them. F20 had been seen on it (30 Oct). No setting is changed after a score; failed or void runs are reported, not adjusted.
7. The Handheld comparison with the paper goes into the report as a footnoted row ("our reference: GPS, horizontal; paper's reference not stated"), with failures shown as numbers plus the label.

## Commands
```
cd ~/switchslam-project && git fetch origin && git checkout --detach origin/f22-handover
cd fusion_v4 && ./handheld/setup_handheld.sh ~/handheld_gps_xy_clean.txt
SEQ_ENV=~/runs_handheld/seq.env SMOKE=1 SMOKE_SECS=160 FRONT=aloam PLAY_RATE=0.5 ./run_fusion_study.sh F26
setsid nohup systemd-inhibit --what=sleep:idle env SEQ_ENV=$HOME/runs_handheld/seq.env FRONT=aloam PLAY_RATE=0.5 REPEAT=1 ./run_fusion_study.sh F5 F26 F35 SW > ~/runs_handheld/batch.log 2>&1 < /dev/null & disown
cd ~ && zip -r handheld_runs.zip runs_handheld -x "runs_handheld/aloam_*" -x "runs_handheld/player_*"
```
