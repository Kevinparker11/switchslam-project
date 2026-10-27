#!/bin/bash
# Farm L-shape test (protocol: docs/results/Farm_L_Shape_Test_Protocol.md): the same 80 m L route as the generation-1 Switch-SLAM-style replication.
#   ./gz_record.sh farm 1 ; ./gz_prepare.sh farm ; ./gz_batch_farm.sh        (about 3 min of bag per run; 9 live runs)
# Run it detached:  setsid nohup systemd-inhibit --what=sleep:idle bash gz_batch_farm.sh > ~/gz_batch_farm.log 2>&1 < /dev/null & disown
# Nothing is tuned: F8 (C_T 0.03, no gate) and F5 (A-LOAM alone) are the A-LOAM master settings, G20 the frozen RTS-Fusion settings.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); FV4=$(dirname "$HERE")
ENV=$HOME/runs_gzfarm_nd/seq.env
[ -f "$ENV" ] || { echo "$ENV not found (run ./gz_prepare.sh farm first)"; exit 1; }
for c in switchslam_gpu_v2 vinsmono_test; do docker start $c >/dev/null 2>&1; done
cd "$FV4" || exit 1
echo "##### gzfarm_nd F8 x3 and F5 x3 (A-LOAM stack)   $(date +%T)"
SEQ_ENV=$ENV FRONT=aloam RECORD_KF=1 REPEAT=3 ./run_fusion_study.sh F8 F5
echo "##### gzfarm_nd G20 x3 (GenZ-LIO stack)   $(date +%T)"
SEQ_ENV=$ENV FRONT=genz RECORD_KF=1 REPEAT=3 ./run_fusion_study.sh G20
echo "##### done $(date +%T)"
