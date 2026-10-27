#!/bin/bash
# Prepare a new SubT-MRS sequence for run_fusion_study.sh (nothing about the method is tuned here).
#
#   ./setup_sequence.sh corridor ~/Downloads/SubT_MRS_Hawkins_Long_Corridor_RC \
#        <Intrinsics.yaml> <Extrinsics.yaml> <ground truth (csv or TUM txt)>
#
# It (1) reads the bag topics and time span, (2) writes the VINS-Mono config from the published calibration
# (make_vins_config.py; IMU noise and tracker settings copied from Multi Floor), (3) writes the velodyne-conversion
# and A-LOAM launch files with this bag's topics, (4) copies everything into the containers, (5) checks the
# ground truth against the bag time span, (6) writes ~/runs_<name>/seq.env for:
#   SEQ_ENV=~/runs_<name>/seq.env REPEAT=3 RECORD_KF=1 ./run_fusion_study.sh F0 F8
# Override topic choices with IMU_TOPIC=..., IMAGE_TOPIC=..., LIDAR_TOPIC=... if the printed choice is wrong.
set -u
NAME=$1; BAGDIR=$(cd "$2" && pwd); INTR=$(realpath "$3"); EXTR=$(realpath "$4"); GTF=$(realpath "$5")
FUSION_DIR=$(cd "$(dirname "$0")" && pwd)
GPU_C=switchslam_gpu_v2; VINS_C=vinsmono_test
OUT=~/runs_$NAME; mkdir -p $OUT
BAGS=$(cd "$BAGDIR" && ls -1 *.bag 2>/dev/null | sort)
[ -z "$BAGS" ] && { echo "no .bag in $BAGDIR (unzip first)"; exit 1; }
for c in $GPU_C $VINS_C; do docker start $c >/dev/null 2>&1; done

