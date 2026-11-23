#!/usr/bin/env bash
# Unmodified A-LOAM on the Gazebo farm L route, one step per sub-command (each long step runs in its own terminal).
# Same world, robot, LiDAR extras file, route driver and reset as the F35 farm run; no VINS-Mono, no fusion node.
# A-LOAM is started from gazebo/live/aloam_standalone.launch (no /switch_fused_pose remap), so its guess comes from its own odometry.
#
# usage (from the repo, laptop):   fusion_v4/stock_aloam/farm_stock.sh <step>
#   1  setup     restart the gpu container (kills leftovers), copy the files in, allow the window (xhost); prints the IP
#   2  gazebo    Gazebo with the window on the display of this shell (terminal 1, stays open)
#   3  reset     start the wheel controller and put the robot at (0, 0, 0.2)       (terminal 2)
#   4  aloam     unmodified A-LOAM (terminal 3, stays open)
#   5  check     A-LOAM about 10 Hz, one alaserMapping, nothing left over; send this printout
#   6  loggers   ground truth and A-LOAM loggers, started in the background
#   7  drive     the L route at 0.25 m/s; wait for "Route complete"
#   8  pull      stop the loggers, copy the three files to ~/farm_stock, score them, zip
#   clean        restart the container (use before a repeat run)
set -u
C=switchslam_gpu_v2
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FUSION=$(cd "$HERE/.." && pwd); REPO=$(cd "$FUSION/.." && pwd)
ROS="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $C 2>/dev/null)
STEP=${1:-}
need_ip() { [ -n "$IP" ] || { echo "the container $C is not running or has no IP: run step 1 (setup) first"; exit 1; }; }

case "$STEP" in
1|setup)
  docker restart $C >/dev/null || exit 1
  sleep 15
  IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $C)
  echo "container IP: $IP"
  LEFT=$(docker exec $C bash -c "ps -eo pid,etime,args | grep -E 'ros|gz|alaser|ascan|fusion|logger|driver' | grep -v grep")
  [ -z "$LEFT" ] && echo "no leftover ROS processes (good)" || { echo "LEFTOVERS, stop here:"; echo "$LEFT"; exit 1; }
  docker exec $C mkdir -p /root/thr
  docker cp "$FUSION/gazebo/live/gt_logger.py" $C:/root/thr/ || exit 1
  docker cp "$FUSION/gazebo/live/aloam_logger.py" $C:/root/thr/ || exit 1
  docker cp "$FUSION/gazebo/live/aloam_standalone.launch" $C:/root/thr/ || exit 1
  docker cp "$REPO/switchslam_v1/farm/waypoint_driver_v4.py" $C:/root/ || exit 1
  docker cp "$FUSION/gazebo/live/husky_velodyne_extra_fwd.urdf.xacro" $C:/root/catkin_ws/ || exit 1
  docker exec $C bash -c "rm -f /root/thr/gt_farm_stock.txt /root/thr/farm_aloam_aft.txt /root/thr/farm_aloam_odom.txt"
  echo "DISPLAY of this shell: ${DISPLAY:-unset}"
  xhost +local:docker
  ;;
2|gazebo)
  need_ip
  [ -n "${DISPLAY:-}" ] || { echo "DISPLAY is not set in this terminal"; exit 1; }
  docker exec -it -e ROS_IP=$IP -e __NV_PRIME_RENDER_OFFLOAD=1 -e __GLX_VENDOR_LIBRARY_NAME=nvidia $C bash -c \
    "$ROS && export HUSKY_URDF_EXTRAS=/root/catkin_ws/husky_velodyne_extra_fwd.urdf.xacro && export DISPLAY=$DISPLAY && roslaunch cpr_agriculture_gazebo agriculture_world.launch"
  ;;
3|reset)
  need_ip
  docker exec -e ROS_IP=$IP $C bash -c "source /opt/ros/noetic/setup.bash && rosservice call /controller_manager/switch_controller '{start_controllers: [\"husky_velocity_controller\"], stop_controllers: [], strictness: 2}'"
  docker exec -e ROS_IP=$IP $C bash -c "source /opt/ros/noetic/setup.bash && rosservice call /gazebo/set_model_state '{model_state: {model_name: husky, pose: {position: {x: 0.0, y: 0.0, z: 0.2}, orientation: {w: 1.0}}}}'"
  ;;
4|aloam)
  need_ip
  docker exec -it -e ROS_IP=$IP $C bash -c "$ROS && roslaunch /root/thr/aloam_standalone.launch rviz:=false"
  ;;
5|check)
  need_ip
  docker exec -e ROS_IP=$IP $C bash -c "$ROS && echo '--- /laser_odom_to_init (expect about 10 Hz)' && timeout 8 rostopic hz /laser_odom_to_init 2>&1 | tail -2; \
    echo '--- /velodyne_points'; timeout 6 rostopic hz /velodyne_points 2>&1 | tail -2; \
    echo '--- nodes'; rosnode list | sort; \
    echo '--- publishers of /aft_mapped_to_init (expect one /alaserMapping)'; rostopic info /aft_mapped_to_init | grep -A2 Publishers; \
    echo '--- processes'; ps -eo pid,etime,args | grep -E 'alaser|ascan|fusion|vins|corridor' | grep -v grep"
  ;;
6|loggers)
  need_ip
  docker exec -d -e ROS_IP=$IP $C bash -c "$ROS && cd /root/thr && python3 gt_logger.py gt_farm_stock.txt > gt_logger.out 2>&1"
  docker exec -d -e ROS_IP=$IP $C bash -c "$ROS && cd /root/thr && python3 aloam_logger.py /root/thr/farm_aloam > aloam_logger.out 2>&1"
  sleep 4
  docker exec $C bash -c "cd /root/thr && wc -l gt_farm_stock.txt farm_aloam_aft.txt farm_aloam_odom.txt"
  ;;
7|drive)
  need_ip
  docker exec -it -e ROS_IP=$IP $C bash -c "source /opt/ros/noetic/setup.bash && python3 /root/waypoint_driver_v4.py"
  ;;
8|pull)
  docker exec $C bash -c "pkill -INT -f gt_logger.py; pkill -INT -f aloam_logger.py; sleep 2; cd /root/thr && wc -l gt_farm_stock.txt farm_aloam_aft.txt farm_aloam_odom.txt"
  mkdir -p ~/farm_stock
  for f in gt_farm_stock.txt farm_aloam_aft.txt farm_aloam_odom.txt; do docker cp $C:/root/thr/$f ~/farm_stock/ || exit 1; done
  python3 "$FUSION/gazebo/live/score_standalone.py" ~/farm_stock/gt_farm_stock.txt ~/farm_stock/farm_aloam
  (cd ~ && zip -r -q farm_stock.zip farm_stock && echo "zip: ~/farm_stock.zip")
  ;;
clean)
  docker restart $C >/dev/null && echo "container restarted"
  ;;
*)
  sed -n 2,17p "${BASH_SOURCE[0]}"
  ;;
esac
