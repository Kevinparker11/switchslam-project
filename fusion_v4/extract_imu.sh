#!/usr/bin/env bash
# usage: bash extract_imu.sh BAG_DIR OUT.csv [topic] [seconds]
#   seconds = only the first N seconds of the bag (jumps via the bag index, fast on a big bag); omit for the whole bag.
#   Run it from fusion_v4:  cd ~/switchslam-project/fusion_v4
set -e
BAG_DIR=$(cd "$1" && pwd); OUT=$(realpath "$2"); HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); TOPIC=${3:-/imu/data,/cmu_sp1/imu/data}; SECS=${4:-0}
docker run --rm -v "$BAG_DIR":/bags:ro -v "$HERE":/code:ro -v "$(dirname "$OUT")":/out --entrypoint bash ros:noetic -c \
  "source /opt/ros/noetic/setup.bash && python3 -u /code/extract_imu.py /bags /out/$(basename "$OUT") $TOPIC $SECS"
