#!/usr/bin/env bash
# Stock FAST-LIVO (original repository, pinned commit) on one of our bag sequences, in its own container.
#   fusion_v4/stock_fastlivo/run_fastlivo.sh <mf|lc|c02|cave02|geode>
# environment: REPEAT=1  RUN_START=1  PLAY_RATE=<sequence default, same as the stock LIO-SAM / A-LOAM run>  FORCE=0
#              ADAPT=auto|off  OUT_ROOT=$HOME/runs_fastlivo  IMAGE=fastlivo_stock  BAGS_ROOT=... BAG_DIR=... BAG_FILES="a.bag b.bag" GT=...
#              SMOKE=1      play the first SMOKE_SECONDS (60) only, print pass or fail, nothing is scored
#              SLICE=1      smoke test on the desktop slices: BAG_DIR=$HOME/slices, BAG_FILES=<seq>_70s.bag, bags on the local disk
#              ALLOW_LOCAL_BAGS=0  REPLAY_LOCK=$HOME/.replay.lock
# The runner never builds: if the image is missing it says how to load it. A preflight reads the first bag; if stock FAST-LIVO cannot
# work on it (no per-point time, no camera topic; FAST-LIVO does not need an IMU orientation) the run is NOT started and NOT_APPLICABLE.txt says why (FORCE=1 overrides,
# the result is then labelled FORCED). BAGS_ROOT, if unset, is the laptop_bags folder of the mounted drive. The run refuses to start
# unless the bag folder is on a mounted drive, and the preflight and every replay hold flock on ~/.replay.lock (shared with F35).
set -u
NAME=${1:?sequence: mf | lc | c02 | cave02 | geode}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FUSION=$(cd "$HERE/.." && pwd); REPO=$(cd "$FUSION/.." && pwd)
[ -f "$HERE/seq/$NAME.env" ] || { echo "no seq/$NAME.env"; exit 1; }
source "$FUSION/baselines/common.sh"
SLICE=${SLICE:-0}; SMOKE=${SMOKE:-0}
if [ "$SLICE" = 1 ]; then
  SMOKE=1; ALLOW_LOCAL_BAGS=1; BAG_DIR=${BAG_DIR:-$HOME/slices}; BAG_FILES=${BAG_FILES:-${NAME}_70s.bag}
  GT=${GT:-/dev/null}; OUT_ROOT=${OUT_ROOT:-$HOME/smoke_fastlivo}
fi
[ -n "${BAG_DIR:-}" ] || bl_find_bags_root
source "$HERE/seq/$NAME.env"
bl_require_mounted "$BAG_DIR"
IMAGE=${IMAGE:-fastlivo_stock}; REPEAT=${REPEAT:-1}; RUN_START=${RUN_START:-1}; FORCE=${FORCE:-0}; ADAPT=${ADAPT:-auto}
SMOKE_SECONDS=${SMOKE_SECONDS:-60}; PLAY_SECONDS=0; [ "$SMOKE" = 1 ] && PLAY_SECONDS=$SMOKE_SECONDS
OUT=${OUT_ROOT:-$HOME/runs_fastlivo}/$NAME; mkdir -p "$OUT"
[ -d "$BAG_DIR" ] || { echo "bag folder not found: $BAG_DIR"; exit 1; }
[ "$SMOKE" = 1 ] || [ -f "$GT" ] || { echo "ground truth not found: $GT"; exit 1; }
BAGS=${BAG_FILES:-$(cd "$BAG_DIR" && ls -1 *.bag 2>/dev/null | sort | tr '\n' ' ')}
[ -n "$BAGS" ] || { echo "no .bag in $BAG_DIR"; exit 1; }
for b in $BAGS; do [ -f "$BAG_DIR/$b" ] || { echo "bag not found: $BAG_DIR/$b"; exit 1; }; done
bl_require_docker
docker image inspect "$IMAGE" > /dev/null 2>&1 || {
  echo "image $IMAGE is not here. This runner never builds. Load it first:  $FUSION/baselines/load_image.sh $IMAGE"
  echo "(on the desktop that builds it:  docker build --network host -t $IMAGE $HERE)"; exit 1; }
echo "image $IMAGE: upstream commit $(docker image inspect "$IMAGE" --format '{{index .Config.Labels "baseline.upstream_commit"}}')"
dr() { docker run --rm -v "$BAG_DIR":/bags:ro -v "$REPO":/repo:ro "$@"; }

