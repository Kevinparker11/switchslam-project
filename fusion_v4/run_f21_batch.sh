#!/usr/bin/env bash
# Live test of F21 = F20 + gmax translation weight + VIO-trust check V1b (docs/results/OT_Channel_Round2.md), 3 recorded runs per sequence,
# then the loop-closure back end with the frozen Multi Floor settings, then one zip for upload.
# Order: Long Corridor and Multi Floor first (bags on the external drive, ~1.5 h), then Corridor02 (laptop copy).
# Start:  setsid nohup systemd-inhibit --what=sleep:idle bash run_f21_batch.sh > ~/f21_batch.log 2>&1 < /dev/null &
set -u
cd "$(dirname "$0")" || exit 1
HDD="/media/$USER/One Touch1/laptop_bags"
echo "start $(date +%T)"
python3 -c "import structure_heading" || { echo "structure_heading.py missing"; exit 1; }
grep -q '\[F21\]' run_fusion_study.sh || { echo "run_fusion_study.sh has no F21 config (git pull)"; exit 1; }
python3 -c "import structure_heading as s; assert hasattr(s, 'scan_tensors')" || { echo "structure_heading.py is older than the OT channel (git pull)"; exit 1; }

seqval() { bash -c "source $1 >/dev/null 2>&1; echo \"\${$2:-}\""; }

if [ -d "$HDD/Long_Corridor_Rosbag" ]; then
  echo "=== Long Corridor (0.5x)"
  PLAY_RATE=0.5 SEQ_ENV=~/runs_corridor/seq.env BAG_DIR_OVERRIDE="$HDD/Long_Corridor_Rosbag" REPEAT=3 RECORD_KF=1 FRONT=aloam ./run_fusion_study.sh F21
else echo "SKIP Long Corridor: $HDD/Long_Corridor_Rosbag not found (drive not mounted?)"; fi
if [ -d "$HDD/RosBag" ]; then
  echo "=== Multi Floor (0.5x)"
  PLAY_RATE=0.5 BAG_DIR_OVERRIDE="$HDD/RosBag" REPEAT=3 RECORD_KF=1 FRONT=aloam ./run_fusion_study.sh F21
else echo "SKIP Multi Floor: $HDD/RosBag not found (drive not mounted?)"; fi
echo "=== external drive no longer needed from here ($(date +%T))"
echo "=== Corridor02 (0.33x)"
PLAY_RATE=0.33 SEQ_ENV=~/runs_corridor2/seq.env REPEAT=3 RECORD_KF=1 FRONT=aloam ./run_fusion_study.sh F21

backend() {   # dir gt extrinsics
  local tags
  tags=$(ls "$1"/keyframes_F21_kf_run*.npz 2>/dev/null | sed 's|.*/keyframes_||; s|\.npz$||' | paste -sd, -)
  [ -z "$tags" ] && { echo "no F21 keyframes in $1"; return; }
  echo "=== back end $1: $tags"
  (export EXTRINSIC_YAML="$3"; ~/venv_backend/bin/python backend_multi.py --dir "$1" --tags "$tags" --gt "$2" \
     --models none,iso,ot --extra "--odom-sigma 1.46,0.054 --calib-end 0") > "$1/backend_F21.out" 2>&1
  tail -n 12 "$1/backend_F21.out"
}
backend ~/runs_corridor "$(seqval ~/runs_corridor/seq.env GT)" "$(seqval ~/runs_corridor/seq.env EXTRINSIC_YAML)"
backend ~/runs_v2 ~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv ""
backend ~/runs_corridor2 "$(seqval ~/runs_corridor2/seq.env GT)" "$(seqval ~/runs_corridor2/seq.env EXTRINSIC_YAML)"

Z=~/Downloads/for_claude_F21.zip; T=$(mktemp -d)
for pair in LC:~/runs_corridor MF:~/runs_v2 C02:~/runs_corridor2; do
  p=${pair%%:*}; d=$(eval echo ${pair#*:})
  cp "$d/results_index.csv" "$T/${p}_results_index.csv" 2>/dev/null
  cp "$d/failed_runs.csv" "$T/${p}_failed_runs.csv" 2>/dev/null
  for f in "$d"/switching_log_v2_F21_kf_run*.csv "$d"/ate_F21_kf_run*.txt "$d"/summary_F21_kf_run*.txt "$d"/node_F21_kf_run*.out \
           "$d"/backend_F21.out "$d"/backend_F21_kf_run*.log; do
    [ -f "$f" ] && cp "$f" "$T/${p}_$(basename "$f")"
  done
done
rm -f "$Z"; (cd "$T" && zip -q "$Z" *) && echo "zip: $Z ($(du -h "$Z" | cut -f1))"
rm -rf "$T"
echo "ALL_DONE $(date +%T)"
