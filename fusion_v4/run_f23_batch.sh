#!/usr/bin/env bash
# Live test of F23 = F21 + anchored WARMUP->FUSED handover (docs/results/F22_Handover_Anchor.md, section 5), front end only
# (the Switch-SLAM target has no loop closure), 3 runs per development sequence, then one zip for upload.
# CFG=F22 runs the ablation (F20 + anchor) instead.  ONLY="MF LC" limits the sequences.  REPEAT=1 for a single run each.
# Start:  setsid nohup systemd-inhibit --what=sleep:idle bash run_f23_batch.sh > ~/f23_batch.log 2>&1 < /dev/null &
set -u
cd "$(dirname "$0")" || exit 1
CFG=${CFG:-F23}; REPEAT=${REPEAT:-3}; ONLY=${ONLY:-"MF LC C02"}
HDD="/media/$USER/One Touch1/laptop_bags"
echo "start $(date +%T)  config $CFG  repeat $REPEAT  sequences $ONLY"
grep -q "\[$CFG\]" run_fusion_study.sh || { echo "run_fusion_study.sh has no $CFG config (apply the F22/F23 patch)"; exit 1; }
python3 -c "import fusion_core as f, inspect; assert 'handover' in inspect.signature(f.FusionCore).parameters" \
  || { echo "fusion_core.py has no handover option (apply the F22/F23 patch)"; exit 1; }
python3 test_handover.py > /dev/null || { echo "test_handover.py failed"; exit 1; }
want() { case " $ONLY " in *" $1 "*) return 0;; esac; return 1; }

if want MF; then
  MFDIR=""
  for d in multifloor MultiFloor Multi_Floor multi_floor RosBag; do [ -d "$HDD/$d" ] && ls "$HDD/$d"/*.bag >/dev/null 2>&1 && { MFDIR="$HDD/$d"; break; }; done
  if [ -n "$MFDIR" ]; then
    echo "=== Multi Floor (0.5x) from $MFDIR"
    PLAY_RATE=0.5 BAG_DIR_OVERRIDE="$MFDIR" REPEAT=$REPEAT RECORD_KF=1 FRONT=aloam ./run_fusion_study.sh $CFG
  else echo "SKIP Multi Floor: no bag folder under $HDD (drive not mounted?)"; fi
fi
if want LC; then
  if ls "$HDD/Long_Corridor_Rosbag"/*.bag >/dev/null 2>&1; then
    echo "=== Long Corridor (0.5x)"
    PLAY_RATE=0.5 SEQ_ENV=~/runs_corridor/seq.env BAG_DIR_OVERRIDE="$HDD/Long_Corridor_Rosbag" REPEAT=$REPEAT RECORD_KF=1 FRONT=aloam ./run_fusion_study.sh $CFG
  else echo "SKIP Long Corridor: no .bag in $HDD/Long_Corridor_Rosbag (drive not mounted?)"; fi
fi
if want C02; then
  echo "=== Corridor02 (0.33x)"
  PLAY_RATE=0.33 SEQ_ENV=~/runs_corridor2/seq.env REPEAT=$REPEAT RECORD_KF=1 FRONT=aloam ./run_fusion_study.sh $CFG
fi

Z=~/Downloads/for_claude_$CFG.zip; T=$(mktemp -d)
for pair in LC:~/runs_corridor MF:~/runs_v2 C02:~/runs_corridor2; do
  p=${pair%%:*}; d=$(eval echo ${pair#*:})
  cp "$d/results_index.csv" "$T/${p}_results_index.csv" 2>/dev/null
  cp "$d/failed_runs.csv" "$T/${p}_failed_runs.csv" 2>/dev/null
  for f in "$d"/switching_log_v2_${CFG}_kf_run*.csv "$d"/ate_${CFG}_kf_run*.txt "$d"/summary_${CFG}_kf_run*.txt "$d"/node_${CFG}_kf_run*.out \
           "$d"/keyframes_${CFG}_kf_run*.npz; do
    [ -f "$f" ] && cp "$f" "$T/${p}_$(basename "$f")"
  done
done
rm -f "$Z"; (cd "$T" && zip -q "$Z" *) && echo "zip: $Z ($(du -h "$Z" | cut -f1))"
rm -rf "$T"
echo "=== results (ATE RMSE / max, m)"
for pair in MF:~/runs_v2 LC:~/runs_corridor C02:~/runs_corridor2; do
  p=${pair%%:*}; d=$(eval echo ${pair#*:})
  grep "^${CFG}_kf_run" "$d/results_index.csv" 2>/dev/null | awk -F, -v s=$p '{print s, $1, $(NF-2), $(NF-1)}'
done
echo "ALL_DONE $(date +%T)"
