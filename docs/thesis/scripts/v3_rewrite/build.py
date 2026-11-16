import sys, re, copy
import docx
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls
from xml.sax.saxutils import escape
sys.path.insert(0, '/tmp/w/v3')
from content1 import ABSTRACT, CH1, CH2
from content2 import CH3, CH4
from content3 import CH5, CH6, CELL_EDITS, ROW_DELETE, ROW_RELABEL, COL_DELETE, PHASE_ROW, ABBR_EDITS, ABBR_ADD, OLD_CITE, NEW_REFS

SRC = '/tmp/w/v3/base.docx'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/w/v3/built.docx'
d = docx.Document(SRC)
body = d.element.body
b = list(body)
NS = nsdecls('w', 'r', 'wp', 'a', 'pic')
XMLSP = '{http://www.w3.org/XML/1998/namespace}space'
BLOCKS = CH1 + CH2 + CH3 + CH4 + CH5 + CH6
CHAP_TITLE_CASE = {'INTRODUCTION': 'Introduction', 'LITERATURE REVIEW': 'Literature Review', 'METHODOLOGY': 'Methodology',
                   'TEST SETUP': 'Test Setup', 'RESULTS AND DISCUSSION': 'Results and Discussion', 'CONCLUSIONS': 'Conclusions'}

def ptext(el):
    return ''.join(t.text or '' for t in el.iter(qn('w:t')))

def strip_tags(s):
    return re.sub(r'</?(b|i|sub|sup)>', '', s)

# ------------------------------------------------------------------ 1. numbering of labels
labels = {}
kinds = {}
ch = 0
h2 = h3 = fig = tab = eq = 0
for blk in BLOCKS:
    k = blk[0]
    if k == 'ch':
        ch += 1; h2 = h3 = fig = tab = eq = 0
    elif k == 'h2':
        h2 += 1; h3 = 0; labels[blk[1]] = '%d.%d' % (ch, h2); kinds[blk[1]] = 'Section'
    elif k == 'h3':
        h3 += 1; labels[blk[1]] = '%d.%d.%d' % (ch, h2, h3); kinds[blk[1]] = 'Section'
    elif k == 'fig':
        fig += 1; labels[blk[1]] = '%d.%d' % (ch, fig); kinds[blk[1]] = 'Figure'
    elif k == 'tab':
        tab += 1; labels[blk[1]] = '%d.%d' % (ch, tab); kinds[blk[1]] = 'Table'
    elif k == 'eq':
        eq += 1; labels[blk[2]] = '%d.%d' % (ch, eq); kinds[blk[2]] = 'Equation'

def refs(s):
    def rep(m):
        full = m.group(1)
        if full.startswith('n:'):
            lab = full[2:]
            if lab not in labels: raise KeyError(lab)
            return labels[lab]
        if full not in labels: raise KeyError(full)
        return '%s %s' % (kinds[full], labels[full])
    return re.sub(r'\{((?:n:)?(?:fig|tab|sec|eq):[A-Za-z0-9_]+)\}', rep, s)

# ------------------------------------------------------------------ 2. citations: convert old numbers in reused tables, then order
def sub_in_par(p, pattern, repl_fn):
    ts = list(p.iter(qn('w:t')))
    full = ''.join(t.text or '' for t in ts)
    ms = list(re.finditer(pattern, full))
    for m in reversed(ms):
        new = repl_fn(m)
        if new is None or new == m.group(0): continue
        s, e = m.span(); pos = 0; first = True
        for t in ts:
            tt = t.text or ''; a, z = pos, pos + len(tt); pos = z
            if z <= s or a >= e: continue
            ls, le = max(s, a) - a, min(e, z) - a
            if first: t.text = tt[:ls] + new + tt[le:]; first = False
            else: t.text = tt[:ls] + tt[le:]
            t.set(XMLSP, 'preserve')

reused_tables = [blk[2] for blk in BLOCKS if blk[0] == 'tab' and isinstance(blk[2], int)]
for tid in reused_tables:
    for p in b[tid].iter(qn('w:p')):
        sub_in_par(p, r'\[(\d+)\]', lambda m: '[@%s]' % OLD_CITE[int(m.group(1))])

cite_order = []
def scan_cites(s):
    for m in re.finditer(r'\[@([^\]]+)\]', s):
        for k in m.group(1).split(','):
            k = k.strip().lstrip('@')
            if k not in cite_order: cite_order.append(k)
