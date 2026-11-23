#!/usr/bin/env bash
# Stock LIO-SAM (original repository, pinned commit) on one of our bag sequences, in its own container.
#   fusion_v4/stock_liosam/run_liosam.sh <mf|lc|c02|cave02|geode>
# environment: REPEAT=1  RUN_START=1  PLAY_RATE=<sequence default, same as the stock A-LOAM run>  FORCE=0
#              ADAPT=auto|off  OUT_ROOT=$HOME/runs_liosam  IMAGE=liosam_stock  BAGS_ROOT=... BAG_DIR=... GT=... (see seq/*.env)
#              ALLOW_LOCAL_BAGS=0  REPLAY_LOCK=$HOME/.replay.lock
# BAGS_ROOT, if unset, is the laptop_bags folder of the mounted drive ("One Touch2" or "One Touch1"). The run refuses to
# start unless the bag folder is on a mounted drive, and every replay holds flock on ~/.replay.lock (shared with F35).
# A preflight reads the bag first. If stock LIO-SAM cannot work on it (no IMU orientation, no ring) the run is NOT started
# and NOT_APPLICABLE.txt says why; FORCE=1 runs it anyway and the result is labelled as forced.
set -u
NAME=${1:?sequence: mf | lc | c02 | cave02 | geode}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FUSION=$(cd "$HERE/.." && pwd); REPO=$(cd "$FUSION/.." && pwd)
[ -f "$HERE/seq/$NAME.env" ] || { echo "no seq/$NAME.env"; exit 1; }
source "$FUSION/baselines/common.sh"
[ -n "${BAG_DIR:-}" ] || bl_find_bags_root
source "$HERE/seq/$NAME.env"
bl_require_mounted "$BAG_DIR"
IMAGE=${IMAGE:-liosam_stock}; REPEAT=${REPEAT:-1}; RUN_START=${RUN_START:-1}; FORCE=${FORCE:-0}; ADAPT=${ADAPT:-auto}
OUT=${OUT_ROOT:-$HOME/runs_liosam}/$NAME; mkdir -p "$OUT"
[ -d "$BAG_DIR" ] || { echo "bag folder not found: $BAG_DIR"; exit 1; }
[ -f "$GT" ] || { echo "ground truth not found: $GT"; exit 1; }
BAGS=$(cd "$BAG_DIR" && ls -1 *.bag 2>/dev/null | sort | tr '\n' ' ')
[ -n "$BAGS" ] || { echo "no .bag in $BAG_DIR"; exit 1; }
bl_require_docker
docker image inspect "$IMAGE" > /dev/null 2>&1 || { echo "building image $IMAGE (first time only)"; docker build --network host -t "$IMAGE" "$HERE" || exit 1; }
dr() { docker run --rm -v "$BAG_DIR":/bags:ro -v "$REPO":/repo:ro "$@"; }

echo "== preflight $NAME ($BAG_DIR)"
FIRST=${BAGS%% *}
bl_lock
dr --entrypoint bash "$IMAGE" -c "source /opt/ros/noetic/setup.bash; python3 /repo/fusion_v4/stock_liosam/preflight.py --imu $IMU_TOPIC ${POINTS_TOPIC:+--points $POINTS_TOPIC} ${PACKETS_TOPIC:+--packets $PACKETS_TOPIC} /bags/$FIRST" 2>&1 | tee "$OUT/preflight.txt"
bl_unlock
VERDICT=$(grep '^VERDICT=' "$OUT/preflight.txt" | head -1 | cut -d= -f2-)
AN=$(grep '^ADAPT_NAN=' "$OUT/preflight.txt" | cut -d= -f2); AT=$(grep '^ADAPT_TIME=' "$OUT/preflight.txt" | cut -d= -f2)
[ "$ADAPT" = off ] && { AN=0; AT=0; }
if [ "$VERDICT" != "OK" ]; then
  echo "$VERDICT" > "$OUT/NOT_APPLICABLE.txt"
  if [ "$FORCE" != 1 ]; then echo; echo "stock LIO-SAM not run on $NAME: $VERDICT"; echo "(FORCE=1 runs it anyway; the result is then not a stock result)"; exit 0; fi
  echo "FORCE=1: running although: $VERDICT"
fi

for k in $(seq "$RUN_START" $((RUN_START + REPEAT - 1))); do
  RD="$OUT/run$k"; mkdir -p "$RD"; rm -f "$RD"/*
  echo "== $NAME run$k  rate ${PLAY_RATE}  adapter: nan=${AN:-0} time=${AT:-0}  ($(date +%H:%M:%S))"
  bl_lock
  dr -v "$RD":/out -e IMU_TOPIC="$IMU_TOPIC" -e PACKETS_TOPIC="${PACKETS_TOPIC:-}" -e POINTS_TOPIC="${POINTS_TOPIC:-}" \
     -e RATE="$PLAY_RATE" -e BAGS="$BAGS" -e EXTR="/repo/fusion_v4/stock_liosam/seq/$EXTRINSICS" -e ADAPT_NAN="${AN:-0}" -e ADAPT_TIME="${AT:-0}" \
     --entrypoint bash "$IMAGE" /repo/fusion_v4/stock_liosam/inside.sh
  bl_unlock
  [ "$VERDICT" != "OK" ] && echo "FORCED RUN: $VERDICT" > "$RD/FORCED.txt"
done

echo; echo "stock LIO-SAM, $NAME, against $GT"
for k in $(seq "$RUN_START" $((RUN_START + REPEAT - 1))); do
  RD="$OUT/run$k"
  printf "run%s  crashes(respawns)=%s  " "$k" "$(cat "$RD/crashes.txt" 2>/dev/null || echo ?)"
  [ -f "$RD/FORCED.txt" ] && printf "[FORCED] "
  (cd "$FUSION" && python3 stock_liosam/score_tum.py --gt "$GT" --est "$RD/odom.tum" | tail -1)
done
