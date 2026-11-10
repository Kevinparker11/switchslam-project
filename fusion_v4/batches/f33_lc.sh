#!/usr/bin/env bash
# About 20 min: F33 on Long Corridor, one run. docs/results/F33_F32_With_VINS_Rotation.md
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/f33_lc.sh > ~/f33lc.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f33_lc.zip}
echo "=== F33 Long Corridor $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=1 REPEAT=1 ONLY="LC" CFGS="F33" bash "$HERE/switchslam_exact_batch.sh"
echo "=== finished $(date)"
