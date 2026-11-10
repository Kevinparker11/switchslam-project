#!/usr/bin/env bash
# About 15 min: F33 (F32 with the output rotation from VINS-Mono) on Multi Floor. docs/results/F33_F32_With_VINS_Rotation.md
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/f33_mf.sh > ~/f33.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f33_mf.zip}
echo "=== F33 queue $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=1 REPEAT=1 ONLY="MF" CFGS="F33" bash "$HERE/switchslam_exact_batch.sh"
echo "=== queue finished $(date)"
