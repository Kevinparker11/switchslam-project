#!/usr/bin/env bash
# About 2.7 h: F30 (LiDAR primary, F26 status guess). docs/results/F30_LiDAR_Primary_Status_Guess.md
#   GEODE 3 runs (3 x 13 min), Cave02 1 run (36 min), Multi Floor 1 (17 min), Long Corridor 1 (about 25 min), Corridor02 1 (45 min)
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/f30_test.sh > ~/f30.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f30.zip}
echo "=== F30 queue $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=1 REPEAT=3 ONLY="GEODE" CFGS="F30" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="MF"    CFGS="F30" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="CAVE"  CFGS="F30" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="LC"    CFGS="F30" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="C02"   CFGS="F30" bash "$HERE/switchslam_exact_batch.sh"
echo "=== queue finished $(date)"
