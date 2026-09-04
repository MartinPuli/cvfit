// Harvard Office of Career Services resume format.
// Rendered by scripts/build_cv.py. Do not edit generated .typ files, edit the profile JSON.
//
// Typography notes, since they are decisions and not defaults:
//   Georgia first, and the reason is measured rather than aesthetic. Rendering
//   the same profile in eight faces at 10.5pt, Charter ran 63pt longer than
//   Times New Roman, roughly five lines, enough to cost a bullet on a one-pager.
//   Georgia lands within 15pt of Times, ships on every Windows and macOS machine,
//   and was drawn by Matthew Carter for screen legibility. Palatino matches it on
//   length; Times New Roman is the shortest and the safest, and is the fallback.
//   Pick Times with --font when the page is genuinely full.
//   Leading is 0.5em and the gap between bullets is 4pt, deliberately larger.
//   Lines wrapped inside one bullet must sit closer together than two separate
//   bullets do, or the list stops reading as a list.
//   Vertical rhythm runs 3pt inside an entry, 7pt between entries and 13pt
//   between sections, all scaled by `rhythm`. build_cv.py raises that multiplier
//   after the content is settled, so a page that would end two inches short gets
//   the room back as air rather than leaving a hole under the last line. The ratio is what carries hierarchy: a section break has to
//   read as clearly bigger than an entry break or the page turns into one list.
//   Bullets are a two-column grid so wrapped lines align under the text rather
//   than under the bullet. A par hanging-indent reads cleaner in source but does
//   not survive into the block, which is why the grid stays.

#let date-grey = rgb("#5a5a5a")

// Every block element here is wrapped in block(above: 0pt, below: 0pt) and the
// gaps are explicit v() calls. Measured reason: with Typst's implicit block
// spacing left on, an entry with no title row (a skills list) sat 12pt lower
// under its rule than every titled entry, and neither a negative v() nor an
// empty grid could pull it back. Zeroing the implicit spacing and owning it
// with one constant brings all sections within 0.5pt of each other.
#let SECTION_GAP = 16pt

#let cv(
  name: "",
  contact: (),
  summary: "",
  sections: (),
  font: ("Georgia", "Palatino", "Times New Roman"),
  size: 10.5pt,
  margin: 0.55in,
  rhythm: 1.0,
) = {
  set document(title: name, author: name)
  set page(paper: "us-letter", margin: margin)
  set text(font: font, size: size, fill: black, hyphenate: false)
  set par(justify: false, leading: 0.55em * rhythm, spacing: 0.55em * rhythm)

  align(center)[
    #text(size: size + 7pt, weight: "bold", tracking: 1.1pt)[#upper(name)]
    #v(3.5pt * rhythm)
    #text(size: size - 1pt, fill: rgb(25, 25, 25))[#contact.join("   |   ")]
  ]
  if summary != "" {
    v(7pt * rhythm)
    // No heading. A labelled "Summary" costs a line and tells the reader nothing
    // they cannot see. The paragraph sits where the eye already lands first.
    set par(justify: false, leading: 0.55em)
    text(size: size)[#summary]
    v(3pt * rhythm)
  } else {
    v(9pt * rhythm)
  }

  for (si, s) in sections.enumerate() {
    if si > 0 { v(13pt * rhythm) }
    text(size: size + 0.5pt, weight: "bold", tracking: 1pt)[#upper(s.heading)]
    v(2pt * rhythm)
    block(above: 0pt, below: 0pt)[#line(length: 100%, stroke: 0.7pt + black)]
    v(SECTION_GAP * rhythm)

    for (i, e) in s.entries.enumerate() {
      if i > 0 { v(7pt * rhythm) }
      if e.title != "" or e.date != "" {
        block(above: 0pt, below: 0pt)[#grid(
          columns: (1fr, auto),
          align: (left, right),
          text(weight: "bold")[#e.title],
          text(style: "italic", size: size - 0.5pt, fill: date-grey)[#e.date],
        )]
      }
      if e.subtitle != "" or e.meta != "" {
        // explicit, since the title block above has below: 0pt
        v(3.5pt * rhythm)
        grid(
          columns: (1fr, auto),
          align: (left, right),
          text(style: "italic")[#e.subtitle],
          text(style: "italic", size: size - 0.5pt, fill: date-grey)[#e.meta],
        )
      }
      // Labelled lines: "Backend: Go, Python, ..." with the label bold. A person
      // scans a skills block by label; an ATS reads it as plain lines.
      if e.items.len() > 0 {
        for (ii, it) in e.items.enumerate() {
          if ii > 0 { v(4pt * rhythm) }   // wider than the leading, or wrapped lines read closer than separate items
          block(above: 0pt, below: 0pt)[#grid(columns: (1fr,), [#strong(it.label): #it.text])]
        }
      }
      if e.bullets.len() > 0 {
        if e.title != "" or e.subtitle != "" { v(3pt * rhythm) }
        for (bi, b) in e.bullets.enumerate() {
          if bi > 0 { v(4pt * rhythm) }
          block(above: 0pt, below: 0pt)[#grid(
            columns: (11pt, 1fr),
            align: (left, left),
            text[#sym.bullet], [#b],
          )]
        }
      }
      if e.text != "" { v(3pt * rhythm); e.text }
    }
  }
}