for blk in BLOCKS:
    k = blk[0]
    if k in ('p', 'li'): scan_cites(blk[1])
    elif k == 'fig': scan_cites(blk[-1])
    elif k == 'tab':
        scan_cites(blk[3])
        if isinstance(blk[2], dict):
            for r in blk[2]['rows']:
                for c in r: scan_cites(c)
        else:
            scan_cites(ptext(b[blk[2]]))
cnum = {k: i + 1 for i, k in enumerate(cite_order)}

def fmt_cite(keys):
    nums = sorted(set(cnum[k.strip().lstrip('@')] for k in keys.split(',')))
    out = []; i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1: j += 1
        if j - i >= 2: out.append('[%d]-[%d]' % (nums[i], nums[j]))
        else: out.extend('[%d]' % n for n in nums[i:j + 1])
        i = j + 1
    return ', '.join(out)

def cites(s):
    return re.sub(r'\[@([^\]]+)\]', lambda m: fmt_cite(m.group(1)), s)

def render(s):
    return cites(refs(s))

for tid in reused_tables:
    for p in b[tid].iter(qn('w:p')):
        sub_in_par(p, r'\[@([^\]]+)\]', lambda m: fmt_cite(m.group(1)))

# ------------------------------------------------------------------ 3. run and paragraph builders
def rpr_xml(bold, ital, sub, sup, sz):
    rp = '<w:rFonts w:cs="Times New Roman" w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
    if bold: rp += '<w:b/>'
    if ital: rp += '<w:i/>'
    rp += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz)
    if sub: rp += '<w:vertAlign w:val="subscript"/>'
    if sup: rp += '<w:vertAlign w:val="superscript"/>'
    return '<w:rPr>%s</w:rPr>' % rp

def runs_xml(markup, sz=24, bold=False):
    out = []; st = {'b': bold, 'i': False, 'sub': False, 'sup': False}
    for tok in re.split(r'(</?(?:b|i|sub|sup)>)', markup):
        if not tok: continue
        m = re.fullmatch(r'<(/?)(b|i|sub|sup)>', tok)
        if m:
            st[m.group(2)] = (m.group(1) == ''); continue
        parts = tok.split('\t')
        for pi, part in enumerate(parts):
            if pi > 0: out.append('<w:r>%s<w:tab/></w:r>' % rpr_xml(st['b'], st['i'], st['sub'], st['sup'], sz))
            if part:
                out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr_xml(st['b'], st['i'], st['sub'], st['sup'], sz), escape(part)))
    return ''.join(out)

PPR = {
    'body': '<w:pPr><w:pStyle w:val="Normal"/><w:spacing w:lineRule="auto" w:line="360"/><w:jc w:val="both"/><w:rPr/></w:pPr>',
    'li': '<w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr><w:spacing w:lineRule="auto" w:line="360"/><w:jc w:val="both"/><w:rPr/></w:pPr>',
    'h2': '<w:pPr><w:pStyle w:val="Normal"/><w:keepNext w:val="true"/><w:spacing w:lineRule="auto" w:line="360" w:before="120" w:after="160"/><w:jc w:val="left"/><w:rPr/></w:pPr>',
    'h3': '<w:pPr><w:pStyle w:val="Normal"/><w:keepNext w:val="true"/><w:spacing w:lineRule="auto" w:line="360" w:before="60" w:after="60"/><w:jc w:val="left"/><w:rPr/></w:pPr>',
    'chnum': '<w:pPr><w:pStyle w:val="Normal"/><w:keepNext w:val="true"/>%s<w:spacing w:lineRule="auto" w:line="360"/><w:jc w:val="center"/><w:rPr/></w:pPr>',
    'chtitle': '<w:pPr><w:pStyle w:val="Normal"/><w:keepNext w:val="true"/>%s<w:spacing w:lineRule="auto" w:line="360" w:before="0" w:after="120"/><w:jc w:val="center"/><w:rPr/></w:pPr>',
    'capfig': '<w:pPr><w:pStyle w:val="Normal"/><w:spacing w:lineRule="auto" w:line="360" w:before="60" w:after="200"/><w:jc w:val="center"/><w:rPr/></w:pPr>',
    'captab': '<w:pPr><w:pStyle w:val="Normal"/><w:keepNext w:val="true"/><w:spacing w:lineRule="auto" w:line="360" w:before="120" w:after="60"/><w:jc w:val="center"/><w:rPr/></w:pPr>',
    'ref': '<w:pPr><w:pStyle w:val="Normal"/><w:spacing w:lineRule="auto" w:line="240" w:before="20" w:after="20"/><w:ind w:left="640" w:hanging="640"/><w:jc w:val="both"/><w:rPr/></w:pPr>',
}
def para(kind, markup, sz=24, bold=False, pbb=False):
    ppr = PPR[kind]
    if '%s' in ppr: ppr = ppr % ('<w:pageBreakBefore w:val="true"/>' if pbb else '')
    return parse_xml('<w:p %s>%s%s</w:p>' % (NS, ppr, runs_xml(markup, sz, bold)))

