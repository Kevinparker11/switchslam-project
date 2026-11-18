#!/usr/bin/env bash
# Builds the work folder the v3 report pipeline expects (its paths are fixed to /tmp/w and /tmp/w/v3) from files stored in the repo.
# Run once, then:  cd /tmp/w/v3 && bash pipe.sh        (result: /tmp/w/v3/final.docx and r2/final.pdf)
# Needs: python3 with python-docx and lxml, LibreOffice (soffice) and poppler (pdfinfo, pdftotext).
set -e
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)
T=$REPO/docs/thesis
mkdir -p /tmp/w/v3/fc
cp $T/work_v3/pagecalc.py $T/work_v3/setpages.py $T/work_v3/frontrow.py $T/work_v3/fields.py $T/work_v3/frontfields.py /tmp/w/
cp $T/work_v3/base.docx $T/work_v3/base.json /tmp/w/v3/
cp $T/work_v3/fc/* /tmp/w/v3/fc/
cp $T/scripts/v3_rewrite/build.py $T/scripts/v3_rewrite/content1.py $T/scripts/v3_rewrite/content2.py $T/scripts/v3_rewrite/content3.py $T/scripts/v3_rewrite/pipe.sh /tmp/w/v3/
echo "work folder ready: cd /tmp/w/v3 && bash pipe.sh"
