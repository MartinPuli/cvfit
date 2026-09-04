# Harvard resume format, as implemented

From the Harvard Office of Career Services resume guidance, plus the parts an
ATS cares about. `templates/harvard.typ` implements this; changing the template
means changing this file too.

## Page

- US Letter, 0.5 to 1 inch margins. The template defaults to 0.5in.
- One page for students and early career. Two only with a decade of history.
- Single column. No tables for layout, no text boxes, no icons, no photo, no colour.
  Anything decorative is a parsing risk and adds nothing a recruiter reads.
- 10 to 12pt body. The template defaults to 10.5pt.

## Header

- Name centred at the top, larger than the body, bold, letter-spaced.
- One centred contact line below it: location, email, and the links worth clicking.
- Plain text links, no `https://`, no `mailto:`, no "Email:" prefixes.
- No street address. City and country is what matters, especially for remote roles.

## Sections

Default order for a student or recent graduate:

1. Education
2. Experience
3. Leadership and Activities
4. Skills and Interests

Move Education to the bottom once there are three or more years of full-time work.
Reorder or rename when a posting justifies it: a specialised section that matches
the role reads far better than a generic one.

Each heading is upper-case, bold, with a rule under it. Entries inside a section
run in reverse chronological order.

## Entries

Two lines, then bullets:

```
Organisation                                         Date range
Role or degree, italic                               Location, italic
• bullet
```

- Dates on the right, en dash between years, `Present` for a current role.
- No periods ending bullets. Bullets are fragments, not sentences.
- No first-person pronouns anywhere.
- Each bullet: past-tense verb, what was built, the technical context, the outcome.
  `Migrated legacy 4D systems to Java and Spring Boot for the second largest private
  bank in Argentina` beats `Responsible for migration work`.
- Digits, not words, for numbers.

## What gets a resume thrown out

- Two pages of one page of content
- Skills listed that no bullet supports
- Job titles inflated past what the offer letter said
- Metrics with no basis, invented because a bullet felt weak
- Dense text with no white space, which reads as unedited rather than thorough

## Sources

Harvard Office of Career Services resume and cover letter guidance; the
r/EngineeringResumes wiki; and the ATS behaviour documented by Greenhouse, Lever
and Workday for text extraction from PDFs.
