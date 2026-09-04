// Harvard Office of Career Services resume format.
// Rendered by scripts/build_cv.py. Do not edit generated .typ files, edit the profile JSON.

#let cv(name: "", contact: (), sections: (), font: "New Computer Modern", size: 10.5pt, margin: 0.5in) = {
  set document(title: name, author: name)
  set page(paper: "us-letter", margin: margin)
  set text(font: font, size: size, hyphenate: false)
  set par(justify: false, leading: 0.62em, spacing: 0.62em)

  align(center)[
    #text(size: size + 6pt, weight: "bold", tracking: 0.5pt)[#upper(name)]
    #v(2pt)
    #text(size: size - 1pt)[#contact.join("  |  ")]
  ]
  v(6pt)

  for s in sections {
    text(size: size, weight: "bold", tracking: 0.6pt)[#upper(s.heading)]
    v(1pt)
    line(length: 100%, stroke: 0.5pt)
    v(3pt)
    for (i, e) in s.entries.enumerate() {
      if i > 0 { v(4pt) }
      if e.title != "" or e.date != "" {
        grid(
          columns: (1fr, auto),
          align: (left, right),
          text(weight: "bold")[#e.title],
          text(style: "italic")[#e.date],
        )
      }
      if e.subtitle != "" or e.meta != "" {
        grid(
          columns: (1fr, auto),
          align: (left, right),
          text(style: "italic")[#e.subtitle],
          text(style: "italic")[#e.meta],
        )
      }
      if e.bullets.len() > 0 {
        if e.title != "" or e.subtitle != "" { v(1pt) }
        for b in e.bullets {
          grid(
            columns: (10pt, 1fr),
            align: (left, left),
            [•], [#b],
          )
        }
      }
      if e.text != "" { v(1pt); e.text }
    }
    v(7pt)
  }
}
