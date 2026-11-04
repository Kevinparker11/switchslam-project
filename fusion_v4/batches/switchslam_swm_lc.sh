#!/usr/bin/env bash
# One SWM run (SW with the scan-to-map Hessian, as in the paper's Eq. 8) on Long Corridor.
# Patches A-LOAM's laserMapping.cpp (patch_mapping_hessian.py, idempotent), rebuilds, runs once.  The patch slows every later run in the
# container: take any other timing-sensitive runs first.  About 25 min (estimate).
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_swm_lc.sh > ~/sw_swm.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); cd "$FV4" || exit 1
LOG=$HOME/sw_swm.log; say() { echo "$*" | tee -a "$LOG"; }
say "=== SWM on Long Corridor $(date) commit $(git rev-parse --short HEAD 2>/dev/null)"
python3 test_switch_slam.py >/dev/null && python3 test_switch_slam_node.py >/dev/null || { say "unit tests failed"; exit 1; }
docker start switchslam_gpu_v2 vinsmono_test >/dev/null 2>&1
docker cp patch_mapping_hessian.py switchslam_gpu_v2:/root/ || { say "docker cp failed"; exit 1; }
docker exec switchslam_gpu_v2 bash -c "python3 /root/patch_mapping_hessian.py && source /opt/ros/noetic/setup.bash && cd /root/catkin_ws && catkin_make 2>&1 | tail -3" 2>&1 | tee -a "$LOG"
docker exec switchslam_gpu_v2 grep -q '"/mapping_hessian"' /root/catkin_ws/src/A-LOAM/src/laserMapping.cpp || { say "mapping patch not in laserMapping.cpp - stop"; exit 1; }
ONLY=LC CFGS="SWM" REPEAT=1 ZIP=$HOME/Downloads/for_claude_SWM_LC.zip bash batches/switchslam_exact_batch.sh >> "$LOG" 2>&1
python3 - <<'PY' 2>&1 | tee -a "$LOG"
import glob, os, pandas as pd
for f in glob.glob(os.path.expanduser("~/runs_corridor/switching_log_v2_SWM_kf_run*.csv")):
    L = pd.read_csv(f); H = L[[c for c in L.columns if c.startswith("Hl_")]].notna().all(axis=1).mean()
    print("SWM: rows %d, mapping Hessian present in %.0f %%, rule fired in %.1f %% of scans, modes %s" % (len(L), 100 * H, 100 * L["sw_degen"].mean(), L["mode"].value_counts().to_dict()))
PY
grep -E "^SWM_kf" "$HOME/runs_corridor/results_index.csv" | cut -d, -f1,4,5 | tee -a "$LOG"
say "SWM_DONE $(date +%T)  send ~/Downloads/for_claude_SWM_LC.zip and the last 8 lines of ~/sw_swm.log"
