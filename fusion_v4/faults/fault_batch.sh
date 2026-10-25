#!/bin/bash
# Sensor-outage campaign on real recordings (protocol: docs/results/Fault_Injection_Protocol.md). Laptop only, about 5-5.5 h, hard cap MAX_HOURS.
# Every run rewrites the recorded bag with camera or LiDAR outages at fixed times (make_fault_bag.py), plays it through the live G20 stack
# (G22 as well on two Long Corridor runs) under exactly the settings of the 24 Oct live runs (Multi Floor 1.0x, Long Corridor and Cave02 0.5x),
# keeps the logs (exact replay gives G0, G17, G19, G22 and VINS-Mono alone from them) and deletes the rewritten bag again.
#   bash fault_batch.sh                run everything in priority order, resumable (runs with a DONE file are skipped)
#   bash fault_batch.sh pack           only (re)build ~/faults_results.tgz from what exists
#   MAX_HOURS=4 bash fault_batch.sh    lower cap; a run is only started if it is expected to end before the cap
#   DEADLINE=06:50 bash fault_batch.sh a clock time (laptop time, next occurrence) instead of MAX_HOURS; no run is started that would end after it
#   Disk: the rewritten bags go to the drive and are deleted after each run; on the laptop SSD every finished run is compacted (raw stage logs
#   replaced by filtered excerpts), about 20-30 MB per run; the batch stops if the SSD has less than 3 GB free.
#   ONLY="MF_C10_r1 LC_L30_r1" bash fault_batch.sh     run just these tags
# Detach it:  setsid nohup systemd-inhibit --what=sleep:idle bash fault_batch.sh > ~/faults_batch.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); REPO=$(dirname "$FV4")
BAGS_ROOT=${BAGS_ROOT:-"/media/$USER/One Touch1/laptop_bags"}
FAULT_ROOT="$BAGS_ROOT/_faults"; WORK=$HOME/runs_faults; PACK=$HOME/runs_faults_pack
MAX_HOURS=${MAX_HOURS:-5.75}; LIMIT=$(awk -v h="$MAX_HOURS" 'BEGIN{printf "%d", h*3600}')
if [ -n "${DEADLINE:-}" ]; then
  LIMIT=$(( $(date -d "$DEADLINE" +%s) - $(date +%s) )); [ "$LIMIT" -le 0 ] && LIMIT=$(( LIMIT + 86400 ))
  CAP="until $DEADLINE ($(( LIMIT / 3600 )) h $(( LIMIT % 3600 / 60 )) min from now)"
fi
CAP=${CAP:-$MAX_HOURS h}
GPU_C=switchslam_gpu_v2; VINS_C=vinsmono_test
SUM=$WORK/batch_summary.csv
say() { echo "[$(date +%H:%M:%S)] $*"; }

