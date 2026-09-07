# cvfit, for agents

One posting and one person in, one page out, aimed at that posting and checked
before it ships.

**If someone asks you for a resume, a CV, or a version of theirs for a
particular job, read `SKILL.md` and follow it.** Eight steps, written to be
executed rather than skimmed. `TAILORING.md` is the scoring method it refers
to. Don't improvise the layout or the honesty rules; the template and the two
scripts are there so you don't have to.

This file is the entry point for any agent that reads `AGENTS.md`: Codex,
Cursor, Gemini CLI, Amp, Zed, Jules and the rest. Claude Code reads `SKILL.md`
directly through the plugin. Same procedure either way.

## Setup

```bash
pip install typst pyyaml pypdf
```

That's the whole toolchain and it needs no system packages, so it works the
same on Windows, on a locked-down laptop and in a notebook. If the machine
already has the `typst` binary and poppler, cvfit uses those instead, since
they're faster and poppler's measurements are exact.

## The two commands

```bash
python3 scripts/build_cv.py profile.yaml -o out/cv.pdf --kind job --preview
python3 scripts/verify_cv.py out/cv.pdf --profile out/cv.profile.json --master master.yaml --target target.json
```

Build fits the page and prints every item it dropped. Verify exits non-zero
when the result can't ship. `python3 tests/run.py` says whether the pipeline
works on this machine.

## What you don't get to decide

- **Facts.** Every number, title and date traces to something the person told
  you or wrote. Uncertain means ask, or leave it out.
- **Dates and titles.** `--master` fails the build if tailoring moved a date,
  grew a title or invented an employer. You may choose and reorder. You may not
  promote anyone.
- **The gate.** A non-zero exit from `verify_cv.py` isn't advisory. Fix the
  profile and build again.
- **The fit.** Write the honest assessment before tailoring, not after, and
  report a weak fit as weak. Applying anyway is the person's call.

## Where things live

| File | What it's for |
|---|---|
| `SKILL.md` | The procedure. Start here |
| `TAILORING.md` | How bullets get scored against a posting, with a worked example |
| `kinds.json` | Job, hackathon and competition: order, priorities, caps, and why |
| `examples/` | Three invented people, one of them a student with no work history |
| `templates/harvard.typ` | The layout, with the spacing constants and what they cost to find |
| `scripts/toolchain.py` | Typst and PDF reading, each with a system path and a pip path |
