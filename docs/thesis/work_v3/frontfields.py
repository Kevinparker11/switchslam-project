import sys, copy, docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
src,out=sys.argv[1:3]
d=docx.Document(src); body=d.element.body
def ptext(p): return "".join(t.text or "" for t in p.iter(qn('w:t'))).strip()
keys=["ACKNOWLEDGEMENT","ABSTRACT","LIST OF FIGURES","LIST OF TABLES","LIST OF ABBREVIATIONS"]
heads={}
for p in body.iterchildren(qn('w:p')):
    t=ptext(p)
    if t in keys and t not in heads: heads[t]=p
assert set(heads)==set(keys), set(keys)-set(heads)
def mkrun(rpr,child):
    r=OxmlElement('w:r')
    if rpr is not None: r.append(copy.deepcopy(rpr))
    r.append(child); return r
def fld(c):
    f=OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'),c); return f
bid=700
names={}
for i,k in enumerate(keys):
    bid+=1; nm="_TocF%d"%(i+1); names[k]=nm
    p=heads[k]
    first=[r for r in p.findall(qn('w:r')) if r.find(qn('w:t')) is not None][0]
    s=OxmlElement('w:bookmarkStart'); s.set(qn('w:id'),str(bid)); s.set(qn('w:name'),nm)
    e=OxmlElement('w:bookmarkEnd'); e.set(qn('w:id'),str(bid))
    first.addprevious(s); first.addnext(e)
tbl=list(body.iterchildren(qn('w:tbl')))[0]
row=tbl.findall(qn('w:tr'))[1]
tc=row.findall(qn('w:tc'))[2]
ps=tc.findall(qn('w:p')); assert len(ps)==5
for p,k in zip(ps,keys):
    runs=[r for r in p.findall(qn('w:r')) if r.find(qn('w:t')) is not None]
    r0=runs[0]; rpr=r0.find(qn('w:rPr'))
    for r in runs[1:]: p.remove(r)
    it=OxmlElement('w:instrText'); it.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); it.text=' PAGEREF %s \\h '%names[k]
    r0.addprevious(mkrun(rpr,fld('begin'))); r0.addprevious(mkrun(rpr,it)); r0.addprevious(mkrun(rpr,fld('separate')))
    r0.addnext(mkrun(rpr,fld('end')))
d.save(out); print('front fields:',names)
