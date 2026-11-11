#!/usr/bin/env bash
# Short closed-loop screen: the first DUR seconds of Corridor02 and Cave02 (default 180 s, about 9 min per run at 0.5x including restarts, estimate).
# Why these: A-LOAM alone fails or drifts on both and Switch-SLAM published no value on either, so a variant can be screened on them without looking
# at Multi Floor or Long Corridor, which stay for the final three-run check (docs/protocols/SwitchSLAM_Exact_Replica.md section 18).
# Why a prefix and not a stretch from the middle: SWF needs a quiet IMU window at the start to find gravity.
# Window results live in <runs dir>/window<DUR>/ and are never mixed into the full-bag tables; ATE is over the window only, so compare variants
# with each other on the same window, not with the full-bag numbers.
#   CFGS="SW SWF" (default; add F24 for the project's own reference)   SEQS="C02 CAVE"   DUR=180   REPEAT=1
# Detach:  setsid nohup systemd-inhibit --what=sleep:idle bash batches/switchslam_window.sh > ~/sw_window.log 2>&1 < /dev/null & disown
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FV4=$(dirname "$HERE")
DUR=${DUR:-180}; SEQS=${SEQS:-"C02 CAVE"}; CFGS=${CFGS:-"SW SWF"}; REPEAT=${REPEAT:-1}
LOG=$HOME/sw_window.log; say() { echo "$*" | tee -a "$LOG"; }
cd "$FV4" || exit 1
say "=== window screen: first ${DUR}s of $SEQS, configs $CFGS, repeat $REPEAT  $(date)"
python3 test_imu_prop.py >/dev/null && python3 test_offline_imu_check.py >/dev/null || { say "unit tests failed - not starting"; exit 1; }
PLAY_DUR=$DUR ONLY="$SEQS" CFGS="$CFGS" REPEAT=$REPEAT ZIP=$HOME/Downloads/for_claude_SW_window.zip bash batches/switchslam_exact_batch.sh >> "$LOG" 2>&1
say "--- window results (ATE RMSE / max over the first ${DUR}s, m)"
for pair in C02:$HOME/runs_corridor2 CAVE:$HOME/runs_cave02_sw; do
  p=${pair%%:*}; d=$pair; d=${pair#*:}; w="$d/window$DUR"
  [ -f "$w/results_index.csv" ] && grep -E "_kf_run" "$w/results_index.csv" | awk -F, -v s=$p '{print s, $1, $(NF-2), $(NF-1)}' | tee -a "$LOG"
done
for g in "$HOME"/runs_corridor2/window$DUR/switching_log_v2_SWF_kf_run*.csv "$HOME"/runs_cave02_sw/window$DUR/switching_log_v2_SWF_kf_run*.csv; do [ -f "$g" ] && python3 - "$g" <<'PY' | tee -a "$LOG"
import sys, pandas as pd, numpy as np
L = pd.read_csv(sys.argv[1]); u = L["sw_imu"] == 1
first = L["time"].iloc[np.argmax(u.values)] - L["time"].iloc[0] if u.any() else float("nan")
print("%s: IMU guess in %.1f %% of %d scans (from +%.1f s); median |IMU - A-LOAM| %.3f deg, %.4f m; rule fired %.1f %%" % (sys.argv[1].split("/")[-1], 100 * u.mean(), len(L), first, L.loc[u, "sw_imu_rdeg"].median(), L.loc[u, "sw_imu_tdiff"].median(), 100 * (L["sw_degen"] == 1).mean()))
PY
done
say "WINDOW_DONE $(date +%T)   send ~/Downloads/for_claude_SW_window.zip is NOT made for window runs: send the window* folders of runs_corridor2 and runs_cave02_sw"
