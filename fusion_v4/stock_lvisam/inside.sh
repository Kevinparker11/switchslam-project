#!/usr/bin/env bash
# Runs INSIDE the lvisam_stock container (started by run_lvisam.sh): one stock LVI-SAM run on one sequence.
# Input through the environment: IMU_TOPIC, PACKETS_TOPIC or POINTS_TOPIC, CAM_TOPIC, CAM_COMPRESSED (0/1), CAM_CONFIG (VINS config,
# repo-relative), RATE, BAGS (names, in play order), EXTR (laser_to_imu yaml), ADAPT_NAN, ADAPT_TIME (0/1), PLAY_SECONDS (0 = whole bag).
# Output files go to /out.
# the ROS setup scripts read unset variables (ROS_MASTER_URI), so nounset is switched on only after sourcing
set +u
source /opt/ros/noetic/setup.bash
source /root/lvi_ws/devel/setup.bash
set -u
S=/repo/fusion_v4/stock_lvisam
L=/repo/fusion_v4/stock_liosam
UP=/root/lvi_ws/src/LVI-SAM
OUT=/out
cd "$OUT" || exit 1
cp /root/lvi_ws/COMMIT "$OUT/lvisam_commit.txt"

roscore > roscore.log 2>&1 &
for i in $(seq 1 30); do rostopic list > /dev/null 2>&1 && break; sleep 1; done
rosparam set use_sim_time true

RAW=${POINTS_TOPIC:-}
PLAY_LIDAR=${POINTS_TOPIC:-}
if [ -n "${PACKETS_TOPIC:-}" ]; then
  # velodyne_packets -> points with the sensor model set, so ring and per-point time are written (as in the LIO-SAM runs)
  RAW=/lvisam_vel_points
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
  CLOUD=/lvisam_cloud
  AD=""; [ "${ADAPT_NAN:-0}" = 1 ] && AD="$AD --drop-nan"; [ "${ADAPT_TIME:-0}" = 1 ] && AD="$AD --shift-time"
  python3 $L/cloud_adapter.py "$RAW" "$CLOUD" $AD > adapter.log 2>&1 &
  echo "adapter on:$AD" > adapter_used.txt
else
  echo "adapter off" > adapter_used.txt
fi

python3 $S/lvi_params.py --camera-base $UP/config/params_camera.yaml --lidar-base $UP/config/params_lidar.yaml \
  --extrinsics "$(realpath "$EXTR")" --camera-config "/repo/$CAM_CONFIG" \
  --points-topic "$CLOUD" --imu-topic "$IMU_TOPIC" --image-topic "$CAM_TOPIC" --outdir "$OUT" > params_changes.txt || exit 1

# the nodes of upstream launch/include/module_sam.launch, unchanged, with our two parameter files. Left out: RViz and the robot
# state publisher (the runs are headless). The image republish line is kept only for a bag that stores compressed images.
{
  echo '<launch>'
  echo '  <arg name="project" default="lvi_sam"/>'
  echo "  <rosparam file=\"$OUT/params_lidar.yaml\" command=\"load\" />"
  echo "  <param name=\"vins_config_file\" type=\"string\" value=\"$OUT/params_camera.yaml\" />"
  for n in imuPreintegration imageProjection featureExtraction mapOptmization; do
    echo "  <node pkg=\"\$(arg project)\" type=\"\$(arg project)_$n\" name=\"\$(arg project)_$n\" output=\"screen\" respawn=\"true\"/>"
  done
  for n in visual_feature visual_odometry visual_loop; do
    echo "  <node pkg=\"\$(arg project)\" type=\"\$(arg project)_$n\" name=\"\$(arg project)_$n\" output=\"screen\" respawn=\"true\"/>"
  done
  if [ "${CAM_COMPRESSED:-0}" = 1 ]; then
    echo "  <node pkg=\"image_transport\" type=\"republish\" name=\"\$(arg project)_republish\" args=\"compressed in:=${CAM_TOPIC%/image_raw} raw out:=$CAM_TOPIC\" output=\"screen\" respawn=\"true\"/>"
  fi
  echo '</launch>'
} > run.launch
roslaunch run.launch > lvisam.log 2>&1 &
python3 $L/record_odom.py /lvi_sam/lidar/mapping/odometry "$OUT/odom.tum" > recorder.log 2>&1 &
for i in $(seq 1 40); do rostopic info /lvi_sam/lidar/mapping/odometry 2>/dev/null | grep -q lvi_sam_mapOptmization && break; sleep 1; done
sleep 3

BAGPATHS=""; for b in $BAGS; do BAGPATHS="$BAGPATHS /bags/$b"; done
CAM_PLAY=$CAM_TOPIC; [ "${CAM_COMPRESSED:-0}" = 1 ] && CAM_PLAY=${CAM_TOPIC%/image_raw}/compressed
DUR=""; [ "${PLAY_SECONDS:-0}" != 0 ] && DUR="-u $PLAY_SECONDS"
( sleep 20; timeout 20 rostopic echo -n 1 "$CLOUD/fields" > cloud_fields.txt 2>&1 ) &
echo "play: rate $RATE, bags:$BAGPATHS, topics: $IMU_TOPIC $PLAY_LIDAR $CAM_PLAY ${DUR:+(first $PLAY_SECONDS s)}"
rosbag play --clock -q -r "$RATE" $DUR $BAGPATHS --topics "$IMU_TOPIC" "$PLAY_LIDAR" "$CAM_PLAY" > player.log 2>&1
sleep 12   # let LVI-SAM finish the queued scans

pkill -INT -f record_odom.py; sleep 3
pkill -INT -f roslaunch; sleep 4   # roslaunch writes its "process has died" lines to the file only when it flushes, so count after it stops
{ grep -c "process has died" lvisam.log || true; } > crashes.txt
{ grep -c "VINS system reboot" lvisam.log || true; } > vins_reboots.txt
echo "poses recorded: $(wc -l < "$OUT/odom.tum")"
