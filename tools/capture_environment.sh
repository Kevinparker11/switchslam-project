#!/bin/bash
# Record everything needed to rebuild the software environment on another PC.
# Run on the machine that works (the laptop with the two containers). Writes ONE text file; nothing is modified.
#   bash tools/capture_environment.sh            -> ~/switchslam_environment.txt
# Container names default to the ones used in run_fusion_study.sh.
GPU_C=${GPU_C:-switchslam_gpu_v2}; VINS_C=${VINS_C:-vinsmono_test}
OUT=${1:-$HOME/switchslam_environment.txt}
{
echo "# SwitchSLAM environment capture  $(date -Is)"
echo; echo "## host"; uname -a; lsb_release -a 2>/dev/null; python3 --version
python3 - <<'PY' 2>&1
import importlib
for m in ("numpy","scipy","pandas","sklearn","matplotlib","yaml","gtsam","rosbag"):
    try:
        mod = importlib.import_module(m); print("%-10s %s" % (m, getattr(mod, "__version__", "installed")))
    except Exception as e:
        print("%-10s MISSING (%s)" % (m, type(e).__name__))
PY
echo; echo "## docker"; docker version --format 'client {{.Client.Version}} server {{.Server.Version}}' 2>&1
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
echo; docker images --digests --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}'
echo; echo "## network"; docker network ls; docker network inspect vins_bridge 2>&1 | head -40
echo; echo "## nvidia"; nvidia-smi --query-gpu=name,driver_version --format=csv 2>&1 | head -3
for C in $GPU_C $VINS_C; do
  echo; echo "################ container $C"
  docker inspect "$C" --format 'image={{.Config.Image}}  cmd={{.Config.Cmd}}  entrypoint={{.Config.Entrypoint}}  net={{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>&1
  echo "-- mounts/env:"; docker inspect "$C" --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}{{range .Config.Env}}{{.}}{{"\n"}}{{end}}' 2>&1
  echo "-- history (how the image was built):"; docker history --no-trunc --format '{{.CreatedBy}}' "$(docker inspect "$C" --format '{{.Image}}')" 2>&1 | head -60
  docker start "$C" >/dev/null 2>&1
  docker exec "$C" bash -c '
    echo "-- os:"; . /etc/os-release; echo $PRETTY_NAME
    for s in /opt/ros/*/setup.bash; do . $s; echo "ros: $ROS_DISTRO"; done
    echo "-- tools:"; gcc --version | head -1; cmake --version | head -1; python3 --version; python --version 2>&1
    echo "-- workspaces:"; ls -d /root/*_ws /root/catkin_ws /root/genz_ws 2>/dev/null
    echo "-- git revisions of every source repo under /root:"
    for g in $(find /root -maxdepth 5 -name .git -type d 2>/dev/null); do d=$(dirname $g); echo "$d  $(git -C $d rev-parse --short HEAD 2>/dev/null)  $(git -C $d remote get-url origin 2>/dev/null)  dirty=$(git -C $d status --porcelain 2>/dev/null | wc -l)"; done
    echo "-- ros packages we depend on:"; for p in aloam_velodyne vins_estimator feature_tracker velodyne_pointcloud genz_lio compressed_image_transport; do echo "$p: $(rospack find $p 2>&1 | tail -1)"; done
    echo "-- libs:"; dpkg -l 2>/dev/null | grep -E "libceres|libpcl-dev|libeigen3-dev|libopencv-dev|libgoogle-glog|ros-[a-z]+-(pcl|velodyne|cv-bridge|image-transport|compressed)" | awk "{print \$2, \$3}"
    ls /usr/local/include/eigen3 >/dev/null 2>&1 && echo "eigen in /usr/local: $(grep -h "define EIGEN_.*_VERSION" /usr/local/include/eigen3/Eigen/src/Core/util/Macros.h | awk "{print \$3}" | head -3 | tr "\n" ".")"
    echo "-- /root and /root/thr:"; ls /root; ls /root/thr 2>/dev/null | head -50
    echo "-- pip:"; pip3 list 2>/dev/null | grep -i -E "numpy|scipy|pandas|gtsam|scikit|yaml|matplotlib|open3d|transforms3d" ' 2>&1
done
echo; echo "## repository"; git -C "$(dirname "$0")/.." log --oneline -1 2>&1
} > "$OUT" 2>&1
echo "wrote $OUT ($(wc -l < "$OUT") lines)"

# Small files that live ONLY on the working machine (container configs, launch files, per-sequence seq.env, file inventory).
X=${OUT%.txt}_files; rm -rf "$X"; mkdir -p "$X/vins_configs" "$X/gpu_root" "$X/gpu_thr" "$X/seq_env"
docker cp $VINS_C:/root/catkin_ws/src/VINS-Mono/config/. "$X/vins_configs/" >/dev/null 2>&1
for f in $(docker exec $GPU_C bash -c 'ls /root/*.launch /root/*.yaml 2>/dev/null'); do docker cp $GPU_C:$f "$X/gpu_root/" >/dev/null 2>&1; done
for f in $(docker exec $GPU_C bash -c 'ls /root/thr/*.yaml /root/thr/*.py /root/thr/*.sh 2>/dev/null'); do docker cp $GPU_C:$f "$X/gpu_thr/" >/dev/null 2>&1; done
for d in $HOME/runs*; do [ -f "$d/seq.env" ] && cp "$d/seq.env" "$X/seq_env/$(basename $d).seq.env"; done
( cd $HOME && find switchslam_project switchslam_channelT -type f ! -name '*.pyc' ! -path '*/__pycache__/*' -printf '%p %s bytes\n' 2>/dev/null | sort ) > "$X/laptop_file_inventory.txt"
# Exact local modifications of the third-party sources (A-LOAM, VINS-Mono, ...): git diff of every repo under /root that is dirty.
mkdir -p "$X/source_diffs"
for C in $GPU_C $VINS_C; do
  docker exec $C bash -c 'rm -rf /tmp/sdiff; mkdir -p /tmp/sdiff; for g in $(find /root -maxdepth 5 -name .git -type d 2>/dev/null); do d=$(dirname $g); n=$(echo $d | tr / _); if [ -n "$(git -C $d status --porcelain 2>/dev/null)" ]; then git -C $d diff > /tmp/sdiff/$n.diff 2>/dev/null; git -C $d status --porcelain > /tmp/sdiff/$n.status 2>/dev/null; fi; done' 2>/dev/null
  docker cp $C:/tmp/sdiff/. "$X/source_diffs/$C/" >/dev/null 2>&1
done
tar czf "${X}.tgz" -C "$(dirname "$X")" "$(basename "$X")" && echo "wrote ${X}.tgz ($(du -h "${X}.tgz" | cut -f1))"
