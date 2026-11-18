"""Final report, step 2 (after edit514.py): the six RViz renders are replaced by the grey placeholders of the v3 report, and the
captions, the list-of-figures rows and the text of Sections 5.1 and 5.6 to 5.10 are matched to the new views, in which the A-LOAM
line is a separate run of stock A-LOAM instead of the A-LOAM output of the F35 run.
usage: python3 edit_rviz.py in.docx v3_rewrite.docx out.docx
  in.docx          Final_Report_5.14_removed.docx (output of edit514.py)
  v3_rewrite.docx  CB.EN.P2MFA25004_Thesis_Report_v3_rewrite.docx (holds the placeholders image23..28)
Only the paragraphs named below are touched; every other part of the file is copied unchanged."""
import re
import shutil
import sys
import zipfile

import docx

src, v3, out = sys.argv[1:4]
d = docx.Document(src)
P = d.paragraphs


def find(prefix):
    hit = [p for p in P if p.text.strip().startswith(prefix)]
    assert len(hit) == 1, (prefix, len(hit))
    return hit[0]


def set_text(p, new):
    assert len(p.runs) == 1, (p.text[:40], len(p.runs))
    p.runs[0].text = new


def sub(p, old, new):
    t = p.text
    assert t.count(old) == 1, (old[:50], t.count(old))
    set_text(p, t.replace(old, new))


# ---- Section 5.1: what the baselines are -------------------------------------------------------------------
p = find("The baselines are VINS-Mono alone")
sub(p, "An implementation of Switch-SLAM within this software stack did not reproduce them (Table 5.13).",
    "An implementation of Switch-SLAM within this software stack did not reproduce them (Table 5.13). "
    "A-LOAM alone (F5) is run through the fusion node, which gives A-LOAM its own last pose as the initial guess of each "
    "scan-to-map matching and uses no motion model. The RViz views of Sections 5.6 to 5.10 show stock A-LOAM instead, the "
    "unmodified A-LOAM, whose initial guess comes from its own scan-to-scan odometry and into which nothing from the fusion "
    "node is fed back. Stock A-LOAM was run once on each of the six sequences, on the same data and at the replay rate of the "
    "F35 runs (the farm route again in Gazebo). These runs serve only the views; they are not part of Table 5.6 or of the tests "
    "in Section 5.11.")

# ---- text of Sections 5.6.1 to 5.10.2 ----------------------------------------------------------------------
set_text(find("Figure 5.6 shows the F35 run on Multi Floor"),
         "Figure 5.6 shows the F35 run on Multi Floor with the ground truth, VINS-Mono alone from the same run and a separate "
         "run of stock A-LOAM (values in the legend). F35 had an ATE of 0.54 m and a maximum error of 1.01 m. In the same run, "
         "VINS-Mono alone scored 1.32 / 4.77 m and the A-LOAM output seeded by the fusion 1.92 / 5.26 m (ATE / maximum error). "
         "Switch-SLAM published 1.61 / 3.63 m.")
set_text(find("Figure 5.7 shows the first F35 run on Corridor02"),
         "Figure 5.7 shows the first F35 run on Corridor02, which gave 1.93 / 3.46 m; the second run gave 2.04 / 3.46 m. The "
         "figure also shows VINS-Mono alone from this run and a separate run of stock A-LOAM (values in the legend). In the first "
         "run VINS-Mono alone scored 3.51 / 8.35 m and the A-LOAM output seeded by the fusion 1.17 / 2.12 m, so on this sequence "
         "the A-LOAM output was more accurate than the fused path. No Switch-SLAM value is published for this sequence.")
set_text(find("Figure 5.8 shows the F35 run on Long Corridor"),
         "Figure 5.8 shows the F35 run on Long Corridor with VINS-Mono alone (4.99 / 10.85 m) and a separate run of stock A-LOAM "
         "(values in the legend). F35 gave 2.10 / 3.73 m, the A-LOAM output of the F35 run 1.00 / 2.50 m, and Switch-SLAM "
         "published 2.42 / 5.09 m.")
sub(find("The runs of F24 and F35 are not a clean pair"),
    "Figure 5.9 shows this run, with the paths of A-LOAM (0.312 / 0.627 m) and VINS-Mono alone (4.31 / 6.95 m) from the same run.",
    "Figure 5.9 shows this run with VINS-Mono alone (4.31 / 6.95 m) and a separate run of stock A-LOAM (values in the "
    "legend); the A-LOAM output of this run scored 0.312 / 0.627 m.")
sub(find("On Cave02, F35 gave 6.23 m"),
    "Figure 5.11 shows the F35 run (6.23 / 10.56 m) with the A-LOAM output from the same run (8.66 / 15.99 m); VINS-Mono alone "
    "lies outside the plotted area in this run.",
    "Figure 5.11 shows the F35 run (6.23 / 10.56 m) with a separate run of stock A-LOAM (values in the legend); the A-LOAM "
    "output of the F35 run scored 8.66 / 15.99 m. VINS-Mono alone lies outside the plotted area in this run.")
sub(find("On GEODE, VINS-Mono lost its scale"),
    "Figure 5.12 shows the first F35 run on the stairwell (6.36 / 14.07 m) with the A-LOAM output from the same run "
    "(6.39 / 12.75 m); VINS-Mono alone lies outside the plotted area.",
    "Figure 5.12 shows the first F35 run on the stairwell (6.36 / 14.07 m) with a separate run of stock A-LOAM (values in the "
    "legend); the A-LOAM output of the F35 run scored 6.39 / 12.75 m. VINS-Mono alone lies outside the plotted area.")

# ---- captions (text and list of figures) -------------------------------------------------------------------
TAIL4 = "RViz view of the F35 live run with the ground truth, VINS-Mono alone from the same run and a separate run of stock A-LOAM"
TAIL2 = "RViz view of the F35 live run with the ground truth and a separate run of stock A-LOAM"
CAPS = {"5.6": ("Multi Floor", TAIL4), "5.7": ("Corridor02", TAIL4), "5.8": ("Long Corridor", TAIL4),
        "5.9": ("Farm route", TAIL4), "5.11": ("Cave02", TAIL2), "5.12": ("GEODE stairs", TAIL2)}
for n, (name, tail) in CAPS.items():
    p = find("Figure %s:" % n)
    assert "RViz view of the F35 live run" in p.text
    set_text(p, "Figure %s: %s: %s" % (n, name, tail))
lof = d.tables[1]
done = 0
for r in lof.rows:
    c0 = r.cells[0].text.strip()
    if c0 in CAPS:
        name, tail = CAPS[c0]
        cell = r.cells[1]
        runs = [x for pp in cell.paragraphs for x in pp.runs]
        runs[0].text = "%s: %s" % (name, tail)
        for x in runs[1:]:
            x.text = ""
        done += 1
assert done == 6, done
d.save(out + ".tmp")

# ---- images: the six renders (image16..19, 21, 22) become the placeholders (image23..28 of the v3 report) --------
SWAP = {"word/media/image16.png": "word/media/image23.png", "word/media/image17.png": "word/media/image24.png",
        "word/media/image18.png": "word/media/image25.png", "word/media/image19.png": "word/media/image26.png",
        "word/media/image21.png": "word/media/image27.png", "word/media/image22.png": "word/media/image28.png"}
zv = zipfile.ZipFile(v3)
zi = zipfile.ZipFile(out + ".tmp")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        data = zv.read(SWAP[it.filename]) if it.filename in SWAP else zi.read(it.filename)
        zo.writestr(it, data)
shutil.os.remove(out + ".tmp")
print("saved", out)
