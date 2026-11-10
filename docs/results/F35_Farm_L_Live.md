# F35 on the Farm L route, live in Gazebo (protocol written 10 Nov 2026, before the run)

Config F35 = F26 with the scan-to-map guess decided by our own channels (`GUESS_MODE=ours DET_CH=R,T,TT DET_CT=0.03 DET_KR=15.7 DET_TT_RULE=min`). Everything else is F26. Rig, route, driver and scoring are those of the 7 Nov F24 and F26 live runs (Farm_Forward_Camera_Test.md): paper sensors (RGB 640 x 480 at 60 Hz camera, VLP-16 10 Hz with 440 samples, IMU 200 Hz), camera forward (`husky_velodyne_extra_fwd.urdf.xacro`, VINS-Mono `farm_fwd_config.yaml`), world `cpr_agriculture_gazebo agriculture_world.launch`, L (0,0)-(0,-40)-(-20,-40)-(-40,-40) with `waypoint_driver_v4.py` at 0.25 m/s, robot reset to (0, 0, 0.2) first, `score_fused.py` (Umeyama SE(3), no scale, from the reset).

## Reference values (same rig, one live run each)
F26 0.290 / 0.562 m (VINS-Mono alone 4.31; guess kinds LiDAR 67 %, VINS 32 %, interpolation 0.6 %). F24 0.472 / 1.068 m (VINS alone 14.47). Farm rule of Switch-SLAM (other setup), reported only: 0.38 / 1.10 m.

## Precondition (void if it fails, not adjusted)
FC-P0': `rostopic hz` shows /imu/data about 200 Hz, /camera/image_raw about 60 Hz with encoding rgb8, /velodyne_points about 10 Hz; the node printout shows `GUESS_MODE=ours`, `HANDOVER=anchor`, `PREDICT_GUARD=1`; VINS-Mono initialises in the wiggle. A run that fails this is reported as void and rerun with the same settings.

## Reading rules (fixed now)
1. Fused RMSE within max(0.1 m, 10 %) of F26's 0.290 (0.19 to 0.39 m) = no change visible. Below 0.19 = lower, above 0.39 = higher. One run supports no claim; F24 alone ranged 0.255 to 0.472 on the two forward rigs, so a result outside the band is a hint, not a difference.
2. Also reported: max error, end-point error, A-LOAM output of the same log, VINS-Mono alone (not an effect of F35: it takes no input from the fusion), mode rows (FUSED / WARMUP / VO_FAIL), and the guess kinds (LIDAR / VO / INTERP shares from `guess_kind`, and where on the route the VINS guess is used).
3. The Farm rule 0.38 / 1.10 is reported only; the rig differs from the paper's and the mounting direction is not stated in the paper.
4. Prediction (not a result): fused 0.19 to 0.39 m. Our channels flag more scans than the published rule (F26: VINS guess 32 %, mostly the last 25 m), so the VINS share should be at least that.
5. A failed start (node not running, A-LOAM died, VINS not initialised, robot stuck) is reported, not scored, and the whole sequence is restarted from step 0. If the first run is inside the band, two more runs from full clean restarts are the rule, as in the earlier Farm protocol. Farm is development data for F20 to F26; no held-out claim.

## Commands (laptop shell; about 25 min per run including the restart, the drive itself about 5.5 min)

### 0. Clean start and copy files
```
cd ~/switchslam-project && git stash && git fetch origin && git checkout --detach origin/f22-handover
cd fusion_v4 && python3 test_predict_guard.py && python3 test_fusion_node_ours.py
docker exec switchslam_gpu_v2 bash -c "pkill -f gt_logger; pkill -f aloam_logger; pkill -f waypoint_driver; pkill -f fusion_node_v2; pkill -f roslaunch; pkill gzserver; pkill gzclient; pkill rosmaster; sleep 2"
for f in fusion_core.py fusion_node_v2.py structure_heading.py guess_status.py switch_slam_core.py switch_slam_detect.py gazebo/live/gt_logger.py gazebo/live/make_live_extrinsics.py; do docker cp $f switchslam_gpu_v2:/root/thr/; done
docker cp ../switchslam_v1/farm/waypoint_driver_v4.py switchslam_gpu_v2:/root/
docker cp gazebo/live/husky_velodyne_extra_fwd.urdf.xacro switchslam_gpu_v2:/root/catkin_ws/
docker cp vinsmono_test:/root/catkin_ws/src/VINS-Mono/config/farm/farm_mono_config.yaml /tmp/farm_mono_config.yaml
python3 gazebo/live/make_forward_vins_config.py /tmp/farm_mono_config.yaml /tmp/farm_fwd_config.yaml
docker cp /tmp/farm_fwd_config.yaml vinsmono_test:/root/catkin_ws/src/VINS-Mono/config/farm/farm_fwd_config.yaml
xhost +local:docker
```

