#!/usr/bin/env bash
# Reproduction check of SW (rule fixed beforehand: docs/protocols/SwitchSLAM_Exact_Replica.md section 5) + sensitivity run SWM + a small first run.
#   1. unit tests, then a 70 s smoke run of SW and V7 on Multi Floor (checks the nodes start, VINS-Mono Hessian arrives, rows are written)
#   2. SW x3 on Multi Floor and Long Corridor  (the pre-registered check)
#   3. SWM x3 on the same two (patches A-LOAM's laserMapping with patch_mapping_hessian.py once; do this LAST: the patch adds an
#      Evaluate() per scan to every later run in the container, so F24/SW/V7 numbers must be taken before it)
#   4. verdict by repro_summary.py -> ~/sw_repro_summary.txt ; zip -> ~/Downloads/for_claude_SW_repro.zip
# Stages: STAGES="1 2 3 4" (default).  Smoke only: STAGES=1.   Skip SWM: STAGES="1 2 4".
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_reproduction.sh > ~/sw_repro.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE")
STAGES=${STAGES:-"1 2 3 4"}; LOG=$HOME/sw_repro.log
say() { echo "$*" | tee -a "$LOG"; }
has() { case " $STAGES " in *" $1 "*) return 0;; esac; return 1; }
cd "$FV4" || exit 1
say "=== SW reproduction $(date)  stages: $STAGES  commit: $(git -C "$FV4" rev-parse --short HEAD 2>/dev/null)"
python3 test_switch_slam.py >/dev/null && python3 test_switch_slam_node.py >/dev/null && python3 test_switching_node_v7.py >/dev/null && python3 test_gyro_prior.py >/dev/null || { say "unit tests failed - not starting"; exit 1; }
if has 1; then
  say "--- stage 1: smoke, 70 s of Multi Floor"
  SMOKE=1 SMOKE_SECS=70 ONLY=MF CFGS="SW V7" REPEAT=1 ZIP=$HOME/Downloads/for_claude_SW_smoke.zip bash batches/switchslam_exact_batch.sh 2>&1 | tee -a "$LOG" | grep -E "SMOKE|rows|modes|VINS|first|NO ROWS|WARNING|did not start|abort|FAILED|MISSING" 
  say "smoke done. Read the 'log rows' line above: a few hundred rows per config means the node works; 0 rows = stop (V7: is /vins_mono_hessian published?)."
fi
if has 2; then
  say "--- stage 2: SW x3 on Multi Floor and Long Corridor"
  ONLY="MF LC" CFGS="SW" REPEAT=3 ZIP=$HOME/Downloads/for_claude_SW_repro.zip bash batches/switchslam_exact_batch.sh >> "$LOG" 2>&1
fi
if has 3; then
  say "--- stage 3: patch A-LOAM for /mapping_hessian, then SWM x3"
  docker cp "$FV4/patch_mapping_hessian.py" switchslam_gpu_v2:/root/ && \
  docker exec switchslam_gpu_v2 bash -c "python3 /root/patch_mapping_hessian.py && source /opt/ros/noetic/setup.bash && cd /root/catkin_ws && catkin_make 2>&1 | tail -3" 2>&1 | tee -a "$LOG"
  ONLY="MF LC" CFGS="SWM" REPEAT=3 ZIP=$HOME/Downloads/for_claude_SW_repro_SWM.zip bash batches/switchslam_exact_batch.sh >> "$LOG" 2>&1
fi
if has 4; then
  python3 repro_summary.py 2>&1 | tee "$HOME/sw_repro_summary.txt" | tee -a "$LOG"
fi
say "REPRO_DONE $(date +%T)"
