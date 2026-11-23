#!/usr/bin/env bash
# Runs INSIDE the r3live_stock container (started by run_r3live.sh): one stock R3LIVE run on one sequence.
# Input through the environment: IMU_TOPIC, PACKETS_TOPIC or POINTS_TOPIC, CAM_TOPIC, CAM_COMPRESSED (0/1), CAM_CONFIG (VINS config,
# repo-relative), RATE, BAGS (names, in play order), EXTR (laser_to_imu yaml), ADAPT_NAN, ADAPT_TIME (0/1), PLAY_SECONDS (0 = whole bag).
# Output files go to /out.
set +u
source /opt/ros/noetic/setup.bash
source /root/r3_ws/devel/setup.bash
set -u
S=/repo/fusion_v4/stock_r3live
L=/repo/fusion_v4/stock_liosam
B=/repo/fusion_v4/baselines
UP=/root/r3_ws/src/r3live
OUT=/out
cd "$OUT" || exit 1
cp /root/r3_ws/COMMIT "$OUT/r3live_commit.txt"

# R3LIVE opens an OpenCV window ("Control panel") in its VIO thread, so it needs a display: a virtual one, nothing is shown anywhere
Xvfb :99 -screen 0 1280x1024x24 > xvfb.log 2>&1 &
export DISPLAY=:99
for i in $(seq 1 20); do xdpyinfo -display :99 > /dev/null 2>&1 && break; sleep 0.5; done

roscore > roscore.log 2>&1 &
for i in $(seq 1 30); do rostopic list > /dev/null 2>&1 && break; sleep 1; done
rosparam set use_sim_time true

RAW=${POINTS_TOPIC:-}
PLAY_LIDAR=${POINTS_TOPIC:-}
if [ -n "${PACKETS_TOPIC:-}" ]; then
  RAW=/r3live_vel_points
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
  CLOUD=/r3live_cloud
  AD=""; [ "${ADAPT_NAN:-0}" = 1 ] && AD="$AD --drop-nan"; [ "${ADAPT_TIME:-0}" = 1 ] && AD="$AD --shift-time"
  python3 $L/cloud_adapter.py "$RAW" "$CLOUD" $AD > adapter.log 2>&1 &
  echo "adapter on:$AD" > adapter_used.txt
else
  echo "adapter off" > adapter_used.txt
fi
# the one non-Livox input format of the R3LIVE front end
python3 $S/vel_to_ouster.py "$CLOUD" /os_cloud_node/points > vel_to_ouster.log 2>&1 &

# camera: compressed bags are decompressed to a raw topic (as for LVI-SAM); an MEI camera is rectified to a pinhole image (R3LIVE takes pinhole only)
CAM_RAW=$CAM_TOPIC
CAM_PLAY=$CAM_TOPIC; [ "${CAM_COMPRESSED:-0}" = 1 ] && CAM_PLAY=${CAM_TOPIC%/image_raw}/compressed
if [ "${CAM_COMPRESSED:-0}" = 1 ]; then
  rosrun image_transport republish compressed in:=${CAM_TOPIC%/image_raw} raw out:=$CAM_TOPIC > republish.log 2>&1 &
fi
MODEL=$(python3 -c "import sys; sys.path.insert(0,'$B'); import mei_model as m; print(m.load_vins_camera_config('/repo/$CAM_CONFIG')[0]['model_type'])")
IMAGE_TOPIC=$CAM_RAW
if [ "$MODEL" = MEI ]; then
  IMAGE_TOPIC=/r3live_image
  python3 $B/mei_rectify.py "/repo/$CAM_CONFIG" "$CAM_RAW" "$IMAGE_TOPIC" > rectify.log 2>&1 &
fi
echo "camera model $MODEL, R3LIVE image topic $IMAGE_TOPIC" > camera_used.txt

python3 $S/r3_params.py --base $UP/config/r3live_config.yaml --extrinsics "$(realpath "$EXTR")" --camera-config "/repo/$CAM_CONFIG" \
  --out "$OUT/r3live_config.yaml" > params_changes.txt || exit 1

# the nodes and parameters of upstream r3live_bag.launch, unchanged, with our config file and topics. Left out: RViz (headless).
cat > run.launch <<EOT
<launch>
  <param name="LiDAR_pointcloud_topic" type="string" value="/laser_cloud_flat" />
  <param name="IMU_topic" type="string" value="$IMU_TOPIC" />
  <param name="Image_topic" type="string" value="$IMAGE_TOPIC" />
  <param name="r3live_common/map_output_dir" type="string" value="$OUT/r3live_output" />
  <rosparam command="load" file="$OUT/r3live_config.yaml" />
  <node pkg="r3live" type="r3live_LiDAR_front_end" name="r3live_LiDAR_front_end" output="screen" required="true"/>
  <node pkg="r3live" type="r3live_mapping" name="r3live_mapping" output="screen" required="true" />
</launch>
EOT
roslaunch run.launch > r3live.log 2>&1 &
python3 $S/record_tf.py "$OUT/odom.tum" > recorder.log 2>&1 &
for i in $(seq 1 60); do rosnode list 2>/dev/null | grep -q R3LIVE_main && break; sleep 1; done
sleep 5

BAGPATHS=""; for b in $BAGS; do BAGPATHS="$BAGPATHS /bags/$b"; done
DUR=""; [ "${PLAY_SECONDS:-0}" != 0 ] && DUR="-u $PLAY_SECONDS"
( sleep 20; timeout 20 rostopic echo -n 1 "$CLOUD/fields" > cloud_fields.txt 2>&1 ) &
echo "play: rate $RATE, bags:$BAGPATHS, topics: $IMU_TOPIC $PLAY_LIDAR $CAM_PLAY ${DUR:+(first $PLAY_SECONDS s)}"
rosbag play --clock -q -r "$RATE" $DUR $BAGPATHS --topics "$IMU_TOPIC" "$PLAY_LIDAR" "$CAM_PLAY" > player.log 2>&1
sleep 12   # let R3LIVE finish the queued scans

pkill -INT -f record_tf.py; sleep 3
pkill -INT -f roslaunch; sleep 4
{ grep -c "process has died" r3live.log || true; } > crashes.txt
echo "poses recorded: $(wc -l < "$OUT/odom.tum")"
