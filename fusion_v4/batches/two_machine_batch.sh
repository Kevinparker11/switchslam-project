#!/bin/bash
# Two-machine batch of 22 Oct 2026 (plan: docs/planning/Two_Machine_Plan_2026-10-22.md).
# Run the SAME script on both machines; MACHINE only names the output folders and picks the control run.
#   MACHINE=L  laptop (Ryzen 5 5600H)      MACHINE=P  PC (i7-12700)
#   Work split (no run is duplicated across machines):
#     P (PC):     GEODE, all configurations (F16, G17, G0, F5)  -> stages "smoke geode"
#     L (laptop): replay-rate controls on the two held-out bags (Corridor02 0.33x, Cave02 0.5x) -> stages "smoke control"
#   STAGES="smoke geode control extra"   default depends on MACHINE (see above)
#   REPS        GEODE replicates of F16, G17, G0 (default 3; F5 once)
#   GEODE_DIR   local copy of the GEODE folder           (default ~/bags/GEODE)
#   CTRL_ROOT   folder holding Corridor02/ or Cave/      (default: L = the external drive, P = ~/bags)
# Detach it from the terminal:
#   MACHINE=P setsid nohup systemd-inhibit --what=sleep:idle --why=slam bash two_machine_batch.sh > ~/batch_P.stdout 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); REPO=$(dirname "$FV4")
M=${MACHINE:?set MACHINE=L (laptop) or MACHINE=P (PC)}
if [ "$M" = L ]; then STAGES=${STAGES:-"smoke control"}; else STAGES=${STAGES:-"smoke geode"}; fi
REPS=${REPS:-3}
if [ "$M" = L ]; then CTRL_ROOT=${CTRL_ROOT:-"/media/$USER/One Touch1/laptop_bags"}; else CTRL_ROOT=${CTRL_ROOT:-$HOME/bags}; fi
GEODE_DIR=${GEODE_DIR:-$CTRL_ROOT/GEODE}   # PC: ~/bags/GEODE (local copy); laptop: the external drive
LOG=$HOME/batch_$M.log
say() { echo "$*" | tee -a "$LOG"; }
trap 'say "!! batch received a signal at $(date) - stopped"; exit 143' HUP TERM INT

# make a seq.env for this machine from the original laptop's example (paths rewritten)
mk_env() {  # example-name outdir bagdir gtfile extrinsics-file
  mkdir -p "$2"
  sed -e "s|/home/kavinkumar|$HOME|g" -e "s|^BAG_DIR=.*|BAG_DIR=\"$3\"|" -e "s|^GT=.*|GT=\"$4\"|" \
      -e "s|^OUT_DIR=.*|OUT_DIR=$2|" -e "s|^export EXTRINSIC_YAML=.*|export EXTRINSIC_YAML=$2/$(basename "$5")|" \
      "$REPO/configs/seq_env_examples/$1.seq.env" > "$2/seq.env"
  cp "$5" "$2/"
}
need() { [ -e "$1" ] || { say "MISSING: $1"; return 1; }; }

{ echo "=== machine $M  $(date)"; echo "cpu: $(lscpu | sed -n 's/^Model name: *//p')  threads: $(nproc)  ram: $(free -g | awk '/Mem:/{print $2}') GB";
  echo "repo commit: $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)  stages: $STAGES"; docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -E 'switchslam_gpu_v2|vinsmono_test' ; } | tee -a "$LOG"

# ---- pre-flight (abort early, with a message) ----
for c in switchslam_gpu_v2 vinsmono_test; do docker inspect "$c" >/dev/null 2>&1 || { say "container $c does not exist - run tools/import_images.sh first"; exit 1; }; docker start "$c" >/dev/null 2>&1; done
python3 -c "import numpy, scipy, pandas" 2>/dev/null || { say "host python needs: pip3 install -r $REPO/requirements.txt"; exit 1; }
avail=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc 0-9); [ "$avail" -ge 15 ] || { say "only ${avail} GB free in $HOME (need >= 15)"; exit 1; }
cd "$FV4" || exit 1
GEODE_ENV=$HOME/runs_geode_$M/seq.env
case " $STAGES " in *" smoke "*|*" geode "*|*" extra "*)
  need "$GEODE_DIR/stairs_alpha.bag" && need "$GEODE_DIR/stairs_alpha.txt" || exit 1
  mk_env geode "$HOME/runs_geode_$M" "$GEODE_DIR" "$GEODE_DIR/stairs_alpha.txt" "$FV4/geode/geode_extrinsics.yaml"
  # install the GEODE files in the containers (a moved environment may lack them; the copies are byte-identical to the laptop's)
  docker exec vinsmono_test mkdir -p /root/vins_output_geode/pose_graph /root/thr
  docker cp "$FV4/geode/geode_config.yaml" vinsmono_test:/root/catkin_ws/src/VINS-Mono/config/geode_config.yaml || { say "could not install geode_config.yaml"; exit 1; }
  docker cp "$REPO/configs/geode/geode_aloam.launch" switchslam_gpu_v2:/root/geode_aloam.launch || { say "could not install geode_aloam.launch"; exit 1; }
  docker exec vinsmono_test test -f /root/catkin_ws/src/VINS-Mono/config/geode_config.yaml || { say "geode_config.yaml still missing in vinsmono_test"; exit 1; } ;; esac

