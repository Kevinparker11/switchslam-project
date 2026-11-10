#!/usr/bin/env bash
# F35 (F26 with the guess decided by our own channels). docs/results/F35_Guess_With_Own_Channels.md
# One run per bag in ONLY (default Long Corridor, about 20 min each; Multi Floor "MF" about 15 min).
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/f35_test.sh > ~/f35.log 2>&1 < /dev/null & disown
# Another bag:  ONLY="MF" setsid nohup ... or ONLY="LC MF"
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f35.zip}
echo "=== F35 $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
for b in ${ONLY:-LC}; do
  RUN_START=1 REPEAT=1 ONLY="$b" CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
done
echo "=== finished $(date)"
