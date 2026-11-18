import sys, docx
sys.path.insert(0,'/tmp/w')
import pagecalc
from docx.oxml.ns import qn
src,pdf,out=sys.argv[1:4]
n,c1,front,tocp,lofp,lotp=pagecalc.calc(pdf,src)
d=docx.Document(src)
tbl=list(d.element.body.iterchildren(qn('w:tbl')))[0]
row=tbl.findall(qn('w:tr'))[1]
tc=row.findall(qn('w:tc'))[2]
ps=tc.findall(qn('w:p'))
keys=["ACKNOWLEDGEMENT","ABSTRACT","LIST OF FIGURES","LIST OF TABLES","LIST OF ABBREVIATIONS"]
assert len(ps)==5,len(ps)
for p,k in zip(ps,keys):
    ts=list(p.iter(qn('w:t'))); ts[0].text=front[k]
    for t in ts[1:]: t.text=''
d.save(out); print(front)
