#!/usr/bin/env bash
cd "$(dirname "$0")"
B="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1"
./batch.sh F17 "$B ROT_CHECK=1"
for m in min gmean harm tonly agree2 hybrid max; do ./batch.sh OT_$m "$B OT_MODE=$m"; done
echo ALL_DONE
