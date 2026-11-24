#!/usr/bin/env bash
# Runs INSIDE the r2live_stock container (started by run_r2live.sh): one stock R2LIVE run on one sequence.
# Input through the environment: IMU_TOPIC, PACKETS_TOPIC or POINTS_TOPIC, CAM_TOPIC, CAM_COMPRESSED (0/1), CAM_CONFIG (VINS config,
# repo-relative), RATE, BAGS (names, in play order), EXTR (laser_to_imu yaml), ADAPT_NAN, ADAPT_TIME (0/1), PLAY_SECONDS (0 = whole bag).
# Output files go to /out.
set +u
source /opt/ros/noetic/setup.bash
source /root/r2_ws/devel/setup.bash
set -u
S=/repo/fusion_v4/stock_r2live
L=/repo/fusion_v4/stock_liosam
UP=/root/r2_ws/src/r2live
OUT=/out
cd "$OUT" || exit 1
cp /root/r2_ws/COMMIT "$OUT/r2live_commit.txt"

roscore > roscore.log 2>&1 &
for i in $(seq 1 30); do rostopic list > /dev/null 2>&1 && break; sleep 1; done
rosparam set use_sim_time true

RAW=${POINTS_TOPIC:-}
PLAY_LIDAR=${POINTS_TOPIC:-}
if [ -n "${PACKETS_TOPIC:-}" ]; then
  RAW=/r2live_vel_points
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
  CLOUD=/r2live_cloud
  AD=""; [ "${ADAPT_NAN:-0}" = 1 ] && AD="$AD --drop-nan"; [ "${ADAPT_TIME:-0}" = 1 ] && AD="$AD --shift-time"
  python3 $L/cloud_adapter.py "$RAW" "$CLOUD" $AD > adapter.log 2>&1 &
  echo "adapter on:$AD" > adapter_used.txt
else
  echo "adapter off" > adapter_used.txt
fi
# per-point time into the field R2LIVE reads (curvature), on the input topic of its Ouster handler
python3 $S/vel_to_r2live.py "$CLOUD" /os1_cloud_node/points > vel_to_r2live.log 2>&1 &

# camera: compressed bags are decompressed to a raw topic (as for LVI-SAM and R3LIVE); R2LIVE's feature tracker takes MEI and pinhole as they are
CAM_PLAY=$CAM_TOPIC; [ "${CAM_COMPRESSED:-0}" = 1 ] && CAM_PLAY=${CAM_TOPIC%/image_raw}/compressed
if [ "${CAM_COMPRESSED:-0}" = 1 ]; then
  rosrun image_transport republish compressed in:=${CAM_TOPIC%/image_raw} raw out:=$CAM_TOPIC > republish.log 2>&1 &
fi

python3 $S/r2_params.py --lio-base $UP/config/lio_config.yaml --cam-base $UP/config/filr_cam.yaml --extrinsics "$(realpath "$EXTR")" \
  --camera-config "/repo/$CAM_CONFIG" --imu-topic "$IMU_TOPIC" --out-dir "$OUT" > params_changes.txt || exit 1

# the nodes and parameters of upstream demo.launch, unchanged, with our two config files and topics. Left out: RViz (headless).
# The LIO half subscribes to "/livox/imu" fixed in its source; the remap points that name at our IMU topic.
cat > run.launch <<EOT
<launch>
  <rosparam command="load" file="$OUT/lio_config.yaml" />
  <node name="feature_tracker" pkg="feature_tracker" type="feature_tracker" output="log">
    <param name="config_file" type="string" value="$OUT/cam_config.yaml" />
    <param name="vins_folder" type="string" value="$UP/" />
    <param name="image_topic" type="string" value="$CAM_TOPIC"/>
  </node>
  <param name="imu_topic" type="string" value="$IMU_TOPIC"/>
  <param name="if_write_to_bag" type="int" value="0" />
  <param name="record_bag_name" type="string" value="/home/ziv/kitti_bag/lic_record_bag/lic.bag" />
  <param name="if_dump_log" type="int" value="0" />
  <param name="acc_mul_G" type="int" value="0" />
  <param name="lidar_drag_cam_tim" type="int" value="10" />
  <param name="if_lidar_start_first" type="int" value="1" />
  <node pkg="r2live" type="lio_feat_extract" name="lio_feat_extract" output="log"/>
  <node name="r2live" pkg="r2live" type="r2live" output="screen">
    <param name="config_file" type="string" value="$OUT/cam_config.yaml" />
    <param name="vins_folder" type="string" value="$UP/" />
    <remap from="/livox/imu" to="$IMU_TOPIC"/>
  </node>
</launch>
EOT
roslaunch run.launch > r2live.log 2>&1 &
python3 $S/record_tf.py "$OUT/odom.tum" > recorder.log 2>&1 &
for i in $(seq 1 60); do rosnode list 2>/dev/null | grep -q "/r2live" && break; sleep 1; done
sleep 5

BAGPATHS=""; for b in $BAGS; do BAGPATHS="$BAGPATHS /bags/$b"; done
DUR=""; [ "${PLAY_SECONDS:-0}" != 0 ] && DUR="-u $PLAY_SECONDS"
( sleep 20; timeout 20 rostopic echo -n 1 "$CLOUD/fields" > cloud_fields.txt 2>&1 ) &
echo "play: rate $RATE, bags:$BAGPATHS, topics: $IMU_TOPIC $PLAY_LIDAR $CAM_PLAY ${DUR:+(first $PLAY_SECONDS s)}"
rosbag play --clock -q -r "$RATE" $DUR $BAGPATHS --topics "$IMU_TOPIC" "$PLAY_LIDAR" "$CAM_PLAY" > player.log 2>&1
sleep 12   # let R2LIVE finish the queued scans

pkill -INT -f record_tf.py; sleep 3
pkill -INT -f roslaunch; sleep 4
{ grep -c "process has died" r2live.log || true; } > crashes.txt
echo "poses recorded: $(wc -l < "$OUT/odom.tum")"
