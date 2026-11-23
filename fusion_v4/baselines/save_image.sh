#!/usr/bin/env bash
# Desktop side: package an image for the laptop.   save_image.sh <image> <drive docker_images folder>
# Writes <image>_<commit8>.tar.gz plus .sha256, .size (bytes the image takes on disk) and .commit next to it.
set -eu
IMAGE=${1:?image}; DEST=${2:?folder on the drive}
mountpoint -q "$(df --output=target "$DEST" | tail -1)" || { echo "$DEST is not on a mounted drive"; exit 1; }
C=$(docker image inspect "$IMAGE" --format '{{index .Config.Labels "baseline.upstream_commit"}}')
[ -n "$C" ] || { echo "$IMAGE has no baseline.upstream_commit label"; exit 1; }
mkdir -p "$DEST"; B="$DEST/${IMAGE}_${C:0:8}"
docker save "$IMAGE" | gzip > "$B.tar.gz"
(cd "$DEST" && sha256sum "$(basename "$B").tar.gz" > "$(basename "$B").tar.gz.sha256")
docker image inspect "$IMAGE" --format '{{.Size}}' > "$B.size"
echo "$C" > "$B.commit"
ls -lh "$B".*
