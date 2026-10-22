#!/bin/bash
# Prepare GEODE device alpha (stairs) for run_fusion_study.sh. Nothing about the method is tuned: the camera, IMU noise and
# extrinsics are the published calibration from alpha_config.yaml.
#   ./setup_geode.sh                       (bag + alpha_config.yaml in laptop_bags/GEODE)
#   ./setup_geode.sh <ground-truth file>   (once the GEODE stairs-alpha trajectory has been downloaded)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
BAGDIR="/media/kavinkumar/One Touch1/laptop_bags/GEODE"
GTF=${1:-}
GPU_C=switchslam_gpu_v2; VINS_C=vinsmono_test
OUT=~/runs_geode; mkdir -p $OUT
[ -f "$BAGDIR/stairs_alpha.bag" ] || { echo "missing $BAGDIR/stairs_alpha.bag"; exit 1; }
for c in $GPU_C $VINS_C; do docker start $c >/dev/null 2>&1; done
docker exec $VINS_C mkdir -p /root/vins_output_geode/pose_graph /root/thr
docker exec $GPU_C mkdir -p /root/thr
docker cp $HERE/geode_config.yaml $VINS_C:/root/catkin_ws/src/VINS-Mono/config/geode_config.yaml
docker cp $HERE/geode_republish.py $VINS_C:/root/thr/geode_republish.py
docker cp $HERE/geode_extrinsics.yaml $GPU_C:/root/thr/geode_extrinsics.yaml
cat > $OUT/geode_aloam.launch <<'XML'
<launch>
    <param name="scan_line" type="int" value="16" />
    <param name="mapping_skip_frame" type="int" value="1" />
    <param name="minimum_range" type="double" value="0.3"/>
    <param name="mapping_line_resolution" type="double" value="0.2"/>
    <param name="mapping_plane_resolution" type="double" value="0.4"/>
    <node pkg="aloam_velodyne" type="ascanRegistration" name="geode_ascanRegistration" output="screen">
        <remap from="/velodyne_points" to="/velodyne_points"/>
    </node>
    <node pkg="aloam_velodyne" type="alaserOdometry" name="geode_alaserOdometry" output="screen"/>
    <node pkg="aloam_velodyne" type="alaserMapping" name="geode_alaserMapping" output="screen">
        <remap from="/laser_odom_to_init" to="/switch_fused_pose"/>
    </node>
</launch>
XML
docker cp $OUT/geode_aloam.launch $GPU_C:/root/geode_aloam.launch
cp $HERE/geode_extrinsics.yaml $OUT/geode_extrinsics.yaml
cat > $OUT/seq.env <<EOT
# written by setup_geode.sh $(date +%F_%T)
BAG_DIR="$BAGDIR"
GT="${GTF:-/NO_GEODE_GROUND_TRUTH_YET}"
VINS_CFG=/root/catkin_ws/src/VINS-Mono/config/geode_config.yaml
VEL_LAUNCH=
ALOAM_LAUNCH=/root/geode_aloam.launch
OUT_DIR=$OUT
MIN_ROWS=2400
SCORER=own
IMU_TOPIC_USED=/imu/data
VINS_PRE_CMD="rosrun image_transport republish compressed in:=/left_camera raw out:=/left_camera/image_raw"
NODE_EXTRA="-e EXTRINSIC_YAML=/root/thr/geode_extrinsics.yaml"
SUMMARY_EXTRA="--calib-end 0"
export EXTRINSIC_YAML=$OUT/geode_extrinsics.yaml
EOT
echo "== done: $OUT/seq.env"; cat $OUT/seq.env
echo "check the container can decode JPEG and publish:"
docker exec $VINS_C bash -c "python -c 'import cv2, numpy, rospy; print(\"cv2\", cv2.__version__)'" 2>&1 | tail -1
echo "next (smoke, 70 s):  SEQ_ENV=$OUT/seq.env SMOKE=1 SMOKE_SECS=160 FRONT=aloam ./run_fusion_study.sh F8"
