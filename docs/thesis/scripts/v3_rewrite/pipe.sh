set -e
cd /tmp/w/v3
python3 build.py built.docx
rm -rf r1 r2; mkdir -p r1 r2
soffice --headless --convert-to pdf --outdir r1 built.docx >/dev/null 2>&1
python3 /tmp/w/setpages.py built.docx r1/built.pdf paged.docx | tail -1
soffice --headless --convert-to pdf --outdir r1 paged.docx >/dev/null 2>&1
python3 /tmp/w/setpages.py paged.docx r1/paged.pdf paged_b.docx | tail -1
python3 /tmp/w/frontrow.py paged_b.docx r1/paged.pdf paged2.docx
python3 /tmp/w/fields.py paged2.docx final.docx
soffice --headless --convert-to pdf --outdir r2 final.docx >/dev/null 2>&1
pdfinfo r2/final.pdf | grep Pages
python3 /tmp/w/pagecalc.py r2/final.pdf final.docx | tail -4
