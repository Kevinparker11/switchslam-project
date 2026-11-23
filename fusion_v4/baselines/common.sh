# Shared helpers for the stock baseline runners (fusion_v4/stock_<method>/run_<method>.sh). Source it, don't run it.
#   bl_find_bags_root      sets BAGS_ROOT if it is unset: the laptop_bags folder on a mounted drive under /media/$USER
#   bl_require_mounted P   refuses to go on unless P exists and sits on a mounted drive (mountpoint -q passes on a parent
#                          other than /). Guards against the empty root-owned folder docker -v makes when the drive is off.
#                          ALLOW_LOCAL_BAGS=1 accepts bags on the internal disk (printed in the log).
#   bl_require_docker      docker info must work without sudo
#   bl_lock / bl_unlock    flock on $HOME/.replay.lock (REPLAY_LOCK overrides), the same file the F35 runner locks,
#                          so two replays never overlap, whichever terminal starts them
# Works under set -u.

BL_LOCK=${REPLAY_LOCK:-$HOME/.replay.lock}

bl_die() { echo "ERROR: $*" >&2; exit 1; }

# print the mount that holds path $1 (the nearest parent for which mountpoint -q passes), / if none
bl_mount_of() {
  local p
  p=$(realpath -m -- "$1")
  while [ "$p" != / ]; do
    mountpoint -q -- "$p" && { echo "$p"; return 0; }
    p=$(dirname -- "$p")
  done
  echo /
}

bl_find_bags_root() {
  [ -n "${BAGS_ROOT:-}" ] && return 0
  local u c
  u=${USER:-$(id -un)}
  for c in "/media/$u/One Touch2/laptop_bags" "/media/$u/One Touch1/laptop_bags" /media/"$u"/*/laptop_bags /mnt/*/laptop_bags; do
    [ -d "$c" ] || continue
    [ "$(bl_mount_of "$c")" = / ] && continue      # a leftover folder on the system disk, not the drive
    BAGS_ROOT=$c
    echo "BAGS_ROOT=$BAGS_ROOT (found)"
    return 0
  done
  bl_die "no mounted drive with a laptop_bags folder under /media/$u or /mnt. Plug in and mount the drive, or set BAGS_ROOT."
}

bl_require_mounted() {
  local p=$1 m
  [ -d "$p" ] || bl_die "not found: $p (is the drive mounted? ls /media/${USER:-$(id -un)}/)"
  m=$(bl_mount_of "$p")
  if [ "$m" = / ]; then
    [ "${ALLOW_LOCAL_BAGS:-0}" = 1 ] && { echo "NOTE: $p is on the system disk (ALLOW_LOCAL_BAGS=1)"; return 0; }
    bl_die "$p is not on a mounted drive (mountpoint -q fails for every parent). If the drive is unplugged, docker -v
       would hand the run an empty folder. Mount the drive, or set ALLOW_LOCAL_BAGS=1 if the bags really are on this disk."
  fi
  echo "bags on mount $m"
}

bl_require_docker() {
  command -v docker > /dev/null 2>&1 || bl_die "docker is not installed"
  docker info > /dev/null 2>&1 || bl_die "docker info fails without sudo. Add yourself to the docker group
       (sudo usermod -aG docker \$USER), then log out and in again."
}

# hold the replay lock on fd 9 until bl_unlock (or until the script exits)
bl_lock() {
  exec 9>> "$BL_LOCK" || bl_die "cannot open $BL_LOCK"
  if ! flock -n 9; then
    echo "waiting for $BL_LOCK: another replay is running ($(date +%H:%M:%S))"
    flock 9
    echo "got $BL_LOCK ($(date +%H:%M:%S))"
  fi
}

bl_unlock() {
  flock -u 9 2> /dev/null
  exec 9>&-
}
