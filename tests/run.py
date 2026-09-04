#!/usr/bin/env python3
"""Evals for cv-converter. No framework, no dependencies beyond the tool itself.

    python3 tests/run.py

Every check builds a real PDF and inspects it, so green means the whole
pipeline works on this machine. Exit code is the number of failures.
"""
import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

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
    m = re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout)
    return int(m.group(1)) if m else -1


def text(pdf):
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout


def headings(effective_json):
    return [s["heading"] for s in json.loads(Path(effective_json).read_text())["sections"]]


def load(path):
    return yaml.safe_load(Path(path).read_text())


def main():
    for tool in ("typst", "pdfinfo", "pdftotext"):
        if not shutil.which(tool):
            print("missing dependency: %s" % tool)
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
        check("caps: filler is what got cut", "Filler" in log and not any("Filler" in b["text"] for e in exp["entries"] for b in e["bullets"]), log)

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

        print("keyword report")
        code, log = run(VERIFY, out / "tailored.pdf", "--profile", out / "tailored.profile.json", "--target", POSTING)
        check("reports coverage", code == 0 and "keywords on the page" in log, log)
        check("shows the fit assessment", "Strong" in log)

    failed = [r for r in results if not r[1]]
    print("\n%d checks, %d failed" % (len(results), len(failed)))
    return len(failed)


if __name__ == "__main__":
    sys.exit(main())
