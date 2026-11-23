#!/usr/bin/env python3
"""Which zips in a folder are redundant because the other zips already contain every file in them?
Compares each file by name, size and CRC32 (read from the zip index, so nothing is extracted or changed). Picks zips greedily by how many files
no earlier pick has, so the kept zips together hold every distinct file once. Prints the keep list and the redundant list; deletes and moves nothing.
usage: zip_cover.py [GLOB]      default ~/Downloads/for_claude_*.zip"""
import glob
import os
import sys
import zipfile

pat = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "Downloads", "for_claude_*.zip")
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