### 1. Gazebo (forward-camera extras file)
```
docker exec -it -e ROS_IP=172.17.0.10 -e __NV_PRIME_RENDER_OFFLOAD=1 -e __GLX_VENDOR_LIBRARY_NAME=nvidia switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export HUSKY_URDF_EXTRAS=/root/catkin_ws/husky_velodyne_extra_fwd.urdf.xacro && export DISPLAY=:1 && roslaunch cpr_agriculture_gazebo agriculture_world.launch"
```

### 2. Controller, then reset the robot
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && rosservice call /controller_manager/switch_controller '{start_controllers: [\"husky_velocity_controller\"], stop_controllers: [], strictness: 2}'"
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && rosservice call /gazebo/set_model_state '{model_state: {model_name: husky, pose: {position: {x: 0.0, y: 0.0, z: 0.2}, orientation: {w: 1.0}}}}'"
```

### 3. A-LOAM (with the /switch_fused_pose remap, as in the F24 and F26 runs); check about 10 Hz
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && roslaunch aloam_velodyne aloam_velodyne_VLP_16.launch"
docker exec switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && timeout 8 rostopic hz /laser_odom_to_init"
```

### 4. VINS-Mono, two terminals (forward config)
```
docker exec -it -e ROS_MASTER_URI=http://172.17.0.10:11311 vinsmono_test bash -c "source /opt/ros/kinetic/setup.bash && source /root/catkin_ws/devel/setup.bash && rosrun feature_tracker feature_tracker _config_file:=/root/catkin_ws/src/VINS-Mono/config/farm/farm_fwd_config.yaml _vins_folder:=/root/catkin_ws/src/VINS-Mono/"
docker exec -it vinsmono_test bash -c "rm -f /root/vins_output/vins_result_no_loop.csv"
docker exec -it -e ROS_MASTER_URI=http://172.17.0.10:11311 vinsmono_test bash -c "source /opt/ros/kinetic/setup.bash && source /root/catkin_ws/devel/setup.bash && rosrun vins_estimator vins_estimator _config_file:=/root/catkin_ws/src/VINS-Mono/config/farm/farm_fwd_config.yaml _vins_folder:=/root/catkin_ws/src/VINS-Mono/"
```

### 5. Wiggle until VINS has poses; repeat until tail shows new rows
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && timeout 8 rostopic pub /husky_velocity_controller/cmd_vel geometry_msgs/Twist '{linear: {x: 0.15}, angular: {z: 0.3}}' -r 10"
docker exec -it vinsmono_test bash -c "tail -5 /root/vins_output/vins_result_no_loop.csv"
```

### 5b. Precondition FC-P0' (send the printout)
```
docker exec -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && for t in /imu/data /camera/image_raw /velodyne_points; do echo \$t; timeout 6 rostopic hz \$t 2>&1 | tail -2; done; timeout 5 rostopic echo -n 1 /camera/image_raw/encoding"
```

### 6. Extrinsics and ground-truth logger (logger stays open)
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 make_live_extrinsics.py /root/thr/farm_live_extrinsics.yaml"
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/thr && python3 gt_logger.py gt_f35farm.txt"
```

### 7. F35 node (printout must show GUESS_MODE=ours, HANDOVER=anchor, PREDICT_GUARD=1)
```
docker exec -it -e ROS_IP=172.17.0.10 -e EXTRINSIC_YAML=/root/thr/farm_live_extrinsics.yaml -e RUN_TAG=F35_farm_live1 -e FUSION_MODE=fused -e C_T=3e-2 -e KAPPA_TH=1e9 -e SAH=1 -e ROT_CHECK=1 -e OT_SRC=geom -e OT_MODE=gmax -e VIO_CHECK=1 -e VIO_CHECK_FAST=5 -e LIDAR_GUARD_T=2 -e LIDAR_GUARD_EX=4.325 -e VIO_CHECK_REF=0.157 -e VIO_CHECK_FAST_REF=0.277 -e VIO_CHECK_START=1 -e HANDOVER=anchor -e PREDICT_GUARD=1 -e GUESS_MODE=ours -e DET_CH=R,T,TT -e DET_CT=0.03 -e DET_KR=15.7 -e DET_TT_RULE=min switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && cd /root/thr && rm -f switching_log_v2_F35_farm_live1.csv && python3 -u fusion_node_v2.py 2>&1 | tee node_F35_farm_live1.out"
```

