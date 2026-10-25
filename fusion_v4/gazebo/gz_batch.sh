#!/bin/bash
# Stage 3: run the fusion configurations live on a prepared Gazebo sequence (the nd variant) and keep the logs for exact replay.
#   ./gz_batch.sh construction        G20 x3 (settings as frozen on 24 Oct), then G22 x1 (C_T 1e-5, frozen 25 Oct); about 11 min each
# Run it detached:  setsid nohup systemd-inhibit --what=sleep:idle bash gz_batch.sh construction > ~/gz_batch_construction.log 2>&1 < /dev/null & disown
# Nothing is tuned here: both configurations come from run_fusion_study.sh unchanged. GenZ-LIO alone, G17, G19 and G22 for the other runs are
# obtained from the logs by exact replay (analysis/improve/universal), as for the office world.
set -u
WORLD=${1:-construction}
HERE=$(cd "$(dirname "$0")" && pwd); FV4=$(dirname "$HERE")
ENV=$HOME/runs_gz${WORLD}_nd/seq.env
[ -f "$ENV" ] || { echo "$ENV not found (run ./gz_prepare.sh $WORLD first)"; exit 1; }
for c in switchslam_gpu_v2 vinsmono_test; do docker start $c >/dev/null 2>&1; done
cd "$FV4" || exit 1
echo "##### gz${WORLD}_nd G20 x3   $(date +%T)"
SEQ_ENV=$ENV FRONT=genz RECORD_KF=1 REPEAT=3 ./run_fusion_study.sh G20
echo "##### gz${WORLD}_nd G22 x1   $(date +%T)"
SEQ_ENV=$ENV FRONT=genz RECORD_KF=1 REPEAT=1 ./run_fusion_study.sh G22
echo "##### done $(date +%T)"
