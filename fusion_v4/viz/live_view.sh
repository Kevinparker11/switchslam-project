#!/usr/bin/env bash
# RViz view of a live bag run, started in a SECOND terminal right after the batch / run_fusion_study.sh has been launched.
#   [FORCE=1] bash viz/live_view.sh [GT_FILE]    (FORCE=1 opens RViz at once, without waiting for the first pose message)
#   bash viz/live_view.sh [GT_FILE]        e.g.  bash viz/live_view.sh ~/runs_corridor/lc_gt.txt
# Shows: A-LOAM map and current scan, A-LOAM mapped path (orange), fused path F20/F22/F23 (green line), ground truth (white).
# Use ONE run (REPEAT=1 ONLY="LC"): the study script restarts roscore for every run, and RViz does not follow a restarted master.
# Needs the X server open to docker (xhost) and the image osrf/ros:noetic-desktop-full (about 3 GB, pulled once).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; GT=${1:-}; GPU_C=${GPU_C:-switchslam_gpu_v2}; IMG=${IMG:-osrf/ros:noetic-desktop-full}
GPU=$(docker inspect -f '{{.NetworkSettings.Networks.vins_bridge.IPAddress}}' "$GPU_C") || exit 1
[ -n "${DISPLAY:-}" ] || { echo "DISPLAY is empty: run this in a terminal on the laptop's desktop session"; exit 1; }
xhost +local:docker >/dev/null 2>&1 || echo "xhost not found: install x11-xserver-utils if the window does not open"
MNT=(); GTARG=""
if [ -n "$GT" ]; then
  [ -f "$GT" ] || { echo "ground-truth file not found: $GT  (run without the argument to skip it)"; exit 1; }
  MNT=(-v "$(readlink -f "$GT"):/gt.txt:ro"); GTARG=/gt.txt
fi
echo "viewer waits for a live run on $GPU (start the batch in the other terminal; it reopens for every new run) ..."
exec docker run --rm -it --network vins_bridge -e DISPLAY="$DISPLAY" -e QT_X11_NO_MITSHM=1 -e FORCE="${FORCE:-}" -e ROS_MASTER_URI="http://$GPU:11311" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw -v "$HERE":/viz:ro "${MNT[@]}" --entrypoint bash "$IMG" /viz/run_in_container.sh "${GTARG:-}"
