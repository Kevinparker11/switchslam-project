#!/bin/bash
# Stage 2b: turn the recorded bag into pipeline sequences (setup_sequence.sh) and write the calibration.
#   ./gz_prepare.sh office            makes   gzoffice     (bag as recorded: the plugin's per-point time)
#                                              gzoffice_nd  (per-point time scaled by 1e-3: no false motion correction)
# Needs the recorded bag on the drive ("$BAGS_ROOT/gazebo_<world>/gazebo_<world>_*.bag") and a copy in the container or on the drive.
set -u
WORLD=${1:-office}; C=switchslam_gpu_v2; SCALE=${TIME_SCALE:-1e-3}
HERE=$(cd "$(dirname "$0")" && pwd); FV4=$(dirname "$HERE")
BAGS_ROOT=${BAGS_ROOT:-"/media/$USER/One Touch1/laptop_bags"}
D="$BAGS_ROOT/gazebo_$WORLD"; BAG=$(ls -1t "$D"/gazebo_${WORLD}_2*.bag 2>/dev/null | head -1)
[ -n "$BAG" ] || { echo "no recorded bag in $D (run ./gz_record.sh $WORLD)"; exit 1; }
B=$(basename "$BAG" .bag); echo "bag: $BAG"
docker start $C >/dev/null 2>&1
docker exec $C test -f /root/gz_bags/$B.bag || { echo "== copying the bag into the container"; docker exec $C mkdir -p /root/gz_bags; docker cp "$BAG" $C:/root/gz_bags/$B.bag; }
docker cp "$HERE/gz_convert.py" $C:/root/gz_convert.py
echo "== converting (a few minutes): time scale $SCALE"
docker exec $C bash -c "export ROS_MASTER_URI=http://localhost:11311; source /opt/ros/noetic/setup.bash; python3 /root/gz_convert.py /root/gz_bags/$B.bag /root/gz_bags/${B}_nd.bag /root/gz_bags/gt_$WORLD.txt $SCALE" || { echo "conversion failed"; exit 1; }
mkdir -p "$BAGS_ROOT/gazebo_${WORLD}_nd"
docker cp $C:/root/gz_bags/${B}_nd.bag "$BAGS_ROOT/gazebo_${WORLD}_nd/${B}_nd.bag" && docker cp $C:/root/gz_bags/gt_$WORLD.txt "$D/gt_$WORLD.txt" || exit 1
python3 "$HERE/make_sim_calib.py" "$D" || exit 1
for V in "" _nd; do
  NAME=gz$WORLD$V; BD="$D"; [ -n "$V" ] && BD="$BAGS_ROOT/gazebo_${WORLD}_nd"
  echo "################ setup_sequence $NAME"
  bash "$FV4/setup_sequence.sh" $NAME "$BD" "$D/gazebo_intrinsics.yaml" "$D/gazebo_extrinsics.yaml" "$D/gt_$WORLD.txt" 2>&1 | tail -25
done
echo "== done. Sequences: ~/runs_gz$WORLD/seq.env  ~/runs_gz${WORLD}_nd/seq.env"
