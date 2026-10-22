#!/usr/bin/env python3
"""Run run_backend.py on several recorded runs and print mean +- sd per loop model.

usage: python3 backend_multi.py --dir RUNS_DIR --tags F8_kf_run1,F8_kf_run3 --gt ground_truth_path.csv \
           [--models none,iso] [--jobs 2] [--extra "--min-gap 30"]
Reads RUNS_DIR/switching_log_v2_<tag>.csv and RUNS_DIR/keyframes_<tag>.npz.  Each run takes about 6-8 minutes
(loop verification dominates); --jobs runs several in parallel (one core each)."""
import argparse
import concurrent.futures as cf
import os
import re
import subprocess
import sys
import warnings

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--tags", required=True)
ap.add_argument("--gt", required=True)
ap.add_argument("--models", default="none,iso")
ap.add_argument("--jobs", type=int, default=2)
ap.add_argument("--extra", default="")
a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
NUM = r"(nan|[\d.]+)"   # bag 0 / bags 1-2 columns are nan on sequences without the Multi Floor split
ROW = re.compile(r"^(\w+)\s+\d+\s+\d+\s+\d+\s*\|\s*" + NUM + r"\s*/\s*" + NUM + r"\s*\|\s*" + NUM + r"\s*/\s*" + NUM + r"\s*\|\s*" + NUM + r"\s*/\s*" + NUM)


def one(tag):
    cmd = [sys.executable, os.path.join(here, "run_backend.py"),
           "--log", os.path.join(a.dir, "switching_log_v2_%s.csv" % tag),
           "--kf", os.path.join(a.dir, "keyframes_%s.npz" % tag), "--gt", a.gt, "--models", a.models] + a.extra.split()
    out = subprocess.run(cmd, capture_output=True, text=True)
    open(os.path.join(a.dir, "backend_%s.log" % tag), "w").write(out.stdout + out.stderr)
    res = {}
    for line in out.stdout.splitlines():
        m = ROW.match(line)
        if m:
            res[m.group(1)] = [float(x) for x in m.groups()[1:]]
    return tag, res


tags = a.tags.split(",")
with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
    results = dict(ex.map(one, tags))
print("%-12s %-11s %16s %16s %16s" % ("run", "model", "full RMSE/max", "bag 0 RMSE/max", "bags 1-2 RMSE/max"))
for tag in tags:
    for m, r in results[tag].items():
        print("%-12s %-11s %7.3f / %5.2f %7.3f / %5.2f %7.3f / %5.2f" % (tag, m, *r))
print()
for m in a.models.split(","):
    rows = np.array([results[t][m] for t in tags if m in results[t]])
    if len(rows):
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mu = np.nanmean(rows, 0)
            sd = np.nanstd(rows, 0, ddof=1) if len(rows) > 1 else np.zeros(rows.shape[1])
        print("%-11s n=%d  full %.3f +- %.3f (max %.2f)  bag0 %.3f +- %.3f  bags1-2 %.3f +- %.3f" % (
            m, len(rows), mu[0], sd[0], mu[1], mu[2], sd[2], mu[4], sd[4]))
