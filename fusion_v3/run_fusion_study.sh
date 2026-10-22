#!/usr/bin/env bash
# Multi Floor runs of fusion_node_v2 (VIO-primary, degeneracy-gated LiDAR correction), one full bag replay each.
#   ./run_fusion_study.sh --dry                 print what would run
#   SMOKE=1 ./run_fusion_study.sh F1            70 s smoke test, no scoring (SMOKE_SECS=160 for a longer one)
#   PLAY_RATE=0.33 ...   replay the bag slower (node time is the bag clock, so a slow machine then drops no scans)
#   ./run_fusion_study.sh F0                    one configuration
#   REPEAT=3 ./run_fusion_study.sh              all configurations, 3 repeats each (~18 x 8 min)
#   BAG_DIR_OVERRIDE="/media/$USER/One Touch1/laptop_bags/RosBag" ...   read the bags from another folder
#   RECORD_KF=1 ./run_fusion_study.sh F1        one extra run (tag F1_kf_run1) that also saves keyframe scans
#                                               for the offline back end (keyframes_F1_kf_run1.npz)
# Long batches:  setsid nohup systemd-inhibit --what=sleep:idle ./run_fusion_study.sh > ~/runs_v2/batch.log 2>&1 < /dev/null & disown
# Same stack, containers and bags as run_all_thresholds.sh; only the node changes.
set -u

# ----------------------------------------------------------------------------------------------
GPU_C=switchslam_gpu_v2
VINS_C=vinsmono_test
BAG_DIR=~/Downloads/RosBag
BAGS=$(cd "$BAG_DIR" 2>/dev/null && ls -1 *.bag 2>/dev/null | sort | sed 's|^|/bags/|' | tr '\n' ' ')
GT=~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv
ATE=~/switchslam_project/multifloor_ate_eval.py
FUSION_DIR=~/switchslam_channelT/fusion_v3
RESTART=~/switchslam_project/clean_restart.sh
ROS1="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROSK="source /opt/ros/kinetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
VINS_CFG=/root/catkin_ws/src/VINS-Mono/config/multifloor_config.yaml
VINS_DIR=/root/catkin_ws/src/VINS-Mono/
LASER_C_T=${LASER_C_T:-1e-3}      # from calibrate_c.py on an F0 log (scan-to-scan Hessian)
MAP_C_T=${MAP_C_T:-1e-4}          # from calibrate_c.py on an F0 log made with HESS_TOPIC=/mapping_hessian
UNGATED_C_T=${UNGATED_C_T:-1e-2}        # config F7
UNGATED_C_T_HI=${UNGATED_C_T_HI:-3e-2}  # config F8
UNGATED_C_T_TOP=${UNGATED_C_T_TOP:-1e-1} # config F9
LASER_C_R=${LASER_C_R:-0}         # LiDAR rotation weight, from calibrate_c.py --c-r-grid (config F6)
VEL_LAUNCH=/root/multifloor_velodyne_convert.launch
ALOAM_LAUNCH=/root/multifloor_aloam.launch
OUT_DIR=~/runs_v2; MIN_ROWS=3000; SCORER=multifloor; NODE_EXTRA=""; SUMMARY_EXTRA=""
# Another sequence: SEQ_ENV=~/runs_corridor/seq.env (written by setup_sequence.sh) overrides the lines above
if [ -n "${SEQ_ENV:-}" ]; then
  [ -f "$SEQ_ENV" ] || { echo "SEQ_ENV $SEQ_ENV not found"; exit 1; }
  source "$SEQ_ENV"
  BAGS=$(cd "$BAG_DIR" 2>/dev/null && ls -1 *.bag 2>/dev/null | sort | sed 's|^|/bags/|' | tr '\n' ' ')
fi
if [ -n "${BAG_DIR_OVERRIDE:-}" ]; then
  BAG_DIR=$BAG_DIR_OVERRIDE
  BAGS=$(cd "$BAG_DIR" 2>/dev/null && ls -1 *.bag 2>/dev/null | sort | sed 's|^|/bags/|' | tr '\n' ' ')
fi

