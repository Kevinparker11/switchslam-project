#!/usr/bin/env bash
# corridors again with their own LiDAR-IMU extrinsics (the first pass used the Multi Floor extrinsic for LC and C02)
cd "$(dirname "$0")"
B="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9"
export ONLY="LC C02"
./batch.sh F8 "$B"
./batch.sh F16 "$B SAH=1"
./batch.sh F17 "$B SAH=1 ROT_CHECK=1"
for m in min gmean harm tonly agree2 hybrid max; do ./batch.sh OT_$m "$B SAH=1 OT_MODE=$m"; done
./batch.sh OTG_min "$B SAH=1 OT_SRC=geom OT_MODE=min"
./batch.sh OTG_max "$B SAH=1 OT_SRC=geom OT_MODE=max"
./batch.sh F20 "$B SAH=1 ROT_CHECK=1 OT_SRC=geom OT_MODE=min"
./batch.sh F16_fault "$B SAH=1 FAULT=1"
./batch.sh F20_fault "$B SAH=1 ROT_CHECK=1 OT_SRC=geom OT_MODE=min FAULT=1"
python3 summ.py F8 F16 F17 OT_min OT_gmean OT_harm OT_tonly OT_agree2 OT_hybrid OT_max OTG_min OTG_max F20 F16_fault F20_fault
echo FRONT_DONE
RUNS="LC1 LC2 LC3 C021 C022 C023" ./be_batch.sh F16
RUNS="LC1 LC2 LC3 C021 C022 C023" ./be_batch.sh F20
python3 be_summ.py F16 F20
echo CHAIN2_DONE
