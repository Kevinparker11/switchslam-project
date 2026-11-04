#!/usr/bin/env bash
# Short on time: ONE run on Multi Floor, by default SW only (about 20 min).  Extras on request: WITH_V7=1 adds one V7 run (and the VINS-Mono
# Hessian patch it needs), WITH_SWM=1 adds one SWM run after the scan-to-map patch (SWM always last).
#   1. unit tests
#   2. patches, each only if its marker is missing (safe to repeat):
#        VINS-Mono container  : /vins_mono_hessian  (patch_vinsmono_hessian.py, needed by V7)         marker "vins_mono_hessian" in estimator.cpp
#        A-LOAM container     : /laser_hessian      (patch_hessian.py, needed by SW, V7)              marker "laser_hessian" in laserOdometry.cpp
#   3. SW, V7 on Multi Floor at 0.5x (about 16 min each, estimate)
#   4. A-LOAM scan-to-map Hessian patch (patch_mapping_hessian.py) + catkin_make, then SWM on Multi Floor (SWM LAST: the patch slows every later run)
#   5. table of the three results against Switch-SLAM Table II (1.61 / 3.63).  One run each: no verdict under the three-run rule of
#      docs/protocols/SwitchSLAM_Exact_Replica.md section 5, only a first look.
# RUN_CFGS=SWI runs the gyro variant instead of SW (RUN_CFGS="SW SWI" both).  Default: steps 1, 2 (laserOdometry patch only), 3 with SW only, 5.  About 20 min (estimate).
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_quick.sh > ~/sw_quick.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); REPO=$(dirname "$FV4"); P=$REPO/patches/aloam_vins
LOG=$HOME/sw_quick.log; say() { echo "$*" | tee -a "$LOG"; }
cd "$FV4" || exit 1
say "=== quick SW/V7/SWM run on Multi Floor $(date)  commit: $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)"
python3 test_switch_slam.py >/dev/null && python3 test_switch_slam_node.py >/dev/null && python3 test_switching_node_v7.py >/dev/null && python3 test_gyro_prior.py >/dev/null || { say "unit tests failed - not starting"; exit 1; }
for c in switchslam_gpu_v2 vinsmono_test; do docker inspect "$c" >/dev/null 2>&1 || { say "container $c does not exist"; exit 1; }; docker start "$c" >/dev/null 2>&1; done

patch_if_missing() {  # container file marker patch.py rebuild-dir
  local c=$1 f=$2 m=$3 py=$4 ws=$5
  if docker exec "$c" grep -q "$m" "$f" 2>/dev/null; then say "patch present: $c $(basename "$f") ($m)"; return 0; fi
  say "patching $c $(basename "$f") with $(basename "$py") ..."
  docker exec "$c" cp "$f" "$f.bak_before_$(basename "$py" .py)" || { say "cannot back up $f"; return 1; }
  docker cp "$py" "$c:/root/$(basename "$py")" && docker exec "$c" python3 "/root/$(basename "$py")" 2>&1 | tee -a "$LOG" || { say "patch script failed"; return 1; }
  docker exec "$c" bash -c "source /opt/ros/noetic/setup.bash && cd $ws && catkin_make 2>&1 | tail -3" 2>&1 | tee -a "$LOG"
  docker exec "$c" grep -q "$m" "$f" || { say "marker still missing after patch: $f"; return 1; }
}
if [ "${WITH_V7:-0}" = 1 ]; then patch_if_missing vinsmono_test /root/catkin_ws/src/VINS-Mono/vins_estimator/src/estimator.cpp vins_mono_hessian "$P/patch_vinsmono_hessian.py" /root/catkin_ws || exit 1; fi
patch_if_missing switchslam_gpu_v2 /root/catkin_ws/src/A-LOAM/src/laserOdometry.cpp laser_hessian "$P/patch_hessian.py" /root/catkin_ws || exit 1

CF="${RUN_CFGS:-SW}"; [ "${WITH_V7:-0}" = 1 ] && CF="SW V7"
say "--- one run each on Multi Floor: $CF"
ONLY=MF CFGS="$CF" REPEAT=1 ZIP=$HOME/Downloads/for_claude_SW_quick.zip bash batches/switchslam_exact_batch.sh >> "$LOG" 2>&1

if [ "${WITH_SWM:-0}" = 1 ]; then
  say "--- scan-to-map Hessian patch, then SWM"
  docker cp "$FV4/patch_mapping_hessian.py" switchslam_gpu_v2:/root/ && \
  docker exec switchslam_gpu_v2 bash -c "python3 /root/patch_mapping_hessian.py && source /opt/ros/noetic/setup.bash && cd /root/catkin_ws && catkin_make 2>&1 | tail -3" 2>&1 | tee -a "$LOG"
  docker exec switchslam_gpu_v2 grep -q '"/mapping_hessian"' /root/catkin_ws/src/A-LOAM/src/laserMapping.cpp || say "WARNING: mapping patch not found in laserMapping.cpp - SWM would get no Hessian"
  ONLY=MF CFGS="SWM" REPEAT=1 ZIP=$HOME/Downloads/for_claude_SW_quick_SWM.zip bash batches/switchslam_exact_batch.sh >> "$LOG" 2>&1
fi
for f in "$HOME"/runs_v2/switching_log_v2_SWI_kf_run*.csv; do [ -f "$f" ] && python3 - "$f" <<'PY' | tee -a "$LOG"
import sys, pandas as pd
L = pd.read_csv(sys.argv[1]); print("SWI gyro used in %.1f %% of %d scans (expect ~100; 0 = no IMU topic reached the node), median |gyro - odometry| rotation %.3f deg" % (100 * L["sw_gyro"].mean(), len(L), L["sw_gyro_deg"].abs().median()))
PY
done
say "--- result (one run each, ATE RMSE / max in m; Switch-SLAM Table II Multi Floor 1.61 / 3.63)"
python3 repro_summary.py 2>&1 | sed -n '1,/^Long Corridor/p' | grep -v "^Long Corridor" | tee "$HOME/sw_quick_summary.txt" | tee -a "$LOG"
say "QUICK_DONE $(date +%T)   send ~/Downloads/for_claude_SW_quick.zip, for_claude_SW_quick_SWM.zip and ~/sw_quick_summary.txt"
