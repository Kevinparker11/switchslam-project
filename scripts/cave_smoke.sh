#!/usr/bin/env bash
# Cave02 stage 1b: repairs ~/runs_cave02/seq.env (setup_sequence.sh wrote the paths without quotes, and "One Touch1" has a
# space), shows the header stamps of the bag against the ground truth clock, then runs the 70 s F8 smoke test.
# Writes ~/Downloads/for_claude13.zip. Does not start the full runs.
# Start:  bash ~/Downloads/cave_smoke.sh 2>&1 | tee ~/cave_smoke.log
set -u
OUT=~/runs_cave02; ENV="$OUT/seq.env"
[ -f "$ENV" ] || { echo "$ENV not found: run cave_check.sh first"; exit 1; }
D="${FUSION_V3_DIR:-$HOME/switchslam_channelT/fusion_v3}"
[ -f "$D/run_fusion_study.sh" ] || { echo "fusion_v3 folder not found: FUSION_V3_DIR=<folder> bash cave_smoke.sh"; exit 1; }

# 1. quote the paths that contain a space
sed -i -E '/^(BAG_DIR|GT)=[^"]/ s/^([A-Z_]+)=(.*)$/\1="\2"/' "$ENV"
grep -E "^(BAG_DIR|GT)=" "$ENV"
BAGDIR=$(bash -c "source '$ENV' >/dev/null 2>&1; echo \"\$BAG_DIR\""); GT=$(bash -c "source '$ENV' >/dev/null 2>&1; echo \"\$GT\"")
[ -d "$BAGDIR" ] && [ -f "$GT" ] || { echo "seq.env still wrong: BAG_DIR=[$BAGDIR] GT=[$GT]"; exit 1; }

# 2. header stamps of the first message of each sensor topic (errors are shown this time)
echo "== header stamps vs record times"
docker run --rm -i -v "$BAGDIR":/b:ro ros:noetic python3 - <<'PY' 2>&1 | tee "$OUT/header_stamps.txt"
import rosbag, glob
b = rosbag.Bag(sorted(glob.glob("/b/*.bag"))[0]); seen = {}
want = ["/velodyne_points", "/imu/data", "/camera_1/image_raw"]
for tp, m, t in b.read_messages(topics=want):
    if tp not in seen:
        seen[tp] = 1
        print("STAMP %s record=%.3f header=%.3f" % (tp, t.to_sec(), m.header.stamp.to_sec()))
    if len(seen) == len(want): break
PY
HT0=$(grep "STAMP /velodyne_points" "$OUT/header_stamps.txt" | sed -E 's/.*header=([0-9.]+).*/\1/')
GT0=$(grep -v '^#' "$GT" | head -1 | awk '{print $1}')
if [ -n "$HT0" ]; then
  python3 - "$HT0" "$GT0" <<'PY'
import sys
h, g = float(sys.argv[1]), float(sys.argv[2]); d = g - h
print("first LiDAR header stamp %.2f, first ground-truth stamp %.2f, difference %.2f s" % (h, g, d))
print("-> ground truth is on the header clock" if abs(d) < 5 else "-> ground truth is NOT on the header clock (constant offset to be found with align_gt_time.py after a full run)")
PY
else echo "no header stamp read"; fi

# 3. smoke test: F8, 70 s, no scoring
echo "== smoke test F8 (70 s)"
cd "$D" || exit 1
SEQ_ENV="$ENV" SMOKE=1 PLAY_RATE=0.5 ./run_fusion_study.sh F8 2>&1 | tail -n 40 | tee "$OUT/smoke.log"
ls -la "$OUT" | tail -n 20

# 4. package
Z=~/Downloads/for_claude13.zip; T=$(mktemp -d)
find "$OUT" -maxdepth 1 -type f \( -name "*.txt" -o -name "*.log" -o -name "*.yaml" -o -name "*.env" -o -name "*.csv" -o -name "*.out" -o -name "*.launch" \) -size -50M -exec cp {} "$T"/ \;
cp ~/cave_smoke.log "$T"/ 2>/dev/null
rm -f "$Z"; (cd "$T" && zip -q "$Z" *) && echo "zip: $Z ($(du -h "$Z" | cut -f1))"
rm -rf "$T"
echo "CAVE_SMOKE_DONE $(date +%T)"
