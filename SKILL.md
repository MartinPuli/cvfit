---
name: cv-converter
description: "Use when someone points at a job or program application and wants a resume for it. Triggers: a job posting URL, a screenshot of a posting, pasted job text, a company plus role name, or phrasings like 'adapt my CV to this', 'tailor my resume for this role', 'Harvard format resume', 'make a CV for this application'. The skill reads the posting, assembles the candidate's material from whatever sources are available (this conversation, an Obsidian vault, markdown files, an existing resume), tailors the selection to the posting, renders a Harvard-format PDF and verifies it before anyone sends it. Do not use for cover letters, LinkedIn profiles or portfolio sites."
---

# cv-converter

Turn a job posting plus scattered career material into a one-page Harvard-format resume, rendered deterministically and gated by automated checks.

The split matters: **the model decides what goes in, the code decides how it looks and whether it passed.** Judgement is not automatable and layout is not worth improvising.

## Pipeline

```
posting (url | screenshot | text)  ─┐
                                    ├─→ target.json  ─┐
career material (session, vault,   ─┘                 ├─→ profile.json ─→ build_cv.py ─→ cv.pdf
markdown, old resume, repos)                          │                        │
                                                      └── tailoring            └─→ verify_cv.py
```

## Step 1: read the posting

| Input | How |
|---|---|
| URL | Fetch it. Greenhouse, Lever, Ashby and Workday render client-side, so a plain HTTP fetch returns the page title and nothing else. When the fetch comes back nearly empty, open it in a browser and read the rendered text. |
| Screenshot | Read the image directly. |
| Pasted text | Use it as is. |
| Just a company and role | Say the posting is missing and ask for it. Do not guess requirements. |

Write `target.json`: company, what they build, role, seniority, location, must-haves quoted in the posting's own words, responsibilities, keywords, and an `honest_fit_assessment`.

**The fit assessment is not optional and it is not marketing.** Say plainly where the candidate matches and where they do not. A resume that claims a background the person lacks fails at the first interview question, and the candidate is the one sitting there.

## Step 2: assemble the profile

Pull from whatever exists, in this order of trust:

1. What the person says in the conversation, including corrections
2. An existing resume or `profile.json`
3. An Obsidian vault or markdown notes: project notes, company notes, decision records
4. Public repos and sites they name

Every number, title and date has to trace back to one of those. When something is uncertain, ask or leave it out; never round a figure up to make a bullet land.

## Step 3: pick the kind

A job, a hackathon and a fellowship read the same career from opposite ends, so
this is a decision before it is a formatting choice.

| Kind | Leads with | Treats as noise |
|---|---|---|
| `job` | Production work: what shipped, who depended on it, what it moved | Podium counts, GPA once there is real work history |
| `hackathon` | Competition record with denominators, then things live and clickable | Long employment bullets, enterprise process detail |
| `competition` | Ranked results against a named field, then academic record, then trajectory | Stack minutiae, internal tooling |

`kinds/*.json` holds the section order, the priority shifts and the reasoning.
Passing `--kind` reorders the sections and changes what the fitter sacrifices
first, so the same profile produces genuinely different documents rather than the
same one with the headings moved.

Read the `notes` field of the kind before writing bullets. A hackathon organiser
filtering thousands of applications in seconds wants evidence a past project
outlived its weekend; a hiring manager wants to know whether this person has done
the job before. Those are different bullets, not different fonts.

## Step 4: tailor

Copy the master profile, then for this specific posting:

- **Reorder sections.** Harvard's default for students is Education, Experience, Leadership and Activities, Skills and Interests. For a specialised role, a dedicated section beats a generic one: a security posting reads *Security Projects* differently from *Projects*.
- **Reorder and rewrite bullets** so the ones matching the posting's language come first. Use the posting's vocabulary only where the work genuinely matches it.
- **Set priorities.** Every bullet and entry takes `priority` (higher survives). This is what the fitter uses when the content does not fit.
- **Write the summary, when the kind wants one.** Two or three lines under the
  contact block, no heading. It is the most posting-sensitive text on the page:
  name the role in the reader's own words, then the one result that proves it.
  `kinds/*.json` decides whether it appears; a hackathon organiser skips it.
