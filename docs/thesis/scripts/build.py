"""Build the thesis report by editing the department's template (front matter kept, body regenerated with the
template's own paragraph formats)."""
import copy, json, os, re, shutil, subprocess, sys
from lxml import etree
from PIL import Image

R = "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/rep"
FMT = "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/fmt"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
NSDECL = ('xmlns:w="%s" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
          'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
          'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"' % W)
FONT = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
TEXT_W = 8283   # page width minus margins (twips)

sys.path.insert(0, R)
import content as C


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


TOK = re.compile(r"(\*\*.+?\*\*|\*.+?\*|_\{.+?\}|\^\{.+?\}|\[\[.+?\]\]|\t)")


def runs(text, size=24, bold=False, italic=False):
    out = []
    for part in TOK.split(text):
        if not part:
            continue
        b, i, va, hl = bold, italic, None, False
        if part == "\t":
            out.append("<w:r><w:rPr>%s<w:sz w:val=\"%d\"/><w:szCs w:val=\"%d\"/></w:rPr><w:tab/></w:r>" % (FONT, size, size)); continue
        if part.startswith("**"): part, b = part[2:-2], True
        elif part.startswith("[["): part, hl = part[2:-2], True
        elif part.startswith("*") and len(part) > 2: part, i = part[1:-1], True
        elif part.startswith("_{"): part, va = part[2:-1], "subscript"
        elif part.startswith("^{"): part, va = part[2:-1], "superscript"
        rpr = FONT + ("<w:b/>" if b else "") + ("<w:i/>" if i else "") + \
            "<w:sz w:val=\"%d\"/><w:szCs w:val=\"%d\"/>" % (size, size) + ("<w:highlight w:val=\"yellow\"/>" if hl else "") + \
            ("<w:vertAlign w:val=\"%s\"/>" % va if va else "")
        out.append("<w:r><w:rPr>%s</w:rPr><w:t xml:space=\"preserve\">%s</w:t></w:r>" % (rpr, esc(part)))
    return "".join(out)


def P(text, jc="both", bold=False, size=24, line=360, before=None, after=None, keep=False, ind=None, extra_ppr="", italic=False):
    sp = '<w:spacing%s%s w:line="%d" w:lineRule="auto"/>' % (
        ' w:before="%d"' % before if before is not None else "", ' w:after="%d"' % after if after is not None else "", line)
    ppr = ("<w:keepNext/>" if keep else "") + sp + (ind or "") + ('<w:jc w:val="%s"/>' % jc if jc else "") + extra_ppr
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % (ppr, runs(text, size, bold, italic))


def page_break():
    return '<w:p><w:pPr><w:rPr>%s<w:sz w:val="24"/></w:rPr></w:pPr><w:r><w:rPr>%s<w:sz w:val="24"/></w:rPr><w:br w:type="page"/></w:r></w:p>' % (FONT, FONT)


def bullet(text):
    return ('<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
            '<w:spacing w:line="360" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr>%s</w:p>' % runs(text))


def equation(text, num):
    ppr = ('<w:tabs><w:tab w:val="center" w:pos="%d"/><w:tab w:val="right" w:pos="%d"/></w:tabs>'
           '<w:spacing w:before="60" w:after="60" w:line="360" w:lineRule="auto"/>' % (TEXT_W // 2, TEXT_W))
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % (ppr, runs("\t" + text + "\t(" + num + ")"))


class Media:
    def __init__(self, unpacked):
        self.u = unpacked; self.n = 0; self.rels = []
    def add(self, path):
        self.n += 1
        name = "rep_image%d.png" % self.n
        shutil.copy(path, os.path.join(self.u, "word", "media", name))
        rid = "rIdRep%d" % self.n
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
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>') % (cx, cy, 1000 + uid, 1000 + uid, 1000 + uid, name, rid, cx, cy)
    p1 = '<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr><w:r>%s</w:r></w:p>' % draw
    p2 = P("Figure %s: %s" % (num, title), jc="center", line=360, before=60, after=200)
    return p1 + p2


def table(rows, widths, num, title, size=21, header=True, align=None):
    tot = sum(widths)
    cap = P("Table %s: %s" % (num, title), jc="center", line=360, before=120, after=60, keep=True)
    grid = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)
    trs = []
    for ri, row in enumerate(rows):
        tcs = []
        for ci, (cell, w) in enumerate(zip(row, widths)):
            jc = "center" if (align is None or align[ci] == "c") else ("left" if align[ci] == "l" else "right")
            b = header and ri == 0
            paras = "".join('<w:p><w:pPr><w:keepNext/><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/><w:jc w:val="%s"/></w:pPr>%s</w:p>'
                            % (jc, runs(line, size, bold=b)) for line in str(cell).split("\n"))
            tcs.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>%s</w:tc>' % (w, paras))
        trpr = '<w:trPr><w:cantSplit/>%s<w:jc w:val="center"/></w:trPr>' % ("<w:tblHeader/>" if header and ri == 0 else "")
        trs.append("<w:tr>%s%s</w:tr>" % (trpr, "".join(tcs)))
    tbl = ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="70" w:type="dxa"/><w:right w:w="70" w:type="dxa"/></w:tblCellMar>'
           '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
           '<w:tblGrid>%s</w:tblGrid>%s</w:tbl>') % (tot, grid, "".join(trs))
    return cap + tbl + P("", line=240, after=60)


