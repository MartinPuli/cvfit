# cv-converter

Give it a job posting and whatever career material you already have. It writes a
one-page Harvard-format resume aimed at that posting, renders it with Typst and
refuses to hand it over if the PDF fails its checks.

Built as a [Claude Code](https://claude.com/claude-code) skill, but the two scripts
run standalone from any shell.

## Why

Tailoring a resume by hand means re-litigating the same fight every time: which
three bullets earn their place, whether it still fits on one page, and whether the
export is text or a picture of text. This splits that in two. The model decides
what goes in, because that is judgement. The code decides how it looks and whether
it passed, because that is not.

The fitter is the part worth having. Every bullet and entry carries a priority; when
the content overflows, the lowest-priority items come out one at a time until the
page limit is met, and then the tool walks them back in from the top and restores
whatever still fits, so a coarse cut does not leave a third of the page blank.
Everything it removed gets printed. Silent truncation is how people send resumes
missing the line they cared about most.

## Install

Needs Python 3.9+, [Typst](https://typst.app), and `pdfinfo` / `pdftotext` from poppler.

```bash
brew install typst poppler          # macOS
# or: cargo install typst-cli; apt install poppler-utils
git clone https://github.com/MartinPuli/cv-converter.git
```

As a Claude Code skill, copy `SKILL.md`, `references/`, `schema/`, `scripts/` and
`templates/` into `~/.claude/skills/cv-converter/`.

## Use

```bash
python3 scripts/build_cv.py examples/profile.example.json -o out/cv.pdf --max-pages 1
python3 scripts/verify_cv.py out/cv.pdf --profile out/cv.profile.json --max-pages 1
```

`build_cv.py` writes three files: the PDF, the effective profile (what actually
survived onto the page), and optionally the generated `.typ` with `--keep-typ`.

## The data model

One JSON file per person. `schema/profile.schema.json` documents it; the shape is:

```json
{
  "name": "Ada Lovelace",
  "contact": ["London, UK", "ada@example.com", "github.com/ada"],
  "sections": [
    { "heading": "Experience", "entries": [
      { "title": "Analytical Engine Project", "subtitle": "Lead Analyst",
        "meta": "London", "date": "1842 - 1843", "priority": 90,
        "bullets": [
          { "text": "Wrote the first published algorithm for a general-purpose machine", "priority": 95 }
        ] }
    ] }
  ]
}
```

`priority` is the only field that needs explaining: higher survives the fit.

## Verification

`verify_cv.py` fails on a page count over the limit, a PDF with no extractable
text layer, a missing name or section heading, first-person pronouns, or em dashes.
Exit code is non-zero, so it works as a pre-send gate or a CI step.

## Honesty

The skill writes an `honest_fit_assessment` into the target file and the model is
told to report gaps out loud. `examples/target.canals.json` is a real posting where
the candidate is a partial fit, and the assessment says so instead of dressing a
backend engineer up as a career security engineer. A resume that oversells gets
found out in the first ten minutes of an interview, and the candidate is the one
sitting in that chair.

## Prior art

The idea of packaging resume standards as a skill comes from
[dabydat/resume-builder-skill](https://github.com/dabydat/resume-builder-skill),
which is prose guidance for an agent. This adds the deterministic half: a renderer,
a priority-driven fitter and a verifier that can fail.

## Licence

MIT.