start_stack() {
  docker exec -d -e ROS_IP=$GPU $GPU_C bash -c "$ROS1 && roscore > /root/thr/roscore.out 2>&1"; sleep 6
  docker exec $GPU_C bash -c "$ROS1 && rosparam set /use_sim_time true"
  [ -n "$VEL_LAUNCH" ] && docker exec -d -e ROS_IP=$GPU $GPU_C bash -c "$ROS1 && roslaunch $VEL_LAUNCH > /root/thr/velodyne.out 2>&1"
  docker exec -d -e ROS_IP=$GPU $GPU_C bash -c "$ROS1 && roslaunch $ALOAM_LAUNCH > /root/thr/aloam.out 2>&1"
  docker exec $VINS_C mkdir -p /root/thr
  docker exec -d -e ROS_MASTER_URI=http://$GPU:11311 -e ROS_IP=$VINS $VINS_C bash -c "$ROSK && rosrun feature_tracker feature_tracker _config_file:=$VINS_CFG _vins_folder:=$VINS_DIR > /root/thr/ft.out 2>&1"
  docker exec -d -e ROS_MASTER_URI=http://$GPU:11311 -e ROS_IP=$VINS $VINS_C bash -c "$ROSK && rosrun vins_estimator vins_estimator _config_file:=$VINS_CFG _vins_folder:=$VINS_DIR > /root/thr/vins.out 2>&1"
  sleep 8
}
# ----------------------------------------------------------------------------------------------

