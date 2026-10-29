#!/usr/bin/env bash
# G-stack replays through the real fusion_node_v2 callbacks.  ./batchg.sh TAG "ENV SETTINGS" ; ONLY="MF LC" narrows by sequence; NPAR workers
cd "$(dirname "$0")"
R=/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/clean4
S=/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad
tag=$1; cfg=$2; ONLY=${ONLY:-}; EXCL=${EXCL:-}
xt() { case $1 in LC) echo "EXTRINSIC_YAML=$R/configs/corridor/corridor_extrinsics.yaml";; C02) echo "EXTRINSIC_YAML=$R/configs/corridor2/corridor2_extrinsics.yaml";;
  CV) echo "EXTRINSIC_YAML=$R/configs/cave02/cave02_extrinsics.yaml";; GEO) echo "EXTRINSIC_YAML=$R/fusion_v4/geode/geode_extrinsics.yaml";;
  GZ) echo "EXTRINSIC_YAML=$S/gz20/gazebo_extrinsics.yaml";; *) echo "";; esac; }
run() { IFS='|' read -r name seq log kf gt ext <<< "$1"
  if [ -n "$ONLY" ]; then case " $ONLY " in *" $seq "*) ;; *) return;; esac; fi
  if [ -n "$EXCL" ]; then case " $EXCL " in *" $name "*) return;; esac; fi
  mkdir -p g/$name; [ -f g/$name/h_$tag.txt ] && grep -q "^rows" g/$name/h_$tag.txt && return
  env $cfg $(xt $seq) SAH_SYNC=1 KF_CACHE=$PWD/kfcache_g RUN_TAG=$tag python3 node_harness.py "$log" "$kf" g/$name > g/$name/h_$tag.txt 2>&1; }
N=${NPAR:-4}; i=0
# long GEODE logs first
while IFS= read -r l; do run "$l" & i=$((i+1)); [ $((i % N)) = 0 ] && wait; done < <(grep '^GEO' glogs.txt; grep -v '^GEO' glogs.txt); wait
echo "BATCHG_DONE $tag"
