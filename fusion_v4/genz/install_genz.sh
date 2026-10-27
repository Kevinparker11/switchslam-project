#!/usr/bin/env bash
# Build GenZ-LIO (pinned commit, information patch applied) inside the ROS Noetic container used by the runs.
# The master system (fusion_v3, A-LOAM in /root/catkin_ws) is not touched: GenZ-LIO goes to its own
# workspace /root/genz_ws. About 10-20 min (catkin_make -j2).
# Start:  bash ~/switchslam_channelT/fusion_v4/genz/install_genz.sh 2>&1 | tee ~/install_genz.log
set -u
GPU_C=${GPU_C:-switchslam_gpu_v2}
COMMIT=bf444f7a747ed3da8548b56b49c14f207e8d49bb        # GenZ-LIO version read and patched on 21 Oct 2026
HERE=$(cd "$(dirname "$0")" && pwd)
ROS1="source /opt/ros/noetic/setup.bash"
[ "$(docker inspect -f '{{.State.Running}}' $GPU_C 2>/dev/null)" = "true" ] || { echo "container $GPU_C is not running (docker start $GPU_C)"; exit 1; }

# 1. source on the host (the container may have no git or network), pinned
SRC=~/genz-lio-src
if [ ! -d "$SRC/.git" ]; then git clone https://github.com/cocel-postech/genz-lio.git "$SRC" || { echo "git clone failed"; exit 1; }; fi
(cd "$SRC" && git fetch -q origin && git checkout -q $COMMIT) || { echo "could not check out $COMMIT"; exit 1; }
echo "GenZ-LIO source: $SRC at $(cd "$SRC" && git rev-parse --short HEAD)"

# 2. copy into the container, apply the information patch there
docker exec $GPU_C bash -c "rm -rf /root/genz_ws/src/genz-lio && mkdir -p /root/genz_ws/src /root/thr"
docker cp "$SRC" $GPU_C:/root/genz_ws/src/genz-lio || exit 1
docker cp "$HERE/patch_genz_information.py" $GPU_C:/root/thr/ || exit 1
docker cp "$HERE/make_genz_config.py" $GPU_C:/root/thr/ || exit 1
docker exec $GPU_C python3 /root/thr/patch_genz_information.py /root/genz_ws/src/genz-lio || { echo "patch failed"; exit 1; }

# 3. dependencies (only what is missing) and build in Release
docker exec $GPU_C bash -c "dpkg -s libyaml-cpp-dev >/dev/null 2>&1 || (apt-get update && apt-get install -y libyaml-cpp-dev)" \
  || echo "WARNING: could not install libyaml-cpp-dev (no network in the container?). Install it, then rerun."
docker exec $GPU_C bash -c "dpkg -s ros-noetic-pcl-ros >/dev/null 2>&1 || apt-get install -y ros-noetic-pcl-ros ros-noetic-pcl-conversions ros-noetic-tf ros-noetic-tf2-ros" \
  || echo "WARNING: ROS PCL packages missing and could not be installed."
docker exec $GPU_C bash -c "$ROS1 && cd /root/genz_ws && catkin_make -j2 -DCMAKE_BUILD_TYPE=Release > /root/thr/genz_build.out 2>&1"
ok=$?
docker exec $GPU_C tail -n 15 /root/thr/genz_build.out
[ $ok = 0 ] || { echo "BUILD FAILED (full log: docker exec $GPU_C cat /root/thr/genz_build.out)"; exit 1; }
docker exec $GPU_C bash -c "$ROS1 && source /root/genz_ws/devel/setup.bash && rospack find genz_lio && ls /root/genz_ws/devel/lib/genz_lio/" \
  || { echo "genz_lio package not found after build"; exit 1; }
docker exec $GPU_C grep -c GENZ_INFO_PATCH /root/genz_ws/src/genz-lio/ros/src/OdometryServer.cpp
echo "GENZ_INSTALL_DONE $(date +%T)"
