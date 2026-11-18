import re,subprocess,sys,json
import docx
def calc(pdf, docx_path):
    d=docx.Document(docx_path)
    n=int(re.search(r"Pages:\s+(\d+)",subprocess.check_output(["pdfinfo",pdf]).decode()).group(1))
    pages=[subprocess.check_output(["pdftotext","-layout","-f",str(i),"-l",str(i),pdf,"-"]).decode() for i in range(1,n+1)]
    norm=lambda s: re.sub(r"\s+"," ",s).strip()
    npages=[norm(p) for p in pages]
    c1=next(i for i,t in enumerate(pages) if re.search(r"^\s*CHAPTER 1\s*$",t,re.M) and i>5)
    def roman(k):
        s="";
        for v,r in [(10,"x"),(9,"ix"),(5,"v"),(4,"iv"),(1,"i")]:
            while k>=v: s+=r;k-=v
        return s
    front={}
    for key in ("ACKNOWLEDGEMENT","ABSTRACT","LIST OF FIGURES","LIST OF TABLES","LIST OF ABBREVIATIONS"):
        for i,t in enumerate(pages):
            lines=[l.strip() for l in t.splitlines() if l.strip()]
            if lines and lines[0]==key: front[key]=roman(i+1);break
    res={}
    # TOC rows
    toc=[];lof=[];lot=[]
    for r in d.tables[0].rows[2:]:
        cells=[c.text for c in r.cells]; toc.append(cells)
    for r in d.tables[1].rows[1:]: lof.append([c.text for c in r.cells])
    for r in d.tables[2].rows[1:]: lot.append([c.text for c in r.cells])
    def find(pat_list):
        for i in range(c1,n):
            for pat in pat_list:
                if re.search(pat,pages[i],re.M): return i-c1+1
        return None
    tocp=[]
    for cells in toc:
        no,title,pg=cells[0].strip(),cells[1].strip(),cells[2].strip()
        if title=="REFERENCES": p=find([r"^\s*REFERENCES\s*$"])
        elif no: p=find([r"^\s*CHAPTER %s\s*$"%re.escape(no)])
        else:
            num=title.split(" ")[0]; 
            p=None
            for i in range(c1,n):
                if re.search(r"^\s*"+re.escape(norm(title)[:45]),pages[i],re.M): p=i-c1+1;break
                if norm(title)[:40] in npages[i] and re.search(r"^\s*"+re.escape(num)+r"\s",pages[i],re.M): p=i-c1+1;break
        tocp.append((no,title,pg,p))
    lofp=[]
    for c in lof:
        p=find([r"Figure %s:"%re.escape(c[0].strip())]); lofp.append((c[0].strip(),c[1][:40],c[2].strip(),p))
    lotp=[]
    for c in lot:
        p=find([r"Table %s:"%re.escape(c[0].strip())]); lotp.append((c[0].strip(),c[1][:40],c[2].strip(),p))
    return n,c1,front,tocp,lofp,lotp
if __name__=="__main__":
    n,c1,front,tocp,lofp,lotp=calc(sys.argv[1],sys.argv[2])
    print("pdf pages",n,"body starts at pdf page",c1+1,front)
    bad=0
    for grp in (tocp,lofp,lotp):
        for no,title,pg,p in grp:
            if str(p)!=pg: bad+=1; print("DIFF",no,title[:40],"| doc says",pg,"| render",p)
    print("entries differing from the numbers now in the file:",bad)
