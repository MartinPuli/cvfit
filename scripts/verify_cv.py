#!/usr/bin/env python3
"""Gate a rendered CV before anyone sends it.

    python3 scripts/verify_cv.py out/cv.pdf --profile profile.json --max-pages 1

Checks page count and fill, that the text layer is extractable (an ATS reads
it), that the name and every section heading survived rendering, and that the
prose has no first-person pronouns or em dashes. With --master, fails if
tailoring moved a date, grew a title or invented an entry. With --target,
also lists which of the posting's keywords reached the page. Exits non-zero
on any failure.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

# First-person pronouns per language. A resume speaks in fragments, not in the
# first person, in every language this tool has been used in.
PRONOUNS = {
    "en": r"\b(I|I'm|I've|I'd|my|My|we|We|our|Our)\b",
    "es": r"\b([Yy]o|[Mm]i|[Mm]is|[Mm]í|[Nn]osotros|[Nn]osotras|[Nn]uestr[oa]s?)\b",
    "pt": r"\b([Ee]u|[Mm]eu|[Mm]inha|[Mm]eus|[Mm]inhas|[Nn]ós|[Nn]oss[oa]s?)\b",
    "fr": r"\b([Jj]e|[Jj]'|[Mm]on|[Mm]a|[Mm]es|[Nn]ous|[Nn]otre|[Nn]os)\b",
}


def load_profile(path):
    raw = Path(path).read_text()
    if str(path).lower().endswith((".yaml", ".yml")):
        import yaml
        return yaml.safe_load(raw)
    return json.loads(raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--profile")
    ap.add_argument("--max-pages", type=int, default=1)
    ap.add_argument("--min-fill", type=float, default=0.75,
                    help="fail when the content uses less of the page than this")
    ap.add_argument("--lang", default="en", choices=sorted(PRONOUNS), help="language of the resume, for the pronoun check")
    ap.add_argument("--target", help="posting json: also report which of its keywords reached the page")
    ap.add_argument("--master", help="the untailored profile. Fails if tailoring changed a date or title, or invented an entry.")
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

    bb = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True).stdout
    ys = [float(m) for m in re.findall(r'yMax="([0-9.]+)"', bb)]
    tops = [float(m) for m in re.findall(r'yMin="([0-9.]+)"', bb)]
    hs = [float(m) for m in re.findall(r'<page width="[0-9.]+" height="([0-9.]+)"', bb)]
    fill = None
    if ys and hs and tops:
        top = min(tops)
        fill = (max(ys) - top) / (hs[0] - 2 * top)
        if fill < a.min_fill:
            fails.append("content uses %.0f%% of the page, under the %.0f%% floor. A one-pager "
                         "that stops short was not edited to fit, it just ran out of material."
                         % (fill * 100, a.min_fill * 100))

    text = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
    if len(text.strip()) < 200:
        fails.append("text layer looks empty, an ATS would read nothing")

    if "," in text:
        fails.append("em dash present; use commas, colons or semicolons")

    hits = sorted(set(re.findall(PRONOUNS[a.lang], text)))
    if hits:
        fails.append("first-person pronouns in the text: %s" % ", ".join(hits))

    if a.profile:
        p = load_profile(a.profile)
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

    if a.master and a.profile:
        m = load_profile(a.master)
        t = load_profile(a.profile)
        ref = {}
        for s_ in m["sections"]:
            for e in s_["entries"]:
                if e.get("title"):
                    ref[e["title"].strip().lower()] = (e.get("date", ""), e.get("subtitle", ""))
        for s_ in t["sections"]:
            for e in s_["entries"]:
                if not e.get("title"):
                    continue
                k = e["title"].strip().lower()
                if k not in ref:
                    fails.append("entry not present in the master profile: %s" % e["title"])
                    continue
                d0, sub0 = ref[k]
                if e.get("date", "") != d0:
                    fails.append("date changed for %s: %r became %r" % (e["title"], d0, e.get("date", "")))
                if e.get("subtitle", "") != sub0:
                    fails.append("title changed for %s: %r became %r" % (e["title"], sub0, e.get("subtitle", "")))

    if a.target:
        # Coverage, not a score. A number invites writing to the keyword list
        # instead of to the truth; every uncovered word is a question, "is
        # there real work behind this", and the default answer is no.
        tg = json.loads(Path(a.target).read_text())
        flat = re.sub(r"\s+", " ", text).lower()
        kws = tg.get("keywords", [])
        hit = [k for k in kws if k.lower() in flat]
        print("posting: %s, %s" % (tg.get("company", "?"), tg.get("role", "?")))
        print("keywords on the page: %d of %d" % (len(hit), len(kws)))
        for k in kws:
            print("  %s  %s" % ("yes" if k in hit else "no ", k))
        if tg.get("honest_fit_assessment"):
            print("fit assessment on file: %s" % tg["honest_fit_assessment"])

    print("pages: %d" % pages)
    if fill is not None:
        print("page fill: %.0f%%" % (fill * 100))
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
