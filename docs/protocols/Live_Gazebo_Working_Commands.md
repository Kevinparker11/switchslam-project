# Live Gazebo working commands (kept here so they are not searched for again)

Source: owner's `FARM WORKING COMMANDS` block used for the 3 Nov F24 Farm run (logs ~/farm_f24), pasted 6 Nov 2026. Lines marked **[verified]** are from that block unchanged. Lines marked **[new]** are what the Fast Rotate / Plane tests change. Nothing else changes.
Hosts: laptop shell; containers `switchslam_gpu_v2` (ROS noetic, IP 172.17.0.10, Gazebo + A-LOAM + node) and `vinsmono_test` (ROS kinetic, VINS-Mono). World: `cpr_agriculture_gazebo agriculture_world.launch` for Farm, Fast Rotate and Plane (our recreations).

## 0. Clean start and copy files (laptop) [verified, two changes]
```
cd ~/switchslam-project && git stash && git fetch origin && git checkout --detach origin/f22-handover     # [new] replaces the git am patch: branch f22-handover already contains F24 PREDICT_GUARD, the route driver and the loggers
cd fusion_v4 && python3 test_predict_guard.py
GPU=172.17.0.10
docker exec switchslam_gpu_v2 bash -c "pkill -f gt_logger; pkill -f aloam_logger; pkill -f waypoint_driver; pkill -f fusion_node_v2; pkill -f roslaunch; pkill gzserver; pkill gzclient; pkill rosmaster; sleep 2"
for f in fusion_core.py fusion_node_v2.py structure_heading.py gazebo/live/gt_logger.py gazebo/live/make_live_extrinsics.py; do docker cp $f switchslam_gpu_v2:/root/thr/; done
docker cp gazebo/live/waypoint_driver_route.py switchslam_gpu_v2:/root/                                # [new]
docker cp gazebo/live/aloam_logger.py switchslam_gpu_v2:/root/thr/                                    # [new] unfed A-LOAM run only
docker cp gazebo/live/aloam_standalone.launch switchslam_gpu_v2:/root/thr/                            # [new] unfed A-LOAM run only
xhost +local:docker
```
If `git stash` says "No local changes", that is fine. If `origin` is missing in ~/switchslam-project, run `git remote -v` and use the remote that points to Kevinparker11/switchslam-project.

## 1. Gazebo [verified]
```
docker exec -it -e ROS_IP=172.17.0.10 -e __NV_PRIME_RENDER_OFFLOAD=1 -e __GLX_VENDOR_LIBRARY_NAME=nvidia switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export HUSKY_URDF_EXTRAS=/root/catkin_ws/husky_velodyne_extra.urdf.xacro && export DISPLAY=:1 && roslaunch cpr_agriculture_gazebo agriculture_world.launch"
```

## 2. Controller, then reset the robot [verified]
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && rosservice call /controller_manager/switch_controller '{start_controllers: [\"husky_velocity_controller\"], stop_controllers: [], strictness: 2}'"
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && rosservice call /gazebo/set_model_state '{model_state: {model_name: husky, pose: {position: {x: 0.0, y: 0.0, z: 0.2}, orientation: {w: 1.0}}}}'"
```

## 3. A-LOAM [verified]; check about 10 Hz
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && roslaunch aloam_velodyne aloam_velodyne_VLP_16.launch"
docker exec switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && timeout 8 rostopic hz /laser_odom_to_init"
```
**Unfed A-LOAM run (F5) uses this instead [new]** (same launch without the /switch_fused_pose remap; `rviz:=false` is added so it does not need a display; delete that argument if you want rviz as in the farm file):
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && roslaunch /root/thr/aloam_standalone.launch rviz:=false"
```

## 4. VINS-Mono, two terminals [verified]; not needed for the unfed A-LOAM run
```
docker exec -it -e ROS_MASTER_URI=http://172.17.0.10:11311 vinsmono_test bash -c "source /opt/ros/kinetic/setup.bash && source /root/catkin_ws/devel/setup.bash && rosrun feature_tracker feature_tracker _config_file:=/root/catkin_ws/src/VINS-Mono/config/farm/farm_mono_config.yaml _vins_folder:=/root/catkin_ws/src/VINS-Mono/"
docker exec -it vinsmono_test bash -c "rm -f /root/vins_output/vins_result_no_loop.csv"
docker exec -it -e ROS_MASTER_URI=http://172.17.0.10:11311 vinsmono_test bash -c "source /opt/ros/kinetic/setup.bash && source /root/catkin_ws/devel/setup.bash && rosrun vins_estimator vins_estimator _config_file:=/root/catkin_ws/src/VINS-Mono/config/farm/farm_mono_config.yaml _vins_folder:=/root/catkin_ws/src/VINS-Mono/"
```

## 5. Wiggle until VINS has poses [verified]; repeat until tail shows new rows
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && timeout 8 rostopic pub /husky_velocity_controller/cmd_vel geometry_msgs/Twist '{linear: {x: 0.15}, angular: {z: 0.3}}' -r 10"
docker exec -it vinsmono_test bash -c "tail -5 /root/vins_output/vins_result_no_loop.csv"
```

