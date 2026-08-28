"""Final alignment pass for the Full dashboard KPI/header concept.

Build 22 confirmed the new KPI symbols were the right visual direction, but live
Windows feedback showed them reading as slightly floaty beside the two-line
label/value block. This layer keeps the existing artwork and semantics while
making each leading icon span the visual height of its title+value group, centering
the complete icon+text group vertically in its card, and centering the passive
live-log status beneath the subtitle.
"""

import tkinter as tk

from .scaling import factor_for, scaled


KPI_ICON_SPAN_BASE = 40
KPI_ICON_SPAN_MIN = 32
KPI_ICON_SIDE_GAP_BASE = 8
KPI_ICON_OUTER_PAD_BASE = 10
KPI_GROUP_ROW_WEIGHTS = (1, 1)


def kpi_icon_span_size(factor=1.0):
    """Return the concept-style leading-icon size for a UI scale factor."""
    try:
        factor = float(factor)
    except (TypeError, ValueError):
        factor = 1.0
    return max(KPI_ICON_SPAN_MIN, int(round(KPI_ICON_SPAN_BASE * max(0.85, factor))))


class DashboardKpiAlignment:
    def __init__(self, app):
        self.app = app
        self.polish = getattr(app, "_dashboard_final_polish", None)
        if self.polish is None:
            raise RuntimeError("KPI alignment requires dashboard final polish")

        self._wrap_scale()
        self.apply()
        app._dashboard_kpi_alignment = self

    def _wrap_scale(self):
        original = self.polish.apply_scale
        if getattr(original, "_kpi_alignment_wrapped", False):
            return

        def apply_scale_with_alignment(*args, **kwargs):
            result = original(*args, **kwargs)
            self.apply()
            return result

        apply_scale_with_alignment._kpi_alignment_wrapped = True
        self.polish.apply_scale = apply_scale_with_alignment

    def _align_live_status(self):
        live = getattr(self.polish, "live_below", None)
        if live is None:
            return
        try:
            live.configure(anchor="center", justify="center")
            live.pack_configure(fill="x", anchor="center", pady=(3, 0))
        except tk.TclError:
            pass

    def _center_kpi_groups(self):
        """Vertically centre each icon + two-line text block in its card."""
        full = getattr(self.polish, "full", None)
        if full is None:
            return

        for key in ("ready", "waiting", "cooldown"):
            widgets = getattr(full, "stat_cards", {}).get(key)
            if not widgets:
                continue
            card = widgets.get("frame")
            caption = widgets.get("caption")
            count = widgets.get("count")
            if card is None or caption is None or count is None:
                continue
            try:
                card.grid_rowconfigure(0, weight=KPI_GROUP_ROW_WEIGHTS[0])
                card.grid_rowconfigure(1, weight=KPI_GROUP_ROW_WEIGHTS[1])
                caption.grid_configure(sticky="sw", pady=0)
                count.grid_configure(sticky="nw", pady=0)
            except tk.TclError:
                pass

        # dashboard_earnings_split points these references at the standalone
        # Run Earnings KPI, so the fourth headline card follows the same geometry.
        primary = getattr(full, "earnings_primary", None)
        title = getattr(full, "earnings_title", None)
        value = getattr(full, "run_money_label", None)
        if primary is not None and title is not None and value is not None:
            try:
                primary.grid_rowconfigure(0, weight=KPI_GROUP_ROW_WEIGHTS[0])
                primary.grid_rowconfigure(1, weight=KPI_GROUP_ROW_WEIGHTS[1])
                title.grid_configure(sticky="sw", pady=0)
                value.grid_configure(sticky="nw", pady=0)
            except tk.TclError:
                pass

    def _align_icon(self, key, canvas, factor):
        size = kpi_icon_span_size(factor)
        gap = scaled(KPI_ICON_SIDE_GAP_BASE, factor, 6)
        outer = scaled(KPI_ICON_OUTER_PAD_BASE, factor, 8)
        try:
            canvas.configure(width=size, height=size)
            # All four headline cards now share the exact same leading-icon rail,
            # including the standalone Run Earnings card.
            canvas.grid_configure(
                row=0,
                column=0,
                rowspan=2,
                sticky="w",
                padx=(outer, gap),
                pady=0,
            )
        except tk.TclError:
            pass

    def apply(self):
        factor = factor_for(self.app)
        self._align_live_status()
        self._center_kpi_groups()
        for key, canvas in getattr(self.polish, "kpi_icons", {}).items():
            self._align_icon(key, canvas, factor)
        try:
            self.polish._draw_kpi_icons()
        except (AttributeError, tk.TclError):
            pass


def install_dashboard_kpi_alignment(app):
    existing = getattr(app, "_dashboard_kpi_alignment", None)
    if existing is not None:
        return existing
    return DashboardKpiAlignment(app)
