#!/bin/bash
# Phase 2a of docs/results/R_Channel_Rotation_Aware_Test_Protocol.md: choose the healthy-state c_R of design B (config F17) on Multi Floor.
# Grid {1e-3, 3e-4, 1e-4, 3e-5, 1e-5} (c_R = 0 is F16 exactly while the check is open and needs no run), 3 live runs per value at 0.5x
# (the rate of the F16 Multi Floor reference, 0.640 +- 0.115, 6 runs), A-LOAM stack. Rule fixed in the protocol: the largest c_R whose 3-run mean
# ATE is within 0.1 m of 0.640 (the tie band; live run-to-run sd is 0.115, so 0.05 m would be below the noise). Nothing is changed after a score is seen.
# About 3 h. Restartable: finished tags are skipped. Run detached:
#   setsid nohup systemd-inhibit --what=sleep:idle --why=slam bash fusion_v4/rot_check/phase2a_batch.sh > ~/rot_phase2a.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "$0")" && pwd); FV4=$(dirname "$HERE")
export FRONT=aloam PLAY_RATE=0.5
BAGS_ROOT=${BAGS_ROOT:-"/media/$USER/One Touch1/laptop_bags"}
[ -d "$BAGS_ROOT" ] || { echo "bags drive not mounted: $BAGS_ROOT"; exit 1; }
for c in switchslam_gpu_v2 vinsmono_test; do docker start $c >/dev/null 2>&1; done
cd "$FV4" || exit 1
echo "repo $(git rev-parse --short HEAD 2>/dev/null)  grid 1e-3 3e-4 1e-4 3e-5 1e-5   $(date +%T)"
for c in 1e-3 3e-4 1e-4 3e-5 1e-5; do
  echo "##### F17 c_R=$c x3 (0.5x)   $(date +%T)"
  ROT_C_R_HEALTHY=$c OUT_DIR_OVERRIDE=$HOME/runs_f17_cR_$c REPEAT=3 ./run_fusion_study.sh F17
done
echo "##### summary (tag, rows, ATE, max)"
for c in 1e-3 3e-4 1e-4 3e-5 1e-5; do echo "--- c_R=$c"; cat $HOME/runs_f17_cR_$c/results_index.csv 2>/dev/null; done
echo "##### done $(date +%T)"