echo "== preflight $NAME ($BAG_DIR)"
FIRST=${BAGS%% *}
bl_lock
{ dr --entrypoint bash "$IMAGE" -c "source /opt/ros/noetic/setup.bash; python3 /repo/fusion_v4/stock_liosam/preflight.py --imu $IMU_TOPIC ${POINTS_TOPIC:+--points $POINTS_TOPIC} ${PACKETS_TOPIC:+--packets $PACKETS_TOPIC} /bags/$FIRST; \
  python3 /repo/fusion_v4/stock_fastlivo/cam_check.py --topic $([ "${CAM_COMPRESSED:-0}" = 1 ] && echo "${CAM_TOPIC%/image_raw}/compressed" || echo "$CAM_TOPIC") /bags/$FIRST" 2>&1; } | tee "$OUT/preflight.txt"
bl_unlock
VERDICT=$(grep '^VERDICT=' "$OUT/preflight.txt" | head -1 | cut -d= -f2-)
# the shared preflight judges for LIO-SAM (9-axis IMU, ring). FAST-LIVO reads neither: its verdict only needs the per-point time of the cloud
if [ "$VERDICT" != NOT_RUN ]; then
  TIMEV=$(grep '^TIME=' "$OUT/preflight.txt" | head -1 | cut -d= -f2-)
  case "$TIMEV" in missing|empty|wrongtype*) VERDICT="NOT_APPLICABLE: per-point time $TIMEV (FAST-LIVO deskews with it)";; *) VERDICT=OK;; esac
fi
grep -q '^CAMERA_TOPIC_OK=yes' "$OUT/preflight.txt" || { [ "$VERDICT" = OK ] && VERDICT="NOT_APPLICABLE: camera topic missing ($(grep '^CAMERA_TOPIC_OK' "$OUT/preflight.txt" | head -1))"; }
AN=$(grep '^ADAPT_NAN=' "$OUT/preflight.txt" | cut -d= -f2); AT=$(grep '^ADAPT_TIME=' "$OUT/preflight.txt" | cut -d= -f2)
[ "$ADAPT" = off ] && { AN=0; AT=0; }
if [ "$VERDICT" != "OK" ]; then
  echo "$VERDICT" > "$OUT/NOT_APPLICABLE.txt"
  if [ "$FORCE" != 1 ]; then echo; echo "stock FAST-LIVO not run on $NAME: $VERDICT"; echo "(FORCE=1 runs it anyway; the result is then not a stock result)"; exit 0; fi
  echo "FORCE=1: running although: $VERDICT"
fi

for k in $(seq "$RUN_START" $((RUN_START + REPEAT - 1))); do
  RD="$OUT/run$k"; mkdir -p "$RD"; rm -f "$RD"/*
  echo "== $NAME run$k  rate ${PLAY_RATE}  adapter: nan=${AN:-0} time=${AT:-0}  ($(date +%H:%M:%S))"
  bl_lock
  dr -v "$RD":/out -e IMU_TOPIC="$IMU_TOPIC" -e PACKETS_TOPIC="${PACKETS_TOPIC:-}" -e POINTS_TOPIC="${POINTS_TOPIC:-}" \
     -e CAM_TOPIC="$CAM_TOPIC" -e CAM_COMPRESSED="${CAM_COMPRESSED:-0}" -e CAM_CONFIG="$CAM_CONFIG" -e PLAY_SECONDS="$PLAY_SECONDS" \
     -e RATE="$PLAY_RATE" -e BAGS="$BAGS" -e EXTR="/repo/fusion_v4/stock_liosam/seq/$EXTRINSICS" -e ADAPT_NAN="${AN:-0}" -e ADAPT_TIME="${AT:-0}" \
     --entrypoint bash "$IMAGE" /repo/fusion_v4/stock_fastlivo/inside.sh
  bl_unlock
  [ "$VERDICT" != "OK" ] && echo "FORCED RUN: $VERDICT" > "$RD/FORCED.txt"
done

echo
if [ "$SMOKE" = 1 ]; then
  echo "SMOKE TEST (first ${SMOKE_SECONDS} s, not scored), $NAME"
  for k in $(seq "$RUN_START" $((RUN_START + REPEAT - 1))); do
    RD="$OUT/run$k"; P=$(wc -l < "$RD/odom.tum" 2>/dev/null || echo 0); C=$(cat "$RD/crashes.txt" 2>/dev/null || echo ?)
    if [ "$P" -ge 100 ] && [ "$C" = 0 ]; then R=PASS; else R=FAIL; fi
    echo "run$k  poses=$P (need at least 100)  node deaths=$C  $R"
  done
  exit 0
fi
echo "stock FAST-LIVO, $NAME, against $GT"
for k in $(seq "$RUN_START" $((RUN_START + REPEAT - 1))); do
  RD="$OUT/run$k"
  printf "run%s  node deaths=%s  " "$k" "$(cat "$RD/crashes.txt" 2>/dev/null || echo ?)"
  [ -f "$RD/FORCED.txt" ] && printf "[FORCED] "
  (cd "$FUSION" && python3 stock_liosam/score_tum.py --gt "$GT" --est "$RD/odom.tum" | tail -1)
done
