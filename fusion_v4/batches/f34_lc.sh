#!/usr/bin/env bash
# About 20 min: F34 on Long Corridor, one run. docs/results/F34_F33_With_Split_Eq15_And_SAH.md
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/f34_lc.sh > ~/f34lc.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f34_lc.zip}
echo "=== F34 Long Corridor $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=1 REPEAT=1 ONLY="LC" CFGS="F34" bash "$HERE/switchslam_exact_batch.sh"
echo "=== finished $(date)"
