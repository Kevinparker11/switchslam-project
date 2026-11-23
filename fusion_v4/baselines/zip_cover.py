#!/usr/bin/env python3
"""Which zips in a folder are redundant because the other zips already contain every file in them?
Compares each file by name, size and CRC32 (read from the zip index, so nothing is extracted or changed). Picks zips greedily by how many files
no earlier pick has, so the kept zips together hold every distinct file once. Prints the keep list and the redundant list; deletes and moves nothing.
usage: zip_cover.py [GLOB]                          list only (default GLOB ~/Downloads/for_claude_*.zip)
       zip_cover.py [GLOB] --archive DIR            also copy the zips into DIR/keep/ and DIR/redundant/ and verify every copy by SHA-256
       zip_cover.py [GLOB] --archive DIR --remove-source    and delete each original, but only after its copy is verified
DIR must already exist (it is never created, so an unmounted drive cannot be filled by mistake) and needs enough free space."""
import argparse
import glob
import hashlib
import os
import shutil
import sys
import zipfile

ap = argparse.ArgumentParser()
ap.add_argument("glob", nargs="?", default=os.path.join(os.path.expanduser("~"), "Downloads", "for_claude_*.zip"))
ap.add_argument("--archive")
ap.add_argument("--remove-source", action="store_true")
args = ap.parse_args()
pat = args.glob
zips = sorted(glob.glob(pat))
if not zips:
    sys.exit("no zip matches %s" % pat)
content = {}
for z in zips:
    try:
        content[z] = {(i.filename, i.file_size, i.CRC) for i in zipfile.ZipFile(z).infolist() if not i.is_dir()}
    except zipfile.BadZipFile:
        print("BAD ZIP, skipped: %s" % z)
union = set().union(*content.values())
covered, keep, redundant = set(), [], []
left = dict(content)
while left:
    z, new = max(((k, len(v - covered)) for k, v in left.items()), key=lambda t: t[1])
    if new == 0:
        redundant = list(left)
        break
    keep.append((z, new)); covered |= left.pop(z)
mb = lambda p: os.path.getsize(p) / 1e6
print("%d zips, %d distinct files (name, size and CRC32 the same = one file)\n" % (len(content), len(union)))
print("KEEP (together they hold every distinct file):")
for z, n in keep:
    print("  %-36s %7.0f MB  %5d files, %5d of them not in an earlier pick" % (os.path.basename(z), mb(z), len(content[z]), n))
print("\nREDUNDANT (every file is already in the KEEP list):")
for z in sorted(redundant):
    print("  %-36s %7.0f MB  %5d files" % (os.path.basename(z), mb(z), len(content[z])))
print("\nkeep %.0f MB, redundant %.0f MB" % (sum(mb(z) for z, _ in keep), sum(mb(z) for z in redundant)))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


if args.archive:
    d = args.archive
    if not os.path.isdir(d):
        sys.exit("REFUSED: %s does not exist (drive not mounted?)" % d)
    need = sum(os.path.getsize(z) for z in content) + 2e9
    free = shutil.disk_usage(d).free
    if free < need:
        sys.exit("REFUSED: %.1f GB free in %s, need %.1f GB" % (free / 1e9, d, need / 1e9))
    plan = [(z, "keep") for z, _ in keep] + [(z, "redundant") for z in sorted(redundant)]
    os.makedirs(os.path.join(d, "keep"), exist_ok=True); os.makedirs(os.path.join(d, "redundant"), exist_ok=True)
    ok = bad = 0
    with open(os.path.join(d, "zip_cover_manifest.txt"), "w") as m:
        for z, kind in plan:
            dst = os.path.join(d, kind, os.path.basename(z))
            shutil.copyfile(z, dst)
            good = os.path.getsize(dst) == os.path.getsize(z) and sha(dst) == sha(z)
            m.write("%s\t%s\t%s\n" % (kind, os.path.basename(z), "verified" if good else "MISMATCH"))
            if good:
                ok += 1
                print("copied and verified: %s/%s" % (kind, os.path.basename(z)))
                if args.remove_source:
                    os.remove(z)
            else:
                bad += 1
                print("MISMATCH, original left in place: %s" % z)
    print("\n%d verified, %d failed%s" % (ok, bad, "; originals of the verified ones removed" if args.remove_source else "; no original was removed"))
