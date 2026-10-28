#!/usr/bin/env bash
# V2 reference calibration on MF (projected checks), for translation rule $1 (OT_SRC $2 OT_MODE $3)
cd "$(dirname "$0")"
cfg="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1 ROT_CHECK=1 OT_SRC=$2 OT_MODE=$3 VIO_CHECK=1 VIO_CHECK_FAST=5 LIDAR_GUARD_T=2 VIO_CHECK_REF=1e9 VIO_CHECK_FAST_REF=1e9 LIDAR_GUARD_EX=1e9 VIO_DEBUG=1 VIO_CHECK_START=1 VIO_CHECK_PROJ=1"
ONLY="MF" ./batch2.sh CAL_V2_$1 "$cfg"
python3 - "$1" <<'PY'
import sys, pandas as pd
rs, rf, n = [], [], []
for i in range(1, 7):
    L = pd.read_csv("out/MF%d/switching_log_v2_CAL_V2_%s.csv" % (i, sys.argv[1])); L = L[pd.to_numeric(L["time"], errors="coerce").notna()]
    a, b = L["vio_r_slow"].astype(float), L["vio_r_fast"].astype(float)
    rs.append(a.max()); rf.append(b.max()); n.append(int(a.notna().sum()))
    print("MF%d slow max %.3f fast max %.3f rows judged %d" % (i, a.max(), b.max(), a.notna().sum()))
print("REF_V2 %s slow %.3f fast %.3f" % (sys.argv[1], max(rs), max(rf)))
PY
