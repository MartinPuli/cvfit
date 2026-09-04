#!/usr/bin/env python3
"""Which words from the posting actually made it onto the page.

    python3 scripts/match_report.py out/cv.pdf --target target.json

Prints covered and uncovered keywords. It deliberately does not produce a score:
a single number invites gaming a resume against a keyword list, which is how
people end up claiming skills they do not have. The uncovered list is a prompt to
ask "is there real work behind this word", not an instruction to paste it in.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--target", required=True)
    a = ap.parse_args()

    text = subprocess.run(["pdftotext", a.pdf, "-"], capture_output=True, text=True).stdout
    flat = re.sub(r"\s+", " ", text).lower()
    t = json.loads(Path(a.target).read_text())
    kws = t.get("keywords", [])
    if not kws:
        sys.exit("target has no keywords")

    hit = [k for k in kws if k.lower() in flat]
    miss = [k for k in kws if k.lower() not in flat]

    print("%s > %s" % (t.get("company", "?"), t.get("role", "?")))
    print("covered %d of %d posting keywords\n" % (len(hit), len(kws)))
    for k in hit:
        print("  yes  %s" % k)
    for k in miss:
        print("  no   %s" % k)
    if t.get("honest_fit_assessment"):
        print("\nfit assessment on file:\n  %s" % t["honest_fit_assessment"])
    if miss:
        print("\nFor each uncovered word, ask whether real work backs it. If not, leave it out.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
