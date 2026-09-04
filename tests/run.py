#!/usr/bin/env python3
"""Evals for cv-converter. No test framework, no extra dependencies.

    python3 tests/run.py

Each check builds a real PDF and inspects it, so a green run means the whole
pipeline works on this machine, not merely that the code parses. Exit code is
the number of failures.
"""
import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "scripts" / "build_cv.py"
VERIFY = ROOT / "scripts" / "verify_cv.py"
MATCH = ROOT / "scripts" / "match_report.py"
EX = ROOT / "examples"

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print("  %s  %s%s" % ("ok " if ok else "FAIL", name, ("  (" + detail.strip() + ")") if detail and not ok else ""))


def run(*args):
    r = subprocess.run([sys.executable] + [str(a) for a in args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def pages(pdf):
    o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", o)
    return int(m.group(1)) if m else -1


def text(pdf):
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout


def headings(profile_json):
    return [s["heading"] for s in json.loads(Path(profile_json).read_text())["sections"]]


def main():
    for tool in ("typst", "pdfinfo", "pdftotext"):
        if not shutil.which(tool):
            print("missing dependency: %s" % tool)
            return 1

    with tempfile.TemporaryDirectory() as d:
        out = Path(d)

        print("build and verify")
        code, log = run(BUILD, EX / "profile.martin-job.json", "-o", out / "job.pdf", "--kind", "job", "--preview")
        check("job profile builds", code == 0, log[-200:])
        check("job profile is one page", pages(out / "job.pdf") == 1)
        check("preview png written", (out / "job.png").exists())
        fill = re.search(r"page fill:\s+(\d+)%", log)
        check("job profile fills the page", fill is not None and int(fill.group(1)) >= 90, log[-200:])
        code, log = run(VERIFY, out / "job.pdf", "--profile", out / "job.profile.json",
                        "--master", EX / "profile.martin-master.json")
        check("job profile passes verify with the master guard", code == 0, log[-300:])

        code, log = run(BUILD, EX / "profile.example.json", "-o", out / "ex.pdf", "--kind", "job")
        check("generic example builds", code == 0, log[-200:])
        check("generic example is one page", pages(out / "ex.pdf") == 1)
        code, log = run(VERIFY, out / "ex.pdf", "--profile", out / "ex.profile.json")
        check("generic example passes verify", code == 0, log[-300:])

        print("kinds")
        orders = {}
        for k in ("job", "hackathon", "competition"):
            run(BUILD, EX / "profile.martin-canals.json", "-o", out / ("k-%s.pdf" % k), "--kind", k)
            orders[k] = headings(out / ("k-%s.profile.json" % k))
        check("job leads with Experience", orders["job"][0] == "Experience", str(orders["job"]))
        check("hackathon leads with projects", "Projects" in orders["hackathon"][0], str(orders["hackathon"]))
        check("competition leads with Education", orders["competition"][0] == "Education", str(orders["competition"]))
        check("three kinds give three different orders", len({tuple(v) for v in orders.values()}) == 3)

        run(BUILD, EX / "profile.martin-job.json", "-o", out / "s-job.pdf", "--kind", "job")
        run(BUILD, EX / "profile.martin-job.json", "-o", out / "s-hack.pdf", "--kind", "hackathon")
        summary = json.loads((EX / "profile.martin-job.json").read_text())["summary"][:40]
        check("summary shows for job", summary in text(out / "s-job.pdf"))
        check("summary hidden for hackathon", summary not in text(out / "s-hack.pdf"))

        print("guards that must fail")
        run(BUILD, EX / "profile.martin-master.json", "-o", out / "long.pdf", "--max-pages", "5", "--no-polish")
        code, log = run(VERIFY, out / "long.pdf", "--max-pages", "1", "--min-fill", "0")
        check("verify rejects a two-page pdf", code != 0 and "page count" in log, log[-200:])

        bad = json.loads((EX / "profile.example.json").read_text())
        bad["sections"][1]["entries"][0]["bullets"][0] = {"text": "I wrote my first program for our machine", "priority": 90}
        (out / "bad.json").write_text(json.dumps(bad))
        run(BUILD, out / "bad.json", "-o", out / "bad.pdf")
        code, log = run(VERIFY, out / "bad.pdf", "--min-fill", "0")
        check("verify rejects first-person pronouns", code != 0 and "pronoun" in log, log[-200:])

        t = json.loads((out / "job.profile.json").read_text())
        for s in t["sections"]:
            for e in s["entries"]:
                if e["title"].startswith("Script"):
                    e["date"] = "2019 - 2026"
                    e["subtitle"] = "Staff Engineer"
        (out / "tampered.json").write_text(json.dumps(t))
        code, log = run(VERIFY, out / "job.pdf", "--profile", out / "tampered.json",
                        "--master", EX / "profile.martin-master.json")
        check("master guard catches an inflated date", code != 0 and "date changed" in log, log[-300:])
        check("master guard catches an inflated title", "title changed" in log, log[-300:])

        t = json.loads((out / "job.profile.json").read_text())
        t["sections"][0]["entries"].append({"title": "Google", "subtitle": "Staff Engineer",
                                            "date": "2020 - 2024", "bullets": [{"text": "Led search."}]})
        (out / "invented.json").write_text(json.dumps(t))
        code, log = run(VERIFY, out / "job.pdf", "--profile", out / "invented.json",
                        "--master", EX / "profile.martin-master.json")
        check("master guard catches an invented entry", code != 0 and "not present in the master" in log, log[-300:])

        print("fit and polish")
        short = json.loads((EX / "profile.example.json").read_text())
        short["sections"] = short["sections"][:1]
        (out / "short.json").write_text(json.dumps(short))
        code, log = run(BUILD, out / "short.json", "-o", out / "short.pdf")
        check("short page is not polished", "polish opened" not in log and "write another bullet" in log, log[-300:])
        code, log = run(VERIFY, out / "short.pdf")
        check("verify rejects a short page", code != 0 and "of the page" in log, log[-200:])

        code, log = run(BUILD, EX / "profile.martin-master.json", "-o", out / "master.pdf", "--kind", "job")
        check("master profile fits by dropping, and says what", code == 0 and "dropped" in log, log[-300:])
        check("master profile lands on one page", pages(out / "master.pdf") == 1)

        print("keyword report")
        code, log = run(MATCH, out / "k-job.pdf", "--target", EX / "target.canals.json")
        check("match report runs", code == 0 and "covered" in log, log[-200:])
        check("match report shows the fit assessment", "Partial" in log)

    failed = [r for r in results if not r[1]]
    print()
    print("%d checks, %d failed" % (len(results), len(failed)))
    return len(failed)


if __name__ == "__main__":
    sys.exit(main())
