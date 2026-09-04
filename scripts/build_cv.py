#!/usr/bin/env python3
"""Render a profile JSON to a Harvard-format PDF, fitted to a page limit.

    python3 scripts/build_cv.py profile.json -o out/cv.pdf --max-pages 1

Fitting has two passes. It first drops the lowest-priority bullets, then any
entry left without bullets, recompiling after each removal until the page limit
is met. It then walks the dropped items back in from highest priority down,
restoring anything that still fits, so a coarse cut does not leave a third of
the page blank. Everything it dropped is printed; silent truncation never
passes unnoticed.
"""
import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "harvard.typ"
KINDS = ROOT / "kinds"


def apply_kind(p, kind):
    """Reorder sections and shift priorities for the kind of thing being applied to.

    A job, a hackathon and a fellowship read the same career from different ends.
    The order decides what a skimming reader sees first; the boost decides what
    the fitter sacrifices when the page runs out.
    """
    f = KINDS / (kind + ".json")
    if not f.exists():
        sys.exit("unknown kind: %s (have: %s)"
                 % (kind, ", ".join(sorted(x.stem for x in KINDS.glob("*.json")))))
    cfg = json.loads(f.read_text())
    # A hiring manager reads a summary; a hackathon organiser skips it and looks
    # for links. The kind decides, not the profile.
    if not cfg.get("summary", False):
        p["summary"] = ""
    order = [h.lower() for h in cfg.get("section_order", [])]

    def rank(sec):
        h = sec["heading"].lower()
        for i, o in enumerate(order):
            if o in h or h in o:
                return i
        return len(order)

    p["sections"].sort(key=rank)
    for sec in p["sections"]:
        delta = 0
        for key, val in cfg.get("boost", {}).items():
            hl, kl = sec["heading"].lower(), key.lower()
            if kl in hl or hl in kl:
                delta = val
                break
        if delta:
            sec["priority"] += delta
            for e in sec["entries"]:
                e["priority"] += delta
                for b in e["bullets"]:
                    b["priority"] += delta
    return cfg


def esc(s):
    """Escape Typst markup in user content."""
    s = str(s)
    for ch in ["\\", "#", "$", "*", "_", "`", "<", ">", "@", "~"]:
        s = s.replace(ch, "\\" + ch)
    return s.replace("[", "\\[").replace("]", "\\]")


