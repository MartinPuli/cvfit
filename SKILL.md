---
name: cvfit
description: "Use when someone points at a job, hackathon, fellowship or program application and wants a resume for it. Triggers: a posting URL, a screenshot of a posting, pasted posting text, a company plus role name, or phrasings like 'adapt my CV to this', 'tailor my resume for this role', 'Harvard format resume', 'make a CV for this application', 'one-page resume'. The skill reads the posting, assembles the person's material from whatever exists (the conversation, an Obsidian vault, markdown notes, an old resume, public repos), decides the right shape for that person and that posting, renders a one-page Harvard-format PDF, and evaluates it against a rubric until it passes or the gap is explained. Don't use for cover letters, LinkedIn profiles or portfolio sites."
---

# cvfit

One posting and one person in; one page out, aimed at that posting, honest, and
checked.

The split that makes it work: **the model decides what goes on the page; the
code decides how it looks and whether it may ship.** Judgement isn't
automatable and layout isn't worth improvising. Everything below is the
judgement, written down so it's done the same way every time.

```
posting (url | screenshot | text) ──→ target.json ─────┐
                                                        ├─→ tailored profile ─→ build ─→ pdf + png
person (conversation, vault, notes, ──→ master profile ─┘         ▲                       │
        old resume, repos)                                        │                       ▼
                                                                  └──── fix ◄──── evaluate (verify, look, rubric)
```

## Inputs

| Posting | How to read it |
|---|---|
| URL | Fetch it. Greenhouse, Lever, Ashby and Workday render client-side; a plain fetch returns the page title and nothing else. When that happens, open it in a browser and read the rendered text. |
| Screenshot | Read the image. |
| Pasted text | Use as is. |
| Company and role only | The posting is missing. Ask for it. Requirements are never guessed. |

| Person | Order of trust |
|---|---|
| What they say in this conversation, including corrections | 1 |
| An existing resume or profile file | 2 |
| An Obsidian vault or markdown notes: project, company and decision notes | 3 |
| Public repos and sites they name | 4 |

Every number, title and date on the page traces to one of these. Uncertain
means ask or leave out. A figure is never rounded up to make a bullet land.

## Step 1: read the position

Write `target.json`: company, what they build, role, seniority, location,
must-haves quoted in the posting's own words, responsibilities, keywords, and
`honest_fit_assessment` on this scale:

- **strong**: the person has done this job or its nearest neighbour
- **partial**: real overlap on some must-haves, clear gaps on others
- **weak**: the overlap is a stretch

The assessment is written before tailoring, not after, so it can't be talked
into a better grade by a nicely worded page. A weak fit is reported as weak;
applying anyway is the person's call.

## Step 2: read the person

Build or update the master profile: everything, untailored, YAML
(`examples/ada-lovelace.yaml` is commented field by field). Skills go in
`items`. `priority` fields can stay at default here; they are set per posting in
step 4.

Ask what is missing before writing. The four things that most often are: the
domain and stakes of each role (a bank, an SME lender, a hospital), who the end
users were, one number per role, and what each unfamiliar organisation actually
is.

## Step 3: decide the shape

This is where the skill adapts to the person rather than the person to a
template.

| The person has | Shape |
|---|---|
| Two or more roles and projects | Standard: Experience, Projects, Education, Skills |
| Roles, no projects | Drop Projects. Three bullets per role carry the depth |
| Projects, no roles (student, self-taught, changing career) | Education first, Projects with two bullets each, Skills, Leadership. The summary leads with what was built and shipped |
| Only study | Education with coursework and awards as entries, Leadership, Skills. Report that the page is thin and name the one thing that would fix it |
| Far more than fits | Caps by kind keep the top N by priority. The rest stays in the master; nothing is deleted |

Never fake a section. A "Projects" entry that's a tutorial, an "Experience"
entry that was a two-week trial, an empty heading: each reads as exactly what
it's. Three true sections beat five where two are padding.

## Step 4: pick the kind and tailor to the position

`kinds.json` holds job, hackathon and competition. Each sets
section order, priority shifts, caps, whether the summary renders, and the
reasoning in a `notes` field. Read the notes before writing a single bullet: a
hiring manager, a hackathon organiser and a selection committee read the same
career from opposite ends.

Then follow `TAILORING.md`: weight the posting's requirements, score
every bullet as evidence against them, turn scores into priorities, apply the
kind, and cut by hand anything the reader for this posting would not miss.

Write to the posting's vocabulary where the work is real and nowhere else.

## Language

The resume is written in whichever language the person asks for, and the same
rules apply in all of them. What changes and what doesn't:

