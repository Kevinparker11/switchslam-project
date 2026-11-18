import docx,re,sys
path=sys.argv[1]
d=docx.Document(path)
P=[p.text.strip() for p in d.paragraphs]
# body start
c1=next(i for i,t in enumerate(P) if t=='CHAPTER 1')
heads=[]
for i,t in enumerate(P[c1:],c1):
    if re.match(r'^\d+\.\d+(\.\d+)?\s+\S',t) and len(t)<140 and not t.endswith('.'): heads.append((i,t))
capT={};capF={}
for i,t in enumerate(P[c1:],c1):
    m=re.match(r'^Table (\d+\.\d+): (.*)',t)
    if m: capT[m.group(1)]=(i,m.group(2))
    m=re.match(r'^Figure (\d+\.\d+): (.*)',t)
    if m: capF[m.group(1)]=(i,m.group(2))
toc=[ [c.text.strip() for c in r.cells] for r in d.tables[0].rows[2:]]
lof=[ [c.text.strip() for c in r.cells] for r in d.tables[1].rows[1:]]
lot=[ [c.text.strip() for c in r.cells] for r in d.tables[2].rows[1:]]
print('headings',len(heads),'toc subrows',sum(1 for r in toc if not r[0] and r[1]!='REFERENCES'),'captions T',len(capT),'F',len(capF),'LOT',len(lot),'LOF',len(lof))
ht=[h[1] for h in heads]
tt=[r[1] for r in toc if not r[0] and r[1]!='REFERENCES']
for a in ht:
    if a not in tt: print('HEADING not in TOC:',a)
for a in tt:
    if a not in ht: print('TOC not a heading:',a)
for r in lot:
    c=capT.get(r[0])
    if not c: print('LOT row without caption',r[0])
    elif c[1]!=r[1]: print('LOT title differs',r[0],'|',r[1],'|',c[1])
for k in capT:
    if k not in [r[0] for r in lot]: print('caption not in LOT',k)
for r in lof:
    c=capF.get(r[0])
    if not c: print('LOF row without caption',r[0])
    elif c[1]!=r[1]: print('LOF title differs',r[0],'|',r[1],'|',c[1])
for k in capF:
    if k not in [r[0] for r in lof]: print('caption not in LOF',k)
# sequence
def seq(keys,name):
    last={}
    for k in keys:
        ch,n=map(int,k.split('.'))
        if n!=last.get(ch,0)+1: print(name,'sequence break at',k)
        last[ch]=n
seq(list(capT),'Table'); seq(list(capF),'Figure')
# cross refs
txt=[]
for p in d.paragraphs: txt.append(p.text)
for t in d.tables:
    for r in t.rows:
        for c in r.cells: txt.append(c.text)
allt='\n'.join(txt)
hn=set(h[1].split(' ')[0] for h in heads)
for m in sorted(set(re.findall(r'Tables? (\d+\.\d+)(?:,| and| to)? ?(\d+\.\d+)?',allt))):
    for k in m:
        if k and k not in capT: print('ref to missing Table',k)
for m in sorted(set(re.findall(r'Figures? (\d+\.\d+)(?:,| and| to)? ?(\d+\.\d+)?',allt))):
    for k in m:
        if k and k not in capF: print('ref to missing Figure',k)
for m in sorted(set(re.findall(r'Sections? (\d+\.\d+(?:\.\d+)?)',allt))):
    if m not in hn and m.split('.')[0]+'.'+m.split('.')[1] not in hn: print('ref to missing Section',m)
for m in sorted(set(re.findall(r'Sections? \d+\.\d+(?:\.\d+)? (?:and|to) (\d+\.\d+(?:\.\d+)?)',allt))):
    if m not in hn: print('ref to missing Section (2nd)',m)
