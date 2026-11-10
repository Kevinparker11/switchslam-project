#!/usr/bin/env bash
# F35 on every bag (about 3 h). docs/results/F35_All_Bags_Test.md
#   Multi Floor 2 runs (about 30 min), GEODE 3 runs (about 40 min), Long Corridor run 2 (run 1 exists, about 20 min),
#   Cave02 1 run (about 36 min), Corridor02 1 run (about 45 min).  Short bags first so a stopped batch still gives results.
# Tags already in results_index.csv are skipped, so a restart does not repeat finished runs.
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash fusion_v4/batches/f35_all.sh > ~/f35all.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f35_all.zip}
echo "=== F35 all bags $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=1 REPEAT=2 ONLY="MF"    CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=3 ONLY="GEODE" CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=2 REPEAT=1 ONLY="LC"    CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="CAVE"  CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="C02"   CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
# small copy for upload (no keyframe scans)
if [ -f "$ZIP" ]; then S="${ZIP%.zip}_small.zip"; cp "$ZIP" "$S" && zip -q -d "$S" '*keyframes*' && echo "small zip: $S ($(du -h "$S" | cut -f1))"; fi
echo "=== finished $(date)"
