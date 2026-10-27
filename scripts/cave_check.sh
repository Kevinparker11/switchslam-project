#!/usr/bin/env bash
# Cave02 control, stage 1 (about 10-15 min): finds the files, checks the camera images are bright enough for VINS-Mono,
# sets the sequence up with setup_sequence.sh (nothing tuned), and runs ONE 70 s smoke test of F8.
# Writes ~/Downloads/for_claude12.zip (upload it to the chat). It does NOT start the full runs.
# Start:  bash ~/Downloads/cave_check.sh 2>&1 | tee ~/cave_check.log
set -u
CAVE="${CAVE:-/media/$USER/One Touch1/laptop_bags/Cave}"
[ -d "$CAVE" ] || { echo "folder not found: $CAVE  (is the drive mounted? set CAVE=... to override)"; exit 1; }

# --- fusion_v3 folder (the one that has run_fusion_study.sh with F16, not a backup copy)
D="${FUSION_V3_DIR:-}"
if [ -z "$D" ]; then
  for c in ~/switchslam_channelT/fusion_v3 "$(pwd)"; do
    [ -f "$c/setup_sequence.sh" ] && grep -q "F16" "$c/run_fusion_study.sh" 2>/dev/null && { D=$c; break; }
  done
fi
[ -n "$D" ] && [ -f "$D/setup_sequence.sh" ] || { echo "fusion_v3 folder not found: run  FUSION_V3_DIR=<folder> bash cave_check.sh"; exit 1; }
echo "fusion_v3: $D"; echo "cave folder: $CAVE"; ls -la "$CAVE" | head -40

# --- bag: unzip if needed, make sure the bag folder holds only Cave02 bags
BAGS=$(find "$CAVE" -maxdepth 3 -type f -iname "*.bag" 2>/dev/null | grep -i "cave02\|cave_02" || true)
if [ -z "$BAGS" ]; then
  Z=$(find "$CAVE" -maxdepth 2 -type f -iname "*cave02*.zip" 2>/dev/null | head -1)
  if [ -n "$Z" ]; then
    echo "unzipping $Z"; mkdir -p "$CAVE/cave02_bag" && unzip -n -q "$Z" -d "$CAVE/cave02_bag" || { echo "unzip failed"; exit 1; }
    BAGS=$(find "$CAVE/cave02_bag" -type f -iname "*.bag")
  fi
fi
[ -z "$BAGS" ] && BAGS=$(find "$CAVE" -maxdepth 3 -type f -iname "*.bag" | head -5)
[ -z "$BAGS" ] && { echo "no .bag found under $CAVE"; exit 1; }
echo "bags:"; echo "$BAGS"
BAGDIR=$(dirname "$(echo "$BAGS" | head -1)")
if [ "$(ls -1 "$BAGDIR"/*.bag | wc -l)" != "$(echo "$BAGS" | wc -l)" ]; then
  echo "folder $BAGDIR holds other bags too: moving the Cave02 bag(s) into $CAVE/cave02_bag"
  mkdir -p "$CAVE/cave02_bag"; echo "$BAGS" | while read -r b; do mv -n "$b" "$CAVE/cave02_bag/"; done
  BAGDIR="$CAVE/cave02_bag"
fi
echo "bag folder: $BAGDIR"

# --- ground truth and calibration (search the cave folder and Downloads; never the Hawkins files)
SRCH=("$CAVE" ~/Downloads)
GT=$(find "${SRCH[@]}" -maxdepth 3 -type f -iname "*cave02*gt*" 2>/dev/null | head -1)
# in the cave folder any name is accepted; in Downloads only names with cave/laurel (never the Hawkins files)
cal() { { find "$CAVE" -maxdepth 3 -type f -iname "*$1*.yaml" 2>/dev/null
          find ~/Downloads -maxdepth 3 -type f -iname "*$1*.yaml" 2>/dev/null | grep -i -E "cave|laurel"; } ; }
EXTR=$(cal xtrinsic | head -1); INTR=$(cal ntrinsic | head -1)
echo "ground truth: ${GT:-NOT FOUND}"; echo "extrinsics:   ${EXTR:-NOT FOUND}"; echo "intrinsics:   ${INTR:-NOT FOUND}"
if [ -z "$GT" ] || [ -z "$EXTR" ] || [ -z "$INTR" ]; then
  echo; echo "Missing file(s). Put cave02_gt.txt and the cave Extrinsics/Intrinsics .yaml in $CAVE (any file name for the yaml files if they are in that folder; the name must contain 'extrinsic' / 'intrinsic')."
  echo "yaml files seen:"; find "${SRCH[@]}" -maxdepth 3 -type f -iname "*.yaml" 2>/dev/null | head -20
  exit 1
