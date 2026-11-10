#!/usr/bin/env bash
# One run each of F24 (final system) and SW (Switch-SLAM as published, switch_slam_node.py) on the sequences where Switch-SLAM has no
# published number (Corridor02, Cave02, GEODE stairs) and on the two with published numbers (Multi Floor, Long Corridor) for the
# reproduction check (Switch-SLAM Table II: Multi Floor 1.61 / 3.63, Long Corridor 2.42 / 5.09; RMSE / max, m).
# Front end only (the paper's Table II used no loop closure).  Same A-LOAM, VINS-Mono, extrinsics, replay rates and scorer for both.
#   ONLY="C02 CAVE GEODE MF LC"   sequences, in this order (default).  CFGS="F24 SW"   configurations per sequence.
#   CFGS="F24 SW V7" adds the generation-1 node (switching_node_v7.py; needs /vins_mono_hessian in the VINS-Mono container).
#   RATE_GEODE / RATE_CAVE = replay rate (default 0.5); SUFFIX=_r025 puts that sequence's runs in a separate folder (runs_geode_sw_r025).
#   REPEAT=1 (default: once each, as planned); REPEAT=3 gives the paper's "average of three repeated tests".
# Needs: python3 test_switch_slam.py passing, containers switchslam_gpu_v2 and vinsmono_test, the external drive for the bags.
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_exact_batch.sh > ~/sw_batch.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); REPO=$(dirname "$FV4")
ONLY=${ONLY:-"C02 CAVE GEODE MF LC"}; CFGS=${CFGS:-"F24 SW"}; REPEAT=${REPEAT:-1}
ROOT=${CTRL_ROOT:-"/media/$USER/One Touch1/laptop_bags"}
LOG=$HOME/sw_batch.log
say() { echo "$*" | tee -a "$LOG"; }
trap 'say "!! batch received a signal at $(date) - stopped"; exit 143' HUP TERM INT
cd "$FV4" || exit 1
want() { case " $ONLY " in *" $1 "*) return 0;; esac; return 1; }
need() { [ -e "$1" ] || { say "MISSING: $1"; return 1; }; }
mk_env() {  # example-name outdir bagdir gtfile extrinsics-file
  mkdir -p "$2"
  sed -e "s|/home/kavinkumar|$HOME|g" -e "s|^BAG_DIR=.*|BAG_DIR=\"$3\"|" -e "s|^GT=.*|GT=\"$4\"|" \
      -e "s|^OUT_DIR=.*|OUT_DIR=$2|" -e "s|^export EXTRINSIC_YAML=.*|export EXTRINSIC_YAML=$2/$(basename "$5")|" \
      "$REPO/configs/seq_env_examples/$1.seq.env" > "$2/seq.env"
  cp "$5" "$2/"
}
say "=== Switch-SLAM exact replica batch $(date)  sequences: $ONLY  configs: $CFGS  repeat: $REPEAT  commit: $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)"
python3 test_switch_slam.py > /dev/null && python3 test_switch_slam_node.py > /dev/null && python3 test_switching_node_v7.py >/dev/null && python3 test_gyro_prior.py > /dev/null && python3 test_f25.py > /dev/null || { say "unit tests failed - not starting"; exit 1; }
for c in switchslam_gpu_v2 vinsmono_test; do docker inspect "$c" >/dev/null 2>&1 || { say "container $c does not exist"; exit 1; }; docker start "$c" >/dev/null 2>&1; done
grep -q "\[V7\]" run_fusion_study.sh || { say "run_fusion_study.sh has no V7 config"; exit 1; }
grep -q "\[F26\]" run_fusion_study.sh || { say "run_fusion_study.sh has no F26 config"; exit 1; }
grep -q "\[SW\]" run_fusion_study.sh || { say "run_fusion_study.sh has no SW config"; exit 1; }

# run <label> <rate> <seq.env or ""> [extra env words]
run() {
  local label=$1 rate=$2 senv=$3; shift 3
  for cfg in $CFGS; do
    say "##### $label  $cfg  rate ${rate}x  $(date +%T)"
    env "$@" ${senv:+SEQ_ENV=$senv} PLAY_RATE=$rate REPEAT=$REPEAT RECORD_KF=1 FRONT=aloam ./run_fusion_study.sh $cfg >> "$LOG" 2>&1
  done
}

if want C02; then
  run Corridor02 0.33 "$HOME/runs_corridor2/seq.env"
