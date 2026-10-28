#!/usr/bin/env bash
# round 2 stage A driver (restartable: finished runs are skipped)
cd "$(dirname "$0")"
B="FUSION_MODE=fused C_T=3e-2 KAPPA_TH=1e9 SAH=1"
declare -A R=(
 [F16]="$B" [F20]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=min"
 [gmin]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=gmin" [gmax]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=gmax"
 [psum]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=psum" [agm]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=agm"
 [ci]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=ci" [wprod]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=wprod"
 [wmean]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=wmean" [min3]="$B ROT_CHECK=1 OT_SRC=geom3 OT_MODE=min"
 [minS]="$B ROT_CHECK=1 OT_SRC=gschur OT_MODE=min" [smin]="$B ROT_CHECK=1 OT_SRC=geom OT_MODE=smin"
 [minRF]="$B ROT_CHECK=1 OT_SRC=georf OT_MODE=min" [sminRF]="$B ROT_CHECK=1 OT_SRC=georf OT_MODE=smin")
ORDER="F20 F16 gmin psum agm wprod wmean min3 minS ci gmax smin minRF sminRF"
declare -A C=([clean]="" [FL]="FAULT=1" [FV]="FAULT=1 FAULT_KIND=vio" [FS]="KF_THIN=0.25")
for r in $ORDER; do ./batch2.sh A_${r}_clean "${R[$r]}"; echo "done A_${r}_clean $(date +%T)"; done
for c in FV FS FL; do for r in $ORDER; do ONLY="MF LC C02" ./batch2.sh A_${r}_$c "${R[$r]} ${C[$c]}"; echo "done A_${r}_$c $(date +%T)"; done; done
echo DRIVE_A_DONE
