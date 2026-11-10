"""Build the F26 version of the report from the owner's uploaded draft (front matter, styles, footers and section breaks kept;
abstract, lists and body regenerated with the same paragraph formats).  usage: build2.py OUT.docx [pages.json]"""
import copy, json, os, re, shutil, subprocess, sys
from lxml import etree
from PIL import Image

S = "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad"
SRC = S + "/rep/un"          # unpacked owner's draft (runs merged); read only
U = S + "/rep/un2"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
NSDECL = ('xmlns:w="%s" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
          'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
          'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"' % W)
FONT = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
TEXT_W = 8283
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content2 as C


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


TOK = re.compile(r"(\*\*.+?\*\*|\*(?=\S)[^*\n]+?\*|_\{.+?\}|\^\{.+?\}|\[\[.+?\]\]|\t)")


def runs(text, size=24, bold=False, italic=False, shade=False):
    out = []
    sh = '<w:shd w:val="clear" w:fill="FFFF00"/>' if shade else ""
    for part in TOK.split(text):
        if not part:
            continue
        b, i, va, hl = bold, italic, None, False
        if part == "\t":
            out.append('<w:r><w:rPr>%s<w:sz w:val="%d"/><w:szCs w:val="%d"/>%s</w:rPr><w:tab/></w:r>' % (FONT, size, size, sh)); continue
        if part.startswith("**"): part, b = part[2:-2], True
        elif part.startswith("[["): part, hl = part[2:-2], True
        elif part.startswith("*") and len(part) > 2 and part.endswith("*") and not part[1].isspace(): part, i = part[1:-1], True
        elif part.startswith("_{"): part, va = part[2:-1], "subscript"
        elif part.startswith("^{"): part, va = part[2:-1], "superscript"
        rpr = FONT + ("<w:b/>" if b else "") + ("<w:i/>" if i else "") + '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (size, size) + \
            ('<w:highlight w:val="yellow"/>' if hl else "") + sh + ('<w:vertAlign w:val="%s"/>' % va if va else "")
        out.append('<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(part)))
    return "".join(out)


def P(text, jc="both", bold=False, size=24, line=360, before=None, after=None, keep=False, italic=False, ppr_extra=""):
    sp = '<w:spacing%s%s w:line="%d" w:lineRule="auto"/>' % (
        ' w:before="%d"' % before if before is not None else "", ' w:after="%d"' % after if after is not None else "", line)
    ppr = ("<w:keepNext/>" if keep else "") + ppr_extra + sp + ('<w:jc w:val="%s"/>' % jc if jc else "")
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % (ppr, runs(text, size, bold, italic))


def page_break():
    return '<w:p><w:pPr><w:rPr>%s<w:sz w:val="24"/></w:rPr></w:pPr><w:r><w:rPr>%s<w:sz w:val="24"/></w:rPr><w:br w:type="page"/></w:r></w:p>' % (FONT, FONT)


def bullet(text):
    return ('<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
            '<w:spacing w:line="360" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr>%s</w:p>' % runs(text))


def equation(text, num):
    ppr = ('<w:tabs><w:tab w:val="center" w:pos="%d"/><w:tab w:val="right" w:pos="%d"/></w:tabs>'
           '<w:spacing w:before="60" w:after="60" w:line="360" w:lineRule="auto"/>' % (TEXT_W // 2, TEXT_W))
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % (ppr, runs("\t" + text + "\t(" + num + ")", shade=True))


class Media:
    def __init__(self):
        self.n = 0; self.rels = []
    def add(self, path):
        self.n += 1
        name = "f26_image%d.png" % self.n
        im = Image.open(path)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); im = bg
        im.save(os.path.join(U, "word", "media", name))
        rid = "rIdF26_%d" % self.n
        self.rels.append((rid, "media/" + name))
        return rid, name


def figure(media, path, width_in, num, title, uid):
    rid, name = media.add(path)
    w, h = Image.open(path).size
    cx = int(width_in * 914400); cy = int(cx * h / w)
    draw = ('<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
            '<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="%d" name="Picture %d"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            '<pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>') % (cx, cy, 2000 + uid, 2000 + uid, 2000 + uid, name, rid, cx, cy)
    p1 = '<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr><w:r>%s</w:r></w:p>' % draw
    p2 = P("Figure %s: %s" % (num, title), jc="center", line=360, before=60, after=200)
    return p1 + p2


def table(rows, widths, num, title, size=20, header=True, align=None):
    tot = sum(widths)
    cap = P("Table %s: %s" % (num, title), jc="center", line=360, before=120, after=60, keep=True)
    grid = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)
    trs = []
    nrows = len(rows)
    for ri, row in enumerate(rows):
        tcs = []
        for ci, (cell, w) in enumerate(zip(row, widths)):
            jc = "center" if (align is None or align[ci] == "c") else ("left" if align[ci] == "l" else "right")
            b = header and ri == 0
            keep = "<w:keepNext/>" if ri < nrows - 1 else ""
            shd = ""
            paras = "".join('<w:p><w:pPr>%s<w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/><w:jc w:val="%s"/></w:pPr>%s</w:p>'
                            % (keep if nrows <= 14 else "", jc, runs(line, size, bold=b)) for line in str(cell).split("\n"))
            tcs.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s<w:vAlign w:val="center"/></w:tcPr>%s</w:tc>' % (w, shd, paras))
        trpr = '<w:trPr><w:cantSplit/>%s<w:jc w:val="center"/></w:trPr>' % ("<w:tblHeader/>" if header and ri == 0 else "")
        trs.append("<w:tr>%s%s</w:tr>" % (trpr, "".join(tcs)))
    tbl = ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="70" w:type="dxa"/><w:right w:w="70" w:type="dxa"/></w:tblCellMar>'
           '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
           '<w:tblGrid>%s</w:tblGrid>%s</w:tbl>') % (tot, grid, "".join(trs))
    return cap + tbl + P("", line=240, after=60)


def parse(xml):
    return list(etree.fromstring("<root %s>%s</root>" % (NSDECL, xml)))


def body_xml(media):
    out = []; uid = 0; first = True
    for blk in C.BODY:
        kind = blk[0]
        if kind == "chapter":
            _, n, title = blk
            out.append(P("CHAPTER %s" % n, jc="center", bold=True, line=360, keep=True, ppr_extra="" if first else "<w:pageBreakBefore/>"))
            first = False
            out.append(P(title.upper(), jc="center", bold=True, line=360, keep=True, before=0, after=120))
        elif kind == "refs":
            out.append(P("REFERENCES", jc="center", bold=True, line=360, keep=True, after=120, ppr_extra="<w:pageBreakBefore/>"))
            for i, r in enumerate(C.REFS, 1):
                out.append('<w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/><w:ind w:left="640" w:hanging="640"/>'
                           '<w:jc w:val="both"/></w:pPr>%s</w:p>' % runs("[%d]\t%s" % (i, r), 21))
        elif kind == "h2":
            out.append(P(blk[1], jc="left", bold=True, line=360, keep=True, before=120, after=160))
        elif kind == "h3":
            out.append(P(blk[1], jc="left", bold=True, line=360, keep=True))
        elif kind == "p":
            out.append(P(blk[1]))
        elif kind == "bul":
            for b in blk[1]:
                out.append(bullet(b))
        elif kind == "eq":
            out.append(equation(blk[1], blk[2]))
        elif kind == "fig":
            uid += 1
            _, path, width, num, title = blk
            out.append(figure(media, path, width, num, title, uid))
        elif kind == "tab":
            _, num, title, rows, widths = blk[:5]
            kw = blk[5] if len(blk) > 5 else {}
            out.append(table(rows, widths, num, title, **kw))
        else:
            raise ValueError(kind)
    return "".join(out)


def set_text_keep_breaks(p, text):
    rs = p.findall("w:r", NS)
    base = None
    for r in rs:
        if r.find("w:t", NS) is not None:
            if base is None:
                base = copy.deepcopy(r.find("w:rPr", NS))
            p.remove(r)
    r = etree.Element("{%s}r" % W)
    if base is not None:
        r.append(base)
    t = etree.SubElement(r, "{%s}t" % W); t.text = text; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    br_runs = [x for x in p.findall("w:r", NS) if x.find("w:br", NS) is not None]
    if br_runs:
        br_runs[0].addprevious(r)
    else:
        p.append(r)


def set_cell(tc, txt, bold=None):
    p = tc.find("w:p", NS)
    for extra in tc.findall("w:p", NS)[1:]:
        tc.remove(extra)
    rs = p.findall("w:r", NS)
    if not rs:
        if not txt:
            return
        p.append(etree.fromstring('<w:r xmlns:w="%s"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
                                  '<w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t>x</w:t></w:r>' % W))
        rs = p.findall("w:r", NS)
    for x in rs[1:]:
        p.remove(x)
    ts = rs[0].findall("w:t", NS)
    if not ts:
        ts = [etree.SubElement(rs[0], "{%s}t" % W)]
    for t in ts[1:]:
        rs[0].remove(t)
    ts[0].text = txt; ts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    rp = rs[0].find("w:rPr", NS)
    if bold is not None and rp is not None:
        for b in rp.findall("w:b", NS) + rp.findall("w:bCs", NS):
            rp.remove(b)
        if bold:
            anchor = rp.find("w:rFonts", NS)
            (anchor.addnext(etree.Element("{%s}b" % W)) if anchor is not None else rp.insert(0, etree.Element("{%s}b" % W)))


def build(out_docx, pages=None):
    if os.path.exists(U):
        shutil.rmtree(U)
    shutil.copytree(SRC, U)
    tree = etree.parse(U + "/word/document.xml"); root = tree.getroot(); body = root.find("w:body", NS)
    els = list(body)
    assert "".join(els[107].itertext()) == "CHAPTER 1", "unexpected layout"
    assert "".join(els[312].itertext()) == "REFERENCES"
    # ---- abstract
    for idx, txt in zip((94, 95, 96), C.FRONT["abstract"]):
        set_text_keep_breaks(els[idx], txt)
    pg = pages or {}
    # ---- table of contents
    toc = els[98]; trs = toc.findall("w:tr", NS)
    front, chap_row, sec_row = trs[1], trs[2], trs[3]
    fr = front.findall("w:tc", NS)[2]
    for p, key in zip(fr.findall("w:p", NS), ("ACKNOWLEDGEMENT", "ABSTRACT", "LIST OF FIGURES", "LIST OF TABLES")):
        v = pg.get("front", {}).get(key)
        if v:
            for t in p.iter("{%s}t" % W):
                t.text = v
    for r in trs[2:]:
        toc.remove(r)
    for level, num, title in C.toc_entries():
        key = "%s %s" % (num, title) if num else title
        page = str(pg.get("toc", {}).get(key, ""))
        if level == 1:
            r = copy.deepcopy(chap_row); cells = [(num, True), (title, True), (page, False)]
        else:
            r = copy.deepcopy(sec_row); cells = [("", None), (key, level == 0), (page, False)]
        toc.append(r)
        for tc, (txt, bold) in zip(r.findall("w:tc", NS), cells):
            set_cell(tc, txt, bold)
    # ---- list of figures / tables
    for tbl, entries, key in ((els[102], C.FIGS, "fig"), (els[105], C.TABS, "tab")):
        trs = tbl.findall("w:tr", NS); proto = copy.deepcopy(trs[1])
        for r in trs[1:]:
            tbl.remove(r)
        for num, title in entries:
            r = copy.deepcopy(proto); tbl.append(r)
            for tc, txt in zip(r.findall("w:tc", NS), (num, C.strip(title), str(pg.get(key, {}).get(num, "")))):
                set_cell(tc, txt)
    # ---- body
    sect = els[-1]
    for e in els[107:-1]:
        body.remove(e)
    media = Media()
    for e in parse(body_xml(media)):
        sect.addprevious(e)
    tree.write(U + "/word/document.xml", xml_declaration=True, encoding="UTF-8", standalone=True)
    # ---- relationships: drop the old body images, add the new ones
    rel = etree.parse(U + "/word/_rels/document.xml.rels"); rr = rel.getroot()
    used = set(re.findall(r'r:(?:embed|id)="([^"]+)"', open(U + "/word/document.xml").read()))
    for e in list(rr):
        if e.get("Type").endswith("/image") and e.get("Id") not in used and not e.get("Id").startswith("rIdF26"):
            tgt = os.path.join(U, "word", e.get("Target"))
            rr.remove(e)
            if os.path.exists(tgt) and e.get("Target") not in [x.get("Target") for x in rr]:
                os.remove(tgt)
    for rid, target in media.rels:
        e = etree.SubElement(rr, "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
        e.set("Id", rid); e.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"); e.set("Target", target)
    rel.write(U + "/word/_rels/document.xml.rels", xml_declaration=True, encoding="UTF-8", standalone=True)
    for ft in ("footer1.xml", "footer2.xml"):           # schema order in sdtPr: id before docPartObj (pre-existing in the draft)
        fp = os.path.join(U, "word", ft)
        if os.path.exists(fp):
            x = open(fp).read()
            x = re.sub(r'(<w:sdtPr>)(<w:docPartObj>.*?</w:docPartObj>)(<w:id w:val="[^"]*"/>)', r'\1\3\2', x)
            open(fp, "w").write(x)
    if os.path.exists(out_docx):
        os.remove(out_docx)
    subprocess.check_call("cd %s && zip -qXrD %s ." % (U, out_docx), shell=True)
    print("built", out_docx, "media", media.n)


if __name__ == "__main__":
    pages = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
    build(sys.argv[1], pages)
