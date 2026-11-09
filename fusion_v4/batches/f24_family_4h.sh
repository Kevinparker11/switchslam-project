#!/usr/bin/env bash
# 4-hour queue (about 4 h) of F24-based versions only (every F24 addition kept): F26 and F27 repeats on Cave02 and GEODE, one F26 run on Corridor02.
#   Cave02    F26 runs 2-3, F27 runs 2-3      4 x about 36 min = about 144 min
#   GEODE     F26 runs 2-3, F27 runs 2-3      4 x about 13 min = about  52 min
#   Corridor02 F26 run 2                      1 x about 45 min = about  45 min
# Tags already in results_index.csv are skipped, so a restart does not repeat finished runs.
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/f24_family_4h.sh > ~/f24fam4h.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f24_family_4h.zip}
echo "=== F24-family 4 h queue $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=2 REPEAT=2 ONLY="CAVE"  CFGS="F26 F27" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=2 REPEAT=2 ONLY="GEODE" CFGS="F26 F27" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=2 REPEAT=1 ONLY="C02"   CFGS="F26"     bash "$HERE/switchslam_exact_batch.sh"
echo "=== queue finished $(date)"
