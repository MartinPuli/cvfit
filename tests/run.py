#!/usr/bin/env python3
"""Evals for cvfit. No test runner, no dependencies beyond the tool itself.

    python3 tests/run.py

Every check builds a real PDF and inspects it, so green means the whole
pipeline works on this machine. Exit code is the number of failures.
"""
import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import toolchain

import yaml

ROOT = Path(__file__).resolve().parent.parent
BUILD, VERIFY = (ROOT / "scripts" / n for n in ("build_cv.py", "verify_cv.py"))
EX = ROOT / "examples"
ADA, ADA_NW, TOMAS, POSTING = (EX / n for n in
    ("ada-lovelace.yaml", "ada-lovelace.northwind.yaml", "tomas-rivera.yaml", "posting-northwind.json"))

results = []


def check(name, ok, detail=""):
    results.append((name, ok))
    print("  %s  %s%s" % ("ok " if ok else "FAIL", name, ("  (" + detail.strip()[-220:] + ")") if detail and not ok else ""))


def run(*args):
    r = subprocess.run([sys.executable] + [str(a) for a in args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def pages(pdf):
    return toolchain.page_count(pdf)


def text(pdf):
    return toolchain.text(pdf)


def headings(effective_json):
    return [s["heading"] for s in json.loads(Path(effective_json).read_text())["sections"]]


def load(path):
    return yaml.safe_load(Path(path).read_text())


def main():
    if not toolchain.can_render():
        print(toolchain.RENDER_HINT)
        return 1
    if not toolchain.backend():
        print(toolchain.READ_HINT)
        return 1

    with tempfile.TemporaryDirectory() as d:
        out = Path(d)

        print("three shapes build and verify")
        for label, prof, extra in (("standard", ADA, []), ("tailored", ADA_NW, ["--master", ADA]), ("student", TOMAS, [])):
            code, log = run(BUILD, prof, "-o", out / (label + ".pdf"), "--kind", "job", "--preview")
            check(label + " builds", code == 0, log)
            check(label + " is one page", pages(out / (label + ".pdf")) == 1)
            fill = re.search(r"page fill:\s+(\d+)%", log)
            check(label + " fills the page", fill is not None and int(fill.group(1)) >= 85, log)
            code, log = run(VERIFY, out / (label + ".pdf"), "--profile", out / (label + ".profile.json"), *extra)
            check(label + " passes verify", code == 0, log)
        check("preview png written", (out / "standard.png").exists())

        print("shape: a student leads with Education even for a job")
        check("student: Education first", headings(out / "student.profile.json")[0] == "Education", str(headings(out / "student.profile.json")))
        check("standard: Experience first", headings(out / "standard.profile.json")[0] == "Experience")

        print("kinds")
        orders = {}
        for k in ("job", "hackathon", "competition"):
            run(BUILD, ADA, "-o", out / ("k-%s.pdf" % k), "--kind", k)
            orders[k] = headings(out / ("k-%s.profile.json" % k))
        check("hackathon leads with Projects", "Projects" in orders["hackathon"][0], str(orders["hackathon"]))
        check("competition leads with Education", orders["competition"][0] == "Education", str(orders["competition"]))
        check("three kinds, three orders", len({tuple(v) for v in orders.values()}) == 3)
        summary = load(ADA)["summary"][:40]
        check("summary shows for job", summary in text(out / "k-job.pdf"))
        check("summary hidden for hackathon", summary not in text(out / "k-hackathon.pdf"))

        print("guards that must fail")
        run(BUILD, ADA, "-o", out / "long.pdf", "--max-pages", "5", "--no-polish", "--font", "Georgia", "--size", "13pt")
        code, log = run(VERIFY, out / "long.pdf", "--max-pages", "1", "--min-fill", "0")
        check("rejects more than one page", code != 0 and "page count" in log, log)

        bad = load(TOMAS)
        bad["sections"][1]["entries"][0]["bullets"][0] = {"text": "I built my predictor for our city", "priority": 95}
        (out / "bad.json").write_text(json.dumps(bad))
        run(BUILD, out / "bad.json", "-o", out / "bad.pdf")
        code, log = run(VERIFY, out / "bad.pdf", "--min-fill", "0")
        check("rejects first-person pronouns", code != 0 and "pronoun" in log, log)

        t = load(ADA_NW)
        for s in t["sections"]:
            for e in s["entries"]:
                if e.get("title", "").startswith("Analytical Engine"):
                    e["date"], e["subtitle"] = "2019 – Present", "Staff Engineer"
        (out / "tampered.json").write_text(json.dumps(t))
        code, log = run(VERIFY, out / "tailored.pdf", "--profile", out / "tampered.json", "--master", ADA)
        check("master guard: inflated date", code != 0 and "date changed" in log, log)
        check("master guard: inflated title", "title changed" in log, log)

        t = load(ADA_NW)
        t["sections"][1]["entries"].append({"title": "Google", "subtitle": "Staff Engineer", "date": "2020 – 2024", "bullets": ["Led search."]})
        (out / "invented.json").write_text(json.dumps(t))
        code, log = run(VERIFY, out / "tailored.pdf", "--profile", out / "invented.json", "--master", ADA)
        check("master guard: invented employer", code != 0 and "not present in the master" in log, log)

        print("fit, caps, missing sections")
        short = load(TOMAS); short["sections"] = short["sections"][:1]
        (out / "short.json").write_text(json.dumps(short))
        code, log = run(BUILD, out / "short.json", "-o", out / "short.pdf")
        check("short page: not polished, told to write more", "polish opened" not in log and "write another bullet" in log, log)
        code, log = run(VERIFY, out / "short.pdf")
        check("short page: rejected", code != 0 and "of the page" in log, log)

        big = load(ADA)
        for s in big["sections"]:
            if s["heading"] == "Experience":
                for e in s["entries"]:
                    e["bullets"] = list(e["bullets"]) + [{"text": "Filler bullet %d." % i, "priority": 10} for i in range(4)]
        (out / "big.json").write_text(json.dumps(big))
        code, log = run(BUILD, out / "big.json", "-o", out / "big.pdf", "--kind", "job")
        exp = [x for x in json.loads((out / "big.profile.json").read_text())["sections"] if x["heading"] == "Experience"][0]
        check("caps: at most 3 bullets per role", all(len(e["bullets"]) <= 3 for e in exp["entries"]))
        # A cap is a ceiling, not a purge: an entry with one real bullet keeps
        # two fillers under a cap of three. What caps guarantee is that nothing
        # real is cut while a lower-priority bullet in the same entry survives.
        real_cut = [l for l in log.splitlines() if l.strip().startswith("- bullet:") and "Filler" not in l and "caps left out" not in l]
        check("caps: only the lowest-priority bullets were cut", "Filler" in log and "caps left out 9" in log, log)
        check("caps: no real bullet was capped", not any("Filler" not in l for l in log.splitlines() if l.startswith("    - bullet:")), log)

        empty = load(ADA)
        empty["sections"] = [dict(s, entries=[]) if s["heading"] == "Projects" else s for s in empty["sections"]]
        (out / "empty.json").write_text(json.dumps(empty))
        run(BUILD, out / "empty.json", "-o", out / "empty.pdf", "--kind", "job")
        check("empty section is dropped, never rendered", "Projects" not in headings(out / "empty.profile.json"))

        print("language")
        code, log = run(BUILD, EX / "tomas-rivera.es.yaml", "-o", out / "es.pdf", "--kind", "job")
        check("spanish profile builds on one page", code == 0 and pages(out / "es.pdf") == 1, log)
        check("spanish headings are recognised: Educación leads", headings(out / "es.profile.json")[0] == "Educación", str(headings(out / "es.profile.json")))
        code, log = run(VERIFY, out / "es.pdf", "--profile", out / "es.profile.json", "--lang", "es")
        check("spanish profile passes verify --lang es", code == 0, log)
        es = load(EX / "tomas-rivera.es.yaml")
        es["sections"][1]["entries"][0]["bullets"][0] = {"text": "Yo construí mi predictor para nuestra ciudad", "priority": 95}
        (out / "es-bad.json").write_text(json.dumps(es))
        run(BUILD, out / "es-bad.json", "-o", out / "es-bad.pdf")
        code, log = run(VERIFY, out / "es-bad.pdf", "--lang", "es", "--min-fill", "0")
        check("spanish pronouns are rejected with --lang es", code != 0 and "pronoun" in log, log)

        print("runs on a machine with no system packages")
        # The two readers have to agree, or the fill number means something
        # different depending on what happens to be installed.
        real = toolchain._has_poppler
        toolchain._has_poppler = lambda: True
        a = toolchain.text_span(out / "standard.pdf") if shutil.which("pdftotext") else None
        toolchain._has_poppler = lambda: False
        b = toolchain.text_span(out / "standard.pdf") if toolchain._pypdf() else None
        toolchain._has_poppler = real
        if a and b:
            fa, fb = (a[2] - a[1]) / (a[0] - 2 * a[1]), (b[2] - b[1]) / (b[0] - 2 * b[1])
            check("poppler and pypdf agree on page fill", abs(fa - fb) < 0.01, "%.3f vs %.3f" % (fa, fb))
        else:
            check("both PDF readers present to compare", False,
                  "skipped: install poppler and pip install pypdf to run this one")
        check("a PDF reader is available", toolchain.backend() is not None)
        check("Typst is available", toolchain.can_render())
        check("AGENTS.md sends agents to SKILL.md", "SKILL.md" in (ROOT / "AGENTS.md").read_text())

        print("docs read like a person wrote them")
        SLOP = ["delve", "leverage", "seamless", "robust", "cutting-edge", "innovative", "empower", "harness",
                "streamline", "elevate", "unlock", "landscape", "journey", "tapestry", "realm", "paradigm",
                "synergy", "testament", "moreover", "furthermore", "ultimately", "utilize", "facilitate",
                "game-changer", "in today's", "it's worth noting", "at the end of the day", "first and foremost"]
        for f in ("README.md", "SKILL.md", "TAILORING.md", "AGENTS.md"):
            body = (ROOT / f).read_text(); low = body.lower()
            check(f + ": no em dashes", "\u2014" not in body)
            hits = [w for w in SLOP if re.search(r"\b" + re.escape(w) + r"\b", low)]
            check(f + ": no filler words", not hits, str(hits))
            stiff = len(re.findall(r"\b(it is|does not|do not|cannot|is not|are not)\b", low))
            check(f + ": contractions in use", stiff <= 3, "%d uncontracted forms" % stiff)

        print("keyword report")
        code, log = run(VERIFY, out / "tailored.pdf", "--profile", out / "tailored.profile.json", "--target", POSTING)
        check("reports coverage", code == 0 and "keywords on the page" in log, log)
        check("shows the fit assessment", "Strong" in log)

    print("plugin marketplace")
    check("marketplace.json is valid and points at this repo",
          json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())["plugins"][0]["source"] == ".")
    check("plugin skill is the same file as the root SKILL.md",
          (ROOT / "skills" / "cvfit" / "SKILL.md").read_text() == (ROOT / "SKILL.md").read_text(),
          "run: cp SKILL.md skills/cvfit/SKILL.md")

    failed = [r for r in results if not r[1]]
    print("\n%d checks, %d failed" % (len(results), len(failed)))
    return len(failed)


if __name__ == "__main__":
    sys.exit(main())
