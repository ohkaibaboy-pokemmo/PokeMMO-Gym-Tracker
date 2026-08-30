"""Add the operational NEXT READY card to the Full dashboard header.

The card answers one question: which gym is the next one that can actually be
rerun? A future timestamp is shown only after that gym has satisfied the 5-rule;
an expired cooldown with fewer than five qualifying trainer wins is therefore not
presented as predictable readiness.

Live review of the first Windows build established a clearer priority order for the
headline: Next Ready -> Ready -> Waiting -> Run Earnings -> Run Details. The raw
Cooldown count remains available in tracker state/route rows, but is intentionally
removed from the Full headline because Next Ready is the more useful operational
summary of cooldown readiness.
"""

import tkinter as tk

from .dashboard_earnings_split import DETAIL_WEIGHT
from .next_ready import (
    ALL_CHARACTERS,
    format_next_ready_detail,
    format_next_ready_time,
    next_ready_gym,
)
from .scaling import factor_for, scaled

NEXT_READY_COLUMN = 0
READY_COLUMN = 1
WAITING_COLUMN = 2
RUN_EARNINGS_COLUMN = 3
DETAIL_COLUMN = 4
HEADLINE_COLUMNS = (0, 1, 2, 3)
HEADER_CARD_ORDER = ("next_ready", "ready", "waiting", "earnings", "details")


def next_ready_summary_column_weights():
    """Return four equal headline cards followed by the wider Run Details card."""
    return (1, 1, 1, 1, DETAIL_WEIGHT)


def next_ready_header_card_order():
    """Return the adopted visible Full-header card order."""
    return HEADER_CARD_ORDER


