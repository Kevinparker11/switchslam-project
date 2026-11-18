import sys, docx, re, subprocess
sys.path.insert(0,'/tmp/w')
import pagecalc
from docx.oxml.ns import qn
src, pdf, out = sys.argv[1:4]
n,c1,front,tocp,lofp,lotp = pagecalc.calc(pdf, src)
d = docx.Document(src)
def setcell(tr, idx, new):
    tc = tr.findall(qn('w:tc'))[idx]
    ts = list(tc.iter(qn('w:t')))
    assert len(ts) >= 1
    ts[0].text = new
    for t in ts[1:]: t.text = ""
tbls = list(d.element.body.iterchildren(qn('w:tbl')))
changed = 0
for tbl, grp, first in ((tbls[0], tocp, 2), (tbls[1], lofp, 1), (tbls[2], lotp, 1)):
    rows = tbl.findall(qn('w:tr'))[first:]
    assert len(rows) == len(grp), (len(rows), len(grp))
    for tr, (no, title, pg, p) in zip(rows, grp):
        assert p is not None, (no, title)
        if str(p) != pg:
            setcell(tr, 2, str(p)); changed += 1; print("  %-5s %-45s %s -> %s" % (no, title[:45], pg, p))
print("changed page numbers:", changed, "| front matter:", front)
d.save(out)
