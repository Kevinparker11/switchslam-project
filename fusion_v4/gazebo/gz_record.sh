#!/bin/bash
# Stage 2a: drive the planned route in a Gazebo world and record the raw bag (LiDAR, IMU, camera, exact pose).
#   ./gz_record.sh office [laps]        (default 2 laps, about 10-12 min; needs about 8 GB free in the container and on the drive)
# The bag goes to "$BAGS_ROOT/gazebo_<world>/" (default: the external drive), like every other test bag.
set -u
WORLD=${1:-office}; LAPS=${2:-2}; C=switchslam_gpu_v2
HERE=$(cd "$(dirname "$0")" && pwd)
BAGS_ROOT=${BAGS_ROOT:-"/media/$USER/One Touch1/laptop_bags"}
case $WORLD in office) ROUTE=office_loop.csv ;; construction) ROUTE=construction_loop.csv ;; *) echo "no planned route for $WORLD yet"; exit 1 ;; esac
[ -d "$BAGS_ROOT" ] || { echo "bag drive not found: $BAGS_ROOT"; exit 1; }
docker start $C >/dev/null 2>&1
FREE_C=$(docker exec $C df -BG --output=avail /root | tail -1 | tr -dc 0-9); FREE_D=$(df -BG --output=avail "$BAGS_ROOT" | tail -1 | tr -dc 0-9)
echo "free space: container ${FREE_C} GB, drive ${FREE_D} GB (need about 8 GB each)"
[ "$FREE_C" -ge 8 ] && [ "$FREE_D" -ge 8 ] || { echo "not enough space"; exit 1; }
docker exec $C test -f /root/cpr_ws/src/cpr_gazebo/cpr_office_gazebo/package.xml || { echo "run ./gz_smoke.sh $WORLD first (copies cpr_gazebo into the container)"; exit 1; }
docker cp "$HERE/husky_sim_extras.urdf.xacro" $C:/root/husky_sim_extras.urdf.xacro
docker cp "$HERE/routes/$ROUTE" $C:/root/$ROUTE
docker cp "$HERE/gz_driver.py" $C:/root/gz_driver.py
docker cp "$HERE/gz_record_inner.sh" $C:/root/gz_record_inner.sh
TAG=gazebo_${WORLD}_$(date +%Y%m%d_%H%M); BAG=/root/gz_bags/$TAG.bag
docker exec $C bash /root/gz_record_inner.sh "$WORLD" /root/$ROUTE "$LAPS" "$BAG" 2>&1 | tee ~/gz_record_$WORLD.txt
grep -q "RECORD $WORLD: DONE" ~/gz_record_$WORLD.txt || { echo "recording failed, see ~/gz_record_$WORLD.txt"; exit 1; }
DEST="$BAGS_ROOT/gazebo_$WORLD"; mkdir -p "$DEST"
docker cp $C:$BAG "$DEST/$TAG.bag" && echo "bag copied: $DEST/$TAG.bag ($(du -h "$DEST/$TAG.bag" | cut -f1))"
docker run --rm -v "$DEST":/b:ro ros:noetic bash -c "source /opt/ros/noetic/setup.bash; rosbag info /b/$TAG.bag" | tee ~/gz_bag_info_$WORLD.txt | grep -E "duration|size|topics|/velodyne|/imu|/camera|/gt"