- **Cut.** A tailored resume is shorter than the master, not longer. Watch for a
  fact stated twice: `English C1` in an education bullet and again in a languages
  line costs a whole line and adds nothing.
- **Name what the reader will not recognise.** An employer, university or client
  that means nothing to the person reading is a wasted line. Say what it is:
  `Script S.A. (BBVA, Volkswagen Financial Services)` rather than `Script S.A.`
  See `references/recognition.md`; this is the most common failure in
  cross-border applications and the cheapest to fix.

Bullet rules: start with a past-tense verb, no first-person pronouns, name the domain and the stakes, use digits, and put the outcome in the same sentence as the action. `verify_cv.py` rejects pronouns and em dashes.

## Step 5: build

```bash
python3 scripts/build_cv.py profile.json -o out/cv.pdf --kind job --max-pages 1 --preview
```

The fitter drops the lowest-priority bullets first, then entries left without any, then walks the dropped items back in from the top down and restores whatever fits. It prints everything it removed and writes the effective profile next to the PDF, so what is on the page is always inspectable.

Auto-fit is a safety net, not the tailoring step. When it reports more than two
or three drops, the profile was too long and the selection should be fixed by
hand.

The build also prints page fill. Under 70% it refuses to polish and says how many
lines are missing: write another bullet. Between 70% and the target it opens the
vertical rhythm a little to use the space. At 100% there is nothing to do.

## Step 6: look at it

`--preview` writes a PNG of page one next to the PDF. Open it and read it as the
recipient would, top to bottom, before running anything else. Things the checks
cannot catch and the eye catches in two seconds:

- a bullet that wraps to three lines and should be two
- a section heading with one thin entry under it, which reads as padding
- a title so long it pushes its date onto a second line
- a word or two orphaned on the last line of a bullet
- two adjacent bullets that say the same thing with different verbs

Fix the profile, rebuild, look again. Two or three passes is normal; a resume that
looked right the first time was not looked at.

## Step 7: verify

```bash
python3 scripts/verify_cv.py out/cv.pdf --profile out/cv.profile.json \
       --master profile.json --max-pages 1
python3 scripts/match_report.py out/cv.pdf --target target.json
```

Checks the page count, that the text layer is extractable (an image-only PDF is
invisible to an ATS), that the name and every section heading survived rendering,
and that no first-person pronouns or em dashes slipped in. Non-zero exit means do
not send it.

`--master` is the guard that matters. It compares the tailored profile against the
untailored one and fails if a date moved, a job title grew, or an entry appeared
that was not in the master. Tailoring is allowed to choose and reorder; it is not
allowed to promote anyone. That check is code because prose asking a model to be
honest is not enforcement.

`match_report.py` lists which of the posting's keywords reached the page and which
did not. It gives no score on purpose: a number invites writing to the list instead
of to the truth. Treat every uncovered word as a question, "is there real work
behind this", and leave it out when the answer is no.

## Step 8: deliver

Before handing anything over, all of these must be true:

- `verify_cv.py` exited 0 with `--master` and the default fill floor
- the preview was looked at after the last rebuild, not before
- every organisation the reader will not recognise says what it is
- every number traces to something the candidate said or a document they gave
- the fit assessment in `target.json` is honest, including where the fit is weak
- `tests/run.py` is green if any script or template was touched

## Step 9: report

Hand over the PDF and say, in this order: what was dropped to make it fit, where the candidate genuinely matches the posting, and where they do not. If the honest answer is that the fit is weak, say so; deciding to apply anyway is the candidate's call, not the tool's.

## Reference

`references/harvard-format.md` has the format rules the template implements.
`references/recognition.md` covers writing for a reader who has never heard of
your employer, which is most of the problem when applying across a border.
`schema/profile.schema.json` documents every field.
`examples/` has a generic profile and a real worked example: a backend engineer applying to a senior security role, where the fit is partial and the assessment says so.
