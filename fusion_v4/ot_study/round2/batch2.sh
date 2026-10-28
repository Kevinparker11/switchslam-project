#!/usr/bin/env bash
# round 2: ./batch2.sh TAG "ENV SETTINGS"  (SET=dev: MF LC C02 GEO [default]; SET=held: FARM only; ONLY="MF LC" narrows dev)
H=/home/claude; S=/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad
tag=$1; cfg=$2; SET=${SET:-dev}
DEV=(
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
 "C023 $H/data_in8/switching_log_v2_F8_kf_run3.csv $H/data_kf/C02_keyframes_F8_kf_run3.npz"
 "GEO1 $S/geo2/runs_geode_P/switching_log_v2_F16_kf_run1.csv $S/geo2/runs_geode_P/keyframes_F16_kf_run1.npz"
 "GEO2 $S/geo2/runs_geode_P/switching_log_v2_F16_kf_run2.csv $S/geo2/runs_geode_P/keyframes_F16_kf_run2.npz"
 "GEO3 $S/geo2/runs_geode_P/switching_log_v2_F5_kf_run1.csv $S/geo2/runs_geode_P/keyframes_F5_kf_run1.npz")
HELD=(
 "FARM1 $S/farm_f8f5/runs_gzfarm_nd/switching_log_v2_F8_kf_run1.csv $S/farm_f8f5/runs_gzfarm_nd/keyframes_F8_kf_run1.npz"
 "FARM2 $S/farm_f8f5/runs_gzfarm_nd/switching_log_v2_F5_kf_run1.csv $S/farm_f8f5/runs_gzfarm_nd/keyframes_F5_kf_run1.npz")
if [ "$SET" = held ]; then LOGS=("${HELD[@]}"); else LOGS=("${DEV[@]}"); fi
HERE=$(cd "$(dirname "$0")" && pwd)
xt() { case $1 in LC*) echo "EXTRINSIC_YAML=$HERE/corridor_extrinsics.yaml";; C02*) echo "EXTRINSIC_YAML=$HERE/corridor2_extrinsics.yaml";;
                    GEO*) echo "EXTRINSIC_YAML=$HERE/geode_extrinsics.yaml";; FARM*) echo "EXTRINSIC_YAML=$HERE/farm_extrinsics.yaml";; *) echo "";; esac; }
seq_of() { case $1 in C02*) echo C02;; *) echo ${1%%[0-9]*};; esac; }
ONLY=${ONLY:-}
run() { set -- $1; if [ -n "$ONLY" ]; then case " $ONLY " in *" $(seq_of $1) "*) ;; *) return;; esac; fi
        [ -f out/$1/h_$tag.txt ] && grep -q "^rows" out/$1/h_$tag.txt && return
        env $cfg $(xt $1) SAH_SYNC=1 KF_CACHE=$HERE/kfcache RUN_TAG=$tag python3 node_harness.py $2 $3 out/$1 > out/$1/h_$tag.txt 2>&1; }
mkdir -p out; for l in "${LOGS[@]}"; do set -- $l; mkdir -p out/$1; done
# longest logs first so the two workers finish together
ORDER=(); for l in "${LOGS[@]}"; do case $l in C02*|GEO*) ORDER=("$l" "${ORDER[@]}");; *) ORDER+=("$l");; esac; done
N=${NPAR:-2}; i=0
for l in "${ORDER[@]}"; do run "$l" & i=$((i+1)); [ $((i % N)) = 0 ] && wait; done; wait
