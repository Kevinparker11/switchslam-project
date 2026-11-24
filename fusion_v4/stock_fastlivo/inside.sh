#!/usr/bin/env bash
# Runs INSIDE the fastlivo_stock container (started by run_fastlivo.sh): one stock FAST-LIVO run on one sequence.
# Input through the environment: IMU_TOPIC, PACKETS_TOPIC or POINTS_TOPIC, CAM_TOPIC, CAM_COMPRESSED (0/1), CAM_CONFIG (VINS config,
# repo-relative), RATE, BAGS (names, in play order), EXTR (laser_to_imu yaml), ADAPT_NAN, ADAPT_TIME (0/1), PLAY_SECONDS (0 = whole bag).
# Output files go to /out.
set +u
source /opt/ros/noetic/setup.bash
source /root/fl_ws/devel/setup.bash
set -u
S=/repo/fusion_v4/stock_fastlivo
L=/repo/fusion_v4/stock_liosam
B=/repo/fusion_v4/baselines
UP=/root/fl_ws/src/FAST-LIVO
OUT=/out
cd "$OUT" || exit 1
cp /root/fl_ws/COMMIT "$OUT/fastlivo_commit.txt"

# FAST-LIVO has no window of its own (only cv::waitKey in the main loop); a virtual display costs nothing and rules out a GUI-library start-up error
Xvfb :99 -screen 0 1280x1024x24 > xvfb.log 2>&1 &
export DISPLAY=:99
for i in $(seq 1 20); do xdpyinfo -display :99 > /dev/null 2>&1 && break; sleep 0.5; done

roscore > roscore.log 2>&1 &
for i in $(seq 1 30); do rostopic list > /dev/null 2>&1 && break; sleep 1; done
rosparam set use_sim_time true

RAW=${POINTS_TOPIC:-}
PLAY_LIDAR=${POINTS_TOPIC:-}
if [ -n "${PACKETS_TOPIC:-}" ]; then
  RAW=/fastlivo_vel_points
  PLAY_LIDAR=$PACKETS_TOPIC
  cat > vel.launch <<EOT
<launch>
  <node pkg="nodelet" type="nodelet" name="vel_manager" args="manager"/>
  <node pkg="nodelet" type="nodelet" name="vel_transform" args="load velodyne_pointcloud/TransformNodelet vel_manager">
    <param name="calibration" value="\$(find velodyne_pointcloud)/params/VLP16db.yaml"/>
    <param name="model" value="VLP16"/>
    <param name="min_range" value="0.4"/>
    <param name="max_range" value="130.0"/>
    <remap from="velodyne_packets" to="$PACKETS_TOPIC"/>
    <remap from="velodyne_points" to="$RAW"/>
  </node>
</launch>
EOT
  roslaunch vel.launch > velodyne.log 2>&1 &
fi

CLOUD=$RAW
if [ "${ADAPT_NAN:-0}" = 1 ] || [ "${ADAPT_TIME:-0}" = 1 ]; then
  CLOUD=/fastlivo_cloud
  AD=""; [ "${ADAPT_NAN:-0}" = 1 ] && AD="$AD --drop-nan"; [ "${ADAPT_TIME:-0}" = 1 ] && AD="$AD --shift-time"
  python3 $L/cloud_adapter.py "$RAW" "$CLOUD" $AD > adapter.log 2>&1 &
  echo "adapter on:$AD" > adapter_used.txt
else
  echo "adapter off" > adapter_used.txt
fi
# FAST-LIVO reads Ouster clouds (lidar_type 3, field t in ns): the same converter as for R3LIVE
python3 /repo/fusion_v4/stock_r3live/vel_to_ouster.py "$CLOUD" /os_cloud_node/points > vel_to_ouster.log 2>&1 &

