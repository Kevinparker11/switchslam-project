#!/usr/bin/env bash
# One more run (run 2) of each Switch-SLAM replica result that was far from the published number in its first run.  Nothing else.
#   Multi Floor    SW   first run 5.03 / 10.22   published 1.61 / 3.63   (SWI 1.51 was close: not repeated)
#   Long Corridor  SW   first run 12.58 / 23.53  published 2.42 / 5.09
#   Long Corridor  SWI  first run 13.81 / 24.78  published 2.42 / 5.09
# Purpose: is the miss repeatable (a property of the replica on our stack) or was the first run unlucky.  About 45 min.
# Run 1 is already in results_index.csv and is skipped; same settings, nothing changed.
# Detach:  cd ~/sw_replica/fusion_v4 && setsid nohup systemd-inhibit --what=sleep:idle bash batches/off_target_rerun.sh > ~/rerun.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); cd "$FV4" || exit 1
B=batches/switchslam_exact_batch.sh
Z=${ZIP:-$HOME/Downloads/for_claude_rerun.zip}
echo "=== off-target rerun $(date)  commit $(git -C "$FV4" rev-parse --short HEAD 2>/dev/null)"
ONLY="MF" CFGS="SW"     REPEAT=2 ZIP=$HOME/Downloads/for_claude_rerun_stage1.zip bash $B; echo "--- MF SW done $(date +%T)"
ONLY="LC" CFGS="SW SWI" REPEAT=2 ZIP=$Z bash $B;                                          echo "--- LC SW, SWI done $(date +%T)"
echo "RERUN_DONE $(date +%T)  zip: $Z"
