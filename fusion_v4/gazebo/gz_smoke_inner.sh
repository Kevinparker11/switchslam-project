#!/bin/bash
# Runs INSIDE switchslam_gpu_v2 (started by gz_smoke.sh): launch one Clearpath world headless with the test sensors, measure, shut down.
WORLD=${1:-office}
export ROS_MASTER_URI=${ROS_MASTER_URI:-http://localhost:11311}   # the ROS setup files fail on an unset variable
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=/root/cpr_ws/src/cpr_gazebo:${ROS_PACKAGE_PATH:-}
export HUSKY_URDF_EXTRAS=/root/husky_sim_extras.urdf.xacro CPR_GAZEBO_PLATFORM=husky
case $WORLD in
  office)       PKG=cpr_office_gazebo;      L=office_world.launch ;;
  construction) PKG=cpr_office_gazebo;      L=office_construction_world.launch ;;
  empty)        PKG=cpr_empty_gazebo;       L=empty_world.launch ;;
  inspection)   PKG=cpr_inspection_gazebo;  L=inspection_world.launch ;;
  agriculture)  PKG=cpr_agriculture_gazebo; L=agriculture_world.launch ;;
  orchard)      PKG=cpr_orchard_gazebo;     L=orchard_world.launch ;;
  obstacle)     PKG=cpr_obstacle_gazebo;    L=cpr_obstacle_world.launch ;;
  *) echo "unknown world $WORLD"; exit 2 ;;
esac
LOGD=/root/gz_logs; mkdir -p $LOGD
echo "== world $WORLD ($PKG/$L), gazebo $(gzserver --version 2>/dev/null | head -1)"
rospack find $PKG >/dev/null 2>&1 || { echo "FAIL: package $PKG not found on ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH"; exit 1; }
# camera sensors need an OpenGL display: use a virtual one
if command -v Xvfb >/dev/null 2>&1; then
  pgrep -x Xvfb >/dev/null || { nohup Xvfb :99 -screen 0 1280x720x24 >$LOGD/xvfb.log 2>&1 & sleep 2; }
  export DISPLAY=:99
else echo "NOTE: Xvfb not installed, using DISPLAY=${DISPLAY:-unset}"; fi
pkill -f roslaunch 2>/dev/null; pkill gzserver 2>/dev/null; pkill gzclient 2>/dev/null; pkill rosmaster 2>/dev/null; sleep 2
nohup roslaunch $PKG $L gui:=false >$LOGD/launch_$WORLD.log 2>&1 &
LP=$!
echo "== waiting for the world (up to 150 s)"
for i in $(seq 1 75); do
  if rostopic list 2>/dev/null | grep -q "^/velodyne_points$" && rostopic list 2>/dev/null | grep -q "^/imu/data$"; then break; fi
  kill -0 $LP 2>/dev/null || { echo "FAIL: roslaunch exited early"; tail -25 $LOGD/launch_$WORLD.log; exit 1; }
  sleep 2
done
sleep 8
echo "== topics"; rostopic list 2>/dev/null | grep -E "velodyne|imu|camera|clock|model_states|cmd_vel|odom" | tr '\n' ' '; echo
echo "== robot description has velodyne / camera links:" $(rosparam get /robot_description 2>/dev/null | grep -c -E 'name="velodyne|name="camera_link')
for t in /imu/data /velodyne_points /camera/image_raw; do
  r=$(timeout 14 rostopic hz $t 2>/dev/null | grep "average rate" | tail -1)
  echo "rate $t: ${r:-none}  (simulation time)"
done
python3 /root/gz_probe.py; PR=$?
echo "== last launch-log warnings"; grep -i -E "error|fail|cannot|could not" $LOGD/launch_$WORLD.log | grep -v -i "preload\|audio\|openal" | tail -8
pkill -f roslaunch; pkill gzserver; pkill gzclient; pkill rosmaster; sleep 2
echo "== SMOKE $WORLD: $([ $PR = 0 ] && echo PASSED || echo FAILED)"
exit $PR
