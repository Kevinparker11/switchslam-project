#!/usr/bin/env bash
# Laptop side: load a baseline image built on the desktop. Never builds.
#   load_image.sh <image>                       newest <image>_*.tar.gz in <drive>/docker_images (checksum checked)
#   load_image.sh <image> --from FILE.tar.gz    a given tarball
#   load_image.sh <image> --from ssh://user@host   stream from the desktop's docker (no file, no drive; needs ssh to the desktop)
# The laptop disk is nearly full, so it refuses to start when the free space under Docker's root is smaller than the image size
# (layers the laptop already has, such as ros:noetic, are not written again; LOAD_ASSUME_SHARED_GB=3 lowers the need by that much).
set -u
IMAGE=${1:?image name, e.g. lvisam_stock}; shift
FROM=""; [ "${1:-}" = --from ] && FROM=${2:?--from needs a value}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$HERE/common.sh"
bl_require_docker
SHARED=${LOAD_ASSUME_SHARED_GB:-0}

free_ok() {   # $1 = image size in bytes
  local root avail need
  root=$(docker info -f '{{.DockerRootDir}}' 2> /dev/null); [ -d "$root" ] || root=/var/lib/docker
  avail=$(df -B1 --output=avail "$root" 2> /dev/null | tail -1 | tr -d ' ')
  need=$(( $1 - SHARED * 1000000000 )); [ "$need" -lt 0 ] && need=0
  echo "image size $(( $1 / 1000000 )) MB, free under $root: $(( avail / 1000000 )) MB (shared layers assumed: ${SHARED} GB)"
  [ "$avail" -ge "$need" ] || bl_die "not enough free disk space. Free space first (docker image ls; docker rmi <unused image>), then run again. Nothing was written."
}

case "$FROM" in
  ssh://*)
    H=${FROM#ssh://}
    SZ=$(ssh "$H" "docker image inspect '$IMAGE' --format '{{.Size}}'") || bl_die "ssh to $H failed"
    COMMIT=$(ssh "$H" "docker image inspect '$IMAGE' --format '{{index .Config.Labels \"baseline.upstream_commit\"}}'")
    free_ok "$SZ"
    echo "streaming $IMAGE from $H ..."
    ssh "$H" "docker save '$IMAGE' | gzip" | gunzip | docker load || bl_die "docker load failed (Docker version gap? see README: private registry fallback)"
    ;;
  *)
    if [ -z "$FROM" ]; then
      bl_find_bags_root
      DIR="$(dirname "$BAGS_ROOT")/docker_images"
      bl_require_mounted "$DIR"
      FROM=$(ls -1t "$DIR/${IMAGE}"_*.tar.gz 2> /dev/null | head -1)
      [ -n "$FROM" ] || bl_die "no ${IMAGE}_*.tar.gz in $DIR"
    fi
    [ -f "$FROM" ] || bl_die "not found: $FROM"
    if [ -f "$FROM.sha256" ]; then
      (cd "$(dirname "$FROM")" && sha256sum -c "$(basename "$FROM").sha256") || bl_die "checksum mismatch, the file is damaged"
    else echo "NOTE: no $FROM.sha256, checksum not checked"; fi
    B=${FROM%.tar.gz}; SZ=$(cat "$B.size" 2> /dev/null || echo $(( $(stat -c %s "$FROM") * 3 )))
    COMMIT=$(cat "$B.commit" 2> /dev/null || true)
    free_ok "$SZ"
    echo "loading $FROM ..."
    gunzip -c "$FROM" | docker load || bl_die "docker load failed (Docker version gap? see README: private registry fallback)"
    ;;
esac

docker image inspect "$IMAGE" > /dev/null 2>&1 || bl_die "after the load, no image named $IMAGE exists (tag missing)"
GOT=$(docker image inspect "$IMAGE" --format '{{index .Config.Labels "baseline.upstream_commit"}}')
echo "loaded $IMAGE, upstream commit label: $GOT"
if [ -n "${COMMIT:-}" ] && [ "$COMMIT" != "$GOT" ]; then bl_die "commit label $GOT does not match the package ($COMMIT)"; fi
echo "LOAD OK"
