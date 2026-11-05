#!/usr/bin/env bash
# One command, two tests, one run each, front end only, settings frozen as F24 (docs/results/F26_Status_Guess.md).
#   CASE 1  F26 = F24 with Switch-SLAM's degeneracy rule choosing the scan-to-map guess (follows the paper).  GEODE, Cave02, Multi Floor, Long Corridor.
#   CASE 2  F27 = our original F24 (VINS motion in the guess) with one change: while the VINS motion is unusable, A-LOAM's own increment
#           replaces the "no motion" guess.  GEODE and Cave02 (the two bags that fail).
# Order (about 2.1 h): GEODE F26 + F27 (24 min), Cave02 F26 + F27 (72 min), Multi Floor F26 (17 min), Long Corridor F26 (13 min).
# References already recorded (F24): GEODE 6.15 / 9.15 / 9.09, Cave02 7.55, Multi Floor 0.45, Long Corridor 2.12 / 2.15 / 1.75.
# Detach:  cd ~/sw_replica/fusion_v4 && setsid nohup systemd-inhibit --what=sleep:idle bash batches/both_tests.sh > ~/both.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); cd "$FV4" || exit 1
B=batches/switchslam_exact_batch.sh; Z=${ZIP:-$HOME/Downloads/for_claude_both.zip}
echo "=== both tests $(date)  commit $(git -C "$FV4" rev-parse --short HEAD 2>/dev/null)"
ONLY="GEODE" CFGS="F26 F27" REPEAT=1 ZIP=$HOME/Downloads/for_claude_both_1.zip bash $B; echo "--- GEODE done $(date +%T)"
ONLY="CAVE"  CFGS="F26 F27" REPEAT=1 ZIP=$HOME/Downloads/for_claude_both_2.zip bash $B; echo "--- Cave02 done $(date +%T)"
ONLY="MF"    CFGS="F26"     REPEAT=1 ZIP=$HOME/Downloads/for_claude_both_3.zip bash $B; echo "--- Multi Floor done $(date +%T)"
ONLY="LC"    CFGS="F26"     REPEAT=1 ZIP=$Z                                   bash $B; echo "--- Long Corridor done $(date +%T)"
echo "BOTH_DONE $(date +%T)  zip (all sequences): $Z"
