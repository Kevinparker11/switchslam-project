#!/usr/bin/env bash
cd "$(dirname "$0")"
B="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1 OT_SRC=geom"
./batch.sh OTG_min "$B OT_MODE=min"
./batch.sh OTG_max "$B OT_MODE=max"
echo STAGE2_DONE
