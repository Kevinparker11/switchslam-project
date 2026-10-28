#!/usr/bin/env bash
# round 2 stage B driver (restartable): VIO-trust variants V1, V1b, V2 on gmax, agm (finalists) and F20, smin (reported arms)
cd "$(dirname "$0")"
B="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1 ROT_CHECK=1"
declare -A R=([gmax]="$B OT_SRC=geom OT_MODE=gmax" [agm]="$B OT_SRC=geom OT_MODE=agm" [F20]="$B OT_SRC=geom OT_MODE=min" [smin]="$B OT_SRC=geom OT_MODE=smin")
declare -A P2=([gmax]="VIO_CHECK_REF=0.165 VIO_CHECK_FAST_REF=0.291" [agm]="VIO_CHECK_REF=0.165 VIO_CHECK_FAST_REF=0.291"
               [F20]="VIO_CHECK_REF=0.166 VIO_CHECK_FAST_REF=0.292" [smin]="VIO_CHECK_REF=0.165 VIO_CHECK_FAST_REF=0.291")
CHK="VIO_CHECK=1 VIO_CHECK_FAST=5 LIDAR_GUARD_T=2 LIDAR_GUARD_EX=4.325"
declare -A V=([V1]="$CHK VIO_CHECK_REF=0.157 VIO_CHECK_FAST_REF=0.277" [V1b]="$CHK VIO_CHECK_REF=0.157 VIO_CHECK_FAST_REF=0.277 VIO_CHECK_START=1")
declare -A C=([clean]="" [FL]="FAULT=1" [FV]="FAULT=1 FAULT_KIND=vio" [FS]="KF_THIN=0.25")
vcfg() { if [ "$2" = V2 ]; then echo "$CHK ${P2[$1]} VIO_CHECK_START=1 VIO_CHECK_PROJ=1"; else echo "${V[$2]}"; fi; }
for c in clean FV FL FS; do
  for r in gmax agm F20 smin; do for v in V1 V1b V2; do
    if [ $c = clean ]; then ./batch2.sh B_${r}_${v}_$c "${R[$r]} $(vcfg $r $v)"
    else ONLY="MF LC C02" ./batch2.sh B_${r}_${v}_$c "${R[$r]} $(vcfg $r $v) ${C[$c]}"; fi
    echo "done B_${r}_${v}_$c $(date +%T)"
  done; done
done
echo DRIVE_B_DONE
