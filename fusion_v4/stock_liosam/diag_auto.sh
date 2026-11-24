#!/usr/bin/env bash
# Unscored diagnosis of stock LIO-SAM on a packet sequence (lc or mf), every step in one background job. Nothing written
# here is a table number: the outputs go to $DIAG_ROOT (default ~/runs_liosam_diag), never to ~/runs_liosam.
#   nohup fusion_v4/stock_liosam/diag_auto.sh lc > /dev/null 2>&1 &      (then read <folder>/summary.txt)
# Steps
#   1. inputs: per-window IMU and LiDAR table of the bag, scan-header packet, IMU stamps and |acc| (diag_inputs_window.py)
#   2. ground-truth motion per window (speed, turning)
#   3. one LIO-SAM run per variant, each followed by diag_error_time.py and the count of IMU-preintegration resets:
#        timefix   per-point time shifted to start at 0 if the preflight finds it negative (the existing adapter), upstream voxels
#                  (skipped when the time is not negative: it would repeat the scored runs)
#        indoor    adapter off (as the scored runs), upstream's documented indoor voxel values
#        both      adapter as the preflight says, indoor voxel values
#   VARIANTS="indoor" (space separated) runs a subset. Every replay holds the shared replay lock.
set -u
NAME=${1:-lc}
case "$NAME" in lc|mf) ;; *) echo "diag_auto.sh is for the packet sequences lc and mf"; exit 1 ;; esac
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FUSION=$(cd "$HERE/.." && pwd); REPO=$(cd "$FUSION/.." && pwd)
source "$FUSION/baselines/common.sh"
[ -n "${BAG_DIR:-}" ] || bl_find_bags_root
source "$HERE/seq/$NAME.env"
bl_require_mounted "$BAG_DIR"
bl_require_docker
IMAGE=${IMAGE:-liosam_stock}
D=${DIAG_ROOT:-$HOME/runs_liosam_diag}/${NAME}_$(date +%m%d_%H%M)
mkdir -p "$D"
S="$D/summary.txt"
say() { echo "$*" | tee -a "$S"; }
echo running > "$D/STATUS"
say "== unscored LIO-SAM diagnosis, $NAME, $(date '+%F %T'), repo $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)"
say "folder $D"
BAGS=$(cd "$BAG_DIR" && ls -1 *.bag | sort | tr '\n' ' ')
BP=""; for b in $BAGS; do BP="$BP /bags/$b"; done

say ""; say "-- 1. inputs (first 150 s of the bag)"
bl_lock
docker run --rm -v "$BAG_DIR":/bags:ro -v "$REPO":/repo:ro --entrypoint bash "$IMAGE" -c \
  "source /opt/ros/noetic/setup.bash; python3 /repo/fusion_v4/stock_liosam/diag_inputs_window.py --imu $IMU_TOPIC --lidar ${PACKETS_TOPIC:-$POINTS_TOPIC} --span 150 $BP" \
  > "$D/inputs.txt" 2>&1
bl_unlock
grep -E "^(t0|IMU|scan header|no messages)" "$D/inputs.txt" | tee -a "$S"

say ""; say "-- 2. ground-truth motion"
(cd "$FUSION" && python3 stock_liosam/diag_inputs_window.py --gt "$GT" --span 150) > "$D/gt.txt" 2>&1
say "(table in gt.txt)"

NEG=0; grep -q "NEGATIVE" "$D/inputs.txt" && NEG=1
VARIANTS=${VARIANTS:-timefix indoor both}
for V in $VARIANTS; do
  case "$V" in
    timefix) [ "$NEG" = 1 ] || { say ""; say "-- variant timefix skipped: per-point time is not negative"; continue; }; AD=auto; PR=upstream ;;
    indoor)  AD=off;  PR=indoor ;;
    both)    AD=auto; PR=indoor ;;
    *) say "unknown variant $V"; continue ;;
  esac
  say ""; say "-- 3. variant $V (adapter $AD, profile $PR), started $(date +%T)"
  OUT_ROOT="$D/$V" REPEAT=1 ADAPT=$AD PROFILE=$PR "$HERE/run_liosam.sh" "$NAME" > "$D/$V.log" 2>&1
  R="$D/$V/$NAME/run1"
  grep -E "^(TIME|TIME_RANGE_S|SCAN_HEADER_IS_PACKET|ADAPT_TIME)=" "$D/$V/$NAME/preflight.txt" 2>/dev/null | tr '\n' ' ' | tee -a "$S"; echo | tee -a "$S"
  say "adapter: $(cat "$R/adapter_used.txt" 2>/dev/null)   profile: $(cat "$R/profile.txt" 2>/dev/null)   respawns: $(cat "$R/crashes.txt" 2>/dev/null)   IMU-preintegration resets: $(grep -c 'reset IMU' "$R/liosam.log" 2>/dev/null)   not-enough-features: $(grep -c 'Not enough features' "$R/liosam.log" 2>/dev/null)"
  if [ -s "$R/odom.tum" ]; then
    (cd "$FUSION" && python3 stock_liosam/diag_error_time.py --gt "$GT" --est "$R/odom.tum") > "$D/$V.diag.txt" 2>&1
    grep -E "^(poses|estimated path|error first|full-span)" "$D/$V.diag.txt" | tee -a "$S"
  else
    say "no poses recorded (see $V.log)"
  fi
done
say ""; say "== done $(date +%T)"
echo done > "$D/STATUS"
