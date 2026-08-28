"""Project-owned muted segmented emblem used for the Gym Tracker app icon.

The design mirrors the approved Full-view visual language: a restrained charcoal /
steel-grey Poké Ball-inspired mark with deliberate negative-space gaps. Small
Windows icon sizes use a deliberately simpler, higher-contrast treatment so the
emblem stays legible in title bars and the taskbar rather than becoming muddy.
"""

from functools import lru_cache


WINDOW_ICON_SIZE = 64
WINDOW_ICON_SIZES = (16, 24, 32, 48, 64)
WINDOWS_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)

_TRANSPARENT = None
_EDGE = "#202930"
_DARK = "#2b353d"
_BAR = "#303a42"
_MAIN = "#52606a"
_HIGHLIGHT = "#66727b"
_BUTTON = "#65717a"
_BUTTON_HIGHLIGHT = "#7b868e"

# Small-size palette intentionally has fewer tones and more contrast.
_SMALL_EDGE = "#1e272e"
_SMALL_BAR = "#3a454d"
_SMALL_MAIN = "#69757e"
_SMALL_BUTTON = "#7c8790"


def _colour_at(x, y, size):
    """Return the emblem colour for one raster pixel, or None for transparency."""
    cx = (size - 1) / 2.0
    cy = (size - 1) / 2.0
    dx = x - cx
    dy = y - cy
    radius = (dx * dx + dy * dy) ** 0.5

    small = size <= 32
    outer = size * (0.445 if small else 0.435)
    inner = size * (0.255 if small else 0.275)
    bar_half = max(1.0, size * (0.055 if small else 0.043))
    # Wider negative space at taskbar/title-bar sizes is the main readability fix.
    arc_gap = bar_half + size * (0.060 if small else 0.032)
    hub_outer = size * (0.180 if small else 0.165)
    hub_inner = size * (0.090 if small else 0.095)

    # Centre button and darker surrounding hub sit above the horizontal bar.
    if radius <= hub_inner:
        if small:
            return _SMALL_BUTTON
        if dx < -size * 0.018 and dy < -size * 0.018 and radius > hub_inner * 0.72:
            return _BUTTON_HIGHLIGHT
        return _BUTTON
    if radius <= hub_outer:
        if small:
            return _SMALL_EDGE
        if radius >= hub_outer - max(1.0, size * 0.018):
            return _EDGE
        return _DARK

    # Broken upper/lower ring. The clear strip around the centre band is kept
    # intentionally obvious so this never collapses into a conventional ball.
    if inner <= radius <= outer and abs(dy) >= arc_gap:
        edge_width = max(1.0, size * (0.035 if small else 0.020))
        if radius >= outer - edge_width or radius <= inner + edge_width:
            return _SMALL_EDGE if small else _EDGE
        if small:
            return _SMALL_MAIN
        if dy < 0 and dx < size * 0.12:
            return _HIGHLIGHT
        return _MAIN

    # Centre bar remains visibly detached from the arcs by transparent gaps.
    if abs(dy) <= bar_half and abs(dx) <= outer * 0.98:
        if small:
            return _SMALL_BAR
        if abs(dy) >= bar_half - max(1.0, size * 0.010):
            return _EDGE
        return _BAR

    return _TRANSPARENT


@lru_cache(maxsize=None)
def icon_spans(size=WINDOW_ICON_SIZE):
    """Return horizontal colour spans as (x1, y1, x2, y2, colour)."""
    size = max(16, int(size))
    spans = []
    for y in range(size):
        run_colour = _colour_at(0, y, size)
        run_start = 0
        for x in range(1, size + 1):
            colour = _colour_at(x, y, size) if x < size else object()
            if colour == run_colour:
                continue
            if run_colour is not None:
                spans.append((run_start, y, x, y + 1, run_colour))
            run_start = x
            run_colour = colour
    return tuple(spans)
