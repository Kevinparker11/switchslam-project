#!/usr/bin/env bash
# 4-hour queue (about 3 h 50 min) for the lowest error on Cave02 and GEODE within the existing F16..F29 family.
# Reading rules: docs/protocols/Least_Error_4h_Protocol.md (written before any of these runs).
#   Cave02 (0.5x, about 36 min per run):  F16, F23, F28, F29, one run each      about 144 min
#   GEODE  (0.5x, about 13 min per run):  F16, F28, F29, two runs each          about  78 min
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/least_error_4h.sh > ~/least4h.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_least_error_4h.zip}
echo "=== least-error 4 h queue $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
ONLY="CAVE"  CFGS="F16 F23 F28 F29" REPEAT=1 bash "$HERE/switchslam_exact_batch.sh"
ONLY="GEODE" CFGS="F16 F28 F29"     REPEAT=2 bash "$HERE/switchslam_exact_batch.sh"
echo "=== queue finished $(date)"
