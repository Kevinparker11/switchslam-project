import json, re, subprocess, sys
sys.path.insert(0, "/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/rep")
import content as C
pdf = sys.argv[1]
n = int(re.search(r"Pages:\s+(\d+)", subprocess.check_output(["pdfinfo", pdf]).decode()).group(1))
pages = [subprocess.check_output(["pdftotext", "-layout", "-f", str(i), "-l", str(i), pdf, "-"]).decode() for i in range(1, n + 1)]
def roman(k):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]; s = ""
    for v, r in vals:
        while k >= v: s += r; k -= v
    return s
front = {}
for key in ("ACKNOWLEDGEMENT", "ABSTRACT", "LIST OF FIGURES", "LIST OF TABLES"):
    for i, t in enumerate(pages):
        lines = [l.strip() for l in t.splitlines() if l.strip()]
        if lines and lines[0] == key:
            front[key] = roman(i + 1); break
c1 = next(i for i, t in enumerate(pages) if re.search(r"^\s*CHAPTER 1\s*$", t, re.M) and i > 5)
def body_page(i): return i - c1 + 1
norm = lambda s: re.sub(r"\s+", " ", s).strip()
toc = {}
for level, num, title in C.toc_entries():
    key = "%s %s" % (num, title) if num else title
    if level == 1:
        pat = r"^\s*CHAPTER %s\s*$" % num
    elif level == 0:
        pat = r"^\s*REFERENCES\s*$"
    else:
        pat = r"^\s*" + re.escape(norm("%s %s" % (num, title)))[:60]
    for i in range(c1, n):
        if re.search(pat, pages[i], re.M) or (level == 2 and norm(key)[:40] in norm(pages[i]) and re.search(r"^\s*" + re.escape(num) + r"\s", pages[i], re.M)):
            toc[key] = body_page(i); break
    else:
        print("not found", key)
fig, tab = {}, {}
for num, _ in C.FIGS:
    for i in range(c1, n):
        if re.search(r"Figure %s:" % re.escape(num), pages[i]): fig[num] = body_page(i); break
    else: print("fig not found", num)
for num, _ in C.TABS:
    for i in range(c1, n):
        if re.search(r"Table %s:" % re.escape(num), pages[i]): tab[num] = body_page(i); break
    else: print("tab not found", num)
json.dump(dict(front=front, toc=toc, fig=fig, tab=tab), open(sys.argv[2], "w"), indent=1)
print(front); print(toc); print(fig); print(tab); print("total pages", n, "front", c1)
