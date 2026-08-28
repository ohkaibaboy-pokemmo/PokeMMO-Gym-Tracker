"""Shared geometry helpers for the v0.6 Full Gym Route.

The original rich-row implementation patched dozens of Tk child widgets to keep
the type icon + Leader group centred. The Full route is now rendered directly on
a Canvas, so alignment is expressed as geometry rather than widget monkey-patches.
"""


BASE_LEADER_GROUP_WIDTH = 120
BASE_LEADER_ICON_SIZE = 22
BASE_LEADER_ICON_GAP = 6


def full_leader_group_geometry(scale_factor=1.0):
    """Return ``(group, icon, gap, text)`` widths for the centred Leader cell."""
    try:
        factor = max(0.85, float(scale_factor or 1.0))
    except (TypeError, ValueError):
        factor = 1.0

    group = max(102, int(round(BASE_LEADER_GROUP_WIDTH * factor)))
    icon = max(18, int(round(BASE_LEADER_ICON_SIZE * factor)))
    gap = max(4, int(round(BASE_LEADER_ICON_GAP * factor)))
    text = max(1, group - icon - gap)
    return group, icon, gap, text


def install_dashboard_table_alignment():
    """Compatibility hook retained for main.pyw.

    Canvas-based Full rows consume :func:`full_leader_group_geometry` directly,
    so there are no row widgets left to patch at install time.
    """
    return None