step() { say "##### $*   $(date +%T)"; }
geode_run() {  # front rep config [rate]
  SEQ_ENV=$GEODE_ENV REPEAT=$2 RECORD_KF=1 PLAY_RATE=${4:-0.5} FRONT=$1 ./run_fusion_study.sh $3 >> "$LOG" 2>&1
}

for stage in $STAGES; do case $stage in
smoke)
  SM=$HOME/smoke_$M.txt; : > "$SM"; echo "machine $M  $(lscpu | sed -n 's/^Model name: *//p')  commit $(git -C "$REPO" rev-parse --short HEAD)" >> "$SM"
  step "SMOKE A-LOAM stack (60 s)"; SEQ_ENV=$GEODE_ENV SMOKE=1 SMOKE_SECS=60 FRONT=aloam ./run_fusion_study.sh F16 >> "$LOG" 2>&1; tail -12 "$LOG" >> "$SM"
  a=$(grep -o 'bag: [0-9]*' "$LOG" | tail -1 | tr -dc 0-9)
  step "SMOKE GenZ stack (60 s)";    SEQ_ENV=$GEODE_ENV SMOKE=1 SMOKE_SECS=60 FRONT=genz  ./run_fusion_study.sh G17 >> "$LOG" 2>&1; tail -12 "$LOG" >> "$SM"
  g=$(grep -o 'bag: [0-9]*' "$LOG" | tail -1 | tr -dc 0-9)
  say "smoke rows: A-LOAM stack ${a:-0}, GenZ stack ${g:-0} (a healthy 60 s smoke gives roughly 400-600 each; summary in $SM)"
  if ! grep -q "first VINS-Mono pose [0-9]" "$SM"; then say "SMOKE FAILED: VINS-Mono produced no pose (see ft_/vins_SMOKE_*.out in the runs folder)"; exit 1; fi
  if [ "${a:-0}" -lt 250 ] || [ "${g:-0}" -lt 250 ]; then say "SMOKE FAILED - stopping before the long runs. Send the last 60 lines of $LOG"; exit 1; fi ;;
geode)
  for rep in $(seq 1 $REPS); do
    step "GEODE pass $rep: F16 (master, A-LOAM)";  geode_run aloam $rep F16
    step "GEODE pass $rep: G17 (GenZ + fusion)";   geode_run genz  $rep G17
    step "GEODE pass $rep: G0 (GenZ alone)";       geode_run genz  $rep G0
    [ $rep = 1 ] && { step "GEODE pass 1: F5 (A-LOAM alone)"; geode_run aloam 1 F5; }
  done ;;
control)   # laptop: both held-out controls with G17 at the master's replay rates (one run each)
  D="$CTRL_ROOT/Corridor02"
  if need "$D/corridor02.bag" && need "$D/corridor02_gt.txt"; then
    O=$HOME/runs_corridor2_rate033_$M; mk_env corridor2 "$O" "$D" "$D/corridor02_gt.txt" "$REPO/configs/corridor2/corridor2_extrinsics.yaml"
    step "CONTROL Corridor02 G17 at 0.33x"; SEQ_ENV=$O/seq.env REPEAT=1 RECORD_KF=1 PLAY_RATE=0.33 FRONT=genz ./run_fusion_study.sh G17 >> "$LOG" 2>&1
  else say "Corridor02 control skipped (external drive not attached?)"; fi
  D="$CTRL_ROOT/Cave/cave02_bag"
  if need "$D/cave02.bag" && need "$CTRL_ROOT/Cave/cave02_gt.txt"; then
    O=$HOME/runs_cave02_rate05_$M; mk_env cave02 "$O" "$D" "$CTRL_ROOT/Cave/cave02_gt.txt" "$REPO/configs/cave02/cave02_extrinsics.yaml"
    step "CONTROL Cave02 G17 at 0.5x"; SEQ_ENV=$O/seq.env REPEAT=1 RECORD_KF=1 PLAY_RATE=0.5 FRONT=genz ./run_fusion_study.sh G17 >> "$LOG" 2>&1
  else say "Cave02 control skipped (external drive not attached?)"; fi ;;
extra)   # a third replicate of the three main configurations (only if time is left)
  step "EXTRA F16 run 3"; geode_run aloam 3 F16
  step "EXTRA G17 run 3"; geode_run genz  3 G17
  step "EXTRA G0 run 3";  geode_run genz  3 G0 ;;
*) say "unknown stage $stage" ;;
esac; done
step "ALL DONE"
