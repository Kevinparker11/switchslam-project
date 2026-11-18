import copy, sys
import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

src, out = sys.argv[1:3]
d = docx.Document(src)
body = d.element.body
W = qn


def ptext(p):
    return ''.join(t.text or '' for t in p.iter(W('w:t'))).strip()


kids = list(body)
# ---- locate Section 5.13 -------------------------------------------------
hi = next(i for i, e in enumerate(kids) if e.tag == W('w:p') and ptext(e) == '5.13 Discussion')
p_intro, p_cap, tbl, p_sp = kids[hi + 1], kids[hi + 2], kids[hi + 3], kids[hi + 4]
assert ptext(p_intro).startswith('Table 5.14 summarises'), ptext(p_intro)
assert ptext(p_cap).startswith('Table 5.14:'), ptext(p_cap)
assert tbl.tag == W('w:tbl') and ptext(tbl).startswith('QuestionAnswerEvidence')
assert p_sp.tag == W('w:p') and ptext(p_sp) == ''
p1, p4, p5 = kids[hi + 5], kids[hi + 6], kids[hi + 7]
assert ptext(p1).startswith('The results show that channel T')
assert ptext(p4).startswith('The detection-rule study')
assert ptext(p5).startswith('The results also have clear limits')

# ---- text of the new Discussion paragraphs (segments: (text, subscript)) ----
P_A = [("This section relates the results to the objectives of Section 1.8. A LiDAR scan taken in a corridor or a stairwell does not "
        "constrain the motion along the axis (Section 1.3): A-LOAM alone had a mean ATE of 15.8 m on Long Corridor and 66.0 m on "
        "Corridor02, and VINS-Mono alone 5.81 m on Long Corridor and 204.6 m on GEODE stairs (Table 5.6), so neither can replace the other.", False)]
P_B = [("Channel T is the core of the fusion. On Long Corridor it reduced the mean ATE to 4.53 m (F8), against 15.8 m for A-LOAM alone and "
        "5.81 m for VINS-Mono alone, and the heading correction then lowered the replayed error to about 2.0 m (Tables 5.3 and 5.6). "
        "The tensor rule on S", False), ("tt", True),
       (" and the safeguards of F21 to F24 matter mainly under faults, and channel R closed its rotation check on 3.6 % of the GEODE "
        "scans. The status guess of F35 lowered the error on Cave02 and GEODE stairs, while on Corridor02 the error was about 0.5 m "
        "above the F24 median.", False)]
P_C = [("The mean ATE of F35 was lower than that of VINS-Mono alone on all six sequences (by 39.2 to 97.5 %) and lower than that of "
        "A-LOAM alone on the four sequences on which it was run (by 39.3 to 98.0 %), and it amounted to 0.20 to 1.68 % of the path "
        "length (Tables 5.6 and 5.7). It was also lower than the published Switch-SLAM values on Multi Floor, Long Corridor and the "
        "farm route (Table 5.12), but from one run each and with different systems, so the margin is not established. Only the "
        "comparison with VINS-Mono alone on GEODE stairs is significant with the exact test (p = 0.008), and no test separates F35 "
        "from F24 (Table 5.11).", False)]
P_D = [("The detection-rule study and the F30 to F34 tests agree: the error of a switching system follows how much control of the "
        "output pose is handed to VINS-Mono, and with A-LOAM the weighted fusion gave a lower error than the switch-and-remap "
        "structure on every sequence on which both were tested.", False)]
P_E = [("The results have limits. F35 has one to three live runs per sequence, its three GEODE runs spread over 3.1 m, and all six "
        "sequences were used during development, so a test on a held-out sequence is the next step. On Cave02 the final version gave "
        "6.23 m against 4.4 m for F8 and F16, for a reason not yet identified.", False)]


def set_runs(p, segs):
    runs = p.findall(W('w:r'))
    tmpl = runs[0]
    rpr = tmpl.find(W('w:rPr'))
    for r in runs:
        if r.find(W('w:t')) is not None:
            p.remove(r)
    for text, sub in segs:
        r = OxmlElement('w:r')
        rp = copy.deepcopy(rpr)
        for va in rp.findall(W('w:vertAlign')):
            rp.remove(va)
        if sub:
            va = OxmlElement('w:vertAlign')
            va.set(W('w:val'), 'subscript')
            rp.append(va)
        r.append(rp)
        t = OxmlElement('w:t')
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        t.text = text
        r.append(t)
        brs = [x for x in p.findall(W('w:r')) if x.find(W('w:br')) is not None]
        (brs[0].addprevious(r) if brs else p.append(r))


# keep a plain template for the new paragraphs before overwriting p1
p_new_b = copy.deepcopy(p1)
p_new_c = copy.deepcopy(p1)
set_runs(p1, P_A)
set_runs(p_new_b, P_B)
set_runs(p_new_c, P_C)
set_runs(p4, P_D)
set_runs(p5, P_E)
p1.addnext(p_new_b)
p_new_b.addnext(p_new_c)
for e in (p_intro, p_cap, tbl, p_sp):
    body.remove(e)

# ---- list of tables: drop the row for Table 5.14 ---------------------------
tbls = list(body.iterchildren(W('w:tbl')))
lot = tbls[2]
rows = lot.findall(W('w:tr'))
hit = [r for r in rows if ptext(r.findall(W('w:tc'))[0]) == '5.14']
assert len(hit) == 1 and 'Main questions' in ptext(hit[0])
lot.remove(hit[0])

# ---- contents rows that no longer match the headings ------------------------
heads = {}
for e in body.iterchildren(W('w:p')):
    t = ptext(e)
    for k in ('5.5 ', '5.7 ', '5.8 '):
        if t.startswith(k) and len(t) < 90 and k not in heads:
            heads[k] = e


def setcell_text(tc, new):
    ts = list(tc.iter(W('w:t')))
    ts[0].text = new
    for t in ts[1:]:
        t.text = ''


# normalise the double space in the 5.7 heading
h57 = heads['5.7 ']
for t in h57.iter(W('w:t')):
    if '5.7  Long' in (t.text or ''):
        t.text = t.text.replace('5.7  Long', '5.7 Long')
heads_txt = {k: ptext(v) for k, v in heads.items()}
print(heads_txt)
toc = tbls[0]
for tr in toc.findall(W('w:tr'))[2:]:
    tcs = tr.findall(W('w:tc'))
    title = ptext(tcs[1])
    for k, h in heads_txt.items():
        if title.startswith(k) and title != h:
            print('TOC row', repr(title), '->', repr(h))
            setcell_text(tcs[1], h)

d.save(out)
print('saved', out)
