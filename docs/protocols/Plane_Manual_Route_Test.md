# Plane, second recreation: spawn at the end of the L, manual route, two replays (11 Nov 2026, rules written before any run)

## What changes against FastRotate_Plane_Test_Protocol.md (announced here, before the run)
1. **Start.** The robot is placed at the end of the L route, (-38.5, -40.0, z 0.2), facing +y (yaw +90 degrees: the L ends heading -x, a right turn points along +y), not at (0, 0). Everything the robot sees from there is open ground, so the whole run is the paper's "ground only" Plane. The two-part score of the first protocol (L plus open leg) is dropped; the primary score is the whole log from the reset.
2. **Route.** Driven once by hand (`drive_manual.py`, 0.25 m/s latched, turn steps of 0.05 rad/s, no spins, about 105 m, the paper's Plane is 109 m). The ground truth of that drive is turned into waypoints 8 m apart (`waypoints_from_gt.py`); the other two runs drive those waypoints with `waypoint_driver_route.py` (0.25 m/s, SPIN_AT=none). The replayed path follows the manual one to about the goal tolerance (1.5 m); the difference in path length is reported.
3. **Arms.** Run 1 (the manual drive): unfed A-LOAM (F5), which is also the precondition check. Run 2: F26 (the final version; the first protocol named F24, which is no longer the final one). Run 3: SW (exact Switch-SLAM replica, paper rule). Run 4 (added 11 Nov 2026, before any run): F35 (F26 with the guess status driven by our own channels R, T and the additional T, `GUESS_MODE=ours`), same waypoints, same steps as run 2.
4. **Rig.** The forward-camera rig of the latest farm runs (RGB 640 x 480 at 60 Hz, `husky_velodyne_extra_fwd.urdf.xacro`, `farm_fwd_config.yaml`), in all three runs so the LiDAR and world are identical. The first protocol named the sideways rig.
5. Wiggle for the VINS-Mono initialisation is a circle of 0.5 m radius turning right (angular -0.3), away from the fence on the left.

## Reading rules (fixed now)
- **Score.** Umeyama SE(3), no scale, from the reset to 40 s after the robot first comes within 1.5 m of the last waypoint (the end of the manual path). Printed full-span values are reported too. Loggers are stopped within 30 s of arrival, so the window normally equals the log.
- **PL-P0 (precondition, else void and not adjusted).** Unfed A-LOAM fails on the run: ATE > 2.5 m or end-point error > 5 m. If it does not, the test is void for the failure direction (this world did not reproduce the paper's LOAM failure), the numbers are reported, and runs 2 and 3 are not read as a Plane result. The recorded route is still used.
- **PL-1.** VINS-Mono alone (from the F26 log) does not fail: ATE <= 2.5 m (paper 1.17 / 0.41).
- **PL-2 (the question).** F26 ATE <= max(1.0 m, 1.5 x VINS-Mono ATE of the same run). Published Switch-SLAM 1.27 / 0.35 for context.
- **PL-2 for F35 (added with run 4, before any run).** The same line as PL-2 and the same VINS-Mono ATE of its own run. F35 is judged against F26 only by the tie band of F35_All_Bags_Test.md (max(0.1 m, 10 %) of F26's ATE); one run each supports no claim and F26 stays final whatever the result.
- **PL-3 (reported, not judged).** SW against F26 and unfed A-LOAM; share of scans flagged degenerate by the paper's rule; guess kinds of F26.
- **Void starts.** Node not running, A-LOAM or VINS-Mono not initialised, SW without /laser_hessian or /vins_mono_hessian, robot stuck: reported, not scored, restarted from step 0 with the same settings.
- **Counts.** One run per arm supports no claim. A second and third run are made only if the F26 result lies within 50 % of the PL-2 line.
- Held-out for F26 (not used in its design). Simulation, one world, our own route: not comparable to the paper's Plane beyond the stated failure direction.

## Not verified when written
`drive_manual.py` and `waypoints_from_gt.py` were only compile-checked (waypoint extraction was run on a synthetic ground-truth file); the manual drive is their first live use. The spawn orientation (z = w = 0.7071068 means facing +y) follows from the quaternion and the driver's yaw formula, not from a run. SW live needs `/laser_hessian` from A-LOAM and `/vins_mono_hessian` from VINS-Mono; SW has never run live.

## Commands
Laptop shell; containers `switchslam_gpu_v2` (172.17.0.10) and `vinsmono_test`. Steps 0 to 2 are repeated before every run.

### 0. Clean start and copy files
```
cd ~/switchslam-project && git stash && git fetch origin && git checkout --detach origin/f22-handover
cd fusion_v4 && python3 test_predict_guard.py
docker restart switchslam_gpu_v2 vinsmono_test && sleep 15
docker exec switchslam_gpu_v2 bash -c "ps -eo pid,etime,args | grep -E 'ros|gz|alaser|ascan|fusion|logger|driver' | grep -v grep"      # expect nothing
docker exec switchslam_gpu_v2 mkdir -p /root/thr
for f in fusion_core.py fusion_node_v2.py structure_heading.py guess_status.py still_detect.py switch_slam_core.py switch_slam_node.py switch_slam_detect.py gyro_prior.py gazebo/live/gt_logger.py gazebo/live/make_live_extrinsics.py gazebo/live/aloam_logger.py gazebo/live/aloam_standalone.launch gazebo/live/drive_manual.py; do docker cp $f switchslam_gpu_v2:/root/thr/; done
docker cp gazebo/live/waypoint_driver_route.py switchslam_gpu_v2:/root/
docker cp gazebo/live/husky_velodyne_extra_fwd.urdf.xacro switchslam_gpu_v2:/root/catkin_ws/
docker cp vinsmono_test:/root/catkin_ws/src/VINS-Mono/config/farm/farm_mono_config.yaml /tmp/farm_mono_config.yaml
python3 gazebo/live/make_forward_vins_config.py /tmp/farm_mono_config.yaml /tmp/farm_fwd_config.yaml
docker cp /tmp/farm_fwd_config.yaml vinsmono_test:/root/catkin_ws/src/VINS-Mono/config/farm/farm_fwd_config.yaml
xhost +local:docker
```

### 1. Gazebo (forward-camera extras)
```
docker exec -it -e ROS_IP=172.17.0.10 -e __NV_PRIME_RENDER_OFFLOAD=1 -e __GLX_VENDOR_LIBRARY_NAME=nvidia switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export HUSKY_URDF_EXTRAS=/root/catkin_ws/husky_velodyne_extra_fwd.urdf.xacro && export DISPLAY=:1 && roslaunch cpr_agriculture_gazebo agriculture_world.launch"
```

### 2. Controller, then place the robot at the end of the L facing +y
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && rosservice call /controller_manager/switch_controller '{start_controllers: [\"husky_velocity_controller\"], stop_controllers: [], strictness: 2}'"
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && rosservice call /gazebo/set_model_state '{model_state: {model_name: husky, pose: {position: {x: -38.5, y: -40.0, z: 0.2}, orientation: {x: 0.0, y: 0.0, z: 0.7071068, w: 0.7071068}}}}'"
```

### RUN 1: manual drive, unfed A-LOAM
```
# terminal 3: A-LOAM without the fused-pose remap; check about 10 Hz
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && roslaunch /root/thr/aloam_standalone.launch rviz:=false"
docker exec switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && timeout 8 rostopic hz /laser_odom_to_init"
# terminal 4: ground-truth logger (stays open)
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 gt_logger.py gt_plane.txt"
# terminal 5: A-LOAM logger (stays open)
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 aloam_logger.py /root/thr/plane_aloam"
# terminal 6: wait about 15 s, then drive by hand. w = go, a / d = turn left / right (small steps), x = straight, s = stop, q = quit
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && python3 /root/thr/drive_manual.py"
```
Drive about 105 m along +y (about 7 min), no turns on the spot, stop with `s` then `q` before any fence or obstacle. Then Ctrl+C terminals 5 and 4 within 30 s.
```
mkdir -p ~/plane_aloam && for f in gt_plane.txt plane_aloam_aft.txt plane_aloam_odom.txt; do docker cp switchslam_gpu_v2:/root/thr/$f ~/plane_aloam/; done
cd ~/switchslam-project/fusion_v4
python3 gazebo/live/score_standalone.py ~/plane_aloam/gt_plane.txt ~/plane_aloam/plane_aloam
python3 gazebo/live/waypoints_from_gt.py ~/plane_aloam/gt_plane.txt 8
cd ~ && zip -r plane_aloam.zip plane_aloam
```
Send the two printouts (the WAYPOINTS line is used in runs 2 and 3) and the zip.

### RUN 2 (F26) and RUN 3 (SW): steps 0, 1, 2 again, then
```
# 3. A-LOAM (fed by the fused pose), check about 10 Hz; for SW also check /laser_hessian
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && roslaunch aloam_velodyne aloam_velodyne_VLP_16.launch"
docker exec switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && timeout 8 rostopic hz /laser_odom_to_init; timeout 8 rostopic hz /laser_hessian"
# 4. VINS-Mono, two terminals (forward config)
docker exec -it -e ROS_MASTER_URI=http://172.17.0.10:11311 vinsmono_test bash -c "source /opt/ros/kinetic/setup.bash && source /root/catkin_ws/devel/setup.bash && rosrun feature_tracker feature_tracker _config_file:=/root/catkin_ws/src/VINS-Mono/config/farm/farm_fwd_config.yaml _vins_folder:=/root/catkin_ws/src/VINS-Mono/"
docker exec -it vinsmono_test bash -c "rm -f /root/vins_output/vins_result_no_loop.csv"
docker exec -it -e ROS_MASTER_URI=http://172.17.0.10:11311 vinsmono_test bash -c "source /opt/ros/kinetic/setup.bash && source /root/catkin_ws/devel/setup.bash && rosrun vins_estimator vins_estimator _config_file:=/root/catkin_ws/src/VINS-Mono/config/farm/farm_fwd_config.yaml _vins_folder:=/root/catkin_ws/src/VINS-Mono/"
# 5. Wiggle (circle of 0.5 m radius to the right) until VINS has poses; repeat until the tail shows new rows
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && timeout 8 rostopic pub /husky_velocity_controller/cmd_vel geometry_msgs/Twist '{linear: {x: 0.15}, angular: {z: -0.3}}' -r 10"
docker exec -it vinsmono_test bash -c "tail -5 /root/vins_output/vins_result_no_loop.csv"
# 5b. Sensor rates (send the printout); for SW also /vins_mono_hessian
docker exec -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && for t in /imu/data /camera/image_raw /velodyne_points /vins_mono_hessian; do echo \$t; timeout 6 rostopic hz \$t 2>&1 | tail -2; done; timeout 5 rostopic echo -n 1 /camera/image_raw/encoding"
# 6. Extrinsics and ground-truth logger (stays open); RUN 3 uses gt_plane_sw.txt
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 make_live_extrinsics.py /root/thr/farm_live_extrinsics.yaml"
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 gt_logger.py gt_plane_f26.txt"
```
7a. RUN 2 node, F26 (printout must show HANDOVER=anchor, PREDICT_GUARD=1, GUESS_MODE=status):
```
docker exec -it -e ROS_IP=172.17.0.10 -e EXTRINSIC_YAML=/root/thr/farm_live_extrinsics.yaml -e RUN_TAG=F26_plane_live1 -e FUSION_MODE=fused -e C_T=3e-2 -e KAPPA_TH=1e9 -e SAH=1 -e ROT_CHECK=1 -e OT_SRC=geom -e OT_MODE=gmax -e VIO_CHECK=1 -e VIO_CHECK_FAST=5 -e LIDAR_GUARD_T=2 -e LIDAR_GUARD_EX=4.325 -e VIO_CHECK_REF=0.157 -e VIO_CHECK_FAST_REF=0.277 -e VIO_CHECK_START=1 -e HANDOVER=anchor -e PREDICT_GUARD=1 -e GUESS_MODE=status switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && cd /root/thr && rm -f switching_log_v2_F26_plane_live1.csv && python3 -u fusion_node_v2.py 2>&1 | tee node_F26_plane_live1.out"
```
7b. RUN 3 node, SW (printout must show FUSION_MODE=switch_slam):
```
docker exec -it -e ROS_IP=172.17.0.10 -e EXTRINSIC_YAML=/root/thr/farm_live_extrinsics.yaml -e RUN_TAG=SW_plane_live1 -e FUSION_MODE=switch_slam -e HESS_TOPIC=/laser_hessian -e N_BUF=5 -e LT_MODE=published -e EQ15_W=0.5 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && cd /root/thr && rm -f switching_log_v2_SW_plane_live1.csv && python3 -u switch_slam_node.py 2>&1 | tee node_SW_plane_live1.out"
```
7c. RUN 4 node, F35 (printout must show GUESS_MODE=ours, HANDOVER=anchor, PREDICT_GUARD=1; logger file gt_plane_f35.txt):
```
docker exec -it -e ROS_IP=172.17.0.10 -e EXTRINSIC_YAML=/root/thr/farm_live_extrinsics.yaml -e RUN_TAG=F35_plane_live1 -e FUSION_MODE=fused -e C_T=3e-2 -e KAPPA_TH=1e9 -e SAH=1 -e ROT_CHECK=1 -e OT_SRC=geom -e OT_MODE=gmax -e VIO_CHECK=1 -e VIO_CHECK_FAST=5 -e LIDAR_GUARD_T=2 -e LIDAR_GUARD_EX=4.325 -e VIO_CHECK_REF=0.157 -e VIO_CHECK_FAST_REF=0.277 -e VIO_CHECK_START=1 -e HANDOVER=anchor -e PREDICT_GUARD=1 -e GUESS_MODE=ours -e DET_CH=R,T,TT -e DET_CT=0.03 -e DET_KR=15.7 -e DET_TT_RULE=min switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && cd /root/thr && rm -f switching_log_v2_F35_plane_live1.csv && python3 -u fusion_node_v2.py 2>&1 | tee node_F35_plane_live1.out"
```
8. When the node prints FUSED (about 25 s), the replay driver with the WAYPOINTS line from run 1:
```
docker exec -it -e ROS_IP=172.17.0.10 -e WAYPOINTS="<paste the WAYPOINTS value printed in run 1>" -e SPIN_AT=none -e LINEAR_SPEED=0.25 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && python3 /root/waypoint_driver_route.py"
```
No second reset. When the driver prints "Route complete", Ctrl+C the logger and the node within 30 s.

9. Pull, score, zip (RUN 2 shown; RUN 3: replace f26 with sw, F26 with SW; RUN 4: replace f26 with f35, F26 with F35):
```
mkdir -p ~/plane_f26 && cd ~/switchslam-project/fusion_v4
for f in gt_plane_f26.txt switching_log_v2_F26_plane_live1.csv node_F26_plane_live1.out; do docker cp switchslam_gpu_v2:/root/thr/$f ~/plane_f26/; done
python3 gazebo/live/score_fused.py ~/plane_f26/gt_plane_f26.txt ~/plane_f26/switching_log_v2_F26_plane_live1.csv
python3 -c "import csv,sys,collections as c;print(c.Counter(r['guess_kind'] for r in csv.DictReader(open(sys.argv[1]))))" ~/plane_f26/switching_log_v2_F26_plane_live1.csv
cd ~ && zip -r plane_f26.zip plane_f26
```
