#!/usr/bin/env bash
# The 4-hour campaign: bring the comparison with Switch-SLAM to the paper's protocol (three repeated runs per configuration) and
# measure the run-to-run spread of F24 on the sequences that matter.  Front end only, A-LOAM + VINS-Mono, no loop closure, frozen settings.
#   stage 1  Multi Floor   F24, SW, SWI  runs 1-3   (runs 1 exist; 6 new runs, about 1.8 h)   Switch-SLAM published 1.61 / 3.63
#   stage 2  Long Corridor SW, SWI       runs 1-3   (F24 already has 3; 4 new runs, about 0.9 h)  Switch-SLAM published 2.42 / 5.09
#   stage 3  Cave02        F24           runs 1-3   (run 1 exists; 2 new runs, about 1.2 h)       F8/F16 earlier 4.4, F24 run 1 7.55
# A tag already in results_index.csv is skipped, so the script can be restarted after an interruption and continues where it stopped.
# Needs the external drive with the bags, containers switchslam_gpu_v2 and vinsmono_test, the laptop on mains power.
# Detach:  cd ~/sw_replica/fusion_v4 && setsid nohup systemd-inhibit --what=sleep:idle bash batches/four_hour_campaign.sh > ~/camp4h.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); cd "$FV4" || exit 1
B=batches/switchslam_exact_batch.sh
ZIP_FINAL=${ZIP:-$HOME/Downloads/for_claude_4h_campaign.zip}
echo "=== 4 h campaign $(date)  commit $(git -C "$FV4" rev-parse --short HEAD 2>/dev/null)"
ONLY="MF"   CFGS="F24 SW SWI" REPEAT=3 ZIP=$HOME/Downloads/for_claude_4h_stage1.zip bash $B; echo "--- stage 1 done $(date +%T)"
ONLY="LC"   CFGS="SW SWI"     REPEAT=3 ZIP=$HOME/Downloads/for_claude_4h_stage2.zip bash $B; echo "--- stage 2 done $(date +%T)"
ONLY="CAVE" CFGS="F24"        REPEAT=3 ZIP=$ZIP_FINAL                              bash $B; echo "--- stage 3 done $(date +%T)"
echo "CAMPAIGN_DONE $(date +%T)  final zip (all sequences): $ZIP_FINAL"