# camera: compressed bags are decompressed to a raw topic (as for LVI-SAM); an MEI camera is rectified to a pinhole image (FAST-LIVO takes pinhole only)
CAM_RAW=$CAM_TOPIC
CAM_PLAY=$CAM_TOPIC; [ "${CAM_COMPRESSED:-0}" = 1 ] && CAM_PLAY=${CAM_TOPIC%/image_raw}/compressed
if [ "${CAM_COMPRESSED:-0}" = 1 ]; then
  rosrun image_transport republish compressed in:=${CAM_TOPIC%/image_raw} raw out:=$CAM_TOPIC > republish.log 2>&1 &
fi
MODEL=$(python3 -c "import sys; sys.path.insert(0,'$B'); import mei_model as m; print(m.load_vins_camera_config('/repo/$CAM_CONFIG')[0]['model_type'])")
IMAGE_TOPIC=$CAM_RAW
if [ "$MODEL" = MEI ]; then
  IMAGE_TOPIC=/fastlivo_image
  python3 $B/mei_rectify.py "/repo/$CAM_CONFIG" "$CAM_RAW" "$IMAGE_TOPIC" > rectify.log 2>&1 &
fi
echo "camera model $MODEL, FAST-LIVO image topic $IMAGE_TOPIC" > camera_used.txt

python3 $S/fl_params.py --main-base $UP/config/NTU_VIRAL.yaml --cam-base $UP/config/camera_NTU_VIRAL.yaml --extrinsics "$(realpath "$EXTR")" \
  --camera-config "/repo/$CAM_CONFIG" --lid-topic /os_cloud_node/points --imu-topic "$IMU_TOPIC" --img-topic "$IMAGE_TOPIC" --out-dir "$OUT" > params_changes.txt || exit 1

# the node and parameter files of upstream mapping_avia_ntu.launch, unchanged, with our two config files. Left out: RViz (headless), the republish node
# (done above for compressed bags), the gdb launch prefix.
cat > run.launch <<EOT
<launch>
  <rosparam command="load" file="$OUT/fastlivo_config.yaml" />
  <node pkg="fast_livo" type="fastlivo_mapping" name="laserMapping" output="screen" required="true">
    <rosparam file="$OUT/fastlivo_camera.yaml" />
  </node>
</launch>
EOT
roslaunch run.launch > fastlivo.log 2>&1 &
python3 $L/record_odom.py /aft_mapped_to_init "$OUT/odom.tum" > recorder.log 2>&1 &
for i in $(seq 1 60); do rosnode list 2>/dev/null | grep -q "/laserMapping" && break; sleep 1; done
sleep 5

BAGPATHS=""; for b in $BAGS; do BAGPATHS="$BAGPATHS /bags/$b"; done
DUR=""; [ "${PLAY_SECONDS:-0}" != 0 ] && DUR="-u $PLAY_SECONDS"
( sleep 20; timeout 20 rostopic echo -n 1 "$CLOUD/fields" > cloud_fields.txt 2>&1 ) &
echo "play: rate $RATE, bags:$BAGPATHS, topics: $IMU_TOPIC $PLAY_LIDAR $CAM_PLAY ${DUR:+(first $PLAY_SECONDS s)}"
rosbag play --clock -q -r "$RATE" $DUR $BAGPATHS --topics "$IMU_TOPIC" "$PLAY_LIDAR" "$CAM_PLAY" > player.log 2>&1
sleep 12   # let FAST-LIVO finish the queued scans

pkill -INT -f record_odom.py; sleep 3
pkill -INT -f roslaunch; sleep 4
{ grep -c "process has died" fastlivo.log || true; } > crashes.txt
# FAST-LIVO prints these when its buffers see time going backwards; counted and reported
{ echo "img_loop_back=$(grep -c "img loop back" fastlivo.log || true)"; echo "imu_loop_back=$(grep -c "imu loop back" fastlivo.log || true)"; echo "not_ready=$(grep -c "FAST-LIO not ready" fastlivo.log || true)"; } > fastlivo_msgs.txt
echo "poses recorded: $(wc -l < "$OUT/odom.tum")"
