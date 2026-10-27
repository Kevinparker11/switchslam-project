#!/bin/bash
# Progress of the two-machine batch.   bash status.sh L|P
M=${1:?L or P}
echo "--- stages"; grep '#####\|smoke rows\|MISSING\|skipped\|signal\|FAILED' ~/batch_$M.log | tail -12
echo "--- last lines"; tail -3 ~/batch_$M.log | cut -c1-160
echo "--- results"; for d in ~/runs_geode_$M ~/runs_geode_${M}_genz ~/runs_corridor2_rate033_${M}_genz ~/runs_cave02_rate05_${M}_genz; do [ -f $d/results_index.csv ] && { echo "== $d"; cat $d/results_index.csv; }; done
echo "--- process"; pgrep -f two_machine_batch >/dev/null && echo "batch is running" || echo "batch is NOT running"
df -h ~ | tail -1