- **Headings** go in the target language (`Experiencia`, `Formación`,
  `Compétences`). The builder recognises them by alias for ordering, caps and
  the Education-first rule, and renders exactly what was written. Unknown
  headings are kept and simply not reordered.
- **Dates**: the local convention, `2023 – Actualidad`, `2023 – Presente`,
  `2023 – Aujourd'hui`. Never mix languages inside one document.
- **Proper nouns and technology names stay as they are.** `Spring Boot` isn't
  translated; `Universidad Nacional de Córdoba` isn't translated into English
  either, but what it's gets explained when the reader won't know it.
- **Pronouns**: fragments, no first person, in every language. Run
  `verify_cv.py --lang es` (or `pt`, `fr`) so the check uses the right words.
- **The recognition rule works in reverse too.** A Spanish resume for a Spanish
  reader still has to say what an unknown foreign employer is.
- Don't translate a finished English resume word for word. Write it in the
  target language from the profile; the sentence rhythm is different and a
  literal translation reads as one.

`examples/tomas-rivera.es.yaml` is the Spanish version of the student example.

## Step 5: write

- Bullets: past-tense verb, what was built, the domain and stakes, the outcome,
  digits not words, no first-person pronouns, no period at the end. The verifier
  rejects pronouns and em dashes.
- **Name what the reader won't recognise.** `Script S.A.` is a wasted line;
  `Script S.A. (BBVA, Volkswagen Financial Services)` is the fact that mattered.
  `TAILORING.md` section 5 has the rule and its source; it's the most
  common failure in cross-border applications and the cheapest to fix.
- Summary last, only for `kind: job`, two or three lines: the role in the
  reader's words, then the one result that proves it.

## Step 6: build

```bash
python3 scripts/build_cv.py profile.yaml -o out/cv.pdf --kind job --max-pages 1 --preview
```

The builder applies the kind, applies caps, fits to the page limit by dropping
the lowest-priority items and then restoring what fits back in highest-priority
first, measures page fill, and opens the vertical rhythm a little when the page
is between 70% and the target. It prints everything it capped and dropped and
writes the effective profile beside the PDF, so what is on the page is always
inspectable. Under 70% it refuses to polish and says how many lines are missing.

Fitting is a safety net. More than two or three drops means the selection in
step 4 was too long; fix it there.

## Step 7: evaluate, and loop

Three checks, in this order, and the loop runs until all three pass or the
failure is explained in the report.

**Verify.** Non-zero exit means it doesn't ship.

```bash
python3 scripts/verify_cv.py out/cv.pdf --profile out/cv.profile.json --master profile.yaml --target target.json --lang en
```

`--master` is the guard that matters: it fails if tailoring moved a date, grew
a title, or invented an entry. Tailoring may choose and reorder; it may not
promote anyone. That rule is a test because asking a model in prose to stay
honest isn't enforcement.

**Look.** Open `out/cv.png` and read it top to bottom as the recipient would.
The checks catch what a program can catch. These are caught by looking:

- a bullet that wraps to three lines and should be two
- a word or two orphaned on the last line of a bullet
- a heading with one thin entry under it, which reads as padding
- a title so long it pushes its date to a second line
- two adjacent bullets saying the same thing with different verbs
- title, subtitle and bullet lines colliding or floating apart

**Score.** Every item 0, 1 or 2. Ship at all 2s, or explain each 1.

| # | Criterion |
|---|---|
| 1 | One page, fill at or above 90% |
| 2 | In the first ten seconds: name, a line that says what they are in the posting's terms, and one hard number, all above the fold |
| 3 | Every must-have the person genuinely meets is on the page, in the posting's words |
| 4 | Nothing on the page the person could not defend in an interview |
| 5 | Every organisation the reader won't know says what it's |
| 6 | Section order matches the kind and the shape decision |
| 7 | The visual list above is clean |
| 8 | `verify_cv.py` exits 0 with `--master` |
| 9 | The fit assessment is written, and honest |

A 1 on criterion 4 or 9 is never shipped. Fix the profile, rebuild, verify,
look, score again. Two or three passes is normal.

## Step 8: deliver

Hand over the PDF and say, in this order: what was capped or dropped and why,
where the person genuinely matches the posting, where they don't, and any
rubric item that isn't a 2 and why. If the fit is weak, say weak.

## Files

- `TAILORING.md`: the scoring and shape procedure, with a worked example
- `kinds.json`: order, priorities, caps and reasoning per kind
- `examples/`: three fictional people. `ada-lovelace.yaml` is the commented
  master profile; `ada-lovelace.northwind.yaml` is her tailored to
  `posting-northwind.json`; `tomas-rivera.yaml` is a student with no roles
- `tests/run.py`: the evals, `python3 tests/run.py`; green means the pipeline works on this machine
