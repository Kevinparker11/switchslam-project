#!/usr/bin/env bash
cd "$(dirname "$0")"
B="FUSION_MODE=fused C_T=5.6e-2 KAPPA_TH=1e9 SAH=1 ROT_CHECK=1 OT_SRC=geom OT_MODE=min VIO_CHECK=1 VIO_CHECK_FAST=5 LIDAR_GUARD_T=2 LIDAR_GUARD_EX=4.325 VIO_CHECK_REF=0.157 VIO_CHECK_FAST_REF=0.277 VIO_CHECK_START=1"
declare -A C=([clean]="" [FL]="FAULT=1" [FV]="FAULT=1 FAULT_KIND=vio" [FS]="KF_THIN=0.25")
./batch2.sh D_ct056_V1b_clean "$B"; SET=held ./batch2.sh D_ct056_V1b_clean "$B"
for c in FV FL FS; do ONLY="MF LC C02" ./batch2.sh D_ct056_V1b_$c "$B ${C[$c]}"; done
echo DRIVE_D_DONE
