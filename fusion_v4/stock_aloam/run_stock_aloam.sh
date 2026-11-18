#!/usr/bin/env bash
# Stock A-LOAM on a bag sequence: the same pipeline as every other run (same containers, bag, replay rate, ground truth,
# logging) with ONE change: the remap  /laser_odom_to_init -> /switch_fused_pose  is removed from the sequence's A-LOAM launch
# file, so alaserMapping takes its initial guess from A-LOAM's own scan-to-scan odometry, exactly as in the original A-LOAM.
# Configuration F5 (FUSION_MODE=lidar PREDICT_WITH_VINS=0) is used only to start the logger node; nothing it publishes is read
# by A-LOAM. VINS-Mono runs beside it as in every other run and influences nothing.
# The result is the aft_ column of the log (A-LOAM scan-to-map output), scored by stock_aloam/score_aft.py.
#
# usage (from fusion_v4/):
#   Multi Floor : REPEAT=3 PLAY_RATE=1.0  ./stock_aloam/run_stock_aloam.sh mf -
#   Long Corridor: REPEAT=3 PLAY_RATE=1.0  ./stock_aloam/run_stock_aloam.sh lc  ~/runs_corridor/seq.env
#   Corridor02  : REPEAT=3 PLAY_RATE=0.33 ./stock_aloam/run_stock_aloam.sh c02 ~/runs_corridor2/seq.env
#   Cave02      : REPEAT=3 PLAY_RATE=0.5  ./stock_aloam/run_stock_aloam.sh cave02 ~/runs_cave02/seq.env
#   GEODE       : REPEAT=3 PLAY_RATE=<the rate of your F35 GEODE runs> ./stock_aloam/run_stock_aloam.sh geode ~/runs_geode/seq.env
# Use the same PLAY_RATE as the F35 runs of that sequence.  Results go to ~/runs_stock_<name>/ (never to the folder of the other runs).
# Not run in the sandbox where it was written (no containers, no bags): do ONE run first (REPEAT=1) and check step 4 below.
set -u
NAME=${1:?sequence name: mf | lc | c02 | cave02 | geode}
SEQENV=${2:?seq.env of the sequence, or - for Multi Floor}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FUSION_DIR=$(cd "$HERE/.." && pwd)
OUT_STOCK=${OUT_STOCK:-$HOME/runs_stock_$NAME}
GPU_C=switchslam_gpu_v2

# 1. a private copy of the sequence settings whose OUT_DIR points to the stock folder
#    (run_fusion_study.sh lets seq.env override OUT_DIR_OVERRIDE, which would write into the old F5 folder and clash with its logs)
TMPENV=$(mktemp /tmp/stock_${NAME}_XXXX.env)
if [ "$SEQENV" != "-" ]; then
  [ -f "$SEQENV" ] || { echo "seq.env not found: $SEQENV"; exit 1; }
  sed "s|^OUT_DIR=.*|OUT_DIR=$OUT_STOCK|" "$SEQENV" > "$TMPENV"
  grep -q "^OUT_DIR=$OUT_STOCK" "$TMPENV" || echo "OUT_DIR=$OUT_STOCK" >> "$TMPENV"
  ( source "$SEQENV"; echo "$ALOAM_LAUNCH" > "$TMPENV.launch"; echo "$GT" > "$TMPENV.gt" )
  CONT_LAUNCH=$(cat "$TMPENV.launch"); GT=$(cat "$TMPENV.gt")
  export SEQ_ENV=$TMPENV
else
  CONT_LAUNCH=/root/multifloor_aloam.launch
  GT=${MULTIFLOOR_GT:-$HOME/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv}
  export OUT_DIR_OVERRIDE=$OUT_STOCK
fi
mkdir -p "$OUT_STOCK"

# 2. stock launch = the sequence's launch without the remap line; the original is kept in the container and put back on exit
#    (the containers must be running to copy into them; run_fusion_study.sh restarts them again before every run, which keeps the files)
for c in $GPU_C vinsmono_test; do
  [ "$(docker inspect -f '{{.State.Running}}' $c 2>/dev/null)" = "true" ] || { echo "starting container $c"; docker start $c > /dev/null || exit 1; }
done
sleep 3
BACKUP=/root/thr/$(basename "$CONT_LAUNCH").orig_before_stock
docker exec $GPU_C bash -c "mkdir -p /root/thr; [ -f $BACKUP ] || cp $CONT_LAUNCH $BACKUP" || exit 1
restore() { docker exec $GPU_C bash -c "[ -f $BACKUP ] && cp $BACKUP $CONT_LAUNCH" && echo "original launch restored: $CONT_LAUNCH"; }
trap restore EXIT
docker exec $GPU_C cat $BACKUP | sed '/<remap from="\/laser_odom_to_init" to="\/switch_fused_pose"\/>/d' > "$TMPENV.stock.launch"
if grep -q switch_fused_pose "$TMPENV.stock.launch"; then echo "the remap line was not removed, abort"; exit 1; fi
docker cp "$TMPENV.stock.launch" $GPU_C:$CONT_LAUNCH || exit 1
echo "stock launch in place: $CONT_LAUNCH (no switch_fused_pose remap)"

# 3. the normal run script, configuration F5 (logger only), A-LOAM stack, repeats as set by REPEAT
cd "$FUSION_DIR" && FRONT=aloam ./run_fusion_study.sh F5

# 4. score the A-LOAM pose of every log (the table printed by run_fusion_study.sh scores the node's fused_ column instead)
echo; echo "stock A-LOAM, aft_ column, against $GT"
for f in "$OUT_STOCK"/switching_log_v2_F5_run*.csv; do
  [ -f "$f" ] && { printf "%s  " "$(basename "$f")"; python3 stock_aloam/score_aft.py --gt "$GT" --log "$f" | tail -1; }
done