### 8. Wait until the node prints FUSED (about 25 s), then the driver (L route, 0.25 m/s)
```
docker exec -it -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && python3 /root/waypoint_driver_v4.py"
```
No second reset. Ctrl+C the logger and the node when the driver prints its completion line.

### 9. Pull, score, guess kinds, zip
```
mkdir -p ~/farm_f35 && cd ~/switchslam-project/fusion_v4
for f in gt_f35farm.txt switching_log_v2_F35_farm_live1.csv node_F35_farm_live1.out; do docker cp switchslam_gpu_v2:/root/thr/$f ~/farm_f35/; done
python3 gazebo/live/score_fused.py ~/farm_f35/gt_f35farm.txt ~/farm_f35/switching_log_v2_F35_farm_live1.csv
python3 -c "import csv,sys,collections as c;print(c.Counter(r['guess_kind'] for r in csv.DictReader(open(sys.argv[1]))))" ~/farm_f35/switching_log_v2_F35_farm_live1.csv
cd ~ && zip -r farm_f35.zip farm_f35
```
For runs 2 and 3 change the tag (`F35_farm_live2`, `gt_f35farm2.txt`, folder `farm_f35_2`) and start again from step 0.

## What is not verified
The install of the forward-camera files (steps 0 and 1: pointing `HUSKY_URDF_EXTRAS` at the copied `husky_velodyne_extra_fwd.urdf.xacro` and writing `farm_fwd_config.yaml` into the VINS config folder) is reconstructed from Farm_Forward_Camera_Test.md, which does not list the commands of the 7 Nov runs; the sensor-rate printout of those runs was not recorded. If step 5b does not show the rates above, the run is void.

## Run 1 (10 Nov 2026, farm_f35.zip): void, not scored
The drive worked: the Husky left the reset at sim t = 121 s, drove the L and stopped at (-38.56, -39.98) after 81.9 m of ground-truth path; VINS-Mono followed it (end (-33.7, -35.3)). The F35 node started at sim t = 102 s with the printout `GUESS_MODE=ours HANDOVER=anchor PREDICT_GUARD=1` as required. The fusion log is not usable:
- 76,481 rows over 2,316 s (about 3.3 times the expected 10 Hz), up to 6 rows per timestamp, 4,821 backward steps in time; 245 non-text bytes in the file (the standard scorer stops on them).
- Rows with the same timestamp carry A-LOAM poses from different places (for example at t = 400.02 the `aft` position alternates between (-1021, 2403, -1309) and (-783, 687, 3979)), and A-LOAM's pose is already in the hundreds to thousands of metres at t = 103 to 110 s, before the robot moved (it moved from t = 121 s). The fused pose jumped to (515, 987, 3492) at t = 130 s and stayed there to the end of the log (t = 2418 s).
- Guess kinds (VO 90 %) are computed from that garbage and say nothing about F35.
So more than one A-LOAM or fusion pipeline was feeding or writing the log. The F35 settings are not the cause of that. The most likely source is processes left alive in `switchslam_gpu_v2` by the earlier replay batch (f35_all.sh runs A-LOAM and the node in the same container); the step-0 `pkill` list does not kill A-LOAM's own node processes. Not confirmed (the process list was not captured). Precondition FC-P0' was not documented for this run either (the step 5b printout and the scorer printout were not sent). Rule 5 applies: failed start, reported, not scored, whole sequence restarted from step 0 with the same settings.

## Revised start for the rerun (replaces the `pkill` line of step 0; nothing else changes)
Restart both containers instead of killing by name, copy the files after the restart, and check for a single A-LOAM and a single node before the drive:
```
docker restart switchslam_gpu_v2 vinsmono_test && sleep 15
docker exec switchslam_gpu_v2 bash -c "ps -eo pid,etime,args | grep -E 'ros|gz|alaser|ascan|fusion|logger|driver' | grep -v grep"      # expect nothing
```
After step 3 (A-LOAM): `docker exec -e ROS_IP=172.17.0.10 switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && rosnode list | sort && rostopic info /aft_mapped_to_init | grep -A2 Publishers"` shows one `/alaserMapping` publisher. Before step 8: `docker exec switchslam_gpu_v2 bash -c "pgrep -fc fusion_node_v2.py"` prints 1 (the tee shell may add one more line to ps; count only python3 processes). The first rows of the new log must have one row per 0.1 s.
