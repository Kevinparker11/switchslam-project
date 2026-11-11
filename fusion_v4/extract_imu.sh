#!/usr/bin/env bash
# usage: bash extract_imu.sh BAG_DIR OUT.csv [topic]    one pass over the bag, no replay, about a minute
set -e
BAG_DIR=$(cd "$1" && pwd); OUT=$(realpath "$2"); HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); TOPIC=${3:-/imu/data,/cmu_sp1/imu/data}
docker run --rm -v "$BAG_DIR":/bags:ro -v "$HERE":/code:ro -v "$(dirname "$OUT")":/out --entrypoint bash ros:noetic -c \
  "source /opt/ros/noetic/setup.bash && python3 /code/extract_imu.py /bags /out/$(basename "$OUT") $TOPIC"
