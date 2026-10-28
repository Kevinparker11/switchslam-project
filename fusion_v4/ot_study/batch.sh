#!/usr/bin/env bash
# usage: ./batch.sh TAG "ENV SETTINGS"   -> runs the harness on all 12 logs, 2 at a time
H=/home/claude
tag=$1; cfg=$2
LOGS=(
 "MF1 $H/data_in4/switching_log_v2_F8_kf_run1.csv $H/data_in4/keyframes_F8_kf_run1.npz"
 "MF2 $H/data_in4/switching_log_v2_F8_kf_run2.csv $H/data_in4/keyframes_F8_kf_run2.npz"
 "MF3 $H/data_in4/switching_log_v2_F8_kf_run3.csv $H/data_in4/keyframes_F8_kf_run3.npz"
 "MF4 $H/data_in5/switching_log_v2_F8_kf_run4.csv $H/data_in5/keyframes_F8_kf_run4.npz"
 "MF5 $H/data_in5/switching_log_v2_F8_kf_run5.csv $H/data_in5/keyframes_F8_kf_run5.npz"
 "MF6 $H/data_in5/switching_log_v2_F8_kf_run6.csv $H/data_in5/keyframes_F8_kf_run6.npz"
 "LC1 $H/data_in7/switching_log_v2_F8_kf_run1.csv $H/data_kf/LC_keyframes_F8_kf_run1.npz"
 "LC2 $H/data_in7/switching_log_v2_F8_kf_run2.csv $H/data_kf/LC_keyframes_F8_kf_run2.npz"
 "LC3 $H/data_in7/switching_log_v2_F8_kf_run3.csv $H/data_kf/LC_keyframes_F8_kf_run3.npz"
 "C021 $H/data_in8/switching_log_v2_F8_kf_run1.csv $H/data_kf/C02_keyframes_F8_kf_run1.npz"
 "C022 $H/data_in8/switching_log_v2_F8_kf_run2.csv $H/data_kf/C02_keyframes_F8_kf_run2.npz"
 "C023 $H/data_in8/switching_log_v2_F8_kf_run3.csv $H/data_kf/C02_keyframes_F8_kf_run3.npz")
HERE=$(cd "$(dirname "$0")" && pwd)
xt() { case $1 in LC*) echo "EXTRINSIC_YAML=$HERE/corridor_extrinsics.yaml";; C02*) echo "EXTRINSIC_YAML=$HERE/corridor2_extrinsics.yaml";; *) echo "";; esac; }
ONLY=${ONLY:-}      # e.g. ONLY="LC C02": run only those sequences
run() { set -- $1; if [ -n "$ONLY" ]; then s=${1%%[0-9]*}; [ "${1:0:3}" = C02 ] && s=C02; case " $ONLY " in *" $s "*) ;; *) return;; esac; fi
        env $cfg $(xt $1) SAH_SYNC=1 RUN_TAG=$tag python3 node_harness.py $2 $3 out/$1 > out/$1/h_$tag.txt 2>&1; }
mkdir -p out; for l in "${LOGS[@]}"; do set -- $l; mkdir -p out/$1; done
i=0
for l in "${LOGS[@]}"; do run "$l" & i=$((i+1)); [ $((i % 2)) = 0 ] && wait; done; wait
