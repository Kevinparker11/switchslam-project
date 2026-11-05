#!/usr/bin/env bash
# F26 (F24 + Switch-SLAM's degeneracy rule for the scan-to-map guess), ONE run per sequence, same settings as F24, front end only.
# Order: the two bags we are trying to improve first, then the two regression checks.  About 1.6 h.
#   GEODE stairs (about 12 min at 0.5x)   F24 6.15 / 9.15 / 9.09 (3 runs), F25A 6.58 / 8.80
#   Cave02       (about 36 min at 0.5x)   F24 7.55 (1 run)
#   Multi Floor  (about 17 min)           F24 0.45 (1 run); published Switch-SLAM 1.61
#   Long Corridor (about 13 min)          F24 2.12 / 2.15 / 1.75; published 2.42
# Detach:  cd ~/sw_replica/fusion_v4 && setsid nohup systemd-inhibit --what=sleep:idle bash batches/f26_test.sh > ~/f26.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); cd "$FV4" || exit 1
B=batches/switchslam_exact_batch.sh; Z=${ZIP:-$HOME/Downloads/for_claude_f26.zip}
echo "=== F26 test $(date)  commit $(git -C "$FV4" rev-parse --short HEAD 2>/dev/null)"
for S in GEODE CAVE MF LC; do
  ONLY="$S" CFGS="F26" REPEAT=1 ZIP=$HOME/Downloads/for_claude_f26_$S.zip bash $B; echo "--- $S done $(date +%T)"
done
cp "$HOME/Downloads/for_claude_f26_LC.zip" "$Z" 2>/dev/null
echo "F26_DONE $(date +%T)  zip (all sequences): $Z"
