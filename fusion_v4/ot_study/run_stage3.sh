#!/usr/bin/env bash
cd "$(dirname "$0")"
./batch.sh F16_fault "FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1 FAULT=1"
./batch.sh F20_fault "FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1 ROT_CHECK=1 OT_SRC=geom OT_MODE=min FAULT=1"
python3 summ.py F16 F20 F16_fault F20_fault
echo STAGE3_DONE
