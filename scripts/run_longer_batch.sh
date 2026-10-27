#!/usr/bin/env bash
# Longer batch (unattended, ~3-4 h): grows N from 3 to 6 on every sequence and adds the matched Multi Floor control.
#  1. Multi Floor, F8, runs 7-9 at 0.5x   (matched control for F16, which was run at 0.5x)
#  2. Long Corridor, F16, runs 4-6 at 0.5x
#  3. Multi Floor,  F16, runs 4-6 at 0.5x
#  4. Corridor02,   F16, runs 4-6 at 0.33x  (laptop copy, no drive needed)
#  5. Back end (frozen Multi Floor settings) on ALL F16 runs (1-6) of each sequence, full loop lists
#  6. One zip: ~/Downloads/for_claude11.zip
# Runs already in results_index.csv are skipped, so it is safe to restart after an interruption.
# Start:  cd <fusion_v3 folder> && setsid nohup systemd-inhibit --what=sleep:idle bash ~/run_longer_batch.sh > ~/longer_batch.log 2>&1 < /dev/null &
set -u
cd "${FUSION_V3_DIR:-$(pwd)}" || exit 1
[ -f run_fusion_study.sh ] || { echo "run this from the fusion_v3 folder (run_fusion_study.sh not found)"; exit 1; }
HDD="/media/$USER/One Touch1/laptop_bags"
echo "start $(date +%T)"
seqval() { bash -c "source $1 >/dev/null 2>&1; echo \"\${$2:-}\""; }

# bag folders: external drive if mounted, else the laptop copy
MFBAG="$HDD/RosBag";            [ -d "$MFBAG" ] || MFBAG=~/Downloads/RosBag
LCBAG="$HDD/Long_Corridor_Rosbag"
if [ -d "$MFBAG" ]; then
  echo "=== 1. Multi Floor F8 control, runs 7-9 (0.5x), bags: $MFBAG"
  PLAY_RATE=0.5 BAG_DIR_OVERRIDE="$MFBAG" RUN_START=7 REPEAT=3 RECORD_KF=1 ./run_fusion_study.sh F8
else echo "SKIP 1: no Multi Floor bags found"; fi
if [ -d "$LCBAG" ]; then
  echo "=== 2. Long Corridor F16 runs 4-6 (0.5x)"
  PLAY_RATE=0.5 SEQ_ENV=~/runs_corridor/seq.env BAG_DIR_OVERRIDE="$LCBAG" RUN_START=4 REPEAT=3 RECORD_KF=1 ./run_fusion_study.sh F16
else echo "SKIP 2: $LCBAG not found (drive not mounted?)"; fi
if [ -d "$MFBAG" ]; then
  echo "=== 3. Multi Floor F16 runs 4-6 (0.5x)"
  PLAY_RATE=0.5 BAG_DIR_OVERRIDE="$MFBAG" RUN_START=4 REPEAT=3 RECORD_KF=1 ./run_fusion_study.sh F16
fi
echo "=== external drive no longer needed from here ($(date +%T))"
echo "=== 4. Corridor02 F16 runs 4-6 (0.33x)"
PLAY_RATE=0.33 SEQ_ENV=~/runs_corridor2/seq.env RUN_START=4 REPEAT=3 RECORD_KF=1 ./run_fusion_study.sh F16

# the back end prints at most 12 loops per run; print up to 400 (edited in place, backup kept)
[ -f run_backend.py.orig ] || cp run_backend.py run_backend.py.orig
sed -i 's/span\[:12\]/span[:400]/' run_backend.py   # backend_multi.py calls run_backend.py; original kept as run_backend.py.orig
backend() {   # dir gt extrinsics
  local tags
  tags=$(ls "$1"/keyframes_F16_kf_run*.npz 2>/dev/null | sed 's|.*/keyframes_||; s|\.npz$||' | paste -sd, -)
  [ -z "$tags" ] && { echo "no F16 keyframes in $1"; return; }
  echo "=== back end $1: $tags"
  (export EXTRINSIC_YAML="$3"; ~/venv_backend/bin/python backend_multi.py --dir "$1" --tags "$tags" --gt "$2" \
     --models none,iso --extra "--odom-sigma 1.46,0.054 --calib-end 0") > "$1/backend_F16_n6.out" 2>&1
  tail -n 14 "$1/backend_F16_n6.out"
}
backend ~/runs_corridor  "$(seqval ~/runs_corridor/seq.env GT)"  "$(seqval ~/runs_corridor/seq.env EXTRINSIC_YAML)"
backend ~/runs_v2        ~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv ""
backend ~/runs_corridor2 "$(seqval ~/runs_corridor2/seq.env GT)" "$(seqval ~/runs_corridor2/seq.env EXTRINSIC_YAML)"

Z=~/Downloads/for_claude11.zip; T=$(mktemp -d)
for pair in LC:~/runs_corridor MF:~/runs_v2 C02:~/runs_corridor2; do
  p=${pair%%:*}; d=$(eval echo ${pair#*:})
  cp "$d/results_index.csv" "$T/${p}_results_index.csv" 2>/dev/null
  cp "$d/failed_runs.csv" "$T/${p}_failed_runs.csv" 2>/dev/null
  for f in "$d"/switching_log_v2_F16_kf_run*.csv "$d"/switching_log_v2_F8_kf_run*.csv "$d"/ate_F16_kf_run*.txt "$d"/ate_F8_kf_run*.txt \
           "$d"/summary_F16_kf_run*.txt "$d"/summary_F8_kf_run*.txt "$d"/node_F16_kf_run*.out "$d"/backend_F16_n6.out "$d"/backend_F16_kf_run*.log; do
    [ -f "$f" ] && cp "$f" "$T/${p}_$(basename "$f")"
  done
done
rm -f "$Z"; (cd "$T" && zip -q "$Z" *) && echo "zip: $Z ($(du -h "$Z" | cut -f1))"
rm -rf "$T"
echo "ALL_DONE $(date +%T)"