declare -A CFG=(
  [F0]="FUSION_MODE=vins"
  [F1]="FUSION_MODE=fused C_T=$LASER_C_T KAPPA_MODE=fixed KAPPA_TH=15.7"
  [F2]="FUSION_MODE=fused C_T=$LASER_C_T KAPPA_MODE=otsu KAPPA_TH=15.7"
  [F3]="FUSION_MODE=fused C_T=$LASER_C_T KAPPA_TH=1e9"
  [F4]="FUSION_MODE=lidar PREDICT_WITH_VINS=1"
  [F5]="FUSION_MODE=lidar PREDICT_WITH_VINS=0"
  [F6]="FUSION_MODE=fused C_T=$LASER_C_T C_R=$LASER_C_R KAPPA_MODE=fixed KAPPA_TH=15.7"
  [F7]="FUSION_MODE=fused C_T=$UNGATED_C_T KAPPA_TH=1e9"      # no gate, C_T from the 5-s-horizon bag-0 rule (calibrate_c.py --horizon 5 --kappa-th 1e9)
  [F8]="FUSION_MODE=fused C_T=$UNGATED_C_T_HI KAPPA_TH=1e9"   # sensitivity run only (not a tuned result)
  [F9]="FUSION_MODE=fused C_T=$UNGATED_C_T_TOP KAPPA_TH=1e9"  # sensitivity run only (not a tuned result)
  [F10]="FUSION_MODE=fused C_T=3e-1 KAPPA_TH=1e9"               # sensitivity run only
  # weighting ablation at the fixed C_T = 0.03 (rotation always from VINS-Mono, no kappa gate):
  [F11]="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 WEIGHT_MODE=iso"        # isotropic, same mean information
  [F12]="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=15.7 WEIGHT_MODE=switch_ss" # hard switch, Switch-SLAM detection rule
  [F13]="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 WEIGHT_MODE=proj"       # hard per-direction 0/1 (kappa_t > 10 dropped)
  [F14]="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 WEIGHT_MODE=lidar"      # LiDAR translation, VINS rotation (W = I)
  [F15]="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 WEIGHT_MODE=diag"       # diagonal block H_tt instead of Schur S_tt
  [F16]="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1"                  # F8 + structure-anchored heading (structure_heading.py)
  [M0]="FUSION_MODE=vins HESS_TOPIC=/mapping_hessian"
  [M1]="FUSION_MODE=fused C_T=$MAP_C_T KAPPA_MODE=fixed KAPPA_TH=15.7 HESS_TOPIC=/mapping_hessian"
)
ORDER="F0 F1 F2 F3 F4 F5"
DRY=0; SEL=()
for a in "$@"; do [ "$a" = "--dry" ] && DRY=1 || SEL+=("$a"); done
[ ${#SEL[@]} -eq 0 ] && SEL=($ORDER)
REPEAT=${REPEAT:-1}; SMOKE=${SMOKE:-0}; RECORD_KF=${RECORD_KF:-0}
[ -z "$BAGS" ] && { echo "no .bag files found in $BAG_DIR"; exit 1; }
for f in fusion_core.py fusion_node_v2.py v2_tools.py fusion_summary.py structure_heading.py; do
  [ -f "$FUSION_DIR/$f" ] || { echo "missing $FUSION_DIR/$f"; exit 1; }
done
echo "bags: $BAGS"
OUT=$OUT_DIR; mkdir -p $OUT; RES=$OUT/results_index.csv
exec 9>$OUT/.run.lock
flock -n 9 || { echo "another run_fusion_study.sh is already running - not starting"; exit 1; }
[ -f "$RES" ] || echo "tag,config,rows,ate_full_rmse,ate_full_max,finished" > "$RES"

envflags() { local s=""; for kv in $1; do s="$s -e $kv"; done; echo "$s"; }
cval() { echo "$1" | tr ' ' '\n' | grep '^C_T=' | cut -d= -f2; }

run_one() {
  local id=$1 r=$2 cfg=${CFG[$1]:-} tag="${1}_run${2}"
  [ $RECORD_KF = 1 ] && tag="${1}_kf_run${2}"
  [ -z "$cfg" ] && { echo "unknown config $id"; return 1; }
  echo "=== $tag : $cfg  ($(date +%T))"
  if [ $DRY = 1 ]; then echo "    would run: restart, stack, fusion_node_v2 $(envflags "$cfg") -e RUN_TAG=$tag, bag, score"; return 0; fi
  [ $SMOKE = 1 ] && tag="SMOKE_$tag"
  [ $SMOKE = 0 ] && grep -q "^$tag," "$RES" && { echo "    already in results_index.csv, skipping"; return 0; }
  # repeats of one configuration must use identical settings (e.g. the same LASER_C_T), or the mean is meaningless
  local prev=$(grep "^${id}_run[0-9]*," "$RES" | head -1 | cut -d'"' -f2)
  if [ $SMOKE = 0 ] && [ -n "$prev" ] && [ "$prev" != "$cfg" ]; then
    echo "    STOP: $id was run before with \"$prev\" but now with \"$cfg\"."
    echo "    Re-run with the same settings (e.g. LASER_C_T=...), or move ~/runs_v2 aside to start a new study."
    exit 1
  fi

  $RESTART > $OUT/restart_$tag.out 2>&1
  GPU=$(docker inspect -f '{{.NetworkSettings.Networks.vins_bridge.IPAddress}}' $GPU_C)
  VINS=$(docker inspect -f '{{.NetworkSettings.Networks.vins_bridge.IPAddress}}' $VINS_C)
  for c in $GPU_C $VINS_C; do
    [ "$(docker inspect -f '{{.State.Running}}' $c 2>/dev/null)" = "true" ] || { echo "    container $c is not running after restart (see $OUT/restart_$tag.out; try: docker start $c; docker logs --tail 20 $c), abort"; exit 1; }
  done
  echo "$GPU $VINS" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+ [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' || { echo "    no vins_bridge IPs after restart (got: $GPU $VINS), abort"; exit 1; }
  docker exec $GPU_C bash -c "mkdir -p /root/thr; pkill -9 -f '[s]witching_node'; pkill -9 -f '[f]usion_node_v2'; pkill -9 -f '[k]eyframe_recorder'; rm -f /root/thr/switching_log_v2_$tag.csv /root/thr/keyframes_$tag.npz"
  for f in fusion_core.py fusion_node_v2.py keyframe_recorder.py structure_heading.py; do
    docker cp $FUSION_DIR/$f $GPU_C:/root/thr/ || { echo "    docker cp $f failed"; exit 1; }
  done
  if [ -n "${EXTRINSIC_YAML:-}" ]; then
    docker cp "$EXTRINSIC_YAML" $GPU_C:/root/thr/$(basename "$EXTRINSIC_YAML") || { echo "    docker cp extrinsics failed"; exit 1; }
  fi
  start_stack
  docker exec -d -e ROS_IP=$GPU $(envflags "$cfg") $NODE_EXTRA -e RUN_TAG=$tag $GPU_C \
    bash -c "$ROS1 && cd /root/thr && python3 -u fusion_node_v2.py > /root/thr/node_$tag.out 2>&1"
  sleep 8
  docker exec $GPU_C head -3 /root/thr/node_$tag.out | tee $OUT/node_head_$tag.txt
  docker exec $GPU_C grep -q "FUSION_MODE=" /root/thr/node_$tag.out || { echo "    node did not start (see node_$tag.out), abort"; docker exec $GPU_C cat /root/thr/node_$tag.out; exit 1; }
  if [ $RECORD_KF = 1 ]; then
    docker exec -d -e ROS_IP=$GPU -e RUN_TAG=$tag $GPU_C \
      bash -c "$ROS1 && cd /root/thr && python3 -u keyframe_recorder.py > /root/thr/kf_$tag.out 2>&1"
    sleep 4
    docker exec $GPU_C grep -q "keyframe_recorder listening" /root/thr/kf_$tag.out || { echo "    keyframe_recorder did not start, abort"; docker exec $GPU_C cat /root/thr/kf_$tag.out; exit 1; }
  fi

  local PLAYOPT=""; [ $SMOKE = 1 ] && PLAYOPT="-u ${SMOKE_SECS:-70}"
  docker run --rm --network vins_bridge -v "$BAG_DIR":/bags:ro -e ROS_MASTER_URI=http://$GPU:11311 \
    --entrypoint bash ros:noetic -c "export ROS_IP=\$(hostname -i); source /opt/ros/noetic/setup.bash; rosbag play --clock -q -r ${PLAY_RATE:-1.0} $PLAYOPT $BAGS" \
    > $OUT/player_$tag.out 2>&1
  sleep 6
  docker exec $GPU_C bash -c "pkill -INT -f '[f]usion_node_v2'; pkill -INT -f '[k]eyframe_recorder'"; sleep 6
  if [ $RECORD_KF = 1 ]; then
    docker cp $GPU_C:/root/thr/keyframes_$tag.npz $OUT/ && echo "    keyframes saved: $OUT/keyframes_$tag.npz ($(du -h $OUT/keyframes_$tag.npz | cut -f1))" \
      || echo "    WARNING: no keyframe file (see kf_$tag.out)"
    docker cp $GPU_C:/root/thr/kf_$tag.out $OUT/ 2>/dev/null
  fi
  docker cp $GPU_C:/root/thr/switching_log_v2_$tag.csv $OUT/ || { echo "    no log produced"; return 1; }
  docker cp $GPU_C:/root/thr/node_$tag.out $OUT/node_$tag.out 2>/dev/null
  for c in aloam velodyne; do docker cp $GPU_C:/root/thr/$c.out $OUT/${c}_$tag.out 2>/dev/null; done
  for c in ft vins; do docker cp $VINS_C:/root/thr/$c.out $OUT/${c}_$tag.out 2>/dev/null; done
  local rows=$(($(wc -l < $OUT/switching_log_v2_$tag.csv) - 1))
  if [ $SMOKE = 1 ]; then
    echo "    log rows in ${SMOKE_SECS:-70} s of bag: $rows (expect a few hundred)"
    python3 - "$OUT/switching_log_v2_$tag.csv" <<'PY'
import sys, pandas as pd
L = pd.read_csv(sys.argv[1]); print("    modes:", L["mode"].value_counts().to_dict())
print("    VINS present in rows:", int(L["v_px"].notna().sum()), "| Hessian present:", int(L["Hl_00"].notna().sum()))
print("    time looks like sim time:", L["time"].min() > 1.6e9)
t0 = L["time"].min()
for name, x in [("VINS-Mono pose", L.loc[L["v_px"].notna(), "time"]), ("FUSED row", L.loc[L["mode"] == "FUSED", "time"])]:
    print("    first %-14s %s" % (name, "%.1f s after the first mapped scan" % (x.min() - t0) if len(x) else "never"))
print("    expect: VINS-Mono from ~20 s into the bag, FUSED about 20 s later (F1/F2/F3 only; WARMUP before that)")
PY
    return 0
  fi
  if [ "$SCORER" = multifloor ]; then
    (cd $OUT && python3 $ATE --gt $GT --fmt switch switching_log_v2_$tag.csv) > $OUT/ate_$tag.txt 2>&1
  else
    (cd $FUSION_DIR && python3 score_run.py --gt $GT --log $OUT/switching_log_v2_$tag.csv) > $OUT/ate_$tag.txt 2>&1
  fi
  local ct=$(cval "$cfg"); [ -z "$ct" ] && ct=1e-3
  (cd $FUSION_DIR && python3 fusion_summary.py --log $OUT/switching_log_v2_$tag.csv --gt $GT --c-t $ct $SUMMARY_EXTRA) > $OUT/summary_$tag.txt 2>&1
  local full=$(grep "full span of this run" $OUT/ate_$tag.txt | sed -E 's/.*RMSE = *([0-9.]+) m *Max = *([0-9.]+).*/\1,\2/')
  echo "    rows=$rows  full-span ATE (RMSE,max) = $full"
  if [ $rows -lt $MIN_ROWS ]; then
    echo "    FAILED: fewer than $MIN_ROWS rows - not added to results_index.csv"
    echo "$tag,\"$cfg\",$rows,$(date +%F_%T)" >> $OUT/failed_runs.csv
  else
    echo "$tag,\"$cfg\",$rows,$full,$(date +%F_%T)" >> "$RES"
  fi
  tail -3 $OUT/ate_$tag.txt
}

for id in "${SEL[@]}"; do for r in $(seq ${RUN_START:-1} $(( ${RUN_START:-1} + REPEAT - 1 ))); do run_one $id $r; done; done
echo "done $(date +%T). Index: $RES"
