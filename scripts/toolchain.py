"""Talking to the tools outside Python: Typst to render, poppler or pypdf to read back.

Each of the two has a system path and a pip path, and cvfit takes whichever is
there. That is the difference between "works on my laptop" and "works on a
Windows box, a locked-down machine or a notebook", where `brew install` isn't a
thing but `pip install` is.

    rendering:  the typst binary, else `pip install typst` (same compiler, no CLI)
    reading:    pdfinfo and pdftotext, else `pip install pypdf`

Poppler is exact and fast, so it wins when present. The pure-Python path
approximates in one place: pypdf reports each line's baseline, not its glyph
box, so the edges are derived from the font size. Measured against poppler on
the example resumes, page fill agrees to within 0.2 of a percentage point,
which is inside the tolerance of a number printed as a whole percent.

Coordinates here are poppler's: origin top-left, y growing downward, points.
"""

import re
import shutil
import subprocess
from pathlib import Path

READ_HINT = ("no way to read the PDF back. Install poppler (brew install poppler, "
             "apt install poppler-utils, choco install poppler) or run: pip install pypdf")
RENDER_HINT = "no Typst. Run: pip install typst   (or brew install typst)"


def _has_poppler():
    return bool(shutil.which("pdfinfo") and shutil.which("pdftotext"))


def _pypdf():
    try:
        import pypdf
    except ImportError:
        return None
    return pypdf


def backend():
    """'poppler', 'pypdf', or None when neither is installed."""
    if _has_poppler():
        return "poppler"
    return "pypdf" if _pypdf() else None


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def page_count(pdf):
    if _has_poppler():
        m = re.search(r"Pages:\s+(\d+)", _run(["pdfinfo", str(pdf)]))
        return int(m.group(1)) if m else -1
    pypdf = _pypdf()
    if not pypdf:
        return -1
    return len(pypdf.PdfReader(str(pdf)).pages)


def text(pdf):
    """The text layer, which is also what an ATS gets."""
    if _has_poppler():
        return _run(["pdftotext", str(pdf), "-"])
    pypdf = _pypdf()
    if not pypdf:
        return ""
    return "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(pdf)).pages)


def text_span(pdf):
    """(page height, top of the first line, bottom of the last line), in points.

    None when the PDF has no text layer, which is itself a finding: a resume
    whose text can't be read back is one an ATS can't read either.
    """
    if _has_poppler():
        bb = _run(["pdftotext", "-bbox", str(pdf), "-"])
        tops = [float(m) for m in re.findall(r'yMin="([0-9.]+)"', bb)]
        bots = [float(m) for m in re.findall(r'yMax="([0-9.]+)"', bb)]
        hs = [float(m) for m in re.findall(r'<page width="[0-9.]+" height="([0-9.]+)"', bb)]
        if not (tops and bots and hs):
            return None
        return hs[0], min(tops), max(bots)

    pypdf = _pypdf()
    if not pypdf:
        return None
    reader = pypdf.PdfReader(str(pdf))
    page_h = float(reader.pages[0].mediabox.height)
    tops, bots = [], []

    for page in reader.pages:
        h = float(page.mediabox.height)

        def visit(t, cm, tm, font_dict, font_size, _h=h):
            if not t or not t.strip():
                return
            # Typst writes each line's position into the transformation matrix
            # and leaves the text matrix at identity, so the baseline is the
            # composition of the two, and either one can carry the scale.
            scale = (abs(float(cm[3])) or 1.0) * (abs(float(tm[3])) or 1.0)
            size = abs(float(font_size or 10)) * scale
            up = float(tm[4]) * float(cm[1]) + float(tm[5]) * float(cm[3]) + float(cm[5])
            baseline = _h - up                          # top-left origin, like poppler
            tops.append(baseline - 0.85 * size)         # ascent, accents included
            bots.append(baseline + 0.25 * size)         # descender

        page.extract_text(visitor_text=visit)

    if not tops:
        return None
    return page_h, max(0.0, min(tops)), max(bots)


# ---- rendering -------------------------------------------------------------


def _typst_module():
    try:
        import typst
    except ImportError:
        return None
    return typst


def can_render():
    return bool(shutil.which("typst")) or _typst_module() is not None


def render(typ, out, fmt=None, ppi=None):
    """Compile a .typ file. Returns (ok, message).

    `pip install typst` ships the compiler as a Python module with no command
    line of its own, so a machine can have Typst and no `typst` on PATH. Both
    paths run the same compiler on the same file.
    """
    typ, out = Path(typ), Path(out)
    if shutil.which("typst"):
        cmd = ["typst", "compile", "--root", str(typ.parent)]
        if fmt:
            cmd += ["--format", fmt]
        if ppi:
            cmd += ["--ppi", str(ppi), "--pages", "1"]
        cmd += [str(typ), str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.returncode == 0, (r.stderr or r.stdout)

    typst = _typst_module()
    if not typst:
        return False, RENDER_HINT
    try:
        typst.compile(str(typ), output=str(out), format=fmt, ppi=ppi, root=str(typ.parent))
        return True, ""
    except Exception as e:                     # the module raises on a bad document
        return False, str(e)
