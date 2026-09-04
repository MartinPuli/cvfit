# Tailoring: from a posting and a person to one page

This is the judgement step. The code can't do it and shouldn't pretend to.
It's written as a procedure so it's done the same way every time and so the
result can be explained.

## 1. Score the posting

From `target.json`, list the must-haves and the responsibilities. Give each a
weight: 3 if the posting repeats it or puts it first, 2 if it's stated once as
a requirement, 1 if it's a nice-to-have. Ten to fifteen items is normal.

## 2. Score every bullet and entry against that list

For each bullet in the master profile, note which posting items it's genuine
evidence for. Not "could be spun as", but evidence a hiring manager would accept
in an interview. Sum the weights. That number, scaled to 40 to 100, becomes the
bullet's `priority`. Entries take the max of their bullets, plus 5 if the
organisation is one the reader will recognise.

A bullet that matches nothing keeps its default and will be the first thing the
fitter drops. That's correct.

## 3. Decide the shape

| The person has | Shape |
|---|---|
| Two or more roles and side projects | Standard: Experience, Projects, Education, Skills |
| Roles, no projects | Drop Projects. Three bullets per role; the depth has to come from the work |
| Projects, no roles (student, self-taught, career changer) | Education first, then Projects with up to two bullets each, then Skills, then Leadership. The summary leads with what was built and shipped, never with what is missing |
| Neither, only study | Education with coursework and awards as entries, Leadership, Skills. Say in the report that the page is thin and name the one thing that would fix it (a shipped project with a link) |
| Far more than fits | Caps by kind trim to the top N by priority; the rest stays in the master. Nothing is deleted, it's just not on this page |

Never fake a section. An empty heading, a "Projects" entry that's a tutorial
follow-along, or an "Experience" entry that was a two-week unpaid trial all read
as exactly what they are.

## 4. Order by the kind, then cut

`kinds.json` sets section order, priority shifts and caps. Apply the kind, then
read the effective profile the builder writes and ask of every remaining line:
would the hiring manager for this posting miss it? If not, cut it by hand rather
than leaving it to the fitter.

## 5. Name what the reader won't recognise

Silver.dev, which places Argentine and Uruguayan engineers into US startups,
puts it bluntly: LatAm resumes rarely carry company names a US reader knows, so
pedigree is worth nothing and impact, tenure and clarity have to carry the page.
The rule generalises to any application that crosses a border, an industry or a
size of company.

For every organisation on the page, ask whether the reader will recognise the
name. When not, say what it's, in the title or the first bullet: the client or
parent (`Script S.A. (BBVA, Volkswagen Financial Services)`), the rank (`the
second largest private bank in Argentina`), or the category and scale (`a
wholesale distributor moving 40,000 SKUs`). Never in a separate glossary.

Source: [The No-BS Guide to Hiring LatAm Engineers](https://blog.silver.dev/2025/02/07/the-no-bs-guide-to-hiring-latam-engineers/), Silver.dev, 2025.

## 6. Write to the posting's vocabulary, honestly

Where the work is real, use the posting's words for it. "Integrated an agentic
testing pipeline into CI/CD" for a posting that says CI/CD, not "automated
testing in the build". Where the work isn't real, the word doesn't go in.
`verify_cv.py --target` lists which posting keywords reached the page; every uncovered
one is a question, "is there real work behind this", and the default answer is
no.

## 7. Rewrite the summary last

It's the most posting-sensitive text on the page and it should be written after
the selection is settled, not before. Name the role in the reader's own words,
then the one result that proves it. Two or three lines. Only for `kind: job`.

## Worked example

`examples/posting-northwind.json` is a posting; `examples/ada-lovelace.yaml` is
the master profile and `examples/ada-lovelace.northwind.yaml` is the same person
tailored to it. Diff the two: the summary is rewritten in the posting's words
(monolith, on-call, latency), the on-call bullet and the ledger role move up in
priority, and nothing else changes. Dates and titles are identical, which is
what `verify_cv.py --master` checks. `examples/tomas-rivera.yaml` is the other
shape: a student with no roles, where Education leads and projects carry it.
