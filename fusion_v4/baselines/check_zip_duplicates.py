#!/usr/bin/env python3
"""Which of the zip files in a folder are only copies of files that exist elsewhere on this machine?
Reads each zip's file list (nothing is extracted, nothing is changed or deleted) and looks every file up by name and size in the
other folders. A file counts as found when a file of the same name and the same size exists, or when name.gz exists (size not compared).
usage: check_zip_duplicates.py [--zips 'GLOB'] [--search DIR ...]
default: zips = ~/Downloads/for_claude_*.zip ; search = ~/runs_* ~/sw_new ~/Desktop ~/Downloads (the zips themselves are skipped)"""
import argparse
import glob
import os
import sys
import zipfile
from collections import defaultdict

H = os.path.expanduser("~")
ap = argparse.ArgumentParser()
ap.add_argument("--zips", default=os.path.join(H, "Downloads", "for_claude_*.zip"))
ap.add_argument("--search", nargs="*")
a = ap.parse_args()
roots = a.search or sorted(glob.glob(os.path.join(H, "runs_*"))) + [os.path.join(H, d) for d in ("sw_new", "Desktop", "Downloads")]
zips = sorted(glob.glob(a.zips))
if not zips:
    sys.exit("no zip matches %s" % a.zips)

size_of = defaultdict(set)     # basename -> {sizes}
names = set()
for r in roots:
    for dp, _, fs in os.walk(r, followlinks=False):
        for f in fs:
            if f.endswith(".zip"):
                continue
            p = os.path.join(dp, f)
            try:
                size_of[f].add(os.path.getsize(p))
            except OSError:
                pass
            names.add(f)

tot_found = tot = 0
print("%-34s %6s %6s %6s %6s  %s" % ("zip", "MB", "files", "exact", "gz", "verdict"))
for z in zips:
    try:
        infos = [i for i in zipfile.ZipFile(z).infolist() if not i.is_dir()]
    except zipfile.BadZipFile:
        print("%-34s  BAD ZIP" % os.path.basename(z)); continue
    exact = gz = 0; missing = []
    for i in infos:
        b = os.path.basename(i.filename)
        if i.file_size in size_of.get(b, ()):
            exact += 1
        elif b + ".gz" in names or (b.endswith(".gz") and b[:-3] in names):
            gz += 1
        else:
            missing.append(i.filename)
    n = len(infos); ok = exact + gz
    tot += n; tot_found += ok
    verdict = "COPY (all files found elsewhere)" if not missing else "%d NOT FOUND elsewhere" % len(missing)
    print("%-34s %6.0f %6d %6d %6d  %s" % (os.path.basename(z)[:34], os.path.getsize(z) / 1e6, n, exact, gz, verdict))
    for m in missing[:3]:
        print("      missing e.g. %s" % m)
print("\n%d of %d files are found elsewhere. Zips marked COPY hold nothing that exists only in the zip." % (tot_found, tot))
