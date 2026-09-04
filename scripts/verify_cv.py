#!/usr/bin/env python3
"""Gate a rendered CV before anyone sends it.

    python3 scripts/verify_cv.py out/cv.pdf --profile profile.json --max-pages 1

Checks page count, that the text layer is extractable (ATS can read it), that
the name and every section heading survived rendering, and that the prose has
no first-person pronouns or em dashes. Exits non-zero on any failure.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

PRONOUNS = r"\b(I|I'm|I've|I'd|my|My|we|We|our|Our)\b"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--profile")
    ap.add_argument("--max-pages", type=int, default=1)
    a = ap.parse_args()

    pdf = Path(a.pdf)
    if not pdf.exists():
        sys.exit("no such file: %s" % pdf)

    fails, warns = [], []

    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    pages = int(m.group(1)) if m else -1
    if pages > a.max_pages or pages < 1:
        fails.append("page count is %d, expected at most %d" % (pages, a.max_pages))

    text = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
    if len(text.strip()) < 200:
        fails.append("text layer looks empty, an ATS would read nothing")

    if "—" in text:
        fails.append("em dash present; use commas, colons or semicolons")

    hits = sorted(set(re.findall(PRONOUNS, text)))
    if hits:
        fails.append("first-person pronouns in the text: %s" % ", ".join(hits))

    if a.profile:
        p = json.loads(Path(a.profile).read_text())
        flat = re.sub(r"\s+", " ", text)
        for part in p["name"].split():
            if part.lower() not in flat.lower():
                fails.append("name fragment missing from the PDF text: %s" % part)
        for s in p["sections"]:
            if s["heading"].lower() not in flat.lower():
                fails.append("section heading missing from the PDF text: %s" % s["heading"])
        kept = sum(len(e.get("bullets", [])) for s in p["sections"] for e in s["entries"])
        if kept == 0:
            warns.append("profile has no bullets at all")

    print("pages: %d" % pages)
    print("extracted characters: %d" % len(text.strip()))
    for wmsg in warns:
        print("WARN  " + wmsg)
    if fails:
        for f in fails:
            print("FAIL  " + f)
        return 1
    print("PASS  all checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
