#!/usr/bin/env bash
# Put everything the second computer needs, except the full bags, into <drive>/pc_transfer/ :
#   gt/ (ground-truth files that live in the laptop's home), laptop_facts.txt (CPU, Docker, disk), rosbag_info/ (rosbag info of
#   every bag), switchslam_repo.bundle (git bundle of the repo). Reads the bags' indexes only. Safe to run again: finished parts are skipped.
# usage (laptop, from anywhere):  bash fusion_v4/baselines/prep_pc_transfer.sh        DRIVE_ROOT=<mount point> to override
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
ROOT="${DRIVE_ROOT:-/media/$USER/One Touch2}"
mountpoint -q "$ROOT" || { echo "DRIVE NOT MOUNTED at $ROOT (set DRIVE_ROOT=...)"; exit 1; }
export BAGS_ROOT="$ROOT/laptop_bags"
T="$ROOT/pc_transfer"; mkdir -p "$T/gt" "$T/rosbag_info"

echo "== 1. ground truth"
for f in "$HOME/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv" \
         "$HOME/Downloads/SubT_MRS_Hawkins_Long_Corridor_RC/corridor01_gt.txt" \
         "$HOME/corridor02_files/corridor02_gt.txt"; do
  if [ -f "$f" ]; then cp -v "$f" "$T/gt/"; else echo "MISSING $f"; fi
done

echo "== 2. laptop facts"
{ echo "== uname"; uname -srm; echo "== os"; grep PRETTY /etc/os-release
  echo "== cpu"; lscpu | grep -E "Model name|^CPU\(s\)|Flags"
  echo "== docker"; docker version --format 'client {{.Client.Version}} server {{.Server.Version}}'
  echo "== images"; docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}'
  echo "== disk"; df -h / "$HOME"; } > "$T/laptop_facts.txt" 2>&1
echo "written $T/laptop_facts.txt"

echo "== 3. rosbag info"
for n in mf lc c02 cave02 geode; do
  ( source "$REPO/fusion_v4/stock_liosam/seq/$n.env"
    for b in "$BAG_DIR"/*.bag; do
      out="$T/rosbag_info/${n}_$(basename "$b" .bag).txt"
      grep -q '^path:' "$out" 2>/dev/null && { echo "have $out"; continue; }     # a real rosbag info starts with "path:"
      docker run --rm -v "$BAG_DIR":/bags:ro --entrypoint bash liosam_stock \
        -c "source /opt/ros/noetic/setup.bash; rosbag info /bags/$(basename "$b")" > "$out" 2>&1
      if grep -q '^path:' "$out"; then echo "wrote $out"; else echo "FAILED, content of $out:"; cat "$out"; fi
    done )
done

echo "== 4. repo bundle"
git -C "$REPO" bundle create "$T/switchslam_repo.bundle" --all

echo "== done"; ls -lh "$T" "$T/gt" "$T/rosbag_info"; du -sh "$T"