def parse(xml):
    root = etree.fromstring("<root %s>%s</root>" % (NSDECL, xml))
    return list(root)


def set_par_text(p, text_runs):
    """replace the runs of paragraph p by the given (text, bold) pieces, keeping the first run's rPr as the base"""
    rs = p.findall("w:r", NS)
    base = copy.deepcopy(rs[0].find("w:rPr", NS)) if rs and rs[0].find("w:rPr", NS) is not None else etree.SubElement(etree.Element("x"), "{%s}rPr" % W)
    for r in rs:
        p.remove(r)
    for k in list(p):
        if etree.QName(k).localname in ("hyperlink", "proofErr", "bookmarkStart", "bookmarkEnd"):
            p.remove(k)
    for text, bold in text_runs:
        r = etree.SubElement(p, "{%s}r" % W)
        rp = copy.deepcopy(base)
        for b in rp.findall("w:b", NS) + rp.findall("w:bCs", NS):
            rp.remove(b)
        if bold:
            rp.insert(1 if rp.find("w:rFonts", NS) is not None else 0, etree.Element("{%s}b" % W))
        if text.startswith("[[") and text.endswith("]]"):
            text = text[2:-2]; h = etree.Element("{%s}highlight" % W); h.set("{%s}val" % W, "yellow")
            anchor = rp.find("w:szCs", NS) if rp.find("w:szCs", NS) is not None else rp.find("w:sz", NS)
            if anchor is not None: anchor.addnext(h)
            else:
                lang = rp.find("w:lang", NS)
                (lang.addprevious(h) if lang is not None else rp.append(h))
        r.append(rp)
        t = etree.SubElement(r, "{%s}t" % W); t.text = text; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def fill_list_table(tbl, header_rows, proto_row, items, cols=3):
    """keep the header rows, replace the others by copies of proto_row filled with items (tuples of cell texts / (text,bold))"""
    rows = tbl.findall("w:tr", NS)
    for r in rows[header_rows:]:
        tbl.remove(r)
    for it in items:
        r = copy.deepcopy(proto_row)
        tcs = r.findall("w:tc", NS)
        for tc, val in zip(tcs, it):
            ps = tc.findall("w:p", NS)
            for extra in ps[1:]:
                tc.remove(extra)
            p = ps[0]
            if isinstance(val, tuple):
                txt, bold = val
            else:
                txt, bold = val, None
            rs = p.findall("w:r", NS)
            if not rs:
                r0 = etree.SubElement(p, "{%s}r" % W); rp = etree.SubElement(r0, "{%s}rPr" % W)
                rp.append(etree.fromstring('<w:rFonts xmlns:w="%s" w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>' % W))
                sz = etree.SubElement(rp, "{%s}sz" % W); sz.set("{%s}val" % W, "24")
                rs = [r0]
            keep = rs[0]
            for x in rs[1:]:
                p.remove(x)
            for x in keep:
                if etree.QName(x).localname not in ("rPr",):
                    keep.remove(x)
            rp = keep.find("w:rPr", NS)
            if bold is not None and rp is not None:
                for b in rp.findall("w:b", NS): rp.remove(b)
                if bold: rp.insert(1, etree.Element("{%s}b" % W))
            t = etree.SubElement(keep, "{%s}t" % W); t.text = txt; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            ind = p.find("w:pPr/w:ind", NS)
            if isinstance(val, tuple) and len(val) > 2:
                pass
        tbl.append(r)


