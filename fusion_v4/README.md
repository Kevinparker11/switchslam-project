# fusion_v3: VIO-primary front end + degeneracy-aware loop-closure back end

v3 keeps everything in v2 (same node, same batch script, same containers) and adds:

| File | What it is |
|---|---|
| `keyframe_recorder.py` | ROS node, runs next to the fusion node when `RECORD_KF=1`: saves a body-frame scan every 1 m / 0.2 rad (`keyframes_<tag>.npz`, ~10-20 MB per Multi Floor run). Publishes nothing. |
| `backend_icp.py` | point-to-plane ICP that returns its information matrix; Schur blocks; loop-factor information models |
| `backend_graph.py` | loop search, verification, GTSAM pose graph (Huber + chi2 pruning), odometry-noise calibration on bag 0 |
| `run_backend.py` | runs the back end on one recorded run and prints the ablation table (ATE full span, bag 0, bags 1-2) |
| `test_backend.py`, `backend_synth.py` | synthetic room + corridor tests (code checks, not evidence) |
| `test_recorder.py` | recorder test with stubbed ROS messages |
| `calibrate_c.py` | now also searches the LiDAR rotation weight (`--c-r-grid`) |
| `run_fusion_study.sh` | adds `RECORD_KF=1` (tag `<cfg>_kf_run<n>`) and config F6 (`C_T` + `C_R`) |

Loop-factor models compared by `run_backend.py`:

| Model | Loop information |
|---|---|
| `none` | no loops (the front end alone) |
| `iso` | LIO-SAM style: variance = ICP fitness score on all six axes |
| `hessian` | ICP Hessian / residual variance, inflated x10, with a 0.5 deg / 5 cm floor |
| `schur` | `hessian`, with information removed along Schur eigen-directions weaker than 5% of their block |
| `schur_otsu` | as `schur`, but the cut comes from Otsu on this run's own loop condition numbers (label-free) |
| `schur_gate` | `schur_otsu`, and loops with a rotation condition number above the Otsu cut are rejected |

## Steps

```bash
# 0. unpack next to v2; results keep going to ~/runs_v2 (same index, same repeat guard)
cd ~/switchslam_channelT && unzip -o ~/Downloads/fusion_v3.zip && cd fusion_v3 && chmod +x run_fusion_study.sh
pip3 install --user scipy pandas                 # add --break-system-packages if pip refuses
python3 test_fusion_core.py                      # ALL TESTS PASSED
python3 test_recorder.py                         # ALL RECORDER TESTS PASSED

# 1. one recording run of F7 (no gate, C_T = 0.01) (about 8 min)
RECORD_KF=1 ./run_fusion_study.sh F7
#    -> ~/runs_v2/keyframes_F7_kf_run1.npz and ~/runs_v2/switching_log_v2_F7_kf_run1.csv

# 2. pack what Claude needs (batch results + the recording run)
cd ~/runs_v2 && zip -j ~/Downloads/for_claude.zip results_index.csv summary_*.txt \
   switching_log_v2_F0_run1.csv switching_log_v2_F1_run1.csv \
   switching_log_v2_F7_kf_run1.csv keyframes_F7_kf_run1.npz
ls -lh ~/Downloads/for_claude.zip                # attach this file in the chat

# 3. optional: run the back end yourself
pip3 install --user gtsam
python3 run_backend.py --log ~/runs_v2/switching_log_v2_F7_kf_run1.csv \
    --kf ~/runs_v2/keyframes_F7_kf_run1.npz \
    --gt ~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv
```

If the zip is too large to attach, leave out the two `switching_log_v2_F0/F1_run1.csv` files first.

## Added 14 Oct 2026: weighting ablation, Long Corridor tooling

**Weighting ablation (live, Multi Floor).** fusion_node_v2 reads `WEIGHT_MODE` (default `schur` = our method):
`iso` isotropic, `const` fixed blend, `proj` per-direction 0/1, `switch_ss` hard switch with the Switch-SLAM rule,
`switch_kR` hard switch on kappa(S_RR), `lidar` W = I, `vins` W = 0, `diag` diagonal block H_tt. Configs F11-F15 in the runner.
Offline paired replay of the same comparison: `python3 ablation_weights.py --gt GT --out ablation.csv LOG1.csv LOG2.csv ...`

**A new SubT-MRS sequence (e.g. Long Corridor).**
1. `./setup_sequence.sh corridor ~/Downloads/SubT_MRS_Hawkins_Long_Corridor_RC <Intrinsics.yaml> <Extrinsics.yaml> corridor01_gt.txt`
   (reads topics and time span, writes the VINS-Mono config with make_vins_config.py, launch files, ~/runs_corridor/seq.env,
   and checks the ground truth overlaps the bag)
2. Smoke: `SEQ_ENV=~/runs_corridor/seq.env SMOKE=1 ./run_fusion_study.sh F8`
3. Runs: `SEQ_ENV=~/runs_corridor/seq.env REPEAT=3 RECORD_KF=1 ./run_fusion_study.sh F0 F8`
4. Back end with everything frozen from Multi Floor:
   `EXTRINSIC_YAML=~/runs_corridor/corridor_extrinsics.yaml python3 backend_multi.py --dir ~/runs_corridor --tags F8_kf_run1,F8_kf_run2,F8_kf_run3 --gt corridor01_gt.txt --models none,iso --extra "--odom-sigma 1.46,0.054 --calib-end 0"`
Other tools: `compare_gt.py A B` (two ground truths of one recording), `score_run.py` (ATE for any csv/TUM ground truth).

## Which clock? (Long Corridor)

`rosbag info` shows the time the bag was RECORDED (1690254112, July 2023). The nodes and the logs use the message
HEADER stamps, and in the Long Corridor bag those are on the sensors' own clock (1517157219, January 2018):

    /imu/data            record 1690254112.822   header 1517157219.159
    /camera_1/image_raw  record 1690254112.836   header 1517157219.043
    /velodyne_packets    record 1690254112.847   header 1517157219.088

`corridor01_gt.txt` (1517157219.8 .. 1517157499.0) is on the header clock, so it overlaps the logs directly and
needs no shift. Always compare a ground truth with the header clock, never with the record times.
`setup_sequence.sh` now reads the first header stamps from the bag and uses them for the ground-truth check.

If a ground truth is really on another clock, `align_gt_time.py` finds the shift: it correlates the rotation speed
of the GT with that of the VINS-Mono and A-LOAM rotations in a log (frame-, drift- and fusion-independent),
cross-checks with ATE-minimising offsets, and refuses to write a file if the sources disagree by more than 0.3 s.
`--check-only` reports the shift without writing (0 = already aligned). `--bag-start` defaults to the first time in
the logs. Self-tests on Multi Floor: shifted by +4.00 s -> +4.00/+4.02 s recovered; already aligned -> +0.01 s.

## Structure-anchored heading (SAH), 17 October 2026
`structure_heading.py` + `SAH=1` in fusion_node_v2 (config F16 = F8 + SAH). At every keyframe (1 m / 0.2 rad of
scan-to-map motion) the registered scan's vertical-wall directions are compared with a learned direction
reference; the heading correction is applied gradually (0.25 deg per scan). Self-disabling where there is no
structure; numpy-only (scipy used if present). Checked offline by driving the real node callbacks with logged
runs (`node_harness.py` in the analysis folder): Long Corridor run 1 1.677 m, Corridor02 run 1 1.705 m,
Multi Floor run 1 0.548 m, identical to the offline replay (1.673 / 1.702 / 0.543). Live batch: run_sah_batch.sh.