fi

OUT=~/runs_cave02; mkdir -p "$OUT"
# --- image brightness (3 sample frames saved as PNG) before anything else is invested
echo "== image brightness"
docker run --rm -i -v "$BAGDIR":/b:ro -v "$OUT":/o ros:noetic python3 - <<'PY' 2>&1 | tee "$OUT/brightness.txt"
import rosbag, glob, zlib, struct
bags = sorted(glob.glob("/b/*.bag")); b = rosbag.Bag(bags[0])
info = b.get_type_and_topic_info().topics
imgs = [t for t, v in info.items() if v.msg_type == "sensor_msgs/Image"]
comp = [t for t, v in info.items() if v.msg_type == "sensor_msgs/CompressedImage"]
print("image topics:", imgs, "compressed:", comp)
if not imgs: print("NO raw image topic - VINS-Mono needs raw images"); raise SystemExit
tp = next((t for t in imgs if "camera_1" in t), imgs[0]); n = info[tp].message_count; k = max(1, n // 12)
def png(path, w, h, g):
    raw = b"".join(b"\x00" + bytes(g[y*w:(y+1)*w]) for y in range(h))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b""))
means, dark, samples = [], [], []
for i, (t, m, ts) in enumerate(b.read_messages(topics=[tp])):
    if i % k: continue
    d = m.data; enc = m.encoding
    if enc in ("mono8", "8UC1"): g = bytes(d)
    elif enc in ("rgb8", "bgr8"): g = bytes((d[j] + d[j+1] + d[j+2]) // 3 for j in range(0, len(d) - 2, 3))
    else: print("skip encoding", enc); continue
    s = g[::37]; means.append(sum(s) / len(s)); dark.append(sum(1 for v in s if v < 20) / len(s))
    samples.append((g, m.width, m.height, enc))
for j, idx in enumerate(sorted({0, len(samples) // 2, len(samples) - 1})):
    if samples: png("/o/frame_%d.png" % j, samples[idx][1], samples[idx][2], samples[idx][0])
print("topic %s: %d msgs, sampled %d frames, encoding %s" % (tp, n, len(means), samples[0][3] if samples else "?"))
print("mean pixel value per sampled frame (0=black, 255=white):", [round(x) for x in means])
print("fraction of pixels below 20 per frame:", [round(x, 2) for x in dark])
med = sorted(means)[len(means)//2] if means else 0
print("median brightness %.0f -> %s  (rough guide only; look at frame_0..2.png)" % (med, "VERY DARK" if med < 25 else "dim" if med < 60 else "bright enough"))
PY

# --- sequence setup (calibration, VINS config, launch files, ground-truth check)
echo "== setup_sequence.sh"
cd "$D" || exit 1
./setup_sequence.sh cave02 "$BAGDIR" "$INTR" "$EXTR" "$GT" 2>&1 | tee "$OUT/setup.log" | tail -n 60

# --- one 70 s smoke test of F8 (no scoring)
if [ -f "$OUT/seq.env" ]; then
  echo "== smoke test F8 (70 s)"
  SEQ_ENV="$OUT/seq.env" SMOKE=1 PLAY_RATE=0.5 ./run_fusion_study.sh F8 2>&1 | tail -n 40 | tee "$OUT/smoke.log"
else echo "setup did not write seq.env: see $OUT/setup.log"; fi

# --- package
Z=~/Downloads/for_claude12.zip; T=$(mktemp -d)
find "$OUT" -maxdepth 1 -type f \( -name "*.txt" -o -name "*.log" -o -name "*.png" -o -name "*.yaml" -o -name "*.env" -o -name "*.csv" -o -name "*.out" -o -name "*.launch" \) -size -50M -exec cp {} "$T"/ \;
cp ~/cave_check.log "$T"/ 2>/dev/null
rm -f "$Z"; (cd "$T" && zip -q "$Z" *) && echo "zip: $Z ($(du -h "$Z" | cut -f1))"
rm -rf "$T"
echo "CAVE_CHECK_DONE $(date +%T)"
