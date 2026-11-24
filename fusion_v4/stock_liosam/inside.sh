#!/usr/bin/env bash
# Runs INSIDE the liosam_stock container (started by run_liosam.sh): one stock LIO-SAM run on one sequence.
# Input through the environment: IMU_TOPIC, PACKETS_TOPIC or POINTS_TOPIC, RATE, BAGS (names, in play order),
# EXTR (laser_to_imu yaml), ADAPT_NAN, ADAPT_TIME (0/1), PROFILE (upstream | indoor, see make_params.py). Output files go to /out.
# the ROS setup scripts read unset variables (ROS_MASTER_URI), so nounset is switched on only after sourcing
set +u
source /opt/ros/noetic/setup.bash
source /root/lio_ws/devel/setup.bash
set -u
S=/repo/fusion_v4/stock_liosam
OUT=/out
cd "$OUT" || exit 1
cp /root/lio_ws/COMMIT "$OUT/liosam_commit.txt"

roscore > roscore.log 2>&1 &
for i in $(seq 1 30); do rostopic list > /dev/null 2>&1 && break; sleep 1; done
rosparam set use_sim_time true

RAW=${POINTS_TOPIC:-}
PLAY_LIDAR=${POINTS_TOPIC:-}
if [ -n "${PACKETS_TOPIC:-}" ]; then
  # velodyne_packets -> points with the sensor model set, so ring and per-point time are written (same converter and
  # ranges as the rest of the project; only the model parameter is added, as for the GenZ-LIO runs)
  RAW=/liosam_vel_points
  PLAY_LIDAR=$PACKETS_TOPIC
  cat > vel.launch <<EOF
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
EOF
  roslaunch vel.launch > velodyne.log 2>&1 &
fi

CLOUD=$RAW
if [ "${ADAPT_NAN:-0}" = 1 ] || [ "${ADAPT_TIME:-0}" = 1 ]; then
  CLOUD=/liosam_cloud
  AD=""; [ "${ADAPT_NAN:-0}" = 1 ] && AD="$AD --drop-nan"; [ "${ADAPT_TIME:-0}" = 1 ] && AD="$AD --shift-time"
  python3 $S/cloud_adapter.py "$RAW" "$CLOUD" $AD > adapter.log 2>&1 &
  echo "adapter on:$AD" > adapter_used.txt
else
  echo "adapter off" > adapter_used.txt
fi

python3 $S/make_params.py --base /root/lio_ws/src/LIO-SAM/config/params.yaml --extrinsics "$(realpath "$EXTR")" \
  --points-topic "$CLOUD" --imu-topic "$IMU_TOPIC" --out "$OUT/params.yaml" --profile "${PROFILE:-upstream}" > params_changes.txt || exit 1
echo "${PROFILE:-upstream}" > profile.txt
cat > run.launch <<EOF
<launch>
  <rosparam file="$OUT/params.yaml" command="load"/>
  <include file="\$(find lio_sam)/launch/include/module_loam.launch"/>
</launch>
EOF
roslaunch run.launch > liosam.log 2>&1 &
python3 $S/record_odom.py /lio_sam/mapping/odometry "$OUT/odom.tum" > recorder.log 2>&1 &
for i in $(seq 1 40); do rostopic info /lio_sam/mapping/odometry 2>/dev/null | grep -q lio_sam_mapOptmization && break; sleep 1; done
sleep 3

BAGPATHS=""; for b in $BAGS; do BAGPATHS="$BAGPATHS /bags/$b"; done
( sleep 20; timeout 20 rostopic echo -n 1 "$CLOUD/fields" > cloud_fields.txt 2>&1 ) &
echo "play: rate $RATE, bags:$BAGPATHS, topics: $IMU_TOPIC $PLAY_LIDAR"
rosbag play --clock -q -r "$RATE" $BAGPATHS --topics "$IMU_TOPIC" "$PLAY_LIDAR" > player.log 2>&1
sleep 12   # let LIO-SAM finish the queued scans

pkill -INT -f record_odom.py; sleep 3
pkill -INT -f roslaunch; sleep 4   # roslaunch writes its "process has died" lines to the file only when it flushes, so count after it stops
{ grep -c "process has died" liosam.log || true; } > crashes.txt
echo "poses recorded: $(wc -l < "$OUT/odom.tum")"
