# fusion_v2: VIO-primary, degeneracy-gated LiDAR correction

Replaces the switching node.  The node fuses **relative motion in the LiDAR body frame**, so VINS-Mono's world
frame and A-LOAM's frames never get mixed (in the old node they differ by 6-62 deg).  Same containers, bags,
A-LOAM launch (feedback remap) and VINS config as the threshold study.

| File | What it is |
|---|---|
| `fusion_core.py` | all the maths (numpy only) |
| `test_fusion_core.py` | unit tests: frame mixing, extrinsic, warm-up, weights, gate, VINS loss/re-init, Otsu |
| `fusion_node_v2.py` | the ROS node (`/switch_fused_pose` out, `/aft_mapped_to_init` + `/vins_estimator/odometry` + Hessian in) |
| `patch_mapping_hessian.py` | optional A-LOAM patch: scan-to-map Hessian on `/mapping_hessian` |
| `calibrate_c.py` | picks `C_T` on bag 0 only (1-s RPE) |
| `fusion_summary.py` | per-run summary + paired replay (VINS-only / LiDAR-only / fused from the same run) |
| `offline_evidence.py` | reproduces the offline evidence from the old logs |
| `run_fusion_study.sh` | unattended batch (configs F0-F5, M0-M1), same structure as run_all_thresholds.sh |

## Steps

```bash
# 0. put the folder next to the threshold study
cd ~/switchslam_channelT && unzip -o ~/Downloads/fusion_v2.zip && cd fusion_v2
python3 test_fusion_core.py                       # must end with ALL TESTS PASSED
chmod +x run_fusion_study.sh && ./run_fusion_study.sh --dry

# 1. smoke test (70 s of bag)
SMOKE=1 ./run_fusion_study.sh F1                  # expect VINS-Mono from ~20 s, FUSED from ~40 s, Hessian present

# 2. one VINS-primary run, then calibrate C_T on bag 0 only
./run_fusion_study.sh F0
python3 calibrate_c.py --log ~/runs_v2/switching_log_v2_F0_run1.csv \
    --gt ~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv
#    -> CHOSEN C_T = ...   (offline evidence: 1e-3 on one old run, 0 on the other)

# 3. the batch (3 repeats of F0-F5, ~2.5 h), with the calibrated value
LASER_C_T=<chosen> REPEAT=3 setsid nohup systemd-inhibit --what=sleep:idle ./run_fusion_study.sh \
    > ~/runs_v2/batch.log 2>&1 < /dev/null & disown

# 4. optional: scan-to-map Hessian (rebuild A-LOAM once; pass the path to laserMapping.cpp if A-LOAM lives elsewhere)
docker cp patch_mapping_hessian.py switchslam_gpu_v2:/root/
docker exec switchslam_gpu_v2 bash -c "python3 /root/patch_mapping_hessian.py && source /opt/ros/noetic/setup.bash && cd /root/catkin_ws && catkin_make"
./run_fusion_study.sh M0          # then calibrate_c.py on its log -> MAP_C_T
MAP_C_T=<chosen> REPEAT=3 ./run_fusion_study.sh M1

# 5. final numbers: 5 runs of F0 and the best configuration (adds runs 4-5; use the SAME values as before)
LASER_C_T=<same as step 3> REPEAT=5 ./run_fusion_study.sh F0 F1
```

Every repeat of a configuration must use the same settings. The script stops if, say, F1_run4 would use a
different `LASER_C_T` from F1_run1-3; move `~/runs_v2` aside to start a new study instead.

Results: `~/runs_v2/results_index.csv` (full-span ATE RMSE and max per run), `ate_*.txt`, `summary_*.txt`.

## Configurations

| Tag | Setting | Question |
|---|---|---|
| F0 | VINS-primary, LiDAR only during VINS warm-up | what VINS-Mono gives inside the frame-consistent node |
| F1 | + LiDAR correction, Schur-direction weights, gate kappa(S_RR) <= 15.7 | the method |
| F2 | as F1, gate re-estimated online by Otsu (label-free) | does the label-free gate hold up |
| F3 | as F1 without the gate | what the gate is worth |
| F4 | scan-to-map output, VINS used only as initial guess | Switch-SLAM-like structure, same front ends |
| F5 | A-LOAM mapping alone | LiDAR baseline |
| M0/M1 | F0/F1 with the scan-to-map Hessian | does the right Hessian help |

Compare with published numbers using the **full-span** ATE (the node now outputs poses from the first mapped
scan, as Switch-SLAM does).  Judge the method against F0 with `fusion_summary.py` (paired, same run), because
VINS-Mono alone varies 1.02-1.34 m between runs.
