#!/bin/bash
# Stage 1 of the Gazebo tests: does the world start headless, and do LiDAR, camera and IMU publish what the pipeline needs?
#   ./gz_smoke.sh office            (worlds: office construction empty inspection agriculture orchard obstacle)
# Run it while no fusion batch is running (it stops any roscore in the LiDAR container). Output also goes to ~/gz_smoke_<world>.txt
set -u
WORLD=${1:-office}; C=switchslam_gpu_v2
HERE=$(cd "$(dirname "$0")" && pwd)
CPR=${CPR_GAZEBO_DIR:-$HOME/cpr_gazebo}
[ -d "$CPR" ] || { echo "cpr_gazebo not found at $CPR (CPR_GAZEBO_DIR=...)"; exit 1; }
docker start $C >/dev/null 2>&1
if ! docker exec $C test -f /root/cpr_ws/src/cpr_gazebo/cpr_office_gazebo/package.xml; then
  echo "== copying cpr_gazebo (without .git) into the container, once"
  docker exec $C mkdir -p /root/cpr_ws/src
  tar --exclude=.git -C "$(dirname "$CPR")" -cf - "$(basename "$CPR")" | docker exec -i $C tar -xf - -C /root/cpr_ws/src
fi
docker cp "$HERE/husky_sim_extras.urdf.xacro" $C:/root/husky_sim_extras.urdf.xacro
docker cp "$HERE/gz_probe.py" $C:/root/gz_probe.py
docker cp "$HERE/gz_smoke_inner.sh" $C:/root/gz_smoke_inner.sh
docker exec $C bash /root/gz_smoke_inner.sh "$WORLD" 2>&1 | tee ~/gz_smoke_$WORLD.txt