class DashboardNextReady:
    def __init__(self, app):
        self.app = app
        self.split = getattr(app, "_dashboard_earnings_split", None)
        self.responsive = getattr(app, "_dashboard_header_responsive", None)
        if self.split is None or self.responsive is None:
            raise RuntimeError("Next Ready requires earnings split and responsive header")

        self.summary = self.split.full.summary
        self._after_id = None
        self._build()
        self._install_layout_hooks()
        self._wrap_theme()
        self._wrap_scale()
        self.app.character_var.trace_add("write", self._character_changed)
        self.refresh()
        self.apply_scale()
        self.apply_theme()
        self._schedule_tick()
        app._dashboard_next_ready = self

    def _configure_summary_columns(self):
        for column in range(5):
            self.summary.columnconfigure(column, weight=0, minsize=0, uniform="")
        for column in HEADLINE_COLUMNS:
            self.summary.columnconfigure(column, weight=1, uniform="headline_kpi")
        self.summary.columnconfigure(DETAIL_COLUMN, weight=DETAIL_WEIGHT, uniform="")

    def _build(self):
        full = self.split.full

        # NEXT READY is the first thing a rerunner needs to know. READY and WAITING
        # follow it, then the current-run money. The old headline COOLDOWN count is
        # deliberately hidden: the route rows still expose individual cooldowns and
        # NEXT READY now provides the useful aggregate timing signal.
        try:
            full.stat_cards["cooldown"]["frame"].grid_forget()
            full.stat_cards["ready"]["frame"].grid_configure(
                row=0,
                column=READY_COLUMN,
                sticky="nsew",
                padx=(0, 7),
            )
            full.stat_cards["waiting"]["frame"].grid_configure(
                row=0,
                column=WAITING_COLUMN,
                sticky="nsew",
                padx=(0, 7),
            )
        except (KeyError, tk.TclError):
            pass

        self.split.run_card.grid_configure(column=RUN_EARNINGS_COLUMN, padx=(0, 7))
        self.split.details_card.grid_configure(column=DETAIL_COLUMN, padx=0)

        self.card = tk.Frame(self.summary, bd=0, highlightthickness=1)
        self.card.grid(row=0, column=NEXT_READY_COLUMN, sticky="nsew", padx=(0, 7))
        self.card.columnconfigure(0, weight=1)

        self.title = tk.Label(
            self.card,
            text="NEXT READY",
            font=("Segoe UI Semibold", 7),
            anchor="w",
        )
        self.title.pack(fill="x", padx=10, pady=(5, 0))

        self.time_var = tk.StringVar(master=self.app, value="—")
        self.time_label = tk.Label(
            self.card,
            textvariable=self.time_var,
            font=("Segoe UI Semibold", 10),
            anchor="w",
        )
        self.time_label.pack(fill="x", padx=10, pady=(0, 0))

        self.detail_var = tk.StringVar(master=self.app, value="Complete 5-rule first")
        self.detail_label = tk.Label(
            self.card,
            textvariable=self.detail_var,
            font=("Segoe UI", 7),
            anchor="w",
        )
        self.detail_label.pack(fill="x", padx=10, pady=(0, 4))

    def _install_layout_hooks(self):
        # DashboardHeaderResponsive owns narrow/wide composition. Teach its
        # existing callbacks about the five-column priority layout rather than
        # creating a second resize system.
        def configure_split_columns():
            self._configure_summary_columns()

        self.split._configure_summary_columns = configure_split_columns

        def configure_stacked_columns():
            self._configure_summary_columns()
            # Run Details is stacked on row 1; all four headline columns remain
            # equal on row 0.
            self.summary.columnconfigure(DETAIL_COLUMN, weight=0, minsize=0, uniform="")

        self.responsive._configure_stacked_columns = configure_stacked_columns

        original_apply = self.responsive.apply
        if not getattr(original_apply, "_next_ready_wrapped", False):
            def apply_with_next_ready(*args, **kwargs):
                result = original_apply(*args, **kwargs)
                self._apply_responsive_layout()
                return result

            apply_with_next_ready._next_ready_wrapped = True
            self.responsive.apply = apply_with_next_ready

        self.responsive._layout_mode = None
        self.responsive.apply()

    def _apply_responsive_layout(self):
        mode = getattr(self.responsive, "_layout_mode", None)
        try:
            self.split.run_card.grid_configure(
                row=0,
                column=RUN_EARNINGS_COLUMN,
                columnspan=1,
                sticky="nsew",
                padx=(0, 7),
                pady=0,
            )
            self.card.grid_configure(
                row=0,
                column=NEXT_READY_COLUMN,
                columnspan=1,
                sticky="nsew",
                padx=(0, 7),
                pady=0,
            )
            if mode == "stacked":
                self._configure_summary_columns()
                self.summary.columnconfigure(DETAIL_COLUMN, weight=0, minsize=0, uniform="")
                self.split.details_card.grid_configure(
                    row=1,
                    column=0,
                    columnspan=5,
                    sticky="nsew",
                    padx=0,
                    pady=(7, 0),
                )
            else:
                self._configure_summary_columns()
                self.split.details_card.grid_configure(
                    row=0,
                    column=DETAIL_COLUMN,
                    columnspan=1,
                    sticky="nsew",
                    padx=0,
                    pady=0,
                )
        except tk.TclError:
            pass

    def _wrap_theme(self):
        original = self.split.apply_theme
        if getattr(original, "_next_ready_wrapped", False):
            return

        def apply_theme_with_next_ready(*args, **kwargs):
            result = original(*args, **kwargs)
            self.apply_theme()
            return result

        apply_theme_with_next_ready._next_ready_wrapped = True
        self.split.apply_theme = apply_theme_with_next_ready

    def _wrap_scale(self):
        original = self.split.apply_scale
        if getattr(original, "_next_ready_wrapped", False):
            return

        def apply_scale_with_next_ready(*args, **kwargs):
            result = original(*args, **kwargs)
            self.apply_scale()
            return result

        apply_scale_with_next_ready._next_ready_wrapped = True
        self.split.apply_scale = apply_scale_with_next_ready

    def _character_changed(self, *_args):
        self.refresh()

    def _schedule_tick(self):
        try:
            self._after_id = self.app.after(1000, self._tick)
        except tk.TclError:
            self._after_id = None

    def _tick(self):
        self._after_id = None
        self.refresh()
        self._schedule_tick()

    def refresh(self):
        selected = self.app.character_var.get() or ALL_CHARACTERS
        result = next_ready_gym(self.app.state_data, selected_character=selected)
        try:
            self.time_var.set(format_next_ready_time(result))
            self.detail_var.set(format_next_ready_detail(result, selected_character=selected))
        except tk.TclError:
            pass

    def apply_scale(self):
        factor = factor_for(self.app)
        try:
            self.title.configure(font=("Segoe UI Semibold", scaled(7, factor, 6)))
            self.time_label.configure(font=("Segoe UI Semibold", scaled(10, factor, 8)))
            self.detail_label.configure(font=("Segoe UI", scaled(7, factor, 6)))
        except tk.TclError:
            pass

    def apply_theme(self):
        theme = self.app.theme()
        try:
            self.card.configure(bg=theme["card_bg"], highlightbackground=theme["card_border"])
            self.title.configure(bg=theme["card_bg"], fg=theme["ready"])
            self.time_label.configure(bg=theme["card_bg"], fg=theme["ready"])
            self.detail_label.configure(bg=theme["card_bg"], fg=theme["muted"])
        except tk.TclError:
            pass


def install_dashboard_next_ready(app):
    existing = getattr(app, "_dashboard_next_ready", None)
    if existing is not None:
        return existing
    return DashboardNextReady(app)
