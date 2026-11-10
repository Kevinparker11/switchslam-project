#!/usr/bin/env bash
# F35 on Multi Floor (2 runs), Long Corridor (run 2; run 1 exists) and Corridor02 (1 run): about 95 min.
# Same rules as docs/results/F35_All_Bags_Test.md (this is the first part of f35_all.sh, without Cave02 and GEODE).
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash fusion_v4/batches/f35_mf_lc_c02.sh > ~/f35_3bags.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export ZIP=${ZIP:-$HOME/Downloads/for_claude_f35_3bags.zip}
echo "=== F35 MF + LC + C02 $(date)  commit: $(git -C "$HERE" rev-parse --short HEAD 2>/dev/null)"
RUN_START=1 REPEAT=2 ONLY="MF"  CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=2 REPEAT=1 ONLY="LC"  CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
RUN_START=1 REPEAT=1 ONLY="C02" CFGS="F35" bash "$HERE/switchslam_exact_batch.sh"
if [ -f "$ZIP" ]; then S="${ZIP%.zip}_small.zip"; cp "$ZIP" "$S" && zip -q -d "$S" '*keyframes*' && echo "small zip: $S ($(du -h "$S" | cut -f1))"; fi
echo "=== finished $(date)"
