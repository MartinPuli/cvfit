# cv-converter

Give it a job posting and whatever career material you already have. It writes
a one-page resume aimed at that posting, in the Harvard format, and refuses to
hand it over if the result fails its checks.

It is a [Claude Code](https://claude.com/claude-code) skill: `SKILL.md` is the
judgement, written down. The two scripts render and gate, and run from any shell.

## Why

The model decides what goes on the page, because that is judgement. The code
decides how it looks and whether it may ship, because that is not.

Every bullet carries a priority. When the page overflows, the lowest go first,
then the tool walks them back in from the top and keeps what fits. Everything it
removed is printed. When the page is short it says how many lines are missing
and refuses to stretch whitespace over the gap. A guard fails the build if
tailoring moved a date, grew a title or invented an employer: tailoring may
choose and reorder, it may not promote anyone.

## Install

Python 3.9+, [Typst](https://typst.app), poppler (`pdfinfo`, `pdftotext`), pyyaml.

```bash
brew install typst poppler && pip install pyyaml      # macOS
git clone https://github.com/MartinPuli/cv-converter.git
```

As a skill, copy the repo into `~/.claude/skills/cv-converter/`.

## Use

```bash
python3 scripts/build_cv.py examples/ada-lovelace.northwind.yaml -o out/cv.pdf --kind job --preview
python3 scripts/verify_cv.py out/cv.pdf --profile out/cv.profile.json --master examples/ada-lovelace.yaml --target examples/posting-northwind.json
```

`build` writes the PDF, a PNG of page one, and the effective profile (what
actually landed on the page). `verify` exits non-zero if anything is wrong.
`python3 tests/run.py` runs the evals.

## The file you edit

One YAML per person. `examples/ada-lovelace.yaml` has a comment beside every
field. Leave out any section you do not have; empty sections are dropped, never
invented. Skills use `items`: a bold label and plain text.

## Kinds

`--kind job | hackathon | competition`. Same career, three documents: a hiring
manager wants to know if you have done the job, an organiser wants evidence a
past project outlived its weekend, a committee compares ranks. `kinds.json`
holds each one's section order, priority shifts, caps and reasoning. With no
Experience section, Education leads whatever the kind.

## Language

Write the profile in whatever language the resume should be in. Headings are
recognised by alias (`Experiencia`, `Formación`, `Compétences`) so ordering and
caps work the same, and the page keeps your wording. `verify_cv.py --lang es`
switches the pronoun check. `examples/tomas-rivera.es.yaml` is the student
example in Spanish.

## Format

US Letter, 0.55in margins, Georgia 10.5pt with Palatino and Times New Roman as
fallbacks (measured: Charter ran five lines longer). Single column, no tables,
no graphics, so an ATS reads it as text. Name centred, one contact line,
upper-case headings with a rule, dates right-aligned in grey. Spacing is
explicit and measured; see the comments in `templates/harvard.typ`.

## Examples

Three fictional people. `ada-lovelace.yaml` is a standard master profile;
`ada-lovelace.northwind.yaml` is her tailored to `posting-northwind.json`, dates
and titles untouched; `tomas-rivera.yaml` is a student with no work history.

## Prior art

[dabydat/resume-builder-skill](https://github.com/dabydat/resume-builder-skill)
packages Harvard and ATS standards as prose for an agent; this adds the code.
[RenderCV](https://github.com/rendercv/rendercv) is the better typesetter and
does no tailoring. [Resume Forge](https://github.com/AjayLuhach/resume-forge)
inspired the keyword coverage, minus the score.
[silver-dev-cv](https://typst.app/universe/package/silver-dev-cv) and its parent
blog supplied the rule in `TAILORING.md` about employers the reader will not know.

MIT.
