#!/usr/bin/env bash
# Before the first GenZ-LIO run on a sequence: does the LiDAR topic carry per-point timing (GenZ-LIO deskews with it)?
# Fast: reads only the bag index and the first LiDAR scan (seconds, even for multi-GB bags on a USB drive).
# usage: bash check_bag_fields.sh "<bag file or folder>" [more]
HERE=$(cd "$(dirname "$0")" && pwd)
for P in "$@"; do
  if [ -d "$P" ]; then BAGS=$(find "$P" -maxdepth 2 -name '*.bag' | sort | head -1); else BAGS=$P; fi
  echo "== $P"
  [ -n "$BAGS" ] && python3 -I "$HERE/check_bag_fields.py" "$BAGS" || echo "  no .bag found"
done
