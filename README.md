# cvfit

Point it at a job posting, give it whatever you've got about yourself, and it
writes a one-page resume aimed at that posting. Then it checks the result and
won't hand it over if something's wrong.

It's a [Claude Code](https://claude.com/claude-code) skill. `SKILL.md` is the
judgement, written down so it's done the same way every time. The two scripts do
the part that shouldn't be improvised: rendering and checking.

## The idea

A model should decide what goes on the page, because that's judgement and nobody
has automated it well. Code should decide how the page looks and whether it's
allowed to ship, because those are the parts where improvising costs you.

So every bullet in your profile carries a priority. When the page overflows, the
lowest ones go first; then the tool walks the dropped ones back in from the top
and keeps whatever still fits. It prints every drop. When the page comes up short
it tells you how many lines are missing and won't stretch the whitespace to hide
it, since a page that's 41% full with big gaps reads worse than one that's
honestly short.

And there's a guard. If tailoring moved a date, grew a job title, or added an
employer that isn't in your master profile, the build fails. Tailoring gets to
choose and reorder. It doesn't get to promote you.

## Install

You need Python 3.9 or newer, [Typst](https://typst.app), poppler for `pdfinfo`
and `pdftotext`, and pyyaml.

```bash
brew install typst poppler && pip install pyyaml
git clone https://github.com/MartinPuli/cvfit.git
```

As a Claude Code plugin, which is the easy way:

```
/plugin marketplace add MartinPuli/cvfit
/plugin install cvfit@cvfit
```

Or copy the repo into `~/.claude/skills/cvfit/` and it loads as a plain skill.

## Two commands

```bash
python3 scripts/build_cv.py examples/ada-lovelace.northwind.yaml -o out/cv.pdf --kind job --preview
python3 scripts/verify_cv.py out/cv.pdf --profile out/cv.profile.json --master examples/ada-lovelace.yaml --target examples/posting-northwind.json
```

Build writes the PDF, a PNG of page one so you can actually look at it, and the
effective profile: what landed on the page after caps and fitting. Verify exits
non-zero when anything's off. `python3 tests/run.py` runs the checks.

## The file you edit

One YAML per person. Open `examples/ada-lovelace.yaml`; every field has a
comment next to it. Don't have a section? Leave it out. Empty sections get
dropped at render time and the tool never invents one. Skills go in `items`,
which render as a bold label followed by plain text, so a person can scan them by
label and an ATS reads them as ordinary lines.

## Kinds

`--kind job`, `hackathon` or `competition`. Same career, three different
documents, because a hiring manager wants to know whether you've done the job
before, a hackathon organiser wants proof a past project survived past Sunday
night, and a selection committee compares ranks. `kinds.json` has each one's
section order, priority shifts, caps, and the reasoning in a `notes` field.

If there's no Experience section at all, Education goes first no matter the
kind. Projects above Education on a student's resume reads like hiding something.

## Language

Write the profile in whatever language the resume should be in. Headings are
matched by alias (`Experiencia`, `Formación`, `Compétences` all count) so
ordering and caps still work, and the page keeps the words you wrote.
`verify_cv.py --lang es` swaps in the Spanish pronoun check.
`examples/tomas-rivera.es.yaml` is the student example in Spanish.

## Format

US Letter, 0.55 inch margins, Georgia at 10.5pt with Palatino and Times New
Roman behind it. Georgia wasn't the first pick. Charter was, until rendering the
same profile in eight faces showed it running 63pt longer than Times, about five
lines, which on a one-pager is a whole bullet. One column, no tables, no
graphics, so an ATS gets plain text. Name centred, one contact line, upper-case
headings with a rule under them, dates in grey on the right.

The spacing is all explicit, and it took four tries to get there. Typst adds
implicit spacing between blocks, and a section whose first entry had no title row
(a skills list, say) sat 12pt lower under its rule than every other section. A
negative `v()` did nothing; an empty grid did nothing. Zeroing every implicit gap
and owning them with named constants is what finally worked. The numbers are in
the comments in `templates/harvard.typ`.

## Examples

Four files, three invented people. `ada-lovelace.yaml` is a standard master
profile with roles and side projects. `ada-lovelace.northwind.yaml` is her
tailored to `posting-northwind.json`, dates and titles untouched, which is what
the guard checks. `tomas-rivera.yaml` is a student with no work history, and
`tomas-rivera.es.yaml` is him in Spanish.

## Prior art

[dabydat/resume-builder-skill](https://github.com/dabydat/resume-builder-skill)
packages the Harvard and ATS rules as prose for an agent; this adds the code.
[RenderCV](https://github.com/rendercv/rendercv) is a far better typesetter and
does no tailoring at all. [Resume Forge](https://github.com/AjayLuhach/resume-forge)
is where the keyword coverage came from, minus the score, since a score turns
into something people write toward.
[silver-dev-cv](https://typst.app/universe/package/silver-dev-cv), by a
recruiter who places Argentine engineers in US startups, and its parent blog
supplied the rule in `TAILORING.md` about employers the reader has never heard of.

MIT.