_pid = [500]
def fig_par(path, width_in, descr):
    from PIL import Image
    w, h = Image.open(path).size
    cx = int(width_in * 914400); cy = int(cx * h / w)
    rid, _ = d.part.get_or_add_image(path)
    _pid[0] += 1; n = _pid[0]; ds = escape(descr, {'"': '&quot;'})
    return parse_xml(
        '<w:p %s><w:pPr><w:pStyle w:val="Normal"/><w:keepNext w:val="true"/><w:spacing w:lineRule="auto" w:line="240" w:before="120" w:after="0"/>'
        '<w:jc w:val="center"/><w:rPr/></w:pPr><w:r><w:rPr/><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="%d" name="Picture %d" descr="%s"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
        '<pic:nvPicPr><pic:cNvPr id="%d" name="Picture %d" descr="%s"/><pic:cNvPicPr><a:picLocks noChangeAspect="1" noChangeArrowheads="1"/></pic:cNvPicPr></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr bwMode="auto"><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
        % (NS, cx, cy, n, n, ds, n, n, ds, rid, cx, cy))

def cell_xml(w, markup, bold=False, sz=20, jc='left'):
    return ('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/><w:tcBorders/><w:vAlign w:val="center"/></w:tcPr>'
            '<w:p><w:pPr><w:pStyle w:val="Normal"/><w:keepNext w:val="true"/><w:widowControl w:val="false"/><w:suppressAutoHyphens w:val="true"/>'
            '<w:spacing w:lineRule="auto" w:line="240" w:before="20" w:after="20"/><w:jc w:val="%s"/><w:rPr/></w:pPr>%s</w:p></w:tc>'
            % (w, jc, runs_xml(markup, sz, bold)))

def new_table(spec):
    widths = spec['widths']; jcs = spec.get('jcs') or ['left'] * len(widths)
    grid = ''.join('<w:gridCol w:w="%d"/>' % w for w in widths)
    x = ('<w:tbl %s><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/><w:tblInd w:w="0" w:type="dxa"/>'
         '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="70" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/>'
         '<w:right w:w="70" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="04a0" w:noHBand="0" w:noVBand="1" w:firstColumn="1" w:lastRow="0" w:lastColumn="0" w:firstRow="1"/>'
         '</w:tblPr><w:tblGrid>%s</w:tblGrid>' % (NS, sum(widths), grid))
    x += '<w:tr><w:trPr><w:tblHeader w:val="true"/><w:cantSplit w:val="true"/></w:trPr>'
    x += ''.join(cell_xml(w, render(h), bold=True) for w, h in zip(widths, spec['header'])) + '</w:tr>'
    for r in spec['rows']:
        x += '<w:tr><w:trPr><w:cantSplit w:val="true"/></w:trPr>'
        x += ''.join(cell_xml(w, render(c), jc=j) for w, c, j in zip(widths, r, jcs)) + '</w:tr>'
    return parse_xml(x + '</w:tbl>')

def set_par_markup(p, markup, sz=None):
    """Replace the text runs of p by runs built from markup; keep pPr and any page-break runs (placed after the text)."""
    runs = p.findall(qn('w:r'))
    if sz is None:
        sz = 24
        for r in runs:
            s_ = r.find('.//' + qn('w:sz'))
            if s_ is not None and r.find(qn('w:t')) is not None: sz = int(s_.get(qn('w:val'))); break
    keep = [r for r in runs if r.find(qn('w:br')) is not None and r.find(qn('w:t')) is None]
    for r in runs:
        if r not in keep: p.remove(r)
    new = parse_xml('<w:p %s>%s</w:p>' % (NS, runs_xml(markup, sz)))
    anchor = keep[0] if keep else None
    for r in list(new):
        if anchor is not None: anchor.addprevious(r)
        else: p.append(r)

def renumber_eq(p, num):
    ts = list(p.iter(qn('w:t')))
    full = ''.join(t.text or '' for t in ts)
    assert re.search(r'\(\d+\.\d+\)\s*$', full), full
    sub_in_par(p, r'\(\d+\.\d+\)(?=\s*$)', lambda m: '(%s)' % num)

