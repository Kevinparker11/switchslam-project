#!/bin/bash
# Recreate the two containers on a new PC from the output of tools/export_images.sh.
#   bash tools/import_images.sh [INDIR]         default INDIR=$HOME/switchslam_export
# The catkin workspaces are unpacked under $HOME (catkin_ws_rebuild / catkin_ws_mono, the names used on the original laptop).
set -e
IN=${1:-$HOME/switchslam_export}; TAG=${TAG:-$(docker load -i "$IN/images.tar.gz" | sed -n 's/.*switchslam_gpu_v2:\(export-[0-9]*\).*/\1/p' | head -1)}
[ -n "$TAG" ] || { echo "could not determine the image tag"; exit 1; }
GPU_WS=$HOME/catkin_ws_rebuild; VINS_WS=$HOME/catkin_ws_mono
[ -e "$GPU_WS" ]  || { mkdir -p "$(dirname "$GPU_WS")";  tar xzf "$IN/ws_gpu_catkin_ws.tgz"  -C "$HOME"; }
[ -e "$VINS_WS" ] || { tar xzf "$IN/ws_vins_catkin_ws.tgz" -C "$HOME"; }
docker network inspect vins_bridge >/dev/null 2>&1 || docker network create vins_bridge
docker pull ros:noetic
docker rm -f switchslam_gpu_v2 vinsmono_test >/dev/null 2>&1 || true
xhost +local: >/dev/null 2>&1 || true      # only needed for rviz/gazebo windows; harmless otherwise
docker run -dit --name switchslam_gpu_v2 --network vins_bridge -e DISPLAY=${DISPLAY:-:1} \
    -v /tmp/.X11-unix:/tmp/.X11-unix -v "$GPU_WS":/root/catkin_ws  switchslam_gpu_v2:$TAG bash
docker run -dit --name vinsmono_test    --network vins_bridge -e DISPLAY=${DISPLAY:-:1} \
    -v /tmp/.X11-unix:/tmp/.X11-unix -v "$VINS_WS":/root/catkin_ws vinsmono_test:$TAG bash
docker ps
echo "next: cd fusion_v4 && SMOKE=1 FRONT=aloam ./run_fusion_study.sh F8   (INSTALL.md section 7)"
