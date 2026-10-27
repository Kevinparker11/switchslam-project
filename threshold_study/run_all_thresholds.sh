#!/usr/bin/env bash
# Runs every threshold configuration of the Multi Floor study, one full bag replay each, unattended.
#   ./run_all_thresholds.sh --dry          print what would run, run nothing
#   ./run_all_thresholds.sh A2             one configuration (do this first)
#   ./run_all_thresholds.sh                all configurations (~15 x 9 min)
#   REPEAT=3 ./run_all_thresholds.sh A2 A8 three repeats of the chosen ones
#   SMOKE=1 ./run_all_thresholds.sh A2     30 s smoke test: checks every topic and the log, no scoring
# Long batches: nohup ./run_all_thresholds.sh > ~/runs_thr/batch.log 2>&1 &
# It only ADDS files: /root/thr/* in the GPU container and ~/runs_thr/* on the host.
set -u

# ----------------------------------------------------------------------------------------------
# CHECK THIS BLOCK AGAINST YOUR RUN-3 COMMANDS ("Multifloor Commands" file) BEFORE THE FIRST RUN
GPU_C=switchslam_gpu_v2
VINS_C=vinsmono_test
BAG_DIR=~/Downloads/RosBag
# all .bag files in BAG_DIR, in name order (the three Multi Floor segments must sort in time order)
BAGS=$(cd "$BAG_DIR" 2>/dev/null && ls -1 *.bag 2>/dev/null | sort | sed 's|^|/bags/|' | tr '\n' ' ')
GT=~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv
ATE=~/switchslam_project/multifloor_ate_eval.py
SUMMARY=~/switchslam_channelT/threshold_study/live_summary.py
RESTART=~/switchslam_project/clean_restart.sh
ROS1="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROSK="source /opt/ros/kinetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
VINS_CFG=/root/catkin_ws/src/VINS-Mono/config/multifloor_config.yaml
VINS_DIR=/root/catkin_ws/src/VINS-Mono/

start_stack() {   # T1-T5 of run 3, detached; output goes to /root/thr/*.out inside the containers
  docker exec -d -e ROS_IP=$GPU $GPU_C bash -c "$ROS1 && roscore > /root/thr/roscore.out 2>&1"; sleep 6
  docker exec $GPU_C bash -c "$ROS1 && rosparam set /use_sim_time true"
  docker exec -d -e ROS_IP=$GPU $GPU_C bash -c "$ROS1 && roslaunch /root/multifloor_velodyne_convert.launch > /root/thr/velodyne.out 2>&1"
  docker exec -d -e ROS_IP=$GPU $GPU_C bash -c "$ROS1 && roslaunch /root/multifloor_aloam.launch > /root/thr/aloam.out 2>&1"
  docker exec $VINS_C mkdir -p /root/thr
  docker exec -d -e ROS_MASTER_URI=http://$GPU:11311 -e ROS_IP=$VINS $VINS_C bash -c "$ROSK && rosrun feature_tracker feature_tracker _config_file:=$VINS_CFG _vins_folder:=$VINS_DIR > /root/thr/ft.out 2>&1"
  docker exec -d -e ROS_MASTER_URI=http://$GPU:11311 -e ROS_IP=$VINS $VINS_C bash -c "$ROSK && rosrun vins_estimator vins_estimator _config_file:=$VINS_CFG _vins_folder:=$VINS_DIR > /root/thr/vins.out 2>&1"
  sleep 8
}
# ----------------------------------------------------------------------------------------------