def body_xml(media):
    out = []; uid = 0
    for blk in C.BODY:
        kind = blk[0]
        if kind == "chapter":
            _, n, title = blk
            out.append(page_break())
            out.append(P("CHAPTER %s" % n, jc="center", bold=True, line=360, keep=True))
            out.append(P(title.upper(), jc="center", bold=True, line=360, keep=True, after=120))
        elif kind == "refs":
            out.append(page_break())
            out.append(P("REFERENCES", jc="center", bold=True, line=360, keep=True, after=120))
            for i, r in enumerate(C.REFS, 1):
                out.append('<w:p><w:pPr><w:spacing w:before="60" w:after="60" w:line="240" w:lineRule="auto"/><w:ind w:left="640" w:hanging="640"/>'
                           '<w:jc w:val="both"/></w:pPr>%s</w:p>' % runs("[%d]\t%s" % (i, r), 22))
        elif kind == "h2":
            out.append(P(blk[1], jc="left", bold=True, line=360, keep=True, before=120))
        elif kind == "h3":
            out.append(P(blk[1], jc="left", bold=True, italic=False, line=360, keep=True))
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


def build(out_docx, pages=None):
    U = R + "/un"
    if os.path.exists(U):
        shutil.rmtree(U)
    shutil.copytree(FMT + "/un", U)
    tree = etree.parse(U + "/word/document.xml"); root = tree.getroot(); body = root.find("w:body", NS)
    els = list(body)
    F = C.FRONT
    # ---- cover
    set_par_text(els[0], [(F["title"], True)])
    set_par_text(els[11], [(F["name"], True)]); set_par_text(els[12], [("(%s)" % F["roll"], True)])
    set_par_text(els[25], [(F["month"], True)])
    # ---- bonafide
    set_par_text(els[31], [("This is to certify that the thesis entitled “", False), (F["title"], True), ("” submitted by “", False),
                           ("%s (%s)" % (F["name"], F["roll"]), True), ("” in partial fulfilment of the requirements for the award of the degree of ", False),
                           ("Master of Technology", True), (" in ", False), ("MANUFACTURING AND AUTOMATION", True),
                           (" is a Bonafide record of the work carried out under my guidance and supervision at Amrita School of Engineering, Coimbatore.", False)])
    set_par_text(els[33], [(F["guide"], False)]); set_par_text(els[35], [(F["designation"], False)])
    # ---- declaration
    set_par_text(els[59], [("I, ", False), ("%s (%s)" % (F["name"], F["roll"]), True), (" hereby declare that this project report, entitled as “", False),
                           (F["title"], True), ("”, is a record of the original work done by me under the guidance of ", False), (F["guide"], True),
                           (", Department of Mechanical Engineering, Amrita School of Engineering, Coimbatore and that this work has not formed the basis "
                            "for the award of any degree/diploma/associateship/fellowship or a similar award, to any candidate in any University, to the best of my knowledge.", False)])
    set_par_text(els[75], [(F["guide"], False)]); set_par_text(els[77], [(F["designation"], False), (",", False)])
    # ---- acknowledgement and abstract
    for idx, parts in zip((82, 84, 86, 88), F["ack"]):
        set_par_text(els[idx], parts)
    abs_slots = [94, 95, 96]
    for idx, txt in zip(abs_slots, F["abstract"]):
        p = els[idx]
        ind = p.find("w:pPr/w:ind", NS)
        if ind is not None:
            ind.getparent().remove(ind)
        if not p.findall("w:r", NS):
            p.append(etree.fromstring('<w:r xmlns:w="%s"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t>x</w:t></w:r>' % W))
        set_par_text(p, [(txt, False)])
    # remove trailing empty abstract paragraphs so the abstract stays on one page
    for idx in list(range(97, 105)) + [111, 112, 113, 114, 118, 119]:
        body.remove(els[idx])
    for idx in (50, 105, 108, 115):
        ppr = els[idx].find("w:pPr", NS)
        ppr.insert(0, etree.Element("{%s}pageBreakBefore" % W))
    # ---- lists (TOC, LOF, LOT)
    pg = pages or {}
    toc = els[106]; trs = toc.findall("w:tr", NS)
    hdr, front, chap_row, sec_row = trs[0], trs[1], trs[2], trs[3]
    # front-matter cell page numbers
    fr = list(front.findall("w:tc", NS))
    roman = pg.get("front", {})
    lastc = fr[2]; ps = lastc.findall("w:p", NS)
    vals = [roman.get(k, "") for k in ("ACKNOWLEDGEMENT", "ABSTRACT", "LIST OF FIGURES", "LIST OF TABLES")]
    for p, v in zip(ps, vals):
        for r in p.findall("w:r", NS):
            for t in r.findall("w:t", NS):
                t.text = v
    for r in trs[2:]:
        toc.remove(r)
    for ent in C.toc_entries():
        level, num, title = ent
        key = "%s %s" % (num, title) if num else title
        page = str(pg.get("toc", {}).get(key, ""))
        if level == 1:
            r = copy.deepcopy(chap_row); cells = [(num, True), (title, True), (page, False)]
        else:
            r = copy.deepcopy(sec_row); cells = [("", None), ("%s %s" % (num, title) if num else title, level == 0), (page, False)]
        toc.append(r)
        tcs = r.findall("w:tc", NS)
        for tc, (txt, bold) in zip(tcs, cells):
            p = tc.find("w:p", NS)
            rs = p.findall("w:r", NS)
            if not rs:
                if not txt:
                    continue
                p.append(etree.fromstring('<w:r xmlns:w="%s"><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t>x</w:t></w:r>' % W))
                rs = p.findall("w:r", NS)
            for x in rs[1:]: p.remove(x)
            rs[0].find("w:t", NS).text = txt
            rp = rs[0].find("w:rPr", NS)
            if bold is not None:
                for b in rp.findall("w:b", NS): rp.remove(b)
                if bold: rp.insert(1, etree.Element("{%s}b" % W))
    for tbl_idx, entries, key in ((110, C.FIGS, "fig"), (117, C.TABS, "tab")):
        tbl = els[tbl_idx]; trs = tbl.findall("w:tr", NS)
        proto = copy.deepcopy(trs[1])
        for r in trs[1:]: tbl.remove(r)
        for num, title in entries:
            r = copy.deepcopy(proto); tbl.append(r)
            for tc, txt in zip(r.findall("w:tc", NS), (num, title, str(pg.get(key, {}).get(num, "")))):
                p = tc.find("w:p", NS); rs = p.findall("w:r", NS)
                for x in rs[1:]: p.remove(x)
                for t in rs[0].findall("w:t", NS)[1:]: rs[0].remove(t)
                rs[0].find("w:t", NS).text = txt
    # remove the blank paragraphs between LOF table and LIST OF TABLES heading (keep the heading on a new page)
    # ---- body: drop template chapters (121 .. 398), keep the final sectPr
    sect = els[-1]
    for e in els[121:-1]:
        body.remove(e)
    media = Media(U)
    for e in parse(body_xml(media)):
        body.insert(list(body).index(sect), e)
    # make every chapter start on a new page without a blank page after the section break: drop the first page break
    first_pb = None
    idx_sect120 = list(body).index(els[120])
    nxt = list(body)[idx_sect120 + 1]
    if nxt.find(".//w:br[@w:type='page']", NS) is not None:
        body.remove(nxt)
    tree.write(U + "/word/document.xml", xml_declaration=True, encoding="UTF-8", standalone=True)
    # relationships and content types
    rel = etree.parse(U + "/word/_rels/document.xml.rels"); rr = rel.getroot()
    for rid, target in media.rels:
        e = etree.SubElement(rr, "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
        e.set("Id", rid); e.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"); e.set("Target", target)
    rel.write(U + "/word/_rels/document.xml.rels", xml_declaration=True, encoding="UTF-8", standalone=True)
    ct = open(U + "/[Content_Types].xml").read()
    if 'Extension="png"' not in ct:
        ct = ct.replace("<Default Extension=\"jpeg\"", "<Default Extension=\"png\" ContentType=\"image/png\"/><Default Extension=\"jpeg\"")
        open(U + "/[Content_Types].xml", "w").write(ct)
    # core properties: title / author
    cp = open(U + "/docProps/core.xml").read()
    cp = re.sub(r"<dc:title>.*?</dc:title>", "<dc:title>%s</dc:title>" % esc(F["title"].title()), cp)
    cp = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator>%s</dc:creator>" % F["name"], cp)
    open(U + "/docProps/core.xml", "w").write(cp)
    if os.path.exists(out_docx):
        os.remove(out_docx)
    subprocess.check_call("cd %s && zip -qXr %s ." % (U, out_docx), shell=True)
    print("built", out_docx)


if __name__ == "__main__":
    pages = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
    build(sys.argv[1], pages)
