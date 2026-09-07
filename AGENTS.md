# cvfit: notes for AI agents

This repository is an agent skill in the open Agent Skills format. The skill
itself is `SKILL.md` (mirrored at `skills/cvfit/SKILL.md` for the `skills` CLI
layout); read it when someone asks for a tailored resume. `TAILORING.md` holds
the priority rules it refers to, `kinds.json` the per-kind layout, and
`templates/harvard.typ` the Typst template.

Working on the repo itself:

- Requirements: Python 3.9+, Typst, poppler (`pdfinfo`, `pdftotext`), pyyaml.
- Build: `python3 scripts/build_cv.py examples/ada-lovelace.northwind.yaml -o out/cv.pdf --kind job --preview`
- Verify: `python3 scripts/verify_cv.py out/cv.pdf --profile out/cv.profile.json --master examples/ada-lovelace.yaml --target examples/posting-northwind.json`
- Tests: `python3 tests/run.py` (run before every push).
- Keep `SKILL.md` and `skills/cvfit/SKILL.md` identical; the tests check it.
- The `.claude-plugin/` folder is only the Claude Code plugin manifest; nothing
  else in the repo depends on any particular agent.
