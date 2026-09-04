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

## Kinds

The same career reads differently depending on what it is aimed at, so `--kind`
changes section order and what the fitter drops first:

```bash
python3 scripts/build_cv.py profile.json -o out/cv.pdf --kind hackathon
```

| Kind | Order it produces |
|---|---|
| `job` | Experience, Projects, Education, Skills |
| `hackathon` | Hackathons and Projects first, then Experience, Education, Leadership |
| `competition` | Awards, Education, Projects, Experience, Leadership |

A hackathon organiser reading thousands of applications wants evidence that a
past project outlived its weekend. A hiring manager wants to know whether this
person has done the job before. A selection committee compares candidates against
each other, so `1st of 151` carries weight that "won a hackathon" does not. Same
material, three documents.

## Typography

Georgia at 10.5pt, falling back to Palatino and Times New Roman. That is a
measurement, not a preference: rendering the same profile in eight faces, Charter
ran 63pt longer than Times New Roman, about five lines, enough to cost a bullet on
a one-page resume. Georgia lands within 15pt of Times, ships on every Windows and
macOS machine, and was drawn for screen legibility. Pass `--font "Times New Roman"`
when the page is genuinely full.

Leading is 0.55em with 4pt between bullets. The gap between two bullets has to
exceed the gap between wrapped lines inside one bullet, or the list stops reading
as a list.

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

One file per person, YAML or JSON. `examples/profile.example.yaml` is the one to
copy: every field has a comment beside it. Leave out any section you do not have;
the builder drops empty sections and never invents one. Skills use `items`, a bold
label and plain text, which a person scans by label and an ATS reads as lines.
`schema/profile.schema.json` documents everything; the JSON shape is:

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

## Look at it

```bash
python3 scripts/build_cv.py profile.json -o out/cv.pdf --kind job --preview
```

`--preview` writes a PNG of page one beside the PDF. The checks below catch what
a program can catch; a bullet that wraps to three lines, a heading with one thin
entry under it, or a title that pushes its date to the next line are caught by
looking. The skill makes looking a step, not an afterthought.

## Tests

```bash
make test        # or: python3 tests/run.py
```

Twenty-five checks, each of which builds a real PDF and inspects it. They cover
the one-page limit, page fill, the three kinds and their section orders, the
summary switching by kind, and every guard that must fail: two pages, first-person
pronouns, an inflated date, an inflated title, an invented employer, a page that
stops short. No test framework, no dependencies beyond the tool itself.

## Verification

`verify_cv.py` fails on a page count over the limit, a PDF with no extractable
text layer, a missing name or section heading, first-person pronouns, or em dashes.
Exit code is non-zero, so it works as a pre-send gate or a CI step.

## Caps

Someone with a lot to tell still gets one page. Each kind sets caps, `[max
entries, max bullets per entry]` per section, applied by priority before fitting.
What the caps leave out is printed and stays in the master profile; nothing is
deleted, it is just not on this page.

## Shape

The skill decides the shape from what the person actually has: standard for
roles plus projects, no Projects section for roles alone, Education and Projects
leading for a student with no roles, and an honest "this page is thin" for
someone with only study. It never fakes a section. `references/tailoring.md`
has the table.

## Summary line

`kind: job` renders two or three lines under the contact block, no heading. It is
the most posting-sensitive text on a resume, so it gets rewritten per application
rather than kept in the master. `hackathon` and `competition` switch it off:
organisers and committees skim for evidence, and three lines of positioning are
three lines a working link or a ranked result would use better.

## Keyword coverage

```bash
python3 scripts/match_report.py out/cv.pdf --target target.json
```

Lists which of the posting's keywords made it onto the page and which did not.
No score, deliberately: a number invites writing to the keyword list rather than
to the truth. Each uncovered word is a question worth asking once, "is there real
work behind this", with leaving it out as the default answer.

## Honesty

Two mechanisms, one of them enforced by code.

`verify_cv.py --master` compares the tailored profile against the untailored one
and fails if a date moved, a job title grew, or an entry appeared that was not in
the master. Tailoring may choose and reorder; it may not promote anyone. Asking a
model in prose to stay honest is not enforcement, so this one is a test.

The skill also writes an `honest_fit_assessment` into the target file and the model
is told to report gaps out loud. `examples/target.canals.json` is a real posting where
the candidate is a partial fit, and the assessment says so instead of dressing a
backend engineer up as a career security engineer. A resume that oversells gets
found out in the first ten minutes of an interview, and the candidate is the one
sitting in that chair.

## Prior art

[dabydat/resume-builder-skill](https://github.com/dabydat/resume-builder-skill)
packages Harvard and ATS standards as prose guidance for an agent; this adds the
deterministic half.

[Resume Forge](https://github.com/AjayLuhach/resume-forge) keeps a single master
`resumeData.json` and emits a keyword-matched PDF from a pasted job description,
which is where the coverage report comes from.
[Resume Matcher](https://github.com/srbhr/Resume-Matcher) scores a resume against
a description using embeddings; this tool reports coverage without a score, since
a score is a target and Goodhart applies to resumes too.
[JSON Resume](https://jsonresume.org) is the closest thing to a standard schema
and is worth supporting as an import path.

[silver-dev-cv](https://typst.app/universe/package/silver-dev-cv) is a Typst CV
template written by a recruiter who places LatAm engineers in US startups. It
defaults to Times New Roman, which the font measurement here arrived at
independently, and its parent blog supplies `references/recognition.md`: when the
reader has never heard of your employer, pedigree is worth nothing and impact,
tenure and clarity have to carry the page.

The immutable-field guard came from a JSON Resume tailoring service that protects
fields from being rewritten. It is the one idea in this list that turns an honesty
rule into a failing test, which is why it is here.

## Licence

MIT.