fi
if want CAVE; then
  D="$ROOT/Cave/cave02_bag"
  if need "$D/cave02.bag" && need "$ROOT/Cave/cave02_gt.txt"; then
    O=$HOME/runs_cave02_sw${SUFFIX:-}; mk_env cave02 "$O" "$D" "$ROOT/Cave/cave02_gt.txt" "$REPO/configs/cave02/cave02_extrinsics.yaml"
    run Cave02 ${RATE_CAVE:-0.5} "$O/seq.env"
  else say "Cave02 skipped (external drive not attached?)"; fi
fi
if want GEODE; then
  G="${GEODE_DIR:-$ROOT/GEODE}"
  if need "$G/stairs_alpha.bag" && need "$G/stairs_alpha.txt"; then
    O=$HOME/runs_geode_sw${SUFFIX:-}; mk_env geode "$O" "$G" "$G/stairs_alpha.txt" "$FV4/geode/geode_extrinsics.yaml"
    docker exec vinsmono_test mkdir -p /root/vins_output_geode/pose_graph /root/thr
    docker cp "$FV4/geode/geode_config.yaml" vinsmono_test:/root/catkin_ws/src/VINS-Mono/config/geode_config.yaml
    docker cp "$REPO/configs/geode/geode_aloam.launch" switchslam_gpu_v2:/root/geode_aloam.launch
    run "GEODE stairs" ${RATE_GEODE:-0.5} "$O/seq.env"
  else say "GEODE skipped (bag not found in $G)"; fi
fi
if want MF; then
  MFDIR=""
  for d in multifloor MultiFloor Multi_Floor multi_floor RosBag; do [ -d "$ROOT/$d" ] && ls "$ROOT/$d"/*.bag >/dev/null 2>&1 && { MFDIR="$ROOT/$d"; break; }; done
  if [ -n "$MFDIR" ]; then run "Multi Floor" 0.5 "" BAG_DIR_OVERRIDE="$MFDIR"; else say "Multi Floor skipped (no bag folder under $ROOT)"; fi
fi
if want LC; then
  if ls "$ROOT/Long_Corridor_Rosbag"/*.bag >/dev/null 2>&1; then
    run "Long Corridor" 0.5 "$HOME/runs_corridor/seq.env" BAG_DIR_OVERRIDE="$ROOT/Long_Corridor_Rosbag"
  else say "Long Corridor skipped (no .bag in $ROOT/Long_Corridor_Rosbag)"; fi
fi

# collect
Z=${ZIP:-$HOME/Downloads/for_claude_SW_batch.zip}; T=$(mktemp -d)
for pair in C02:$HOME/runs_corridor2 CAVE:$HOME/runs_cave02_sw${SUFFIX:-} GEODE:$HOME/runs_geode_sw${SUFFIX:-} MF:$HOME/runs_v2 LC:$HOME/runs_corridor; do
  p=${pair%%:*}; d=${pair#*:}
  cp "$d/results_index.csv" "$T/${p}_results_index.csv" 2>/dev/null; cp "$d/failed_runs.csv" "$T/${p}_failed_runs.csv" 2>/dev/null
  for f in "$d"/switching_log_v2_{F24,F25A,F26,F27,F28,F29,F30,F31,SW,SWD,SWDRT,SWI,SWM,SW1,V7}_kf_run*.csv "$d"/ate_{F24,F25A,F26,F27,F28,F29,F30,F31,SW,SWD,SWDRT,SWI,SWM,SW1,V7}_kf_run*.txt "$d"/node_{F24,F25A,F26,F27,F28,F29,F30,F31,SW,SWD,SWDRT,SWI,SWM,SW1,V7}_kf_run*.out "$d"/keyframes_{F24,F25A,F26,F27,F28,F29,F30,F31,SW,SWD,SWDRT,SWI,SWM,SW1,V7}_kf_run*.npz; do
    [ -f "$f" ] && cp "$f" "$T/${p}_$(basename "$f")"
  done
done
mkdir -p "$(dirname "$Z")"; rm -f "$Z"; (cd "$T" && zip -q "$Z" *) && say "zip: $Z ($(du -h "$Z" | cut -f1))"; rm -rf "$T"
say "=== results (ATE RMSE / max, m)"
for pair in C02:$HOME/runs_corridor2 CAVE:$HOME/runs_cave02_sw${SUFFIX:-} GEODE:$HOME/runs_geode_sw${SUFFIX:-} MF:$HOME/runs_v2 LC:$HOME/runs_corridor; do
  p=${pair%%:*}; d=${pair#*:}
  grep -E "^(F24|F25A|F26|F27|F28|F29|F30|F31|SW|SWD|SWDRT|SWI|SWM|SW1|V7)_kf_run" "$d/results_index.csv" 2>/dev/null | awk -F, -v s=$p '{print s, $1, $(NF-2), $(NF-1)}' | tee -a "$LOG"
done
say "ALL_DONE $(date +%T)"
