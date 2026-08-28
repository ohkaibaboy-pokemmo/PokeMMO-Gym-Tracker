"""Responsive composition for the Full dashboard KPI header.

The approved wide layout keeps Ready / Waiting / Cooldown / Run Earnings /
Run Details on one line. Live Windows testing at roughly half-monitor width showed
that the supporting Run Details card could extend beyond the right edge even
though the headline KPI cards still fit. At narrower widths, keep the four
headline KPIs on the first line and move Run Details onto its own full-width row.

This is presentation-only. No earnings or tracker state is changed.
"""

import tkinter as tk

from .scaling import factor_for


SUMMARY_INLINE_MIN_WIDTH_BASE = 980


def summary_layout_mode(width, factor=1.0):
    """Return ``inline`` or ``stacked`` for the available KPI-summary width."""
    try:
        width = max(1, int(width))
    except (TypeError, ValueError):
        width = 1
    try:
        factor = max(0.85, float(factor or 1.0))
    except (TypeError, ValueError):
        factor = 1.0
    threshold = int(round(SUMMARY_INLINE_MIN_WIDTH_BASE * factor))
    return "inline" if width >= threshold else "stacked"


class DashboardHeaderResponsive:
    """Re-grid the Run Details card when the Full header becomes narrow."""

    def __init__(self, app):
        self.app = app
        self.split = getattr(app, "_dashboard_earnings_split", None)
        if self.split is None:
            raise RuntimeError("Responsive header requires the earnings split")
        self.summary = self.split.full.summary
        self._layout_mode = None
        self._after_id = None

        self.summary.bind("<Configure>", self._summary_configured, add="+")
        scale_var = getattr(app, "ui_scale_var", None)
        if scale_var is not None:
            scale_var.trace_add("write", self._scale_changed)
        try:
            app.after_idle(self.apply)
        except tk.TclError:
            pass
        app._dashboard_header_responsive = self

    def _summary_configured(self, _event=None):
        self._schedule()

    def _scale_changed(self, *_args):
        self._layout_mode = None
        self._schedule()

    def _schedule(self):
        if self._after_id is not None:
            return
        try:
            self._after_id = self.app.after_idle(self._apply_scheduled)
        except tk.TclError:
            self._after_id = None

    def _apply_scheduled(self):
        self._after_id = None
        self.apply()

    def _configure_inline_columns(self):
        self.split._configure_summary_columns()

    def _configure_stacked_columns(self):
        for column in range(5):
            self.summary.columnconfigure(column, weight=0, minsize=0, uniform="")
        for column in range(4):
            self.summary.columnconfigure(column, weight=1, uniform="headline_kpi")

    def apply(self):
        try:
            width = self.summary.winfo_width()
            factor = factor_for(self.app)
            mode = summary_layout_mode(width, factor)
        except tk.TclError:
            return
        if mode == self._layout_mode:
            return
        self._layout_mode = mode

        try:
            if mode == "inline":
                self._configure_inline_columns()
                self.split.details_card.grid_configure(
                    row=0,
                    column=4,
                    columnspan=1,
                    sticky="nsew",
                    padx=0,
                    pady=0,
                )
                self.summary.rowconfigure(1, weight=0, minsize=0)
            else:
                self._configure_stacked_columns()
                self.split.details_card.grid_configure(
                    row=1,
                    column=0,
                    columnspan=5,
                    sticky="nsew",
                    padx=0,
                    pady=(7, 0),
                )
                self.summary.rowconfigure(1, weight=0, minsize=0)
        except tk.TclError:
            pass


def install_dashboard_header_responsive(app):
    existing = getattr(app, "_dashboard_header_responsive", None)
    if existing is not None:
        return existing
    return DashboardHeaderResponsive(app)
