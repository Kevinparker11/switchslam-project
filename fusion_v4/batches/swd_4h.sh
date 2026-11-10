#!/usr/bin/env bash
# About 3.6 h: Switch-SLAM with our detection (SWD) against the Switch-SLAM replica (SW), interleaved.
# docs/protocols/Switch_SLAM_With_Our_Detection_Protocol.md (rules written before the runs).
#   GEODE (0.5x)  SW run 1, SWD run 1, SW run 2, SWD run 2, SWD run 3     5 x about 13 min = about  65 min
#   Multi Floor   SWD run 1                                               1 x about 17 min = about  17 min
#   Cave02        SW run 1, SWD run 1, SWD run 2                          3 x about 36 min = about 108 min
#   Long Corridor SWD run 1                                               1 x about 25 min = about  25 min
# Tags already in results_index.csv are skipped.
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/swd_4h.sh > ~/swd4h.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_swd_4h.zip}
echo "=== SWD 4 h queue $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=1 REPEAT=1 ONLY="GEODE" CFGS="SW"  bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="GEODE" CFGS="SWD" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=2 REPEAT=1 ONLY="GEODE" CFGS="SW"  bash "$HERE/switchslam_exact_batch.sh"
RUN_START=2 REPEAT=1 ONLY="GEODE" CFGS="SWD" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=3 REPEAT=1 ONLY="GEODE" CFGS="SWD" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="MF"    CFGS="SWD" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="CAVE"  CFGS="SW"  bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=2 ONLY="CAVE"  CFGS="SWD" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="LC"    CFGS="SWD" bash "$HERE/switchslam_exact_batch.sh"
echo "=== queue finished $(date)"