echo "== 1. bag info"
docker run --rm -v "$BAGDIR":/b:ro ros:noetic bash -c "source /opt/ros/noetic/setup.bash; cd /b; for f in $(echo $BAGS); do rosbag info \$f; done" > $OUT/rosbag_info.txt 2>&1
grep -E "^(path|duration|start|end|messages)" $OUT/rosbag_info.txt
grep -E "sensor_msgs/(Imu|Image|CompressedImage|PointCloud2)|velodyne_msgs/VelodyneScan" $OUT/rosbag_info.txt | sed 's/^ *topics: *//' | sort -u
# topic lines only ("/topic  N msgs : type"); the "types:" lines also contain the type name and must not match
pick() { grep -E "msgs? *: *($1)" $OUT/rosbag_info.txt | sed 's/^ *topics: *//' | awk '{print $1}' | grep '^/' | sort -u; }
IMU=${IMU_TOPIC:-$( (pick "sensor_msgs/Imu" | grep -m1 "imu/data") || pick "sensor_msgs/Imu" | head -1)}
IMG=${IMAGE_TOPIC:-$( (pick "sensor_msgs/Image( |$)" | grep -m1 "camera_1/image_raw") || pick "sensor_msgs/Image( |$)" | head -1)}
PKT=$(pick "velodyne_msgs/VelodyneScan" | head -1)
PTS=${LIDAR_TOPIC:-$(pick "sensor_msgs/PointCloud2" | grep -m1 velodyne)}
T0=$(grep -E "^start" $OUT/rosbag_info.txt | sed -E 's/.*\(([0-9.]+)\).*/\1/' | sort -n | head -1)
T1=$(grep -E "^end" $OUT/rosbag_info.txt | sed -E 's/.*\(([0-9.]+)\).*/\1/' | sort -n | tail -1)
DUR=$(python3 -c "print(round($T1-$T0,1))")
echo "chosen: imu=$IMU image=$IMG velodyne_packets=${PKT:-none} points=${PTS:-none} span $T0..$T1 ($DUR s)"
[ -z "$IMU" ] || [ -z "$IMG" ] && { echo "no IMU or image topic found: set IMU_TOPIC / IMAGE_TOPIC"; exit 1; }
[ -z "$PKT" ] && [ -z "$PTS" ] && { echo "no LiDAR topic found: set LIDAR_TOPIC"; exit 1; }
case "$IMU$IMG$PKT$PTS" in *msgs/*) echo "topic choice looks wrong (a message type was picked): set IMU_TOPIC / IMAGE_TOPIC / LIDAR_TOPIC"; exit 1;; esac
grep -q "compressed" <<< "$IMG" && echo "WARNING: compressed image topic - VINS-Mono needs raw images (republish)"

echo "== 2. VINS-Mono config"
python3 $FUSION_DIR/make_vins_config.py --intrinsics "$INTR" --extrinsics "$EXTR" --imu-topic "$IMU" \
  --image-topic "$IMG" --name $NAME --out $OUT/${NAME}_config.yaml || exit 1
docker cp $OUT/${NAME}_config.yaml $VINS_C:/root/catkin_ws/src/VINS-Mono/config/${NAME}_config.yaml
docker exec $VINS_C mkdir -p /root/vins_output_$NAME/pose_graph /root/thr

echo "== 3. launch files"
if [ -n "$PKT" ]; then
  POINTS=/$NAME/velodyne_points
  cat > $OUT/${NAME}_velodyne_convert.launch <<EOF
<launch>
  <node pkg="nodelet" type="nodelet" name="${NAME}_nodelet_manager" args="manager" output="screen"/>
  <node pkg="nodelet" type="nodelet" name="${NAME}_transform_nodelet"
        args="load velodyne_pointcloud/TransformNodelet ${NAME}_nodelet_manager" output="screen">
    <param name="calibration" value="\$(find velodyne_pointcloud)/params/VLP16db.yaml"/>
    <param name="min_range" value="0.4"/>
    <param name="max_range" value="130.0"/>
    <remap from="velodyne_packets" to="$PKT"/>
    <remap from="velodyne_points" to="$POINTS"/>
  </node>
</launch>
EOF
  docker cp $OUT/${NAME}_velodyne_convert.launch $GPU_C:/root/${NAME}_velodyne_convert.launch
  VEL=/root/${NAME}_velodyne_convert.launch
else
  POINTS=$PTS; VEL=""
fi
cat > $OUT/${NAME}_aloam.launch <<EOF
<launch>
    <param name="scan_line" type="int" value="16" />
    <param name="mapping_skip_frame" type="int" value="1" />
    <param name="minimum_range" type="double" value="0.3"/>
    <param name="mapping_line_resolution" type="double" value="0.2"/>
    <param name="mapping_plane_resolution" type="double" value="0.4"/>
    <node pkg="aloam_velodyne" type="ascanRegistration" name="${NAME}_ascanRegistration" output="screen">
        <remap from="/velodyne_points" to="$POINTS"/>
    </node>
    <node pkg="aloam_velodyne" type="alaserOdometry" name="${NAME}_alaserOdometry" output="screen"/>
    <node pkg="aloam_velodyne" type="alaserMapping" name="${NAME}_alaserMapping" output="screen">
        <remap from="/laser_odom_to_init" to="/switch_fused_pose"/>
    </node>
</launch>
EOF
docker cp $OUT/${NAME}_aloam.launch $GPU_C:/root/${NAME}_aloam.launch
docker exec $GPU_C mkdir -p /root/thr
docker cp "$EXTR" $GPU_C:/root/thr/${NAME}_extrinsics.yaml
cp "$EXTR" $OUT/${NAME}_extrinsics.yaml

echo "== 4. ground truth vs bag (on the clock the nodes use: message header stamps, not rosbag record times)"
HS=$(docker run --rm -i -v "$BAGDIR":/b:ro ros:noetic python3 - "${PKT:-$PTS}" "$IMU" "$IMG" 2>/dev/null <<'PY'
import rosbag, glob, sys
topics = sys.argv[1:]
b = rosbag.Bag(sorted(glob.glob("/b/*.bag"))[0]); seen = {}
for tp, m, t in b.read_messages(topics=topics):
    if tp not in seen:
        seen[tp] = 1
        print("STAMP %s %.3f %.3f" % (tp, t.to_sec(), m.header.stamp.to_sec()))
    if len(seen) == len(topics):
        break
PY
)
echo "$HS"
HT0=$(echo "$HS" | awk -v t="${PKT:-$PTS}" '$2==t{print $4}')
GT0=$T0; GT1=$T1
if [ -n "$HT0" ]; then
  GT0=$HT0; GT1=$(python3 -c "print(round($HT0+$T1-$T0,3))")
  python3 -c "d=abs($HT0-$T0); print('header stamps are on another clock than the record times (%.0f s apart): GT check uses the header clock' % d if d>1 else 'header stamps match the record times')"
fi
python3 $FUSION_DIR/check_gt.py --gt "$GTF" --bag-start $GT0 --bag-end $GT1 | tee $OUT/check_gt.txt
grep -q "NO OVERLAP" $OUT/check_gt.txt && echo "NOTE: the ground truth is on a different clock from the sensor stamps. After one full run: python3 $FUSION_DIR/align_gt_time.py --gt \"$GTF\" --seq-env $OUT/seq.env --logs $OUT/switching_log_v2_F8_run1.csv  (add --check-only to only look)"

MINR=$(python3 -c "print(int(7.2*$DUR))")
cat > $OUT/seq.env <<EOF
# written by setup_sequence.sh $(date +%F_%T)
BAG_DIR=$BAGDIR
GT=$GTF
VINS_CFG=/root/catkin_ws/src/VINS-Mono/config/${NAME}_config.yaml
VEL_LAUNCH=$VEL
ALOAM_LAUNCH=/root/${NAME}_aloam.launch
OUT_DIR=$OUT
MIN_ROWS=$MINR
SCORER=own
NODE_EXTRA="-e EXTRINSIC_YAML=/root/thr/${NAME}_extrinsics.yaml"
SUMMARY_EXTRA="--calib-end 0"
export EXTRINSIC_YAML=$OUT/${NAME}_extrinsics.yaml
EOF
echo "== done: $OUT/seq.env"; cat $OUT/seq.env
echo "next (smoke, 70 s):  SEQ_ENV=$OUT/seq.env SMOKE=1 ./run_fusion_study.sh F8"
