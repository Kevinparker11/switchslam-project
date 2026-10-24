#!/bin/bash
# $1 = "name|cfg|keyframes|gt|extrinsics"
IFS='|' read n c kf gt ex <<< "$1"; ME=$(cd "$(dirname "$0")" && pwd)
[ "$ex" != "-" ] && export EXTRINSIC_YAML=$ex
cd /tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/clean4/fusion_v4 && timeout 2400 python3 run_backend.py --log $ME/bk/${n}_${c}.csv --kf $kf --gt $gt --models none,iso --odom-sigma 1.46,0.054 --calib-end 0 > $ME/bk/${n}_${c}.out 2>&1
