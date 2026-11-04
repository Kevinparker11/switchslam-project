#!/usr/bin/env bash
# SW and SWI once each on the Farm L-shape recording (Switch-SLAM Table II Farm: 0.38 / 1.10 m), same bag and settings as gz_batch_farm.sh.
# Needs the recording made by gz_record.sh / gz_prepare.sh (~/runs_gzfarm_nd/seq.env).  About 6 min per run (3 min of bag plus restart), estimate.
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_farm.sh > ~/sw_farm.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); cd "$FV4" || exit 1
ENV=$HOME/runs_gzfarm_nd/seq.env; LOG=$HOME/sw_farm.log; say() { echo "$*" | tee -a "$LOG"; }
[ -f "$ENV" ] || { say "$ENV not found (run gazebo/gz_prepare.sh farm first, see gazebo/gz_batch_farm.sh)"; exit 1; }
python3 test_switch_slam.py >/dev/null && python3 test_switch_slam_node.py >/dev/null && python3 test_gyro_prior.py >/dev/null || { say "unit tests failed"; exit 1; }
docker start switchslam_gpu_v2 vinsmono_test >/dev/null 2>&1
say "=== Farm SW SWI $(date) commit $(git rev-parse --short HEAD 2>/dev/null)"
SEQ_ENV=$ENV FRONT=aloam RECORD_KF=1 REPEAT=1 ./run_fusion_study.sh SW SWI >> "$LOG" 2>&1
D=$(grep -E '^OUT_DIR=' "$ENV" | head -1 | cut -d= -f2 | tr -d '"'); D=${D:-$HOME/runs_gzfarm_nd}
grep -E "^(F8|F5|SW|SWI|G20)_kf" "$D/results_index.csv" 2>/dev/null | cut -d, -f1,4,5 | tee -a "$LOG"
python3 - "$D" <<'PY' 2>&1 | tee -a "$LOG"
import glob, sys, pandas as pd
for f in sorted(glob.glob(sys.argv[1] + "/switching_log_v2_SW*_kf_run*.csv")):
    L = pd.read_csv(f); g = L["sw_gyro"].mean() if "sw_gyro" in L else float("nan")
    print("%s: rows %d, rule fired %.1f %%, gyro used %.0f %%, modes %s" % (f.split("/")[-1], len(L), 100 * L["sw_degen"].mean(), 100 * g, L["mode"].value_counts().to_dict()))
PY
Z=$HOME/Downloads/for_claude_SW_farm.zip; T=$(mktemp -d); cp "$D"/results_index.csv "$T/" 2>/dev/null
for f in "$D"/switching_log_v2_SW*_kf_run*.csv "$D"/ate_SW*_kf_run*.txt "$D"/node_SW*_kf_run*.out; do [ -f "$f" ] && cp "$f" "$T/"; done
mkdir -p "$(dirname "$Z")"; rm -f "$Z"; (cd "$T" && zip -q "$Z" *); rm -rf "$T"
say "FARM_DONE $(date +%T)  send $Z and the last 8 lines of ~/sw_farm.log"