spacer_tpl = b[205]

# ------------------------------------------------------------------ 4. edits to reused tables
def tbl_rows(t): return t.findall(qn('w:tr'))
def cell(t, r, c): return tbl_rows(t)[r].findall(qn('w:tc'))[c]
for (tid, r, c), mk in CELL_EDITS.items():
    p = cell(b[tid], r, c).find(qn('w:p')); set_par_markup(p, render(mk))
for (tid, r, c), mk in ROW_RELABEL.items():
    p = cell(b[tid], r, c).find(qn('w:p')); set_par_markup(p, mk)
for tid, rows in ROW_DELETE.items():
    trs = tbl_rows(b[tid])
    for ri in sorted(rows, reverse=True): b[tid].remove(trs[ri])
for tid, ci in COL_DELETE.items():
    t = b[tid]
    tw = t.find(qn('w:tblPr')).find(qn('w:tblW')); total = int(tw.get(qn('w:w')))
    grid = t.find(qn('w:tblGrid')); gcs = grid.findall(qn('w:gridCol')); grid.remove(gcs[ci])
    for tr in tbl_rows(t): tr.remove(tr.findall(qn('w:tc'))[ci])
    gcs = grid.findall(qn('w:gridCol')); ws = [int(g.get(qn('w:w'))) for g in gcs]; f = total / sum(ws)
    nw = [int(round(w * f)) for w in ws]
    for g, w in zip(gcs, nw): g.set(qn('w:w'), str(w))
    for tr in tbl_rows(t):
        for tc, w in zip(tr.findall(qn('w:tc')), nw): tc.find(qn('w:tcPr')).find(qn('w:tcW')).set(qn('w:w'), str(w))
for tr in tbl_rows(b[264]):
    tcs = tr.findall(qn('w:tc'))
    if ptext(tcs[0]).strip() == PHASE_ROW[0]:
        set_par_markup(tcs[1].find(qn('w:p')), PHASE_ROW[1])

# keep the caption and the first rows of every reused table together
for tid in reused_tables:
    trs = tbl_rows(b[tid]); upto = min(6, len(trs) - 1) if len(trs) > 12 else len(trs) - 1
    for tr in trs[:upto]:
        for p in tr.iter(qn('w:p')):
            ppr = p.find(qn('w:pPr'))
            if ppr is None: ppr = parse_xml('<w:pPr %s/>' % NS); p.insert(0, ppr)
            if ppr.find(qn('w:keepNext')) is None:
                kn = parse_xml('<w:keepNext %s w:val="true"/>' % NS)
                st = ppr.find(qn('w:pStyle'))
                (st.addnext(kn) if st is not None else ppr.insert(0, kn))

# abbreviations (front matter table b[112])
abt = b[112]
for tr in tbl_rows(abt)[1:]:
    tcs = tr.findall(qn('w:tc')); key = ptext(tcs[0]).strip()
    if key in ABBR_EDITS: set_par_markup(tcs[1].find(qn('w:p')), render(ABBR_EDITS[key]))
for key, meaning in ABBR_ADD:
    rows = tbl_rows(abt)[1:]
    after = None
    for tr in rows:
        if ptext(tr.findall(qn('w:tc'))[0]).strip().lower() < key.lower(): after = tr
    nr = copy.deepcopy(rows[0]); tcs = nr.findall(qn('w:tc'))
    set_par_markup(tcs[0].find(qn('w:p')), key); set_par_markup(tcs[1].find(qn('w:p')), meaning)
    after.addnext(nr)

# abstract
for p, mk in zip((b[98], b[99], b[100]), ABSTRACT):
    set_par_markup(p, mk)

