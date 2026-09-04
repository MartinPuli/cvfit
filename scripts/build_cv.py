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
KINDS = ROOT / "kinds.json"

# Section headings are whatever the profile says, in whatever language. Kinds
# reason about canonical names, so headings are normalised for matching only;
# the page keeps the user's wording. Add a language by adding its words here.
ALIASES = {
    "experience": ["experience", "experiencia", "expérience", "experiência", "work", "employment", "trabajo"],
    "projects": ["projects", "proyectos", "projets", "projetos"],
    "education": ["education", "educación", "educacion", "formación", "formacion", "études", "formação"],
    "leadership": ["leadership", "liderazgo", "activities", "actividades", "activités", "atividades"],
    "skills": ["skills", "habilidades", "competencias", "compétences", "competências", "tecnologías", "tools"],
    "hackathons": ["hackathons", "hackatones", "hackathon", "hackatón"],
    "awards": ["awards", "premios", "prix", "prêmios", "honors", "distinciones", "competitions", "competencias"],
    "summary": ["summary", "resumen", "perfil", "résumé", "resumo"],
}


def canon(heading):
    """'Experiencia Profesional' -> 'experience'. Unknown headings map to themselves."""
    h = heading.lower()
    for key, words in ALIASES.items():
        if any(w in h for w in words):
            return key
    return h


def apply_kind(p, kind):
    """Reorder sections and shift priorities for the kind of thing being applied to.

    A job, a hackathon and a fellowship read the same career from different ends.
    The order decides what a skimming reader sees first; the boost decides what
    the fitter sacrifices when the page runs out.
    """
    allk = json.loads(KINDS.read_text())
    if kind not in allk:
        sys.exit("unknown kind: %s (have: %s)" % (kind, ", ".join(sorted(allk))))
    cfg = allk[kind]
    # A hiring manager reads a summary; a hackathon organiser skips it and looks
    # for links. The kind decides, not the profile.
    if not cfg.get("summary", False):
        p["summary"] = ""
    order = [h.lower() for h in cfg.get("section_order", [])]

    def rank(sec):
        h = canon(sec["heading"])
        for i, o in enumerate(order):
            if canon(o) == h:
                return i
        return len(order)

    p["sections"].sort(key=rank)

    # No work history means a student or a career changer. Harvard puts
    # Education first for them regardless of kind, and a hiring manager reads
    # "Projects" above "Education" on a student resume as someone hiding the
    # fact. So: no Experience section, Education leads.
    heads = [canon(x["heading"]) for x in p["sections"]]
    if "experience" not in heads:
        edu = [x for x in p["sections"] if canon(x["heading"]) == "education"]
        if edu:
            p["sections"].remove(edu[0])
            p["sections"].insert(0, edu[0])
        # and projects carry the page, so they get the room a role would have had
        cfg.setdefault("caps", {})["Projects"] = [4, 2]

    # Caps: someone with a lot to tell still gets one page. Keep the top N
    # entries per section and top M bullets per entry, by priority, and say
    # what was left out. This runs before the fitter so the fitter starts from
    # an already editorial selection rather than from everything.
    capped = []
    for sec in p["sections"]:
        for key, (max_e, max_b) in cfg.get("caps", {}).items():
            if canon(key) != canon(sec["heading"]):
                continue
            ranked = sorted(sec["entries"], key=lambda e: -e["priority"])
            for e in ranked[max_e:]:
                capped.append("entry: %s: %s" % (sec["heading"], e["title"]))
            sec["entries"] = [e for e in sec["entries"] if e in ranked[:max_e]]
            for e in sec["entries"]:
                if len(e["bullets"]) > max_b:
                    keep = sorted(e["bullets"], key=lambda b: -b["priority"])[:max_b]
                    for b in e["bullets"]:
                        if b not in keep:
                            capped.append("bullet: %s: %s" % (e["title"], b["text"][:56]))
                    e["bullets"] = [b for b in e["bullets"] if b in keep]
    cfg["_capped"] = capped
    for sec in p["sections"]:
        delta = 0
        for key, val in cfg.get("boost", {}).items():
            if canon(key) == canon(sec["heading"]):
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
    """JSON or YAML. YAML is the editable one: comments, no quoting, no commas."""
    raw = Path(path).read_text()
    if str(path).lower().endswith((".yaml", ".yml")):
        try:
            import yaml
        except ImportError:
            sys.exit("YAML profile needs pyyaml: pip install pyyaml")
        p = yaml.safe_load(raw)
    else:
        p = json.loads(raw)
    for si, s in enumerate(p["sections"]):
        s.setdefault("priority", 50)
        for ei, e in enumerate(s["entries"]):
            for k in ("title", "subtitle", "meta", "date", "text"):
                e.setdefault(k, "")
            e.setdefault("priority", 50)
            e["id"] = "e%d.%d" % (si, ei)
            e["items"] = [{"label": str(it.get("label", "")), "text": str(it.get("text", ""))}
                          for it in (e.get("items") or [])]
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
            if e["bullets"] and not bl and not e["text"] and not e.get("items"):
                continue  # entry lost every bullet, a bare title helps nobody
            entries.append({**e, "bullets": bl})
        if entries:
            out["sections"].append({**s, "entries": entries})
    return out


