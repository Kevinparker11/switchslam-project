#!/usr/bin/env bash
# Build iG-LIO (pinned commit, information patch applied) inside the ROS Noetic container used by the runs.
# Neither the master system (A-LOAM, /root/catkin_ws) nor GenZ-LIO (/root/genz_ws) is touched: iG-LIO goes to its own
# workspace /root/iglio_ws. About 10-15 min (catkin_make -j2). livox_ros_driver is replaced by a message-only stub
# (ig_lio lists it in CMake although a Velodyne run never uses it; the stub needs no Livox SDK).
# Start:  bash ~/switchslam_channelT/fusion_v4/ig_lio/install_iglio.sh 2>&1 | tee ~/install_iglio.log
set -u
GPU_C=${GPU_C:-switchslam_gpu_v2}
COMMIT=2d79259e3aaa5bbb10d6b13234398760bbacf8f5        # iG-LIO version read and patched on 27 Oct 2026
HERE=$(cd "$(dirname "$0")" && pwd)
ROS1="source /opt/ros/noetic/setup.bash"
[ "$(docker inspect -f '{{.State.Running}}' $GPU_C 2>/dev/null)" = "true" ] || { echo "container $GPU_C is not running (docker start $GPU_C)"; exit 1; }

# 1. source on the host (the container may have no git or network), pinned
SRC=~/iglio-src
if [ ! -d "$SRC/.git" ]; then git clone https://github.com/zijiechenrobotics/ig_lio.git "$SRC" || { echo "git clone failed"; exit 1; }; fi
(cd "$SRC" && git fetch -q origin && git checkout -q $COMMIT) || { echo "could not check out $COMMIT"; exit 1; }
echo "iG-LIO source: $SRC at $(cd "$SRC" && git rev-parse --short HEAD)"

# 2. copy into the container, add the Livox message stub, apply the information patch there
docker exec $GPU_C bash -c "rm -rf /root/iglio_ws/src/ig_lio /root/iglio_ws/src/livox_ros_driver && mkdir -p /root/iglio_ws/src /root/thr"
docker cp "$SRC" $GPU_C:/root/iglio_ws/src/ig_lio || exit 1
docker cp "$HERE/livox_stub" $GPU_C:/root/iglio_ws/src/livox_ros_driver || exit 1
docker cp "$HERE/patch_iglio_information.py" $GPU_C:/root/thr/ || exit 1
docker cp "$HERE/make_iglio_config.py" $GPU_C:/root/thr/ || exit 1
docker exec $GPU_C python3 /root/thr/patch_iglio_information.py /root/iglio_ws/src/ig_lio || { echo "patch failed"; exit 1; }

# 3. dependencies (only what is missing) and build in Release
docker exec $GPU_C bash -c "dpkg -s libgoogle-glog-dev >/dev/null 2>&1 || (apt-get update && apt-get install -y libgoogle-glog-dev)" \
  || echo "WARNING: could not install libgoogle-glog-dev (no network in the container?). Install it, then rerun."
docker exec $GPU_C bash -c "dpkg -s libtbb-dev >/dev/null 2>&1 || apt-get install -y libtbb-dev" \
  || echo "WARNING: could not install libtbb-dev."
docker exec $GPU_C bash -c "dpkg -s ros-noetic-pcl-ros >/dev/null 2>&1 || apt-get install -y ros-noetic-pcl-ros ros-noetic-pcl-conversions ros-noetic-tf ros-noetic-tf2-ros" \
  || echo "WARNING: ROS PCL packages missing and could not be installed."
docker exec $GPU_C bash -c "$ROS1 && cd /root/iglio_ws && catkin_make -j2 -DCMAKE_BUILD_TYPE=Release > /root/thr/iglio_build.out 2>&1"
ok=$?
docker exec $GPU_C tail -n 15 /root/thr/iglio_build.out
[ $ok = 0 ] || { echo "BUILD FAILED (full log: docker exec $GPU_C cat /root/thr/iglio_build.out)"; exit 1; }
docker exec $GPU_C bash -c "$ROS1 && source /root/iglio_ws/devel/setup.bash && rospack find ig_lio && ls /root/iglio_ws/devel/lib/ig_lio/" \
  || { echo "ig_lio package not found after build"; exit 1; }
docker exec $GPU_C grep -c IGLIO_INFO_PATCH /root/iglio_ws/src/ig_lio/src/ig_lio_node.cpp
echo "IGLIO_INSTALL_DONE $(date +%T)"
