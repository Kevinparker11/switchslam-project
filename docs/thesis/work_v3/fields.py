import sys, re, copy, docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
src,out=sys.argv[1:3]
d=docx.Document(src)
body=d.element.body
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def ptext(p): return "".join(t.text or "" for t in p.iter(qn('w:t'))).strip()
tbls=list(body.iterchildren(qn('w:tbl')))
last_list_tbl=tbls[2]
paras=[]; seen=False
for e in body.iterchildren():
    if e is last_list_tbl: seen=True; continue
    if seen and e.tag==qn('w:p'): paras.append(e)
bid=[100]; names={}
def bookmark(p,name):
    bid[0]+=1
    s=OxmlElement('w:bookmarkStart'); s.set(qn('w:id'),str(bid[0])); s.set(qn('w:name'),name)
    e=OxmlElement('w:bookmarkEnd'); e.set(qn('w:id'),str(bid[0]))
    ppr=p.find(qn('w:pPr'))
    if ppr is not None: ppr.addnext(s)
    else: p.insert(0,s)
    p.append(e)
def find_target(kind,key):
    for p in paras:
        t=ptext(p)
        if kind=='chap' and t==key: return p
        if kind=='ref' and t=="REFERENCES": return p
        if kind=='head' and t==key: return p
        if kind=='cap' and t.startswith(key): return p
    return None
def mkrun(rpr,child):
    r=OxmlElement('w:r')
    if rpr is not None: r.append(copy.deepcopy(rpr))
    r.append(child); return r
def fld(c): 
    f=OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'),c); return f
def setfield(tc,name):
    p=tc.find(qn('w:p')); runs=[r for r in p.findall(qn('w:r')) if r.find(qn('w:t')) is not None]
    assert len(runs)>=1
    r0=runs[0]; rpr=r0.find(qn('w:rPr')); txt=r0.find(qn('w:t')).text
    for r in runs[1:]: p.remove(r)
    it=OxmlElement('w:instrText'); it.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); it.text=' PAGEREF %s \\h '%name
    seq=[mkrun(rpr,fld('begin')),mkrun(rpr,it),mkrun(rpr,fld('separate')),r0,mkrun(rpr,fld('end'))]
    r0.addprevious(seq[0]); r0.addprevious(seq[1]); r0.addprevious(seq[2]); r0.addnext(seq[4])
n=0; missing=[]
def rowkey(kind,cells):
    pass
# TOC
for i,tr in enumerate(tbls[0].findall(qn('w:tr'))[2:]):
    tcs=tr.findall(qn('w:tc')); txt=[ptext(tc) for tc in tcs]
    no,title=txt[0],txt[1]
    if title=="REFERENCES": t=find_target('ref',None)
    elif no: t=find_target('chap',"CHAPTER "+no)
    else: t=find_target('head',title)
    if t is None: missing.append(('toc',no,title)); continue
    nm="_TocA%05d"%(i+1); bookmark(t,nm); setfield(tcs[2],nm); n+=1
for j,(tb,pref,base) in enumerate(((tbls[1],"Figure",2),(tbls[2],"Table",3))):
    for i,tr in enumerate(tb.findall(qn('w:tr'))[1:]):
        tcs=tr.findall(qn('w:tc')); no=ptext(tcs[0])
        t=find_target('cap',"%s %s:"%(pref,no))
        if t is None: missing.append((pref,no)); continue
        nm="_Toc%s%05d"%("B" if pref=="Figure" else "C",i+1); bookmark(t,nm); setfield(tcs[2],nm); n+=1
print("fields:",n,"missing:",missing)
assert not missing
# updateFields in settings
st=d.settings.element
uf=OxmlElement('w:updateFields'); uf.set(qn('w:val'),'true')
for tag in ('hdrShapeDefaults','footnotePr','endnotePr','compat'):
    el=st.find(qn('w:'+tag))
    if el is not None: el.addprevious(uf); break
d.save(out)
