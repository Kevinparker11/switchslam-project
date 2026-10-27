#!/usr/bin/env bash
# Cave02 control, full batch (unattended, about 5.5 h at 0.5x; the bag is 956 s, so each run is about 32 min).
# Order: F8 and F16 alternate (run 1, 2, 3), then the VINS-primary control F0 (runs 1-3).  Nothing is tuned.
# PRE-REGISTERED PASS RULE (written 19 Oct 2026, before any Cave02 result):
#   1. SAH must switch itself off in the cave: in the F16 logs the heading correction applied (sah_total_deg) stays small
#      (final total under about 2 degrees) and few keyframes are accepted (sah_acc).
#   2. F16 mean ATE within 0.2 m of F8 mean ATE (differences under ~0.1-0.3 m are ties in this project).
#   If F16 is clearly worse than F8, that is recorded as a failure of the null test. No constant is changed afterwards.
# Runs already in results_index.csv are skipped, so it is safe to restart after an interruption.
# Start:  cd ~/switchslam_channelT/fusion_v3 && setsid nohup systemd-inhibit --what=sleep:idle bash ~/Downloads/run_cave_batch.sh > ~/cave_batch.log 2>&1 < /dev/null &
set -u
cd "${FUSION_V3_DIR:-$HOME/switchslam_channelT/fusion_v3}" || exit 1
[ -f run_fusion_study.sh ] || { echo "fusion_v3 folder not found (run_fusion_study.sh)"; exit 1; }
ENV=~/runs_cave02/seq.env; OUT=~/runs_cave02
[ -f "$ENV" ] || { echo "$ENV not found"; exit 1; }
bash -c "source '$ENV' >/dev/null 2>&1; [ -d \"\$BAG_DIR\" ] && [ -f \"\$GT\" ]" || { echo "bag folder or ground truth in seq.env not found (drive mounted?)"; exit 1; }
echo "start $(date +%T)"
run() {   # config run_number
  echo "=== $1 run $2 $(date +%T)"
  PLAY_RATE=0.5 SEQ_ENV="$ENV" RUN_START=$2 REPEAT=1 ./run_fusion_study.sh $1
}
for r in 1 2 3; do run F8 $r; run F16 $r; done
echo "=== F8 and F16 done $(date +%T): upload the zip now if you like, F0 follows"
for r in 1 2 3; do run F0 $r; done

# package (no bags; logs, scores and the ground truth so the numbers can be re-checked)
Z=~/Downloads/for_claude14.zip; T=$(mktemp -d)
for f in "$OUT"/results_index.csv "$OUT"/failed_runs.csv "$OUT"/seq.env "$OUT"/rosbag_info.txt "$OUT"/header_stamps.txt \
         "$OUT"/switching_log_v2_F*_run*.csv "$OUT"/ate_F*_run*.txt "$OUT"/summary_F*_run*.txt "$OUT"/node_F*_run*.out; do
  [ -f "$f" ] && cp "$f" "$T"/
done
for f in "$OUT"/vins_F*_run*.out; do [ -f "$f" ] && [ "$(stat -c %s "$f")" -lt 5000000 ] && cp "$f" "$T"/; done
bash -c "source '$ENV' >/dev/null 2>&1; cp \"\$GT\" '$T'/cave02_gt.txt"
rm -f "$Z"; (cd "$T" && zip -q "$Z" *) && echo "zip: $Z ($(du -h "$Z" | cut -f1))"
rm -rf "$T"
echo "ALL_DONE $(date +%T)"
