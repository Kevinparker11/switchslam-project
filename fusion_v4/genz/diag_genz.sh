#!/usr/bin/env bash
# Diagnose "0 rows": restart GenZ-LIO in the running stack, replay 60 s of Multi Floor, and measure what flows.
# Run it right after a smoke run (the stack is still up). Output: ~/genz_diag.txt (also printed).
GPU_C=switchslam_gpu_v2
BAGS_ROOT=${BAGS_ROOT:-"/media/$USER/One Touch1/laptop_bags"}
BAGDIR=""; for d in multifloor MultiFloor Multi_Floor multi_floor RosBag; do ls "$BAGS_ROOT/$d"/*.bag >/dev/null 2>&1 && { BAGDIR="$BAGS_ROOT/$d"; break; }; done
[ -n "$BAGDIR" ] || { echo "no Multi Floor bags under $BAGS_ROOT"; exit 1; }
GPU=$(docker inspect -f '{{.NetworkSettings.Networks.vins_bridge.IPAddress}}' $GPU_C)
ROS1="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && source /root/genz_ws/devel/setup.bash"
OUT=~/genz_diag.txt; : > $OUT
{
echo "== restart GenZ-LIO"
docker exec $GPU_C bash -c "$ROS1; rosnode kill /genz_lio >/dev/null 2>&1; pkill -f '[g]enz_lio_node'; sleep 2"
docker exec -d -e ROS_IP=$GPU -e PYTHONUNBUFFERED=1 $GPU_C bash -c "$ROS1 && roslaunch genz_lio odometry.launch config:=/root/thr/genz_frozen.yaml rviz:=false > /root/thr/genz_diag.out 2>&1"
sleep 4
echo "== start rate monitors (45 s)"
for t in /imu/data /multifloor/velodyne_points /Odometry /cloud_registered /aft_mapped_to_init /laser_hessian; do
  n=$(echo $t | tr '/' '_')
  docker exec -d $GPU_C bash -c "$ROS1; timeout 50 rostopic hz $t > /root/thr/hz$n.txt 2>&1"
done
docker exec -d $GPU_C bash -c "$ROS1; timeout 50 rostopic echo -n1 /imu/data/header/stamp > /root/thr/st_imu.txt 2>&1; timeout 50 rostopic echo -n1 /multifloor/velodyne_points/header/stamp > /root/thr/st_lidar.txt 2>&1"
docker exec -d $GPU_C bash -c "$ROS1; timeout 50 rostopic echo -n1 /clock > /root/thr/st_clock.txt 2>&1"
echo "== replay first 45 s of the bag"
docker run --rm --network vins_bridge -v "$BAGDIR":/bags:ro -e ROS_MASTER_URI=http://$GPU:11311 --entrypoint bash ros:noetic -c \
  "export ROS_IP=\$(hostname -i); source /opt/ros/noetic/setup.bash; rosbag play --clock -q -u 45 /bags/multifloor_0.bag" > /dev/null 2>&1
sleep 5
for n in _imu_data _multifloor_velodyne_points _Odometry _cloud_registered _aft_mapped_to_init _laser_hessian; do
  echo "--- rate $n"; docker exec $GPU_C bash -c "grep -E 'average rate|no new messages|subscribed' /root/thr/hz$n.txt | tail -2"
done
echo "--- stamps (header stamp vs /clock): seconds"
for f in clock imu lidar; do echo "$f: $(docker exec $GPU_C bash -c "grep -E 'secs|^ *secs|clock:' -A1 /root/thr/st_$f.txt | tr '\n' ' '")"; done
echo "--- GenZ-LIO output"; docker exec $GPU_C tail -n 25 /root/thr/genz_diag.out
echo "--- bridge output"; docker exec $GPU_C tail -n 8 /root/thr/bridge.out
} 2>&1 | tee $OUT