def to_typst(v, font, size, margin, rhythm=1.0):
    fonts = "(" + ", ".join('"%s"' % esc_str(f.strip()) for f in str(font).split(",")) + ")"

    def arr(items):
        return "(" + ", ".join(items) + ("," if len(items) == 1 else "") + ")"

    secs = []
    for s in v["sections"]:
        entries = []
        for e in s["entries"]:
            bl = arr(["[" + esc(b["text"]) + "]" for b in e["bullets"]]) if e["bullets"] else "()"
            its = arr(["(label: [%s], text: [%s])" % (esc(i["label"]), esc(i["text"]))
                       for i in e.get("items", [])]) if e.get("items") else "()"
            entries.append(
                "(title: [%s], subtitle: [%s], meta: [%s], date: [%s], text: [%s], bullets: %s, items: %s)"
                % (esc(e["title"]), esc(e["subtitle"]), esc(e["meta"]),
                   esc(e["date"]), esc(e["text"]), bl, its))
        secs.append("(heading: [%s], entries: %s)" % (esc(s["heading"]), arr(entries)))
    contact = arr(["[" + esc(c) + "]" for c in v.get("contact", [])])
    return (TEMPLATE.read_text()
            + '\n#cv(name: "%s", contact: %s, summary: [%s], sections: %s, font: %s, size: %s, margin: %s, rhythm: %s)\n'
            % (esc_str(v["name"]), contact, esc(v.get("summary", "")),
               arr(secs), fonts, size, margin, rhythm))


def fill_ratio(pdf, margin_pt):
    """How much of the usable text block the content actually occupies.

    A one-page resume that ends two inches short is not "fitted", it is
    under-written: the page limit was met by luck rather than by editing. The
    ratio is measured off the last text baseline in the PDF, not estimated.
    """
    out = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"],
                         capture_output=True, text=True).stdout
    ys = [float(m) for m in re.findall(r'yMax="([0-9.]+)"', out)]
    hs = [float(m) for m in re.findall(r"<page width=\"[0-9.]+\" height=\"([0-9.]+)\"", out)]
    if not ys or not hs:
        return None
    page_h, last = hs[0], max(ys)
    usable = page_h - 2 * margin_pt
    return max(0.0, min(1.0, (last - margin_pt) / usable))


