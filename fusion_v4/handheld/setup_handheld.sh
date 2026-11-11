#!/bin/bash
# Prepare the LVI-SAM Handheld bag for run_fusion_study.sh (11 Nov 2026), modelled on geode/setup_geode.sh. Nothing about the method is tuned:
# VINS-Mono config, LiDAR-IMU and camera-IMU extrinsics are LVI-SAM's own published values (handheld_config.yaml, handheld_Extrinsics.yaml).
#   ./handheld/setup_handheld.sh <handheld_gps_xy_clean.txt>        (bag in laptop_bags/handheld, GPS reference from make_gps_reference.py)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
BAGDIR=${HANDHELD_DIR:-"$(ls -d /media/$USER/*/laptop_bags/handheld 2>/dev/null | head -1)"}
GTF=$(realpath "${1:?usage: setup_handheld.sh handheld_gps_xy_clean.txt}")
GPU_C=switchslam_gpu_v2; VINS_C=vinsmono_test
OUT=~/runs_handheld; mkdir -p $OUT
[ -f "$BAGDIR/handheld.bag" ] || { echo "missing $BAGDIR/handheld.bag (set HANDHELD_DIR=)"; exit 1; }
for c in $GPU_C $VINS_C; do docker start $c >/dev/null 2>&1; done
docker exec $VINS_C mkdir -p /root/vins_output_handheld/pose_graph /root/thr
docker exec $GPU_C mkdir -p /root/thr
docker cp $HERE/handheld_config.yaml $VINS_C:/root/catkin_ws/src/VINS-Mono/config/handheld_config.yaml
docker cp $HERE/handheld_Extrinsics.yaml $GPU_C:/root/thr/handheld_extrinsics.yaml
cat > $OUT/handheld_aloam.launch <<'XML'
<launch>
    <param name="scan_line" type="int" value="16" />
    <param name="mapping_skip_frame" type="int" value="1" />
    <param name="minimum_range" type="double" value="0.3"/>
    <param name="mapping_line_resolution" type="double" value="0.2"/>
    <param name="mapping_plane_resolution" type="double" value="0.4"/>
    <node pkg="aloam_velodyne" type="ascanRegistration" name="handheld_ascanRegistration" output="screen">
        <remap from="/velodyne_points" to="/points_raw"/>
    </node>
    <node pkg="aloam_velodyne" type="alaserOdometry" name="handheld_alaserOdometry" output="screen"/>
    <node pkg="aloam_velodyne" type="alaserMapping" name="handheld_alaserMapping" output="screen">
        <remap from="/laser_odom_to_init" to="/switch_fused_pose"/>
    </node>
</launch>
XML
docker cp $OUT/handheld_aloam.launch $GPU_C:/root/handheld_aloam.launch
cp $HERE/handheld_Extrinsics.yaml $OUT/handheld_extrinsics.yaml
cat > $OUT/seq.env <<EOT
# written by setup_handheld.sh $(date +%F_%T)
BAG_DIR="$BAGDIR"
GT="$GTF"
VINS_CFG=/root/catkin_ws/src/VINS-Mono/config/handheld_config.yaml
VEL_LAUNCH=
ALOAM_LAUNCH=/root/handheld_aloam.launch
OUT_DIR=$OUT
MIN_ROWS=5000
SCORER=xy
IMU_TOPIC_USED=/imu_raw
VINS_PRE_CMD="rosrun image_transport republish compressed in:=/camera/image_raw raw out:=/camera/image_raw"
NODE_EXTRA="-e EXTRINSIC_YAML=/root/thr/handheld_extrinsics.yaml"
SUMMARY_EXTRA="--calib-end 0"
export EXTRINSIC_YAML=$OUT/handheld_extrinsics.yaml
EOT
echo "== done: $OUT/seq.env"; cat $OUT/seq.env
echo "next (smoke, 160 s):  SEQ_ENV=$OUT/seq.env SMOKE=1 SMOKE_SECS=160 FRONT=aloam PLAY_RATE=0.5 ./run_fusion_study.sh F26"
