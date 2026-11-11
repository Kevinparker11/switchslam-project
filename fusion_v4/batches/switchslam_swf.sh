#!/usr/bin/env bash
# SWF (Switch-SLAM replica with a LiDAR-IMU propagation as the LiDAR guess) on Multi Floor and Long Corridor, 0.5x replay.
#   REPEAT=1 (default): first look, one run per sequence, about 30 min (estimate: MF about 16 min, LC about 12 min).
#   REPEAT=3: the reproduction check of docs/protocols/SwitchSLAM_Exact_Replica.md sections 5 and 18, about 1.5 h.
# Pass rule (written before the first run, section 18): mean RMSE within +-50 % of the published value on BOTH sequences
# (Multi Floor 1.61, Long Corridor 2.42), three runs each.  Nothing is tuned on these sequences; a change after a failed check is a new
# variant with its own name and is reported next to this one.
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_swf.sh > ~/sw_swf.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE"); REPO=$(dirname "$FV4"); P=$REPO/patches/aloam_vins
LOG=$HOME/sw_swf.log; say() { echo "$*" | tee -a "$LOG"; }
REPEAT=${REPEAT:-1}
cd "$FV4" || exit 1
say "=== SWF run, REPEAT=$REPEAT $(date)  commit: $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)"
python3 test_imu_prop.py >/dev/null && python3 test_switch_slam.py >/dev/null && python3 test_switch_slam_node.py >/dev/null && python3 test_gyro_prior.py >/dev/null || { say "unit tests failed - not starting"; exit 1; }
for c in switchslam_gpu_v2 vinsmono_test; do docker inspect "$c" >/dev/null 2>&1 || { say "container $c does not exist"; exit 1; }; docker start "$c" >/dev/null 2>&1; done
f=/root/catkin_ws/src/A-LOAM/src/laserOdometry.cpp
if ! docker exec switchslam_gpu_v2 grep -q laser_hessian "$f" 2>/dev/null; then
  say "patching laserOdometry (/laser_hessian) ..."
  docker exec switchslam_gpu_v2 cp "$f" "$f.bak_before_patch_hessian"
  docker cp "$P/patch_hessian.py" switchslam_gpu_v2:/root/patch_hessian.py && docker exec switchslam_gpu_v2 python3 /root/patch_hessian.py 2>&1 | tee -a "$LOG"
  docker exec switchslam_gpu_v2 bash -c "source /opt/ros/noetic/setup.bash && cd /root/catkin_ws && catkin_make 2>&1 | tail -3" 2>&1 | tee -a "$LOG"
  docker exec switchslam_gpu_v2 grep -q laser_hessian "$f" || { say "marker still missing after patch"; exit 1; }
fi
ONLY="MF LC" CFGS="SWF" REPEAT=$REPEAT ZIP=$HOME/Downloads/for_claude_SWF.zip bash batches/switchslam_exact_batch.sh >> "$LOG" 2>&1
for g in "$HOME"/runs_v2/switching_log_v2_SWF_kf_run*.csv "$HOME"/runs_corridor/switching_log_v2_SWF_kf_run*.csv; do [ -f "$g" ] && python3 - "$g" <<'PY' | tee -a "$LOG"
import sys, pandas as pd, numpy as np
L = pd.read_csv(sys.argv[1])
u = L["sw_imu"] == 1
first = L["time"].iloc[np.argmax(u.values)] - L["time"].iloc[0] if u.any() else float("nan")
print("%s: IMU guess used in %.1f %% of %d scans (first at +%.1f s); median |IMU - A-LOAM| rotation %.3f deg, translation %.4f m per scan; "
      "|bg| %.4f rad/s, |ba| %.3f m/s2 at the end; median velocity %.2f m/s; rule fired on %.1f %% of scans"
      % (sys.argv[1].split("/")[-1], 100 * u.mean(), len(L), first, L.loc[u, "sw_imu_rdeg"].median(), L.loc[u, "sw_imu_tdiff"].median(),
         L["sw_imu_bg"].iloc[-1], L["sw_imu_ba"].iloc[-1], L["sw_imu_v"].median(), 100 * (L["sw_degen"] == 1).mean()))
PY
done
python3 repro_summary.py 2>&1 | tee "$HOME/sw_swf_summary.txt" | tee -a "$LOG"
say "SWF_DONE $(date +%T)   send ~/Downloads/for_claude_SWF.zip and ~/sw_swf_summary.txt"
