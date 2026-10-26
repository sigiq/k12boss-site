"""Generate outlined SVG logos for K12 BOSS into ../assets.

Concept: the "ceiling" is a heavy bar sitting over K12; it snaps where BOSS
rises past it, and two shards of it lift away.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from textpath import text_path, measure  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(HERE, "..", "assets")
HEAVY = os.path.join(FONTS, "BigShoulders-900.ttf")
BOLD = os.path.join(FONTS, "BigShoulders-800.ttf")
MONO = os.path.join(FONTS, "PlexMono-500.ttf")

INK = "#15161B"
BUS = "#FFC21A"
PAPER = "#F3F4EF"


def poly(points, fill):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}"/>'


def wordmark_parts(ink, x0=0.0, baseline=0.0, cap_target=100.0):
    """Return (svg elements, bbox) for the horizontal wordmark."""
    from fontTools.ttLib import TTFont

    cap_ratio = TTFont(HEAVY)["OS/2"].sCapHeight / TTFont(HEAVY)["head"].unitsPerEm
    size_b = cap_target / cap_ratio
    size_k = size_b * 0.62
    cap_b = cap_target
    cap_k = cap_target * 0.62

    els = []
    d_k, w_k, _ = text_path("K12", BOLD, size_k, x0, baseline, tracking=0.02)
    gap = cap_b * 0.26
    xb = x0 + w_k + gap
    d_b, w_b, _ = text_path("BOSS", HEAVY, size_b, xb, baseline, tracking=0.015)
    els.append(f'<path d="{d_k}" fill="{ink}"/>')
    els.append(f'<path d="{d_b}" fill="{ink}"/>')

    # The ceiling: a bar over K12, snapped at an angle just past it.
    t = cap_b * 0.11
    bar_bottom = baseline - cap_k - cap_b * 0.10
    bar_top = bar_bottom - t
    end = x0 + w_k + gap * 0.55
    els.append(poly([(x0, bar_top), (end + t * 0.35, bar_top), (end - t * 0.35, bar_bottom), (x0, bar_bottom)], ink))

    # Shards lifting off from the break, clear of the B.
    b_top = baseline - cap_b
    s1x, s1y = end + cap_b * 0.02, b_top - cap_b * 0.20
    els.append(poly([(s1x, s1y + t * 0.9), (s1x + t * 1.6, s1y + t * 0.15), (s1x + t * 1.9, s1y + t * 0.85), (s1x + t * 0.3, s1y + t * 1.6)], ink))
    s2x, s2y = xb + cap_b * 0.30, b_top - cap_b * 0.36
    els.append(poly([(s2x, s2y + t * 0.6), (s2x + t * 0.95, s2y), (s2x + t * 1.25, s2y + t * 0.5), (s2x + t * 0.3, s2y + t * 1.05)], ink))

    top = min(bar_top, s2y)
    bbox = (x0, top, xb + w_b, baseline)
    return els, bbox


def svg(w, h, body, extra=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}"{extra}>{body}</svg>\n'


def write(name, content):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(content)
    print("wrote", name)


def make_wordmarks():
    for name, ink, bg in [("logo.svg", INK, None), ("logo-light.svg", "#FFFFFF", None), ("logo-on-yellow.svg", INK, BUS)]:
        els, (x1, y1, x2, y2) = wordmark_parts(ink, 0, 0, 100)
        pad = 24 if bg else 2
        w, h = (x2 - x1) + pad * 2, (y2 - y1) + pad * 2
        body = f'<g transform="translate({pad - x1:.2f},{pad - y1:.2f})">{"".join(els)}</g>'
        if bg:
            body = f'<rect width="{w:.0f}" height="{h:.0f}" fill="{bg}"/>' + body
        write(name, svg(w, h, body))


def mark_body(size=512, grid=True, tile=True):
    """Square app/podcast mark: yellow tile, wordmark stacked K12 over BOSS."""
    s = size
    els = [f'<rect width="{s}" height="{s}" fill="{BUS}"/>'] if tile else []
    if grid and tile:
        step = s / 16
        lines = []
        for i in range(1, 16):
            p = i * step
            lines.append(f"M{p:.1f} 0V{s}M0 {p:.1f}H{s}")
        els.append(f'<path d="{"".join(lines)}" stroke="{INK}" stroke-opacity="0.09" stroke-width="{s / 512:.2f}" fill="none"/>')

    m = s * 0.11
    # BOSS fills the width along the bottom.
    w_target = s - 2 * m
    w_unit = measure("BOSS", HEAVY, 100, tracking=0.015)
    size_b = 100 * w_target / w_unit
    from fontTools.ttLib import TTFont
    f = TTFont(HEAVY)
    cap_b = f["OS/2"].sCapHeight / f["head"].unitsPerEm * size_b
    baseline = s - m
    d_b, _, _ = text_path("BOSS", HEAVY, size_b, m, baseline, tracking=0.015)
    els.append(f'<path d="{d_b}" fill="{INK}"/>')

    # K12 above, left aligned, with the ceiling bar over it.
    size_k = size_b * 0.5
    fk = TTFont(BOLD)
    cap_k = fk["OS/2"].sCapHeight / fk["head"].unitsPerEm * size_k
    base_k = baseline - cap_b - s * 0.05
    d_k, w_k, _ = text_path("K12", BOLD, size_k, m, base_k, tracking=0.02)
    els.append(f'<path d="{d_k}" fill="{INK}"/>')

    t = s * 0.036
    bar_bottom = base_k - cap_k - s * 0.035
    bar_top = bar_bottom - t
    end = m + w_k + s * 0.06
    els.append(poly([(m, bar_top), (end + t * 0.35, bar_top), (end - t * 0.35, bar_bottom), (m, bar_bottom)], INK))
    # The rest of the ceiling, broken off and lifting to the right.
    rx = end + s * 0.06
    els.append(poly([(rx, bar_top - s * 0.02), (s - m, bar_top - s * 0.075), (s - m, bar_bottom - s * 0.075), (rx - t * 0.3, bar_bottom - s * 0.02)], INK))
    sx, sy = end + s * 0.005, bar_top - s * 0.06
    els.append(poly([(sx, sy + t * 0.8), (sx + t * 1.2, sy), (sx + t * 1.5, sy + t * 0.6), (sx + t * 0.3, sy + t * 1.35)], INK))
    return "".join(els)


def make_marks():
    write("mark.svg", svg(512, 512, mark_body(512)))
    # Stacked lockup on transparent, cropped to the artwork (for cover art, print).
    write("logo-stacked.svg", svg(512 * 0.80, 512 * 0.74, f'<g transform="translate({-512 * 0.10:.1f},{-512 * 0.17:.1f})">{mark_body(512, tile=False)}</g>'))
    write("favicon.svg", svg(64, 64, favicon_body()))


def favicon_body():
    """At 16-32px only a few shapes survive: K12 under a snapped bar."""
    s = 64
    els = [f'<rect width="{s}" height="{s}" rx="10" fill="{BUS}"/>']
    from fontTools.ttLib import TTFont
    f = TTFont(HEAVY)
    w_unit = measure("K12", HEAVY, 100, tracking=0.01)
    size = 100 * (s * 0.74) / w_unit
    cap = f["OS/2"].sCapHeight / f["head"].unitsPerEm * size
    x = (s - s * 0.74) / 2
    base = s * 0.86
    d, _, _ = text_path("K12", HEAVY, size, x, base, tracking=0.01)
    els.append(f'<path d="{d}" fill="{INK}"/>')
    t = 6
    bar_bottom = base - cap - 4
    bar_top = bar_bottom - t
    mid = s * 0.52
    els.append(poly([(x, bar_top), (mid, bar_top), (mid - 3, bar_bottom), (x, bar_bottom)], INK))
    els.append(poly([(mid + 4, bar_top - 2), (s - x, bar_top - 6), (s - x, bar_bottom - 6), (mid + 1, bar_bottom - 2)], INK))
    return "".join(els)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    make_wordmarks()
    make_marks()
