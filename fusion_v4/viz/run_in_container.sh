#!/usr/bin/env bash
# Runs INSIDE the RViz container (started by live_view.sh).  usage: run_in_container.sh [GT_FILE_IN_CONTAINER]
# Waits for a FRESH /switch_fused_pose message (a topic name left in the master by an earlier run is not enough), opens RViz,
# and when the ROS master restarts (new run: its /run_id changes) closes RViz and waits for the next run. Closing the window ends it.
GT=${1:-}
export ROS_IP=$(hostname -i); source /opt/ros/noetic/setup.bash
while true; do
  echo "[viz] waiting for a live run (a new /switch_fused_pose message) ..."
  if [ "${FORCE:-}" != 1 ]; then
    until timeout 6 rostopic echo -n1 /switch_fused_pose >/dev/null 2>&1; do
      echo "[viz] no pose message yet | $(timeout 4 rostopic info /switch_fused_pose 2>&1 | grep -A3 Publishers | tr '\n' ' ' | cut -c1-110) | /clock publishers: $(timeout 4 rostopic info /clock 2>&1 | grep -c '^ \* /')"
      sleep 2
    done
  fi
  RID=$(rosparam get /run_id 2>/dev/null); echo "[viz] run $RID detected, opening RViz"
  python3 /viz/fused_path.py & P1=$!
  P2=""; [ -n "$GT" ] && { python3 /viz/gt_path.py "$GT" & P2=$!; }
  rviz -d /viz/live.rviz & RV=$!
  WHY=closed
  while kill -0 $RV 2>/dev/null; do
    sleep 4
    [ "$(rosparam get /run_id 2>/dev/null)" = "$RID" ] || { WHY=restart; break; }
  done
  kill $P1 $P2 2>/dev/null; [ "$WHY" = restart ] && kill $RV 2>/dev/null; wait 2>/dev/null
  [ "$WHY" = closed ] && { echo "[viz] RViz closed, bye"; exit 0; }
  echo "[viz] the ROS master restarted (next run)"; sleep 3
done
