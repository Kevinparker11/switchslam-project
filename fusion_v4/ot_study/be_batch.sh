#!/usr/bin/env bash
# usage: ./be_batch.sh TAG   -> loop back end (none, iso, ot) on the harness logs of TAG for all 12 runs, 2 at a time
cd "$(dirname "$0")"
FD=/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/clean4/fusion_v4
H=/home/claude; U=/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6
tag=$1
declare -A KF=( [MF1]=$H/data_in4/keyframes_F8_kf_run1.npz [MF2]=$H/data_in4/keyframes_F8_kf_run2.npz [MF3]=$H/data_in4/keyframes_F8_kf_run3.npz
  [MF4]=$H/data_in5/keyframes_F8_kf_run4.npz [MF5]=$H/data_in5/keyframes_F8_kf_run5.npz [MF6]=$H/data_in5/keyframes_F8_kf_run6.npz
  [LC1]=$H/data_kf/LC_keyframes_F8_kf_run1.npz [LC2]=$H/data_kf/LC_keyframes_F8_kf_run2.npz [LC3]=$H/data_kf/LC_keyframes_F8_kf_run3.npz
  [C021]=$H/data_kf/C02_keyframes_F8_kf_run1.npz [C022]=$H/data_kf/C02_keyframes_F8_kf_run2.npz [C023]=$H/data_kf/C02_keyframes_F8_kf_run3.npz )
gt() { case $1 in MF*) echo /mnt/user-data/uploads/ground_truth_path.csv;; LC*) echo $U/26b723ff-corridor01_gt.txt;; C02*) echo $U/db62c9b7-corridor02_gt.txt;; esac; }
one() { r=$1; (cd $FD && python3 run_backend.py --log $OLDPWD/out/$r/switching_log_v2_$tag.csv --kf ${KF[$r]} --gt $(gt $r) \
        --models none,iso,ot --odom-sigma 1.46,0.054 --rounds 1) > out/$r/be_$tag.txt 2>&1; }
i=0
RUNS=${RUNS:-"MF1 MF2 MF3 MF4 MF5 MF6 LC1 LC2 LC3 C021 C022 C023"}
for r in $RUNS; do one $r & i=$((i+1)); [ $((i % 2)) = 0 ] && wait; done; wait
echo BE_DONE $tag
