#!/bin/bash
# $1 = log name, $2 = config
A=$(cd "$(dirname "$0")" && pwd)
cd $A
[ -f bk/$1_$2.csv ] || python3 make_backend_log.py $1 $2 >/dev/null 2>&1
KF=$(python3 -c "exec(open('logs.py').read()); print([e for e in LOGS if e[0]=='$1'][0][3])")
GT=$(python3 -c "exec(open('logs.py').read()); print([e for e in LOGS if e[0]=='$1'][0][4])")
cd "$A/../../../fusion_v4"
python3 run_backend.py --log $A/bk/$1_$2.csv --kf $KF --gt $GT --models none,iso --odom-sigma 1.46,0.054 --calib-end 0 > $A/bk/$1_$2.out 2>&1
