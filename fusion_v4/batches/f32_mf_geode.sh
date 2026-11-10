#!/usr/bin/env bash
# About 47 min: F30 on Multi Floor, F32 on Multi Floor and GEODE. docs/results/F32_F30_With_F24_VINS_Checks.md
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/f32_mf_geode.sh > ~/f32.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f32.zip}
echo "=== F30/F32 queue $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=1 REPEAT=1 ONLY="MF"    CFGS="F30" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="MF"    CFGS="F32" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="GEODE" CFGS="F32" bash "$HERE/switchslam_exact_batch.sh"
echo "=== queue finished $(date)"