# ------------------------------------------------------------------ 5. build the new body
new = []
toc_entries = []   # (kind, no, title)
lof = []; lot = []
ch = 0
used = set()
for blk in BLOCKS:
    k = blk[0]
    if k == 'ch':
        ch += 1
        new.append(para('chnum', 'CHAPTER %d' % ch, bold=True, pbb=(ch > 1)))
        new.append(para('chtitle', blk[1], bold=True))
        toc_entries.append(('ch', str(ch), CHAP_TITLE_CASE[blk[1]]))
    elif k in ('h2', 'h3'):
        title = '%s %s' % (labels[blk[1]], blk[2])
        new.append(para(k, title, bold=True))
        if k == 'h2': toc_entries.append(('sec', '', title))
    elif k == 'p':
        new.append(para('body', render(blk[1])))
    elif k == 'li':
        new.append(para('li', render(blk[1])))
    elif k == 'eq':
        el = b[blk[1]]; used.add(blk[1]); renumber_eq(el, labels[blk[2]]); new.append(el)
    elif k == 'fig':
        lab = blk[1]; cap = render(blk[-1])
        if isinstance(blk[2], int):
            el = b[blk[2]]; used.add(blk[2]); new.append(el)
        else:
            new.append(fig_par(blk[2], blk[3], strip_tags(cap)))
        new.append(para('capfig', 'Figure %s: %s' % (labels[lab], cap)))
        lof.append((labels[lab], cap))
    elif k == 'tab':
        lab = blk[1]; cap = render(blk[3])
        new.append(para('captab', 'Table %s: %s' % (labels[lab], cap)))
        if isinstance(blk[2], int):
            el = b[blk[2]]; used.add(blk[2]); new.append(el)
        else:
            new.append(new_table(blk[2]))
        new.append(copy.deepcopy(spacer_tpl))
        lot.append((labels[lab], cap))
    else:
        raise ValueError(k)

# references
new.append(para('chtitle', 'REFERENCES', bold=True, pbb=True))
toc_entries.append(('ref', '', 'REFERENCES'))
old_refs = {}
for i in range(405, 437):
    m = re.match(r'^\[(\d+)\]', ptext(b[i]))
    num = int(m.group(1))
    import json
old_json = {x['id']: x['m'] for x in json.load(open('/tmp/w/v3/base.json')) if x['k'] == 'P'}
for i in range(405, 437):
    mk = old_json[str(i)]
    m = re.match(r'^\[(\d+)\]', mk); num = int(m.group(1))
    old_refs[OLD_CITE[num]] = mk[m.end():].lstrip('\t')
allrefs = dict(old_refs); allrefs.update(NEW_REFS)
missing = [k for k in cite_order if k not in allrefs]
assert not missing, missing
unused = [k for k in allrefs if k not in cnum]
for k in cite_order:
    new.append(para('ref', '[%d]\t%s' % (cnum[k], allrefs[k]), sz=21))

# detach the old body (from CHAPTER 1 to the end, keeping the final sectPr)
sect = b[-1]; assert sect.tag == qn('w:sectPr')
for el in b[114:-1]:
    body.remove(el)
for el in new:
    sect.addprevious(el)

# ------------------------------------------------------------------ 6. TOC, list of figures, list of tables
def set_cell_text(tc, markup, sz=None):
    ps = tc.findall(qn('w:p'))
    for extra in ps[1:]: tc.remove(extra)
    set_par_markup(ps[0], markup, sz)

toc = b[102]; rows = tbl_rows(toc)
REF_ROW_MARKUP = '<b>%s</b>' if '<b>REFERENCES</b>' in [x['m'] for x in json.load(open('/tmp/w/v3/base.json')) if x['id'].startswith('102.')] else '%s'
ch_tpl, sec_tpl, ref_tpl = copy.deepcopy(rows[2]), copy.deepcopy(rows[3]), copy.deepcopy(rows[-1])
for tr in rows[2:]: toc.remove(tr)
for kind, no, title in toc_entries:
    tr = copy.deepcopy({'ch': ch_tpl, 'sec': sec_tpl, 'ref': ref_tpl}[kind]); tcs = tr.findall(qn('w:tc'))
    if kind == 'ch':
        set_cell_text(tcs[0], '<b>%s</b>' % no); set_cell_text(tcs[1], '<b>%s</b>' % title)
    elif kind == 'ref':
        set_cell_text(tcs[1], REF_ROW_MARKUP % title)
    else:
        set_cell_text(tcs[1], title)
    set_cell_text(tcs[2], '0')
    toc.append(tr)
for tbl, entries in ((b[106], lof), (b[109], lot)):
    rows = tbl_rows(tbl); tpl = copy.deepcopy(rows[1])
    for tr in rows[1:]: tbl.remove(tr)
    for no, cap in entries:
        tr = copy.deepcopy(tpl); tcs = tr.findall(qn('w:tc'))
        set_cell_text(tcs[0], no); set_cell_text(tcs[1], cap); set_cell_text(tcs[2], '0')
        tbl.append(tr)

d.save(OUT)
print('saved', OUT, '| chapters', ch, '| figures', len(lof), '| tables', len(lot), '| references', len(cite_order), '| unused refs', unused)