declare -A CFG=(
  [A1]="SCHUR_RULE=semicircle T_RULE=off"
  [A2]="SCHUR_RULE=kappa SCHUR_VAL=10 T_RULE=off"
  [A3]="SCHUR_RULE=kappa SCHUR_VAL=50 T_RULE=off"
  [A4]="SCHUR_RULE=diag_kappa SCHUR_VAL=10 T_RULE=off"
  [A5]="SCHUR_RULE=lmin SCHUR_VAL=100 T_RULE=off"
  [A6]="SCHUR_RULE=never T_RULE=off"
  [A7]="SCHUR_RULE=fcn SCHUR_VAL=10 T_RULE=off"
  [A8]="SCHUR_RULE=kappa_rot SCHUR_VAL=15.7 T_RULE=off"
  [B1]="SCHUR_RULE=never T_RULE=lmin T_VAL=0.15"
  [B2]="SCHUR_RULE=never T_RULE=kappa T_VAL=10"
  [B3]="SCHUR_RULE=never T_RULE=floor T_VAL=0.045"
  [B4]="SCHUR_RULE=never T_RULE=woodcock"
  [B5]="SCHUR_RULE=never T_RULE=demantke"
  [C1]="SCHUR_RULE=kappa SCHUR_VAL=10 T_RULE=floor T_VAL=0.045"
  [C2]="SCHUR_RULE=kappa SCHUR_VAL=10 T_RULE=kappa T_VAL=10"
  [REF]="SCHUR_RULE=semicircle T_RULE=lmin T_VAL=0.15"
)
ORDER="A2 A1 A3 A4 A5 A6 A7 A8 B1 B2 B3 B4 B5 C1 C2"
DRY=0; SEL=()
for a in "$@"; do [ "$a" = "--dry" ] && DRY=1 || SEL+=("$a"); done
[ ${#SEL[@]} -eq 0 ] && SEL=($ORDER)
REPEAT=${REPEAT:-1}; SMOKE=${SMOKE:-0}
[ -z "$BAGS" ] && { echo "no .bag files found in $BAG_DIR"; exit 1; }
echo "bags: $BAGS"
mkdir -p ~/runs_thr; RES=~/runs_thr/results_index.csv
# only one copy may run: a second copy would restart the containers under the first one
exec 9>~/runs_thr/.run.lock
flock -n 9 || { echo "another run_all_thresholds.sh is already running - not starting"; exit 1; }
[ -f "$RES" ] || echo "tag,config,rows,ate_file,summary_file,finished" > "$RES"

envflags() { local s=""; for kv in $1; do s="$s -e $kv"; done; echo "$s"; }

run_one() {
  local id=$1 r=$2 cfg=${CFG[$1]} tag="${1}_run${2}"
  [ -z "$cfg" ] && { echo "unknown config $id"; return 1; }
  echo "=== $tag : $cfg  ($(date +%T))"
  if [ $DRY = 1 ]; then echo "    would run: restart, T1-T5, node $(envflags "$cfg") -e RUN_TAG=$tag, bag, score"; return 0; fi
  # skip if already done
  [ $SMOKE = 1 ] && tag="SMOKE_$tag"
  [ $SMOKE = 0 ] && grep -q "^$tag," "$RES" && { echo "    already in results_index.csv, skipping"; return 0; }

  $RESTART > ~/runs_thr/restart_$tag.out 2>&1
  GPU=$(docker inspect -f '{{.NetworkSettings.Networks.vins_bridge.IPAddress}}' $GPU_C)
  VINS=$(docker inspect -f '{{.NetworkSettings.Networks.vins_bridge.IPAddress}}' $VINS_C)
  [ -z "$GPU" ] || [ -z "$VINS" ] && { echo "    no vins_bridge IPs after restart, abort"; exit 1; }
  docker exec $GPU_C bash -c "mkdir -p /root/thr; pkill -9 -f '[s]witching_node'; rm -f /root/thr/switching_log_thr_$tag.csv"
  for f in switching_node_mf_thr.py degeneracy_rules.py; do
    docker cp ~/switchslam_channelT/threshold_study/$f $GPU_C:/root/thr/ || { echo "    docker cp $f failed"; exit 1; }
  done
  start_stack
  docker exec -d -e ROS_IP=$GPU $(envflags "$cfg") -e RUN_TAG=$tag $GPU_C \
    bash -c "$ROS1 && cd /root/thr && python3 -u switching_node_mf_thr.py > /root/thr/node_$tag.out 2>&1"
  sleep 8
  docker exec $GPU_C head -3 /root/thr/node_$tag.out | tee ~/runs_thr/node_head_$tag.txt
  docker exec $GPU_C grep -q "SCHUR_RULE=" /root/thr/node_$tag.out || { echo "    node did not print its rule, abort"; exit 1; }

  local PLAYOPT=""; [ $SMOKE = 1 ] && PLAYOPT="-u 40"
  if [ $SMOKE = 1 ]; then   # measure topic rates while the first 40 s play
    ( sleep 15; for tp in /multifloor/velodyne_points /laser_hessian /laser_odom_to_init /laser_cloud_surf_last /vins_estimator/odometry /vins_mono_hessian /feature_tracker/feature /switch_fused_pose; do
        n=$(docker exec -e ROS_IP=$GPU $GPU_C bash -c "$ROS1 && timeout 6 rostopic hz $tp 2>/dev/null | grep -m1 'average rate'"); echo "    $tp : ${n:-NO MESSAGES}"; done ) > ~/runs_thr/smoke_topics.txt &
  fi
  docker run --rm --network vins_bridge -v "$BAG_DIR":/bags:ro -e ROS_MASTER_URI=http://$GPU:11311 \
    --entrypoint bash ros:noetic -c "export ROS_IP=\$(hostname -i); source /opt/ros/noetic/setup.bash; rosbag play --clock -q -r 1.0 $PLAYOPT $BAGS" \
    > ~/runs_thr/player_$tag.out 2>&1
  sleep 6
  docker exec $GPU_C bash -c "pkill -INT -f '[s]witching_node_mf_thr'"; sleep 4
  docker cp $GPU_C:/root/thr/switching_log_thr_$tag.csv ~/runs_thr/ || { echo "    no log produced"; return 1; }
  docker cp $GPU_C:/root/thr/node_$tag.out ~/runs_thr/node_$tag.out 2>/dev/null
  for c in aloam velodyne; do docker cp $GPU_C:/root/thr/$c.out ~/runs_thr/${c}_$tag.out 2>/dev/null; done
  for c in ft vins; do docker cp $VINS_C:/root/thr/$c.out ~/runs_thr/${c}_$tag.out 2>/dev/null; done
  local rows=$(($(wc -l < ~/runs_thr/switching_log_thr_$tag.csv) - 1))
  if [ $SMOKE = 1 ]; then
    wait; echo "    --- topic rates (expect ~10 Hz LiDAR topics, ~10-25 Hz VINS) ---"; cat ~/runs_thr/smoke_topics.txt
    echo "    log rows in 40 s: $rows (expect roughly 150-400)"; head -1 ~/runs_thr/switching_log_thr_$tag.csv | tr ',' '\n' | tail -12 | tr '\n' ' '; echo
    python3 - "$HOME/runs_thr/switching_log_thr_$tag.csv" <<'PY'
import sys, pandas as pd
L = pd.read_csv(sys.argv[1]); print("    rule:", L["rule"].iloc[0] if "rule" in L else "MISSING rule column")
for c in ["flag_R_rot", "flag_R_trans", "flag_T"]: print(f"    {c} fire rate: {L[c].mean():.3f}" if c in L else f"    {c} MISSING")
print("    modes:", L["mode"].value_counts().to_dict()); print("    time looks like sim time:", L["time"].min() > 1.6e9)
PY
    return 0
  fi
  (cd ~/runs_thr && python3 $ATE --gt $GT --fmt switch switching_log_thr_$tag.csv) > ~/runs_thr/ate_$tag.txt 2>&1
  python3 $SUMMARY --log ~/runs_thr/switching_log_thr_$tag.csv --gt $GT > ~/runs_thr/summary_$tag.txt 2>&1
  echo "    rows=$rows"
  if [ $rows -lt 3000 ]; then
    echo "    FAILED: fewer than 3000 rows - not added to results_index.csv (it will be re-run). Check node_$tag.out, aloam_$tag.out, vins_$tag.out"
    echo "$tag,\"$cfg\",$rows,$(date +%F_%T)" >> ~/runs_thr/failed_runs.csv
  else
    echo "$tag,\"$cfg\",$rows,ate_$tag.txt,summary_$tag.txt,$(date +%F_%T)" >> "$RES"
  fi
  tail -3 ~/runs_thr/ate_$tag.txt; grep -E "fire rate|mode share|held out" ~/runs_thr/summary_$tag.txt
}

for id in "${SEL[@]}"; do for r in $(seq 1 $REPEAT); do run_one $id $r; done; done
echo "done $(date +%T). Index: $RES"