ssd_free() { df -BG --output=avail "$HOME" | tail -1 | tr -dc 0-9; }
compact() {   # $1 = run output folder: keep switching logs, scores, summaries, keyframes; replace the raw stage logs by filtered excerpts
  local d=$1 f
  for f in "$d"/node_*.out; do [ -f "$f" ] && { tail -n 3000 "$f" > "$f.tail"; rm -f "$f"; }; done
  for f in "$d"/vins_*.out "$d"/ft_*.out "$d"/genz_*.out "$d"/bridge_*.out "$d"/velodyne_*.out; do
    [ -f "$f" ] || continue
    grep -aiE "fail|restart|reset|init|warn|error|lost|drop|unstable|diverg|nan" "$f" | head -n 3000 > "$f.filtered"; wc -l < "$f" > "$f.lines"; rm -f "$f"
  done
}
pack() {
  rm -rf "$PACK"; mkdir -p "$PACK"
  for d in "$WORK"/*_genz; do
    [ -d "$d" ] || continue; n=$(basename "$d" _genz); mkdir -p "$PACK/$n"
    cp "$d"/switching_log_v2_*.csv "$d"/ate_*.txt "$d"/summary_*.txt "$d"/node_head_*.txt "$d"/fault_manifest.json "$d"/results_index.csv "$d"/failed_runs.csv "$PACK/$n/" 2>/dev/null
    compact "$d"
    cp "$d"/*.tail "$d"/*.filtered "$d"/*.lines "$PACK/$n/" 2>/dev/null
  done
  cp "$SUM" "$PACK/" 2>/dev/null; cp "$WORK"/*.log "$PACK/" 2>/dev/null; cp "$HOME/faults_batch.log" "$PACK/" 2>/dev/null
  tar czf "$HOME/faults_results.tgz" -C "$PACK" . && say "packed: $HOME/faults_results.tgz ($(du -h "$HOME/faults_results.tgz" | cut -f1), $(ls "$PACK" | wc -l) entries)"
}
[ "${1:-}" = pack ] && { pack; exit 0; }

mkdir -p "$WORK" "$FAULT_ROOT"
[ -f "$SUM" ] || echo "tag,configs,status,minutes,detail" > "$SUM"
template() { case $1 in LC) t=$HOME/runs_corridor_A_L/seq.env; [ -f "$t" ] || t=$REPO/configs/seq_env_examples/corridor.seq.env ;;
                         C02) t=$HOME/runs_cave02_rate05_L/seq.env; [ -f "$t" ] || t=$REPO/configs/seq_env_examples/cave02.seq.env ;; esac; echo "$t"; }
src_dir() { case $1 in
    MF) for d in multifloor MultiFloor Multi_Floor multi_floor RosBag; do ls "$BAGS_ROOT/$d"/*.bag >/dev/null 2>&1 && { echo "$BAGS_ROOT/$d"; return; }; done ;;
    *)  ( source "$(template $1)" >/dev/null 2>&1; echo "${BAG_DIR:-}" ) ;; esac; }
declare -A RATE=([MF]=1.0 [LC]=0.5 [C02]=0.5) EST=([MF]=600 [LC]=640 [C02]=2200)

for c in $GPU_C $VINS_C; do docker inspect $c >/dev/null 2>&1 || { say "container $c does not exist"; exit 1; }; docker start $c >/dev/null 2>&1; done
docker image inspect ros:noetic >/dev/null 2>&1 || { say "image ros:noetic missing"; exit 1; }
[ -d "$BAGS_ROOT" ] || { say "bag drive not found: $BAGS_ROOT"; exit 1; }
say "free space: laptop SSD $(ssd_free) GB, drive $(df -BG --output=avail "$BAGS_ROOT" | tail -1 | tr -dc 0-9) GB"
[ "$(ssd_free)" -ge 3 ] || { say "less than 3 GB free on the laptop SSD - free some space first"; exit 1; }
for s in MF LC C02; do d=$(src_dir $s); if ls "$d"/*.bag >/dev/null 2>&1; then say "$s bags: $d ($(du -sh "$d" | cut -f1))"; else say "$s: no bags found ($d)"; fi; done

# priority order: S control, A core (8 runs), B replicates, C cave. tag = SEQ_FAULT_rREP, configs run live on that rewritten bag
PLAN=(
 "MF none 1 G20"
 "MF C10 1 G20" "MF L10 1 G20" "MF C30 1 G20" "MF L30 1 G20"
 "LC C10 1 G20" "LC L10 1 G20" "LC C30 1 G20 G22" "LC L30 1 G20 G22"
 "MF C10 2 G20" "MF L10 2 G20" "MF C30 2 G20" "MF L30 2 G20"
 "LC C10 2 G20" "LC L10 2 G20" "LC C30 2 G20" "LC L30 2 G20"
 "C02 C30 1 G20" "C02 L30 1 G20"
)
START=$SECONDS; FAILS=0
say "plan: ${#PLAN[@]} runs, cap $CAP; start $(date)"
for item in "${PLAN[@]}"; do
  set -- $item; seq=$1; fault=$2; rep=$3; shift 3; cfgs="$*"; ncfg=$#; tag=${seq}_${fault}_r${rep}
  [ -n "${ONLY:-}" ] && ! echo " $ONLY " | grep -q " $tag " && continue
  OUTD="$WORK/${tag}_genz"
  [ -f "$OUTD/DONE" ] && { say "$tag: done earlier, skipping"; continue; }
  need=$(( EST[$seq] * ncfg + 300 )); el=$(( SECONDS - START ))
  if [ $(( el + need )) -gt $LIMIT ]; then say "$tag: SKIPPED (elapsed ${el}s + about ${need}s would pass the cap)"; echo "$tag,\"$cfgs\",SKIPPED_TIME,0,cap" >> "$SUM"; continue; fi
  if [ $FAILS -ge 3 ]; then say "three failures in a row - stopping (look at the logs in $WORK)"; break; fi
  [ "$(ssd_free)" -ge 3 ] || { say "less than 3 GB free on the laptop SSD - stopping"; break; }
  src=$(src_dir $seq); dst="$FAULT_ROOT/$tag"; T0=$SECONDS
  say "=== $tag  (seq $seq, fault $fault, rep $rep, configs: $cfgs)  elapsed $(( el / 60 )) min"
  FREE=$(df -BG --output=avail "$BAGS_ROOT" | tail -1 | tr -dc 0-9); SZ=$(du -s -BG "$src" | cut -f1 | tr -dc 0-9)
  [ "$FREE" -gt $(( SZ + 2 )) ] || { say "$tag: not enough free space on the drive (${FREE} GB free, need $(( SZ + 2 )))"; echo "$tag,\"$cfgs\",FAIL_SPACE,0," >> "$SUM"; FAILS=$((FAILS+1)); continue; }
  rm -rf "$dst"; mkdir -p "$dst"
  docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$src":/in:ro -v "$dst":/out -v "$HERE":/tools:ro ros:noetic bash -c \
    "source /opt/ros/noetic/setup.bash && python3 /tools/make_fault_bag.py --fault $fault --out /out \$(ls -1 /in/*.bag | sort)" > "$WORK/$tag.rewrite.log" 2>&1
  RC=$?; tail -n 12 "$WORK/$tag.rewrite.log"
  if [ $RC -ne 0 ] || ! ls "$dst"/*.bag >/dev/null 2>&1; then
    say "$tag: bag rewrite failed (rc $RC)"; echo "$tag,\"$cfgs\",FAIL_REWRITE,0,rc$RC" >> "$SUM"; FAILS=$((FAILS+1)); rm -f "$dst"/*.bag; rmdir "$dst" 2>/dev/null; continue
  fi
  T1=$SECONDS
  ENVF="$WORK/$tag.seq.env"
  if [ $seq = MF ]; then : > "$ENVF"; else cat "$(template $seq)" > "$ENVF"; fi
  { echo "BAG_DIR=\"$dst\""; echo "OUT_DIR=$WORK/$tag"; echo "MIN_ROWS=1"; } >> "$ENVF"
  ( cd "$FV4" && SEQ_ENV="$ENVF" FRONT=genz RECORD_KF=1 REPEAT=1 PLAY_RATE=${RATE[$seq]} ./run_fusion_study.sh $cfgs ) > "$WORK/$tag.log" 2>&1
  RC=$?; grep -E "rows=|FAILED|STOP|abort|no log" "$WORK/$tag.log" | tail -n 6
  cp "$dst/fault_manifest.json" "$OUTD/" 2>/dev/null; compact "$OUTD"
  rm -f "$dst"/*.bag "$dst"/fault_manifest.json; rmdir "$dst" 2>/dev/null
  n_ok=$(ls "$OUTD"/switching_log_v2_*.csv 2>/dev/null | wc -l)
  M=$(( (SECONDS - T0) / 60 )); DET=$(grep -E "rows=" "$WORK/$tag.log" | tr '\n' ';' | tr ',' ' ')
  if [ "$n_ok" -ge "$ncfg" ]; then touch "$OUTD/DONE"; FAILS=0; echo "$tag,\"$cfgs\",OK,$M,\"$DET\"" >> "$SUM"; say "$tag: OK in $M min"
  else FAILS=$((FAILS+1)); echo "$tag,\"$cfgs\",FAIL_RUN rc$RC,$M,\"$DET\"" >> "$SUM"; say "$tag: run produced $n_ok of $ncfg logs (rc $RC), see $WORK/$tag.log"; fi
  EST[$seq]=$(( (SECONDS - T1) / ncfg )); [ "${EST[$seq]}" -lt 120 ] && EST[$seq]=120
done
say "finished after $(( (SECONDS - START) / 60 )) min"; pack
