// Harvard Office of Career Services resume format.
// Rendered by scripts/build_cv.py. Do not edit generated .typ files, edit the profile JSON.
//
// Typography notes, since they are decisions and not defaults:
//   Charter first. Matthew Carter drew it for low-resolution output at small
//   sizes, so it has a tall x-height and narrow set width: more words per line
//   than Georgia, more legible on screen than Times. Georgia and Times New Roman
//   follow as fallbacks because every machine has them.
//   Leading is 0.5em and the gap between bullets is 4pt, deliberately larger.
//   Lines wrapped inside one bullet must sit closer together than two separate
//   bullets do, or the list stops reading as a list.
//   Vertical rhythm runs 2pt inside an entry, 5pt between entries, 8pt between
//   sections, so the eye reads hierarchy from spacing alone.

#let cv(
  name: "",
  contact: (),
  sections: (),
  font: ("Charter", "Georgia", "Times New Roman"),
  size: 10.5pt,
  margin: 0.55in,
) = {
  set document(title: name, author: name)
  set page(paper: "us-letter", margin: margin)
  set text(font: font, size: size, fill: black, hyphenate: false)
  set par(justify: false, leading: 0.5em, spacing: 0.5em)

  align(center)[
    #text(size: size + 7pt, weight: "bold", tracking: 1.1pt)[#upper(name)]
    #v(3.5pt)
    #text(size: size - 1pt, fill: rgb(25, 25, 25))[#contact.join("   |   ")]
  ]
  v(9pt)

  for (si, s) in sections.enumerate() {
    if si > 0 { v(8pt) }
    text(size: size + 0.5pt, weight: "bold", tracking: 1pt)[#upper(s.heading)]
    v(2pt)
    line(length: 100%, stroke: 0.7pt + black)
    v(4pt)

    for (i, e) in s.entries.enumerate() {
      if i > 0 { v(5pt) }
      if e.title != "" or e.date != "" {
        grid(
          columns: (1fr, auto),
          align: (left, right),
          text(weight: "bold")[#e.title],
          text(style: "italic", size: size - 0.5pt)[#e.date],
        )
      }
      if e.subtitle != "" or e.meta != "" {
        v(0.5pt)
        grid(
          columns: (1fr, auto),
          align: (left, right),
          text(style: "italic")[#e.subtitle],
          text(style: "italic", size: size - 0.5pt)[#e.meta],
        )
      }
      if e.bullets.len() > 0 {
        if e.title != "" or e.subtitle != "" { v(2pt) }
        for (bi, b) in e.bullets.enumerate() {
          block(above: if bi == 0 { 0pt } else { 4pt }, below: 0pt)[
            #grid(
              columns: (12pt, 1fr),
              align: (left, left),
              text[#sym.bullet], [#b],
            )
          ]
        }
      }
      if e.text != "" { v(3pt); e.text }
    }
  }
}
