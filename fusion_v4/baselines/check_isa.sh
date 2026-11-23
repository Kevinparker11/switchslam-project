#!/usr/bin/env bash
# Scan compiled binaries for instructions the laptop (AMD Ryzen 5 5600H) and the desktop (i7-12700) do not both have.
# Neither has AVX-512, so any zmm register or AVX-512 mask register (%k0..%k7) fails the check. AVX2/FMA (ymm) is allowed, both have it;
# its count is printed, because the build is meant to be plain x86-64 and a count above 0 means a -march flag slipped in.
#   check_isa.sh DIR_OR_FILE...      (default: /root/*_ws/devel /usr/local/lib, i.e. what the Dockerfiles build)
# Exit 0 = pass, 1 = AVX-512 found, 2 = nothing to scan.
set -u
[ "$#" -gt 0 ] || set -- $(ls -d /root/*_ws/devel /root/*_ws/build /usr/local/lib 2> /dev/null)
command -v objdump > /dev/null || { echo "objdump not found (binutils)"; exit 2; }
FILES=$(find "$@" -type f \( -name '*.so*' -o -perm -u+x \) 2> /dev/null | while read -r f; do
  head -c4 "$f" 2> /dev/null | grep -q $'^\x7fELF' && echo "$f"; done)
[ -n "$FILES" ] || { echo "no ELF files under: $*"; exit 2; }
BAD=0; N=0; YMM=0
while read -r f; do
  N=$((N + 1))
  D=$(objdump -d --no-show-raw-insn "$f" 2> /dev/null)
  z=$(printf '%s\n' "$D" | grep -cE '%zmm|%k[0-7]\b')
  y=$(printf '%s\n' "$D" | grep -c '%ymm')
  YMM=$((YMM + y))
  [ "$z" -gt 0 ] && { echo "AVX-512: $z instructions in $f"; BAD=$((BAD + 1)); }
done <<< "$FILES"
echo "scanned $N ELF files; files with AVX-512: $BAD; ymm (AVX/AVX2) instructions in total: $YMM"
[ "$BAD" = 0 ] && { echo "ISA CHECK: PASS"; exit 0; }
echo "ISA CHECK: FAIL"; exit 1
