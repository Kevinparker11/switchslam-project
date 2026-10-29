#!/usr/bin/env bash
cd "$(dirname "$0")"
G20="FUSION_MODE=fused C_T=3e-6 C_R=5e-6 KAPPA_TH=1e9 SAH=1 VIO_CHECK=1 VIO_SCALE_T=10 VIO_CHECK_FAST=5 LIDAR_GUARD_T=2"
declare -A M=([min]="OT_MODE=min" [smin]="OT_MODE=smin" [gmax]="OT_MODE=gmax" [agm]="OT_MODE=agm")
export NPAR=2
for r in min smin gmax agm; do ./batchg.sh Gc_${r}_clean "$G20 OT_SRC=geom ${M[$r]}"; done
FL="FAULT=1"; FV="FAULT=1 FAULT_KIND=vio"
ONLY="MF LC CV" ./batchg.sh Gbase_FL "$G20 $FL"; ONLY="MF LC CV" ./batchg.sh Gbase_FV "$G20 $FV"
for r in min smin gmax agm; do
  ONLY="MF LC CV" ./batchg.sh Gc_${r}_FL "$G20 OT_SRC=geom ${M[$r]} $FL"
  ONLY="MF LC CV" ./batchg.sh Gc_${r}_FV "$G20 OT_SRC=geom ${M[$r]} $FV"
done
echo DRIVEG_DONE