## 6. Extrinsics and ground-truth logger (logger stays open) [verified, file name changed for Plane]
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 make_live_extrinsics.py /root/thr/farm_live_extrinsics.yaml"
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 gt_logger.py gt_plane.txt"          # Fast Rotate: gt_fr.txt
```
Unfed A-LOAM run: run only the gt_logger line, plus the A-LOAM logger in a second terminal [new]:
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 aloam_logger.py /root/thr/plane_aloam"
```

## 7. F24 node [verified, only RUN_TAG and the log name changed]; printout must show HANDOVER=anchor PREDICT_GUARD=1
```
docker exec -it -e ROS_IP=172.17.0.10 -e EXTRINSIC_YAML=/root/thr/farm_live_extrinsics.yaml -e RUN_TAG=F24_plane_live1 -e FUSION_MODE=fused -e C_T=3e-2 -e KAPPA_TH=1e9 -e SAH=1 -e ROT_CHECK=1 -e OT_SRC=geom -e OT_MODE=gmax -e VIO_CHECK=1 -e VIO_CHECK_FAST=5 -e LIDAR_GUARD_T=2 -e LIDAR_GUARD_EX=4.325 -e VIO_CHECK_REF=0.157 -e VIO_CHECK_FAST_REF=0.277 -e VIO_CHECK_START=1 -e HANDOVER=anchor -e PREDICT_GUARD=1 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && cd /root/thr && rm -f switching_log_v2_F24_plane_live1.csv && python3 -u fusion_node_v2.py 2>&1 | tee node_F24_plane_live1.out"
```

## 8. Wait until the node prints FUSED (about 25 s), then the driver [new: route driver instead of waypoint_driver_v4.py]
Plane (80 m L + 105 m open ground, no spins):
```
docker exec -it -e ROS_IP=172.17.0.10 -e WAYPOINTS="0,-40;-20,-40;-40,-40;-40,-10;-40,25;-40,65" -e SPIN_AT=none switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && python3 /root/waypoint_driver_route.py"
```
Fast Rotate (116 m, nine spins):
```
docker exec -it -e ROS_IP=172.17.0.10 -e WAYPOINTS="0,-13;0,-26;0,-40;0,-27;0,-14;0,0;0,-12;0,-24;0,-36" -e SPIN_AT=all -e SPIN_RATE=2.0 -e SPIN_TURNS=1 -e LINEAR_SPEED=0.25 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && python3 /root/waypoint_driver_route.py"
```
No second reset. Stop logger and node with Ctrl+C when the driver prints its completion line. Keep the "Spin done" lines (Fast Rotate). The route driver was only py_compile-checked: first do a dry drive (run step 8 for about 30 s and watch the robot head to the first waypoint; if it misbehaves, stop and report).

## 9. Pull, score and zip [verified, names changed]
```
mkdir -p ~/plane_f24 && cd ~/switchslam-project/fusion_v4
for f in gt_plane.txt switching_log_v2_F24_plane_live1.csv node_F24_plane_live1.out; do docker cp switchslam_gpu_v2:/root/thr/$f ~/plane_f24/; done
python3 gazebo/live/score_fused.py ~/plane_f24/gt_plane.txt ~/plane_f24/switching_log_v2_F24_plane_live1.csv
cd ~ && zip -r plane_f24.zip plane_f24
```
Unfed A-LOAM run: `for f in gt_plane.txt plane_aloam_aft.txt plane_aloam_odom.txt; do docker cp switchslam_gpu_v2:/root/thr/$f ~/plane_aloam/; done` then `python3 gazebo/live/score_standalone.py ~/plane_aloam/gt_plane.txt ~/plane_aloam/plane_aloam`.
(The open-ground-leg score, aligned on its own, is done offline by Claude from the zip.)

## Run order (pre-registered)
Plane: unfed A-LOAM (precondition PL-P0), then F24, then SW. Fast Rotate: unfed A-LOAM, then F24, then SW. Each run starts at step 0 (full clean start) and step 2 (reset).

## Not yet verified
- SW node live: config `FUSION_MODE=switch_slam HESS_TOPIC=/laser_hessian N_BUF=5 LT_MODE=published EQ15_W=0.5` with `python3 -u switch_slam_node.py` (needs /laser_hessian from the Hessian-publishing A-LOAM build and switch_slam_core.py, guess_status.py, still_detect.py copied to /root/thr). Not run live before; do it last.
- waypoint_driver_route.py has never run in ROS.
- Plane and Fast Rotate use the agriculture world (the paper's own worlds are not released).