def esc_str(s):
    """Escape for a Typst string literal rather than markup."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def load(path):
    p = json.loads(Path(path).read_text())
    for si, s in enumerate(p["sections"]):
        s.setdefault("priority", 50)
        for ei, e in enumerate(s["entries"]):
            for k in ("subtitle", "meta", "date", "text"):
                e.setdefault(k, "")
            e.setdefault("priority", 50)
            e["id"] = "e%d.%d" % (si, ei)
            bl = []
            for bi, b in enumerate(e.get("bullets", [])):
                if isinstance(b, str):
                    b = {"text": b, "priority": 50}
                bl.append({"text": b["text"], "priority": int(b.get("priority", 50)),
                           "id": "b%d.%d.%d" % (si, ei, bi)})
            e["bullets"] = bl
    return p


def view(p, dropped):
    """The profile as it will render, with dropped ids removed and orphans pruned."""
    out = {"name": p["name"], "contact": p.get("contact", []),
           "summary": p.get("summary", ""), "sections": []}
    for s in p["sections"]:
        entries = []
        for e in s["entries"]:
            if e["id"] in dropped:
                continue
            bl = [b for b in e["bullets"] if b["id"] not in dropped]
            if e["bullets"] and not bl and not e["text"]:
                continue  # entry lost every bullet, a bare title helps nobody
            entries.append({**e, "bullets": bl})
        if entries:
            out["sections"].append({**s, "entries": entries})
    return out


def to_typst(v, font, size, margin):
    fonts = "(" + ", ".join('"%s"' % esc_str(f.strip()) for f in str(font).split(",")) + ")"

    def arr(items):
        return "(" + ", ".join(items) + ("," if len(items) == 1 else "") + ")"

    secs = []
    for s in v["sections"]:
        entries = []
        for e in s["entries"]:
            bl = arr(["[" + esc(b["text"]) + "]" for b in e["bullets"]]) if e["bullets"] else "()"
            entries.append(
                "(title: [%s], subtitle: [%s], meta: [%s], date: [%s], text: [%s], bullets: %s)"
                % (esc(e["title"]), esc(e["subtitle"]), esc(e["meta"]),
                   esc(e["date"]), esc(e["text"]), bl))
        secs.append("(heading: [%s], entries: %s)" % (esc(s["heading"]), arr(entries)))
    contact = arr(["[" + esc(c) + "]" for c in v.get("contact", [])])
    return (TEMPLATE.read_text()
            + '\n#cv(name: "%s", contact: %s, summary: [%s], sections: %s, font: %s, size: %s, margin: %s)\n'
            % (esc_str(v["name"]), contact, esc(v.get("summary", "")),
               arr(secs), fonts, size, margin))


def compile_pdf(src, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "cv.typ"
        t.write_text(src)
        r = subprocess.run(["typst", "compile", "--root", str(t.parent), str(t), str(out)],
                           capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("typst failed:\n" + (r.stderr or r.stdout))
    info = subprocess.run(["pdfinfo", str(out)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    return int(m.group(1)) if m else -1


def candidates(p, dropped):
    """Droppable items, lowest priority first. Bullets go before whole entries."""
    out = []
    for s in p["sections"]:
        for e in s["entries"]:
            if e["id"] in dropped:
                continue
            live = [b for b in e["bullets"] if b["id"] not in dropped]
            for b in live:
                out.append((b["priority"], 0, b["id"], "bullet",
                            "%s: %s" % (e["title"] or s["heading"], b["text"][:56])))
            if not e["bullets"]:
                out.append((e["priority"], 1, e["id"], "entry", "%s: %s" % (s["heading"], e["title"])))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile")
    ap.add_argument("-o", "--out", default="out/cv.pdf")
    ap.add_argument("--max-pages", type=int, default=1)
    ap.add_argument("--font", default="Georgia,Palatino,Times New Roman",
                    help="comma-separated fallback chain")
    ap.add_argument("--size", default="10.5pt")
    ap.add_argument("--margin", default="0.55in")
    ap.add_argument("--kind", help="job | hackathon | competition. Reorders sections and shifts what the fitter drops first.")
    ap.add_argument("--no-restore", action="store_true", help="skip the pass that walks dropped items back in")
    ap.add_argument("--keep-typ", action="store_true")
    a = ap.parse_args()

    for tool in ("typst", "pdfinfo"):
        if not shutil.which(tool):
            sys.exit("missing dependency: " + tool)

    p = load(a.profile)
    cfg = apply_kind(p, a.kind) if a.kind else None
    out = Path(a.out)
    dropped, log = set(), []

    def render():
        src = to_typst(view(p, dropped), a.font, a.size, a.margin)
        return src, compile_pdf(src, out)

    src, pages = render()

    while pages > a.max_pages:
        cands = candidates(p, dropped)
        if not cands:
            print("fit: nothing left to drop, still %d pages" % pages, file=sys.stderr)
            break
        prio, _, cid, kind, label = cands[0]
        dropped.add(cid)
        log.append((cid, kind, label, prio))
        src, pages = render()

    restored = []
    if log and not a.no_restore:
        # highest priority first: the restore pass exists to undo an over-cut, so it
        # has to reconsider the most valuable casualty before the cheapest one
        for cid, kind, label, prio in sorted(log, key=lambda x: -x[3]):
            dropped.discard(cid)
            src2, pages2 = render()
            if pages2 <= a.max_pages:
                restored.append(cid)
                src, pages = src2, pages2
            else:
                dropped.add(cid)
                src, pages = render()

    final = view(p, dropped)
    if a.keep_typ:
        out.with_suffix(".typ").write_text(src)
    effp = out.with_suffix(".profile.json")
    effp.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n")

    if cfg:
        print("kind: %s" % cfg["label"])
        print("  leads with: %s" % cfg["lead_with"])
    print("%s  %d page(s)" % (out, pages))
    print("effective profile: %s" % effp)
    gone = [(k, l) for cid, k, l, _ in log if cid in dropped]
    if gone:
        print("fit dropped %d item(s) to reach %d page(s):" % (len(gone), a.max_pages))
        for k, l in gone:
            print("  - %s: %s" % (k, l))
    if restored:
        print("restore pass put %d item(s) back" % len(restored))
    return 0 if pages <= a.max_pages else 1


if __name__ == "__main__":
    sys.exit(main())