def pt(v):
    """'0.55in' or '12pt' to points."""
    v = str(v).strip()
    if v.endswith("in"):
        return float(v[:-2]) * 72
    if v.endswith("mm"):
        return float(v[:-2]) * 72 / 25.4
    return float(v.rstrip("pt"))


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
    ap.add_argument("--target-fill", type=float, default=0.93,
                    help="how much of the text block a finished page should use, 0 to 1")
    ap.add_argument("--no-polish", action="store_true",
                    help="skip the pass that opens the rhythm to fill a short page")
    ap.add_argument("--no-restore", action="store_true", help="skip the pass that walks dropped items back in")
    ap.add_argument("--keep-typ", action="store_true")
    ap.add_argument("--preview", action="store_true",
                    help="also write a PNG of page one next to the PDF, for looking at the result")
    a = ap.parse_args()

    for tool in ("typst", "pdfinfo"):
        if not shutil.which(tool):
            sys.exit("missing dependency: " + tool)

    p = load(a.profile)
    # a `style` block in the profile sets the defaults; flags still win
    st = p.get("style") or {}
    if a.font == ap.get_default("font") and st.get("font"):
        a.font = st["font"]
    if a.size == ap.get_default("size") and st.get("size"):
        a.size = str(st["size"])
    if a.margin == ap.get_default("margin") and st.get("margin"):
        a.margin = str(st["margin"])
    cfg = apply_kind(p, a.kind) if a.kind else None
    out = Path(a.out)
    dropped, log = set(), []

    rhythm = [1.0]

    def render():
        src = to_typst(view(p, dropped), a.font, a.size, a.margin, rhythm[0])
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

    # Polish: the content is settled, so spend whatever page is left on air rather
    # than leaving a hole under the last line. Bounded, and it never overflows,
    # because every step is compiled and measured.
    margin_pt = pt(a.margin)
    fill = fill_ratio(out, margin_pt)
    polished = False
    # Only polish a page that is already nearly full. Opening the rhythm on a
    # half-empty page turns missing content into decorative whitespace, which
    # reads worse than the gap it was meant to hide.
    POLISH_FLOOR, POLISH_CEIL = 0.70, 1.45
    if fill is not None and not a.no_polish and pages <= a.max_pages and fill >= POLISH_FLOOR:
        best = (rhythm[0], src, pages, fill)
        step = 1.0
        while step < POLISH_CEIL:
            step = round(step + 0.06, 2)
            rhythm[0] = step
            src2, pages2 = render()
            f2 = fill_ratio(out, margin_pt)
            if pages2 > a.max_pages or f2 is None:
                break
            if f2 <= a.target_fill + 0.02:
                best = (step, src2, pages2, f2)
            else:
                break
        rhythm[0], src, pages, fill = best
        polished = rhythm[0] > 1.0
        render()

    final = view(p, dropped)
    if a.keep_typ:
        out.with_suffix(".typ").write_text(src)
    effp = out.with_suffix(".profile.json")
    effp.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n")

    if cfg:
        print("kind: %s" % cfg["label"])
        print("  leads with: %s" % cfg["lead_with"])
        if cfg.get("_capped"):
            print("  caps left out %d item(s) (still in the master profile):" % len(cfg["_capped"]))
            for c in cfg["_capped"]:
                print("    - " + c)
    if a.preview and shutil.which("pdftoppm"):
        stem = out.with_suffix("")
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-singlefile", "-f", "1", "-l", "1",
                        str(out), str(stem)], capture_output=True)
        print("preview: %s.png" % stem)

    print("%s  %d page(s)" % (out, pages))
    if fill is not None:
        bar = "#" * int(round(fill * 30))
        print("page fill: %3.0f%%  [%-30s]" % (fill * 100, bar))
        if polished:
            print("polish opened the rhythm to %.2fx to use the space left over" % rhythm[0])
        if fill < 0.70:
            missing = int(round((a.target_fill - fill) * 46))
            print("  short by roughly %d lines. Polish stays off below 70%% on purpose:" % missing)
            print("  write another bullet, do not stretch the whitespace.")
        elif fill < 0.85:
            print("  there is room for a line or two more if you have one.")
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
