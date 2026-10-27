#!/bin/bash
# iG-LIO Phase B (specification: docs/results/IgLIO_Feasibility_Protocol.md, "Full test", item 2). About 4 h on the laptop.
#   Multi Floor I20 x3 (1.0x) | Long Corridor I0 x2 + I20 x2 (0.5x) | Cave02 I0 x1 + I20 x1 (0.5x), all live, RECORD_KF=1.
# Settings are frozen: the pre-declared 0.25 m change (IGLIO_SET) and the calibration result of Phase A3 read literally
# (c_T 1e-6, c_R 2e-5). Nothing is changed after seeing a score. A failed run is kept and reported. Restartable: finished tags are skipped.
# Run detached:  setsid nohup systemd-inhibit --what=sleep:idle --why=slam bash phaseB_batch.sh > ~/iglio_phaseB.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "$0")" && pwd); FV4=$(dirname "$HERE")
export FRONT=iglio RECORD_KF=1
export IGLIO_SET="scan_resolution=0.25,voxel_map_resolution=0.25,point_filter_num=3"
export IGLIO_C_T=1e-6 IGLIO_C_R=2e-5
BAGS_ROOT=${BAGS_ROOT:-"/media/$USER/One Touch1/laptop_bags"}
[ -d "$BAGS_ROOT" ] || { echo "bags drive not mounted: $BAGS_ROOT"; exit 1; }
first() { for f in "$@"; do [ -f "$f" ] && { echo "$f"; return; }; done; }
LC=$(first "$HOME/runs_corridor/seq.env"); C02=$(first "$HOME/runs_cave02/seq.env" "$HOME/runs_cave02_rate05_L/seq.env")
[ -n "$LC" ]  || { echo "no Long Corridor seq.env (~/runs_corridor/seq.env)"; exit 1; }
[ -n "$C02" ] || { echo "no Cave02 seq.env (~/runs_cave02/seq.env or ~/runs_cave02_rate05_L/seq.env)"; exit 1; }
for c in switchslam_gpu_v2 vinsmono_test; do docker start $c >/dev/null 2>&1; done
cd "$FV4" || exit 1
echo "repo $(git rev-parse --short HEAD)  IGLIO_SET=$IGLIO_SET  C_T=$IGLIO_C_T C_R=$IGLIO_C_R  LC=$LC  C02=$C02"
echo "##### Multi Floor I20 x3 (1.0x)   $(date +%T)";                  REPEAT=3 ./run_fusion_study.sh I20
echo "##### Long Corridor I0 x2 and I20 x2 (0.5x)   $(date +%T)";      SEQ_ENV=$LC  PLAY_RATE=0.5 REPEAT=2 ./run_fusion_study.sh I0 I20
echo "##### Cave02 I0 x1 and I20 x1 (0.5x)   $(date +%T)";             SEQ_ENV=$C02 PLAY_RATE=0.5 REPEAT=1 ./run_fusion_study.sh I0 I20
echo "##### done $(date +%T)"
