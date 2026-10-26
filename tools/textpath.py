"""Convert a string set in a TTF into SVG path data (outlined text).

Usage from other scripts:
    from textpath import text_path
    d, width, cap = text_path("BOSS", "fonts/BigShoulders-900.ttf", size=200, x=0, y=200)
`y` is the baseline. Returns path data, advance width, and cap height in px.
"""
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

_cache = {}


def _font(path):
    if path not in _cache:
        _cache[path] = TTFont(path)
    return _cache[path]


def measure(text, font_path, size, tracking=0.0):
    f = _font(font_path)
    upm = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    s = size / upm
    w = 0.0
    for i, ch in enumerate(text):
        w += hmtx[cmap[ord(ch)]][0] * s
        if i < len(text) - 1:
            w += tracking * size
    return w


def text_path(text, font_path, size, x=0.0, y=0.0, tracking=0.0):
    f = _font(font_path)
    upm = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    hmtx = f["hmtx"]
    s = size / upm
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    cx = x
    for i, ch in enumerate(text):
        gname = cmap[ord(ch)]
        tp = TransformPen(pen, (s, 0, 0, -s, cx, y))
        gs[gname].draw(tp)
        cx += hmtx[gname][0] * s
        if i < len(text) - 1:
            cx += tracking * size
    os2 = f["OS/2"]
    cap = getattr(os2, "sCapHeight", 0) * s
    return pen.getCommands(), cx - x, cap
