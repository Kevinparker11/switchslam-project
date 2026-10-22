#!/bin/bash
# Pack the two working containers for a new PC (run on the working laptop).
#   bash tools/export_images.sh [OUTDIR]        default OUTDIR=$HOME/switchslam_export
# Produces in OUTDIR:
#   images.tar.gz          docker images committed from the CURRENT containers (several GB)
#   ws_gpu_catkin_ws.tgz   the host folder bind-mounted at /root/catkin_ws in switchslam_gpu_v2 (A-LOAM, built)
#   ws_vins_catkin_ws.tgz  the host folder bind-mounted at /root/catkin_ws in vinsmono_test (VINS-Mono, built)
#   mounts.txt             the original host paths of those folders
# The two catkin workspaces are bind mounts, so `docker commit` does not contain them - they are archived separately.
# Nothing is modified; the containers are only committed (a new image tag is added).
set -e
GPU_C=${GPU_C:-switchslam_gpu_v2}; VINS_C=${VINS_C:-vinsmono_test}
OUT=${1:-$HOME/switchslam_export}; TAG=export-$(date +%Y%m%d)
mkdir -p "$OUT"
src_of() { docker inspect "$1" --format '{{range .Mounts}}{{if eq .Destination "/root/catkin_ws"}}{{.Source}}{{end}}{{end}}'; }
GPU_WS=$(src_of $GPU_C); VINS_WS=$(src_of $VINS_C)
[ -d "$GPU_WS" ] && [ -d "$VINS_WS" ] || { echo "cannot find the bind-mounted catkin_ws folders (got '$GPU_WS' / '$VINS_WS')"; exit 1; }
{ echo "$GPU_C  $GPU_WS"; echo "$VINS_C  $VINS_WS"; } > "$OUT/mounts.txt"
docker stop $GPU_C $VINS_C >/dev/null
docker commit $GPU_C  switchslam_gpu_v2:$TAG
docker commit $VINS_C vinsmono_test:$TAG
docker save switchslam_gpu_v2:$TAG vinsmono_test:$TAG | gzip > "$OUT/images.tar.gz"
tar czf "$OUT/ws_gpu_catkin_ws.tgz"  -C "$(dirname "$GPU_WS")"  "$(basename "$GPU_WS")"
tar czf "$OUT/ws_vins_catkin_ws.tgz" -C "$(dirname "$VINS_WS")" "$(basename "$VINS_WS")"
docker start $GPU_C $VINS_C >/dev/null
ls -lh "$OUT"; echo "copy $OUT to the new PC and run tools/import_images.sh there"
