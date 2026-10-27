#!/bin/bash
# Runs INSIDE switchslam_gpu_v2 (started by gz_record.sh): world up, drive the route, record the bag, shut down.
# usage: gz_record_inner.sh <world> <route.csv> <laps> <bag path>
WORLD=${1:-office}; ROUTE=$2; LAPS=${3:-2}; BAG=$4
export ROS_MASTER_URI=${ROS_MASTER_URI:-http://localhost:11311}
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=/root/cpr_ws/src/cpr_gazebo:${ROS_PACKAGE_PATH:-}
export HUSKY_URDF_EXTRAS=/root/husky_sim_extras.urdf.xacro CPR_GAZEBO_PLATFORM=husky
case $WORLD in
  office)       PKG=cpr_office_gazebo;      L=office_world.launch ;;
  construction) PKG=cpr_office_gazebo;      L=office_construction_world.launch ;;
  empty)        PKG=cpr_empty_gazebo;       L=empty_world.launch ;;
  farm)         PKG=cpr_agriculture_gazebo; L=agriculture_world.launch ;;   # generation-1 farm world (L route); confirm with gz_smoke.sh agriculture
  *) echo "no route for world $WORLD yet"; exit 2 ;;
esac
LOGD=/root/gz_logs; mkdir -p $LOGD $(dirname $BAG)
if command -v Xvfb >/dev/null 2>&1; then pgrep -x Xvfb >/dev/null || { nohup Xvfb :99 -screen 0 1280x720x24 >$LOGD/xvfb.log 2>&1 & sleep 2; }; export DISPLAY=:99; fi
pkill -f roslaunch 2>/dev/null; pkill gzserver 2>/dev/null; pkill gzclient 2>/dev/null; pkill rosmaster 2>/dev/null; pkill rosbag 2>/dev/null; sleep 2
nohup roslaunch $PKG $L gui:=false >$LOGD/launch_$WORLD.log 2>&1 &
LP=$!
for i in $(seq 1 75); do
  rostopic list 2>/dev/null | grep -q "^/velodyne_points$" && rostopic list 2>/dev/null | grep -q "^/imu/data$" && break
  kill -0 $LP 2>/dev/null || { echo "FAIL: roslaunch exited early"; tail -20 $LOGD/launch_$WORLD.log; exit 1; }
  sleep 2
done
sleep 10
echo "== world up, sim time $(rostopic echo -n1 /clock 2>/dev/null | grep -m1 secs | awk '{print $2}') s"
if [ "$WORLD" = farm ]; then   # generation-1 protocol: the husky is reset to (0, 0, 0.2) before the drive
  rosservice call /gazebo/set_model_state '{model_state: {model_name: husky, pose: {position: {x: 0.0, y: 0.0, z: 0.2}, orientation: {x: 0, y: 0, z: 0, w: 1}}, twist: {linear: {x: 0, y: 0, z: 0}, angular: {x: 0, y: 0, z: 0}}, reference_frame: world}}' | head -2
  sleep 6
fi
nohup rosbag record -O $BAG /velodyne_points /imu/data /camera/image_raw /camera/camera_info /gt/husky_pose __name:=gzrec >$LOGD/rosbag.log 2>&1 &
sleep 3
python3 /root/gz_driver.py $ROUTE $LAPS ${GZ_SPEED:-0.5}; DR=$?
sleep 3
rosnode kill /gzrec >/dev/null 2>&1; sleep 6
pkill -f roslaunch; pkill gzserver; pkill gzclient; pkill rosmaster; sleep 2
ls -la $BAG* 2>/dev/null
echo "== RECORD $WORLD: $([ $DR = 0 ] && echo DONE || echo "FAILED (driver exit $DR)")"
exit $DR
